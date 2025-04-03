from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from sms.models import SentSMS
from sms.utils import check_sms_balance, check_sms_status

# ✅ Helper function to allow only Admins and Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def sms_status_view(request):
    """
    View to check SMS balance and delivery status of messages sent via Beem.
    """
    balance = check_sms_balance()
    sent_messages = SentSMS.objects.all()
    total_sent_sms = sent_messages.count()  # ✅ Calculate total sent SMS
    messages_info = []

    for sms in sent_messages:
        phone_number = sms.phone_number
        request_id = sms.request_id

        status = check_sms_status(dest_addr=phone_number, request_id=request_id)

        # Update status in the database
        sms.status = status
        sms.save()

        messages_info.append({
            "id": sms.id,  # ✅ Include ID for delete button
            "sent_at": sms.sent_at.strftime("%Y-%m-%d %H:%M:%S"),
            "name": sms.recipient.full_name,
            "phone": sms.phone_number,
            "message": sms.message,
            "status": status,
        })

    context = {
        "balance": balance,
        "total_sent_sms": total_sent_sms,  # ✅ Pass total sent SMS count
        "messages_info": messages_info
    }

    return render(request, "sms/sms_status.html", context)

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def delete_sms(request, sms_id):
    """
    Show a confirmation page before deleting a single sent SMS.
    """
    sms = get_object_or_404(SentSMS, id=sms_id)

    if request.method == "POST":
        sms.delete()
        messages.success(request, "📩 SMS deleted successfully!")
        return redirect("sms_status")

    return render(request, "sms/delete_sms_confirm.html", {"sms": sms})

@login_required
def delete_all_sms(request):
    """
    Delete all sent SMS messages after user confirmation.
    """
    if request.method == "POST":
        SentSMS.objects.all().delete()
        messages.success(request, "📩 All SMS messages deleted successfully!")
        return redirect("sms_status")

    return render(request, "sms/delete_all_confirm.html")

@login_required
def secretary_sms_status_view(request):
    """
    View to check SMS balance and delivery status of messages sent via Beem.
    """
    balance = check_sms_balance()
    sent_messages = SentSMS.objects.all()
    total_sent_sms = sent_messages.count()  # ✅ Calculate total sent SMS
    messages_info = []

    for sms in sent_messages:
        phone_number = sms.phone_number
        request_id = sms.request_id

        status = check_sms_status(dest_addr=phone_number, request_id=request_id)

        # Update status in the database
        sms.status = status
        sms.save()

        messages_info.append({
            "id": sms.id,  # ✅ Include ID for delete button
            "sent_at": sms.sent_at.strftime("%Y-%m-%d %H:%M:%S"),
            "name": sms.recipient.full_name,
            "phone": sms.phone_number,
            "message": sms.message,
            "status": status,
        })

    context = {
        "balance": balance,
        "total_sent_sms": total_sent_sms,  # ✅ Pass total sent SMS count
        "messages_info": messages_info
    }

    return render(request, "secretary/sms/sms_status.html", context)

@login_required
def secretary_delete_sms(request, sms_id):
    """
    Show a confirmation page before deleting a single sent SMS.
    """
    sms = get_object_or_404(SentSMS, id=sms_id)

    if request.method == "POST":
        sms.delete()
        messages.success(request, "📩 SMS deleted successfully!")
        return redirect("sms_status")

    return render(request, "secretary/sms/delete_sms_confirm.html", {"sms": sms})

@login_required
def secretary_delete_all_sms(request):
    """
    Delete all sent SMS messages after user confirmation.
    """
    if request.method == "POST":
        SentSMS.objects.all().delete()
        messages.success(request, "📩 All SMS messages deleted successfully!")
        return redirect("sms_status")

    return render(request, "secretary/sms/delete_all_confirm.html")
