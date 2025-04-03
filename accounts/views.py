from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.utils.timezone import now
from .forms import LoginForm
from .utils import authenticate_with_username_or_email, get_client_ip
from .models import LoginHistory
from django.contrib.auth.decorators import login_required
from leaders.models import Leader
from django.urls import reverse

def login_view(request):
    # 🛑 If user is already authenticated, redirect them properly
    if request.user.is_authenticated:
        last_path = request.session.get('last_visited_path')

        # Prevent login redirect loop
        if not last_path or last_path in get_ignored_paths():
            return handle_user_redirection(request.user)

        return redirect(last_path)

    form = LoginForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            username_or_email = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # ✅ Authenticate
            user = authenticate_with_username_or_email(username_or_email, password)

            if user is not None:
                # ✅ Check if user is ACTIVE (unless they are superuser/admin)
                if not user.is_superuser and user.user_type == 'CHURCH_MEMBER':
                    if not user.church_member or user.church_member.status != 'Active':
                        messages.error(request, '❌ Your account is inactive. Contact admin for assistance.')
                        return render(request, 'accounts/login.html', {'form': form})

                login(request, user)

                # ✅ Store login record
                login_record = LoginHistory.objects.create(
                    user=user,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )

                # ✅ Retrieve last visited path
                last_path = request.session.pop('last_visited_path', None)
                if last_path and last_path not in get_ignored_paths():
                    return redirect(last_path)

                # ✅ Redirect based on user role
                return handle_user_redirection(user)

            else:
                messages.error(request, '❌ Invalid username/email or password.')

    return render(request, 'accounts/login.html', {'form': form})

def get_ignored_paths():
    """ Returns a list of paths that should be ignored in redirection. """
    return [
        reverse('login'),
        reverse('request_account'),
        reverse('forgot_password'),
        reverse('welcome'),
        reverse('public_news_list'),
    ]

def get_user_last_path(user, current_login_id):
    """
    Fetch last_visited_path from the most recent *previous* login record.
    Ignore the latest record because it's the one we just created.
    """
    prior_records = user.login_history.exclude(pk=current_login_id).order_by('-login_time')

    if prior_records.exists():
        last_path = prior_records.first().last_visited_path
        if last_path and last_path not in get_ignored_paths():
            return last_path
    return None

def handle_user_redirection(user):
    """
    Redirect user to the appropriate dashboard based on role.
    """
    # ✅ Admins go directly to the Admin Dashboard
    if user.is_superuser or user.user_type == 'ADMIN':
        return redirect('admin_dashboard')

    # ✅ Church Members (must be active)
    if user.user_type == 'CHURCH_MEMBER':
        if hasattr(user.church_member, 'leader'):  # Check if the user is a leader
            leader = user.church_member.leader

            # ✅ Redirect based on occupation
            if leader.occupation == 'Senior Pastor':
                return redirect('pastor_dashboard')
            elif leader.occupation == 'Evangelist':
                return redirect('evangelist_dashboard')
            elif leader.occupation == 'Parish Council Secretary':
                return redirect('secretary_dashboard')
            elif leader.occupation == 'Parish Treasurer':
                return redirect('accountant_dashboard')

        # ✅ Default church member dashboard
        return redirect('member_dashboard')

    # ✅ If no valid role is found, return to login
    return redirect('login')


@login_required
def logout_view(request):
    """
    Logs the user out, deletes all session data, clears login history,
    and redirects to the appropriate dashboard.
    """
    user = request.user

    # ✅ Delete all login history records for the user
    LoginHistory.objects.filter(user=user).delete()

    # ✅ Flush session to remove stored data and authentication info
    request.session.flush()

    # ✅ Redirect user to their appropriate dashboard
    return handle_user_redirection(user)

from django.shortcuts import render
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required, user_passes_test
from settings.models import Year
from .utils import (
    get_general_finance_analysis,
    get_general_sacraments_analysis,
    get_general_properties_analysis,
    get_account_completion_analysis,
    get_leaders_distribution_analysis,
    get_members_distribution_analysis,
    get_general_data_analysis  # Import the new function
)

