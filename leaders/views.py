from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Leader
from members.models import ChurchMember
from .forms import LeaderForm
from datetime import date
from django.contrib.auth.decorators import login_required, user_passes_test

# ✅ Helper function to allow only Admins and Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# 📝 Create or Update Leader View (Admin & Superuser Only)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def create_or_update_leader(request, pk=None):
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
            return redirect('leader_list')  
        else:
            print("❌ Form is NOT valid")  
            print("⚠️ Form Errors:", form.errors)  
            messages.error(request, f'Failed to {action.lower()} the leader. Please correct the errors below.')
    else:
        print("📤 Displaying form for leader")  
        form = LeaderForm(instance=leader)

    return render(request, 'leaders/leader_form.html', {
        'form': form,
        'action': action,
    })


from django.shortcuts import render
from datetime import date
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from .models import Leader
from members.models import ChurchMember
from settings.models import Cell, OutStation  # Updated imports

# ✅ Helper function to allow only Admins and Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

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

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from .models import Leader
from settings.models import Cell, OutStation
from datetime import date

def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

def calculate_time_in_service(start_date):
    """
    Calculate time in service from start_date to today.
    Returns a string like '3 years, 2 months'.
    """
    today = date.today()
    years = today.year - start_date.year
    months = today.month - start_date.month
    
    if months < 0:
        years -= 1
        months += 12
    
    if years < 0:
        return "Not started yet"
    
    parts = []
    if years > 0:
        parts.append(f"{years} year{'s' if years > 1 else ''}")
    if months > 0:
        parts.append(f"{months} month{'s' if months > 1 else ''}")
    
    return ", ".join(parts) if parts else "Less than a month"

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def leader_list_view(request):
    """
    View to display a list of active leaders with search and filtering options.
    Only accessible to Admins and Superusers.
    Leaders are sorted alphabetically by their full names.
    """
    # 🔍 Get search query parameters
    search_name = request.GET.get('search_name', '').strip()
    search_gender = request.GET.get('search_gender', '')
    search_occupation = request.GET.get('search_occupation', '')
    search_cell = request.GET.get('search_cell', '')
    search_outstation = request.GET.get('search_outstation', '')

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
        leaders = leaders.filter(church_member__cell_id=search_cell)
    if search_outstation:
        leaders = leaders.filter(church_member__cell__outstation_id=search_outstation)

    # 📊 Calculate Total Counts
    total_leaders = leaders.count()
    total_male = leaders.filter(church_member__gender="Male").count()
    total_female = leaders.filter(church_member__gender="Female").count()

    # 🌍 Get Unique Cells & Outstations for Filters
    all_cells = Cell.objects.all()
    all_outstations = OutStation.objects.all()

    # 💼 Get Unique Occupations from Leader Model Choices
    all_occupations = [choice[0] for choice in Leader.OCCUPATION_CHOICES]

    return render(request, 'leaders/leader_list.html', {
        'leaders': leaders,
        'total_leaders': total_leaders,
        'total_male': total_male,
        'total_female': total_female,
        'all_cells': all_cells,
        'all_outstations': all_outstations,
        'all_occupations': all_occupations,
        'search_name': search_name,
        'search_gender': search_gender,
        'search_occupation': search_occupation,
        'search_cell': search_cell,
        'search_outstation': search_outstation,
    })


