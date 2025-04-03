from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import ChurchMember
from .forms import ChurchMemberForm
from leaders.forms import LeaderForm  # Import LeaderForm
from leaders.models import Leader  # Import Leader
from sms.utils import send_sms  # Assuming this exists

def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def create_or_update_church_member(request, member_id=None):
    """
    View for creating or updating a church member.
    - On creation: Sends SMS and redirects based on leadership status.
    - On update: Always redirects to church_member_list.
    """
    # Determine if this is an update or create operation
    if member_id:
        try:
            church_member = ChurchMember.objects.get(id=member_id)
            is_update = True
        except ChurchMember.DoesNotExist:
            messages.error(request, '❌ Church member not found.')
            return redirect('church_member_list')
    else:
        church_member = None
        is_update = False

    if request.method == 'POST':
        form = ChurchMemberForm(request.POST, request.FILES, instance=church_member)
        if form.is_valid():
            try:
                church_member = form.save()
                
                if not is_update:  # Creation logic
                    # Send SMS to the new member
                    sms_message = (
                        f"Habari {church_member.full_name}, karibu katika application yetu ya kkkt mkwawa, "
                        f"kama unatumia smartphone unaweza kupata akaunti yako mwenyewe kwa kutumia "
                        f"utambulisho wako ID (Usimpe yeyote!!) {church_member.member_id}, kwa kutumia link "
                        f"https://f692-197-250-100-119.ngrok-free.app/accounts/request-account/"
                    )
                    response = send_sms(to=church_member.phone_number, message=sms_message, member=church_member)
                    print(f"📩 SMS sent to {church_member.phone_number} (Request ID: {response.get('request_id', 'N/A')}): {response}")

                    messages.success(request, '✅ Church member saved successfully & SMS notification sent!')
                    
                    # Redirect based on is_this_church_member_a_leader for creation only
                    if church_member.is_this_church_member_a_leader:
                        return redirect('create_leader_from_member', member_id=church_member.id)
                else:  # Update logic
                    messages.success(request, '✅ Church member updated successfully!')

                # Always redirect to church_member_list (for updates, or if no leader on create)
                return redirect('church_member_list')

            except ValidationError as e:
                for msg in e.messages:
                    messages.error(request, f"❌ {msg}")
        else:
            messages.error(request, '❌ Failed to save church member. Please correct the errors below.')
    else:
        form = ChurchMemberForm(instance=church_member)

    return render(request, 'members/church_member_form.html', {'form': form, 'is_update': is_update})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from members.models import ChurchMember
from sms.utils import send_sms  # Assuming this exists for SMS functionality

# ✅ Access Control: Only Admins & Superusers Allowed
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# ✅ Approve Church Member View
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def approve_church_member(request, member_id):
    """
    Approves a pending church member, changes their status to 'Active', and sends an SMS notification.
    """
    member = get_object_or_404(ChurchMember, id=member_id, status='Pending')

    if request.method == 'POST':
        # Update status to Active
        member.status = 'Active'
        member.save()

        # Send SMS notification
        sms_message = (
            f"Congratulations, you have been approved to join our church KKKT-MKWAWA, "
            f"now you are an active member, you can proceed using our services if you have a "
            f"smartphone using the link below to request your account, use your id "
            f"{member.member_id} to request an account since you are already an active member\n"
            f"https://3140-196-249-105-88.ngrok-free.app/accounts/request-account/"
        )
        response = send_sms(to=member.phone_number, message=sms_message, member=member)
        print(f"📩 SMS sent to {member.phone_number} (Request ID: {response.get('request_id', 'N/A')}): {response}")

        messages.success(request, f"✅ {member.full_name} has been approved and notified via SMS!")
        return redirect('church_member_list')  # Redirect to the church member list

    return render(request, 'members/approve_church_member.html', {'member': member})