# ✅ Helper Function: Check if user is Admin or Superuser
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required(login_url='login')
@user_passes_test(is_admin_or_superuser, login_url='login')
def admin_dashboard(request):
    """
    Admin Dashboard View:
    - Fetches General Finance, Sacraments, Properties, Account Completion,
      Leaders, Members Distribution & General Data Analysis Data.
    - Updates the system's current year.
    """
    current_system_year = now().year  # Get the current system year

    # Check the current year in the database
    current_year_entry = Year.objects.filter(is_current=True).first()

    if current_year_entry:
        if current_year_entry.year != current_system_year:
            # Unset outdated year
            current_year_entry.is_current = False
            current_year_entry.save()

            # Set the new current year
            new_year_entry, created = Year.objects.get_or_create(year=current_system_year)
            new_year_entry.is_current = True
            new_year_entry.save()
    else:
        # No current year exists, create a new one
        Year.objects.create(year=current_system_year, is_current=True)

    # Fetch all data
    general_finance_data = get_general_finance_analysis()
    general_sacraments_data = get_general_sacraments_analysis()
    general_properties_data = get_general_properties_analysis()
    account_completion_data = get_account_completion_analysis(request.user)
    leaders_distribution_data = get_leaders_distribution_analysis()
    members_distribution_data = get_members_distribution_analysis()
    general_data_analysis = get_general_data_analysis()

    return render(request, 'accounts/admin_dashboard.html', {
        'general_finance_data': general_finance_data,
        'general_sacraments_data': general_sacraments_data,
        'general_properties_data': general_properties_data,
        'account_completion_data': account_completion_data,
        'leaders_distribution_data': leaders_distribution_data,
        'members_distribution_data': members_distribution_data,
        'general_data_analysis': general_data_analysis
    })


from django.shortcuts import render
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required, user_passes_test
from settings.models import Year
from .utils import (
    get_general_finance_analysis,
    get_general_sacraments_analysis,
    get_general_properties_analysis,
    get_account_completion_analysis,
    get_leaders_distribution_analysis,
    get_members_distribution_analysis,
    get_general_data_analysis  # Import the new function
)

@login_required(login_url='login')  # Redirect to login if not logged in
def secretary_dashboard(request):
    """
    Admin Dashboard View:
    - Fetches General Finance, Sacraments, Properties, Account Completion,
      Leaders, Members Distribution & General Data Analysis Data.
    - Updates the system's current year.
    """
    current_system_year = now().year  # Get the current system year

    # Check the current year in the database
    current_year_entry = Year.objects.filter(is_current=True).first()

    if current_year_entry:
        if current_year_entry.year != current_system_year:
            # Unset outdated year
            current_year_entry.is_current = False
            current_year_entry.save()

            # Set the new current year
            new_year_entry, created = Year.objects.get_or_create(year=current_system_year)
            new_year_entry.is_current = True
            new_year_entry.save()
    else:
        # No current year exists, create a new one
        Year.objects.create(year=current_system_year, is_current=True)

    # Fetch all data
    general_finance_data = get_general_finance_analysis()
    general_sacraments_data = get_general_sacraments_analysis()
    general_properties_data = get_general_properties_analysis()
    account_completion_data = get_account_completion_analysis(request.user)
    leaders_distribution_data = get_leaders_distribution_analysis()
    members_distribution_data = get_members_distribution_analysis()
    general_data_analysis = get_general_data_analysis()

    return render(request, 'accounts/secretary_dashboard.html', {
        'general_sacraments_data': general_sacraments_data,
        'general_properties_data': general_properties_data,
        'leaders_distribution_data': leaders_distribution_data,
        'members_distribution_data': members_distribution_data,
    })


