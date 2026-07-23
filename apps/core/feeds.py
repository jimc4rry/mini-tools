from django.conf import settings
from django.contrib.syndication.views import Feed

from apps.docs.models import Document
from apps.tools.models import Tool


class ChangelogFeed(Feed):
    """
    A single feed mixing newly published Documents and newly added Tools,
    so external automation (Zapier/Make -> social media) can watch one URL
    instead of polling the admin.
    """

    title = "Minitools Hub — Changelog"
    description = "New free mini-tools and support documents, as they're published."

    def link(self):
        return f"{settings.SITE_URL}/"

    def items(self):
        docs = Document.objects.filter(is_published=True)
        tools = Tool.objects.filter(is_active=True)
        combined = sorted(
            [*docs, *tools],
            key=lambda obj: obj.updated_at if isinstance(obj, Document) else obj.created_at,
            reverse=True,
        )
        return combined[:30]

    def item_title(self, item):
        if isinstance(item, Document):
            return item.title
        return item.name

    def item_description(self, item):
        if isinstance(item, Document):
            return item.summary or "Updated support document."
        return item.description or "New free mini-tool."

    def item_link(self, item):
        return f"{settings.SITE_URL}{item.get_absolute_url()}"

    def item_pubdate(self, item):
        return item.updated_at if isinstance(item, Document) else item.created_at
