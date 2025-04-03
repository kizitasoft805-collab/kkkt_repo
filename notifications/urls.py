from django.urls import path
from .views import notifications_home, create_notification, load_recipients, notification_list, delete_notification

urlpatterns = [
    path('notifications/', notifications_home, name='notifications_home'),
    path("notifications/create/", create_notification, name="create_notification"),
    path("load_recipients/", load_recipients, name="load_recipients"),
    path("notifications/list/", notification_list, name="notification_list"),
    # Confirm and delete group notifications
    path("notifications/delete/<str:delete_type>/<str:identifier>/", delete_notification, name="delete_notification"),
]
