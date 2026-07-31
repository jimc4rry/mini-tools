from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

TICKETS_TRIAL_LENGTH_DAYS = 14


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


class Ticket(models.Model):
    class Status(models.TextChoices):
        TODO = "todo", _("To Do")
        IN_PROGRESS = "in_progress", _("In Progress")
        DONE = "done", _("Done")

    class Priority(models.TextChoices):
        LOW = "low", _("Low")
        MEDIUM = "medium", _("Medium")
        HIGH = "high", _("High")

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="tickets")
    title = models.CharField(max_length=200, verbose_name=_("Title"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.MEDIUM, verbose_name=_("Priority")
    )
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


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField(verbose_name=_("Comment"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author} on {self.ticket}"
