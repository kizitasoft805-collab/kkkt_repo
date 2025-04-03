from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .utils import get_sacraments_trend_analysis

# ✅ Helper Function: Check if user is Admin or Superuser
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required(login_url='login')
@user_passes_test(is_admin_or_superuser, login_url='login')
def sacraments_home(request):
    """
    View for the Sacraments home page, displaying different sacrament categories.
    Accessible only by Admins and Superusers.
    """
    sacraments_trend_data = get_sacraments_trend_analysis()

    return render(request, 'sacraments/sacraments_home.html', {
        'sacraments_trend_data': sacraments_trend_data
    })

# 🚿 Baptized Members List (Restricted to Admins/Superusers)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def baptized_members(request):
    """
    Retrieves all church members who are baptized (both active and inactive), sorts them by time since baptism,
    and displays them in a WhatsApp-style contact list.
    Accessible only by Admins and Superusers.
    """
    print("🔍 Fetching all baptized members (active & inactive)...")

    # Get all baptized church members
    baptized_members = ChurchMember.objects.filter(is_baptised=True)
    print(f"✅ Found {baptized_members.count()} baptized members.")

    # Count total male and female baptized members
    total_male = baptized_members.filter(gender="Male").count()
    total_female = baptized_members.filter(gender="Female").count()

    # Get today's date
    today = now().date()

    # Calculate time since baptism & Sort members
    sorted_members = []
    for member in baptized_members:
        if member.date_of_baptism:
            days_difference = (today - member.date_of_baptism).days

            if days_difference < 0:
                # Future Baptism Case
                days_remaining = abs(days_difference)
                years = days_remaining // 365
                months = (days_remaining % 365) // 30
                days = (days_remaining % 365) % 30

                member.time_since_baptism = (
                    f"{years} year(s), {months} month(s), {days} day(s) to come"
                    if years > 0 else
                    f"{months} month(s), {days} day(s) to come"
                    if months > 0 else
                    f"{days} day(s) to come" if days > 0 else "Today"
                )
                sorted_members.append((-days_remaining, member))
            else:
                # Past Baptism Case
                years = days_difference // 365
                months = (days_difference % 365) // 30
                days = (days_difference % 365) % 30

                member.time_since_baptism = (
                    f"{years} year(s), {months} month(s) ago"
                    if years > 0 else
                    f"{months} month(s), {days} day(s) ago"
                    if months > 0 else
                    f"{days} day(s) ago" if days > 0 else "Today"
                )
                sorted_members.append((days_difference, member))
        else:
            member.time_since_baptism = "Unknown"
            sorted_members.append((float("inf"), member))  # Place unknown dates at the bottom

    # ✅ Sort baptized members
    sorted_members.sort(key=lambda x: x[0])
    baptized_members_sorted = [member for _, member in sorted_members]

    context = {
        "baptized_members": baptized_members_sorted,
        "total_male": total_male,
        "total_female": total_female
    }
    return render(request, "sacraments/baptized_members.html", context)


from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from datetime import date
from members.models import ChurchMember
import os

# ✅ Access Control for Admins & Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# 🚿 **Add Baptism Members (Admins/Superusers Only)**
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def add_baptism_members(request):
    print("🔹 Fetching eligible church members...")

    # Updated filter: Remove has_received_first_communion and is_married
    eligible_members = ChurchMember.objects.filter(
        status="Active",
        is_baptised=False,
        is_confirmed=False
    )

    print(f"✅ Found {eligible_members.count()} eligible members.")

    if request.method == "GET":
        return render(request, "sacraments/add_baptism_members.html", {
            "eligible_members": eligible_members,
            "today": date.today()
        })

    elif request.method == "POST":
        baptism_date = request.POST.get("baptism_date", "").strip()
        selected_members = list(set(request.POST.getlist("selected_members")))

        if not baptism_date:
            return JsonResponse({"error": "Baptism date is required."}, status=400)

        if not selected_members:
            return JsonResponse({"error": "No members were selected!"}, status=400)

        for member_id in selected_members:
            try:
                member = ChurchMember.objects.get(id=member_id)
                member.is_baptised = True
                member.date_of_baptism = baptism_date

                file_key = f"certificate_{member_id}"
                if file_key in request.FILES:
                    uploaded_file = request.FILES[file_key]
                    base_filename, file_extension = os.path.splitext(uploaded_file.name)
                    shortened_name = slugify(member.full_name[:10])
                    filename = f"baptism_certificates/{shortened_name}_{uploaded_file.name}"

                    if len(filename) > 255:
                        filename = filename[:250] + file_extension

                    saved_path = default_storage.save(filename, ContentFile(uploaded_file.read()))
                    member.baptism_certificate = saved_path

                member.save()

            except ChurchMember.DoesNotExist:
                return JsonResponse({"error": f"Member ID {member_id} not found."}, status=400)

        return JsonResponse({
            "message": "Baptism records updated successfully!",
            "redirect_url": "/sacraments/baptized-members/"
        }, status=200)

    return JsonResponse({"error": "Invalid request method."}, status=405)

