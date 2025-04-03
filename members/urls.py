# members/urls.py

from django.urls import path
from .views import create_or_update_church_member, church_member_list, update_church_member
from . import views

urlpatterns = [
    path('create/', create_or_update_church_member, name='create_church_member'),
    path('leader/create/<int:member_id>/', views.create_leader_from_member, name='create_leader_from_member'),
    path('members/home/view/', views.members_home, name='members_home'),  # New Home Page
    path('list/', church_member_list, name='church_member_list'),
    path('inactive/list/', views.inactive_church_member_list, name='inactive_church_member_list'),
    path('delete/<int:pk>/', views.delete_church_member, name='delete_church_member'),
    path('update/<int:pk>/', update_church_member, name='update_church_member'),
    path('members/<int:pk>/upload-passport/', views.upload_passport, name='upload_passport'),
    path('members/<int:pk>/detail/', views.church_member_detail, name='church_member_detail'),
    path('church/members/report/', views.church_members_report, name='church_members_report'),
    path('church/members/signup/', views.church_member_signup, name='church_member_signup'),
    path('signup/success/for/any/member/', views.signup_success, name='signup_success'),
    path('<int:member_id>/approve/', views.approve_church_member, name='approve_church_member'),
]
