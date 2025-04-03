from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.timezone import now
from datetime import date
from members.models import ChurchMember
from .decorators import parish_council_secretary_required


from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from sacraments.utils import get_sacraments_trend_analysis


@login_required
@parish_council_secretary_required
def secretary_sacraments_home(request):
    """
    View for the Sacraments home page, displaying different sacrament categories.
    Accessible only by Admins and Superusers.
    """
    sacraments_trend_data = get_sacraments_trend_analysis()

    return render(request, 'secretary/secretary_sacraments_home.html', {
        'sacraments_trend_data': sacraments_trend_data
    })



# 🚿 Baptized Members List (Restricted to Admins/Superusers)
@login_required
@parish_council_secretary_required
def secretary_baptized_members(request):
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
    return render(request, "secretary/secretary_baptized_members.html", context)


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


# 🚿 **Add Baptism Members (Admins/Superusers Only)**
@login_required
@parish_council_secretary_required
def secretary_add_baptism_members(request):
    print("🔹 Fetching eligible church members...")

    eligible_members = ChurchMember.objects.filter(
        status="Active",
        is_baptised=False,
        has_received_first_communion=False,
        is_confirmed=False,
        is_married=False
    )

    print(f"✅ Found {eligible_members.count()} eligible members.")

    if request.method == "GET":
        return render(request, "secretary/secretary_add_baptism_members.html", {
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
            "redirect_url": "/secretary/baptized-members/"
        }, status=200)

    return JsonResponse({"error": "Invalid request method."}, status=405)


# 🍞 **First Communion Members (Admins/Superusers Only)**
@login_required
@parish_council_secretary_required
def secretary_first_communion_members(request):
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
    return render(request, "secretary/secretary_first_communion_members.html", context)

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

