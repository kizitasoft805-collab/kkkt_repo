from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

# ✅ Helper function to allow only Admins and Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# 🔔 Notifications Home View (Restricted to Admins/Superusers)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def notifications_home(request):
    """
    View for the Notifications Home Page.
    Only accessible to Admins and Superusers.
    """
    return render(request, 'notifications/notifications_home.html')


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Notification
from members.models import ChurchMember
from .forms import NotificationForm
from sms.utils import send_sms  # ✅ Import Beem SMS function

# ✅ Helper function to allow only Admins and Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# 🚀 Create Notification View (Restricted)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def create_notification(request):
    """
    View to create and send notifications to church members.
    Only accessible to Admins and Superusers.
    Sends an SMS notification to each selected member.
    """
    members = ChurchMember.objects.filter(status="Active")
    leaders = members.filter(leader__isnull=False)  # Leaders are also members

    for member in members:
        member.passport_url = member.passport.url if member.passport else "/static/images/user.png"

    if request.method == 'POST':
        form = NotificationForm(request.POST)
        selected_ids = list(set(request.POST.getlist('recipients')))  # ✅ Remove duplicates

        if not selected_ids:
            messages.error(request, "⚠️ You must select at least one recipient.")
            return render(request, 'notifications/create_notification.html', {
                'form': form,
                'members': members,
                'leaders': leaders,
            })

        if form.is_valid():
            message = form.cleaned_data["message"]
            recipients = ChurchMember.objects.filter(id__in=selected_ids)

            for recipient in recipients:
                # ✅ Save the notification in the database
                notification = Notification.objects.create(
                    title="Notification",  # Title is required in the model, but will not be included in SMS
                    message=message,
                    church_member=recipient
                )

                # ✅ Construct the SMS message without the title
                sms_message = f"Ndugu {recipient.full_name}, {message}"

                # ✅ Send SMS to the recipient
                response = send_sms(to=recipient.phone_number, message=sms_message, member=recipient)

                # ✅ Log response for debugging
                print(f"📩 SMS sent to {recipient.phone_number} (Request ID: {response.get('request_id', 'N/A')}): {response}")

            messages.success(request, "📩 Notifications and SMS sent successfully!")
            return redirect('notification_list')

        else:
            messages.error(request, "⚠️ Failed to send notification. Please check the form.")
    else:
        form = NotificationForm()

    return render(request, 'notifications/create_notification.html', {
        'form': form,
        'members': members,
        'leaders': leaders,
    })

# 🚀 Load Recipients via AJAX (Restricted)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def load_recipients(request):
    """
    AJAX function to dynamically load active recipients based on selection.
    Only accessible to Admins and Superusers.
    """
    recipient_type = request.GET.get("type", "all")
    search_query = request.GET.get("search", "").strip().lower()

    if recipient_type == "leaders":
        recipients = ChurchMember.objects.filter(leader__isnull=False, status="Active")
    else:
        recipients = ChurchMember.objects.filter(status="Active")

    if search_query:
        recipients = recipients.filter(full_name__icontains=search_query)

    for recipient in recipients:
        recipient.passport_url = recipient.passport.url if recipient.passport else "/static/images/user.png"

    html = render_to_string("notifications/_recipients_list.html", {"members": recipients})
    return HttpResponse(html)

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils.timezone import now
from collections import defaultdict
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Notification

# ✅ Helper Function for Access Control
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# 🚀 View: List Notifications (Restricted)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def notification_list(request):
    """
    View to list notifications grouped by their title and calculate time since creation.
    Accessible only by Admins and Superusers.
    """
    notifications = Notification.objects.select_related('church_member').filter(
        church_member__isnull=False
    ).order_by('-created_at')

    grouped_notifications = defaultdict(list)

    for notification in notifications:
        time_diff = now() - notification.created_at
        if time_diff.days > 0:
            time_since = f"{time_diff.days} days ago"
        elif time_diff.seconds > 3600:
            time_since = f"{time_diff.seconds // 3600} hours ago"
        elif time_diff.seconds > 60:
            time_since = f"{time_diff.seconds // 60} minutes ago"
        else:
            time_since = "Just now"

        full_name = notification.church_member.full_name if notification.church_member else "Unknown"
        profile_pic = notification.church_member.passport.url if notification.church_member.passport else "/static/images/user.png"

        grouped_notifications[notification.title].append({
            "id": notification.id,
            "message": notification.message,
            "full_name": full_name,
            "profile_pic": profile_pic,
            "created_at": notification.created_at.strftime("%Y-%m-%d %H:%M"),
            "time_since": time_since
        })

    return render(request, 'notifications/notification_list.html', {
        'grouped_notifications': dict(grouped_notifications)
    })

# 🚀 View: Filter Notifications by Title (AJAX, Restricted)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def filter_notifications_by_title(request):
    """
    AJAX-based filtering of notifications by title.
    Accessible only by Admins and Superusers.
    """
    search_query = request.GET.get("title", "").strip().lower()

    notifications = Notification.objects.select_related('church_member').filter(
        church_member__isnull=False,
        title__icontains=search_query
    ).order_by('-created_at')

    grouped_notifications = defaultdict(list)

    for notification in notifications:
        time_diff = now() - notification.created_at
        if time_diff.days > 0:
            time_since = f"{time_diff.days} days ago"
        elif time_diff.seconds > 3600:
            time_since = f"{time_diff.seconds // 3600} hours ago"
        elif time_diff.seconds > 60:
            time_since = f"{time_diff.seconds // 60} minutes ago"
        else:
            time_since = "Just now"

        full_name = notification.church_member.full_name if notification.church_member else "Unknown"
        profile_pic = notification.church_member.passport.url if notification.church_member.passport else "/static/images/user.png"

        grouped_notifications[notification.title].append({
            "id": notification.id,
            "message": notification.message,
            "full_name": full_name,
            "profile_pic": profile_pic,
            "created_at": notification.created_at.strftime("%Y-%m-%d %H:%M"),
            "time_since": time_since
        })

    return JsonResponse({"grouped_notifications": dict(grouped_notifications)})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Notification

# ✅ Helper Function for Access Control
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# 🚀 View: Delete Notifications (Restricted)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def delete_notification(request, delete_type, identifier):
    """
    Handles both:
    - Deleting a group of notifications under a title.
    - Deleting a single notification for a member.

    Parameters:
    - `delete_type`: "group" or "member"
    - `identifier`: Title (for group) or notification ID (for member)
    Accessible only by Admins and Superusers.
    """

    # 🗑️ Deleting a Group of Notifications (by Title)
    if delete_type == "group":
        notifications = Notification.objects.filter(title=identifier)

        if request.method == "POST":
            if notifications.exists():
                notifications.delete()
                messages.success(request, f"✅ All notifications under '{identifier}' deleted successfully.")
            else:
                messages.error(request, f"⚠️ No notifications found under '{identifier}'.")
            return redirect("notification_list")

        # Render Confirmation Page (GET Request)
        return render(request, "notifications/confirm_delete_group.html", {"title": identifier})

    # 🗑️ Deleting an Individual Notification
    elif delete_type == "member":
        notification = get_object_or_404(Notification, id=identifier)

        if request.method == "POST":
            notification.delete()
            messages.success(request, "✅ Deleted the selected notification successfully.")
            return redirect("notification_list")

        # Render Confirmation Page (GET Request)
        return render(request, "notifications/confirm_delete_member.html", {"notification": notification})

    # 🚫 Invalid Deletion Type Handling
    messages.error(request, "❌ Invalid deletion request.")
    return redirect("notification_list")
