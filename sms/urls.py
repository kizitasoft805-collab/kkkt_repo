from django.urls import path
from .views import sms_status_view, delete_sms, delete_all_sms, secretary_sms_status_view, secretary_delete_sms, secretary_delete_all_sms

urlpatterns = [
    path("sms-status/", sms_status_view, name="sms_status"),
    path("delete-sms/<int:sms_id>/", delete_sms, name="delete_sms"),
    path("delete-all-sms/", delete_all_sms, name="delete_all_sms"),
    path("secretary-sms-status/", secretary_sms_status_view, name="secretary_sms_status"),
    path("secretary-delete-sms/<int:sms_id>/", secretary_delete_sms, name="secretary_delete_sms"),
    path("secretary-delete-all-sms/", secretary_delete_all_sms, name="secretary_delete_all_sms"),
]