@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def create_leader_from_member(request, member_id):
    """
    View for creating leader details for a specific church member.
    Pre-populates the church_member field with the member's full name.
    """
    try:
        church_member = ChurchMember.objects.get(id=member_id)
    except ChurchMember.DoesNotExist:
        messages.error(request, '❌ Church member not found.')
        return redirect('church_member_list')

    # Check if a Leader record already exists for this member
    if Leader.objects.filter(church_member=church_member).exists():
        messages.error(request, '❌ This church member already has leader details.')
        return redirect('church_member_list')

    if request.method == 'POST':
        form = LeaderForm(request.POST)
        if form.is_valid():
            leader = form.save(commit=False)
            leader.church_member = church_member  # Set the church_member
            leader.save()
            messages.success(request, f'✅ Leader details for {church_member.full_name} saved successfully!')
            return redirect('church_member_list')
        else:
            messages.error(request, '❌ Failed to save leader details. Please correct the errors below.')
    else:
        # Pre-populate the form with the church_member
        form = LeaderForm(initial={'church_member': church_member})

    context = {
        'form': form,
        'church_member': church_member,
    }
    return render(request, 'members/leader_from_member_form.html', context)


from django.shortcuts import render
from django.utils.timezone import now, localtime
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
import pytz

from .models import ChurchMember
from settings.models import Cell, OutStation  # Updated imports

# ✅ Helper function to allow only Admins and Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

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

# ✅ View Restricted to Admins & Superusers
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def church_member_list(request):
    """
    View to display and filter the list of Active and Pending church members, 
    sorted with Pending at the top, then alphabetically by full name.
    Only accessible to Admins and Superusers.
    """
    # Get query parameters
    name_query = request.GET.get('name', '').strip()
    gender_query = request.GET.get('gender', '').strip()
    cell_query = request.GET.get('cell', '').strip()  # Changed from community
    outstation_query = request.GET.get('outstation', '').strip()  # Changed from zone

    # Retrieve Active and Pending members, sort Pending first, then by full_name
    church_members = ChurchMember.objects.select_related('cell__outstation').filter(
        status__in=['Active', 'Pending']
    ).order_by('-status', 'full_name')  # '-status' puts Pending before Active

    # Apply Filters
    if name_query:
        church_members = church_members.filter(
            Q(full_name__icontains=name_query) | Q(member_id__icontains=name_query)
        )

    if gender_query:
        church_members = church_members.filter(gender=gender_query)

    if cell_query:
        church_members = church_members.filter(cell_id=cell_query)  # Changed from community_id

    if outstation_query:
        church_members = church_members.filter(cell__outstation_id=outstation_query)  # Changed from community__zone_id

    # Calculate "Since Created" for each member
    for member in church_members:
        member.time_since_created = format_time_since(member.date_created)

    # Totals
    total_members = church_members.count()
    total_males = church_members.filter(gender='Male').count()
    total_females = church_members.filter(gender='Female').count()

    # Get distinct cells and outstations for dropdowns
    cells = Cell.objects.all()  # Changed from communities
    outstations = OutStation.objects.all()  # Changed from zones

    context = {
        'church_members': church_members,
        'total_members': total_members,
        'total_males': total_males,
        'total_females': total_females,
        'cells': cells,  # Changed from communities
        'outstations': outstations,  # Changed from zones
        'name_query': name_query,
        'gender_query': gender_query,
        'cell_query': cell_query,  # Changed from community_query
        'outstation_query': outstation_query,  # Changed from zone_query
    }

    return render(request, 'members/church_member_list.html', context)


