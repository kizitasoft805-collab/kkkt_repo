# settings/urls.py

from django.urls import path
from .views import create_year, year_list, update_year, delete_year, set_church_location, location_list, update_church_location, view_church_location, delete_church_location

from . import views

urlpatterns = [
    path('create_year/', create_year, name='create_year'),
    path('year_list/', year_list, name='year_list'),
    path('settings/home/view/', views.settings_home, name='settings_home'),
    path('update_year/<int:pk>/', update_year, name='update_year'),
    path('delete_year/<int:pk>/', delete_year, name='delete_year'),
    path("outstations/create/", views.create_or_update_outstation, name="create_outstation"),  # Changed from zones/create/
    path("outstations/update/<int:outstation_id>/", views.create_or_update_outstation, name="update_outstation"),  # Changed from zones/update/
    path("outstations/list/", views.outstation_list, name="outstation_list"),  # Changed from zones/list/
    path("outstations/delete/<int:outstation_id>/", views.delete_outstation, name="delete_outstation"),  # Changed from zones/delete/
    path("outstations/detail/<int:pk>/", views.outstation_detail, name="outstation_detail"),  # Changed from zones/detail/
    path("cells/create/", views.create_update_cell, name="create_cell"),  # Changed from community/create/
    path("cells/update/<int:cell_id>/", views.create_update_cell, name="update_cell"),  # Changed from community/update/
    path("cells/list/", views.cell_list, name="cell_list"),  # Changed from communities/list/
    path("cells/delete/<int:cell_id>/", views.delete_cell, name="delete_cell"),  # Changed from community/delete/
    path("cells/detail/<int:cell_id>/", views.cell_detail, name="cell_detail"),  # Changed from community/<int:community_id>/
    path("set-church-location/", set_church_location, name="set_church_location"),
    path("church-map/", location_list, name="location_list"),
    path("update-church-location/", update_church_location, name="update_church_location"),
    path("church-location/view/", view_church_location, name="view_church_location"),
    path("church-location/delete/", delete_church_location, name="delete_church_location"),
]