# 🍞 **First Communion Members (Admins/Superusers Only)**
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def first_communion_members(request):
    communion_members = ChurchMember.objects.filter(is_baptised=True, has_received_first_communion=True)
    total_male = communion_members.filter(gender="Male").count()
    total_female = communion_members.filter(gender="Female").count()
    today = now().date()

    sorted_members = []
    for member in communion_members:
        if member.date_of_communion:
            days_difference = (today - member.date_of_communion).days

            if days_difference < 0:
                days_remaining = abs(days_difference)
                member.time_since_communion = f"{days_remaining} day(s) to come"
                sorted_members.append((-days_remaining, member))
            else:
                member.time_since_communion = f"{days_difference} day(s) ago"
                sorted_members.append((days_difference, member))
        else:
            member.time_since_communion = "Unknown"
            sorted_members.append((float("inf"), member))

    sorted_members.sort(key=lambda x: x[0])
    communion_members_sorted = [member for _, member in sorted_members]

    context = {
        "communion_members": communion_members_sorted,
        "total_male": total_male,
        "total_female": total_female
    }
    return render(request, "sacraments/first_communion_members.html", context)

from django.utils.text import slugify
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.timezone import now
from datetime import date
from members.models import ChurchMember
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
import os

# ✅ Access Control for Admins & Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')


# 🍞 **Add First Communion Members (Admins/Superusers Only)**
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def add_communion_members(request):
    print("🔹 Fetching eligible church members...")

    eligible_members = ChurchMember.objects.filter(
        status="Active",
        is_baptised=True,  # Must be baptized to receive Communion
        has_received_first_communion=False
    )

    print(f"✅ Found {eligible_members.count()} eligible members.")

    if request.method == "GET":
        return render(request, "sacraments/add_communion_members.html", {
            "eligible_members": eligible_members,
            "today": date.today()
        })

    elif request.method == "POST":
        communion_date = request.POST.get("communion_date", "").strip()
        selected_members = list(set(request.POST.getlist("selected_members")))  # Remove duplicates

        if not communion_date:
            messages.error(request, "First Communion date is required.")
            return render(request, "sacraments/add_communion_members.html", {
                "eligible_members": eligible_members,
                "today": date.today()
            })

        if not selected_members:
            messages.error(request, "No members were selected!")
            return render(request, "sacraments/add_communion_members.html", {
                "eligible_members": eligible_members,
                "today": date.today()
            })

        for member_id in selected_members:
            try:
                member = ChurchMember.objects.get(id=member_id)
                print(f"🔍 Processing member ID: {member_id}")

                member.has_received_first_communion = True
                member.date_of_communion = communion_date

                file_key = f"certificate_{member_id}"
                if file_key in request.FILES:
                    uploaded_file = request.FILES[file_key]

                    # Shorten filename by keeping only the first 10 characters
                    base_filename, file_extension = os.path.splitext(uploaded_file.name)
                    shortened_name = slugify(member.full_name[:10])  
                    filename = f"communion_certificates/{shortened_name}_{uploaded_file.name}"

                    if len(filename) > 255:
                        filename = filename[:250] + file_extension  

                    saved_path = default_storage.save(filename, ContentFile(uploaded_file.read()))
                    member.communion_certificate = saved_path
                    print(f"📂 Certificate uploaded for {member.full_name}: {saved_path}")
                else:
                    print(f"⚠️ No certificate uploaded for {member.full_name}")

                member.save()
                print(f"✅ First Communion details saved for {member.full_name}")

            except ChurchMember.DoesNotExist:
                messages.error(request, f"Member ID {member_id} not found.")
                return render(request, "sacraments/add_communion_members.html", {
                    "eligible_members": eligible_members,
                    "today": date.today()
                })

        messages.success(request, "✅ All selected members updated successfully!")
        return redirect("communion_members")

    return render(request, "sacraments/add_communion_members.html", {
        "eligible_members": eligible_members,
        "today": date.today()
    })

from django.shortcuts import render
from django.utils.timezone import now
from datetime import date
from members.models import ChurchMember
from django.contrib.auth.decorators import login_required, user_passes_test

# ✅ Access Control for Admins & Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# 🕊️ **Confirmation Members View (Admins/Superusers Only)**
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def confirmation_members(request):
    """
    Retrieves all church members who have received Confirmation, sorts them by time since confirmation,
    and displays them in a WhatsApp-style contact list.
    """
    print("🔍 Fetching all confirmed members...")

    # Get all confirmed church members (active & inactive), updated filter
    confirmed_members = ChurchMember.objects.filter(
        is_baptised=True,  # Keep this as a prerequisite for confirmation
        is_confirmed=True  # Main filter for confirmed members
    )

    # Count total male and female confirmed members
    total_male = confirmed_members.filter(gender="Male").count()
    total_female = confirmed_members.filter(gender="Female").count()

    # Get today's date
    today = now().date()
    sorted_members = []

    for member in confirmed_members:
        print(f"📌 Processing: {member.full_name} | Status: {member.status}")

        if member.date_confirmed:
            days_difference = (today - member.date_confirmed).days

            if days_difference < 0:
                # Future Confirmation Case: Display "X days to come"
                days_remaining = abs(days_difference)
                years = days_remaining // 365
                months = (days_remaining % 365) // 30
                days = (days_remaining % 365) % 30

                member.time_since_confirmation = (
                    f"{years} year(s), {months} month(s), {days} day(s) to come"
                    if years or months or days
                    else "Today"
                )

                print(f"🔵 Future Confirmation: {member.full_name} in {member.time_since_confirmation}")

                # Store future confirmations at the top
                sorted_members.append((-days_remaining, member))  
            else:
                # Past Confirmation Case: Display "X days ago"
                years = days_difference // 365
                months = (days_difference % 365) // 30
                days = (days_difference % 365) % 30

                member.time_since_confirmation = (
                    f"{years} year(s), {months} month(s) ago"
                    if years or months
                    else f"{days} day(s) ago" if days else "Today"
                )

                print(f"🟢 Past Confirmation: {member.full_name} - {member.time_since_confirmation}")

                sorted_members.append((days_difference, member))
        else:
            member.time_since_confirmation = "Unknown"
            sorted_members.append((float("inf"), member))
            print(f"⚠️ {member.full_name} has unknown confirmation date.")

    # ✅ **Sorting Logic**
    sorted_members.sort(key=lambda x: x[0])

    # Extract sorted members list
    confirmed_members_sorted = [member for _, member in sorted_members]

    print("✅ Confirmation members list successfully sorted.")

    context = {
        "confirmed_members": confirmed_members_sorted,
        "total_male": total_male,
        "total_female": total_female
    }
    return render(request, "sacraments/confirmation_members.html", context)

