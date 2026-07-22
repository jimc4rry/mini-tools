from django.db import models
from django.urls import NoReverseMatch, reverse


class Project(models.Model):
    """
    Groups documents under the external project/app they belong to
    (e.g. a Jira Marketplace app), shown in the left sidebar on doc pages.
    """

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(
        blank=True, help_text="Markdown supported. Shown at the top of the project's page."
    )
    url_name = models.CharField(
        max_length=200,
        blank=True,
        help_text=(
            "Named URL of the project's own app, if it's hosted inside this "
            "Django project (e.g. 'dashboard'). Shown as an 'Open' link on "
            "the project's page. Leave blank for doc-only projects, or use "
            "external_url instead for an app hosted elsewhere."
        ),
    )
    external_url = models.URLField(
        blank=True,
        help_text=(
            "Full URL of the app, if it's hosted on its own separate site "
            "(e.g. https://getmenuhub.com/) rather than inside this Django "
            "project. Takes priority over url_name for the 'Open' link."
        ),
    )
    is_public = models.BooleanField(
        default=True,
        help_text=(
            "Whether this project is shown in the sidebar and browsable via "
            "its project page. Turn off while a project isn't ready to be "
            "publicly listed yet — its individual documents stay reachable "
            "by direct link regardless, since those are what get shared "
            "externally (e.g. submitted to a marketplace listing)."
        ),
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Application"
        verbose_name_plural = "Applications"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("project_detail", args=[self.slug])

    def get_app_url(self):
        if self.external_url:
            return self.external_url
        if not self.url_name:
            return ""
        try:
            return reverse(self.url_name)
        except NoReverseMatch:
            return ""


class Document(models.Model):
    """
    A support/policy document that gets linked to from other systems (Jira, etc.).
    The slug is the public identifier — never repurpose or delete one that has
    already been shared externally, since that breaks every link pointing at it.
    """

    title = models.CharField(max_length=200)
    slug = models.SlugField(
        unique=True,
        help_text="Used in the public URL. Treat as permanent once shared externally.",
    )
    project = models.ForeignKey(
        Project, on_delete=models.PROTECT, related_name="documents", null=True, blank=True
    )
    summary = models.CharField(max_length=300, blank=True)
    body = models.TextField(help_text="Markdown is supported.")
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("docs:detail", args=[self.slug])
