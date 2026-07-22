from django.shortcuts import get_object_or_404, render

from .models import Document


def document_list(request):
    documents = Document.objects.filter(is_published=True).select_related("category")
    return render(request, "docs/list.html", {"documents": documents})


def document_detail(request, slug):
    document = get_object_or_404(Document, slug=slug, is_published=True)
    return render(request, "docs/detail.html", {"document": document})