import os
from django.utils.text import slugify
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.timezone import now
from datetime import date
from members.models import ChurchMember
from django.contrib.auth.decorators import login_required, user_passes_test

# ✅ Access Control for Admins & Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# 🕊️ **Add Confirmation Members View (Admins/Superusers Only)**
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def add_confirmation_members(request):
    print("🔹 Fetching eligible church members for confirmation...")

    # Updated filter: Remove has_received_first_communion
    eligible_members = ChurchMember.objects.filter(
        status="Active",
        is_baptised=True,  # Keep as a prerequisite for confirmation
        is_confirmed=False
    )

    print(f"✅ Found {eligible_members.count()} eligible members.")

    # Handle GET request (Render the template)
    if request.method == "GET":
        print("🖥 Rendering Add Confirmation Members page.")
        return render(request, "sacraments/add_confirmation_members.html", {
            "eligible_members": eligible_members,
            "today": date.today()
        })

    # Handle POST request (Process form submission)
    elif request.method == "POST":
        print("🔹 Received POST request for Confirmation members.")

        confirmation_date = request.POST.get("confirmation_date", "").strip()
        selected_members = list(set(request.POST.getlist("selected_members")))  # Remove duplicates

        if not confirmation_date:
            return render(request, "sacraments/add_confirmation_members.html", {
                "eligible_members": eligible_members,
                "today": date.today(),
                "error": "Confirmation date is required."
            })

        if not selected_members:
            return render(request, "sacraments/add_confirmation_members.html", {
                "eligible_members": eligible_members,
                "today": date.today(),
                "error": "No members were selected!"
            })

        for member_id in selected_members:
            try:
                member = ChurchMember.objects.get(id=member_id)
                print(f"🔍 Processing member ID: {member_id}")

                member.is_confirmed = True
                member.date_confirmed = confirmation_date

                # Handle file upload
                file_key = f"certificate_{member_id}"
                if file_key in request.FILES:
                    uploaded_file = request.FILES[file_key]

                    # Shorten filename by keeping only the first 10 characters
                    base_filename, file_extension = os.path.splitext(uploaded_file.name)
                    shortened_name = slugify(member.full_name[:10])  # Keep only 10 characters
                    filename = f"confirmation_certificates/{shortened_name}_{uploaded_file.name}"

                    # Ensure the total path does not exceed 255 characters
                    if len(filename) > 255:
                        filename = filename[:250] + file_extension  # Truncate if too long

                    saved_path = default_storage.save(filename, ContentFile(uploaded_file.read()))
                    member.confirmation_certificate = saved_path
                    print(f"📂 Certificate uploaded for {member.full_name}: {saved_path}")
                else:
                    print(f"⚠️ No certificate uploaded for {member.full_name}")

                member.save()
                print(f"✅ Confirmation details saved for {member.full_name}")

            except ChurchMember.DoesNotExist:
                print(f"❌ Error: Member ID {member_id} does not exist.")
                return render(request, "sacraments/add_confirmation_members.html", {
                    "eligible_members": eligible_members,
                    "today": date.today(),
                    "error": f"Member ID {member_id} not found."
                })

        print("✅ All selected members updated successfully. Redirecting...")
        return redirect("confirmed_members")  # ✅ Redirect to Confirmation Members Page

    return render(request, "sacraments/add_confirmation_members.html", {
        "eligible_members": eligible_members,
        "today": date.today(),
        "error": "Invalid request method."
    })

import os
from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import default_storage
from django.utils.text import slugify
from members.models import ChurchMember
from django.contrib.auth.decorators import login_required, user_passes_test

# ✅ Access Control for Admins & Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')


