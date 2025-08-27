from django.urls import path
from .views import finance_home, OfferingsCreateByCategoryView, OfferingsListView, OfferingsUpdateByCategoryView, OfferingsDeleteView


from .views import pledge_create_view

from . import views

urlpatterns = [
    path('finance/', finance_home, name='finance_home'),
    path('offering/category/<int:cat_pk>/create/', OfferingsCreateByCategoryView.as_view(), name='offering_create_by_category'),    
    path('offerings/list/', OfferingsListView.as_view(), name='offerings_list'),
    path('offering/category/<int:cat_pk>/update/<int:pk>/', OfferingsUpdateByCategoryView.as_view(), name='offerings_update_by_category'),
    path('offerings/delete/<int:pk>/', OfferingsDeleteView.as_view(), name='offerings_delete'),
    path('facility-renting/create/', views.facility_renting_create, name='facility_renting_create'),
    path('facility-renting/<int:pk>/update/', views.facility_renting_update, name='facility_renting_update'),
    path('facility-renting/list/', views.facility_renting_list, name='facility_renting_list'),
    path('facility-renting/delete/<int:pk>/', views.facility_renting_delete, name='facility_renting_delete'),
    path('special-contributions/create/', views.special_contribution_form, name='special_contribution_create'),
    path('special-contributions/<int:pk>/edit/', views.special_contribution_form, name='special_contribution_update'),
    path('special-contributions/<int:pk>/delete/', views.special_contribution_delete, name='special_contribution_delete'),
    path('special-contributions/list/', views.special_contribution_list, name='special_contribution_list'),
    path('special-contributions/<int:contribution_id>/donation-item-fund/new/', 
         views.donation_item_fund_form, 
         name='donation_item_fund_create'),

    path('special-contributions/<int:contribution_id>/donation-item-fund/<int:pk>/edit/', 
         views.donation_item_fund_form, 
         name='donation_item_fund_update'),
    path('special-contributions/<int:contribution_id>/donation-item-funds/', 
         views.donation_item_fund_list, 
         name='donation_item_fund_list'),
    path('special-contributions/<int:contribution_id>/donation-item-fund/<int:pk>/delete/', 
         views.donation_item_fund_delete, 
         name='donation_item_fund_delete'),
    path('donation-item-funds/all/', views.all_donation_item_funds, name='all_donation_item_funds'),
    path("pledge/create/", pledge_create_view, name="pledge_create"),
    path("pledge/update/<int:pk>/", pledge_create_view, name="pledge_update"),
    path('pledges/list/', views.pledge_list_view, name='pledge_list'),
    path("pledge/delete/<int:pk>/", views.pledge_delete_view, name="pledge_delete"),
    path('category/create/', views.category_create, name='category_create'),
    path('all/category/list/', views.category_list, name='category_list'),
    path('category/<int:pk>/update/', views.category_update, name='category_update'),
    path('category/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('expenditure/<int:category_pk>/create/', views.expenditure_create, name='expenditure_create'),
    path('expenditure/<int:pk>/update/', views.expenditure_update, name='expenditure_update'),
    path('expenditure/all/', views.expenditure_list_all, name='expenditure_list_all'),
    path('expenditure/<int:pk>/delete/', views.expenditure_delete, name='expenditure_delete'),
    path('category/<int:category_pk>/expenditures/', views.category_expenditure_list, name='category_expenditure_list'),
    path('report/general/', views.finance_general_report, name='finance_general_report'),
    path('offering-category/create/', views.offering_category_create, name='offering_category_create'),
    path('offering-category/<int:pk>/update/', views.offering_category_update, name='offering_category_update'),
    path('offering-category/list/', views.offering_category_list, name='offering_category_list'),
    path('offering-category/<int:pk>/delete/', views.offering_category_delete, name='offering_category_delete'),
    path('offering/category/<int:cat_pk>/all/', views.offerings_by_category_list, name='offerings_by_category_list'),
]