# 🚫 Inactive Leader List View (Restricted to Admin & Superuser)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def inactive_leader_list_view(request):
    """
    View to display a list of inactive leaders with search and filtering options.
    Only accessible to Admins and Superusers.
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

    return render(request, 'leaders/inactive_leader_list.html', {
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

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Leader
from members.models import ChurchMember
from members.forms import ChurchMemberPassportForm  # Import the form for passport upload

# ✅ Helper function to allow only Admins and Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# 📤 Update Leader Profile (Passport Upload)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def update_leader_profile(request, pk):
    """
    View to update the profile picture of a leader.
    Only accessible to Admins and Superusers.
    """
    leader = get_object_or_404(Leader, pk=pk)
    church_member = leader.church_member  # Get the associated ChurchMember

    if request.method == 'POST':
        form = ChurchMemberPassportForm(request.POST, request.FILES, instance=church_member)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Profile picture updated successfully for {church_member.full_name}!")
            return redirect('leader_list')  # Redirect to leader list after successful update
        else:
            messages.error(request, "❌ Failed to update profile picture. Please correct the errors below.")
    else:
        form = ChurchMemberPassportForm(instance=church_member)

    return render(request, 'members/upload_passport.html', {
        'form': form,
        'church_member': church_member,
    })


# 🗑️ Delete Leader View (Restricted to Admin & Superuser)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def delete_leader(request, pk):
    """
    View to delete a leader.
    Only accessible to Admins and Superusers.
    """
    leader = get_object_or_404(Leader, pk=pk)

    if request.method == "POST":
        leader.delete()
        messages.success(request, "🗑️ Leader deleted successfully.")
        return redirect('leader_list')

    return render(request, "leaders/leader_confirm_delete.html", {"leader": leader})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import date
from .models import Leader

def is_superuser(user):
    """ Helper function to check if the user is a superuser. """
    return user.is_authenticated and user.is_superuser

# leaders/views.py
from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now, localtime
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Leader
from datetime import date

def is_admin_or_superuser(user):
    """
    Check if the user is either a superuser or has the 'ADMIN' user_type.
    """
    return user.is_superuser or user.user_type == 'ADMIN'

def calculate_time_in_service(start_date):
    """
    Calculate time in service from start_date to today.
    Returns a string like '3 years, 2 months'.
    """
    today = date.today()
    years = today.year - start_date.year
    months = today.month - start_date.month
    
    if months < 0:
        years -= 1
        months += 12
    
    if years < 0:
        return "Not started yet"
    
    parts = []
    if years > 0:
        parts.append(f"{years} year{'s' if years > 1 else ''}")
    if months > 0:
        parts.append(f"{months} month{'s' if months > 1 else ''}")
    
    return ", ".join(parts) if parts else "Less than a month"

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
    return "----"

@login_required(login_url='/accounts/login/')
@user_passes_test(is_admin_or_superuser, login_url='/accounts/login/')
def leader_detail_view(request, pk):
    """
    View to display all details of a specific leader.
    """
    leader = get_object_or_404(Leader, pk=pk)
    church_member = leader.church_member

    # Calculate and update the time in service dynamically
    if leader.start_date:
        leader.time_in_service = calculate_time_in_service(leader.start_date)
        leader.save(update_fields=['time_in_service'])

    # Calculate the "since created" time
    since_created = calculate_since_created(leader.date_created)

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
        ("🏘️ Cell", f"{church_member.cell.name} ({church_member.cell.outstation.name})" if church_member.cell else "Not Assigned"),
        ("💼 Occupation", leader.occupation),
        ("📅 Start Date", leader.start_date.strftime('%d %B, %Y') if leader.start_date else "----"),
        ("⏳ Time in Service", leader.time_in_service if leader.time_in_service else "----"),
        ("📋 Responsibilities", leader.responsibilities or "----"),
    ]

    # Add outstation only for Evangelists
    if leader.occupation == 'Evangelist':
        leader_details.append(
            ("🏞️ Outstation", leader.outstation.name if leader.outstation else "Not Assigned")
        )

    leader_details.append(
        ("📅 Date Created", f"{localtime(leader.date_created).strftime('%d %B, %Y %I:%M %p')} ({since_created})")
    )
    leader_details.extend([
        ("💍 Marital Status", church_member.marital_status or "----"),
        ("📅 Date of Marriage", church_member.date_of_marriage.strftime('%d %B, %Y') if church_member.date_of_marriage else "----"),
        ("📛 Emergency Contact Name", church_member.emergency_contact_name or "----"),
        ("📞 Emergency Contact Phone", church_member.emergency_contact_phone or "----"),
    ])

    return render(request, "leaders/leader_detail.html", {
        "leader": leader,
        "leader_details": leader_details,
    })

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .utils import get_leaders_distribution_trend
from .models import Leader

# ✅ Helper Function: Allow Only Admins & Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required(login_url='login')
@user_passes_test(is_admin_or_superuser, login_url='login')
def leaders_home(request):
    """
    Leaders Home Page:
    - Displays total active/inactive leaders.
    - Fetches distribution data for the line chart (communities & zones).
    - Accessible only by Admins & Superusers.
    """
    # Get active & inactive leader counts
    total_active_leaders = Leader.objects.filter(church_member__status='Active').count()
    total_inactive_leaders = Leader.objects.filter(church_member__status='Inactive').count()

    # Fetch distribution data for communities & zones
    leaders_distribution_data = get_leaders_distribution_trend()

    return render(request, 'leaders/leaders_home.html', {
        'total_active_leaders': total_active_leaders,
        'total_inactive_leaders': total_inactive_leaders,
        'leaders_distribution_data': leaders_distribution_data,
    })