from django.shortcuts import render
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required, user_passes_test
from settings.models import Year
from .utils import (
    get_general_finance_analysis,
    get_general_sacraments_analysis,
    get_general_properties_analysis,
    get_account_completion_analysis,
    get_leaders_distribution_analysis,
    get_members_distribution_analysis,
    get_general_data_analysis  # Import the new function
)

@login_required(login_url='login')
def accountant_dashboard(request):
    """
    Admin Dashboard View:
    - Fetches General Finance, Sacraments, Properties, Account Completion,
      Leaders, Members Distribution & General Data Analysis Data.
    - Updates the system's current year.
    """
    current_system_year = now().year  # Get the current system year

    # Check the current year in the database
    current_year_entry = Year.objects.filter(is_current=True).first()

    if current_year_entry:
        if current_year_entry.year != current_system_year:
            # Unset outdated year
            current_year_entry.is_current = False
            current_year_entry.save()

            # Set the new current year
            new_year_entry, created = Year.objects.get_or_create(year=current_system_year)
            new_year_entry.is_current = True
            new_year_entry.save()
    else:
        # No current year exists, create a new one
        Year.objects.create(year=current_system_year, is_current=True)

    # Fetch all data
    general_finance_data = get_general_finance_analysis()
    general_sacraments_data = get_general_sacraments_analysis()
    general_properties_data = get_general_properties_analysis()
    account_completion_data = get_account_completion_analysis(request.user)
    leaders_distribution_data = get_leaders_distribution_analysis()
    members_distribution_data = get_members_distribution_analysis()
    general_data_analysis = get_general_data_analysis()

    return render(request, 'accounts/accountant_dashboard.html', {
        'general_finance_data': general_finance_data,
        'general_sacraments_data': general_sacraments_data,
        'general_properties_data': general_properties_data,
        'account_completion_data': account_completion_data,
        'leaders_distribution_data': leaders_distribution_data,
        'members_distribution_data': members_distribution_data,
        'general_data_analysis': general_data_analysis
    })

@login_required
def member_dashboard(request):
    return render(request, 'accounts/member_dashboard.html')

# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

# ✅ Helper Function: Allow Only Admins and Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required(login_url='login')  # Redirect to login if not logged in
@user_passes_test(is_admin_or_superuser, login_url='login')  # Restrict access to Admins/Superusers
def upload_profile_picture(request):
    """
    View to handle profile picture uploads.
    Only accessible by Admins and Superusers.
    """
    if request.method == 'POST':
        uploaded_file = request.FILES.get('cameraInput') or request.FILES.get('fileInput')
        if uploaded_file:
            # Save the uploaded file to the user's profile picture
            request.user.profile_picture.save(
                uploaded_file.name,
                uploaded_file,
                save=True
            )
            messages.success(request, '✅ Profile picture uploaded successfully!')
            return redirect('admin_dashboard')
        else:
            messages.error(request, '❌ No file uploaded. Please select a file and try again.')

    return render(request, 'accounts/upload_profile_picture.html')


@login_required(login_url='login')  # Redirect to login if not logged in
def pastor_upload_profile_picture(request):
    """
    View to handle profile picture uploads.
    Only accessible by Admins and Superusers.
    """
    if request.method == 'POST':
        uploaded_file = request.FILES.get('cameraInput') or request.FILES.get('fileInput')
        if uploaded_file:
            # Save the uploaded file to the user's profile picture
            request.user.profile_picture.save(
                uploaded_file.name,
                uploaded_file,
                save=True
            )
            messages.success(request, '✅ Profile picture uploaded successfully!')
            return redirect('pastor_dashboard')
        else:
            messages.error(request, '❌ No file uploaded. Please select a file and try again.')

    return render(request, 'accounts/pastor_upload_profile_picture.html')

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required
def remove_profile_picture(request):
    if request.method == "POST":
        user = request.user
        if user.profile_picture:
            user.profile_picture.delete()  # Deletes the file
            user.profile_picture = None  # Clears the field
            user.save()
            return JsonResponse({"success": True})
        return JsonResponse({"error": "No profile picture found"}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=400)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import CustomUser

