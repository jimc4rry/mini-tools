from django.shortcuts import get_object_or_404, render

from .models import Document, Project


def document_list(request):
    documents = Document.objects.filter(is_published=True).select_related("project")
    context = {
        "documents": documents,
        "all_projects": Project.objects.all(),
        "current_project": None,
    }
    return render(request, "docs/list.html", context)


def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug)
    documents = project.documents.filter(is_published=True)
    context = {
        "project": project,
        "documents": documents,
        "all_projects": Project.objects.all(),
        "current_project": project,
    }
    return render(request, "docs/project_detail.html", context)


def document_detail(request, slug):
    document = get_object_or_404(Document, slug=slug, is_published=True)
    context = {
        "document": document,
        "all_projects": Project.objects.all(),
        "current_project": document.project,
    }
    return render(request, "docs/detail.html", context)
