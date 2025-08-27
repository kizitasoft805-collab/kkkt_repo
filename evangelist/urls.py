# urls.py
from django.urls import path

from . import views

from .views import EvangelistOfferingCategoryListView

from .views import evangelist_report_create

urlpatterns = [
    # Details urls
    path('evangelist/details/', views.evangelist_details, name='evangelist_details'),

    # Leaders urls
    path('evangelist/leaders/', views.evangelist_leader_list_view, name='evangelist_leader_list'),
    path('evangelist/inactive/leaders/', views.evangelist_inactive_leader_list_view, name='evangelist_inactive_leader_list'),
    path('evangelist/leaders/<int:pk>/detail/', views.evangelist_leader_detail_view, name='evangelist_leader_detail'),
    path('evangelist/leaders/home/', views.evangelist_leaders_home, name='evangelist_leaders_home'),  # New Leaders Home Page

    # Members urls
    path('evangelist/members/home/view/', views.evangelist_members_home, name='evangelist_members_home'),  # New Home Page
    path('evangelist/members/list/', views.evangelist_church_member_list, name='evangelist_church_member_list'),
    path('evangelist/inactive/members/list/', views.evangelist_inactive_church_member_list, name='evangelist_inactive_church_member_list'),
    path('evangelist/members/<int:pk>/detail/', views.evangelist_church_member_detail, name='evangelist_church_member_detail'),

    # Chatbot url
    path('help/chatbot/evangelist', views.evangelist_chatbot_view, name='evangelist_chatbot'),

    path('evangelist/create/news/', views.evangelist_create_news_view, name='evangelist_create_news'),
    path('evangelist/news/list/', views.evangelist_news_list_view, name='evangelist_news_list'),
    path("evangelist/news/<int:pk>/", views.evangelist_news_detail_view, name="evangelist_news_detail"),
    path("evangelist/news/<int:pk>/delete/", views.evangelist_delete_news_view, name="evangelist_delete_news"),
    path("evangelist/news/<int:pk>/edit/", views.evangelist_create_news_view, name="evangelist_edit_news"),
    path('evangelist/home/news/', views.evangelist_news_home, name='evangelist_news_home'),
    path('evangelist/notifications/', views.evangelist_notifications_view, name='evangelist_notifications'),  # 🚀 New URL for Notifications
    path(
        "evangelist-offering-categories/",
        EvangelistOfferingCategoryListView.as_view(),
        name="evangelist_offering_category_list",
    ),

    path(
        "evangelist-report/create/",
        evangelist_report_create,
        name="evangelist_report_create",
    ),
]
