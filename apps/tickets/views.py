import datetime
import json

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.billing.models import Subscription

from .forms import BoardForm, CommentForm, InviteMemberForm, TicketForm
from .models import TICKETS_TRIAL_LENGTH_DAYS, Board, Ticket


def _ensure_subscription(user):
    """No profile data to collect up front - same lazy approach as Invoicing."""
    Subscription.objects.get_or_create(
        user=user,
        product="tickets",
        defaults={
            "trial_ends_at": timezone.localdate()
            + datetime.timedelta(days=TICKETS_TRIAL_LENGTH_DAYS)
        },
    )


def _get_board_or_404(request, pk):
    board = get_object_or_404(Board, pk=pk)
    if not board.is_accessible_by(request.user):
        # Deliberately 404, not 403 - don't reveal a board exists to non-members.
        raise Http404
    return board


@login_required
def board_list(request):
    _ensure_subscription(request.user)
    boards = Board.objects.filter(
        Q(owner=request.user) | Q(memberships__user=request.user)
    ).distinct()
    return render(request, "tickets/board_list.html", {"boards": boards})


@login_required
def board_create(request):
    if request.method == "POST":
        form = BoardForm(request.POST)
        if form.is_valid():
            board = form.save(commit=False)
            board.owner = request.user
            board.save()
            messages.success(request, _("Board created."))
            return redirect("tickets:board_detail", pk=board.pk)
    else:
        form = BoardForm()
    return render(request, "tickets/board_form.html", {"form": form})


@login_required
def board_detail(request, pk):
    board = _get_board_or_404(request, pk)
    tickets = board.tickets.select_related("assignee", "reporter")
    columns = [
        (status, label, tickets.filter(status=status))
        for status, label in Ticket.Status.choices
    ]
    return render(request, "tickets/board_detail.html", {"board": board, "columns": columns})


@login_required
def board_settings(request, pk):
    board = _get_board_or_404(request, pk)
    if board.owner_id != request.user.id:
        raise Http404

    if request.method == "POST":
        form = InviteMemberForm(request.POST)
        if form.is_valid():
            user_to_invite = get_user_model().objects.get(username=form.cleaned_data["username"])
            if user_to_invite.id == board.owner_id:
                messages.error(request, _("That's already the board owner."))
            else:
                board.memberships.get_or_create(user=user_to_invite)
                messages.success(request, _("Member added."))
            return redirect("tickets:board_settings", pk=board.pk)
    else:
        form = InviteMemberForm()

    return render(
        request,
        "tickets/board_settings.html",
        {"board": board, "form": form, "members": board.memberships.select_related("user")},
    )


@login_required
@require_POST
def board_remove_member(request, pk, membership_pk):
    board = _get_board_or_404(request, pk)
    if board.owner_id != request.user.id:
        raise Http404
    board.memberships.filter(pk=membership_pk).delete()
    messages.success(request, _("Member removed."))
    return redirect("tickets:board_settings", pk=board.pk)


@login_required
@require_POST
def board_delete(request, pk):
    board = _get_board_or_404(request, pk)
    if board.owner_id != request.user.id:
        raise Http404
    board.delete()
    messages.success(request, _("Board deleted."))
    return redirect("tickets:board_list")


@login_required
def ticket_create(request, pk):
    board = _get_board_or_404(request, pk)
    if request.method == "POST":
        form = TicketForm(request.POST, board=board)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.board = board
            ticket.reporter = request.user
            ticket.save()
            messages.success(request, _("Ticket created."))
            return redirect("tickets:board_detail", pk=board.pk)
    else:
        form = TicketForm(board=board)
    return render(request, "tickets/ticket_form.html", {"form": form, "board": board})


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket.objects.select_related("board", "assignee", "reporter"), pk=pk)
    if not ticket.board.is_accessible_by(request.user):
        raise Http404

    if request.method == "POST":
        if "add_comment" in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.ticket = ticket
                comment.author = request.user
                comment.save()
                messages.success(request, _("Comment added."))
                return redirect("tickets:ticket_detail", pk=ticket.pk)
            edit_form = TicketForm(instance=ticket, board=ticket.board)
        else:
            edit_form = TicketForm(request.POST, instance=ticket, board=ticket.board)
            if edit_form.is_valid():
                edit_form.save()
                messages.success(request, _("Ticket updated."))
                return redirect("tickets:ticket_detail", pk=ticket.pk)
            comment_form = CommentForm()
    else:
        edit_form = TicketForm(instance=ticket, board=ticket.board)
        comment_form = CommentForm()

    context = {
        "ticket": ticket,
        "board": ticket.board,
        "edit_form": edit_form,
        "comment_form": comment_form,
        "comments": ticket.comments.select_related("author"),
    }
    return render(request, "tickets/ticket_detail.html", context)


@login_required
@require_POST
def ticket_move(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if not ticket.board.is_accessible_by(request.user):
        raise Http404

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return HttpResponseBadRequest("Invalid JSON")

    new_status = data.get("status")
    if new_status not in Ticket.Status.values:
        return HttpResponseBadRequest("Invalid status")

    ticket.status = new_status
    ticket.save(update_fields=["status", "updated_at"])
    return JsonResponse({"ok": True})