# 🕊️ **Update Baptized Member View (Admins/Superusers Only)**
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def update_baptized_member(request, member_id):
    """
    Allows updating the baptism date and uploading a new baptism certificate
    for a specific baptized church member (Admins/Superusers only).
    """
    print("🔍 Fetching baptized member details...")

    # Fetch the member or return 404 if not found
    member = get_object_or_404(ChurchMember, id=member_id, is_baptised=True)
    print(f"✅ Member found: {member.full_name} (ID: {member.id})")

    if request.method == "POST":
        print("📤 Received POST request for updating baptized member.")

        # Get the new Baptism Date from the form
        baptism_date = request.POST.get("baptism_date", "").strip()
        remove_certificate = request.POST.get("remove_certificate")  # Checkbox value

        print(f"📅 New Baptism Date: {baptism_date}")
        print(f"🗑 Remove Certificate Checkbox: {remove_certificate}")

        # ✅ Validate if date was provided
        if not baptism_date:
            print("❌ Error: Baptism date is missing.")
            return render(request, "sacraments/update_baptized_member.html", {
                "member": member,
                "error": "Baptism date is required."
            })

        # ✅ Update the date of baptism
        member.date_of_baptism = baptism_date
        print("✅ Baptism date updated.")

        # ✅ Handle removing the existing certificate if checkbox is checked
        if remove_certificate == "yes" and member.baptism_certificate:
            print(f"🗑 Removing existing baptism certificate: {member.baptism_certificate.name}")
            if default_storage.exists(member.baptism_certificate.name):
                default_storage.delete(member.baptism_certificate.name)
                print("✅ Baptism certificate deleted from storage.")
            else:
                print("⚠️ Certificate file not found in storage.")
            member.baptism_certificate = None  # Remove from database

        # ✅ Handle new certificate upload if provided
        if "baptism_certificate" in request.FILES:
            uploaded_file = request.FILES["baptism_certificate"]
            print(f"📂 New Certificate Uploaded: {uploaded_file.name}")

            # Generate a clean filename
            base_filename, file_extension = os.path.splitext(uploaded_file.name)
            shortened_name = slugify(member.full_name[:10])  # First 10 chars only
            filename = f"baptism_certificates/{shortened_name}_{uploaded_file.name}"

            # Ensure the total path does not exceed 255 characters
            if len(filename) > 255:
                filename = filename[:250] + file_extension  # Truncate if too long

            print(f"📂 Saving certificate as: {filename}")

            # Save the file
            saved_path = default_storage.save(filename, uploaded_file)
            member.baptism_certificate = saved_path
            print(f"✅ Certificate saved at: {saved_path}")

        # ✅ Save changes
        member.save()
        print("✅ Member details updated successfully.")

        # ✅ Redirect back to the Baptized Members List
        print("🔄 Redirecting to baptized members list...")
        return redirect("baptized_members")

    print("🖥 Rendering update baptism form.")
    return render(request, "sacraments/update_baptized_member.html", {"member": member})

import os
from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import default_storage
from members.models import ChurchMember
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

# ✅ Access Control: Only Admins & Superusers Allowed
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')


# 🗑️ **Delete Baptized Member (Admins/Superusers Only)**
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def delete_baptized_member(request, member_id):
    """
    Deletes a baptized member’s sacramental data and resets all related fields.
    Only accessible by Admins and Superusers.
    """
    print("🔍 Fetching baptized member details...")

    # Fetch the member or return 404 if not found
    member = get_object_or_404(ChurchMember, id=member_id, is_baptised=True)
    print(f"✅ Member found: {member.full_name} (ID: {member.id})")

    if request.method == "POST":
        print("📤 Received POST request to delete baptism record.")

        # ✅ Remove Certificates (Baptism, Communion, Confirmation, Marriage)
        certificate_fields = [
            ("baptism_certificate", "Baptism"),
            ("communion_certificate", "Communion"),
            ("confirmation_certificate", "Confirmation"),
            ("marriage_certificate", "Marriage")
        ]

        for field, cert_name in certificate_fields:
            certificate = getattr(member, field)
            if certificate:
                if default_storage.exists(certificate.name):
                    default_storage.delete(certificate.name)
                    print(f"🗑 {cert_name} Certificate deleted: {certificate.name}")
                else:
                    print(f"⚠️ {cert_name} Certificate not found in storage.")
                setattr(member, field, None)  # Remove certificate from database

        # ✅ Reset Sacramental Fields
        print("🔄 Resetting sacramental fields...")
        member.is_baptised = False
        member.date_of_baptism = None
        member.has_received_first_communion = False
        member.date_of_communion = None
        member.is_confirmed = False
        member.date_confirmed = None
        member.is_married = False
        member.marital_status = "Single"
        member.date_of_marriage = None
        member.spouse_name = None

        # ✅ Save Changes
        member.save()
        print("✅ Member sacramental data deleted successfully.")

        # ✅ Success Message & Redirect
        messages.success(request, f"Baptism and related sacramental data for {member.full_name} have been deleted.")
        return redirect("baptized_members")

    print("🖥 Rendering delete confirmation page.")
    return render(request, "sacraments/delete_baptized_member.html", {"member": member})


import os
from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import default_storage
from django.utils.text import slugify
from members.models import ChurchMember
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

# ✅ Access Control: Only Admins & Superusers Allowed
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')


