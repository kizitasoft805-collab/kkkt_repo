import json
from django.db.models import Count
from settings.models import OutStation, Cell
from members.models import ChurchMember

def get_outstations_analysis():
    """
    Fetches:
      - The total number of members in each outstation (line chart).
      - The outstation with the largest membership.
      - The outstation with the smallest membership.
      - The total number of outstations overall.
      - The count of members per outstation.

    Returns JSON data for Chart.js, plus textual analysis.
    """

    # Query for each outstation + number of members associated
    # (via the outstation->cells->members relationship)
    outstations_qs = (
        ChurchMember.objects.values("cell__outstation__name")  # get outstation name
        .annotate(count=Count("id"))                           # how many members
        .order_by("cell__outstation__name")                    # sort by outstation name
    )

    # Create lists for Chart.js
    outstation_labels = []
    outstation_counts = []

    for entry in outstations_qs:
        outstation_name = entry["cell__outstation__name"]
        if outstation_name:  # ensure outstation is not None
            outstation_labels.append(outstation_name)
            outstation_counts.append(entry["count"])

    # Compute total outstations (from OutStation table)
    total_outstations = OutStation.objects.count()

    # If we have data, find largest & smallest
    largest_outstation = "N/A"
    smallest_outstation = "N/A"
    largest_count = 0
    smallest_count = 0

    if outstation_labels:
        # Build a list of (outstation, count) to find max/min
        outstation_data = list(zip(outstation_labels, outstation_counts))
        # Sort by count ascending
        outstation_data_sorted = sorted(outstation_data, key=lambda x: x[1])
        smallest_outstation, smallest_count = outstation_data_sorted[0]
        largest_outstation, largest_count = outstation_data_sorted[-1]

    # Summaries for textual analysis
    total_members = sum(outstation_counts)

    # Build a list summarizing each outstation + count
    members_in_each_outstation_str = ", ".join(f"{z}: {c}" for z, c in zip(outstation_labels, outstation_counts))

    analysis_text = (
        f"There are {total_outstations} outstation(s) overall, with a total of {total_members} member(s) across all outstations. "
        f"Member counts by outstation: {members_in_each_outstation_str}. "
        f"The outstation with the largest membership is {largest_outstation} ({largest_count} member(s)), "
        f"while {smallest_outstation} has the fewest members ({smallest_count})."
    )

    # Return JSON data needed by Chart.js + extra strings for analysis
    return json.dumps({
        "labels": outstation_labels,
        "data": outstation_counts,
        "analysis": analysis_text,
        "total_outstations": total_outstations,
        "largest_outstation": largest_outstation,
        "largest_count": largest_count,
        "smallest_outstation": smallest_outstation,
        "smallest_count": smallest_count
    })

def get_cells_analysis():
    """
    Builds a bar chart and detailed analysis for all cells:
      - The total members in each cell (bar graph).
      - The cell with the largest number of members, and smallest.
      - # of baptized/unbaptized, confirmed/unconfirmed,
        married males/unmarried males, married females/unmarried females, etc.
      - Returns JSON for Chart.js plus a text summary of all categories.
    """
    cells = Cell.objects.order_by("name")

    labels = []
    data = []  # total members per cell for the bar chart

    # Track extra stats in a list for textual analysis
    details_list = []

    largest_cell_name = ""
    smallest_cell_name = ""
    largest_cell_count = 0
    smallest_cell_count = 0

    if cells.exists():
        smallest_cell_count = None  # so we can set it initially

    for cell in cells:
        members_qs = cell.members.all()

        # Basic totals
        total_count = members_qs.count()

        # Baptism
        baptized_count = members_qs.filter(is_baptised=True).count()
        unbaptized_count = total_count - baptized_count

        # Confirmation (using date_confirmed as proxy for confirmed status)
        confirmed_count = members_qs.filter(date_confirmed__isnull=False).count()
        unconfirmed_count = total_count - confirmed_count

        # Married Males / Unmarried Males
        married_males = members_qs.filter(marital_status='Married', gender="Male").count()
        unmarried_males = members_qs.exclude(marital_status='Married').filter(gender="Male").count()

        # Married Females / Unmarried Females
        married_females = members_qs.filter(marital_status='Married', gender="Female").count()
        unmarried_females = members_qs.exclude(marital_status='Married').filter(gender="Female").count()

        # Append to the bar chart data
        labels.append(cell.name)
        data.append(total_count)

        # Keep track for largest / smallest
        if total_count > largest_cell_count:
            largest_cell_count = total_count
            largest_cell_name = cell.name

        if smallest_cell_count is None or total_count < smallest_cell_count:
            smallest_cell_count = total_count
            smallest_cell_name = cell.name

        # Store all stats for textual analysis
        details_list.append({
            "cell_name": cell.name,
            "total_count": total_count,
            "baptized_count": baptized_count,
            "unbaptized_count": unbaptized_count,
            "confirmed_count": confirmed_count,
            "unconfirmed_count": unconfirmed_count,
            "married_males": married_males,
            "unmarried_males": unmarried_males,
            "married_females": married_females,
            "unmarried_females": unmarried_females,
        })

    # Summaries
    total_cells = cells.count()
    grand_total_members = sum(data)

    # Build a descriptive text
    analysis_text = (
        f"There are {total_cells} cell(s) in total, "
        f"with a grand total of {grand_total_members} member(s) across all cells. "
        f"The cell with the largest membership is {largest_cell_name} ({largest_cell_count} members), "
        f"while {smallest_cell_name} has the fewest members ({smallest_cell_count})."
    )

    # Return JSON for Chart.js plus the textual details
    return json.dumps({
        "labels": labels,
        "data": data,
        "analysis": analysis_text,
        "details": details_list,  # array of per-cell stats
        "total_cells": total_cells,
        "grand_total_members": grand_total_members,
        "largest_cell_name": largest_cell_name,
        "largest_cell_count": largest_cell_count,
        "smallest_cell_name": smallest_cell_name,
        "smallest_cell_count": smallest_cell_count
    })



