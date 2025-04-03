from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

User = get_user_model()

def authenticate_with_username_or_email(username_or_email, password):
    """
    Authenticates a user using either username or email and password.
    Returns the user object if authentication is successful, else None.
    """
    try:
        # Check if the input matches an email
        user = User.objects.get(email=username_or_email)
    except User.DoesNotExist:
        # If not an email, treat it as a username
        try:
            user = User.objects.get(username=username_or_email)
        except User.DoesNotExist:
            return None

    # Validate the password
    if user.check_password(password):
        return user
    return None


def get_client_ip(request):
    """
    Returns the real client IP address from the request,
    handling proxies if needed.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # If multiple IP addresses, get the first (i.e., the real client)
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip

import json
from django.utils.timezone import now
from django.db.models import Sum
from finance.models import Offerings, FacilityRenting, DonationItemFund

def get_general_finance_analysis():
    """
    Fetches total amounts from Offerings, Facility Renting, and Special Contributions
    for the current year and returns JSON data for visualization.
    """
    current_year = now().year

    # Fetch total amount from each financial component
    total_offerings = Offerings.objects.filter(date_given__year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0
    total_facility_renting = FacilityRenting.objects.filter(date_rented__year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0
    total_special_contributions = DonationItemFund.objects.filter(year__year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0

    # Convert Decimal values to float for JSON serialization
    total_offerings = float(total_offerings)
    total_facility_renting = float(total_facility_renting)
    total_special_contributions = float(total_special_contributions)

    # Data Labels and Values
    labels = ["Offerings", "Facility Renting", "Special Contributions"]
    data = [total_offerings, total_facility_renting, total_special_contributions]

    # Generate an analysis message
    analysis = (
        f"In the current year, the church received a total of **TZS {total_offerings:,.2f}** in offerings, "
        f"**TZS {total_facility_renting:,.2f}** from facility renting, and "
        f"**TZS {total_special_contributions:,.2f}** in special contributions."
    )

    # Return JSON data for Chart.js
    return json.dumps({
        "labels": labels,
        "data": data,
        "analysis": analysis
    })

# utils.py
import json
from django.utils.timezone import now
from members.models import ChurchMember

def get_general_sacraments_analysis():
    """
    Fetches the count of baptized, confirmed, and marital status categories
    and returns JSON data for visualization.
    """
    # Get the total count of members
    total_members = ChurchMember.objects.count()

    # Baptism statistics
    baptized = ChurchMember.objects.filter(is_baptised=True).count()
    unbaptized = ChurchMember.objects.filter(is_baptised=False).count()

    # Confirmation statistics (using date_confirmed as a proxy since is_confirmed is removed)
    confirmed = ChurchMember.objects.filter(date_confirmed__isnull=False).count()
    unconfirmed = ChurchMember.objects.filter(date_confirmed__isnull=True).count()

    # Marital status statistics
    married_males = ChurchMember.objects.filter(marital_status='Married', gender='Male').count()
    married_females = ChurchMember.objects.filter(marital_status='Married', gender='Female').count()
    unmarried_males = ChurchMember.objects.filter(marital_status__in=['Single', 'Divorced', 'Widowed'], gender='Male').count()
    unmarried_females = ChurchMember.objects.filter(marital_status__in=['Single', 'Divorced', 'Widowed'], gender='Female').count()

    # Data Labels and Values
    labels = [
        "Baptized", "Unbaptized",
        "Confirmed", "Unconfirmed",
        "Married Males", "Married Females",
        "Unmarried Males", "Unmarried Females"
    ]
    data = [
        baptized, unbaptized,
        confirmed, unconfirmed,
        married_males, married_females,
        unmarried_males, unmarried_females
    ]

    # Generate an analysis message with total members
    analysis = (
        f"The church has a total of **{total_members}** members. "
        f"Among them, **{baptized}** members are baptized, while **{unbaptized}** are unbaptized. "
        f"**{confirmed}** members are confirmed, and **{unconfirmed}** are not. "
        f"Among the married members, **{married_males}** are males and **{married_females}** are females. "
        f"Meanwhile, **{unmarried_males}** males and **{unmarried_females}** females remain unmarried."
    )

    # Return JSON data for Chart.js
    return json.dumps({
        "labels": labels,
        "data": data,
        "analysis": analysis
    })

import json
from django.db.models import Sum, F
from properties.models import ChurchAsset

def get_general_properties_analysis():
    """
    Fetches the count of church properties by status and calculates the total value.
    Returns JSON data for visualization with Chart.js.
    """
    # Get total number of properties
    total_properties = ChurchAsset.objects.count()

    # Get property counts by status
    statuses = ["Good", "Needs Repair", "Damaged", "Sold", "Donated"]
    property_counts = {
        status: ChurchAsset.objects.filter(status=status).count() for status in statuses
    }

    # Calculate total value of all properties
    total_value = ChurchAsset.objects.aggregate(total=Sum(F('quantity') * F('value')))['total'] or 0

    # Data Labels and Values
    labels = list(property_counts.keys())
    data = list(property_counts.values())

    # Generate an analysis message
    analysis = (
        f"The church owns a total of **{total_properties}** properties. "
        f"Among them, **{property_counts['Good']}** are in good condition, "
        f"**{property_counts['Needs Repair']}** need repair, **{property_counts['Damaged']}** are damaged, "
        f"**{property_counts['Sold']}** have been sold, and **{property_counts['Donated']}** have been donated. "
        f"The overall value of all properties combined is **TZS {total_value:,.2f}**."
    )

    # Return JSON data for Chart.js
    return json.dumps({
        "labels": labels,
        "data": data,
        "analysis": analysis
    })

import json
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from accounts.models import LoginHistory

def get_account_completion_analysis(user):
    """
    Calculates the percentage of profile details completed by an admin user.
    Also returns the time since the account was created and last login.
    Returns JSON data for Chart.js visualization.
    """
    User = get_user_model()

    # Required fields for a complete profile
    required_fields = [
        user.username, user.email, user.phone_number, user.profile_picture, user.first_name, user.last_name
    ]

    # Count filled fields
    filled_fields = sum(1 for field in required_fields if field)

    # Calculate completion percentage
    total_fields = len(required_fields)
    completion_percentage = round((filled_fields / total_fields) * 100, 2) if total_fields > 0 else 0

    # Get time since account creation
    account_age_days = (now() - user.date_joined).days

    # Get last login time
    last_login = user.last_login
    last_login_time = (now() - last_login).total_seconds() if last_login else None

    # Convert last login time to a readable format
    if last_login_time:
        if last_login_time < 60:
            last_login_desc = f"{int(last_login_time)} seconds ago"
        elif last_login_time < 3600:
            last_login_desc = f"{int(last_login_time // 60)} minutes ago"
        elif last_login_time < 86400:
            last_login_desc = f"{int(last_login_time // 3600)} hours ago"
        else:
            last_login_desc = f"{int(last_login_time // 86400)} days ago"
    else:
        last_login_desc = "Never logged in"

    # Generate an analysis message
    analysis = (
        f"Your profile is **{completion_percentage}%** complete. "
        f"Your account was created **{account_age_days} days ago**, and you last logged in **{last_login_desc}**. "
        "You can update your credentials at any time by pressing the **Details** box on the dashboard "
        "and clicking the **pencil icon**."
    )

    # Return JSON data for Chart.js
    return json.dumps({
        "labels": ["Completed", "Missing"],
        "data": [completion_percentage, 100 - completion_percentage],
        "analysis": analysis
    })

import json
from django.db.models import Count
from members.models import ChurchMember
from leaders.models import Leader
from settings.models import Cell, OutStation, Year  # Updated imports: Cell and OutStation

def get_leaders_distribution_analysis():
    """
    Fetches the count of leaders per cell, total male and female leaders,
    total leaders per outstation, and returns JSON data for visualization.
    """
    # Get total number of leaders
    total_leaders = Leader.objects.count()
    
    # Get total male and female leaders
    total_male_leaders = Leader.objects.filter(church_member__gender="Male").count()
    total_female_leaders = Leader.objects.filter(church_member__gender="Female").count()

    # Get leaders count by cell
    leaders_by_cell = (
        Leader.objects.values("church_member__cell__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Get leaders count by outstation (replaced zone)
    leaders_by_outstation = (
        Leader.objects.values("church_member__cell__outstation__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Filter out cells with no leaders
    cell_labels = [entry["church_member__cell__name"] for entry in leaders_by_cell if entry["church_member__cell__name"]]
    cell_counts = [entry["count"] for entry in leaders_by_cell if entry["church_member__cell__name"]]

    # Calculate percentage per cell
    cell_percentages = [
        round((count / total_leaders) * 100, 2) if total_leaders > 0 else 0
        for count in cell_counts
    ]

    # Generate an analysis message
    analysis = (
        f"The church has a total of **{total_leaders}** leaders, with **{total_male_leaders}** males and **{total_female_leaders}** females. "
        f"Leaders are distributed across various cells and outstations, with the highest concentration in some cells. "
        "You can use this analysis to manage leadership assignments effectively."
    )

    # Return JSON data for Chart.js
    return json.dumps({
        "labels": cell_labels,
        "data": cell_percentages,
        "total_leaders": total_leaders,
        "total_male_leaders": total_male_leaders,
        "total_female_leaders": total_female_leaders,
        "total_outstations": leaders_by_outstation.count(),  # Changed from total_zones
        "analysis": analysis
    })

def get_members_distribution_analysis():
    """
    Fetches the count of members per cell, total male and female members,
    total members per outstation, and total active and inactive members.
    Returns JSON data for visualization.
    """
    # Get total number of members
    total_members = ChurchMember.objects.count()

    # Get total male and female members
    total_male_members = ChurchMember.objects.filter(gender="Male").count()
    total_female_members = ChurchMember.objects.filter(gender="Female").count()

    # Get total active and inactive members
    total_active_members = ChurchMember.objects.filter(status="Active").count()
    total_inactive_members = ChurchMember.objects.filter(status="Inactive").count()

    # Get members count by cell
    members_by_cell = (
        ChurchMember.objects.values("cell__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Get members count by outstation (replaced zone)
    members_by_outstation = (
        ChurchMember.objects.values("cell__outstation__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Filter out cells with no members
    cell_labels = [entry["cell__name"] for entry in members_by_cell if entry["cell__name"]]
    cell_counts = [entry["count"] for entry in members_by_cell if entry["cell__name"]]

    # Calculate percentage per cell
    cell_percentages = [
        round((count / total_members) * 100, 2) if total_members > 0 else 0
        for count in cell_counts
    ]

    # Generate an analysis message
    analysis = (
        f"The church has a total of **{total_members}** members, with **{total_male_members}** males and **{total_female_members}** females. "
        f"Among them, **{total_active_members}** are active, while **{total_inactive_members}** are inactive. "
        f"Members are distributed across various cells and outstations, with the highest concentration in some cells."
    )

    # Return JSON data for Chart.js
    return json.dumps({
        "labels": cell_labels,
        "data": cell_percentages,
        "total_members": total_members,
        "total_male_members": total_male_members,
        "total_female_members": total_female_members,
        "total_outstations": members_by_outstation.count(),  # Changed from total_zones
        "total_active_members": total_active_members,
        "total_inactive_members": total_inactive_members,
        "analysis": analysis
    })

from accounts.models import CustomUser
from news.models import News
from notifications.models import Notification

def get_general_data_analysis():
    """
    Fetches the count of years, outstations, cells, accounts, news, notifications,
    total members, total leaders, and total properties.
    Returns JSON data for visualization in a Polar Area Chart.
    """
    # Get total counts
    total_years = Year.objects.count()
    total_outstations = OutStation.objects.count()  # Changed from Zone
    total_cells = Cell.objects.count()  # Changed from Community
    total_accounts = CustomUser.objects.count()
    total_news = News.objects.count()
    total_notifications = Notification.objects.count()
    total_members = ChurchMember.objects.count()
    total_leaders = Leader.objects.count()
    total_properties = ChurchAsset.objects.count()

    # Data Labels and Values
    labels = [
        "Years", "Outstations", "Cells", "Accounts",  # Updated labels
        "News", "Notifications", "Total Members", "Total Leaders", "Total Properties"
    ]
    data = [
        total_years, total_outstations, total_cells, total_accounts,
        total_news, total_notifications, total_members, total_leaders, total_properties
    ]

    # Generate an analysis message
    analysis = (
        f"The system currently holds **{total_years}** saved years, **{total_outstations}** church outstations, "
        f"and **{total_cells}** cells. There are **{total_accounts}** user accounts, "
        f"**{total_news}** published news articles, and **{total_notifications}** notifications sent. "
        f"The total number of church members is **{total_members}**, with **{total_leaders}** serving as leaders. "
        f"Additionally, the system manages **{total_properties}** church assets."
    )

    # Return JSON data for Chart.js
    return json.dumps({
        "labels": labels,
        "data": data,
        "total_years": total_years,
        "total_outstations": total_outstations,  # Changed from total_zones
        "total_cells": total_cells,  # Changed from total_communities
        "total_accounts": total_accounts,
        "total_news": total_news,
        "total_notifications": total_notifications,
        "total_members": total_members,
        "total_leaders": total_leaders,
        "total_properties": total_properties,
        "analysis": analysis
    })