def is_admin_or_superuser(user):
    """ Helper function to check if the user is a superuser or has the ADMIN role. """
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required
@user_passes_test(is_admin_or_superuser)  # Restrict access to superusers and admins
def superuser_detail_view(request):
    """
    View to display all details of the currently logged-in superuser or admin.
    """
    user = request.user  # Get the logged-in superuser/admin

    # Ensure profile picture URL is safely checked
    profile_picture_url = user.profile_picture.url if user.profile_picture else None

    superuser_details = [
        ("📛 Username", user.username),
        ("📧 Email", user.email if user.email else "N/A"),
        ("📞 Phone Number", user.phone_number),
        ("🛠 User Type", dict(user.USER_TYPES).get(user.user_type, "Unknown Role")),
        ("📅 Date Created", user.date_created),
    ]

    return render(request, "accounts/superuser_detail.html", {
        "user": user,
        "profile_picture_url": profile_picture_url,
        "superuser_details": superuser_details,
    })

from django.shortcuts import render, redirect
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import AdminUpdateForm
from .models import CustomUser

def is_admin_or_superuser(user):
    """ Helper function to check if the user is a superuser or has the ADMIN role. """
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required
@user_passes_test(is_admin_or_superuser)  # Restrict access to superusers and admins
def admin_update_view(request):
    """
    View to allow the superuser or admin to update their profile, including username and password.
    """
    user = request.user

    if request.method == 'POST':
        form = AdminUpdateForm(request.POST, request.FILES, instance=user)

        if form.is_valid():
            user = form.save()

            # If the password was changed, update the session to prevent logout
            if form.cleaned_data.get("password"):
                update_session_auth_hash(request, user)

            messages.success(request, "Profile updated successfully!")
            return redirect('superuser_detail')  # Redirect to profile page instead of login
        else:
            messages.error(request, "Error updating profile. Please check the form.")

    else:
        form = AdminUpdateForm(instance=user)

    return render(request, "accounts/admin_update.html", {"form": form})


from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .models import CustomUser
from .forms import AccountRequestForm
from members.models import ChurchMember
from leaders.models import Leader

def request_account(request):
    """
    View to handle account requests for Church Members.
    """
    print("📌 Entered request_account view")  # Debugging Entry Point

    form = AccountRequestForm()
    member_id_valid = False
    display_message = None
    church_member = None

    if request.method == "POST":
        print("📥 Received POST request")  # Debugging Step 1
        print("📌 Form Data:", request.POST)  # Print the entire form data

        if "validate_id" in request.POST:  # Step 1: Validate Member ID
            print("🔍 Validate ID button pressed")  # Debugging Step 2
            member_id = request.POST.get("member_id", "").strip()
            print(f"🔎 Received Member ID: {member_id}")  # Debugging Step 3

            try:
                church_member = ChurchMember.objects.get(member_id=member_id)
                leader = Leader.objects.filter(church_member=church_member).first()

                member_id_valid = True  # Set flag to show the hidden fields
                display_message = f"✅ Well done, we identify you as {church_member.full_name}."
                print(f"✅ Member ID is valid: {church_member.full_name}")  # Debugging Step 4

                if leader:
                    display_message = f"✅ You are a leader: {leader.occupation} ({church_member.full_name})."
                    print(f"🎖 Leader detected: {leader.occupation}")  # Debugging Step 5

                # Pre-fill the form with validated member_id
                form = AccountRequestForm(initial={
                    'member_id': member_id, 
                    'email': church_member.email or "",
                })

            except ChurchMember.DoesNotExist:
                print("❌ Invalid Member ID: Not found in database")  # Debugging Step 6
                messages.error(request, "❌ The system does not identify you. Please contact the admin at +255767972343.")
                return render(request, "accounts/request_account.html", {"form": form})

        elif "submit_account" in request.POST:  # Step 2: Submit Full Form
            print("📤 Submit Account button pressed")  # Debugging Step 7
            form = AccountRequestForm(request.POST)

            if form.is_valid():
                print("✅ Form is valid")  # Debugging Step 8
                church_member = form.cleaned_data['member_id']
                email = form.cleaned_data['email']
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']

                # Determine user type
                leader = Leader.objects.filter(church_member=church_member).first()
                user_type = "CHURCH_MEMBER"

                # Create the user
                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    phone_number=church_member.phone_number,
                    user_type=user_type,
                    church_member=church_member,
                )
                user.set_password(password)
                user.save()

                print(f"🎉 Account successfully created for {church_member.full_name}")  # Debugging Step 9
                messages.success(request, f"🎉 Account successfully created for {church_member.full_name}. You can now log in.")
                return redirect("login")

            else:
                print("❌ Form is NOT valid")  # Debugging Step 10
                print("⚠️ Form Errors:", form.errors)  # Print form errors

    print("📤 Rendering template")  # Debugging Step 11
    return render(request, "accounts/request_account.html", {
        "form": form,
        "member_id_valid": member_id_valid,
        "display_message": display_message,
    })

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CustomUser
from .forms import ForgotPasswordForm
from members.models import ChurchMember