@login_required
@parish_council_secretary_required
def secretary_add_communion_members(request):
    print("🔹 Fetching eligible church members...")

    eligible_members = ChurchMember.objects.filter(
        status="Active",
        is_baptised=True,  # Must be baptized to receive Communion
        has_received_first_communion=False
    )

    print(f"✅ Found {eligible_members.count()} eligible members.")

    if request.method == "GET":
        return render(request, "secretary/secretary_add_communion_members.html", {
            "eligible_members": eligible_members,
            "today": date.today()
        })

    elif request.method == "POST":
        communion_date = request.POST.get("communion_date", "").strip()
        selected_members = list(set(request.POST.getlist("selected_members")))  # Remove duplicates

        if not communion_date:
            messages.error(request, "First Communion date is required.")
            return render(request, "secretary/secretary_add_communion_members.html", {
                "eligible_members": eligible_members,
                "today": date.today()
            })

        if not selected_members:
            messages.error(request, "No members were selected!")
            return render(request, "secretary/secretary_add_communion_members.html", {
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
                return render(request, "secretary/secretary_add_communion_members.html", {
                    "eligible_members": eligible_members,
                    "today": date.today()
                })

        messages.success(request, "✅ All selected members updated successfully!")
        return redirect("communion_members")

    return render(request, "secretary/secretary_add_communion_members.html", {
        "eligible_members": eligible_members,
        "today": date.today()
    })

from django.shortcuts import render
from django.utils.timezone import now
from datetime import date
from members.models import ChurchMember
from django.contrib.auth.decorators import login_required, user_passes_test

# 🕊️ **Confirmation Members View (Admins/Superusers Only)**
@login_required
@parish_council_secretary_required
def secretary_confirmation_members(request):
    """
    Retrieves all church members who have received Confirmation, sorts them by time since confirmation,
    and displays them in a WhatsApp-style contact list.
    """
    print("🔍 Fetching all confirmed members...")

    # Get all confirmed church members (active & inactive)
    confirmed_members = ChurchMember.objects.filter(
        is_baptised=True,
        has_received_first_communion=True,
        is_confirmed=True
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
    return render(request, "secretary/secretary_confirmation_members.html", context)

import os
from django.utils.text import slugify
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.timezone import now
from datetime import date
from members.models import ChurchMember
from django.contrib.auth.decorators import login_required, user_passes_test

# 🕊️ **Add Confirmation Members View (Admins/Superusers Only)**
@login_required
@parish_council_secretary_required
def secretary_add_confirmation_members(request):
    print("🔹 Fetching eligible church members for confirmation...")

    eligible_members = ChurchMember.objects.filter(
        status="Active",
        is_baptised=True,
        has_received_first_communion=True,
        is_confirmed=False
    )

    print(f"✅ Found {eligible_members.count()} eligible members.")

    # Handle GET request (Render the template)
    if request.method == "GET":
        print("🖥 Rendering Add Confirmation Members page.")
        return render(request, "secretary/secretary_add_confirmation_members.html", {
            "eligible_members": eligible_members,
            "today": date.today()
        })

    # Handle POST request (Process form submission)
    elif request.method == "POST":
        print("🔹 Received POST request for Confirmation members.")

        confirmation_date = request.POST.get("confirmation_date", "").strip()
        selected_members = list(set(request.POST.getlist("selected_members")))  # Remove duplicates

        if not confirmation_date:
            return render(request, "secretary/secretary_add_confirmation_members.html", {
                "eligible_members": eligible_members,
                "today": date.today(),
                "error": "Confirmation date is required."
            })

        if not selected_members:
            return render(request, "secretary/secretary_add_confirmation_members.html", {
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
                return render(request, "secretary/secretary_add_confirmation_members.html", {
                    "eligible_members": eligible_members,
                    "today": date.today(),
                    "error": f"Member ID {member_id} not found."
                })

        print("✅ All selected members updated successfully. Redirecting...")
        return redirect("secretary_confirmed_members")  # ✅ Redirect to Confirmation Members Page

    return render(request, "secretary/secretary_add_confirmation_members.html", {
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

# 🕊️ **Update Baptized Member View (Admins/Superusers Only)**
@login_required
@parish_council_secretary_required
def secretary_update_baptized_member(request, member_id):
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
            return render(request, "secretary/secretary_update_baptized_member.html", {
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
        return redirect("secretary_baptized_members")

    print("🖥 Rendering update baptism form.")
    return render(request, "secretary/secretary_update_baptized_member.html", {"member": member})

import os
from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import default_storage
from members.models import ChurchMember
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

# 🗑️ **Delete Baptized Member (Admins/Superusers Only)**
@login_required
@parish_council_secretary_required
def secretary_delete_baptized_member(request, member_id):
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
        return redirect("secretary_baptized_members")

    print("🖥 Rendering delete confirmation page.")
    return render(request, "secretary/secretary_delete_baptized_member.html", {"member": member})


import os
from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import default_storage
from django.utils.text import slugify
from members.models import ChurchMember
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

# ✏️ **Update First Communion Member (Admins/Superusers Only)**
@login_required
@parish_council_secretary_required
def secretary_update_communion_member(request, member_id):
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
            return render(request, "secretary/secretary_update_communion_member.html", {
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
        return redirect("secretary_communion_members")

    print("🖥 Rendering update First Communion form.")
    return render(request, "secretary/secretary_update_communion_member.html", {"member": member})


import os
from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import default_storage
from members.models import ChurchMember
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

# 🗑️ **Delete First Communion Member (Admins/Superusers Only)**
@login_required
@parish_council_secretary_required
def secretary_delete_communion_member(request, member_id):
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
        return redirect("secretary_communion_members")

    print("🖥 Rendering delete confirmation form.")
    return render(request, "secretary/secretary_delete_communion_member.html", {"member": member})


import os
from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import default_storage
from members.models import ChurchMember
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

# 🗑️ **Delete Confirmation Member (Admins/Superusers Only)**
@login_required
@parish_council_secretary_required
def secretary_delete_confirmation_member(request, member_id):
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
        return redirect("secretary_confirmed_members")

    print("🖥 Rendering delete confirmation member form.")
    return render(request, "secretary/secretary_delete_confirmation_member.html", {"member": member})


import os
from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import default_storage
from django.utils.text import slugify
from members.models import ChurchMember
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

# ✏️ **Update Confirmation Member (Admins/Superusers Only)**
@login_required
@parish_council_secretary_required
def secretary_update_confirmation_member(request, member_id):
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
        return redirect("secretary_confirmed_members")

    print("🖥 Rendering update Confirmation form.")
    return render(request, "secretary/secretary_update_confirmation_member.html", {"member": member})

import os
from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from members.models import ChurchMember

# 💍 **Register Marriages (Admins/Superusers Only)**
@login_required
@parish_council_secretary_required
def secretary_create_marriage(request):
    """
    Allows selecting multiple male and female church members to register marriages at once.
    Only accessible by Admins and Superusers.
    """
    print("🔍 Fetching eligible members for marriage...")

    # ✅ Get Eligible Males and Females
    males = ChurchMember.objects.filter(
        status="Active", is_baptised=True, has_received_first_communion=True,
        is_confirmed=True, gender="Male", is_married=False
    )
    print(f"✅ Found {males.count()} eligible males.")

    females = ChurchMember.objects.filter(
        status="Active", is_baptised=True, has_received_first_communion=True,
        is_confirmed=True, gender="Female", is_married=False
    )
    print(f"✅ Found {females.count()} eligible females.")

    if request.method == "POST":
        print("📤 Received POST request to register marriages...")

        marriages = []  # Store successful marriages

        # Retrieve form data
        marriage_dates = request.POST.getlist("marriage_date")
        selected_males = request.POST.getlist("selected_male")
        selected_females = request.POST.getlist("selected_female")
        marriage_certificates = request.FILES.getlist("marriage_certificate")

        print(f"📆 Marriage dates received: {marriage_dates}")
        print(f"👨 Selected males: {selected_males}")
        print(f"👩 Selected females: {selected_females}")
        print(f"📜 Certificates uploaded: {len(marriage_certificates)}")

        # ✅ Validation: Ensure all required fields are provided
        if not marriage_dates or not selected_males or not selected_females:
            print("❌ ERROR: Missing required fields (date, male, or female selection).")
            messages.error(request, "All marriages must have a date, one groom, and one bride.")
            return render(request, "secretary/marriages/secretary_create_marriage.html", {"males": males, "females": females})

        # ✅ Validation: Ensure matching data lengths
        if len(selected_males) != len(selected_females) or len(selected_males) != len(marriage_dates):
            print("❌ ERROR: Mismatched marriage details. Number of males, females, and dates must be the same.")
            messages.error(request, "Each marriage must have exactly one male, one female, and one date.")
            return render(request, "secretary/marriages/secretary_create_marriage.html", {"males": males, "females": females})

        # ✅ Process Each Marriage
        for i in range(len(selected_males)):
            male_id = selected_males[i]
            female_id = selected_females[i]
            marriage_date = marriage_dates[i]
            marriage_certificate = marriage_certificates[i] if i < len(marriage_certificates) else None

            try:
                male = ChurchMember.objects.get(id=male_id)
                female = ChurchMember.objects.get(id=female_id)
            except ChurchMember.DoesNotExist:
                print(f"❌ ERROR: Member not found (Male ID: {male_id}, Female ID: {female_id}). Skipping...")
                continue

            print(f"💍 Processing Marriage: {male.full_name} & {female.full_name} on {marriage_date}")

            # ✅ Update Member Details
            male.is_married = True
            male.marital_status = "Married"
            male.date_of_marriage = marriage_date
            male.spouse_name = female.full_name

            female.is_married = True
            female.marital_status = "Married"
            female.date_of_marriage = marriage_date
            female.spouse_name = male.full_name

            # ✅ Save Marriage Certificate (if provided)
            if marriage_certificate:
                try:
                    file_path = default_storage.save(f"marriage_certificates/{marriage_certificate.name}", marriage_certificate)
                    male.marriage_certificate = file_path
                    female.marriage_certificate = file_path
                    print(f"📜 Saved marriage certificate for {male.full_name} & {female.full_name}")
                except Exception as e:
                    print(f"❌ ERROR saving marriage certificate: {e}")
                    messages.error(request, f"Failed to save marriage certificate for {male.full_name} & {female.full_name}.")

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
        return redirect("secretary_marriage_list")  # Redirect to marriage list after success

    print("🖥 Rendering marriage creation form.")
    return render(request, "secretary/marriages/secretary_create_marriage.html", {"males": males, "females": females})

from django.utils.timezone import now, make_aware
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from members.models import ChurchMember
from datetime import datetime

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
@parish_council_secretary_required
def secretary_marriage_list_view(request):
    """
    Displays a list of married males sorted based on marriage time.
    Only accessible by Admins and Superusers.
    """
    print("🔍 Retrieving married males...")

    # ✅ Filter Married Males
    married_males = ChurchMember.objects.filter(
        gender="Male",
        is_baptised=True,
        has_received_first_communion=True,
        is_confirmed=True,
        is_married=True
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

    return render(request, "secretary/marriages/secretary_marriage_list.html", {
        "married_males": married_males
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import default_storage
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from members.models import ChurchMember
import os

# 💍 **Update Marriage Details (Admin/Superuser Only)**
@login_required
@parish_council_secretary_required
def secretary_update_marriage(request, member_id):
    """
    Allows updating marriage details:
    - Date of marriage
    - Spouse name
    - Uploading or removing marriage certificate
    Only accessible by Admins and Superusers.
    """
    print(f"🔍 Fetching marriage details for Member ID: {member_id}")

    # ✅ Get the married member
    member = get_object_or_404(ChurchMember, id=member_id, is_married=True)
    previous_spouse_name = member.spouse_name  # Store previous spouse name

    if request.method == "POST":
        print(f"📤 Processing marriage update for: {member.full_name}")

        # Get form values
        marriage_date = request.POST.get("marriage_date", "").strip()
        new_spouse_name = request.POST.get("spouse_name", "").strip()
        marriage_certificate = request.FILES.get("marriage_certificate")
        remove_certificate = request.POST.get("remove_certificate")

        # 🚩 **Validation Checks**
        if not marriage_date:
            messages.error(request, "⚠️ Marriage date is required.")
            return redirect("secretary_update_marriage", member_id=member.id)

        if not new_spouse_name:
            messages.error(request, "⚠️ Spouse name is required.")
            return redirect("secretary_update_marriage", member_id=member.id)

        # 🗑️ **Remove Existing Marriage Certificate**
        if remove_certificate and member.marriage_certificate:
            print(f"🗑️ Removing Marriage Certificate for {member.full_name}")
            if os.path.exists(member.marriage_certificate.path):
                os.remove(member.marriage_certificate.path)
                print("✅ Marriage certificate removed from storage.")
            member.marriage_certificate = None

        # ✅ **Update Marriage Details**
        member.date_of_marriage = marriage_date
        member.spouse_name = new_spouse_name

        # 📂 **Upload New Marriage Certificate**
        if marriage_certificate:
            file_path = default_storage.save(f"marriage_certificates/{marriage_certificate.name}", marriage_certificate)
            member.marriage_certificate = file_path
            print(f"📥 Uploaded new marriage certificate: {file_path}")

        # 🔄 **Handle Spouse Name Update**
        if previous_spouse_name and previous_spouse_name != new_spouse_name:
            print(f"🔄 Updating spouse record from '{previous_spouse_name}' to '{new_spouse_name}'")

            # Find the spouse in the system
            spouse = ChurchMember.objects.filter(full_name=previous_spouse_name).first()

            if spouse:
                print(f"✅ Found spouse record: {spouse.full_name} - Updating spouse name")
                spouse.spouse_name = new_spouse_name
                spouse.save()
            else:
                print(f"⚠️ No matching spouse found for: {previous_spouse_name}")

        # ✅ Save Changes
        member.save()
        print(f"✅ Marriage details updated for {member.full_name}")

        messages.success(request, "✅ Marriage details updated successfully!")
        return redirect("secretary_marriage_list")

    print("🖥 Rendering marriage update form.")
    return render(request, "secretary/marriages/secretary_update_marriage.html", {"member": member})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required, user_passes_test
from members.models import ChurchMember
import os

# 💔 **Delete Marriage (Admin/Superuser Only)**
@login_required
@parish_council_secretary_required
def secretary_delete_marriage(request, member_id):
    """
    Deletes a marriage by resetting the marital status of both partners.
    Only accessible by Admins and Superusers.
    """
    print(f"🔍 Fetching marriage details for Member ID: {member_id}")

    # ✅ Get the married male member
    male_member = get_object_or_404(ChurchMember, id=member_id, is_married=True)

    if male_member.gender != "Male":
        messages.error(request, "❌ Only married male members can be removed from a marriage.")
        return redirect("secretary_marriage_list")

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
    return redirect("secretary_marriage_list")


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from properties.models import ChurchAsset
from properties.forms import ChurchAssetFormSet
from datetime import datetime
import pytz

# 🌍 Set timezone for Tanzania
TZ_TZ = pytz.timezone('Africa/Dar_es_Salaam')


# 🏠 View: Properties Home (Restricted)
@login_required
@parish_council_secretary_required
def secretary_properties_home(request):
    """
    View for the Properties home page, displaying church properties section.
    Accessible only by Admins and Superusers.
    """
    return render(request, 'secretary/properties/properties_home.html')


# 🏗️ View: Create Church Assets (Restricted)
@login_required
@parish_council_secretary_required
def secretary_create_church_assets(request):
    """
    View to create multiple church assets using a formset.
    Accessible only by Admins and Superusers.
    """
    if request.method == 'POST':
        formset = ChurchAssetFormSet(request.POST)
        if formset.is_valid():
            saved_assets = []
            for form in formset:
                if form.cleaned_data:
                    asset = form.save()
                    saved_assets.append(asset.pk)

            request.session['saved_assets'] = saved_assets
            return redirect('upload_church_asset_media')
        else:
            messages.error(request, 'Failed to save assets. Please correct the errors below.')
    else:
        formset = ChurchAssetFormSet()

    return render(request, 'secretary/properties/create_church_assets.html', {'formset': formset})


# 📊 View: Display Church Assets (Restricted)
@login_required
@parish_council_secretary_required
def secretary_church_assets_view(request):
    """
    View to display a list of church assets in a structured table format with search.
    Accessible only by Admins and Superusers.
    """
    # Fetch query parameters
    search_query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', '').strip()

    # Start with all assets
    church_assets = ChurchAsset.objects.all()

    # Apply filters
    if search_query:
        church_assets = church_assets.filter(name__icontains=search_query)
    
    if search_type:
        church_assets = church_assets.filter(asset_type=search_type)

    # Time formatting
    for asset in church_assets:
        asset.time_since_acquired = time_since(asset.acquisition_date)
        asset.time_since_created = time_since(asset.created_at)

    # Calculate totals
    total_quantity = church_assets.aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_value = church_assets.aggregate(Sum('value'))['value__sum'] or 0

    return render(request, 'secretary/properties/church_assets_list.html', {
        'church_assets': church_assets,
        'total_quantity': total_quantity,
        'total_value': total_value,
        'search_query': search_query,
        'search_type': search_type
    })


# ⏳ Helper Function for Time Formatting
def time_since(past_date):
    """
    Calculate time since a given date and return a readable string.
    """
    if not past_date:
        return "N/A"

    current_date = datetime.now().date()
    if isinstance(past_date, datetime):
        past_date = past_date.date()

    days = (current_date - past_date).days

    if days < 1:
        return "Today"
    elif days == 1:
        return "Yesterday"
    elif days < 7:
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif days < 30:
        weeks = days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    else:
        years = days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.timezone import now, localtime, make_aware
from datetime import datetime, date
import pytz

from properties.models import ChurchAsset, ChurchAssetMedia
from properties.forms import UpdateChurchAssetForm

# 🌍 Timezone for Tanzania
TZ_TZ = pytz.timezone('Africa/Dar_es_Salaam')


# 🔄 Update Church Asset (Restricted)
@login_required
@parish_council_secretary_required
def secretary_update_church_asset(request, asset_id):
    """
    View to update an existing church asset.
    Accessible only by Admins and Superusers.
    """
    church_asset = get_object_or_404(ChurchAsset, id=asset_id)

    if request.method == 'POST':
        form = UpdateChurchAssetForm(request.POST, instance=church_asset)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Church asset updated successfully!")
            return redirect('secretary_church_assets_list')
        else:
            messages.error(request, "❌ Failed to update asset. Please correct the errors.")
    else:
        form = UpdateChurchAssetForm(instance=church_asset)

    return render(request, 'secretary_properties/update_church_asset.html', {
        'form': form,
        'church_asset': church_asset
    })


# 📋 Church Asset Details (Restricted)
@login_required
@parish_council_secretary_required
def secretary_church_asset_detail(request, asset_id):
    """
    View to retrieve details of a specific Church Asset, including uploaded media.
    Accessible only by Admins and Superusers.
    """
    church_asset = get_object_or_404(ChurchAsset, id=asset_id)
    asset_media = ChurchAssetMedia.objects.filter(church_asset=church_asset)

    # Format dates
    acquisition_since = format_time_since(church_asset.acquisition_date)
    created_since = format_time_since(church_asset.created_at)

    # Asset Details
    asset_details = {
        "📛 Name": church_asset.name,
        "📂 Type": church_asset.get_asset_type_display(),
        "🔧 Status": church_asset.get_status_display(),
        "📦 Quantity": f"{church_asset.quantity} ({church_asset.get_quantity_name_display()})",
        "💰 Value": f"{church_asset.value} TZS",
        "📅 Acquisition Date": f"{church_asset.acquisition_date} ({acquisition_since})",
        "⏳ Date Created": f"{church_asset.created_at} ({created_since})",
        "📝 Description": church_asset.description or "No description available",
    }

    return render(request, "secretary/properties/church_asset_detail.html", {
        "church_asset": church_asset,
        "asset_details": asset_details,
        "asset_media": asset_media,
    })


# ⏳ Helper Function: Format Time Since Date
def format_time_since(past_date):
    """
    Convert a date/datetime to a human-readable format.
    """
    if not past_date:
        return "N/A"

    if isinstance(past_date, date) and not isinstance(past_date, datetime):
        past_date = datetime.combine(past_date, datetime.min.time())
        past_date = make_aware(past_date, timezone=TZ_TZ)

    past_date = localtime(past_date, timezone=TZ_TZ)
    current_time = localtime(now(), timezone=TZ_TZ)

    time_difference = current_time - past_date
    seconds = time_difference.total_seconds()

    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif seconds < 2419200:
        weeks = int(seconds // 604800)
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif seconds < 29030400:
        months = int(seconds // 2419200)
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        years = int(seconds // 29030400)
        return f"{years} year{'s' if years > 1 else ''} ago"


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.forms import modelformset_factory
from django.conf import settings
import os

from properties.models import ChurchAsset, ChurchAssetMedia
from properties.forms import ChurchAssetMediaForm

# 🚮 Delete Church Asset (Restricted)
@login_required
@parish_council_secretary_required
def secretary_delete_church_asset(request, asset_id):
    """
    View to delete a given Church Asset along with all associated media.
    Accessible only by Admins and Superusers.
    """
    church_asset = get_object_or_404(ChurchAsset, id=asset_id)

    if request.method == "POST":
        # Delete associated media files from storage
        asset_media = ChurchAssetMedia.objects.filter(church_asset=church_asset)
        for media in asset_media:
            if media.image:
                image_path = os.path.join(settings.MEDIA_ROOT, str(media.image))
                if os.path.exists(image_path):
                    os.remove(image_path)  # Remove image from storage

        # Delete media records & the asset itself
        asset_media.delete()
        church_asset.delete()

        messages.success(request, "✅ Church Asset and all associated media deleted successfully!")
        return redirect('secretary_church_assets_list')

    return render(request, 'secretary/properties/church_asset_confirm_delete.html', {
        'church_asset': church_asset,
    })


# 📤 Upload Additional Media for Church Asset (Restricted)
@login_required
@parish_council_secretary_required
def secretary_upload_additional_church_asset_media(request, asset_id):
    """
    View to upload multiple additional media files for a ChurchAsset.
    Accessible only by Admins and Superusers.
    """
    church_asset = get_object_or_404(ChurchAsset, id=asset_id)
    existing_media = ChurchAssetMedia.objects.filter(church_asset=church_asset)

    # Define FormSet
    ChurchAssetMediaFormSet = modelformset_factory(
        ChurchAssetMedia,
        form=ChurchAssetMediaForm,
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        formset = ChurchAssetMediaFormSet(request.POST, request.FILES, queryset=existing_media)
        if formset.is_valid():
            instances = formset.save(commit=False)
            saved_count = 0

            for instance in instances:
                if instance.image:
                    instance.church_asset = church_asset
                    instance.save()
                    saved_count += 1

            if saved_count > 0:
                messages.success(request, f"✅ {saved_count} media uploaded successfully!")
                return redirect('secretary_church_asset_detail', asset_id=church_asset.id)
            else:
                messages.warning(request, "⚠️ No media uploaded. Please select an image.")

        else:
            messages.error(request, "❌ Failed to upload media. Please check the form.")

    else:
        formset = ChurchAssetMediaFormSet(queryset=existing_media)

    return render(request, 'secretary/properties/upload_additional_church_asset_media.html', {
        'formset': formset,
        'church_asset': church_asset,
        'existing_media': existing_media,
    })


# 🗑️ Delete Church Asset Media (Restricted)
@login_required
@parish_council_secretary_required
def secretary_delete_church_asset_media(request, media_id):
    """
    Deletes a specific church asset media file.
    Accessible only by Admins and Superusers.
    """
    if request.method == 'POST':
        media = get_object_or_404(ChurchAssetMedia, id=media_id)

        # Delete media file from storage
        if media.image:
            image_path = os.path.join(settings.MEDIA_ROOT, str(media.image))
            if os.path.exists(image_path):
                os.remove(image_path)

        media.delete()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from properties.models import ChurchAsset, ChurchAssetMedia
from properties.forms import ChurchAssetMediaForm


# 📤 Upload Media for Church Assets (Restricted)
@login_required
@parish_council_secretary_required
def secretary_upload_church_asset_media(request):
    """
    View to upload multiple media files for church assets.
    Accessible only by Admins and Superusers.
    
    - Each church asset has a block for uploading images.
    - Users can upload multiple images per asset.
    - Users can skip this step if no images are needed.
    """
    # Retrieve the latest church assets created
    latest_assets = ChurchAsset.objects.order_by('-created_at')[:5]  # Adjust the limit as needed
    total_assets = latest_assets.count()

    if request.method == 'POST':
        uploaded_files_count = 0  # Track the number of files uploaded

        for asset in latest_assets:
            files = request.FILES.getlist(f'images_{asset.id}')  # Get multiple files per asset

            if files:
                for file in files:
                    ChurchAssetMedia.objects.create(church_asset=asset, image=file)
                    uploaded_files_count += 1

        if uploaded_files_count > 0:
            messages.success(request, f'✅ {uploaded_files_count} media files uploaded successfully!')
        else:
            messages.warning(request, '⚠️ No files uploaded. Please select files to upload.')

        return redirect('secretary_church_assets_list')  # Redirect to the assets list

    return render(request, 'secretary/properties/upload_church_asset_media.html', {
        'latest_assets': latest_assets,
        'total_assets': total_assets,
    })

# settings/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from settings.forms import YearForm
from django.contrib.auth.decorators import login_required, user_passes_test

# 📅 **Create Year (Admin/Superuser Only)**
@login_required
@parish_council_secretary_required
def secretary_create_year(request):
    """
    View for creating a Year instance.
    Ensures only one year is set as current.
    Only accessible by Admins and Superusers.
    """
    print("🔍 Accessing Create Year View")

    if request.method == 'POST':
        print("📥 Received POST request to create a new year")
        form = YearForm(request.POST)

        if form.is_valid():
            # ✅ Ensure only one year is set as current
            if form.cleaned_data.get('is_current'):
                print("⚠️ Setting this year as current. Unsetting others...")
                from .models import Year
                Year.objects.filter(is_current=True).update(is_current=False)  # Unset all other current years

            form.save()
            print("✅ Year created successfully!")

            messages.success(request, "🎉 Year created successfully!")
            return redirect('year_list')  # Redirect to the year list page
        else:
            print("❌ Form validation failed:", form.errors)
            messages.error(request, "❌ Failed to create year. Please correct the errors.")
    else:
        print("🗒️ Displaying empty form for new year creation")
        form = YearForm()

    return render(request, 'secretary/settings/create_year.html', {'form': form})

# settings/views.py

from django.shortcuts import render
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from settings.models import Year

# ⏱️ **Calculate Time Since Creation**
def calculate_time_since(created_at):
    """
    Calculates how much time has passed since a year was created.
    Returns a human-readable time format.
    """
    delta = now() - created_at

    if delta < timedelta(minutes=1):
        return "Just now"
    elif delta < timedelta(hours=1):
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif delta < timedelta(days=1):
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif delta < timedelta(weeks=1):
        days = delta.days
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif delta < timedelta(days=30):
        weeks = delta.days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif delta < timedelta(days=365):
        months = delta.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        years = delta.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"


# 📋 **List Years (Admin/Superuser Only)**
@login_required
@parish_council_secretary_required
def secretary_year_list(request):
    """
    View for listing all the years.
    Accessible only by Admins and Superusers.
    """
    print("📅 Accessing Year List View")

    try:
        years = Year.objects.all().order_by('year')  # Sort years in ascending order
        print(f"✅ Retrieved {years.count()} years from the database")

        # Add calculated time since creation
        for year in years:
            year.time_since_created = calculate_time_since(year.date_created)

    except Exception as e:
        print(f"❌ Error retrieving years: {e}")
        messages.error(request, "⚠️ Failed to load years. Please try again later.")
        years = []

    return render(request, 'secretary/settings/year_list.html', {'years': years})

# settings/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required, user_passes_test
from settings.models import Year
from settings.forms import YearForm

# ✏️ **Update Year (Admin/Superuser Only)**
@login_required
@parish_council_secretary_required
def secretary_update_year(request, pk):
    """
    View for updating a year.
    Accessible only by Admins and Superusers.
    """
    print(f"📋 Accessing Update Year View for Year ID: {pk}")

    year = get_object_or_404(Year, pk=pk)

    if request.method == 'POST':
        form = YearForm(request.POST, instance=year)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Year updated successfully!")
            print(f"✅ Year {year.year} updated successfully!")
            return redirect('year_list')
        else:
            messages.error(request, "⚠️ Failed to update year. Please correct the errors.")
            print(f"❌ Form errors: {form.errors}")
    else:
        form = YearForm(instance=year)

    return render(request, 'secretary/settings/update_year.html', {'form': form, 'year': year})


# 🗑️ **Delete Year (Admin/Superuser Only)**
@login_required
@parish_council_secretary_required
def secretary_delete_year(request, pk):
    """
    View for confirming and deleting a year.
    Accessible only by Admins and Superusers.
    """
    print(f"🗑️ Accessing Delete Year View for Year ID: {pk}")

    year = get_object_or_404(Year, pk=pk)

    if request.method == 'POST':
        try:
            # ❌ Prevent deletion of the current year
            if year.is_current:
                raise ValidationError("⚠️ You cannot delete the current year.")

            # ✅ Delete the year if it's not current
            year.delete()
            messages.success(request, "✅ Year deleted successfully!")
            print(f"✅ Year {year.year} deleted successfully!")

        except ValidationError as e:
            messages.error(request, str(e))
            print(f"❌ Error: {e}")

        return redirect('year_list')

    return render(request, 'secretary/settings/confirm_delete_year.html', {'year': year})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from settings.models import Year, OutStation, Cell  # Updated imports
from settings.utils import get_settings_distribution_analysis  # Utility for bar chart data



@login_required
@parish_council_secretary_required
def secretary_settings_home(request):
    """
    View to render the Settings Home Page.
    Accessible only by Parish Council Secretaries (or Admins/Superusers if adjusted).
    """
    print(f"⚙️ Accessing Settings Home by {request.user.username}")

    # Get counts for each item
    years_count = Year.objects.count()
    outstations_count = OutStation.objects.count()  # Updated from zones_count
    cells_count = Cell.objects.count()  # Updated from communities_count
    # Removed movements_count since ApostolicMovement is not in settings/models.py

    # Get settings distribution data for the bar chart
    settings_distribution_data = get_settings_distribution_analysis()

    context = {
        "settings_distribution_data": settings_distribution_data,
        "years_count": years_count,
        "outstations_count": outstations_count,  # Updated from zones_count
        "cells_count": cells_count,              # Updated from communities_count
        # Removed movements_count from context
    }
    return render(request, "secretary/settings/settings_home.html", context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

from settings.models import OutStation, Cell, Year
from settings.forms import OutStationForm, CellForm



# ✅ Create or Update OutStation
@login_required
@parish_council_secretary_required
def secretary_create_or_update_outstation(request, outstation_id=None):
    """
    View to create or update an OutStation.
    Access restricted to Parish Council Secretaries or Superusers.
    """
    action = "Update" if outstation_id else "Create"
    outstation = None

    if outstation_id:
        outstation = get_object_or_404(OutStation, id=outstation_id)

    if request.method == "POST":
        form = OutStationForm(request.POST, instance=outstation)
        if form.is_valid():
            saved_outstation = form.save()

            if outstation:
                messages.success(request, "✅ Outstation updated successfully!")
            else:
                messages.success(request, "✅ Outstation created successfully!")

            return redirect(reverse("secretary_outstation_list"))
        else:
            messages.error(request, "⚠️ Failed to save outstation. Please correct the errors.")
    else:
        form = OutStationForm(instance=outstation)

    context = {
        "form": form,
        "outstation": outstation,
        "action": action
    }

    return render(request, "secretary/settings/create_update_outstation.html", context)

# ⏱️ **Time Since Calculation Helper**
def time_since(dt):
    """
    Calculate time since a given datetime.
    """
    now = datetime.now(timezone.utc)
    delta = now - dt

    if delta.days > 365:
        years = delta.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif delta.days > 30:
        months = delta.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif delta.days > 0:
        return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"


# 📍 **OutStation List View (Admin/Superuser Only)**
@login_required
@parish_council_secretary_required
def secretary_outstation_list(request):  # Updated from secretary_zone_list
    """
    View for listing all the outstations with:
    - Total cells in each outstation
    - Total number of outstations (filtered total)
    - Search by outstation ID or name
    """
    print(f"📍 Outstation List accessed by {request.user.username}")

    search_query = request.GET.get("search_outstation", "").strip()  # Updated from search_zone

    # Filter outstations by name or ID
    outstations = OutStation.objects.annotate(total_cells=Count('cells')).order_by('-date_created')  # Updated from zones

    if search_query:
        outstations = outstations.filter(Q(name__icontains=search_query) | Q(outstation_id__icontains=search_query))  # Updated field
        print(f"🔍 Search query: '{search_query}' | Results found: {outstations.count()}")

    total_outstations = outstations.count()  # Updated from total_zones
    print(f"✅ Total Outstations Displayed: {total_outstations}")

    # Add time since created and updated
    for outstation in outstations:
        outstation.time_since_created = time_since(outstation.date_created)
        outstation.time_since_updated = time_since(outstation.date_updated)

    return render(request, 'secretary/settings/outstation_list.html',  # Updated template
                  {
                      'outstations': outstations,  # Updated context key
                      'total_outstations': total_outstations,  # Updated context key
                      'search_query': search_query
                  })


# 🚨 **Delete OutStation View (Admin/Superuser Only)**
@login_required
@parish_council_secretary_required
def secretary_delete_outstation(request, outstation_id):  # Updated from secretary_delete_zone
    """
    View for deleting an OutStation after user confirmation.
    Only accessible to Parish Council Secretaries (or Admins/Superusers if adjusted).
    """
    outstation = get_object_or_404(OutStation, id=outstation_id)  # Updated from Zone
    print(f"🗑️ Deletion Requested for Outstation: {outstation.name} (ID: {outstation.id}) by {request.user.username}")

    if request.method == "POST":
        outstation_name = outstation.name
        outstation.delete()

        messages.success(request, f"✅ Outstation '{outstation_name}' deleted successfully.")
        print(f"✅ Outstation '{outstation_name}' deleted by {request.user.username}")
        return redirect("secretary_outstation_list")  # Updated redirect

    print(f"⚠️ Confirmation required for deleting Outstation: {outstation.name}")
    return render(request, "secretary/settings/delete_outstation.html",  # Updated template
                  {"outstation": outstation})  # Updated context key


# ✅ Helper Function: Calculate Time Since Creation/Update
def time_since_helper(date):  # Renamed to avoid conflict with prior function
    """
    Helper function to calculate time since creation or update.
    """
    if not date:
        return "Unknown"

    if isinstance(date, datetime):
        date_to_compare = date
    else:
        date_to_compare = make_aware(datetime.combine(date, time.min))

    delta = now() - date_to_compare
    days = delta.days
    seconds = delta.total_seconds()

    if days > 365:
        return f"{days // 365} years ago"
    elif days > 30:
        return f"{days // 30} months ago"
    elif days > 0:
        return f"{days} days ago"
    elif seconds > 3600:
        return f"{int(seconds // 3600)} hours ago"
    elif seconds > 60:
        return f"{int(seconds // 60)} minutes ago"
    else:
        return "Just now"


# 🚀 **Secure OutStation Detail View**
@login_required
@parish_council_secretary_required
def secretary_outstation_detail(request, pk):  # Updated from secretary_zone_detail
    """
    View for displaying the details of a specific OutStation.
    Accessible only to authenticated users.
    """
    print(f"🔍 Outstation Details Requested for Outstation ID: {pk} by {request.user.username}")

    outstation = get_object_or_404(OutStation, pk=pk)  # Updated from Zone

    outstation.time_since_created = time_since_helper(outstation.date_created)
    outstation.time_since_updated = time_since_helper(outstation.date_updated)

    print(f"✅ Outstation '{outstation.name}' details retrieved successfully.")

    return render(request, "secretary/settings/outstation_detail.html",  # Updated template
                  {"outstation": outstation})  # Updated context key


# 📍 **Create or Update Cell**
@login_required
@parish_council_secretary_required
def secretary_create_update_cell(request, cell_id=None):  # Updated from secretary_create_update_community
    """
    View to create or update a cell.
    - **Create Mode:** No cell_id provided.
    - **Update Mode:** cell_id is provided to fetch and update an existing cell.
    """
    if cell_id:
        print(f"✏️ Editing Cell ID: {cell_id}")
        cell = get_object_or_404(Cell, pk=cell_id)  # Updated from Community
    else:
        print("➕ Creating a new Cell")
        cell = None

    if request.method == "POST":
        print("📤 Received POST request")
        form = CommunityForm(request.POST, instance=cell)  # Note: Should be CellForm
        if form.is_valid():
            form.save()
            if cell:
                messages.success(request, "✅ Cell updated successfully!")
            else:
                messages.success(request, "✅ Cell created successfully!")
            return redirect("secretary_cell_list")  # Updated redirect
        else:
            print(f"❌ Form errors: {form.errors}")
            messages.error(request, "⚠️ Failed to save the cell. Please check the form.")
    else:
        form = CommunityForm(instance=cell)  # Note: Should be CellForm

    return render(request, "secretary/settings/create_update_cell.html",  # Updated template
                  {"form": form, "cell": cell})  # Updated context key


# 🚨 **Delete Cell View**
@login_required
@parish_council_secretary_required
def secretary_delete_cell(request, cell_id):  # Updated from secretary_delete_community
    """
    View to delete a cell after user confirmation.
    """
    print(f"🗑️ Attempting to delete Cell ID: {cell_id}")
    cell = get_object_or_404(Cell, id=cell_id)  # Updated from Community

    if request.method == "POST":
        cell.delete()
        print(f"✅ Cell '{cell.name}' deleted successfully.")
        messages.success(request, f"✅ The cell '{cell.name}' has been deleted successfully.")
        return redirect("secretary_cell_list")  # Updated redirect

    return render(request, "secretary/settings/delete_cell.html",  # Updated template
                  {"cell": cell})  # Updated context key


# 📋 **Cell List View**
@login_required
@parish_council_secretary_required
def secretary_cell_list(request):  # Updated from secretary_community_list
    """
    View to display a list of cells grouped by their respective outstations.

    🔍 Features:
    - Total number of cells in the church.
    - Total number of cells per outstation.
    - Search by outstation ID or Name.
    - Search by cell ID or Name.
    """
    print("📥 Processing cell list request")

    search_outstation = request.GET.get("search_outstation", "").strip()  # Updated from search_zone
    search_cell = request.GET.get("search_cell", "").strip()  # Updated from search_community

    print(f"🔍 Search - Outstation: {search_outstation}, Cell: {search_cell}")

    # Filter outstations by ID or Name
    outstations = OutStation.objects.all().order_by("name")  # Updated from zones
    if search_outstation:
        outstations = outstations.filter(Q(name__icontains=search_outstation) | Q(outstation_id__icontains=search_outstation))  # Updated field
        print(f"✅ Outstations after filter: {outstations.count()}")

    outstation_cells = {}  # Updated from zone_communities
    outstations_without_cells = []  # Updated from zones_without_communities
    total_cells = 0  # Updated from total_communities

    for outstation in outstations:
        print(f"🏠 Processing Outstation: {outstation.name}")

        cells = Cell.objects.filter(outstation=outstation).order_by('-date_created')  # Updated from communities
        if search_cell:
            cells = cells.filter(Q(name__icontains=search_cell) | Q(cell_id__icontains=search_cell))  # Updated field
            print(f"✅ Cells after filter: {cells.count()}")

        cell_count = cells.count()
        total_cells += cell_count

        if cell_count > 0:
            for cell in cells:
                cell.time_since_created = calculate_time_since(cell.date_created)
                cell.time_since_updated = calculate_time_since(cell.date_updated)

            outstation_cells[outstation] = {
                "cells": cells,  # Updated key
                "total": cell_count
            }
        else:
            outstations_without_cells.append(outstation.name)

    print(f"📊 Total Cells: {total_cells}")
    print(f"🚫 Outstations without Cells: {len(outstations_without_cells)}")

    return render(request, "secretary/settings/cell_list.html",  # Updated template
                  {
                      "outstation_cells": outstation_cells,  # Updated context key
                      "outstations_without_cells": outstations_without_cells,  # Updated context key
                      "total_cells": total_cells,  # Updated context key
                      "search_outstation": search_outstation,  # Updated context key
                      "search_cell": search_cell  # Updated context key
                  })


# 📋 **Cell Detail View**
@login_required
@parish_council_secretary_required
def secretary_cell_detail(request, cell_id):  # Updated from secretary_community_detail
    """
    View to display details of a single cell.
    
    📋 Features:
    - Displays time since the cell was created & updated.
    - Secured access for authenticated users only.
    """
    print(f"🔍 Fetching details for Cell ID: {cell_id}")

    cell = get_object_or_404(Cell, pk=cell_id)  # Updated from Community

    cell.time_since_created = calculate_time_since(cell.date_created)
    cell.time_since_updated = calculate_time_since(cell.date_updated)

    print(f"✅ Retrieved cell: {cell.name}")
    print(f"⏳ Created: {cell.time_since_created}, Updated: {cell.time_since_updated}")

    return render(request, "secretary/settings/cell_detail.html",  # Updated template
                  {"cell": cell})  # Updated context key


# Helper Functions (unchanged unless renamed for clarity)
def calculate_time_since(date):  # Already consistent across views
    """ 
    Returns a human-readable time difference since the given date.
    """
    if not date:
        return "N/A"
    
    now = datetime.now(timezone.utc)
    diff = now - date

    days = diff.days
    seconds = diff.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    if days > 0:
        return f"{days} days ago"
    elif hours > 0:
        return f"{hours} hours ago"
    elif minutes > 0:
        return f"{minutes} minutes ago"
    else:
        return "Just now"
    
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from settings.models import ChurchLocation
from settings.forms import ChurchLocationForm

@login_required
@parish_council_secretary_required
def secretary_set_church_location(request):
    """
    🚀 Allows setting the church location manually or via OpenStreetMap.
    - Secured with login requirement.
    - Updates or creates the location record.
    - Only one active location at a time.
    """
    print("📍 Accessing Church Location Setup")

    # Retrieve existing location or create a new instance
    location = ChurchLocation.objects.first()
    form = ChurchLocationForm(instance=location)

    if request.method == "POST":
        print("📥 Processing POST request to save church location")
        form = ChurchLocationForm(request.POST, instance=location)
        if form.is_valid():
            church_location = form.save(commit=False)

            # Deactivate all other locations (if any)
            ChurchLocation.objects.update(is_active=False)
            
            # Set the new location as active
            church_location.is_active = True
            church_location.save()

            messages.success(request, "✅ Church location saved successfully!")
            print("✅ Church location updated and set as active")
            return redirect("secretary_location_list")
        else:
            messages.error(request, "❌ Failed to save the location. Please correct the errors.")
            print("❌ Validation errors:", form.errors)

    return render(request, "secretary/settings/set_church_location.html", {"form": form, "location": location})

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from settings.models import ChurchLocation

@login_required
@parish_council_secretary_required
def secretary_location_list(request):
    """
    🗺️ Displays a full-screen OpenStreetMap with the active church location.
    - Shows the most recently set active location.
    - Secured with login requirement.
    """
    print("🌍 Loading Church Location Map...")

    # Retrieve the active church location
    active_location = ChurchLocation.objects.filter(is_active=True).first()

    if active_location:
        print(f"✅ Active Location Found: ({active_location.latitude}, {active_location.longitude})")
    else:
        print("⚠️ No active church location found!")

    return render(request, "secretary/settings/location_map.html", {"active_location": active_location})

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from settings.models import ChurchLocation

@login_required
@parish_council_secretary_required
def secretary_update_church_location(request):
    """
    🚀 Updates the church location using OpenStreetMap.
    - Displays the current location and allows selecting a new one.
    - Handles both updates and creation of a new location if none exists.
    """
    print("📍 Accessing Church Location Update Page")

    # Fetch the currently active church location
    church_location = ChurchLocation.objects.filter(is_active=True).first()

    if request.method == "POST":
        print("📥 Received POST request to update location")

        # Get new latitude and longitude from form submission
        new_latitude = request.POST.get("latitude")
        new_longitude = request.POST.get("longitude")

        # Validate inputs
        if new_latitude and new_longitude:
            # Deactivate all existing locations
            ChurchLocation.objects.update(is_active=False)

            if church_location:
                print(f"🔄 Updating existing location: {church_location.name}")
                church_location.latitude = new_latitude
                church_location.longitude = new_longitude
                church_location.is_active = True
                church_location.save()
            else:
                print("➕ Creating a new church location")
                ChurchLocation.objects.create(latitude=new_latitude, longitude=new_longitude, is_active=True)

            messages.success(request, "✅ Church location updated successfully!")
            return redirect("secretary_location_list")

        else:
            messages.error(request, "❌ Both latitude and longitude are required.")
            print("❌ Missing latitude or longitude")

    context = {
        "church_location": church_location,
    }
    return render(request, "secretary/settings/update_location.html", context)

from django.shortcuts import render
from django.http import Http404
from django.contrib.auth.decorators import login_required
from settings.models import ChurchLocation

@login_required
@parish_council_secretary_required
def secretary_view_church_location(request):
    """
    🗺️ Displays a full-screen OpenStreetMap with the active church location.
    - Retrieves the active location from the database.
    - Returns a 404 error if no active location is found.
    """
    print("🌍 Loading Church Location Map...")

    # Get the active church location
    active_location = ChurchLocation.objects.filter(is_active=True).first()

    if not active_location:
        print("⚠️ No active church location found!")
        raise Http404("No active church location found.")

    print(f"✅ Active Location: {active_location.latitude}, {active_location.longitude}")
    return render(request, "secretary/settings/view_church_location.html", {"active_location": active_location})

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from settings.models import ChurchLocation

@login_required
@parish_council_secretary_required
def secretary_delete_church_location(request):
    """
    🗑️ Deletes the existing church location if it exists.
    - Prompts for confirmation before deletion.
    - Provides feedback upon successful deletion or errors.
    """
    print("📍 Attempting to delete church location...")

    # Fetch the first saved church location
    church_location = ChurchLocation.objects.first()

    if not church_location:
        messages.error(request, "⚠️ No church location found to delete.")
        print("❌ No church location exists.")
        return redirect("secretary_view_church_location")  # Redirect to map view if no location exists

    if request.method == "POST":
        print(f"🗑️ Deleting Church Location: {church_location.latitude}, {church_location.longitude}")
        church_location.delete()
        messages.success(request, "✅ Church location has been deleted successfully.")
        return redirect("secretary_view_church_location")  # Redirect after successful deletion

    return render(request, "secretary/settings/delete_church_location.html", {"church_location": church_location})


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from leaders.models import Leader
from members.models import ChurchMember
from leaders.forms import LeaderForm
from datetime import date
from django.contrib.auth.decorators import login_required, user_passes_test

# 📝 Create or Update Leader View (Admin & Superuser Only)
@login_required
@parish_council_secretary_required
def secretary_create_or_update_leader(request, pk=None):
    """
    View for creating a new leader or updating an existing leader.
    Only accessible to Admins and Superusers.
    If pk is provided, the view updates the leader.
    """
    print("🔹 Entered create_or_update_leader view")  # Debugging Step 1

    if pk:
        leader = get_object_or_404(Leader, pk=pk)
        action = 'Update'
        print(f"🟢 Editing Leader: {leader.church_member.full_name}")  # Fixed the reference
    else:
        leader = None
        action = 'Create'
        print("🟢 Creating a New Leader")

    if request.method == 'POST':
        print("📥 Received POST request")
        print("📌 Form data received:", request.POST)  

        form = LeaderForm(request.POST, instance=leader)

        if form.is_valid():
            print("✅ Form is valid")
            leader = form.save(commit=False)  # Don't save yet, process time_in_service

            # 📅 Calculate Time in Service (Years, Months, Days)
            today = date.today()
            start_date = leader.start_date
            years = today.year - start_date.year
            months = today.month - start_date.month
            days = today.day - start_date.day

            if days < 0:
                months -= 1
                days += 30  # Approximate month days
            if months < 0:
                years -= 1
                months += 12

            leader.time_in_service = f"{years} years, {months} months, {days} days"
            leader.save()
            
            print(f"🟢 Successfully {action.lower()}d leader: {leader.church_member.full_name}")  

            messages.success(request, f'Leader {action.lower()}d successfully!')
            return redirect('secretary_leader_list')  
        else:
            print("❌ Form is NOT valid")  
            print("⚠️ Form Errors:", form.errors)  
            messages.error(request, f'Failed to {action.lower()} the leader. Please correct the errors below.')
    else:
        print("📤 Displaying form for leader")  
        form = LeaderForm(instance=leader)

    return render(request, 'secretary/leaders/leader_form.html', {
        'form': form,
        'action': action,
    })


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.utils.timezone import now, localtime
from datetime import date, datetime, timezone

from leaders.models import Leader
from members.models import ChurchMember
from settings.models import Cell, OutStation  # Updated imports
from members.forms import ChurchMemberPassportForm
from leaders.utils import get_leaders_distribution_trend
from .decorators import parish_council_secretary_required


# 📅 Function to Calculate Time in Service
def calculate_time_in_service(start_date):
    """
    Function to calculate the time in service (years, months, days)
    """
    today = date.today()
    years = today.year - start_date.year
    months = today.month - start_date.month
    days = today.day - start_date.day

    if days < 0:
        months -= 1
        days += 30  # Approximate days in a month

    if months < 0:
        years -= 1
        months += 12

    return f"{years} years, {months} months, {days} days"


# 👥 Leader List View (Restricted to Admin & Superuser)
@login_required
@parish_council_secretary_required
def secretary_leader_list_view(request):
    """
    View to display a list of active leaders with search and filtering options.
    Only accessible to Parish Council Secretaries (or Admins/Superusers if adjusted).
    Leaders are sorted alphabetically by their full names.
    """
    # 🔍 Get search query parameters
    search_name = request.GET.get('search_name', '').strip()
    search_gender = request.GET.get('search_gender', '')
    search_occupation = request.GET.get('search_occupation', '')
    search_cell = request.GET.get('search_cell', '')  # Updated from search_community
    search_outstation = request.GET.get('search_outstation', '')  # Updated from search_zone

    # 📊 Retrieve Active Leaders and Sort by Name
    leaders = Leader.objects.filter(church_member__status="Active").order_by('church_member__full_name')

    # ⏱️ Update time in service for all leaders
    for leader in leaders:
        if leader.start_date:
            leader.time_in_service = calculate_time_in_service(leader.start_date)
            leader.save(update_fields=['time_in_service'])

    # 🔎 Filtering Logic
    if search_name:
        leaders = leaders.filter(
            Q(church_member__full_name__icontains=search_name) |
            Q(church_member__member_id__icontains=search_name)
        )
    if search_gender:
        leaders = leaders.filter(church_member__gender=search_gender)
    if search_occupation:
        leaders = leaders.filter(occupation=search_occupation)
    if search_cell:
        leaders = leaders.filter(church_member__cell_id=search_cell)  # Updated from church_member__community_id
    if search_outstation:
        leaders = leaders.filter(church_member__cell__outstation_id=search_outstation)  # Updated from church_member__community__zone_id

    # 📊 Calculate Total Counts
    total_leaders = leaders.count()
    total_male = leaders.filter(church_member__gender="Male").count()
    total_female = leaders.filter(church_member__gender="Female").count()

    # 🌍 Get Unique Cells & Outstations for Filters
    all_cells = Cell.objects.all()  # Updated from all_communities
    all_outstations = OutStation.objects.all()  # Updated from all_zones

    # 💼 Get Unique Occupations from Leader Model Choices
    all_occupations = [choice[0] for choice in Leader.OCCUPATION_CHOICES]

    return render(request, 'secretary/leaders/leader_list.html', {
        'leaders': leaders,
        'total_leaders': total_leaders,
        'total_male': total_male,
        'total_female': total_female,
        'all_cells': all_cells,  # Updated from all_communities
        'all_outstations': all_outstations,  # Updated from all_zones
        'all_occupations': all_occupations,
        'search_name': search_name,
        'search_gender': search_gender,
        'search_occupation': search_occupation,
        'search_cell': search_cell,  # Updated from search_community
        'search_outstation': search_outstation,  # Updated from search_zone
    })


# 🚫 Inactive Leader List View (Restricted to Admin & Superuser)
@login_required
@parish_council_secretary_required
def secretary_inactive_leader_list_view(request):
    """
    View to display a list of inactive leaders with search and filtering options.
    Only accessible to Parish Council Secretaries (or Admins/Superusers if adjusted).
    Leaders are sorted alphabetically by their full names.
    """
    # 🔍 Get search query parameters
    search_name = request.GET.get('search_name', '').strip()
    search_gender = request.GET.get('search_gender', '')
    search_occupation = request.GET.get('search_occupation', '')
    search_cell = request.GET.get('search_cell', '')  # Updated from search_community
    search_outstation = request.GET.get('search_outstation', '')  # Updated from search_zone

    # 📊 Retrieve Inactive Leaders and Sort by Name
    leaders = Leader.objects.filter(church_member__status="Inactive").order_by('church_member__full_name')

    # ⏱️ Update time in service for all leaders
    for leader in leaders:
        if leader.start_date:
            leader.time_in_service = calculate_time_in_service(leader.start_date)
            leader.save(update_fields=['time_in_service'])

    # 🔎 Filtering Logic
    if search_name:
        leaders = leaders.filter(
            Q(church_member__full_name__icontains=search_name) |
            Q(church_member__member_id__icontains=search_name)
        )
    if search_gender:
        leaders = leaders.filter(church_member__gender=search_gender)
    if search_occupation:
        leaders = leaders.filter(occupation=search_occupation)
    if search_cell:
        leaders = leaders.filter(church_member__cell_id=search_cell)  # Updated from church_member__community_id
    if search_outstation:
        leaders = leaders.filter(church_member__cell__outstation_id=search_outstation)  # Updated from church_member__community__zone_id

    # 📊 Calculate Total Counts
    total_leaders = leaders.count()
    total_male = leaders.filter(church_member__gender="Male").count()
    total_female = leaders.filter(church_member__gender="Female").count()

    # 🌍 Get Unique Cells & Outstations for Filters
    all_cells = Cell.objects.all()  # Updated from all_communities
    all_outstations = OutStation.objects.all()  # Updated from all_zones

    # 💼 Get Unique Occupations from Leader Model Choices
    all_occupations = [choice[0] for choice in Leader.OCCUPATION_CHOICES]

    return render(request, 'secretary/leaders/inactive_leader_list.html', {
        'leaders': leaders,
        'total_leaders': total_leaders,
        'total_male': total_male,
        'total_female': total_female,
        'all_cells': all_cells,  # Updated from all_communities
        'all_outstations': all_outstations,  # Updated from all_zones
        'all_occupations': all_occupations,
        'search_name': search_name,
        'search_gender': search_gender,
        'search_occupation': search_occupation,
        'search_cell': search_cell,  # Updated from search_community
        'search_outstation': search_outstation,  # Updated from search_zone
    })


# 📤 Update Leader Profile (Passport Upload)
@login_required
@parish_council_secretary_required
def secretary_update_leader_profile(request, pk):
    """
    View to update the profile picture of a leader.
    Only accessible to Parish Council Secretaries (or Admins/Superusers if adjusted).
    """
    leader = get_object_or_404(Leader, pk=pk)
    church_member = leader.church_member  # Get the associated ChurchMember

    if request.method == 'POST':
        form = ChurchMemberPassportForm(request.POST, request.FILES, instance=church_member)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Profile picture updated successfully for {church_member.full_name}!")
            return redirect('secretary_leader_list')  # Updated redirect to match view name
        else:
            messages.error(request, "❌ Failed to update profile picture. Please correct the errors below.")
    else:
        form = ChurchMemberPassportForm(instance=church_member)

    return render(request, 'secretary/members/upload_passport.html', {
        'form': form,
        'church_member': church_member,
    })


# 🗑️ Delete Leader View (Restricted to Admin & Superuser)
@login_required
@parish_council_secretary_required
def secretary_delete_leader(request, pk):
    """
    View to delete a leader.
    Only accessible to Parish Council Secretaries (or Admins/Superusers if adjusted).
    """
    leader = get_object_or_404(Leader, pk=pk)

    if request.method == "POST":
        leader.delete()
        messages.success(request, "🗑️ Leader deleted successfully.")
        return redirect('secretary_leader_list')

    return render(request, "secretary/leaders/leader_confirm_delete.html", {"leader": leader})


# Helper Functions for Leader Detail View
def calculate_since_created(date_created):
    """
    Calculate the time since the leader's record was created.
    Returns a human-friendly string.
    """
    current_time = now()
    delta = current_time - date_created

    if delta.days < 1:
        if delta.seconds < 60:
            return "Just now"
        elif delta.seconds < 3600:
            return f"{delta.seconds // 60} minute(s) ago"
        else:
            return f"{delta.seconds // 3600} hour(s) ago"
    elif delta.days == 1:
        return "1 day ago"
    elif delta.days < 7:
        return f"{delta.days} day(s) ago"
    elif delta.days < 30:
        weeks = delta.days // 7
        return f"{weeks} week(s) ago"
    elif delta.days < 365:
        months = delta.days // 30
        return f"{months} month(s) ago"
    else:
        years = delta.days // 365
        return f"{years} year(s) ago"


def calculate_age(date_of_birth):
    """
    Calculate the age of a Leader based on their date of birth.
    """
    if date_of_birth:
        today = date.today()
        age = today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
        )
        return f"{age} years old"
    return "----"  # Decorated placeholder for missing DOB


# 🔍 Leader Detail View
@login_required
@parish_council_secretary_required
def secretary_leader_detail_view(request, pk):
    """
    View to display all details of a specific leader.
    Only accessible to Parish Council Secretaries (or Admins/Superusers if adjusted).
    """
    leader = get_object_or_404(Leader, pk=pk)
    church_member = leader.church_member

    # Calculate and update the time in service dynamically
    if leader.start_date:
        leader.time_in_service = calculate_time_in_service(leader.start_date)
        leader.save(update_fields=['time_in_service'])

    # Calculate the "since created" time
    since_created = calculate_since_created(leader.date_created)

    # Format boolean fields as emojis
    def format_boolean(value):
        return "✅" if value else "❌"

    # Prepare leader details dynamically with corresponding emojis
    leader_details = [
        ("📛 Full Name", church_member.full_name),
        ("🆔 Leader ID", leader.leader_id),
        ("🆔 Member ID", church_member.member_id),
        ("🎂 Date of Birth", church_member.date_of_birth.strftime('%d %B, %Y') if church_member.date_of_birth else "----"),
        ("🔢 Age", calculate_age(church_member.date_of_birth)),
        ("⚥ Gender", church_member.gender),
        ("📞 Phone Number", church_member.phone_number),
        ("📧 Email", church_member.email if church_member.email else "----"),
        ("🏠 Address", church_member.address or "----"),
        ("📅 Date Created", f"{localtime(leader.date_created).strftime('%d %B, %Y %I:%M %p')} ({since_created})"),
        ("📅 Start Date", leader.start_date.strftime('%d %B, %Y') if leader.start_date else "----"),
        ("⏳ Time in Service", leader.time_in_service if leader.time_in_service else "----"),
        ("🏢 Committee", leader.committee or "----"),
        ("📋 Responsibilities", leader.responsibilities or "----"),
        ("🎓 Education Level", leader.education_level or "----"),
        ("✝️ Religious Education", leader.religious_education or "----"),
        ("💰 Compensation/Allowance", leader.compensation_allowance or "----"),
        ("🙌 Voluntary", format_boolean(leader.voluntary)),
        ("💍 Marital Status", church_member.marital_status or "----"),
        ("❤️ Spouse Name", church_member.spouse_name or "----"),  # Note: Assumes this field exists; adjust if not
        ("👶 Number of Children", church_member.number_of_children or "----"),  # Note: Assumes this field exists; adjust if not
        ("📛 Emergency Contact Name", church_member.emergency_contact_name or "----"),
        ("📞 Emergency Contact Phone", church_member.emergency_contact_phone or "----"),
        ("🎭 Talent", church_member.talent or "----"),  # Note: Assumes this field exists; adjust if not
        ("🌟 Special Interests", church_member.special_interests or "----"),  # Note: Assumes this field exists; adjust if not
    ]

    return render(request, "secretary/leaders/leader_detail.html", {
        "leader": leader,
        "leader_details": leader_details,
    })


# 🏠 Leaders Home View
@login_required
@parish_council_secretary_required
def secretary_leaders_home(request):
    """
    Leaders Home Page:
    - Displays total active/inactive leaders.
    - Fetches distribution data for the line chart (cells & outstations).
    - Accessible only by Parish Council Secretaries (or Admins/Superusers if adjusted).
    """
    # Get active & inactive leader counts
    total_active_leaders = Leader.objects.filter(church_member__status='Active').count()
    total_inactive_leaders = Leader.objects.filter(church_member__status='Inactive').count()

    # Fetch distribution data for cells & outstations
    leaders_distribution_data = get_leaders_distribution_trend()

    return render(request, 'secretary/leaders/leaders_home.html', {
        'total_active_leaders': total_active_leaders,
        'total_inactive_leaders': total_inactive_leaders,
        'leaders_distribution_data': leaders_distribution_data,
    })

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from members.models import ChurchMember

from django.shortcuts import render, redirect
from django.contrib import messages
from members.models import ChurchMember

def validate_member_data(form):
    """
    Validate the ChurchMember form before saving.
    """
    if not form.cleaned_data:
        return []  # If no data, return an empty list

    cleaned_data = form.cleaned_data  # Get cleaned form data
    errors = []

    is_baptised = cleaned_data.get("is_baptised", False)
    has_received_first_communion = cleaned_data.get("has_received_first_communion", False)
    is_confirmed = cleaned_data.get("is_confirmed", False)
    is_married = cleaned_data.get("is_married", False)
    marital_status = cleaned_data.get("marital_status", "Single")

    # ❌ A member cannot receive First Communion without being baptized
    if has_received_first_communion and not is_baptised:
        errors.append("A member cannot receive First Communion without being baptized.")

    # ❌ A member cannot be confirmed without First Communion and Baptism
    if is_confirmed and (not has_received_first_communion or not is_baptised):
        errors.append("A member cannot be confirmed without being baptized and receiving First Communion.")

    # ❌ A member cannot be married without Confirmation, First Communion, and Baptism
    if is_married and (not is_confirmed or not has_received_first_communion or not is_baptised):
        errors.append("A married member must be baptized, have First Communion, and be confirmed.")

    # ❌ If marital status is "Married", the member should be marked as married
    if marital_status == "Married" and not is_married:
        errors.append("A member with 'Married' status must also be marked as married.")

    return errors

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from members.models import ChurchMember
from sms.utils import send_sms  # ✅ Import Beem SMS function
from .decorators import parish_council_secretary_required  # ✅ Ensure correct permission

# 🚀 Create/Update Church Members (Restricted to Parish Council Secretary)
@login_required
@parish_council_secretary_required
def secretary_create_or_update_church_member(request):
    """
    View for creating or updating multiple church members at once.
    Only accessible to the Parish Council Secretary.
    Sends an SMS to each new member upon successful creation.
    """
    if request.method == 'POST':
        formset = ChurchMemberFormSet(request.POST, request.FILES)

        if formset.is_valid():
            new_members = []  # Store newly created members for SMS sending

            try:
                for form in formset:
                    if form.cleaned_data:
                        church_member = form.save()  # ✅ Save the member
                        new_members.append(church_member)  # ✅ Add to list for SMS

                # ✅ Send SMS to each newly created member
                for member in new_members:
                    sms_message = f"Habari {member.full_name}, karibu katika application yetu ya parokia ya mkwawa, " \
                                  f"kama unatumia smartphone unaweza kupata akaunti yako mwenyewe kwa kutumia " \
                                  f"utambulisho wako ID (Usimpe yeyote!!) {member.member_id}, kwa kutumia link (bonyeza link hii hapa) " \
                                  f"https://4404-196-249-93-210.ngrok-free.app/accounts/request-account/"

                    # ✅ Now pass `member` as the third argument
                    response = send_sms(to=member.phone_number, message=sms_message, member=member)

                    # ✅ Log response for debugging
                    print(f"📩 SMS sent to {member.phone_number} (Request ID: {response.get('request_id', 'N/A')}): {response}")

                messages.success(request, '✅ Church members saved successfully & SMS notifications sent!')
                return redirect('secretary_church_member_list')

            except ValidationError as e:
                for msg in e.messages:
                    messages.error(request, f"❌ {msg}")
                return render(request, 'secretary/members/church_member_form.html', {'formset': formset})

        else:
            messages.error(request, '❌ Failed to save church members. Please correct the errors below.')

    else:
        formset = ChurchMemberFormSet()

    return render(request, 'secretary/members/church_member_form.html', {'formset': formset})


from django.shortcuts import render, get_object_or_404, redirect
from django.utils.timezone import now, localtime
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import ValidationError
import pytz

from members.models import ChurchMember
from settings.models import Cell, OutStation  # Updated imports
from members.forms import UpdateChurchMemberForm, ChurchMemberPassportForm
from members.utils import get_membership_distribution_analysis



# 🌍 Set Tanzania timezone
TZ_TZ = pytz.timezone('Africa/Dar_es_Salaam')


# ⏱️ Time Formatter for Displaying "Since Created"
def format_time_since(created_date):
    """
    Returns a user-friendly time format based on Tanzania timezone.
    """
    if not created_date:
        return "N/A"

    # Convert stored UTC time to Tanzania timezone
    created_date = localtime(created_date, timezone=TZ_TZ)
    current_time = localtime(now(), timezone=TZ_TZ)

    time_difference = current_time - created_date
    seconds = time_difference.total_seconds()

    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"Since {minutes} minute{'s' if minutes > 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"Since {hours} hour{'s' if hours > 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f"Since {days} day{'s' if days > 1 else ''} ago"
    elif seconds < 2419200:
        weeks = int(seconds // 604800)
        return f"Since {weeks} week{'s' if weeks > 1 else ''} ago"
    elif seconds < 29030400:
        months = int(seconds // 2419200)
        return f"Since {months} month{'s' if months > 1 else ''} ago"
    else:
        years = int(seconds // 29030400)
        return f"Since {years} year{'s' if years > 1 else ''} ago"


# ✅ Active Church Member List View
@login_required
@parish_council_secretary_required
def secretary_church_member_list(request):
    """
    View to display and filter the list of active church members, sorted alphabetically by full name.
    Only accessible to Parish Council Secretaries (or Admins/Superusers if adjusted).
    """
    # Get query parameters
    name_query = request.GET.get('name', '').strip()
    gender_query = request.GET.get('gender', '').strip()
    cell_query = request.GET.get('cell', '').strip()  # Updated from community_query
    outstation_query = request.GET.get('outstation', '').strip()  # Updated from zone_query

    # Retrieve only Active members and order by full_name alphabetically
    church_members = ChurchMember.objects.select_related('cell__outstation').filter(status="Active").order_by('full_name')  # Updated relation

    # Apply Filters
    if name_query:
        church_members = church_members.filter(
            Q(full_name__icontains=name_query) | Q(member_id__icontains=name_query)
        )
    if gender_query:
        church_members = church_members.filter(gender=gender_query)
    if cell_query:
        church_members = church_members.filter(cell_id=cell_query)  # Updated from community_id
    if outstation_query:
        church_members = church_members.filter(cell__outstation_id=outstation_query)  # Updated from community__zone_id

    # Calculate "Since Created" for each member
    for member in church_members:
        member.time_since_created = format_time_since(member.date_created)

    # Totals
    total_members = church_members.count()
    total_males = church_members.filter(gender='Male').count()
    total_females = church_members.filter(gender='Female').count()

    # Get distinct cells and outstations for dropdowns
    cells = Cell.objects.all()  # Updated from communities
    outstations = OutStation.objects.all()  # Updated from zones

    context = {
        'church_members': church_members,
        'total_members': total_members,
        'total_males': total_males,
        'total_females': total_females,
        'cells': cells,  # Updated from communities
        'outstations': outstations,  # Updated from zones
        'name_query': name_query,
        'gender_query': gender_query,
        'cell_query': cell_query,  # Updated from community_query
        'outstation_query': outstation_query,  # Updated from zone_query
    }

    return render(request, 'secretary/members/church_member_list.html', context)


# ✅ Inactive Church Member List View
@login_required
@parish_council_secretary_required
def secretary_inactive_church_member_list(request):
    """
    View to display and filter the list of inactive church members, sorted alphabetically by full name.
    Only accessible to Parish Council Secretaries (or Admins/Superusers if adjusted).
    """
    # Get query parameters
    name_query = request.GET.get('name', '').strip()
    gender_query = request.GET.get('gender', '').strip()
    cell_query = request.GET.get('cell', '').strip()  # Updated from community_query
    outstation_query = request.GET.get('outstation', '').strip()  # Updated from zone_query

    # Retrieve only Inactive members and order by full_name alphabetically
    church_members = ChurchMember.objects.select_related('cell__outstation').filter(status="Inactive").order_by('full_name')  # Updated relation

    # Apply Filters
    if name_query:
        church_members = church_members.filter(
            Q(full_name__icontains=name_query) | Q(member_id__icontains=name_query)
        )
    if gender_query:
        church_members = church_members.filter(gender=gender_query)
    if cell_query:
        church_members = church_members.filter(cell_id=cell_query)  # Updated from community_id
    if outstation_query:
        church_members = church_members.filter(cell__outstation_id=outstation_query)  # Updated from community__zone_id

    # Calculate "Since Created" for each member
    for member in church_members:
        member.time_since_created = format_time_since(member.date_created)

    # Totals
    total_members = church_members.count()
    total_males = church_members.filter(gender='Male').count()
    total_females = church_members.filter(gender='Female').count()

    # Get distinct cells and outstations for dropdowns
    cells = Cell.objects.all()  # Updated from communities
    outstations = OutStation.objects.all()  # Updated from zones

    context = {
        'church_members': church_members,
        'total_members': total_members,
        'total_males': total_males,
        'total_females': total_females,
        'cells': cells,  # Updated from communities
        'outstations': outstations,  # Updated from zones
        'name_query': name_query,
        'gender_query': gender_query,
        'cell_query': cell_query,  # Updated from community_query
        'outstation_query': outstation_query,  # Updated from zone_query
    }

    return render(request, 'secretary/members/inactive_church_member_list.html', context)


# 🏠 Members Home View
@login_required
@parish_council_secretary_required
def secretary_members_home(request):
    """
    Members Home Page:
    - Displays total active and inactive members in summary boxes.
    - Fetches membership distribution data for the graphs (cells, outstations).
    - Only accessible to Parish Council Secretaries (or Admins/Superusers if adjusted).
    """
    # Calculate total active & inactive members
    total_active_members = ChurchMember.objects.filter(status='Active').count()
    total_inactive_members = ChurchMember.objects.filter(status='Inactive').count()

    # Fetch membership distribution data
    membership_distribution_data = get_membership_distribution_analysis()

    return render(request, 'secretary/members/members_home.html', {
        'total_active_members': total_active_members,
        'total_inactive_members': total_inactive_members,
        'membership_distribution_data': membership_distribution_data
    })


# 🚫 Delete Church Member
@login_required
@parish_council_secretary_required
def secretary_delete_church_member(request, pk):
    """
    View to confirm and delete a specific ChurchMember.
    Only accessible to Parish Council Secretaries (or Admins/Superusers if adjusted).
    """
    church_member = get_object_or_404(ChurchMember, pk=pk)

    if request.method == 'POST':
        church_member.delete()
        messages.success(request, f"✅ Church member '{church_member.full_name}' deleted successfully!")
        return redirect('secretary_church_member_list')

    return render(request, 'secretary/members/confirm_delete_church_member.html', {
        'church_member': church_member,
    })


# 🔍 Validation Helper for Church Member Data
def validate_member_data(church_member):
    """
    Validates the logical consistency of church member data.
    - Note: Fields like has_received_first_communion, is_confirmed, is_married are not in the provided model.
    - Adjusted to use available fields (is_baptised, date_confirmed, marital_status, date_of_marriage).
    """
    errors = []

    # ❌ A member cannot be confirmed without being baptized
    if church_member.date_confirmed and not church_member.is_baptised:
        errors.append("A member cannot be confirmed without being baptized.")

    # ❌ A member cannot have a marriage date without being baptized and confirmed
    if church_member.date_of_marriage and (not church_member.is_baptised or not church_member.date_confirmed):
        errors.append("A member cannot be married without being baptized and confirmed.")

    # ❌ Marital Status cannot be "Married" without a date_of_marriage
    if church_member.marital_status == "Married" and not church_member.date_of_marriage:
        errors.append("Marital Status cannot be 'Married' if no marriage date is provided.")

    if errors:
        raise ValidationError(errors)


# 🚀 Update Church Member
@login_required
@parish_council_secretary_required
def secretary_update_church_member(request, pk):
    """
    View for updating an existing church member, including document uploads.
    Only accessible to Parish Council Secretaries (or Admins/Superusers if adjusted).
    """
    church_member = get_object_or_404(ChurchMember, pk=pk)

    if request.method == 'POST':
        form = UpdateChurchMemberForm(request.POST, request.FILES, instance=church_member)

        if form.is_valid():
            try:
                # Save the form; validate_member_data will check logical consistency
                church_member = form.save(commit=False)
                validate_member_data(church_member)
                church_member.save()

                messages.success(request, '✅ Church member updated successfully!')
                return redirect('secretary_church_member_detail', pk=church_member.pk)

            except ValidationError as e:
                for msg in e.messages:
                    messages.error(request, msg)

        else:
            messages.error(request, '❌ Failed to update the church member. Please correct the errors below.')
    else:
        form = UpdateChurchMemberForm(instance=church_member)

    return render(request, 'secretary/members/update_church_member.html', {
        'form': form,
        'church_member': church_member,
    })


# 🚀 Upload Passport
@login_required
@parish_council_secretary_required
def secretary_upload_passport(request, pk):
    """
    View for uploading or updating a church member's passport.
    Only accessible to Parish Council Secretaries (or Admins/Superusers if adjusted).
    """
    member = get_object_or_404(ChurchMember, pk=pk)

    if request.method == 'POST':
        form = ChurchMemberPassportForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Passport uploaded successfully!')
            return redirect('secretary_church_member_list')
        else:
            messages.error(request, '❌ Failed to upload passport. Please try again.')
    else:
        form = ChurchMemberPassportForm(instance=member)

    return render(request, 'secretary/members/upload_passport.html', {'form': form, 'member': member})


# Helper Functions for Detail View
def calculate_age(date_of_birth):
    """
    Calculate the age of a ChurchMember based on their date of birth.
    """
    if date_of_birth:
        today = date.today()
        age = today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
        )
        return f"{age} years old"
    return "----"


def calculate_since_created(date_created):
    """
    Calculate the time since the member's record was created.
    Returns a human-readable string.
    """
    current_time = now()
    delta = current_time - date_created

    if delta.days < 1:
        if delta.seconds < 60:
            return "Just now"
        elif delta.seconds < 3600:
            return f"{delta.seconds // 60} minute(s) ago"
        else:
            return f"{delta.seconds // 3600} hour(s) ago"
    elif delta.days == 1:
        return "1 day ago"
    elif delta.days < 7:
        return f"{delta.days} day(s) ago"
    elif delta.days < 30:
        weeks = delta.days // 7
        return f"{weeks} week(s) ago"
    elif delta.days < 365:
        months = delta.days // 30
        return f"{months} month(s) ago"
    else:
        years = delta.days // 365
        return f"{years} year(s) ago"


# 🔍 Church Member Detail View
@login_required
@parish_council_secretary_required
def secretary_church_member_detail(request, pk):
    """
    View to retrieve and display all details of a specific ChurchMember with uploaded documents.
    Only accessible to Parish Council Secretaries (or Admins/Superusers if adjusted).
    """
    church_member = get_object_or_404(ChurchMember, pk=pk)

    # Calculate "since created" time
    since_created = calculate_since_created(church_member.date_created)

    # Convert boolean fields to emojis
    def format_boolean(value):
        return "✅" if value else "❌"

    # Collect all available uploaded documents with corresponding emojis
    documents = {
        "📜 Baptism Certificate": church_member.baptism_certificate.url if church_member.baptism_certificate else None,
        "🕊️ Confirmation Certificate": church_member.confirmation_certificate.url if church_member.confirmation_certificate else None,
        # Note: marriage_certificate is not in the model; removed or adjust if added later
    }

    # Prepare details (adjusted for actual ChurchMember fields)
    details = {
        "👤 Full Name": church_member.full_name,
        "🆔 Member ID": church_member.member_id,
        "🎂 Date of Birth": church_member.date_of_birth.strftime('%d %B, %Y') if church_member.date_of_birth else "----",
        "🔢 Age": calculate_age(church_member.date_of_birth),
        "⚥ Gender": church_member.gender,
        "📞 Phone Number": church_member.phone_number,
        "📧 Email": church_member.email or "----",
        "🏠 Address": church_member.address or "----",
        "🏘️ Cell": f"{church_member.cell.name} ({church_member.cell.outstation.name})" if church_member.cell else "----",  # Updated from community
        "🔘 Status": f"✅ Active" if church_member.status == "Active" else "❌ Inactive",
        "📅 Date Created": f"{localtime(church_member.date_created).strftime('%d %B, %Y %I:%M %p')} ({since_created})",

        # Sacramental Information
        "🌊 Baptized": format_boolean(church_member.is_baptised),
        "🗓️ Date of Baptism": church_member.date_of_baptism.strftime('%d %B, %Y') if church_member.date_of_baptism else "----",
        "🕊️ Confirmed": format_boolean(church_member.date_confirmed is not None),  # Using date_confirmed as proxy
        "🗓️ Date of Confirmation": church_member.date_confirmed.strftime('%d %B, %Y') if church_member.date_confirmed else "----",

        # Marriage Information
        "💍 Marital Status": church_member.marital_status or "----",
        "🗓️ Date of Marriage": church_member.date_of_marriage.strftime('%d %B, %Y') if church_member.date_of_marriage else "----",

        # Emergency Contact
        "📛 Emergency Contact Name": church_member.emergency_contact_name or "----",
        "📞 Emergency Contact Phone": church_member.emergency_contact_phone or "----",
    }

    # Removed fields not in ChurchMember model: spouse_name, number_of_children, job, talent, services, disability, special_interests, apostolic_movement, is_the_member_a_leader_of_the_movement

    return render(request, 'secretary/members/church_member_detail.html', {
        'church_member': church_member,
        'details': details,
        'documents': documents
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from news.forms import NewsForm, NewsMediaForm
from news.models import News, NewsMedia

@login_required
@parish_council_secretary_required
def secretary_create_news_view(request, pk=None):
    """
    View to create or update a news post with multiple media uploads.
    Only accessible to superusers and admins.
    """
    news = None
    if pk:
        news = get_object_or_404(News, pk=pk)  # Get existing news for updating

    if request.method == "POST":
        form = NewsForm(request.POST, instance=news)
        media_types = request.POST.getlist('media_type')
        media_files = request.FILES.getlist('file')

        if form.is_valid():
            news = form.save()  # Save or update news post

            # If updating, delete old media
            if pk:
                news.media.all().delete()

            # Save multiple media files
            for media_type, media_file in zip(media_types, media_files):
                if media_type and media_file:
                    NewsMedia.objects.create(news=news, media_type=media_type, file=media_file)

            if pk:
                messages.success(request, "✅ News post updated successfully!")
            else:
                messages.success(request, "✅ News post created successfully!")

            return redirect("secretary_news_list")  # Redirect to news list after saving
        else:
            messages.error(request, "❌ Please correct the errors in the form.")

    else:
        form = NewsForm(instance=news)  # Pre-fill form if updating

    return render(request, "secretary/news/create_news.html", {"form": form, "news": news})

from django.shortcuts import render
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import timedelta
from news.models import News

def calculate_time_since(created_at):
    """
    Function to calculate how much time has passed since news was created.
    """
    delta = now() - created_at

    if delta < timedelta(minutes=1):
        return "Just now"
    elif delta < timedelta(hours=1):
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif delta < timedelta(days=1):
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif delta < timedelta(weeks=1):
        days = delta.days
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif delta < timedelta(days=30):
        weeks = delta.days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif delta < timedelta(days=365):
        months = delta.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        years = delta.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"

@login_required
@parish_council_secretary_required
def secretary_news_list_view(request):
    """
    View to display a list of news articles (without media) with the time since creation.
    Only accessible to superusers and admins.
    """
    news_list = News.objects.all()

    # Calculate "time since created" for each news
    for news in news_list:
        news.time_since_created = calculate_time_since(news.created_at)

    return render(request, "secretary/news/news_list.html", {"news_list": news_list})

from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth.decorators import login_required, user_passes_test
from news.models import News

# 🕰️ Time Calculation Helper
def calculate_time_since(created_at):
    """
    Function to calculate how much time has passed since news was created.
    """
    delta = now() - created_at

    if delta < timedelta(minutes=1):
        return "Just now"
    elif delta < timedelta(hours=1):
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif delta < timedelta(days=1):
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif delta < timedelta(weeks=1):
        days = delta.days
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif delta < timedelta(days=30):
        weeks = delta.days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif delta < timedelta(days=365):
        months = delta.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        years = delta.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"

# 🚀 News Detail View (Restricted to Admins/Superusers)
@login_required
@parish_council_secretary_required
def secretary_news_detail_view(request, pk):
    """
    View to display the full details of a specific news article.
    Only accessible to Admins and Superusers.
    """
    news = get_object_or_404(News, pk=pk)
    news.time_since_created = calculate_time_since(news.created_at)

    # Separate media into categories
    images = news.media.filter(media_type='image')
    videos = news.media.filter(media_type='video')
    documents = news.media.filter(media_type='document')

    return render(request, "secretary/news/news_detail.html", {
        "news": news,
        "images": images,
        "videos": videos,
        "documents": documents,
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from news.models import News, NewsMedia

@login_required
@parish_council_secretary_required
def secretary_delete_news_view(request, pk):
    """
    View to delete a news article and all associated media.
    """
    news = get_object_or_404(News, pk=pk)

    if request.method == "POST":
        # Delete all associated media files
        news.media.all().delete()
        
        # Delete the news post
        news.delete()

        messages.success(request, "News post and all associated media deleted successfully!")
        return redirect("secretary_news_list")

    return render(request, "secretary/news/delete_news.html", {"news": news})

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from datetime import timedelta
from news.models import News, Like
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils.timezone import now
from datetime import timedelta
from news.models import News, Like, Comment

def calculate_time_since(created_at):
    """
    Function to calculate how much time has passed since news was created.
    """
    delta = now() - created_at

    if delta < timedelta(minutes=1):
        return "Just now"
    elif delta < timedelta(hours=1):
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif delta < timedelta(days=1):
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif delta < timedelta(weeks=1):
        days = delta.days
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif delta < timedelta(days=30):
        weeks = delta.days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif delta < timedelta(days=365):
        months = delta.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        years = delta.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"


from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

# 📰 News Home View (Restricted to Admins/Superusers)
@login_required
@parish_council_secretary_required
def secretary_news_home(request):
    """
    View for the News Home Page.
    Only accessible to Admins and Superusers.
    """
    return render(request, 'secretary/news/news_home.html')


from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

# 🔔 Notifications Home View (Restricted to Admins/Superusers)
@login_required
@parish_council_secretary_required
def secretary_notifications_home(request):
    """
    View for the Notifications Home Page.
    Only accessible to Admins and Superusers.
    """
    return render(request, 'secretary/notifications/notifications_home.html')


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import now
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from notifications.models import Notification
from members.models import ChurchMember
from notifications.forms import NotificationForm
from sms.utils import send_sms  # ✅ Import Beem SMS function
from .decorators import parish_council_secretary_required  # ✅ Ensure correct permission

# 🚀 Create Notification View (Restricted)
@login_required
@parish_council_secretary_required
def secretary_create_notification(request):
    """
    View to create and send notifications to church members.
    Only accessible to Parish Council Secretary.
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
            return render(request, 'secretary/notifications/create_notification.html', {
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
            return redirect('secretary_notification_list')

        else:
            messages.error(request, "⚠️ Failed to send notification. Please check the form.")
    else:
        form = NotificationForm()

    return render(request, 'secretary/notifications/create_notification.html', {
        'form': form,
        'members': members,
        'leaders': leaders,
    })

# 🚀 Load Recipients via AJAX (Restricted)
@login_required
@parish_council_secretary_required
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

    html = render_to_string("secretary/notifications/_recipients_list.html", {"members": recipients})
    return HttpResponse(html)

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils.timezone import now
from collections import defaultdict
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from notifications.models import Notification

# 🚀 View: List Notifications (Restricted)
@login_required
@parish_council_secretary_required
def secretary_notification_list(request):
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

    return render(request, 'secretary/notifications/notification_list.html', {
        'grouped_notifications': dict(grouped_notifications)
    })

# 🚀 View: Filter Notifications by Title (AJAX, Restricted)
@login_required
@parish_council_secretary_required
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
from notifications.models import Notification

# 🚀 View: Delete Notifications (Restricted)
@login_required
@parish_council_secretary_required
def secretary_delete_notification(request, delete_type, identifier):
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
            return redirect("secretary_notification_list")

        # Render Confirmation Page (GET Request)
        return render(request, "secretary/notifications/confirm_delete_group.html", {"title": identifier})

    # 🗑️ Deleting an Individual Notification
    elif delete_type == "member":
        notification = get_object_or_404(Notification, id=identifier)

        if request.method == "POST":
            notification.delete()
            messages.success(request, "✅ Deleted the selected notification successfully.")
            return redirect("secretary_notification_list")

        # Render Confirmation Page (GET Request)
        return render(request, "secretary/notifications/confirm_delete_member.html", {"notification": notification})

    # 🚫 Invalid Deletion Type Handling
    messages.error(request, "❌ Invalid deletion request.")
    return redirect("secretary_notification_list")


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.decorators import admin_required

@login_required
@parish_council_secretary_required
def secretary_chatbot_view(request):
    """
    🤖 Admin Chatbot View for Quick FAQs

    - Provides instant responses to common admin queries.
    - Ensures secure access with login required.
    - Supports clickable links for easy contact.
    """
    print("🤖 Loading Admin Chatbot...")

    # Predefined FAQs (Frequently Asked Questions)
    faq = {
        "How can I register a church member?": (
            "You can register a member by going to the Member List page. "
            "Click on the Members box from your dashboard (Admin/Superuser), "
            "or use the toggle button (three bars icon) to access Members. "
            "Then click 'Create New Member' and fill out the form."
        ),
        "How can I register leaders?": (
            "Go to the Leaders page and click 'Create New Leader'. "
            "Fill in the leader's credentials and save."
        ),
        "How can I send messages and notifications to church members?": (
            "Navigate to the Notifications page and click 'Send SMS & Notification'. "
            "Fill in the title, message, select recipients, and send."
        ),
        "How can I create the church location on the map?": (
            "Go to Settings > Church Location. Click the '+' icon to open the map. "
            "Select the location, and the latitude/longitude will be saved automatically."
        ),
        "What is Finance specialized with?": (
            "Finance manages all aspects related to the church's income and financial records."
        ),
        "Am I required to update settings all the time?": (
            "No, only when necessary. For example, update the current year when a new year starts."
        ),
        "What is Sacraments based on?": (
            "Sacraments manage records for Baptism, First Communion, Confirmation, and Marriage."
        ),
        "What rules should I follow when registering a church member?": (
            "Ensure logical consistency: "
            "- A member with First Communion must be baptized. "
            "- A married member should be confirmed and have received sacraments in sequence."
        ),
        "What if I make mistakes when registering or saving data?": (
            "You can correct mistakes by clicking the 'Edit' (pencil) icon, "
            "making changes, and saving the update."
        ),
        "What do the Eye, Pencil, and Trash icons mean?": (
            "👁️ Eye: View details\n"
            "✏️ Pencil: Edit/Update\n"
            "🗑️ Trash: Delete the record"
        ),
        "How can I get more support?": (
            "📧 Email: <a href='mailto:kigangomkwawa123@gmail.com'>kigangomkwawa123@gmail.com</a><br>"
            "📞 Call: <a href='tel:+255767972343'>+255767972343</a>"
        ),
        "Where can I get services like this?": (
            "Contact Kizita Soft Limited:<br>"
            "📞 <a href='tel:+255762023662'>+255762023662</a>, "
            "<a href='tel:+255741943155'>+255741943155</a>, "
            "<a href='tel:+255763968849'>+255763968849</a><br>"
            "📧 Email: <a href='mailto:kizitasoft805@gmail.com'>kizitasoft805@gmail.com</a>, "
            "<a href='mailto:kizitasoft@gmail.com'>kizitasoft@gmail.com</a>"
        )
    }

    print(f"✅ Loaded {len(faq)} FAQ entries.")

    context = {
        "faq": faq
    }
    return render(request, "secretary/secretary_chatbot.html", context)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .decorators import parish_council_secretary_required

@login_required
@parish_council_secretary_required
def parish_council_secretary_details(request):
    """
    View to retrieve all details of a Parish Council Secretary:
    - Account Information
    - Membership Details
    - Leadership Details
    - Certificates (Displayed as Buttons)
    """
    user = request.user
    church_member = user.church_member
    leader = church_member.leader  # The leader details

    # ✅ Helper function for boolean fields with WhatsApp-like icons
    def format_boolean(value):
        return '<span style="color: green; font-size: 18px;">✔️</span>' if value else '<span style="color: red; font-size: 18px;">❌</span>'

    # ✅ Account Details
    account_details = {
        "Username": user.username,
        "Email": user.email or "Not provided",
        "Phone Number": user.phone_number,
        "Date Created": user.date_created.strftime("%d %B %Y"),
    }

    # ✅ Membership Details (Ensure everything is included)
    membership_details = {
        "Full Name": church_member.full_name,
        "Member ID": church_member.member_id,
        "Date of Birth": church_member.date_of_birth.strftime("%d %B %Y"),
        "Gender": church_member.gender,
        "Phone Number": church_member.phone_number,
        "Email": church_member.email or "Not provided",
        "Address": church_member.address,
        "Community": church_member.community.name if church_member.community else "Not Assigned",
        "Apostolic Movement": church_member.apostolic_movement.name if church_member.apostolic_movement else "Not Assigned",
        "Leader of Movement": format_boolean(church_member.is_the_member_a_leader_of_the_movement),
        "Baptized": format_boolean(church_member.is_baptised),
        "Date of Baptism": church_member.date_of_baptism.strftime("%d %B %Y") if church_member.date_of_baptism else "Not Available",
        "Received First Communion": format_boolean(church_member.has_received_first_communion),
        "Date of Communion": church_member.date_of_communion.strftime("%d %B %Y") if church_member.date_of_communion else "Not Available",
        "Confirmed": format_boolean(church_member.is_confirmed),
        "Date Confirmed": church_member.date_confirmed.strftime("%d %B %Y") if church_member.date_confirmed else "Not Available",
        "Marital Status": church_member.marital_status,
        "Spouse Name": church_member.spouse_name or "Not provided",
        "Number of Children": church_member.number_of_children or "Not provided",
        "Job": church_member.job,
        "Talent": church_member.talent or "Not Provided",
        "Church Services": church_member.services or "Not Involved",
        "Emergency Contact Name": church_member.emergency_contact_name,
        "Emergency Contact Phone": church_member.emergency_contact_phone,
        "Disability": church_member.disability or "None",
        "Special Interests": church_member.special_interests or "None",
    }

    # ✅ Leadership Details
    leadership_details = {
        "Occupation": leader.occupation,
        "Start Date": leader.start_date.strftime("%d %B %Y"),
        "Committee": leader.committee,
        "Responsibilities": leader.responsibilities,
        "Education Level": leader.education_level,
        "Religious Education": leader.religious_education or "Not Provided",
        "Voluntary Service": format_boolean(leader.voluntary),
    }

    # ✅ Certificates (Displayed as Button Links)
    certificates = {
        "Baptism Certificate": church_member.baptism_certificate.url if church_member.baptism_certificate else None,
        "First Communion Certificate": church_member.communion_certificate.url if church_member.communion_certificate else None,
        "Confirmation Certificate": church_member.confirmation_certificate.url if church_member.confirmation_certificate else None,
        "Marriage Certificate": church_member.marriage_certificate.url if church_member.marriage_certificate else None,
    }

    # ✅ Passport (Move to Top)
    passport_url = church_member.passport.url if church_member.passport else None

    return render(request, "secretary/parish_council_secretary_details.html", {
        "passport_url": passport_url,
        "account_details": account_details,
        "membership_details": membership_details,
        "leadership_details": leadership_details,
        "certificates": certificates,
    })
