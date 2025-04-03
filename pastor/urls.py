# urls.py
from django.urls import path

from . import views

urlpatterns = [
    # Details urls
    path('pastor/details/', views.pastor_details, name='pastor_details'),

    # Leaders urls
    path('pastor/leaders/', views.pastor_leader_list_view, name='pastor_leader_list'),
    path('pastor/inactive/leaders/', views.pastor_inactive_leader_list_view, name='pastor_inactive_leader_list'),
    path('secretary/leaders/<int:pk>/detail/', views.pastor_leader_detail_view, name='pastor_leader_detail'),
    path('pastor/leaders/home/', views.pastor_leaders_home, name='pastor_leaders_home'),  # New Leaders Home Page

    # Members urls
    path('pastor/members/home/view/', views.pastor_members_home, name='pastor_members_home'),  # New Home Page
    path('pastor/members/list/', views.pastor_church_member_list, name='pastor_church_member_list'),
    path('pastor/inactive/members/list/', views.pastor_inactive_church_member_list, name='pastor_inactive_church_member_list'),
    path('pastor/members/<int:pk>/detail/', views.pastor_church_member_detail, name='pastor_church_member_detail'),

    # Chatbot url
    path('help/chatbot/pastor', views.pastor_chatbot_view, name='pastor_chatbot'),

    # Existing report route example (function-based)
    path('report/pastor', views.pastor_report, name='pastor_report'),

    # ----------------------------------------------------
    # NEW PastorReport CREATE & DETAIL Routes
    # ----------------------------------------------------
    path('report/pastor/create/', views.PastorReportCreateView.as_view(), name='pastor_report_create'),


    path('reports/all/', views.all_reports, name='all_reports'),

    path('pastor/report/<int:pk>/', views.pastor_report_detail, name='pastor_report_detail'),

    path('report/pastor/<int:pk>/edit/', views.PastorReportCreateView.as_view(), name='pastor_report_edit'),

    path('pastor/report/<int:pk>/delete/', views.pastor_report_delete, name='pastor_report_delete'),
]