def forgot_password(request):
    """
    View to handle password reset for Church Members.
    """
    print("📌 Entered forgot_password view")  # Step 1: View loaded

    form = ForgotPasswordForm()
    member_id_valid = False
    display_message = None
    church_member = None

    if request.method == "POST":
        print("📥 Received POST request")  # Step 2: We received POST

        if "validate_id" in request.POST:
            print("🔍 Validate ID button clicked")  # Step 3: Validate button was actually clicked

            member_id = request.POST.get("member_id", "").strip()
            print(f"🔎 Validating Member ID: {member_id}")  # Step 4: Checking which ID was entered

            try:
                church_member = ChurchMember.objects.get(member_id=member_id)
                print(f"✅ Member found: {church_member.full_name}")  # Step 5: Found member

                user = CustomUser.objects.filter(church_member=church_member).first()

                if user:
                    member_id_valid = True  # Allow showing other fields
                    
                    # ⚠️ Displaying the previous password is a security risk, but added as per your request
                    previous_username = user.username
                    previous_password = "(Hidden for security reasons)"  # Passwords are hashed
                    
                    display_message = f"""
                        ✅ Well done! We identified you as {church_member.full_name}. with
                        🔑 Previous Username: {previous_username}
                        🔒 Previous Password: {previous_password}
                        You can reset and enter the new credentials by filling the form fields below.
                    """
                    print(f"🎉 Member has an account: {user.username}")  # Step 6

                    form = ForgotPasswordForm(initial={'member_id': member_id})

                else:
                    print("❌ No user account linked to this member.")  # Step 7
                    messages.error(request, "❌ This member does not have an account. Please request an account first.")
                    return render(request, "accounts/forgot_password.html", {"form": form})

            except ChurchMember.DoesNotExist:
                print("❌ Member ID not found in database.")  # Step 8
                messages.error(request, "❌ The system does not recognize this ID. Please contact admin at +255767972343.")
                return render(request, "accounts/forgot_password.html", {"form": form})

        elif "submit_reset" in request.POST:
            print("🔄 Processing Password Reset")  # Step 9

            form = ForgotPasswordForm(request.POST)
            if form.is_valid():
                church_member = form.cleaned_data['member_id']
                new_username = form.cleaned_data['new_username']
                new_password = form.cleaned_data['new_password']

                print(f"🔄 Updating Credentials for: {church_member.full_name}")  # Step 10

                user = CustomUser.objects.get(church_member=church_member)
                user.username = new_username
                user.set_password(new_password)
                user.save()

                print(f"✅ Credentials updated for: {user.username}")  # Step 11

                messages.success(request, f"🎉 Password reset successfully for {church_member.full_name}. You can now log in.")
                return redirect("login")

            else:
                print("❌ Form validation failed")  # Step 12
                print("⚠️ Form Errors:", form.errors)  # Step 13

    print("📤 Rendering forgot_password template")  # Step 14
    return render(request, "accounts/forgot_password.html", {
        "form": form,
        "member_id_valid": member_id_valid,
        "display_message": display_message,
        "church_member": church_member
    })


# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .decorators import church_member_required  # Import the custom decorator

@login_required
@church_member_required
def member_upload_profile_picture(request):
    """
    Allows CHURCH_MEMBER users to upload a profile picture.
    """
    if request.method == 'POST':
        uploaded_file = request.FILES.get('cameraInput') or request.FILES.get('fileInput')
        if uploaded_file:
            request.user.profile_picture.save(
                uploaded_file.name,
                uploaded_file,
                save=True
            )
            messages.success(request, '📸 Profile picture uploaded successfully!')
            return redirect('member_dashboard')
        else:
            messages.error(request, '⚠️ No file uploaded. Please select a file and try again.')

    return render(request, 'accounts/member_upload_profile_picture.html')

@login_required
@church_member_required
def member_remove_profile_picture(request):
    """
    Allows CHURCH_MEMBER users to remove their profile picture.
    """
    if request.method == "POST":
        user = request.user
        if user.profile_picture:
            user.profile_picture.delete()  # Deletes the file
            user.profile_picture = None   # Clears the database field
            user.save()
            return JsonResponse({"success": True})
        return JsonResponse({"error": "⚠️ No profile picture found."}, status=400)

    return JsonResponse({"error": "⚠️ Invalid request method."}, status=400)


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .decorators import church_member_required  # Import the custom decorator

@login_required
def secretary_upload_profile_picture(request):
    """
    Allows CHURCH_MEMBER users to upload a profile picture.
    """
    if request.method == 'POST':
        uploaded_file = request.FILES.get('cameraInput') or request.FILES.get('fileInput')
        if uploaded_file:
            request.user.profile_picture.save(
                uploaded_file.name,
                uploaded_file,
                save=True
            )
            messages.success(request, '📸 Profile picture uploaded successfully!')
            return redirect('secretary_dashboard')
        else:
            messages.error(request, '⚠️ No file uploaded. Please select a file and try again.')

    return render(request, 'accounts/secretary_upload_profile_picture.html')


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .decorators import church_member_required  # Import the custom decorator

@login_required
def accountant_upload_profile_picture(request):
    """
    Allows CHURCH_MEMBER users to upload a profile picture.
    """
    if request.method == 'POST':
        uploaded_file = request.FILES.get('cameraInput') or request.FILES.get('fileInput')
        if uploaded_file:
            request.user.profile_picture.save(
                uploaded_file.name,
                uploaded_file,
                save=True
            )
            messages.success(request, '📸 Profile picture uploaded successfully!')
            return redirect('accountant_dashboard')
        else:
            messages.error(request, '⚠️ No file uploaded. Please select a file and try again.')

    return render(request, 'accounts/accountant_upload_profile_picture.html')

from django.shortcuts import render

def welcome_page(request):
    return render(request, 'accounts/welcome.html')


from django.shortcuts import render
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required, user_passes_test
from settings.models import Year
from .utils import (
    get_general_finance_analysis,
    get_general_sacraments_analysis,
    get_general_properties_analysis,
    get_account_completion_analysis,
    get_leaders_distribution_analysis,
    get_members_distribution_analysis,
    get_general_data_analysis  # Import the new function
)