# ✏️ **Update First Communion Member (Admins/Superusers Only)**
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def update_communion_member(request, member_id):
    """
    Allows updating the First Communion date and uploading a new First Communion certificate
    for a specific church member who has received First Communion.
    Only accessible by Admins and Superusers.
    """
    print("🔍 Fetching First Communion member details...")

    # Fetch the member or return 404 if not found
    member = get_object_or_404(ChurchMember, id=member_id, has_received_first_communion=True)
    print(f"✅ Member found: {member.full_name} (ID: {member.id})")

    if request.method == "POST":
        print("📤 Received POST request for updating First Communion member.")

        # Get the new Communion Date from the form
        communion_date = request.POST.get("communion_date", "").strip()
        remove_certificate = request.POST.get("remove_certificate")  # Checkbox value

        print(f"📅 New First Communion Date: {communion_date}")
        print(f"🗑 Remove Certificate Checkbox: {remove_certificate}")

        # ✅ Validate if date was provided
        if not communion_date:
            print("❌ Error: First Communion date is missing.")
            messages.error(request, "First Communion date is required.")
            return render(request, "sacraments/update_communion_member.html", {
                "member": member,
            })

        # ✅ Update the date of First Communion
        member.date_of_communion = communion_date
        print("✅ First Communion date updated.")

        # ✅ Handle removing the existing certificate if checkbox is checked
        if remove_certificate == "yes" and member.communion_certificate:
            print(f"🗑 Removing existing First Communion certificate: {member.communion_certificate.name}")
            if default_storage.exists(member.communion_certificate.name):
                default_storage.delete(member.communion_certificate.name)
                print("✅ First Communion certificate deleted from storage.")
            else:
                print("⚠️ Certificate file not found in storage.")
            member.communion_certificate = None  # Remove from database

        # ✅ Handle new certificate upload if provided
        if "communion_certificate" in request.FILES:
            uploaded_file = request.FILES["communion_certificate"]
            print(f"📂 New Certificate Uploaded: {uploaded_file.name}")

            # Generate a clean filename
            base_filename, file_extension = os.path.splitext(uploaded_file.name)
            shortened_name = slugify(member.full_name[:10])  # First 10 chars only
            filename = f"communion_certificates/{shortened_name}_{uploaded_file.name}"

            # Ensure the total path does not exceed 255 characters
            if len(filename) > 255:
                filename = filename[:250] + file_extension  # Truncate if too long

            print(f"📂 Saving certificate as: {filename}")

            # Save the file
            saved_path = default_storage.save(filename, uploaded_file)
            member.communion_certificate = saved_path
            print(f"✅ Certificate saved at: {saved_path}")

        # ✅ Save changes
        member.save()
        print("✅ Member details updated successfully.")

        # ✅ Success Message & Redirect
        messages.success(request, f"First Communion details for {member.full_name} have been updated successfully.")
        print("🔄 Redirecting to First Communion members list...")
        return redirect("communion_members")

    print("🖥 Rendering update First Communion form.")
    return render(request, "sacraments/update_communion_member.html", {"member": member})


import os
from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import default_storage
from members.models import ChurchMember
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

# ✅ Access Control: Only Admins & Superusers Allowed
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')


# 🗑️ **Delete First Communion Member (Admins/Superusers Only)**
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def delete_communion_member(request, member_id):
    """
    Deletes a First Communion member and resets all related sacramental fields.
    Only accessible by Admins and Superusers.
    """
    print("🔍 Fetching First Communion member details...")

    # Fetch the member or return 404 if not found
    member = get_object_or_404(ChurchMember, id=member_id, has_received_first_communion=True)
    print(f"✅ Member found: {member.full_name} (ID: {member.id})")

    if request.method == "POST":
        print("📤 Received POST request for deleting communion member.")

        # ✅ Remove First Communion certificate if exists
        if member.communion_certificate:
            print(f"🗑 Removing communion certificate: {member.communion_certificate.name}")
            if default_storage.exists(member.communion_certificate.name):
                default_storage.delete(member.communion_certificate.name)
                print("✅ Communion certificate deleted from storage.")
            else:
                print("⚠️ Communion certificate file not found in storage.")
            member.communion_certificate = None

        # ✅ Remove Confirmation certificate if exists
        if member.confirmation_certificate:
            print(f"🗑 Removing confirmation certificate: {member.confirmation_certificate.name}")
            if default_storage.exists(member.confirmation_certificate.name):
                default_storage.delete(member.confirmation_certificate.name)
                print("✅ Confirmation certificate deleted from storage.")
            else:
                print("⚠️ Confirmation certificate file not found in storage.")
            member.confirmation_certificate = None

        # ✅ Remove Marriage certificate if exists
        if member.marriage_certificate:
            print(f"🗑 Removing marriage certificate: {member.marriage_certificate.name}")
            if default_storage.exists(member.marriage_certificate.name):
                default_storage.delete(member.marriage_certificate.name)
                print("✅ Marriage certificate deleted from storage.")
            else:
                print("⚠️ Marriage certificate file not found in storage.")
            member.marriage_certificate = None

        # ✅ Reset all sacramental fields
        print("🛠 Resetting sacramental fields...")
        member.has_received_first_communion = False
        member.date_of_communion = None
        member.is_confirmed = False
        member.date_confirmed = None
        member.is_married = False
        member.marital_status = "Single"
        member.date_of_marriage = None
        member.spouse_name = None

        # ✅ Save the member
        member.save()
        print("✅ Member details updated successfully.")

        # ✅ Success Message & Redirect
        messages.success(request, f"All sacramental details for {member.full_name} have been deleted successfully.")
        print("🔄 Redirecting to First Communion Members list...")
        return redirect("communion_members")

    print("🖥 Rendering delete confirmation form.")
    return render(request, "sacraments/delete_communion_member.html", {"member": member})


import os
from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import default_storage
from members.models import ChurchMember
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

# ✅ Access Control: Only Admins & Superusers Allowed
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')