import json
from members.models import ChurchMember

def get_active_inactive_analysis():
    """
    Returns JSON data for a pie chart showing the percentage of active vs. inactive members.
    Also includes a text summary of how many members are active/inactive.
    """
    active_count = ChurchMember.objects.filter(status="Active").count()
    inactive_count = ChurchMember.objects.filter(status="Inactive").count()

    total_members = active_count + inactive_count

    # If total_members is zero, handle gracefully
    if total_members == 0:
        # Provide no data for the pie chart
        labels = []
        data = []
        analysis_text = "No members in the system."
    else:
        labels = ["Active", "Inactive"]
        data = [active_count, inactive_count]
        analysis_text = (
            f"There are {active_count} active members and {inactive_count} inactive members "
            f"out of a total of {total_members} member(s)."
        )

    # Return JSON for Chart.js plus textual analysis
    return json.dumps({
        "labels": labels,
        "data": data,
        "analysis": analysis_text,
        "active_count": active_count,
        "inactive_count": inactive_count,
        "total_members": total_members
    })

import json
from leaders.models import Leader

def get_leaders_active_inactive_analysis():
    """
    Returns JSON data for a doughnut chart showing active vs. inactive leaders.
    Also includes text describing totals.
    """
    # Count how many leaders have 'Active' vs 'Inactive' status
    active_leaders_count = Leader.objects.filter(church_member__status="Active").count()
    inactive_leaders_count = Leader.objects.filter(church_member__status="Inactive").count()

    total_leaders = active_leaders_count + inactive_leaders_count

    if total_leaders == 0:
        # No leaders exist
        labels = []
        data = []
        analysis_text = "No leaders found in the system."
    else:
        labels = ["Active Leaders", "Inactive Leaders"]
        data = [active_leaders_count, inactive_leaders_count]
        analysis_text = (
            f"There are {total_leaders} leader(s) in total. "
            f"Among them, {active_leaders_count} are active and {inactive_leaders_count} are inactive."
        )

    # Return JSON for Chart.js plus textual analysis
    return json.dumps({
        "labels": labels,
        "data": data,
        "analysis": analysis_text,
        "active_leaders_count": active_leaders_count,
        "inactive_leaders_count": inactive_leaders_count,
        "total_leaders": total_leaders
    })

import json
from datetime import date, timedelta
from django.db.models import Sum
from django.utils.timezone import now
from django.db.models.functions import ExtractWeek, ExtractMonth, ExtractYear
from finance.models import Offerings

