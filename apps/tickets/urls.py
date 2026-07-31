from django.urls import path

from . import views

app_name = "tickets"

urlpatterns = [
    path("", views.board_list, name="board_list"),
    path("boards/new/", views.board_create, name="board_create"),
    path("boards/<int:pk>/", views.board_detail, name="board_detail"),
    path("boards/<int:pk>/calendar/", views.board_calendar, name="board_calendar"),
    path("boards/<int:pk>/settings/", views.board_settings, name="board_settings"),
    path("boards/<int:pk>/tags/new/", views.tag_create, name="tag_create"),
    path("boards/<int:pk>/tags/<int:tag_pk>/delete/", views.tag_delete, name="tag_delete"),
    path(
        "boards/<int:pk>/members/<int:membership_pk>/remove/",
        views.board_remove_member,
        name="board_remove_member",
    ),
    path("boards/<int:pk>/delete/", views.board_delete, name="board_delete"),
    path("boards/<int:pk>/tickets/new/", views.ticket_create, name="ticket_create"),
    path("tickets/<int:pk>/", views.ticket_detail, name="ticket_detail"),
    path("tickets/<int:pk>/move/", views.ticket_move, name="ticket_move"),
]
