from django.urls import path

from . import cbv_views

# app_name gives these URLs a namespace, so they're reversed as "cbv:list", "cbv:detail", ...
app_name = 'cbv'

urlpatterns = [
    path('', cbv_views.RecordListView.as_view(), name='list'),
    path('add/', cbv_views.RecordCreateView.as_view(), name='add'),
    path('<int:pk>/', cbv_views.RecordDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', cbv_views.RecordUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', cbv_views.RecordDeleteView.as_view(), name='delete'),
]