def get_offerings_analysis():
    """
    Gathers data for:
    - Line chart of total offerings (sum of amounts) per mass name, for the current year.
    - Identifies the mass with highest & lowest total offerings.
    - Builds a SINGLE descriptive text (long_description) that includes:
      - Overall total offerings (all years),
      - This year's total,
      - This month's total,
      - This week's total,
      - Last day total,
      - The highest & lowest mass info,
      - Advice/explanations.

    Returns JSON for Chart.js (line chart) and the single descriptive text.
    """

    current_year = now().year

    # 1) Group offerings by mass_name for the current year
    current_year_offerings = (
        Offerings.objects.filter(date_given__year=current_year)
        .values("mass_name")
        .annotate(total=Sum("amount"))
        .order_by("mass_name")
    )

    labels = []
    data = []

    highest_mass_name = ""
    highest_amount = 0
    lowest_mass_name = ""
    lowest_amount = 0
    if current_year_offerings.exists():
        lowest_amount = None

    for entry in current_year_offerings:
        mass = entry["mass_name"]
        amt = entry["total"] or 0
        labels.append(mass)
        data.append(float(amt))

        if amt > highest_amount:
            highest_amount = amt
            highest_mass_name = mass

        if lowest_amount is None or amt < lowest_amount:
            lowest_amount = amt
            lowest_mass_name = mass

    # 2) Summaries
    # A) Overall total (all years)
    overall_total = Offerings.objects.aggregate(sum=Sum("amount"))["sum"] or 0

    # B) total offerings in the current year
    total_current_year = (
        Offerings.objects.filter(date_given__year=current_year)
        .aggregate(sum=Sum("amount"))["sum"]
        or 0
    )

    # C) total offerings in the current month
    this_month = now().month
    total_current_month = (
        Offerings.objects.filter(date_given__year=current_year, date_given__month=this_month)
        .aggregate(sum=Sum("amount"))["sum"]
        or 0
    )

    # D) total offerings in the current week
    this_week_num = now().isocalendar()[1]  # 1–52
    total_current_week = (
        Offerings.objects.annotate(
            week=ExtractWeek("date_given"),
            annotated_year=ExtractYear("date_given"),
        )
        .filter(week=this_week_num, annotated_year=current_year)
        .aggregate(sum=Sum("amount"))["sum"]
        or 0
    )

    # E) total offerings of the last day (the most recent date in the DB)
    last_day_qs = Offerings.objects.order_by("-date_given").values("date_given").first()
    if last_day_qs:
        last_day_date = last_day_qs["date_given"]
        total_last_day = (
            Offerings.objects.filter(date_given=last_day_date)
            .aggregate(sum=Sum("amount"))["sum"]
            or 0
        )
    else:
        last_day_date = None
        total_last_day = 0

    # 3) Advice / Explanation
    advice_text = (
        "Offerings remain a vital source of church funding. "
        "Monitoring these patterns can help in financial planning."
    )

    # 4) Chart analysis text
    if not labels:
        line_analysis = "No offering data available for the current year."
        highest_info = "N/A"
        lowest_info = "N/A"
    else:
        line_analysis = (
            f"In {current_year}, the mass with the highest total offerings is "
            f"{highest_mass_name} ({highest_amount} TZS), and the lowest is "
            f"{lowest_mass_name} ({lowest_amount} TZS)."
        )
        highest_info = f"{highest_mass_name} ({highest_amount} TZS)"
        lowest_info = f"{lowest_mass_name} ({lowest_amount} TZS)"

    # 5) Create a SINGLE descriptive text combining all summary info
    last_day_str = str(last_day_date) if last_day_date else "N/A"
    long_description = (
        f"Overall, the total offerings across all recorded years amount to {overall_total} TZS. "
        f"So far this year ({current_year}), the church has collected {total_current_year} TZS. "
        f"In the current month, the total is {total_current_month} TZS. "
        f"This current week alone has accumulated {total_current_week} TZS in offerings. "
        f"On the most recent recorded day ({last_day_str}), the total was {total_last_day} TZS. "
        f"From the analysis of masses in {current_year}, the highest total offerings come from "
        f"{highest_mass_name} with {highest_amount} TZS, while the lowest are from {lowest_mass_name} "
        f"with {lowest_amount} TZS. {advice_text}"
    )

    # 6) Return everything as JSON for Chart.js and partial
    return json.dumps({
        # Data for the line chart
        "labels": labels,
        "data": data,
        "line_analysis": line_analysis,

        # Single descriptive text
        "offerings_description": long_description,
    })

import json
from django.db.models import Sum
from django.utils.timezone import now
from finance.models import FacilityRenting

