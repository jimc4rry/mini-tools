from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

TICKETS_TRIAL_LENGTH_DAYS = 14

# How many days out a due date still counts as "safe" (green) vs "coming up"
# (orange) on the kanban card pill - see Ticket.due_status below.
DUE_SOON_THRESHOLD_DAYS = 3


class Board(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_boards"
    )
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("tickets:board_detail", args=[self.pk])

    def is_accessible_by(self, user):
        return self.owner_id == user.id or self.memberships.filter(user=user).exists()


class BoardMembership(models.Model):
    """
    The new pattern this app introduces to the Hub: an owner can invite
    other existing platform accounts to see/use a Board. No roles beyond
    member for v1 - the owner is always implicitly privileged (can invite/
    remove members, rename/delete the board).
    """

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="board_memberships"
    )
    invited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("board", "user")

    def __str__(self):
        return f"{self.user} on {self.board}"


class Tag(models.Model):
    """
    Scoped to a Board (not global) - two unrelated teams' boards shouldn't
    share one tag namespace, and different boards may want the same tag
    name in a different color. A deliberate deviation from a literal
    "unique name" reading of the spec, for the same multi-tenant reason
    BoardMembership/TicketTemplate are board-scoped.
    """

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="tags")
    name = models.CharField(max_length=50, verbose_name=_("Name"))
    color = models.CharField(max_length=7, default="#6d5efc", verbose_name=_("Color"))

    class Meta:
        unique_together = ("board", "name")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Ticket(models.Model):
    class Status(models.TextChoices):
        TODO = "todo", _("To Do")
        IN_PROGRESS = "in_progress", _("In Progress")
        DONE = "done", _("Done")

    class Priority(models.TextChoices):
        CRITICAL = "critical", _("Critical")
        HIGH = "high", _("High")
        MEDIUM = "medium", _("Medium")
        LOW = "low", _("Low")

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="tickets")
    title = models.CharField(max_length=200, verbose_name=_("Title"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.MEDIUM, verbose_name=_("Priority")
    )
    due_date = models.DateField(null=True, blank=True, verbose_name=_("Due date"))
    tags = models.ManyToManyField(Tag, blank=True, related_name="tickets", verbose_name=_("Tags"))
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reported_tickets"
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
        verbose_name=_("Assignee"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("tickets:ticket_detail", args=[self.pk])

    @property
    def due_status(self):
        """
        "ok" (green, >3 days out or no due date), "soon" (orange, within
        DUE_SOON_THRESHOLD_DAYS), or "overdue" (red, past due and not Done) -
        drives the colored pill on the kanban card. Reuses the same
        ok/warning/critical vocabulary as Vault's own urgency property.
        """
        if not self.due_date:
            return None
        if self.status == self.Status.DONE:
            return "ok"
        days_left = (self.due_date - timezone.localdate()).days
        if days_left < 0:
            return "overdue"
        if days_left <= DUE_SOON_THRESHOLD_DAYS:
            return "soon"
        return "ok"


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField(verbose_name=_("Comment"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author} on {self.ticket}"
