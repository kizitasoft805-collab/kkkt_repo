from django.urls import path
from .views import (
    secretary_sacraments_home, secretary_baptized_members, secretary_add_baptism_members,
    secretary_add_communion_members, secretary_first_communion_members, secretary_confirmation_members,
    secretary_add_confirmation_members, secretary_update_baptized_member, secretary_delete_baptized_member,
    secretary_marriage_list_view, secretary_update_marriage, secretary_delete_marriage,
    parish_council_secretary_details
)
from . import views

urlpatterns = [
    # Sacraments URLs (unchanged)
    path('secretary/sacraments/', secretary_sacraments_home, name='secretary_sacraments_home'),
    path("secretary-baptized-members/", secretary_baptized_members, name="secretary_baptized_members"),
    path("secretary-add-baptism-members/", secretary_add_baptism_members, name="secretary_add_baptism_members"),
    path("secretary/sacraments/first-communion-members/", secretary_first_communion_members, name="secretary_communion_members"),
    path("secretary/sacraments/add-communion-members/", secretary_add_communion_members, name="secretary_add_communion_members"),
    path("secretary/sacraments/confirmed-members/", secretary_confirmation_members, name="secretary_confirmed_members"),
    path("secretary/sacraments/add-confirmation-members/", secretary_add_confirmation_members, name="secretary_add_confirmation_members"),
    path("secretary/baptized-members/update/<int:member_id>/", secretary_update_baptized_member, name="secretary_update_baptized_member"),
    path("secretary-baptized-members/delete/<int:member_id>/", secretary_delete_baptized_member, name="secretary_delete_baptized_member"),
    path("secretary-communion-members/update/<int:member_id>/", views.secretary_update_communion_member, name="secretary_update_communion_member"),
    path("secretary-communion-members/delete/<int:member_id>/", views.secretary_delete_communion_member, name="secretary_delete_communion_member"),
    path("secretary-confirmation-members/update/<int:member_id>/", views.secretary_update_confirmation_member, name="secretary_update_confirmation_member"),
    path("secretary-confirmation-members/delete/<int:member_id>/", views.secretary_delete_confirmation_member, name="secretary_delete_confirmation_member"),
    path("secretary/marriages/create/", views.secretary_create_marriage, name="secretary_create_marriage"),
    path('secretary/marriages/list/', secretary_marriage_list_view, name='secretary_marriage_list'),
    path("secretary/marriages/update/<int:member_id>/", secretary_update_marriage, name="secretary_update_marriage"),
    path("secretary/marriages/delete/<int:member_id>/", secretary_delete_marriage, name="secretary_delete_marriage"),

    # Properties URLs (unchanged)
    path('secretary/properties/', views.secretary_properties_home, name='secretary_properties_home'),
    path('secretary-create-assets/', views.secretary_create_church_assets, name='secretary_create_church_assets'),
    path('secretary-upload-assets-media/', views.secretary_upload_church_asset_media, name='secretary_upload_church_asset_media'),
    path('secretary-church-assets/', views.secretary_church_assets_view, name='secretary_church_assets_list'),
    path('secretary-church-assets/update/<int:asset_id>/', views.secretary_update_church_asset, name='secretary_update_church_asset'),
    path('secretary-church-assets/detail/<int:asset_id>/', views.secretary_church_asset_detail, name='secretary_church_asset_detail'),
    path('secretary-church-assets/delete/<int:asset_id>/', views.secretary_delete_church_asset, name='secretary_delete_church_asset'),
    path('secretary-delete-media/<int:media_id>/', views.secretary_delete_church_asset_media, name='secretary_delete_church_asset_media'),
    path('secretary-church-assets/<int:asset_id>/upload-additional-media/', views.secretary_upload_additional_church_asset_media, name='secretary_upload_additional_church_asset_media'),

    # Settings URLs (updated for OutStation and Cell)
    path('secretary_create_year/', views.secretary_create_year, name='secretary_create_year'),
    path('secretary_year_list/', views.secretary_year_list, name='secretary_year_list'),
    path('secretary/settings/home/view/', views.secretary_settings_home, name='secretary_settings_home'),
    path('secretary_update_year/<int:pk>/', views.secretary_update_year, name='secretary_update_year'),
    path('secretary_delete_year/<int:pk>/', views.secretary_delete_year, name='secretary_delete_year'),
    path("secretary/outstations/create/", views.secretary_create_or_update_outstation, name="secretary_create_outstation"),  # Updated from zones
    path("secretary/outstations/update/<int:outstation_id>/", views.secretary_create_or_update_outstation, name="secretary_update_outstation"),  # Updated from zones, zone_id → outstation_id
    path("secretary/outstations/list/", views.secretary_outstation_list, name="secretary_outstation_list"),  # Updated from zones
    path("secretary/outstations/delete/<int:outstation_id>/", views.secretary_delete_outstation, name="secretary_delete_outstation"),  # Updated from zones, zone_id → outstation_id
    path("secretary/outstations/detail/<int:pk>/", views.secretary_outstation_detail, name="secretary_outstation_detail"),  # Updated from zones
    path("secretary/cell/create/", views.secretary_create_update_cell, name="secretary_create_cell"),  # Updated from community
    path("secretary/cell/update/<int:cell_id>/", views.secretary_create_update_cell, name="secretary_update_cell"),  # Updated from community, community_id → cell_id
    path("secretary/cells/list/", views.secretary_cell_list, name="secretary_cell_list"),  # Updated from communities
    path("secretary/cell/delete/<int:cell_id>/", views.secretary_delete_cell, name="secretary_delete_cell"),  # Updated from community, community_id → cell_id
    path("secretary/cell/<int:cell_id>/", views.secretary_cell_detail, name="secretary_cell_detail"),  # Updated from community, community_id → cell_id
    path("secretary-set-church-location/", views.secretary_set_church_location, name="secretary_set_church_location"),
    path("secretary-church-map/", views.secretary_location_list, name="secretary_location_list"),
    path("secretary-update-church-location/", views.secretary_update_church_location, name="secretary_update_church_location"),
    path("secretary-church-location/view/", views.secretary_view_church_location, name="secretary_view_church_location"),
    path("secretary-church-location/delete/", views.secretary_delete_church_location, name="secretary_delete_church_location"),

    # Leaders URLs (unchanged)
    path('secretary/leaders/create/', views.secretary_create_or_update_leader, name='secretary_create_leader'),
    path('secretary/leaders/<int:pk>/update/', views.secretary_create_or_update_leader, name='secretary_update_leader'),
    path('secretary/leaders/', views.secretary_leader_list_view, name='secretary_leader_list'),
    path('secretary/inactive/leaders/', views.secretary_inactive_leader_list_view, name='secretary_inactive_leader_list'),
    path('secretary/leaders/<int:pk>/update-profile/', views.secretary_update_leader_profile, name='secretary_update_leader_profile'),
    path('secretary/leaders/<int:pk>/delete/', views.secretary_delete_leader, name='secretary_delete_leader'),
    path('secretary/leaders/<int:pk>/detail/', views.secretary_leader_detail_view, name='secretary_leader_detail'),
    path('secretary/leaders/home/', views.secretary_leaders_home, name='secretary_leaders_home'),

    # Members URLs (unchanged)
    path('secretary/member/create/', views.secretary_create_or_update_church_member, name='secretary_create_church_member'),
    path('secretary/members/home/view/', views.secretary_members_home, name='secretary_members_home'),
    path('secretary/members/list/', views.secretary_church_member_list, name='secretary_church_member_list'),
    path('secretary/inactive/members/list/', views.secretary_inactive_church_member_list, name='secretary_inactive_church_member_list'),
    path('secretary/members/delete/<int:pk>/', views.secretary_delete_church_member, name='secretary_delete_church_member'),
    path('secretary/members/update/<int:pk>/', views.secretary_update_church_member, name='secretary_update_church_member'),
    path('secretary/members/<int:pk>/upload-passport/', views.secretary_upload_passport, name='secretary_upload_passport'),
    path('secretary/members/<int:pk>/detail/', views.secretary_church_member_detail, name='secretary_church_member_detail'),

    # News URLs (unchanged)
    path('secretary/create/news/', views.secretary_create_news_view, name='secretary_create_news'),
    path('secretary/news/list/', views.secretary_news_list_view, name='secretary_news_list'),
    path("secretary/news/<int:pk>/", views.secretary_news_detail_view, name="secretary_news_detail"),
    path("secretary/news/<int:pk>/delete/", views.secretary_delete_news_view, name="secretary_delete_news"),
    path("secretary/news/<int:pk>/edit/", views.secretary_create_news_view, name="secretary_edit_news"),
    path('secretary/home/news/', views.secretary_news_home, name='secretary_news_home'),

    # Notifications URLs (unchanged)
    path('secretary/notifications/', views.secretary_notifications_home, name='secretary_notifications_home'),
    path("secretary/notifications/create/", views.secretary_create_notification, name="secretary_create_notification"),
    path("load_recipients/", views.load_recipients, name="load_recipients"),
    path("secretary/notifications/list/", views.secretary_notification_list, name="secretary_notification_list"),
    path("secretary/notifications/delete/<str:delete_type>/<str:identifier>/", views.secretary_delete_notification, name="secretary_delete_notification"),

    # Details URLs (unchanged)
    path('secretary/details/', parish_council_secretary_details, name='parish_council_secretary_details'),
]