def get_facility_renting_analysis():
    """
    Analyzes FacilityRenting in the current year (of the 'year' field).
    - For each property that has a renting record in the current year, sum amounts.
    - Identify property with the highest total renting, and property with the smallest total.
    - Compute overall total across ALL years, and per-property amounts for the current year.
    - Return data for a bar chart, plus a detailed text summary.
    """

    # 1) Identify the current system year from 'now()'
    current_year = now().year

    # 2) Filter facility renting by property where the facility's 'year__year' matches current_year
    #    i.e. the 'year' field is the current "Year" object whose year == current_year
    current_year_renting_qs = (
        FacilityRenting.objects
        .filter(year__year=current_year)
        .values("property_rented__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")  # Sort by highest amount first
    )

    labels = []
    data = []
    renting_details = []  # Store property-wise renting details

    highest_prop_name = None
    highest_amount = 0
    lowest_prop_name = None
    lowest_amount = None

    # Fill chart data only for properties with rentals in the current year
    for entry in current_year_renting_qs:
        prop_name = entry["property_rented__name"]
        total_amt = entry["total"] or 0
        labels.append(prop_name)
        data.append(float(total_amt))

        # Track highest renting property
        if total_amt > highest_amount:
            highest_amount = total_amt
            highest_prop_name = prop_name

        # Track lowest renting property
        if lowest_amount is None or total_amt < lowest_amount:
            lowest_amount = total_amt
            lowest_prop_name = prop_name

        # Store details
        renting_details.append(f"{prop_name}: {total_amt:,.2f} TZS")

    # 3) Compute overall total renting across ALL years
    overall_total = FacilityRenting.objects.aggregate(s=Sum("amount"))["s"] or 0

    # 4) Build a **detailed description**
    if not labels:
        description = (
            f"No facility renting records found for the current year ({current_year}). "
            f"So far, no property has been rented in {current_year}."
        )
    else:
        description = (
            f"In the current year ({current_year}), church properties have generated rental income as follows: "
            f"{', '.join(renting_details)}. The highest renting property is **{highest_prop_name}** "
            f"with **{highest_amount:,.2f} TZS**, while the lowest is **{lowest_prop_name}** "
            f"with **{lowest_amount:,.2f} TZS**. Across all recorded years, "
            f"the total revenue from facility renting amounts to **{overall_total:,.2f} TZS**."
        )

    # 5) Return JSON data for the **bar chart** plus a **detailed description**
    return json.dumps({
        "labels": labels,  # List of property names
        "data": data,  # Corresponding rental sums
        "description": description  # Full textual breakdown
    })


import json
from django.db.models import Sum
from django.utils.timezone import now
from finance.models import DonationItemFund

def get_special_contribution_funds_analysis():
    """
    Analyzes DonationItemFund records for the current year (of the 'year' field).
    - Groups by SpecialContribution (contribution_type__name).
    - Sums the 'amount'.
    - Returns data for a Radar chart, plus a descriptive text summary:
      * Overall total for the current year (all special contributions).
      * Per-special-contribution totals for the current year.
    """

    current_year = now().year  # From system's timezone

    # 1) Filter DonationItemFund by 'year__year == current_year'
    qs = (
        DonationItemFund.objects
        .filter(year__year=current_year)
        .values("contribution_type__name")
        .annotate(total=Sum("amount"))
        .order_by("contribution_type__name")
    )

    labels = []
    data = []
    overall_total = 0
    details_list = []

    # 2) Build lists for Radar chart + track sums
    for entry in qs:
        contrib_name = entry["contribution_type__name"]
        amt = entry["total"] or 0

        labels.append(contrib_name)
        data.append(float(amt))
        overall_total += amt

        # Store a line like "Church Renovation Fund: 500,000 TZS"
        details_list.append(f"{contrib_name}: {amt:,.2f} TZS")

    # 3) Construct a descriptive text summary
    if not labels:
        description = (
            f"No DonationItemFund data found for the current year ({current_year}). "
            f"Likely no special contributions were recorded yet this year."
        )
    else:
        # Summaries about each special contribution + overall total
        description = (
            f"For the current year ({current_year}), the total DonationItemFund across all Special Contributions "
            f"is {overall_total:,.2f} TZS. Below is a breakdown per contribution: "
            + "; ".join(details_list)
            + "."
        )

    # 4) Return JSON data for the Radar chart plus the description
    return json.dumps({
        "labels": labels,       # e.g. ["Renovation Fund", "Charity Drive", "Youth Org Fund"]
        "data": data,           # e.g. [1200000, 500000, 250000, ...]
        "description": description
    })