@login_required(login_url='login')
def pastor_dashboard(request):
    """
    Admin Dashboard View:
    - Fetches General Finance, Sacraments, Properties, Account Completion,
      Leaders, Members Distribution & General Data Analysis Data.
    - Updates the system's current year.
    """
    current_system_year = now().year  # Get the current system year

    # Check the current year in the database
    current_year_entry = Year.objects.filter(is_current=True).first()

    if current_year_entry:
        if current_year_entry.year != current_system_year:
            # Unset outdated year
            current_year_entry.is_current = False
            current_year_entry.save()

            # Set the new current year
            new_year_entry, created = Year.objects.get_or_create(year=current_system_year)
            new_year_entry.is_current = True
            new_year_entry.save()
    else:
        # No current year exists, create a new one
        Year.objects.create(year=current_system_year, is_current=True)

    # Fetch all data
    general_finance_data = get_general_finance_analysis()
    general_sacraments_data = get_general_sacraments_analysis()
    general_properties_data = get_general_properties_analysis()
    account_completion_data = get_account_completion_analysis(request.user)
    leaders_distribution_data = get_leaders_distribution_analysis()
    members_distribution_data = get_members_distribution_analysis()
    general_data_analysis = get_general_data_analysis()

    return render(request, 'accounts/pastor_dashboard.html', {
        'general_finance_data': general_finance_data,
        'general_sacraments_data': general_sacraments_data,
        'general_properties_data': general_properties_data,
        'account_completion_data': account_completion_data,
        'leaders_distribution_data': leaders_distribution_data,
        'members_distribution_data': members_distribution_data,
        'general_data_analysis': general_data_analysis
    })


from django.shortcuts import render
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required, user_passes_test
from settings.models import Year
from .utils import (
    get_general_finance_analysis,
    get_general_sacraments_analysis,
    get_general_properties_analysis,
    get_account_completion_analysis,
    get_leaders_distribution_analysis,
    get_members_distribution_analysis,
    get_general_data_analysis  # Import the new function
)


@login_required(login_url='login')
def evangelist_dashboard(request):
    """
    Admin Dashboard View:
    - Fetches General Finance, Sacraments, Properties, Account Completion,
      Leaders, Members Distribution & General Data Analysis Data.
    - Updates the system's current year.
    """
    current_system_year = now().year  # Get the current system year

    # Check the current year in the database
    current_year_entry = Year.objects.filter(is_current=True).first()

    if current_year_entry:
        if current_year_entry.year != current_system_year:
            # Unset outdated year
            current_year_entry.is_current = False
            current_year_entry.save()

            # Set the new current year
            new_year_entry, created = Year.objects.get_or_create(year=current_system_year)
            new_year_entry.is_current = True
            new_year_entry.save()
    else:
        # No current year exists, create a new one
        Year.objects.create(year=current_system_year, is_current=True)

    # Fetch all data
    general_finance_data = get_general_finance_analysis()
    general_sacraments_data = get_general_sacraments_analysis()
    general_properties_data = get_general_properties_analysis()
    account_completion_data = get_account_completion_analysis(request.user)
    leaders_distribution_data = get_leaders_distribution_analysis()
    members_distribution_data = get_members_distribution_analysis()
    general_data_analysis = get_general_data_analysis()

    return render(request, 'accounts/evangelist_dashboard.html', {
        'general_finance_data': general_finance_data,
        'general_sacraments_data': general_sacraments_data,
        'general_properties_data': general_properties_data,
        'account_completion_data': account_completion_data,
        'leaders_distribution_data': leaders_distribution_data,
        'members_distribution_data': members_distribution_data,
        'general_data_analysis': general_data_analysis
    })


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .decorators import church_member_required  # Import the custom decorator

@login_required
def evangelist_upload_profile_picture(request):
    """
    Allows CHURCH_MEMBER users to upload a profile picture.
    """
    if request.method == 'POST':
        uploaded_file = request.FILES.get('cameraInput') or request.FILES.get('fileInput')
        if uploaded_file:
            request.user.profile_picture.save(
                uploaded_file.name,
                uploaded_file,
                save=True
            )
            messages.success(request, '📸 Profile picture uploaded successfully!')
            return redirect('evangelist_dashboard')
        else:
            messages.error(request, '⚠️ No file uploaded. Please select a file and try again.')

    return render(request, 'accounts/evangelist_upload_profile_picture.html')

