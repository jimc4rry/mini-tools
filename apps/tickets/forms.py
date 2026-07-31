from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import Board, Comment, Ticket

User = get_user_model()


class BoardForm(forms.ModelForm):
    class Meta:
        model = Board
        fields = ["name"]


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["title", "description", "priority", "assignee"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, board=None, **kwargs):
        super().__init__(*args, **kwargs)
        if board is not None:
            member_ids = list(board.memberships.values_list("user_id", flat=True))
            member_ids.append(board.owner_id)
            self.fields["assignee"].queryset = User.objects.filter(id__in=member_ids)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 2, "placeholder": _("Add a comment...")})}


class InviteMemberForm(forms.Form):
    username = forms.CharField(label=_("Username"))

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if not User.objects.filter(username=username).exists():
            raise forms.ValidationError(_("No account with that username."))
        return username
