# views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

@login_required
def pastor_details(request):
    """
    View to retrieve all details of a 'Senior Pastor' with:
      - user.user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a leader
      - leader.occupation == 'Senior Pastor'
    """
    user = request.user

    # 1) Must be a CHURCH_MEMBER
    if user.user_type != 'CHURCH_MEMBER':
        raise PermissionDenied("Access denied: user type must be CHURCH_MEMBER.")

    # 2) Must have an active ChurchMember record
    church_member = getattr(user, 'church_member', None)
    if not church_member or church_member.status != 'Active':
        raise PermissionDenied("Access denied: Church Member status must be 'Active'.")

    # 3) Must be a Leader
    leader = getattr(church_member, 'leader', None)
    if not leader:
        raise PermissionDenied("Access denied: this Church Member is not a Leader.")

    # 4) Must have occupation == 'Senior Pastor'
    if leader.occupation != 'Senior Pastor':
        raise PermissionDenied("Access denied: Leader occupation must be 'Senior Pastor'.")

    # ✅ If we reach here, user meets all the criteria

    # Helper function for boolean fields
    def format_boolean(value):
        return '<span style="color: green; font-size: 18px;">✔️</span>' if value else '<span style="color: red; font-size: 18px;">❌</span>'

    # Account Details
    account_details = {
        "Username": user.username,
        "Email": user.email or "Not provided",
        "Phone Number": user.phone_number,
        "Date Created": user.date_created.strftime("%d %B %Y"),
    }

    # Membership Details
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

    # Leadership Details
    leadership_details = {
        "Occupation": leader.occupation,
        "Start Date": leader.start_date.strftime("%d %B %Y"),
        "Committee": leader.committee,
        "Responsibilities": leader.responsibilities,
        "Education Level": leader.education_level,
        "Religious Education": leader.religious_education or "Not Provided",
        "Voluntary Service": format_boolean(leader.voluntary),
    }

    # Certificates
    certificates = {
        "Baptism Certificate": church_member.baptism_certificate.url if church_member.baptism_certificate else None,
        "First Communion Certificate": church_member.communion_certificate.url if church_member.communion_certificate else None,
        "Confirmation Certificate": church_member.confirmation_certificate.url if church_member.confirmation_certificate else None,
        "Marriage Certificate": church_member.marriage_certificate.url if church_member.marriage_certificate else None,
    }

    # Passport
    passport_url = church_member.passport.url if church_member.passport else None

    return render(request, "pastor/pastor_details.html", {
        "passport_url": passport_url,
        "account_details": account_details,
        "membership_details": membership_details,
        "leadership_details": leadership_details,
        "certificates": certificates,
    })


from django.shortcuts import render
from django.utils.timezone import now, localtime
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
import pytz

from members.models import ChurchMember
from settings.models import Cell, OutStation  # Updated imports: Community → Cell, Zone → OutStation

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


@login_required
def pastor_church_member_list(request):
    """
    View to display and filter the list of church members, sorted alphabetically by full name.
    Accessible only to a logged-in user who is:
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - leader.occupation == 'Senior Pastor'
    """
    user = request.user
    
    # 1) Must be a CHURCH_MEMBER
    if user.user_type != 'CHURCH_MEMBER':
        raise PermissionDenied("Access denied: user type must be CHURCH_MEMBER.")
    
    # 2) Must have an Active ChurchMember
    church_member = getattr(user, 'church_member', None)
    if not church_member or church_member.status != 'Active':
        raise PermissionDenied("Access denied: ChurchMember must be active.")
    
    # 3) Must be a Leader
    leader = getattr(church_member, 'leader', None)
    if not leader:
        raise PermissionDenied("Access denied: ChurchMember is not a Leader.")
    
    # 4) Must be 'Senior Pastor'
    if leader.occupation != 'Senior Pastor':
        raise PermissionDenied("Access denied: Only Senior Pastors can access this view.")
    
    # ✅ If all checks pass, proceed with existing logic
    name_query = request.GET.get('name', '').strip()
    gender_query = request.GET.get('gender', '').strip()
    cell_query = request.GET.get('cell', '').strip()  # Updated from community to cell
    outstation_query = request.GET.get('outstation', '').strip()  # Updated from zone to outstation

    # Retrieve only Active members and order by full_name alphabetically
    church_members = (
        ChurchMember.objects
        .select_related('cell__outstation')  # Updated relationship: community__zone → cell__outstation
        .filter(status="Active")
        .order_by('full_name')
    )

    # Apply Filters
    if name_query:
        church_members = church_members.filter(
            Q(full_name__icontains=name_query) | Q(member_id__icontains=name_query)
        )
    if gender_query:
        church_members = church_members.filter(gender=gender_query)
    if cell_query:
        church_members = church_members.filter(cell_id=cell_query)  # Updated from community_id to cell_id
    if outstation_query:
        church_members = church_members.filter(cell__outstation_id=outstation_query)  # Updated from community__zone_id to cell__outstation_id

    # Calculate "Since Created" for each member
    for member in church_members:
        member.time_since_created = format_time_since(member.date_created)

    # Totals
    total_members = church_members.count()
    total_males = church_members.filter(gender='Male').count()
    total_females = church_members.filter(gender='Female').count()

    # Get distinct cells and outstations for dropdown filters
    cells = Cell.objects.all()  # Updated from Community to Cell
    outstations = OutStation.objects.all()  # Updated from Zone to OutStation

    context = {
        'church_members': church_members,
        'total_members': total_members,
        'total_males': total_males,
        'total_females': total_females,
        'cells': cells,  # Updated from communities to cells
        'outstations': outstations,  # Updated from zones to outstations
        'name_query': name_query,
        'gender_query': gender_query,
        'cell_query': cell_query,  # Updated from community_query to cell_query
        'outstation_query': outstation_query,  # Updated from zone_query to outstation_query
    }

    return render(request, 'pastor/members/church_member_list.html', context)


from django.shortcuts import render
from django.utils.timezone import now, localtime
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
import pytz