# 🗑️ **Delete Confirmation Member (Admins/Superusers Only)**
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def delete_confirmation_member(request, member_id):
    """
    Deletes a confirmed member and resets all related sacramental fields.
    Only accessible by Admins and Superusers.
    """
    print("🔍 Fetching confirmed member details for deletion...")

    # Fetch the member or return 404 if not found
    member = get_object_or_404(ChurchMember, id=member_id, is_confirmed=True)
    print(f"✅ Member found: {member.full_name} (ID: {member.id})")

    if request.method == "POST":
        print("📤 Received POST request for deleting confirmed member.")

        # ✅ Remove Confirmation Certificate if Exists
        if member.confirmation_certificate:
            print(f"🗑 Removing confirmation certificate: {member.confirmation_certificate.name}")
            if default_storage.exists(member.confirmation_certificate.name):
                default_storage.delete(member.confirmation_certificate.name)
                print("✅ Confirmation certificate deleted from storage.")
            else:
                print("⚠️ Certificate file not found in storage.")
            member.confirmation_certificate = None  # Remove from database

        # ✅ Remove Marriage Certificate if Exists
        if member.marriage_certificate:
            print(f"🗑 Removing marriage certificate: {member.marriage_certificate.name}")
            if default_storage.exists(member.marriage_certificate.name):
                default_storage.delete(member.marriage_certificate.name)
                print("✅ Marriage certificate deleted from storage.")
            else:
                print("⚠️ Certificate file not found in storage.")
            member.marriage_certificate = None  # Remove from database

        # ✅ Reset Confirmation & Marriage Fields
        print("🛠 Resetting confirmation & marriage fields...")
        member.is_confirmed = False
        member.date_confirmed = None
        member.is_married = False
        member.marital_status = "Single"
        member.date_of_marriage = None
        member.spouse_name = None  # Remove spouse name

        # ✅ Save Changes
        member.save()
        print("✅ Confirmation & marriage details removed successfully.")

        # ✅ Success Message & Redirect
        messages.success(request, f"All sacramental details for {member.full_name} have been deleted successfully.")
        print("🔄 Redirecting to confirmation members list...")
        return redirect("confirmed_members")

    print("🖥 Rendering delete confirmation member form.")
    return render(request, "sacraments/delete_confirmation_member.html", {"member": member})


import os
from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import default_storage
from django.utils.text import slugify
from members.models import ChurchMember
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

# ✅ Access Control: Only Admins & Superusers Allowed
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')


# ✏️ **Update Confirmation Member (Admins/Superusers Only)**
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def update_confirmation_member(request, member_id):
    """
    Allows updating the confirmation date and uploading a new confirmation certificate
    for a specific confirmed church member.
    Only accessible by Admins and Superusers.
    """
    print("🔍 Fetching confirmed member details for update...")

    # Fetch the member or return 404 if not found
    member = get_object_or_404(ChurchMember, id=member_id, is_confirmed=True)
    print(f"✅ Member found: {member.full_name} (ID: {member.id})")

    if request.method == "POST":
        print("📤 Received POST request for updating confirmed member.")

        # Get the new Confirmation Date from the form
        confirmation_date = request.POST.get("confirmation_date", "").strip()
        remove_certificate = request.POST.get("remove_certificate")  # Checkbox value

        print(f"📅 New Confirmation Date: {confirmation_date}")
        print(f"🗑 Remove Certificate Checkbox: {remove_certificate}")

        # ✅ Validate Confirmation Date
        if not confirmation_date:
            print("❌ Error: Confirmation date is missing.")
            messages.error(request, "Confirmation date is required.")
            return render(request, "sacraments/update_confirmation_member.html", {"member": member})

        # ✅ Update the Confirmation Date
        member.date_confirmed = confirmation_date
        print("✅ Confirmation date updated.")

        # ✅ Remove Existing Certificate if Checkbox is Checked
        if remove_certificate == "yes" and member.confirmation_certificate:
            print(f"🗑 Removing existing confirmation certificate: {member.confirmation_certificate.name}")
            if default_storage.exists(member.confirmation_certificate.name):
                default_storage.delete(member.confirmation_certificate.name)
                print("✅ Confirmation certificate deleted from storage.")
            else:
                print("⚠️ Certificate file not found in storage.")
            member.confirmation_certificate = None  # Remove from database

        # ✅ Upload New Certificate if Provided
        if "confirmation_certificate" in request.FILES:
            uploaded_file = request.FILES["confirmation_certificate"]
            print(f"📂 New Certificate Uploaded: {uploaded_file.name}")

            # Generate a Clean Filename
            base_filename, file_extension = os.path.splitext(uploaded_file.name)
            shortened_name = slugify(member.full_name[:10])  # First 10 characters only
            filename = f"confirmation_certificates/{shortened_name}_{uploaded_file.name}"

            # Ensure the Total Path Does Not Exceed 255 Characters
            if len(filename) > 255:
                filename = filename[:250] + file_extension  # Truncate if too long

            print(f"📂 Saving certificate as: {filename}")

            # Save the File
            saved_path = default_storage.save(filename, uploaded_file)
            member.confirmation_certificate = saved_path
            print(f"✅ Certificate saved at: {saved_path}")

        # ✅ Save Changes
        member.save()
        print("✅ Member details updated successfully.")

        # ✅ Success Message & Redirect
        messages.success(request, f"Confirmation details for {member.full_name} updated successfully.")
        print("🔄 Redirecting to Confirmation members list...")
        return redirect("confirmed_members")

    print("🖥 Rendering update Confirmation form.")
    return render(request, "sacraments/update_confirmation_member.html", {"member": member})


