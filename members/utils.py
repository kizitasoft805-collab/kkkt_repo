import json
from django.db.models import Count
from members.models import ChurchMember
from settings.models import Cell, OutStation  # Updated imports

def get_membership_distribution_analysis():
    """
    Fetches the count of members per cell and outstation.
    Returns JSON data for visualization.
    """

    # Get total members
    total_members = ChurchMember.objects.count()
    total_active_members = ChurchMember.objects.filter(status="Active").count()
    total_inactive_members = ChurchMember.objects.filter(status="Inactive").count()

    # Get members count by cell
    members_by_cell = (
        ChurchMember.objects.values("cell__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Get members count by outstation (changed from zone)
    members_by_outstation = (
        ChurchMember.objects.values("cell__outstation__name")  # Updated from cell__zone__name
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Filter out cells and outstations with no members
    cell_labels = [entry["cell__name"] for entry in members_by_cell if entry["cell__name"]]
    cell_counts = [entry["count"] for entry in members_by_cell if entry["cell__name"]]

    outstation_labels = [entry["cell__outstation__name"] for entry in members_by_outstation if entry["cell__outstation__name"]]  # Updated from zone_labels
    outstation_counts = [entry["count"] for entry in members_by_outstation if entry["cell__outstation__name"]]  # Updated from zone_counts

    # Calculate percentages for cells and outstations
    cell_percentages = [
        round((count / total_members) * 100, 2) if total_members > 0 else 0
        for count in cell_counts
    ]

    outstation_percentages = [  # Updated from zone_percentages
        round((count / total_members) * 100, 2) if total_members > 0 else 0
        for count in outstation_counts
    ]

    # Generate an analysis message
    analysis = (
        f"The church has a total of **{total_members}** members, with **{total_active_members}** active and **{total_inactive_members}** inactive. "
        f"Members are distributed across various **cells and outstations**, with the highest concentration in some cells."
    )

    # Return JSON data for Chart.js
    return json.dumps({
        "cell_labels": cell_labels,
        "cell_data": cell_percentages,
        "outstation_labels": outstation_labels,  # Updated from zone_labels
        "outstation_data": outstation_percentages,  # Updated from zone_data
        "total_members": total_members,
        "total_active_members": total_active_members,
        "total_inactive_members": total_inactive_members,
        "analysis": analysis
    })