from members.models import ChurchMember
from settings.models import Cell, OutStation  # Updated imports: Community → Cell, Zone → OutStation

# 🌍 Set Tanzania timezone
TZ_TZ = pytz.timezone('Africa/Dar_es_Salaam')

def format_time_since(created_date):
    """
    Returns a user-friendly time format based on Tanzania timezone.
    """
    if not created_date:
        return "N/A"

    created_date = localtime(created_date, timezone=TZ_TZ)
    current_time = localtime(now(), timezone=TZ_TZ)

    time_diff = current_time - created_date
    seconds = time_diff.total_seconds()

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


@login_required
def pastor_inactive_church_member_list(request):
    """
    View to display and filter the list of 'Inactive' church members.
    Accessible only to a user who is:
      - Logged in
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a leader
      - leader.occupation == 'Senior Pastor'
    """
    user = request.user

    # 1) Must be a CHURCH_MEMBER
    if user.user_type != 'CHURCH_MEMBER':
        raise PermissionDenied("Access denied: user type must be CHURCH_MEMBER.")

    # 2) Must have an Active ChurchMember
    church_member = getattr(user, 'church_member', None)
    if not church_member or church_member.status != 'Active':
        raise PermissionDenied("Access denied: ChurchMember must be active.")

    # 3) Must be a Leader
    leader = getattr(church_member, 'leader', None)
    if not leader:
        raise PermissionDenied("Access denied: ChurchMember is not a Leader.")

    # 4) Must have occupation == 'Senior Pastor'
    if leader.occupation != 'Senior Pastor':
        raise PermissionDenied("Access denied: Only Senior Pastors can access this view.")

    # ✅ If checks pass, proceed with listing Inactive members
    name_query = request.GET.get('name', '').strip()
    gender_query = request.GET.get('gender', '').strip()
    cell_query = request.GET.get('cell', '').strip()  # Updated from community to cell
    outstation_query = request.GET.get('outstation', '').strip()  # Updated from zone to outstation

    # Retrieve only Inactive members, sorted alphabetically
    church_members = (
        ChurchMember.objects
        .select_related('cell__outstation')  # Updated relationship: community__zone → cell__outstation
        .filter(status="Inactive")
        .order_by('full_name')
    )

    # Apply Filters
    if name_query:
        church_members = church_members.filter(
            Q(full_name__icontains=name_query) | Q(member_id__icontains=name_query)
        )
    if gender_query:
        church_members = church_members.filter(gender=gender_query)
    if cell_query:
        church_members = church_members.filter(cell_id=cell_query)  # Updated from community_id to cell_id
    if outstation_query:
        church_members = church_members.filter(cell__outstation_id=outstation_query)  # Updated from community__zone_id to cell__outstation_id

    # Calculate "Since Created" for each member
    for member in church_members:
        member.time_since_created = format_time_since(member.date_created)

    # Totals
    total_members = church_members.count()
    total_males = church_members.filter(gender='Male').count()
    total_females = church_members.filter(gender='Female').count()

    # Distinct cells and outstations
    cells = Cell.objects.all()  # Updated from Community to Cell
    outstations = OutStation.objects.all()  # Updated from Zone to OutStation

    context = {
        'church_members': church_members,
        'total_members': total_members,
        'total_males': total_males,
        'total_females': total_females,
        'cells': cells,  # Updated from communities to cells
        'outstations': outstations,  # Updated from zones to outstations
        'name_query': name_query,
        'gender_query': gender_query,
        'cell_query': cell_query,  # Updated from community_query to cell_query
        'outstation_query': outstation_query,  # Updated from zone_query to outstation_query
    }

    return render(request, 'pastor/members/church_member_list.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages

from members.models import ChurchMember
from members.utils import get_membership_distribution_analysis  # <-- Import the analysis function

@login_required
def pastor_members_home(request):
    """
    Members Home Page:
    - Displays total active and inactive members in summary boxes.
    - Fetches membership distribution data for the graphs (communities, zones, apostolic movements).
    - Only accessible to a user who is:
      - logged in
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - is a leader
      - leader.occupation == 'Senior Pastor'
    """

    user = request.user

    # 1) Must be a CHURCH_MEMBER
    if user.user_type != 'CHURCH_MEMBER':
        raise PermissionDenied("Access denied: user type must be CHURCH_MEMBER.")

    # 2) Must have an Active ChurchMember
    church_member = getattr(user, 'church_member', None)
    if not church_member or church_member.status != 'Active':
        raise PermissionDenied("Access denied: ChurchMember must be active.")

    # 3) Must be a Leader
    leader = getattr(church_member, 'leader', None)
    if not leader:
        raise PermissionDenied("Access denied: ChurchMember is not a Leader.")

    # 4) Must have occupation == 'Senior Pastor'
    if leader.occupation != 'Senior Pastor':
        raise PermissionDenied("Access denied: Only Senior Pastors can access this page.")

    # ✅ If checks pass, proceed with original logic
    total_active_members = ChurchMember.objects.filter(status='Active').count()
    total_inactive_members = ChurchMember.objects.filter(status='Inactive').count()

    # Fetch membership distribution data
    membership_distribution_data = get_membership_distribution_analysis()

    return render(
        request,
        'pastor/members/members_home.html',
        {
            'total_active_members': total_active_members,
            'total_inactive_members': total_inactive_members,
            'membership_distribution_data': membership_distribution_data
        }
    )

from django.shortcuts import render, get_object_or_404
from django.utils.timezone import localtime, now
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from datetime import date

from members.models import ChurchMember

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

@login_required
def pastor_church_member_detail(request, pk):
    """
    View to retrieve and display details of a specific ChurchMember.
    Accessible only to a user who:
      - is logged in,
      - user_type == 'CHURCH_MEMBER',
      - church_member.status == 'Active',
      - church_member is a leader,
      - leader.occupation == 'Senior Pastor'.
    """
    # 1) Must be CHURCH_MEMBER
    user = request.user
    if user.user_type != 'CHURCH_MEMBER':
        raise PermissionDenied("Access denied: user type must be CHURCH_MEMBER.")

    # 2) Must have an Active ChurchMember
    church_member_user = getattr(user, 'church_member', None)
    if not church_member_user or church_member_user.status != 'Active':
        raise PermissionDenied("Access denied: ChurchMember must be active.")

    # 3) Must be a Leader
    leader = getattr(church_member_user, 'leader', None)
    if not leader:
        raise PermissionDenied("Access denied: ChurchMember is not a Leader.")

    # 4) Must have occupation == 'Senior Pastor'
    if leader.occupation != 'Senior Pastor':
        raise PermissionDenied("Access denied: Only Senior Pastors can access this page.")

    # ✅ If checks pass, proceed to display detail of the specified member
    church_member = get_object_or_404(ChurchMember, pk=pk)

    since_created = calculate_since_created(church_member.date_created)

    def format_boolean(value):
        return "✅" if value else "❌"

    documents = {
        "📜 Baptism Certificate": church_member.baptism_certificate.url if church_member.baptism_certificate else None,
        "🕊️ Confirmation Certificate": church_member.confirmation_certificate.url if church_member.confirmation_certificate else None,
        "💍 Marriage Certificate": church_member.marriage_certificate.url if church_member.marriage_certificate else None,
    }

    details = {
        "👤 Full Name": church_member.full_name,
        "🆔 Member ID": church_member.member_id,
        "🎂 Date of Birth": church_member.date_of_birth.strftime('%d %B, %Y') if church_member.date_of_birth else "----",
        "🔢 Age": calculate_age(church_member.date_of_birth),
        "⚥ Gender": church_member.gender,
        "📞 Phone Number": church_member.phone_number,
        "📧 Email": church_member.email or "----",
        "🏠 Address": church_member.address or "----",
        "🏘️ Community": (
            f"{church_member.community.name} ({church_member.community.zone.name})"
            if church_member.community else "----"
        ),
        "🔘 Status": f"✅ Active" if church_member.status == "Active" else "❌ Inactive",
        "📅 Date Created": f"{localtime(church_member.date_created).strftime('%d %B, %Y %I:%M %p')} ({since_created})",

        # Sacramental
        "🌊 Baptized": format_boolean(church_member.is_baptised),
        "🗓️ Date of Baptism": church_member.date_of_baptism.strftime('%d %B, %Y') if church_member.date_of_baptism else "----",
        "🕊️ Confirmed": format_boolean(church_member.is_confirmed),
        "🗓️ Date of Confirmation": church_member.date_confirmed.strftime('%d %B, %Y') if church_member.date_confirmed else "----",

        # Marriage
        "💍 Marital Status": church_member.marital_status or "----",
        "❤️ Spouse Name": church_member.spouse_name or "----",
        "👶 Number of Children": church_member.number_of_children or "----",
        "🗓️ Date of Marriage": church_member.date_of_marriage.strftime('%d %B, %Y') if church_member.date_of_marriage else "----",

        # Additional
        "💼 Job": church_member.job or "----",
        "🎨 Talent": church_member.talent or "----",
        "🙏 Services": church_member.services or "----",
        "📛 Emergency Contact Name": church_member.emergency_contact_name or "----",
        "📞 Emergency Contact Phone": church_member.emergency_contact_phone or "----",
        "♿ Disability": church_member.disability or "----",
        "🌟 Special Interests": church_member.special_interests or "----",

        # Apostolic Movement
        "🕊️ Apostolic Movement": church_member.apostolic_movement.name if church_member.apostolic_movement else "----",
        "👑 Is Leader of Movement?": format_boolean(church_member.is_the_member_a_leader_of_the_movement),
    }

    return render(request, 'pastor/members/church_member_detail.html', {
        'church_member': church_member,
        'details': details,
        'documents': documents,
    })


from django.shortcuts import render
from datetime import date
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from members.models import ChurchMember
from leaders.models import Leader
from settings.models import Cell, OutStation  # Updated imports: Community → Cell, Zone → OutStation

def calculate_time_in_service(start_date):
    """
    Function to calculate the time in service (years, months, days).
    """
    if not start_date:
        return ""
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


@login_required
def pastor_leader_list_view(request):
    """
    View to display a list of leaders with search and filtering options.
    Accessible only to:
      - Logged in user
      - user_type == 'CHURCH_MEMBER'
      - The user's ChurchMember is 'Active'
      - The user is actually a Leader
      - The Leader has occupation == 'Senior Pastor'
    Leaders are sorted alphabetically by their full_name.
    """

    # 1) Must be CHURCH_MEMBER
    user = request.user
    if user.user_type != 'CHURCH_MEMBER':
        raise PermissionDenied("Access denied: user type must be CHURCH_MEMBER.")

    # 2) Must have an active ChurchMember record
    church_member_user = getattr(user, 'church_member', None)
    if not church_member_user or church_member_user.status != 'Active':
        raise PermissionDenied("Access denied: ChurchMember must be active.")

    # 3) Must be a Leader
    leader_user = getattr(church_member_user, 'leader', None)
    if not leader_user:
        raise PermissionDenied("Access denied: ChurchMember is not a Leader.")

    # 4) Must have occupation == 'Senior Pastor'
    if leader_user.occupation != 'Senior Pastor':
        raise PermissionDenied("Access denied: Only Senior Pastors can access this view.")

    # ✅ If checks pass, proceed with the original logic:
    search_name = request.GET.get('search_name', '').strip()
    search_gender = request.GET.get('search_gender', '')
    search_occupation = request.GET.get('search_occupation', '')
    search_cell = request.GET.get('search_cell', '')  # Updated from search_community to search_cell
    search_outstation = request.GET.get('search_outstation', '')  # Updated from search_zone to search_outstation

    leaders = Leader.objects.filter(church_member__status="Active").order_by('church_member__full_name')

    # Update time in service for each leader
    for leader in leaders:
        if leader.start_date:
            leader.time_in_service = calculate_time_in_service(leader.start_date)
            leader.save(update_fields=['time_in_service'])

    # Apply Filters
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
        leaders = leaders.filter(church_member__cell_id=search_cell)  # Updated from community_id to cell_id
    if search_outstation:
        leaders = leaders.filter(church_member__cell__outstation_id=search_outstation)  # Updated from community__zone_id to cell__outstation_id

    # Calculate Totals
    total_leaders = leaders.count()
    total_male = leaders.filter(church_member__gender="Male").count()
    total_female = leaders.filter(church_member__gender="Female").count()

    # Distinct cells and outstations
    all_cells = Cell.objects.all()  # Updated from all_communities to all_cells
    all_outstations = OutStation.objects.all()  # Updated from all_zones to all_outstations

    # Occupations from Leader model
    all_occupations = [choice[0] for choice in Leader.OCCUPATION_CHOICES]

    return render(request, 'pastor/leaders/leader_list.html', {
        'leaders': leaders,
        'total_leaders': total_leaders,
        'total_male': total_male,
        'total_female': total_female,
        'all_cells': all_cells,  # Updated from all_communities to all_cells
        'all_outstations': all_outstations,  # Updated from all_zones to all_outstations
        'all_occupations': all_occupations,
        'search_name': search_name,
        'search_gender': search_gender,
        'search_occupation': search_occupation,
        'search_cell': search_cell,  # Updated from search_community to search_cell
        'search_outstation': search_outstation,  # Updated from search_zone to search_outstation
    })


from django.shortcuts import render
from datetime import date
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from leaders.models import Leader
from members.models import ChurchMember
from settings.models import Cell, OutStation  # Updated imports: Community → Cell, Zone → OutStation

def calculate_time_in_service(start_date):
    """
    Function to calculate the time in service (years, months, days).
    """
    if not start_date:
        return ""
    today = date.today()
    years = today.year - start_date.year
    months = today.month - start_date.month
    days = today.day - start_date.day

    if days < 0:
        months -= 1
        days += 30  # approximate
    if months < 0:
        years -= 1
        months += 12

    return f"{years} years, {months} months, {days} days"


@login_required
def pastor_inactive_leader_list_view(request):
    """
    View to display a list of inactive leaders with search and filtering options.
    Accessible only to:
      - logged-in user
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - is a leader
      - leader.occupation == 'Senior Pastor'
    Leaders are sorted alphabetically by church_member.full_name.
    """
    user = request.user

    # 1) Must be CHURCH_MEMBER
    if user.user_type != 'CHURCH_MEMBER':
        raise PermissionDenied("Access denied: user type must be CHURCH_MEMBER.")

    # 2) Must have an Active ChurchMember
    church_member_user = getattr(user, 'church_member', None)
    if not church_member_user or church_member_user.status != 'Active':
        raise PermissionDenied("Access denied: ChurchMember must be active.")

    # 3) Must be a Leader
    leader_user = getattr(church_member_user, 'leader', None)
    if not leader_user:
        raise PermissionDenied("Access denied: ChurchMember is not a Leader.")

    # 4) Must have occupation == 'Senior Pastor'
    if leader_user.occupation != 'Senior Pastor':
        raise PermissionDenied("Access denied: Only Senior Pastors can access this view.")

    # ✅ If checks pass, proceed with the original logic
    search_name = request.GET.get('search_name', '').strip()
    search_gender = request.GET.get('search_gender', '')
    search_occupation = request.GET.get('search_occupation', '')
    search_cell = request.GET.get('search_cell', '')  # Updated from search_community to search_cell
    search_outstation = request.GET.get('search_outstation', '')  # Updated from search_zone to search_outstation

    # Retrieve Inactive Leaders, sorted by name
    leaders = Leader.objects.filter(church_member__status="Inactive").order_by('church_member__full_name')

    # Update time_in_service for each leader
    for leader in leaders:
        if leader.start_date:
            leader.time_in_service = calculate_time_in_service(leader.start_date)
            leader.save(update_fields=['time_in_service'])

    # Apply filtering
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
        leaders = leaders.filter(church_member__cell_id=search_cell)  # Updated from community_id to cell_id
    if search_outstation:
        leaders = leaders.filter(church_member__cell__outstation_id=search_outstation)  # Updated from community__zone_id to cell__outstation_id

    # Totals
    total_leaders = leaders.count()
    total_male = leaders.filter(church_member__gender="Male").count()
    total_female = leaders.filter(church_member__gender="Female").count()

    # Distinct cells & outstations for dropdowns
    all_cells = Cell.objects.all()  # Updated from all_communities to all_cells
    all_outstations = OutStation.objects.all()  # Updated from all_zones to all_outstations

    # Occupations from Leader model
    all_occupations = [choice[0] for choice in Leader.OCCUPATION_CHOICES]

    return render(request, 'pastor/leaders/inactive_leader_list.html', {
        'leaders': leaders,
        'total_leaders': total_leaders,
        'total_male': total_male,
        'total_female': total_female,
        'all_cells': all_cells,  # Updated from all_communities to all_cells
        'all_outstations': all_outstations,  # Updated from all_zones to all_outstations
        'all_occupations': all_occupations,
        'search_name': search_name,
        'search_gender': search_gender,
        'search_occupation': search_occupation,
        'search_cell': search_cell,  # Updated from search_community to search_cell
        'search_outstation': search_outstation,  # Updated from search_zone to search_outstation
    })


from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now, localtime
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from datetime import date

from leaders.models import Leader
from members.models import ChurchMember

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
    Calculate the age of a Leader based on date of birth.
    """
    if date_of_birth:
        today = date.today()
        age = today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
        )
        return f"{age} years old"
    return "----"

def calculate_time_in_service(start_date):
    """
    Function to calculate the time in service (years, months, days)
    """
    if not start_date:
        return ""
    today = date.today()
    years = today.year - start_date.year
    months = today.month - start_date.month
    days = today.day - start_date.day

    if days < 0:
        months -= 1
        days += 30  # Approximate
    if months < 0:
        years -= 1
        months += 12

    return f"{years} years, {months} months, {days} days"


@login_required
def pastor_leader_detail_view(request, pk):
    """
    View to display all details of a specific leader.
    Only accessible to a user who is:
      - logged in
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a leader
      - leader.occupation == 'Senior Pastor'
    """
    # 1) Must be CHURCH_MEMBER
    user = request.user
    if user.user_type != 'CHURCH_MEMBER':
        raise PermissionDenied("Access denied: user type must be CHURCH_MEMBER.")

    # 2) Must have an Active ChurchMember
    church_member_user = getattr(user, 'church_member', None)
    if not church_member_user or church_member_user.status != 'Active':
        raise PermissionDenied("Access denied: ChurchMember must be active.")

    # 3) Must be a Leader
    leader_user = getattr(church_member_user, 'leader', None)
    if not leader_user:
        raise PermissionDenied("Access denied: ChurchMember is not a Leader.")

    # 4) Must have occupation == 'Senior Pastor'
    if leader_user.occupation != 'Senior Pastor':
        raise PermissionDenied("Access denied: Only Senior Pastors can access this page.")

    # ✅ If checks pass, proceed with the original logic
    leader = get_object_or_404(Leader, pk=pk)
    church_member = leader.church_member

    # Calculate time in service
    if leader.start_date:
        leader.time_in_service = calculate_time_in_service(leader.start_date)
        leader.save(update_fields=['time_in_service'])

    # Calculate the "since created" time
    since_created = calculate_since_created(leader.date_created)

    def format_boolean(value):
        return "✅" if value else "❌"

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
        ("❤️ Spouse Name", church_member.spouse_name or "----"),
        ("👶 Number of Children", church_member.number_of_children or "----"),
        ("📛 Emergency Contact Name", church_member.emergency_contact_name or "----"),
        ("📞 Emergency Contact Phone", church_member.emergency_contact_phone or "----"),
        ("🎭 Talent", church_member.talent or "----"),
        ("🌟 Special Interests", church_member.special_interests or "----"),
    ]

    return render(
        request, 
        "pastor/leaders/leader_detail.html", 
        {
            "leader": leader,
            "leader_details": leader_details,
        }
    )

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from leaders.utils import get_leaders_distribution_trend
from leaders.models import Leader
from members.models import ChurchMember

@login_required
def pastor_leaders_home(request):
    """
    Leaders Home Page:
    - Displays total active/inactive leaders.
    - Fetches distribution data for the line chart (communities & zones).
    - Accessible only by a user who is:
      - logged in
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a leader
      - leader.occupation == 'Senior Pastor'
    """

    # 1) Must be CHURCH_MEMBER
    user = request.user
    if user.user_type != 'CHURCH_MEMBER':
        raise PermissionDenied("Access denied: user type must be CHURCH_MEMBER.")

    # 2) Must have an Active ChurchMember
    church_member_user = getattr(user, 'church_member', None)
    if not church_member_user or church_member_user.status != 'Active':
        raise PermissionDenied("Access denied: ChurchMember must be active.")

    # 3) Must be a Leader
    leader_user = getattr(church_member_user, 'leader', None)
    if not leader_user:
        raise PermissionDenied("Access denied: ChurchMember is not a Leader.")

    # 4) Must have occupation == 'Senior Pastor'
    if leader_user.occupation != 'Senior Pastor':
        raise PermissionDenied("Access denied: Only Senior Pastors can access this view.")

    # ✅ If checks pass, proceed with original logic
    total_active_leaders = Leader.objects.filter(church_member__status='Active').count()
    total_inactive_leaders = Leader.objects.filter(church_member__status='Inactive').count()

    leaders_distribution_data = get_leaders_distribution_trend()

    return render(
        request,
        'pastor/leaders/leaders_home.html',
        {
            'total_active_leaders': total_active_leaders,
            'total_inactive_leaders': total_inactive_leaders,
            'leaders_distribution_data': leaders_distribution_data,
        }
    )

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

@login_required
def pastor_chatbot_view(request):
    """
    Chatbot view accessible only to a user who is:
      - logged in
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a leader
      - leader.occupation == 'Senior Pastor'
    """
    user = request.user

    # 1) Must be CHURCH_MEMBER
    if user.user_type != 'CHURCH_MEMBER':
        raise PermissionDenied("Access denied: user type must be CHURCH_MEMBER.")

    # 2) Must have an Active ChurchMember
    church_member_user = getattr(user, 'church_member', None)
    if not church_member_user or church_member_user.status != 'Active':
        raise PermissionDenied("Access denied: ChurchMember must be active.")

    # 3) Must be a Leader
    leader_user = getattr(church_member_user, 'leader', None)
    if not leader_user:
        raise PermissionDenied("Access denied: ChurchMember is not a Leader.")

    # 4) Must have occupation == 'Senior Pastor'
    if leader_user.occupation != 'Senior Pastor':
        raise PermissionDenied("Access denied: Only Senior Pastors can access the chatbot.")

    # ✅ If checks pass, proceed with original chatbot logic
    faq = {
        "How can I see my details?": (
            "You can see your details by simply pressing the dashboard details box, or "
            "using the sidebar by pressing the toggle button and then pressing the details button, "
            "or using the arrow icon located at the bottom right-hand side of your viewport by pressing it "
            "and then selecting the details button."
        ),
        "How can I see the posts?": (
            "You can see and create posts by just pressing the Posts box in your dashboard, "
            "or pressing the toggle button of the sidebar located at the top-left-hand side, "
            "then pressing the posts button, or using the bottom bar by pressing the arrow icon located "
            "at the bottom right-hand side, then pressing the posts button."
        ),
        "How can I see the notifications?": (
            "You can see the notifications by pressing the notifications button on your dashboard, "
            "the sidebar toggle button, or the bottom bar arrow icon."
        ),
        "How can I see my tithe history?": (
            "You can see your tithe history by pressing the tithe history button on your dashboard, "
            "the sidebar toggle button, or the bottom bar arrow icon."
        ),
        "How can I create my posts?": (
            "You can create posts by going to the posts list and then pressing the create new post button. "
            "You will visit the page for creating a post. Note that you cannot update or delete your post. "
            "Make sure your posts are related to religious matters."
        ),
        "How can I get more support?": (
            "You can get more support by contacting the church directly via email at "
            "<a href='mailto:kigangomkwawa123@gmail.com'>kigangomkwawa123@gmail.com</a> or by calling "
            "<a href='tel:+255767972343'>+255767972343</a>."
        ),
        "Where can I get services like this?": (
            "You can get services like this by contacting Kizitasoft Company Limited at "
            "<a href='tel:+255762023662'>+255762023662</a>, <a href='tel:+255741943155'>+255741943155</a>, "
            "or <a href='tel:+255763968849'>+255763968849</a>. You can also reach them via email at "
            "<a href='mailto:kizitasoft805@gmail.com'>kizitasoft805@gmail.com</a> or "
            "<a href='mailto:kizitasoft@gmail.com'>kizitasoft@gmail.com</a>."
        ),
    }

    context = {
        "user": user,
        "faq": faq,
    }
    return render(request, "pastor/churchmember/chatbot.html", context)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count

from members.models import ChurchMember
from settings.models import Cell, OutStation  # Updated imports: Community → Cell, Zone → OutStation
from leaders.models import Leader

@login_required
def pastor_report(request):
    """
    Generates a comprehensive statistics report for the pastor.
    Accessible only if the user is:
      - logged in
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a leader
      - leader.occupation == 'Senior Pastor'
    """

    user = request.user

    # 1) Must be CHURCH_MEMBER
    if user.user_type != 'CHURCH_MEMBER':
        raise PermissionDenied("Access denied: user type must be CHURCH_MEMBER.")

    # 2) Must have an Active ChurchMember
    church_member_user = getattr(user, 'church_member', None)
    if not church_member_user or church_member_user.status != 'Active':
        raise PermissionDenied("Access denied: ChurchMember must be active.")

    # 3) Must be a Leader
    leader_user = getattr(church_member_user, 'leader', None)
    if not leader_user:
        raise PermissionDenied("Access denied: ChurchMember is not a Leader.")

    # 4) Must have occupation == 'Senior Pastor'
    if leader_user.occupation != 'Senior Pastor':
        raise PermissionDenied("Access denied: Only Senior Pastors can access this report.")

    # ✅ If checks pass, proceed with the statistics logic
    total_active_members = ChurchMember.objects.filter(status='Active').count()
    total_inactive_members = ChurchMember.objects.filter(status='Inactive').count()

    active_baptized = ChurchMember.objects.filter(status='Active', is_baptised=True).count()
    active_unbaptized = ChurchMember.objects.filter(status='Active', is_baptised=False).count()

    # Use date_confirmed instead of is_confirmed (corrected field)
    active_confirmed = ChurchMember.objects.filter(status='Active', date_confirmed__isnull=False).count()
    active_unconfirmed = ChurchMember.objects.filter(status='Active', date_confirmed__isnull=True).count()

    # Use marital_status instead of is_married (corrected field)
    active_married_male = ChurchMember.objects.filter(status='Active', marital_status='Married', gender='Male').count()
    inactive_unmarried_male = ChurchMember.objects.filter(status='Inactive', marital_status__in=['Single', 'Divorced', 'Widowed'], gender='Male').count()
    active_married_female = ChurchMember.objects.filter(status='Active', marital_status='Married', gender='Female').count()
    inactive_unmarried_female = ChurchMember.objects.filter(status='Inactive', marital_status__in=['Single', 'Divorced', 'Widowed'], gender='Female').count()

    total_outstations = OutStation.objects.count()  # Updated from total_zones
    total_cells = Cell.objects.count()  # Updated from total_communities

    outstations = OutStation.objects.all()  # Updated from zones
    outstation_stats = []  # Updated from zone_stats
    for o in outstations:
        members_in_outstation = ChurchMember.objects.filter(cell__outstation=o)  # Updated relationship: community__zone → cell__outstation

        outstation_baptized = members_in_outstation.filter(is_baptised=True).count()
        outstation_unbaptized = members_in_outstation.filter(is_baptised=False).count()
        outstation_confirmed = members_in_outstation.filter(date_confirmed__isnull=False).count()  # Updated field
        outstation_unconfirmed = members_in_outstation.filter(date_confirmed__isnull=True).count()  # Updated field
        outstation_married_male = members_in_outstation.filter(marital_status='Married', gender='Male').count()  # Updated field
        outstation_unmarried_male = members_in_outstation.filter(marital_status__in=['Single', 'Divorced', 'Widowed'], gender='Male').count()  # Updated field
        outstation_married_female = members_in_outstation.filter(marital_status='Married', gender='Female').count()  # Updated field
        outstation_unmarried_female = members_in_outstation.filter(marital_status__in=['Single', 'Divorced', 'Widowed'], gender='Female').count()  # Updated field
        active_leaders_in_outstation = members_in_outstation.filter(status='Active', leader__isnull=False).count()

        outstation_stats.append({
            'outstation': o,  # Updated key from zone to outstation
            'outstation_baptized': outstation_baptized,  # Updated from zone_baptized
            'outstation_unbaptized': outstation_unbaptized,  # Updated from zone_unbaptized
            'outstation_confirmed': outstation_confirmed,  # Updated from zone_confirmed
            'outstation_unconfirmed': outstation_unconfirmed,  # Updated from zone_unconfirmed
            'outstation_married_male': outstation_married_male,  # Updated from zone_married_male
            'outstation_unmarried_male': outstation_unmarried_male,  # Updated from zone_unmarried_male
            'outstation_married_female': outstation_married_female,  # Updated from zone_married_female
            'outstation_unmarried_female': outstation_unmarried_female,  # Updated from zone_unmarried_female
            'active_leaders_in_outstation': active_leaders_in_outstation,  # Updated from active_leaders_in_zone
        })

    cells = Cell.objects.select_related('outstation').all()  # Updated from communities, zone → outstation
    cell_stats = []  # Updated from community_stats
    for c in cells:
        members_in_cell = ChurchMember.objects.filter(cell=c)  # Updated from community to cell

        cell_baptized = members_in_cell.filter(is_baptised=True).count()  # Updated from comm_baptized
        cell_unbaptized = members_in_cell.filter(is_baptised=False).count()  # Updated from comm_unbaptized
        cell_confirmed = members_in_cell.filter(date_confirmed__isnull=False).count()  # Updated from comm_confirmed
        cell_unconfirmed = members_in_cell.filter(date_confirmed__isnull=True).count()  # Updated from comm_unconfirmed
        cell_married_male = members_in_cell.filter(marital_status='Married', gender='Male').count()  # Updated from comm_married_male
        cell_unmarried_male = members_in_cell.filter(marital_status__in=['Single', 'Divorced', 'Widowed'], gender='Male').count()  # Updated from comm_unmarried_male
        cell_married_female = members_in_cell.filter(marital_status='Married', gender='Female').count()  # Updated from comm_married_female
        cell_unmarried_female = members_in_cell.filter(marital_status__in=['Single', 'Divorced', 'Widowed'], gender='Female').count()  # Updated from comm_unmarried_female
        active_leaders_in_cell = members_in_cell.filter(status='Active', leader__isnull=False).count()  # Updated from active_leaders_in_comm

        display_name = f"{c.name} ({c.outstation.name})"  # Updated from zone to outstation

        cell_stats.append({
            'cell': c,  # Updated from community to cell
            'display_name': display_name,
            'cell_baptized': cell_baptized,  # Updated from comm_baptized
            'cell_unbaptized': cell_unbaptized,  # Updated from comm_unbaptized
            'cell_confirmed': cell_confirmed,  # Updated from comm_confirmed
            'cell_unconfirmed': cell_unconfirmed,  # Updated from comm_unconfirmed
            'cell_married_male': cell_married_male,  # Updated from comm_married_male
            'cell_unmarried_male': cell_unmarried_male,  # Updated from comm_unmarried_male
            'cell_married_female': cell_married_female,  # Updated from comm_married_female
            'cell_unmarried_female': cell_unmarried_female,  # Updated from comm_unmarried_female
            'active_leaders_in_cell': active_leaders_in_cell,  # Updated from active_leaders_in_comm
        })

    overall_active_leaders = ChurchMember.objects.filter(status='Active', leader__isnull=False).count()
    overall_inactive_leaders = ChurchMember.objects.filter(status='Inactive', leader__isnull=False).count()

    context = {
        'total_active_members': total_active_members,
        'total_inactive_members': total_inactive_members,

        'active_baptized': active_baptized,
        'active_unbaptized': active_unbaptized,
        'active_confirmed': active_confirmed,
        'active_unconfirmed': active_unconfirmed,
        'active_married_male': active_married_male,
        'inactive_unmarried_male': inactive_unmarried_male,
        'active_married_female': active_married_female,
        'inactive_unmarried_female': inactive_unmarried_female,

        'total_outstations': total_outstations,  # Updated from total_zones
        'total_cells': total_cells,  # Updated from total_communities

        'outstation_stats': outstation_stats,  # Updated from zone_stats
        'cell_stats': cell_stats,  # Updated from community_stats

        'overall_active_leaders': overall_active_leaders,
        'overall_inactive_leaders': overall_inactive_leaders,
    }

    return render(request, 'pastor/pastor_report.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import PastorReport, DatesOfServices, VisitedLocalCongregation
from .forms import (
    PastorReportForm,
    DatesOfServicesFormSet,
    VisitedLocalCongregationFormSet
)

class PastorReportCreateView(LoginRequiredMixin, View):
    """
    A single view for both creating and updating a PastorReport.
    If 'pk' is provided, we load that PastorReport for update;
    otherwise, we create a new one.
    After saving, redirects to 'pastor_report_detail'.

    Accessible only to a user who:
      - is logged in (LoginRequiredMixin)
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a leader
      - leader.occupation == 'Senior Pastor'
    """
    template_name = 'pastor/pastor_report_form.html'

    def user_is_senior_pastor(self, request):
        """
        Checks whether the logged-in user meets the Senior Pastor criteria.
        Raises PermissionDenied if any condition fails.
        """
        user = request.user

        # Must be CHURCH_MEMBER
        if user.user_type != 'CHURCH_MEMBER':
            raise PermissionDenied("Access denied: user type must be CHURCH_MEMBER.")

        # Must have an Active ChurchMember
        church_member_user = getattr(user, 'church_member', None)
        if not church_member_user or church_member_user.status != 'Active':
            raise PermissionDenied("Access denied: ChurchMember must be active.")

        # Must be a Leader
        leader_user = getattr(church_member_user, 'leader', None)
        if not leader_user:
            raise PermissionDenied("Access denied: ChurchMember is not a Leader.")

        # Must have occupation == 'Senior Pastor'
        if leader_user.occupation != 'Senior Pastor':
            raise PermissionDenied("Access denied: Only Senior Pastors can access this.")

    def get_object(self, pk):
        """Fetches an existing PastorReport or returns None if pk is None."""
        if pk is not None:
            return get_object_or_404(PastorReport, pk=pk)
        return None

    def get(self, request, pk=None, *args, **kwargs):
        # Ensure user meets the Senior Pastor criteria
        self.user_is_senior_pastor(request)

        instance = self.get_object(pk)

        if instance:
            # Updating
            report_form = PastorReportForm(instance=instance)
            dates_formset = DatesOfServicesFormSet(prefix='dates', instance=instance)
            congregations_formset = VisitedLocalCongregationFormSet(prefix='congregations', instance=instance)
        else:
            # Creating
            report_form = PastorReportForm()
            dates_formset = DatesOfServicesFormSet(prefix='dates', queryset=DatesOfServices.objects.none())
            congregations_formset = VisitedLocalCongregationFormSet(prefix='congregations', queryset=VisitedLocalCongregation.objects.none())

        return render(request, self.template_name, {
            'report_form': report_form,
            'dates_formset': dates_formset,
            'congregations_formset': congregations_formset,
            'instance': instance,
        })

    def post(self, request, pk=None, *args, **kwargs):
        # Ensure user meets the Senior Pastor criteria
        self.user_is_senior_pastor(request)

        instance = self.get_object(pk)

        if instance:
            # Updating existing
            report_form = PastorReportForm(request.POST, instance=instance)
            dates_formset = DatesOfServicesFormSet(request.POST, prefix='dates', instance=instance)
            congregations_formset = VisitedLocalCongregationFormSet(request.POST, prefix='congregations', instance=instance)
        else:
            # Creating new
            report_form = PastorReportForm(request.POST)
            dates_formset = DatesOfServicesFormSet(request.POST, prefix='dates')
            congregations_formset = VisitedLocalCongregationFormSet(request.POST, prefix='congregations')

        if (report_form.is_valid() 
            and dates_formset.is_valid() 
            and congregations_formset.is_valid()):

            saved_report = report_form.save()
            # Attach child formsets to this saved object
            dates_formset.instance = saved_report
            congregations_formset.instance = saved_report
            dates_formset.save()
            congregations_formset.save()

            if instance:
                messages.success(request, "Pastor Report updated successfully!")
            else:
                messages.success(request, "Pastor Report created successfully!")

            # Redirect to the detail page after saving
            return redirect('pastor_report_detail', pk=saved_report.pk)

        # If invalid, re-render with errors
        return render(request, self.template_name, {
            'report_form': report_form,
            'dates_formset': dates_formset,
            'congregations_formset': congregations_formset,
            'instance': instance,
        })

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import PastorReport

@login_required
def all_reports(request):
    """
    Displays a simple list of all PastorReport records,
    showing month, year, date_created, and date_updated,
    ordered from newest to oldest by date_created.
    Accessible only to a user who is:
      - logged in
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - is a leader
      - leader.occupation == 'Senior Pastor'
    """
    # 1) Must be CHURCH_MEMBER
    user = request.user
    if user.user_type != 'CHURCH_MEMBER':
        raise PermissionDenied("Access denied: user type must be CHURCH_MEMBER.")

    # 2) Must have an Active ChurchMember
    church_member_user = getattr(user, 'church_member', None)
    if not church_member_user or church_member_user.status != 'Active':
        raise PermissionDenied("Access denied: ChurchMember must be active.")

    # 3) Must be a Leader
    leader_user = getattr(church_member_user, 'leader', None)
    if not leader_user:
        raise PermissionDenied("Access denied: ChurchMember is not a Leader.")

    # 4) Must have occupation == 'Senior Pastor'
    if leader_user.occupation != 'Senior Pastor':
        raise PermissionDenied("Access denied: Only Senior Pastors can view all reports.")

    # ✅ If checks pass, proceed with original logic
    reports = (
        PastorReport.objects
        .select_related('year')
        .order_by('-date_created')
    )

    return render(request, 'pastor/all_reports.html', {
        'reports': reports,
    })

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import PastorReport

@login_required
def pastor_report_detail(request, pk):
    """
    Retrieves a single PastorReport by its primary key (pk)
    and displays it in a detailed block structure.
    Accessible only to a user who is:
      - logged in
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a leader
      - leader.occupation == 'Senior Pastor'
    """
    user = request.user

    # 1) Must be CHURCH_MEMBER
    if user.user_type != 'CHURCH_MEMBER':
        raise PermissionDenied("Access denied: user type must be CHURCH_MEMBER.")

    # 2) Must have an Active ChurchMember
    church_member_user = getattr(user, 'church_member', None)
    if not church_member_user or church_member_user.status != 'Active':
        raise PermissionDenied("Access denied: ChurchMember must be active.")

    # 3) Must be a Leader
    leader_user = getattr(church_member_user, 'leader', None)
    if not leader_user:
        raise PermissionDenied("Access denied: ChurchMember is not a Leader.")

    # 4) Must have occupation == 'Senior Pastor'
    if leader_user.occupation != 'Senior Pastor':
        raise PermissionDenied("Access denied: Only Senior Pastors can view report details.")

    # ✅ If all checks pass, proceed
    report = get_object_or_404(
        PastorReport.objects.select_related('year')
                            .prefetch_related('dates_of_services', 'visited_congregations'),
        pk=pk
    )

    # The template expects a list named 'reports'. We'll pass just [report].
    return render(request, 'pastor/pastor_report_detail.html', {
        'reports': [report],  # Single report in a list so the template can loop
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages

from .models import PastorReport

@login_required
def pastor_report_delete(request, pk):
    """
    Deletes a single PastorReport after confirming.
    Accessible only if the logged-in user is:
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - is a leader
      - leader.occupation == 'Senior Pastor'
    """
    user = request.user

    # 1) Must be CHURCH_MEMBER
    if user.user_type != 'CHURCH_MEMBER':
        raise PermissionDenied("Access denied: user type must be CHURCH_MEMBER.")

    # 2) Must have an Active ChurchMember
    church_member_user = getattr(user, 'church_member', None)
    if not church_member_user or church_member_user.status != 'Active':
        raise PermissionDenied("Access denied: ChurchMember must be active.")

    # 3) Must be a Leader
    leader_user = getattr(church_member_user, 'leader', None)
    if not leader_user:
        raise PermissionDenied("Access denied: ChurchMember is not a Leader.")

    # 4) Must have occupation == 'Senior Pastor'
    if leader_user.occupation != 'Senior Pastor':
        raise PermissionDenied("Access denied: Only Senior Pastors can delete a PastorReport.")

    # ✅ If all checks pass, proceed with the deletion logic
    report = get_object_or_404(PastorReport, pk=pk)

    if request.method == "POST":
        # User confirmed the deletion
        report.delete()
        messages.success(request, "Pastor report deleted successfully!")
        # Redirect anywhere, e.g. back to the all_reports page
        return redirect('all_reports')  # or wherever you want

    # If GET, render the confirmation page
    return render(
        request,
        'pastor/pastor_report_confirm_delete.html',
        {'report': report}
    )