from django.utils.timezone import now, make_aware
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from members.models import ChurchMember
from datetime import datetime

# ✅ Access Control: Only Admins & Superusers Allowed
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# 🔄 **Calculate Time Since/Until Marriage**
def calculate_time_since_married(marriage_date):
    """
    Calculates time until or since marriage in a human-readable format:
    - Future dates: "X days to come"
    - Past dates: "X days ago"
    """
    if not marriage_date:
        return "Unknown", 0  # Default case

    current_time = now()  # Timezone-aware current time
    marriage_datetime = make_aware(datetime.combine(marriage_date, datetime.min.time()))  # Convert date to timezone-aware datetime

    time_diff = marriage_datetime - current_time
    seconds = int(time_diff.total_seconds())

    if seconds > 0:  # Future marriage
        if seconds < 60:
            return f"{seconds} seconds to come", seconds
        elif seconds < 3600:
            return f"{seconds // 60} minutes to come", seconds
        elif seconds < 86400:
            return f"{seconds // 3600} hours to come", seconds
        elif seconds < 2592000:
            return f"{seconds // 86400} days to come", seconds
        elif seconds < 31536000:
            return f"{seconds // 2592000} months to come", seconds
        else:
            return f"{seconds // 31536000} years to come", seconds

    else:  # Past marriage
        seconds = abs(seconds)
        if seconds < 60:
            return f"{seconds} seconds ago", -seconds
        elif seconds < 3600:
            return f"{seconds // 60} minutes ago", -seconds
        elif seconds < 86400:
            return f"{seconds // 3600} hours ago", -seconds
        elif seconds < 2592000:
            return f"{seconds // 86400} days ago", -seconds
        elif seconds < 31536000:
            return f"{seconds // 2592000} months ago", -seconds
        else:
            return f"{seconds // 31536000} years ago", -seconds

# 📋 **View Married Members (Admins/Superusers Only)**
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def marriage_list_view(request):
    """
    Displays a list of married males sorted based on marriage time.
    Only accessible by Admins and Superusers.
    """
    print("🔍 Retrieving married males...")

    # ✅ Filter Married Males
    married_males = ChurchMember.objects.filter(
        gender="Male",
        marital_status="Married"  # Use marital_status instead of is_married
    )

    # ✅ Calculate Time Since/Until Marriage
    sorted_marriages = []
    for male in married_males:
        time_since_married, sorting_value = calculate_time_since_married(male.date_of_marriage)
        male.time_since_married = time_since_married
        male.sorting_value = sorting_value  # Used for sorting
        sorted_marriages.append((sorting_value, male))

    # ✅ Sort: Future Marriages First, Then Recent Past
    sorted_marriages.sort(reverse=True, key=lambda x: x[0])

    married_males = [item[1] for item in sorted_marriages]

    print(f"✅ Sorted {len(married_males)} married males.")

    return render(request, "sacraments/marriages/marriage_list.html", {
        "married_males": married_males
    })

import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from members.models import ChurchMember

# ✅ Access Control: Only Admins & Superusers Allowed
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# 💍 **Register Marriages (Admins/Superusers Only)**
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def create_marriage(request):
    """
    Allows selecting multiple male and female church members to register marriages at once.
    Only accessible by Admins and Superusers.
    """
    print("🔍 Fetching eligible members for marriage...")

    # ✅ Get Eligible Males and Females
    males = ChurchMember.objects.filter(
        status="Active",
        is_baptised=True,
        is_confirmed=True,
        gender="Male",
        marital_status="Single"  # Replaced is_married=False
    )
    print(f"✅ Found {males.count()} eligible males.")

    females = ChurchMember.objects.filter(
        status="Active",
        is_baptised=True,
        is_confirmed=True,
        gender="Female",
        marital_status="Single"  # Replaced is_married=False
    )
    print(f"✅ Found {females.count()} eligible females.")

    if request.method == "POST":
        print("📤 Received POST request to register marriages...")

        marriages = []  # Store successful marriages

        # Retrieve form data
        marriage_dates = request.POST.getlist("marriage_date")
        selected_males = request.POST.getlist("selected_male")
        selected_females = request.POST.getlist("selected_female")
        # Removed marriage_certificates since the field is gone

        print(f"📆 Marriage dates received: {marriage_dates}")
        print(f"👨 Selected males: {selected_males}")
        print(f"👩 Selected females: {selected_females}")

        # ✅ Validation: Ensure all required fields are provided
        if not marriage_dates or not selected_males or not selected_females:
            print("❌ ERROR: Missing required fields (date, male, or female selection).")
            messages.error(request, "All marriages must have a date, one groom, and one bride.")
            return render(request, "sacraments/marriages/create_marriage.html", {"males": males, "females": females})

        # ✅ Validation: Ensure matching data lengths
        if len(selected_males) != len(selected_females) or len(selected_males) != len(marriage_dates):
            print("❌ ERROR: Mismatched marriage details. Number of males, females, and dates must be the same.")
            messages.error(request, "Each marriage must have exactly one male, one female, and one date.")
            return render(request, "sacraments/marriages/create_marriage.html", {"males": males, "females": females})

        # ✅ Process Each Marriage
        for i in range(len(selected_males)):
            male_id = selected_males[i]
            female_id = selected_females[i]
            marriage_date = marriage_dates[i]

            try:
                male = ChurchMember.objects.get(id=male_id)
                female = ChurchMember.objects.get(id=female_id)
            except ChurchMember.DoesNotExist:
                print(f"❌ ERROR: Member not found (Male ID: {male_id}, Female ID: {female_id}). Skipping...")
                continue

            print(f"💍 Processing Marriage: {male.full_name} & {female.full_name} on {marriage_date}")

            # ✅ Update Member Details
            male.marital_status = "Married"  # Replaced is_married=True
            male.date_of_marriage = marriage_date
            # Removed spouse_name and marriage_certificate updates

            female.marital_status = "Married"  # Replaced is_married=True
            female.date_of_marriage = marriage_date
            # Removed spouse_name and marriage_certificate updates

            # ✅ Save Member Records
            try:
                male.save()
                female.save()
                marriages.append(f"{male.full_name} & {female.full_name}")
                print(f"✅ Successfully registered marriage: {male.full_name} & {female.full_name}")
            except Exception as e:
                print(f"❌ ERROR saving marriage data: {e}")
                messages.error(request, f"Failed to register marriage for {male.full_name} & {female.full_name}.")

        # ✅ Success Message & Redirect
        if marriages:
            messages.success(request, f"Successfully registered {len(marriages)} marriages!")
        else:
            messages.warning(request, "No marriages were successfully registered.")

        print(f"🎉 Successfully registered {len(marriages)} marriages.")
        return redirect("marriage_list")  # Redirect to marriage list after success

    print("🖥 Rendering marriage creation form.")
    return render(request, "sacraments/marriages/create_marriage.html", {"males": males, "females": females})

