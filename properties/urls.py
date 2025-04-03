from django.urls import path
from .views import properties_home, delete_church_asset_media

from . import views


urlpatterns = [
    path('properties/', properties_home, name='properties_home'),
    path('create-assets/', views.create_church_assets, name='create_church_assets'),
    path('upload-assets-media/', views.upload_church_asset_media, name='upload_church_asset_media'),
    path('church-assets/', views.church_assets_view, name='church_assets_list'),
    path('church-assets/update/<int:asset_id>/', views.update_church_asset, name='update_church_asset'),
    path('church-assets/detail/<int:asset_id>/', views.church_asset_detail, name='church_asset_detail'),
    path('church-assets/delete/<int:asset_id>/', views.delete_church_asset, name='delete_church_asset'),
    path('delete-media/<int:media_id>/', delete_church_asset_media, name='delete_church_asset_media'),
    path('church-assets/<int:asset_id>/upload-additional-media/', views.upload_additional_church_asset_media, name='upload_additional_church_asset_media'),
]
