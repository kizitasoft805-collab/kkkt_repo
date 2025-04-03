from django.urls import path

from .views import load_recipients, parish_treasurer_details

from . import views

urlpatterns = [
    # finance urls
    path('accountant/finance/', views.accountant_finance_home, name='accountant_finance_home'),
    path('accountant/offerings/create/', views.AccountantOfferingsCreateView.as_view(), name='accountant_offerings_create'),
    path('accountant/offerings/list/', views.AccountantOfferingsListView.as_view(), name='accountant_offerings_list'),
    path('accountant/offerings/update/<int:pk>/', views.AccountantOfferingsUpdateView.as_view(), name='accountant_offerings_update'),
    path('accountant/offerings/delete/<int:pk>/', views.AccountantOfferingsDeleteView.as_view(), name='accountant_offerings_delete'),
    path('accountant/tithes/create/', views.accountant_create_multiple_tithes, name='accountant_create_tithe'),
    path('accountant/tithes/update/<int:tithe_id>/', views.accountant_create_or_update_tithe, name='accountant_update_tithe'),
    path('accountant/tithes/', views.accountant_tithe_list, name='accountant_tithe_list'),
    path('accountant/tithes/delete/<int:tithe_id>/', views.accountant_delete_tithe, name='accountant_delete_tithe'),
    path('accountant-facility-renting/create/', views.accountant_facility_renting_create, name='accountant_facility_renting_create'),
    path('accountant-facility-renting/<int:pk>/update/', views.accountant_facility_renting_update, name='accountant_facility_renting_update'),
    path('accountant/facility-renting/list/', views.accountant_facility_renting_list, name='accountant_facility_renting_list'),
    path('accountant-facility-renting/delete/<int:pk>/', views.accountant_facility_renting_delete, name='accountant_facility_renting_delete'),
    path('accountant-special-contributions/create/', views.accountant_special_contribution_form, name='accountant_special_contribution_create'),
    path('accountant-special-contributions/<int:pk>/edit/', views.accountant_special_contribution_form, name='accountant_special_contribution_update'),
    path('accountant-special-contributions/<int:pk>/delete/', views.accountant_special_contribution_delete, name='accountant_special_contribution_delete'),
    path('accountant-special-contributions/list/', views.accountant_special_contribution_list, name='accountant_special_contribution_list'),
    path('accountant-special-contributions/<int:contribution_id>/donation-item-fund/new/', 
         views.accountant_donation_item_fund_form, 
         name='accountant_donation_item_fund_create'),

    path('accountant-special-contributions/<int:contribution_id>/donation-item-fund/<int:pk>/edit/', 
         views.accountant_donation_item_fund_form, 
         name='accountant_donation_item_fund_update'),
    path('accountant-special-contributions/<int:contribution_id>/donation-item-funds/', 
         views.accountant_donation_item_fund_list, 
         name='accountant_donation_item_fund_list'),
    path('accountant-special-contributions/<int:contribution_id>/donation-item-fund/<int:pk>/delete/', 
         views.accountant_donation_item_fund_delete, 
         name='accountant_donation_item_fund_delete'),
    path('accountant-donation-item-funds/all/', views.accountant_all_donation_item_funds, name='accountant_all_donation_item_funds'),

    # properties urls
    path('accountant/properties/', views.accountant_properties_home, name='accountant_properties_home'),
    path('accountant-create-assets/', views.accountant_create_church_assets, name='accountant_create_church_assets'),
    path('accountant-upload-assets-media/', views.accountant_upload_church_asset_media, name='accountant_upload_church_asset_media'),
    path('accountant-church-assets/', views.accountant_church_assets_view, name='accountant_church_assets_list'),
    path('accountant-church-assets/update/<int:asset_id>/', views.accountant_update_church_asset, name='accountant_update_church_asset'),
    path('accountant-church-assets/detail/<int:asset_id>/', views.accountant_church_asset_detail, name='accountant_church_asset_detail'),
    path('accountant_church-assets/delete/<int:asset_id>/', views.accountant_delete_church_asset, name='accountant_delete_church_asset'),
    path('accountant-delete-media/<int:media_id>/', views.accountant_delete_church_asset_media, name='accountant_delete_church_asset_media'),
    path('accountant-church-assets/<int:asset_id>/upload-additional-media/', views.accountant_upload_additional_church_asset_media, name='accountant_upload_additional_church_asset_media'),


    # News urls
    path('accountant/create/news/', views.accountant_create_news_view, name='accountant_create_news'),
    path('accountant/news/list/', views.accountant_news_list_view, name='accountant_news_list'),
    path("accountant/news/<int:pk>/", views.accountant_news_detail_view, name="accountant_news_detail"),
    path("accountant/news/<int:pk>/delete/", views.accountant_delete_news_view, name="accountant_delete_news"),
    path("accountant/news/<int:pk>/edit/", views.accountant_create_news_view, name="accountant_edit_news"),
    path('accountant/home/news/', views.accountant_news_home, name='accountant_news_home'),


    # Notifications url
    path('accountant/notifications/', views.accountant_notifications_home, name='accountant_notifications_home'),
    path("accountant/notifications/create/", views.accountant_create_notification, name="accountant_create_notification"),
    path("load_recipients/", load_recipients, name="load_recipients"),
    path("accountant/notifications/list/", views.accountant_notification_list, name="accountant_notification_list"),
    # Confirm and delete group notifications
    path("accountant/notifications/delete/<str:delete_type>/<str:identifier>/", views.accountant_delete_notification, name="accountant_delete_notification"),

    # Details urls
    path('treasurer/details/', parish_treasurer_details, name='parish_treasurer_details'),
]
