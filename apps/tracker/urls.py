from django.urls import path

from . import views
from .billing import paddle_webhook

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('signup/', views.signup, name='signup'),
    path('items/new/', views.item_create, name='item_create'),
    path('items/<int:pk>/edit/', views.item_edit, name='item_edit'),
    path('items/<int:pk>/delete/', views.item_delete, name='item_delete'),
    path('items/<int:pk>/consume/', views.item_consume, name='item_consume'),
    path('items/<int:pk>/waste/', views.item_waste, name='item_waste'),
    path('waste-log/', views.waste_log, name='waste_log'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('api/barcode-lookup/', views.barcode_lookup, name='barcode_lookup'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('settings/', views.settings_view, name='settings'),
    path('billing/paddle-webhook/', paddle_webhook, name='paddle_webhook'),
]
