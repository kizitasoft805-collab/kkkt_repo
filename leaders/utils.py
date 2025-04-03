import json
from django.db.models import Count
from leaders.models import Leader
from settings.models import Cell, OutStation  # Updated imports

def get_leaders_distribution_trend():
    """
    Fetches the count of leaders per cell and per outstation.
    Returns JSON data for visualization with Chart.js (Two-Line Chart).
    Also determines the cells and outstations with the highest and lowest number of leaders.
    """

    # Get total leaders per cell (updated from community)
    leaders_by_cell = (
        Leader.objects.values("church_member__cell__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Get total leaders per outstation (updated from zone)
    leaders_by_outstation = (
        Leader.objects.values("church_member__cell__outstation__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Filter out cells and outstations with no leaders
    cell_labels = [entry["church_member__cell__name"] for entry in leaders_by_cell if entry["church_member__cell__name"]]
    cell_counts = [entry["count"] for entry in leaders_by_cell if entry["church_member__cell__name"]]

    outstation_labels = [entry["church_member__cell__outstation__name"] for entry in leaders_by_outstation if entry["church_member__cell__outstation__name"]]
    outstation_counts = [entry["count"] for entry in leaders_by_outstation if entry["church_member__cell__outstation__name"]]

    # Identify the cells with the most and least leaders
    largest_cell = cell_labels[0] if cell_labels else "N/A"
    smallest_cell = cell_labels[-1] if cell_labels else "N/A"

    # Identify the outstations with the most and least leaders
    largest_outstation = outstation_labels[0] if outstation_labels else "N/A"
    smallest_outstation = outstation_labels[-1] if outstation_labels else "N/A"

    # Generate an analysis message
    analysis = (
        f"The church has leaders distributed across **various cells and outstations**. "
        f"The highest number of leaders is observed in **{largest_cell}**, "
        f"while **{smallest_cell}** has the fewest leaders. "
        f"Similarly, the outstation with the most leaders is **{largest_outstation}**, "
        f"while **{smallest_outstation}** has the least leaders."
    )

    # Return JSON data for Chart.js
    return json.dumps({
        "cell_labels": cell_labels,  # Updated from community_labels
        "cell_data": cell_counts,    # Updated from community_data
        "outstation_labels": outstation_labels,  # Updated from zone_labels
        "outstation_data": outstation_counts,    # Updated from zone_data
        "largest_cell": largest_cell,            # Updated from largest_community
        "smallest_cell": smallest_cell,          # Updated from smallest_community
        "largest_outstation": largest_outstation,  # Updated from largest_zone
        "smallest_outstation": smallest_outstation,  # Updated from smallest_zone
        "analysis": analysis
    })