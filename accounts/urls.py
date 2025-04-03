# accounts/urls.py

from django.urls import path
from .views import (
    login_view,
    admin_dashboard,
    secretary_dashboard,
    accountant_dashboard,
    member_dashboard,
    upload_profile_picture,
    remove_profile_picture,
    member_upload_profile_picture,
    member_remove_profile_picture,
    superuser_detail_view,
    admin_update_view,
    logout_view,
    request_account,
    forgot_password
)

from . import views

urlpatterns = [
    path('welcome/page/', views.welcome_page, name='welcome'),  # Welcome Page
    path('login/', login_view, name='login'),
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    path('upload_profile_picture/', upload_profile_picture, name='upload_profile_picture'),
    path('members_upload_profile_picture/', member_upload_profile_picture, name='member_upload_profile_picture'),
    path('accountant_upload_profile_picture/', views.accountant_upload_profile_picture, name='accountant_upload_profile_picture'),
    path('secretary_upload_profile_picture/', views.secretary_upload_profile_picture, name='secretary_upload_profile_picture'),
    path('secretary_dashboard/', secretary_dashboard, name='secretary_dashboard'),
    path('accountant_dashboard/', accountant_dashboard, name='accountant_dashboard'),
    path('member_dashboard/', member_dashboard, name='member_dashboard'),
    path('remove_profile_picture/', remove_profile_picture, name='remove_profile_picture'),
    path('member_remove_profile_picture/', member_remove_profile_picture, name='member_remove_profile_picture'),
    path("superuser/detail/", superuser_detail_view, name="superuser_detail"),
    path('admin/update/', admin_update_view, name='admin_update'),
    path('logout/', logout_view, name='logout'),
    path("request-account/", request_account, name="request_account"),
    path("forgot-password/", forgot_password, name="forgot_password"),
    path('pastor_dashboard/', views.pastor_dashboard, name='pastor_dashboard'),
    path('pastor_upload_profile_picture/', views.pastor_upload_profile_picture, name='pastor_upload_profile_picture'),
    path('evangelist_dashboard/', views.evangelist_dashboard, name='evangelist_dashboard'),
    path('evangelist_upload_profile_picture/', views.evangelist_upload_profile_picture, name='evangelist_upload_profile_picture'),
]