# 💍 **Update Marriage Details (Admin/Superuser Only)**
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def update_marriage(request, member_id):
    """
    Allows updating marriage details:
    - Date of marriage
    Only accessible by Admins and Superusers.
    """
    print(f"🔍 Fetching marriage details for Member ID: {member_id}")

    # ✅ Get the married member
    member = get_object_or_404(ChurchMember, id=member_id, marital_status="Married")  # Replaced is_married=True

    if request.method == "POST":
        print(f"📤 Processing marriage update for: {member.full_name}")

        # Get form values
        marriage_date = request.POST.get("marriage_date", "").strip()
        # Removed spouse_name and marriage_certificate handling

        # 🚩 **Validation Checks**
        if not marriage_date:
            messages.error(request, "⚠️ Marriage date is required.")
            return redirect("update_marriage", member_id=member.id)

        # ✅ **Update Marriage Details**
        member.date_of_marriage = marriage_date
        # Removed spouse_name and marriage_certificate updates

        # ✅ Save Changes
        member.save()
        print(f"✅ Marriage details updated for {member.full_name}")

        messages.success(request, "✅ Marriage details updated successfully!")
        return redirect("marriage_list")

    print("🖥 Rendering marriage update form.")
    return render(request, "sacraments/marriages/update_marriage.html", {"member": member})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required, user_passes_test
from members.models import ChurchMember
import os

# ✅ Access Control: Only Admins & Superusers Allowed
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')


# 💔 **Delete Marriage (Admin/Superuser Only)**
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def delete_marriage(request, member_id):
    """
    Deletes a marriage by resetting the marital status of both partners.
    Only accessible by Admins and Superusers.
    """
    print(f"🔍 Fetching marriage details for Member ID: {member_id}")

    # ✅ Get the married male member
    male_member = get_object_or_404(ChurchMember, id=member_id, is_married=True)

    if male_member.gender != "Male":
        messages.error(request, "❌ Only married male members can be removed from a marriage.")
        return redirect("marriage_list")

    # 🔍 **Fetch the Spouse (Female Member)**
    female_member = None
    if male_member.spouse_name:
        female_member = ChurchMember.objects.filter(full_name=male_member.spouse_name, gender="Female").first()

    print(f"💔 Removing marriage between {male_member.full_name} and {female_member.full_name if female_member else 'Unknown Spouse'}")

    # 🗑️ **Remove Marriage Certificate (If Exists)**
    if male_member.marriage_certificate:
        print(f"🗑️ Deleting Marriage Certificate for {male_member.full_name}")
        if os.path.exists(male_member.marriage_certificate.path):
            os.remove(male_member.marriage_certificate.path)
            print("✅ Marriage certificate deleted from storage.")
        male_member.marriage_certificate = None

    # 🚩 **Reset Male Member's Marriage Details**
    male_member.is_married = False
    male_member.marital_status = "Single"
    male_member.date_of_marriage = None
    male_member.spouse_name = None
    male_member.save()

    # 🚩 **Reset Spouse's Marriage Details (If Found)**
    if female_member:
        female_member.is_married = False
        female_member.marital_status = "Single"
        female_member.date_of_marriage = None
        female_member.marriage_certificate = None
        female_member.spouse_name = None
        female_member.save()
        print(f"✅ Reset marriage details for spouse: {female_member.full_name}")

    print(f"✅ Successfully deleted marriage for {male_member.full_name}")

    # ✅ **Feedback Message**
    messages.success(request, f"✅ Marriage deleted successfully for {male_member.full_name}.")
    return redirect("marriage_list")