@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def inactive_church_member_list(request):
    """
    View to display and filter the list of inactive church members, sorted alphabetically by full name.
    Only accessible to Admins and Superusers.
    """
    # Get query parameters
    name_query = request.GET.get('name', '').strip()
    gender_query = request.GET.get('gender', '').strip()
    cell_query = request.GET.get('cell', '').strip()  # Changed from community
    outstation_query = request.GET.get('outstation', '').strip()  # Changed from zone

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
        church_members = church_members.filter(cell_id=cell_query)  # Changed from community_id

    if outstation_query:
        church_members = church_members.filter(cell__outstation_id=outstation_query)  # Changed from community__zone_id

    # Calculate "Since Created" for each member
    for member in church_members:
        member.time_since_created = format_time_since(member.date_created)

    # Totals
    total_members = church_members.count()
    total_males = church_members.filter(gender='Male').count()
    total_females = church_members.filter(gender='Female').count()

    # Get distinct cells and outstations for dropdowns
    cells = Cell.objects.all()  # Changed from communities
    outstations = OutStation.objects.all()  # Changed from zones

    context = {
        'church_members': church_members,
        'total_members': total_members,
        'total_males': total_males,
        'total_females': total_females,
        'cells': cells,  # Changed from communities
        'outstations': outstations,  # Changed from zones
        'name_query': name_query,
        'gender_query': gender_query,
        'cell_query': cell_query,  # Changed from community_query
        'outstation_query': outstation_query,  # Changed from zone_query
    }

    return render(request, 'members/inactive_church_member_list.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from members.models import ChurchMember
from .utils import get_membership_distribution_analysis  # <-- Import the analysis function

# ✅ Helper Function: Restrict Access to Admins and Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required(login_url='login')
@user_passes_test(is_admin_or_superuser, login_url='login')
def members_home(request):
    """
    Members Home Page:
    - Displays total active and inactive members in summary boxes.
    - Fetches membership distribution data for the graphs (communities, zones, apostolic movements).
    - Only accessible to Admins and Superusers.
    """
    # Calculate total active & inactive members
    total_active_members = ChurchMember.objects.filter(status='Active').count()
    total_inactive_members = ChurchMember.objects.filter(status='Inactive').count()

    # Fetch membership distribution data
    membership_distribution_data = get_membership_distribution_analysis()

    # Render the members_home template, passing the summary counts and graph data
    return render(request, 'members/members_home.html', {
        'total_active_members': total_active_members,
        'total_inactive_members': total_inactive_members,
        'membership_distribution_data': membership_distribution_data
    })

# 🚫 Delete Church Member (Restricted to Admins/Superusers)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def delete_church_member(request, pk):
    """
    View to confirm and delete a specific ChurchMember.
    Only accessible to Admins and Superusers.
    """
    church_member = get_object_or_404(ChurchMember, pk=pk)

    if request.method == 'POST':
        church_member.delete()
        messages.success(request, f"✅ Church member '{church_member.full_name}' deleted successfully!")
        return redirect('church_member_list')

    return render(request, 'members/confirm_delete_church_member.html', {
        'church_member': church_member,
    })


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import ChurchMember
from .forms import UpdateChurchMemberForm

def validate_member_data(church_member):
    """
    Validates the logical consistency of church member data.
    - First Communion requires Baptism.
    - Confirmation requires First Communion and Baptism.
    - Marriage requires Confirmation, First Communion, and Baptism.
    - Marital Status cannot be 'Married' if the member is not actually married.
    """
    errors = []

    # ❌ A member cannot receive First Communion without being baptized
    if church_member.has_received_first_communion and not church_member.is_baptised:
        errors.append("A member cannot receive First Communion without being baptized.")

    # ❌ A member cannot be confirmed without First Communion & Baptism
    if church_member.is_confirmed and (not church_member.has_received_first_communion or not church_member.is_baptised):
        errors.append("A member cannot be confirmed without First Communion and Baptism.")

    # ❌ A member cannot be married without Confirmation, First Communion, and Baptism
    if church_member.is_married and (not church_member.is_confirmed or not church_member.has_received_first_communion or not church_member.is_baptised):
        errors.append("A member cannot be married without being confirmed, receiving First Communion, and being baptized.")

    # ❌ Marital Status cannot be "Married" unless the member is actually married
    if church_member.marital_status == "Married" and not church_member.is_married:
        errors.append("Marital Status cannot be 'Married' if the member is not marked as married.")

    if errors:
        raise ValidationError(errors)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import ChurchMember
from .forms import UpdateChurchMemberForm, ChurchMemberPassportForm

# ✅ Helper function to allow only Admins and Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# 🚀 Update Church Member (Restricted to Admins/Superusers)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def update_church_member(request, pk):
    """
    View for updating an existing church member, including document uploads.
    Only accessible to Admins and Superusers.
    """
    church_member = get_object_or_404(ChurchMember, pk=pk)

    if request.method == 'POST':
        form = UpdateChurchMemberForm(request.POST, request.FILES, instance=church_member)

        if form.is_valid():
            try:
                # Save the form; model's clean() will handle validation
                church_member = form.save()

                messages.success(request, '✅ Church member updated successfully!')
                return redirect('church_member_detail', pk=church_member.pk)  # Redirect to details page

            except ValidationError as e:
                # Display validation errors from the model
                for msg in e.messages:
                    messages.error(request, msg)

        else:
            messages.error(request, '❌ Failed to update the church member. Please correct the errors below.')

    else:
        form = UpdateChurchMemberForm(instance=church_member)

    return render(request, 'members/update_church_member.html', {
        'form': form,
        'church_member': church_member,
    })

# 🚀 Upload Passport (Restricted to Admins/Superusers)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def upload_passport(request, pk):
    """
    View for uploading or updating a church member's passport.
    Only accessible to Admins and Superusers.
    """
    member = get_object_or_404(ChurchMember, pk=pk)

    if request.method == 'POST':
        form = ChurchMemberPassportForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Passport uploaded successfully!')
            return redirect('church_member_list')  # Redirect to the list of members
        else:
            messages.error(request, '❌ Failed to upload passport. Please try again.')
    else:
        form = ChurchMemberPassportForm(instance=member)

    return render(request, 'members/upload_passport.html', {'form': form, 'member': member})

from django.shortcuts import render, get_object_or_404
from django.utils.timezone import localtime, now
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import ChurchMember
from settings.models import Cell, OutStation  # Updated imports
from datetime import date

def is_admin_or_superuser(user):
    """
    Check if the user is a superuser or has the 'ADMIN' user_type.
    """
    return user.is_superuser or user.user_type == 'ADMIN'

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
    return "----"  # Placeholder for missing DOB

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

@login_required(login_url='/accounts/login/')
@user_passes_test(is_admin_or_superuser, login_url='/accounts/login/')
def church_member_detail(request, pk):
    """
    View to retrieve and display all details of a specific ChurchMember with uploaded documents.
    Only accessible to Admins and Superusers.
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
    }

    # Prepare details
    details = {
        "👤 Full Name": church_member.full_name,
        "🆔 Member ID": church_member.member_id,
        "🎂 Date of Birth": church_member.date_of_birth.strftime('%d %B, %Y') if church_member.date_of_birth else "----",
        "🔢 Age": calculate_age(church_member.date_of_birth),
        "⚥ Gender": church_member.gender,
        "📞 Phone Number": church_member.phone_number,
        "📧 Email": church_member.email or "----",
        "🏠 Address": church_member.address or "----",
        "🏘️ Cell": f"{church_member.cell.name} ({church_member.cell.outstation.name})"
                   if church_member.cell else "----",
        "🔘 Status": {
            "Active": "✅ Active",
            "Pending": "⏳ Pending",
            "Inactive": "❌ Inactive"
        }.get(church_member.status, "❓ Unknown"),  # Use raw status value
        "📅 Date Created": f"{localtime(church_member.date_created).strftime('%d %B, %Y %I:%M %p')} ({since_created})",

        # Sacramental Information
        "🌊 Baptized": format_boolean(church_member.is_baptised),
        "🗓️ Date of Baptism": church_member.date_of_baptism.strftime('%d %B, %Y') if church_member.date_of_baptism else "----",
        "🕊️ Confirmed": format_boolean(church_member.is_confirmed),  # Fixed to use is_confirmed
        "🗓️ Date of Confirmation": church_member.date_confirmed.strftime('%d %B, %Y') if church_member.date_confirmed else "----",

        # Marriage Information
        "💍 Marital Status": church_member.marital_status or "----",
        "🗓️ Date of Marriage": church_member.date_of_marriage.strftime('%d %B, %Y') if church_member.date_of_marriage else "----",

        # Emergency Contact Information
        "📛 Emergency Contact Name": church_member.emergency_contact_name or "----",
        "📞 Emergency Contact Phone": church_member.emergency_contact_phone or "----",

        # Other Details
        "📸 Passport": church_member.passport.url if church_member.passport else "----",
    }

    return render(request, 'members/church_member_detail.html', {
        'church_member': church_member,
        'details': details,
        'documents': documents
    })

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from settings.models import Cell, OutStation  # Updated imports
from members.models import ChurchMember

def is_admin_or_superuser(user):
    """
    Check if the user is a superuser or has the 'ADMIN' user_type.
    """
    return user.is_superuser or user.user_type == 'ADMIN'

@login_required
@user_passes_test(is_admin_or_superuser, login_url='/accounts/login/')
def church_members_report(request):
    """
    Displays a comprehensive Church Members report with various statistics:
      - total members (active & inactive),
      - gender breakdown for active/inactive,
      - outstation & cell counts,
      - per-cell breakdown (active/inactive, gender),
      - the cell with the largest number of members,
      - the cell with the smallest number of members,
      - sacramental details (baptized/unbaptized, confirmed/unconfirmed),
      - marriage details by gender and marital status,
      - the same stats at a cell level for active members,
      - plus a concluding comments/advice section.

    Accessible to Admins and Superusers only.
    """

    # ============ 1) Basic Totals ============
    total_members = ChurchMember.objects.count()
    total_active = ChurchMember.objects.filter(status='Active').count()
    total_inactive = ChurchMember.objects.filter(status='Inactive').count()

    # Gender breakdown (active)
    active_male = ChurchMember.objects.filter(status='Active', gender='Male').count()
    active_female = ChurchMember.objects.filter(status='Active', gender='Female').count()

    # Gender breakdown (inactive)
    inactive_male = ChurchMember.objects.filter(status='Inactive', gender='Male').count()
    inactive_female = ChurchMember.objects.filter(status='Inactive', gender='Female').count()

    # ============ 2) OutStation & Cell Stats ============
    total_outstations = OutStation.objects.count()  # Changed from total_zones
    total_cells = Cell.objects.count()  # Changed from total_communities

    cells = Cell.objects.select_related('outstation').all()  # Changed from communities
    cell_stats_list = []  # Changed from community_stats_list

    for cell in cells:
        all_cell_members = cell.members.all()  # Changed from comm.members
        total_cell_members = all_cell_members.count()  # Changed from total_comm_members

        # Active/inactive
        active_cell = all_cell_members.filter(status='Active').count()  # Changed from active_comm
        inactive_cell = all_cell_members.filter(status='Inactive').count()  # Changed from inactive_comm

        # Active male/female
        active_male_cell = all_cell_members.filter(status='Active', gender='Male').count()  # Changed from active_male_comm
        active_female_cell = all_cell_members.filter(status='Active', gender='Female').count()  # Changed from active_female_comm

        # Inactive male/female
        inactive_male_cell = all_cell_members.filter(status='Inactive', gender='Male').count()  # Changed from inactive_male_comm
        inactive_female_cell = all_cell_members.filter(status='Inactive', gender='Female').count()  # Changed from inactive_female_comm

        # Sacramental stats (only for active members)
        active_baptized_cell = all_cell_members.filter(status='Active', is_baptised=True).count()  # Changed from active_baptized_comm
        active_unbaptized_cell = all_cell_members.filter(status='Active', is_baptised=False).count()  # Changed from active_unbaptized_comm
        active_confirmed_cell = all_cell_members.filter(status='Active', date_confirmed__isnull=False).count()  # Changed from active_confirmed_comm, adjusted for no is_confirmed
        active_unconfirmed_cell = all_cell_members.filter(status='Active', date_confirmed__isnull=True).count()  # Changed from active_unconfirmed_comm

        # Marital status for active male/female
        married_males_cell = all_cell_members.filter(status='Active', gender='Male', marital_status='Married').count()  # Changed from married_males_comm, adjusted for no is_married
        unmarried_males_cell = all_cell_members.filter(status='Active', gender='Male', marital_status__in=['Single', 'Divorced', 'Widowed']).count()  # Changed from unmarried_males_comm
        married_females_cell = all_cell_members.filter(status='Active', gender='Female', marital_status='Married').count()  # Changed from married_females_comm
        unmarried_females_cell = all_cell_members.filter(status='Active', gender='Female', marital_status__in=['Single', 'Divorced', 'Widowed']).count()  # Changed from unmarried_females_comm

        cell_stats_list.append({
            'cell': cell,  # Changed from community
            'cell_display': f"{cell.name} ({cell.outstation.name})",  # Changed from community_display
            'total_members': total_cell_members,
            'active_members': active_cell,
            'inactive_members': inactive_cell,
            'active_male': active_male_cell,
            'active_female': active_female_cell,
            'inactive_male': inactive_male_cell,
            'inactive_female': inactive_female_cell,

            'active_baptized': active_baptized_cell,
            'active_unbaptized': active_unbaptized_cell,
            'active_confirmed': active_confirmed_cell,
            'active_unconfirmed': active_unconfirmed_cell,

            'married_males': married_males_cell,
            'unmarried_males': unmarried_males_cell,
            'married_females': married_females_cell,
            'unmarried_females': unmarried_females_cell,
        })

    # Largest & smallest cell by total members
    if cell_stats_list:
        largest_cell = max(cell_stats_list, key=lambda c: c['total_members'])  # Changed from largest_community
        smallest_cell = min(cell_stats_list, key=lambda c: c['total_members'])  # Changed from smallest_community
    else:
        largest_cell = None
        smallest_cell = None

    # ============ 3) Overall Sacramental & Marital Stats (Active) ============
    active_baptized = ChurchMember.objects.filter(status='Active', is_baptised=True).count()
    active_unbaptized = ChurchMember.objects.filter(status='Active', is_baptised=False).count()
    active_confirmed = ChurchMember.objects.filter(status='Active', date_confirmed__isnull=False).count()  # Adjusted for no is_confirmed
    active_unconfirmed = ChurchMember.objects.filter(status='Active', date_confirmed__isnull=True).count()

    married_males = ChurchMember.objects.filter(status='Active', gender='Male', marital_status='Married').count()  # Adjusted for no is_married
    unmarried_males = ChurchMember.objects.filter(status='Active', gender='Male', marital_status__in=['Single', 'Divorced', 'Widowed']).count()
    married_females = ChurchMember.objects.filter(status='Active', gender='Female', marital_status='Married').count()
    unmarried_females = ChurchMember.objects.filter(status='Active', gender='Female', marital_status__in=['Single', 'Divorced', 'Widowed']).count()

    # ============ 4) Comments/Explanations/Advice ============
    comments_explanations_advice = (
        "These statistics provide insights into membership trends, gender distribution, and sacramental participation "
        "across outstations and cells. Cells with lower membership may indicate areas needing outreach or support. "
        "Sacramental and marital data can guide pastoral planning and highlight opportunities for spiritual growth."
    )

    context = {
        # Basic stats
        'total_members': total_members,
        'total_active': total_active,
        'total_inactive': total_inactive,
        'active_male': active_male,
        'active_female': active_female,
        'inactive_male': inactive_male,
        'inactive_female': inactive_female,

        # Outstation & cell stats
        'total_outstations': total_outstations,  # Changed from total_zones
        'total_cells': total_cells,  # Changed from total_communities
        'cell_stats_list': cell_stats_list,  # Changed from community_stats_list
        'largest_cell': largest_cell,  # Changed from largest_community
        'smallest_cell': smallest_cell,  # Changed from smallest_community

        # Overall sacramental & marital (active only)
        'active_baptized': active_baptized,
        'active_unbaptized': active_unbaptized,
        'active_confirmed': active_confirmed,
        'active_unconfirmed': active_unconfirmed,
        'married_males': married_males,
        'unmarried_males': unmarried_males,
        'married_females': married_females,
        'unmarried_females': unmarried_females,

        # Comments/Advice
        'comments_explanations_advice': comments_explanations_advice,
    }

    return render(request, "members/church_members_report.html", context)


from django.shortcuts import render, redirect
from .forms import ChurchMemberSignupForm
from django.contrib import messages

def church_member_signup(request):
    if request.method == 'POST':
        form = ChurchMemberSignupForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your signup request has been submitted successfully! It is pending approval.')
            return redirect('signup_success')  # Redirect to same page or another success page
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ChurchMemberSignupForm()
    
    return render(request, 'members/signup.html', {'form': form})


def signup_success(request):
    return render(request, 'members/signup_success.html')