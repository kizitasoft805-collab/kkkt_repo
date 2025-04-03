from django.urls import path
from .views import logged_member_details

from . import views

urlpatterns = [
    path('member/details/', logged_member_details, name="logged_member_details"),
    path('member/create/news/', views.member_create_news_view, name='member_create_news'),
    path('member/news/list/', views.member_news_list_view, name='member_news_list'),
    path("member/news/<int:pk>/", views.member_news_detail_view, name="member_news_detail"),
    path("member/news/<int:pk>/delete/", views.member_delete_news_view, name="member_delete_news"),
    path("member/news/<int:pk>/edit/", views.member_create_news_view, name="member_edit_news"),
    path('member/notifications/', views.member_notifications_view, name='member_notifications'),  # 🚀 New URL for Notifications
    path('member/tithes/', views.member_tithes_view, name='member_tithes'),
    path('help/chatbot/', views.chatbot_view, name='chatbot'),
    path('public/help/chatbot/', views.public_chatbot_view, name='public_chatbot'),
    path('admin/help/chatbot/', views.admin_chatbot_view, name='admin_chatbot'),
    path('secretary/help/chatbot/', views.secretary_chatbot_view, name='secretary_chatbot'),
    path('accountant/help/chatbot/', views.accountant_chatbot_view, name='accountant_chatbot'),
    path("member/pledge/create/", views.member_pledge_create_view, name="member_pledge_create"),
    path("member/pledge/list/", views.member_pledge_list_view, name="member_pledge_list"),
]
