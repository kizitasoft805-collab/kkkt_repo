from django.urls import path
from .views import create_or_update_leader, leader_list_view, leader_detail_view

from . import views

urlpatterns = [
    path('leaders/create/', create_or_update_leader, name='create_leader'),
    path('leaders/<int:pk>/update/', create_or_update_leader, name='update_leader'),
    path('leaders/', leader_list_view, name='leader_list'),
    path('inactive/leaders/', views.inactive_leader_list_view, name='inactive_leader_list'),
    path('leaders/<int:pk>/update-profile/', views.update_leader_profile, name='update_leader_profile'),
    path('leaders/<int:pk>/delete/', views.delete_leader, name='delete_leader'),
    path('leaders/<int:pk>/detail/', leader_detail_view, name='leader_detail'),
    path('leaders/home/', views.leaders_home, name='leaders_home'),  # New Leaders Home Page
]
