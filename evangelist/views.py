from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from members.models import ChurchMember
from leaders.models import Leader

@login_required
def evangelist_details(request):
    """
    View to retrieve all details of an 'Evangelist':
    - Account Information
    - Membership Details
    - Leadership Details
    - Certificates (Displayed as Buttons)
    
    Accessible only to a user who:
      - is logged in
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a leader
      - leader.occupation == 'Evangelist'
    """
    user = request.user

    # 1) Must be CHURCH_MEMBER
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

    # 4) Must have occupation == 'Evangelist'
    if leader.occupation != 'Evangelist':
        raise PermissionDenied("Access denied: Only Evangelists can access this page.")

    # ✅ If checks pass, proceed with original logic
    def format_boolean(value):
        return '<span style="color: green; font-size: 18px;">✔️</span>' if value else '<span style="color: red; font-size: 18px;">❌</span>'

    # ✅ Account Details
    account_details = {
        "Username": user.username,
        "Email": user.email or "Not provided",
        "Phone Number": user.phone_number,
        "Date Created": user.date_created.strftime("%d %B %Y"),
    }

    # ✅ Membership Details
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
        "Confirmation Certificate": church_member.confirmation_certificate.url if church_member.confirmation_certificate else None,
        "Marriage Certificate": church_member.marriage_certificate.url if church_member.marriage_certificate else None,
    }

    # ✅ Passport (Move to Top)
    passport_url = church_member.passport.url if church_member.passport else None

    return render(request, "evangelist/evangelist_details.html", {
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

def format_time_since(created_date):
    """
    Returns a user-friendly time format based on Tanzania timezone.
    """
    if not created_date:
        return "N/A"

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
def evangelist_church_member_list(request):
    """
    View to display and filter the list of church members, 
    accessible only if the user is:
      - logged in
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a leader
      - leader.occupation == 'Evangelist'
    Members are sorted alphabetically by full name.
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

    # 4) Must have occupation == 'Evangelist'
    if leader_user.occupation != 'Evangelist':
        raise PermissionDenied("Access denied: Only Evangelists can access this view.")

    # ✅ If checks pass, proceed with original logic
    name_query = request.GET.get('name', '').strip()
    gender_query = request.GET.get('gender', '').strip()
    cell_query = request.GET.get('cell', '').strip()  # Updated from community to cell
    outstation_query = request.GET.get('outstation', '').strip()  # Updated from zone to outstation

    church_members = (
        ChurchMember.objects
        .select_related('cell__outstation')  # Updated relationship: community__zone → cell__outstation
        .filter(status="Active")
        .order_by('full_name')
    )

    # Apply filters
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
    cells = Cell.objects.all()  # Updated from communities to cells
    outstations = OutStation.objects.all()  # Updated from zones to outstations

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

    return render(request, 'evangelist/members/church_member_list.html', context)


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
def evangelist_inactive_church_member_list(request):
    """
    Displays a list of Inactive church members, filtered and sorted alphabetically by full name.
    Accessible only if:
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a leader
      - leader.occupation == 'Evangelist'
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

    # 4) Must have occupation == 'Evangelist'
    if leader_user.occupation != 'Evangelist':
        raise PermissionDenied("Access denied: Only Evangelists can access this view.")

    # ✅ If checks pass, proceed with original logic
    name_query = request.GET.get('name', '').strip()
    gender_query = request.GET.get('gender', '').strip()
    cell_query = request.GET.get('cell', '').strip()  # Updated from community to cell
    outstation_query = request.GET.get('outstation', '').strip()  # Updated from zone to outstation

    # Retrieve only Inactive members, sorted by full name
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

    # Distinct cells & outstations for dropdowns
    cells = Cell.objects.all()  # Updated from communities to cells
    outstations = OutStation.objects.all()  # Updated from zones to outstations

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

    return render(request, 'evangelist/members/church_member_list.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages

from members.models import ChurchMember
from members.utils import get_membership_distribution_analysis

@login_required
def evangelist_members_home(request):
    """
    Members Home Page:
      - Displays total active & inactive members
      - Fetches membership distribution data for graphs
      - Only accessible if user is:
        - logged in
        - user_type == 'CHURCH_MEMBER'
        - church_member.status == 'Active'
        - is a leader
        - leader.occupation == 'Evangelist'
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

    # 4) Must have occupation == 'Evangelist'
    if leader_user.occupation != 'Evangelist':
        raise PermissionDenied("Access denied: Only Evangelists can access this page.")

    # ✅ If checks pass, proceed with original logic
    total_active_members = ChurchMember.objects.filter(status='Active').count()
    total_inactive_members = ChurchMember.objects.filter(status='Inactive').count()

    membership_distribution_data = get_membership_distribution_analysis()

    return render(
        request,
        'evangelist/members/members_home.html',
        {
            'total_active_members': total_active_members,
            'total_inactive_members': total_inactive_members,
            'membership_distribution_data': membership_distribution_data
        }
    )


from django.shortcuts import render, get_object_or_404
from django.utils.timezone import localtime, now
from django.contrib.auth.decorators import login_required, user_passes_test
from members.models import ChurchMember
from datetime import date


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

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils.timezone import localtime, now
from datetime import date

from members.models import ChurchMember

@login_required
def evangelist_church_member_detail(request, pk):
    """
    View to retrieve and display all details of a specific ChurchMember,
    accessible only if the user is:
      - logged in
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a leader
      - leader.occupation == 'Evangelist'
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

    # 4) Must have occupation == 'Evangelist'
    if leader_user.occupation != 'Evangelist':
        raise PermissionDenied("Access denied: Only Evangelists can view church member detail.")

    # ✅ If checks pass, proceed with original logic
    church_member = get_object_or_404(ChurchMember, pk=pk)

    # Calculate "since created" time
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
        "🎂 Date of Birth": (
            church_member.date_of_birth.strftime('%d %B, %Y')
            if church_member.date_of_birth else "----"
        ),
        "🔢 Age": calculate_age(church_member.date_of_birth),
        "⚥ Gender": church_member.gender,
        "📞 Phone Number": church_member.phone_number,
        "📧 Email": church_member.email or "----",
        "🏠 Address": church_member.address or "----",
        "🏘️ Community": (
            f"{church_member.community.name} ({church_member.community.zone.name})"
            if church_member.community else "----"
        ),
        "🔘 Status": (
            "✅ Active" if church_member.status == "Active"
            else "❌ Inactive"
        ),
        "📅 Date Created": (
            f"{localtime(church_member.date_created).strftime('%d %B, %Y %I:%M %p')} "
            f"({since_created})"
        ),

        # Sacramental Info
        "🌊 Baptized": format_boolean(church_member.is_baptised),
        "🗓️ Date of Baptism": (
            church_member.date_of_baptism.strftime('%d %B, %Y')
            if church_member.date_of_baptism else "----"
        ),
        "🕊️ Confirmed": format_boolean(church_member.is_confirmed),
        "🗓️ Date of Confirmation": (
            church_member.date_confirmed.strftime('%d %B, %Y')
            if church_member.date_confirmed else "----"
        ),

        # Marriage
        "💍 Marital Status": church_member.marital_status or "----",
        "❤️ Spouse Name": church_member.spouse_name or "----",
        "👶 Number of Children": church_member.number_of_children or "----",
        "🗓️ Date of Marriage": (
            church_member.date_of_marriage.strftime('%d %B, %Y')
            if church_member.date_of_marriage else "----"
        ),

        # Additional
        "💼 Job": church_member.job or "----",
        "🎨 Talent": church_member.talent or "----",
        "🙏 Services": church_member.services or "----",
        "📛 Emergency Contact Name": church_member.emergency_contact_name or "----",
        "📞 Emergency Contact Phone": church_member.emergency_contact_phone or "----",
        "♿ Disability": church_member.disability or "----",
        "🌟 Special Interests": church_member.special_interests or "----",

        # Apostolic Movement
        "🕊️ Apostolic Movement": (
            church_member.apostolic_movement.name
            if church_member.apostolic_movement else "----"
        ),
        "👑 Is Leader of Movement?": format_boolean(church_member.is_the_member_a_leader_of_the_movement),
    }

    return render(
        request,
        'evangelist/members/church_member_detail.html',
        {
            'church_member': church_member,
            'details': details,
            'documents': documents
        }
    )

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
def evangelist_leader_list_view(request):
    """
    View to display a list of leaders with search and filtering options.
    Accessible only to a user who is:
      - logged in
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a leader
      - leader.occupation == 'Evangelist'
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

    # 4) Must have occupation == 'Evangelist'
    if leader_user.occupation != 'Evangelist':
        raise PermissionDenied("Access denied: Only Evangelists can access this view.")

    # ✅ If checks pass, proceed with the original logic
    search_name = request.GET.get('search_name', '').strip()
    search_gender = request.GET.get('search_gender', '')
    search_occupation = request.GET.get('search_occupation', '')
    search_cell = request.GET.get('search_cell', '')  # Updated from search_community to search_cell
    search_outstation = request.GET.get('search_outstation', '')  # Updated from search_zone to search_outstation

    # Retrieve Active Leaders sorted by name
    leaders = Leader.objects.filter(
        church_member__status="Active"
    ).order_by('church_member__full_name')

    # Update time in service for each leader
    for leader in leaders:
        if leader.start_date:
            leader.time_in_service = calculate_time_in_service(leader.start_date)
            leader.save(update_fields=['time_in_service'])

    # Filtering
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

    # Distinct cells and outstations
    all_cells = Cell.objects.all()  # Updated from all_communities to all_cells
    all_outstations = OutStation.objects.all()  # Updated from all_zones to all_outstations

    # Occupations from Leader model
    all_occupations = [choice[0] for choice in Leader.OCCUPATION_CHOICES]

    return render(request, 'evangelist/leaders/leader_list.html', {
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
def evangelist_inactive_leader_list_view(request):
    """
    View to display a list of inactive leaders with search and filtering options.
    Only accessible if user:
      - is logged in
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - is a leader
      - leader.occupation == 'Evangelist'
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

    # 4) Must have occupation-functions == 'Evangelist'
    if leader_user.occupation != 'Evangelist':
        raise PermissionDenied("Access denied: Only Evangelists can access this view.")

    # ✅ If checks pass, proceed with original logic
    search_name = request.GET.get('search_name', '').strip()
    search_gender = request.GET.get('search_gender', '')
    search_occupation = request.GET.get('search_occupation', '')
    search_cell = request.GET.get('search_cell', '')  # Updated from search_community to search_cell
    search_outstation = request.GET.get('search_outstation', '')  # Updated from search_zone to search_outstation

    # Retrieve Inactive Leaders, sorted by full name
    leaders = Leader.objects.filter(church_member__status="Inactive").order_by('church_member__full_name')

    # Update time in service for each leader
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

    # Distinct cells & outstations
    all_cells = Cell.objects.all()  # Updated from all_communities to all_cells
    all_outstations = OutStation.objects.all()  # Updated from all_zones to all_outstations

    # Occupations from Leader model
    all_occupations = [choice[0] for choice in Leader.OCCUPATION_CHOICES]

    return render(request, 'evangelist/leaders/inactive_leader_list.html', {
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
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils.timezone import localtime, now
from datetime import date

from leaders.models import Leader
from members.models import ChurchMember

def calculate_since_created(date_created):
    """
    Calculate the time since the leader's record was created (human-readable).
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
    Calculate the age of a Leader based on date_of_birth.
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
    Calculate the time in service (years, months, days).
    """
    if not start_date:
        return ""
    today = date.today()
    years = today.year - start_date.year
    months = today.month - start_date.month
    days = today.day - start_date.day

    if days < 0:
        months -= 1
        days += 30
    if months < 0:
        years -= 1
        months += 12

    return f"{years} years, {months} months, {days} days"


@login_required
def evangelist_leader_detail_view(request, pk):
    """
    View to display details of a specific Leader.
    Accessible only if:
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a Leader
      - leader.occupation == 'Evangelist'
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

    # 4) Must have occupation == 'Evangelist'
    if leader_user.occupation != 'Evangelist':
        raise PermissionDenied("Access denied: Only Evangelists can view this leader detail.")

    # ✅ If checks pass, continue
    leader = get_object_or_404(Leader, pk=pk)
    church_member = leader.church_member

    # Update time_in_service dynamically
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

    return render(request, "evangelist/leaders/leader_detail.html", {
        "leader": leader,
        "leader_details": leader_details,
    })


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from leaders.utils import get_leaders_distribution_trend
from leaders.models import Leader

@login_required
def evangelist_leaders_home(request):
    """
    Leaders Home Page:
      - Displays total active/inactive leaders.
      - Fetches distribution data for line charts (communities & zones).
      - Accessible only if user:
        - is logged in
        - user_type == 'CHURCH_MEMBER'
        - church_member.status == 'Active'
        - is a Leader
        - leader.occupation == 'Evangelist'
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

    # 4) Must have occupation == 'Evangelist'
    if leader_user.occupation != 'Evangelist':
        raise PermissionDenied("Access denied: Only Evangelists can view Leaders Home.")

    # ✅ If checks pass, proceed
    total_active_leaders = Leader.objects.filter(church_member__status='Active').count()
    total_inactive_leaders = Leader.objects.filter(church_member__status='Inactive').count()

    leaders_distribution_data = get_leaders_distribution_trend()

    return render(request, 'evangelist/leaders/leaders_home.html', {
        'total_active_leaders': total_active_leaders,
        'total_inactive_leaders': total_inactive_leaders,
        'leaders_distribution_data': leaders_distribution_data,
    })

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

@login_required
def evangelist_chatbot_view(request):
    """
    Evangelist Chatbot View:
      - Shows a list of predefined Q&A
      - Accessible only if user is:
        - logged in
        - user_type == 'CHURCH_MEMBER'
        - church_member.status == 'Active'
        - is a leader
        - leader.occupation == 'Evangelist'
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

    # 4) Must have occupation == 'Evangelist'
    if leader_user.occupation != 'Evangelist':
        raise PermissionDenied("Access denied: Only Evangelists can access the chatbot.")

    # ✅ If checks pass, proceed with chatbot logic
    faq = {
        "How can I see my details?": (
            "You can see your details by simply pressing the dashboard details box, "
            "or using the sidebar by pressing the toggle button and then pressing the details button, "
            "or using the arrow icon located at the bottom right-hand side of your viewport "
            "by pressing it and then selecting the details button."
        ),
        "How can I see the posts?": (
            "You can see and create the posts by just simply pressing the Posts box in your dashboard, "
            "or pressing the toggle button of the sidebar located at the top-left-hand side then pressing the posts button, "
            "or using the bottom bar by pressing the arrow icon located at the bottom right-hand side then pressing the posts button."
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
        "faq": faq
    }
    return render(request, "evangelist/churchmember/chatbot.html", context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from news.forms import NewsForm, NewsMediaForm
from news.models import News, NewsMedia
from members.models import ChurchMember
from leaders.models import Leader

@login_required
def evangelist_create_news_view(request, pk=None):
    """
    View to create or update a news post with multiple media uploads.
    Accessible only to a user who:
      - is logged in
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a leader
      - leader.occupation == 'Evangelist'
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

    # 4) Must have occupation == 'Evangelist'
    if leader_user.occupation != 'Evangelist':
        raise PermissionDenied("Access denied: Only Evangelists can create or update news.")

    # ✅ If checks pass, proceed with the original logic
    news = None
    if pk:
        news = get_object_or_404(News, pk=pk)  # Retrieve existing news for updating

    if request.method == "POST":
        form = NewsForm(request.POST, instance=news)
        media_types = request.POST.getlist('media_type')
        media_files = request.FILES.getlist('file')

        if form.is_valid():
            news = form.save()  # Create or update the news post

            # If updating, remove old media
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

            return redirect("evangelist_news_list")  # Redirect to the news list page
        else:
            messages.error(request, "❌ Please correct the errors in the form.")
    else:
        form = NewsForm(instance=news)  # Pre-fill form if updating

    return render(request, "evangelist/news/create_news.html", {"form": form, "news": news})

from django.shortcuts import render
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
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
def evangelist_news_list_view(request):
    """
    View to display a list of news articles with the time since creation,
    accessible only to a user who is:
      - logged in
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a leader
      - leader.occupation == 'Evangelist'
    """
    # 1) Must be CHURCH_MEMBER
    user = request.user
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

    # 4) Must have occupation == 'Evangelist'
    if leader.occupation != 'Evangelist':
        raise PermissionDenied("Access denied: Only Evangelists can access the news list.")

    # ✅ If checks pass, proceed
    news_list = News.objects.all()

    # Calculate "time since created" for each news
    for news in news_list:
        news.time_since_created = calculate_time_since(news.created_at)

    return render(request, "evangelist/news/news_list.html", {"news_list": news_list})

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils.timezone import now
from datetime import timedelta

from news.models import News
from members.models import ChurchMember
from leaders.models import Leader

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
def evangelist_news_detail_view(request, pk):
    """
    View to display full details of a specific news article,
    accessible only to a user who is:
      - logged in
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a leader
      - leader.occupation == 'Evangelist'
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

    # 4) Must have occupation == 'Evangelist'
    if leader_user.occupation != 'Evangelist':
        raise PermissionDenied("Access denied: Only Evangelists can view news details.")

    # ✅ If checks pass, proceed with original logic
    news = get_object_or_404(News, pk=pk)
    news.time_since_created = calculate_time_since(news.created_at)

    # Separate media by type
    images = news.media.filter(media_type='image')
    videos = news.media.filter(media_type='video')
    documents = news.media.filter(media_type='document')

    return render(request, "evangelist/news/news_detail.html", {
        "news": news,
        "images": images,
        "videos": videos,
        "documents": documents,
    })


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from news.models import News, NewsMedia

@login_required
def evangelist_delete_news_view(request, pk):
    """
    View to delete a news article and all associated media.
    Accessible only if user is:
      - logged in
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a leader
      - leader.occupation == 'Evangelist'
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

    # 4) Must have occupation == 'Evangelist'
    if leader_user.occupation != 'Evangelist':
        raise PermissionDenied("Access denied: Only Evangelists can delete news.")

    # ✅ If checks pass, proceed to delete
    news = get_object_or_404(News, pk=pk)

    if request.method == "POST":
        # Delete all associated media files
        news.media.all().delete()
        
        # Delete the news post itself
        news.delete()

        messages.success(request, "News post and all associated media deleted successfully!")
        return redirect("evangelist_news_list")

    return render(request, "evangelist/news/delete_news.html", {"news": news})


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from news.models import News

@login_required(login_url='login')
def evangelist_news_home(request):
    """
    View for the News Home Page.
    Accessible only if user:
      - is logged in
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a leader
      - leader.occupation == 'Evangelist'
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

    # 4) Must have occupation == 'Evangelist'
    if leader_user.occupation != 'Evangelist':
        raise PermissionDenied("Access denied: Only Evangelists can view the news home.")

    # ✅ If checks pass, proceed with original logic
    news_count = News.objects.count()

    return render(request, 'evangelist/news/news_home.html', {
        'news_count': news_count
    })


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from notifications.models import Notification

@login_required
def evangelist_notifications_view(request):
    """
    View to retrieve all notifications for the logged-in church member.
    Only accessible if the user:
      - is logged in
      - user_type == 'CHURCH_MEMBER'
      - church_member.status == 'Active'
      - church_member is a leader
      - leader.occupation == 'Evangelist'

    Automatically marks all unread notifications as read when accessed.
    """
    user = request.user

    # 1) Must be CHURCH_MEMBER
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

    # 4) Must have occupation == 'Evangelist'
    if leader.occupation != 'Evangelist':
        raise PermissionDenied("Access denied: Only Evangelists can view notifications.")

    # ✅ If checks pass, proceed with original logic
    notifications = Notification.objects.filter(church_member=church_member).order_by('-created_at')
    # Mark unread notifications as read
    notifications.filter(is_read=False).update(is_read=True)

    return render(
        request,
        "evangelist/churchmember/member_notifications.html",
        {"notifications": notifications}
    )
