from django.urls import path
from .views import sacraments_home, baptized_members, add_baptism_members, add_communion_members, first_communion_members, confirmation_members, add_confirmation_members, update_baptized_member, delete_baptized_member, marriage_list_view, update_marriage, delete_marriage

from . import views

urlpatterns = [
    path('sacraments/', sacraments_home, name='sacraments_home'),
    path("baptized-members/", baptized_members, name="baptized_members"),
    path("add-baptism-members/", add_baptism_members, name="add_baptism_members"),
    path("sacraments/confirmed-members/", confirmation_members, name="confirmed_members"),
    path("sacraments/add-confirmation-members/", add_confirmation_members, name="add_confirmation_members"),
    path("baptized-members/update/<int:member_id>/", update_baptized_member, name="update_baptized_member"),
    path("baptized-members/delete/<int:member_id>/", delete_baptized_member, name="delete_baptized_member"),
    path("communion-members/update/<int:member_id>/", views.update_communion_member, name="update_communion_member"),
    path("communion-members/delete/<int:member_id>/", views.delete_communion_member, name="delete_communion_member"),
    path("confirmation-members/update/<int:member_id>/", views.update_confirmation_member, name="update_confirmation_member"),
    path("confirmation-members/delete/<int:member_id>/", views.delete_confirmation_member, name="delete_confirmation_member"),
    path("marriages/create/", views.create_marriage, name="create_marriage"),
    path('marriages/list/', marriage_list_view, name='marriage_list'),
    path("marriages/update/<int:member_id>/", update_marriage, name="update_marriage"),
    path("marriages/delete/<int:member_id>/", delete_marriage, name="delete_marriage"),
]

