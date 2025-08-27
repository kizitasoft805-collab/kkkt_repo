import json
from django.db.models import Count
from leaders.models import Leader
from settings.models import Cell, OutStation

def get_leaders_distribution_trend():
    """
    Fetches the count of leaders per cell and per outstation.
    Returns JSON data for visualization with Chart.js (Two-Line Chart).
    Also determines the cells and outstations with the highest and lowest number of leaders.
    """
    # Get total leaders per cell
    leaders_by_cell = (
        Leader.objects.values("church_member__cell__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Get total leaders per outstation
    leaders_by_outstation = (
        Leader.objects.values("church_member__cell__outstation__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Handle unassigned leaders
    unassigned_count = Leader.objects.filter(church_member__cell__isnull=True).count()

    # Process cell data
    cell_labels = [entry["church_member__cell__name"] for entry in leaders_by_cell if entry["church_member__cell__name"]]
    cell_counts = [entry["count"] for entry in leaders_by_cell if entry["church_member__cell__name"]]
    if unassigned_count > 0:
        cell_labels.append("Unassigned")
        cell_counts.append(unassigned_count)

    # Process outstation data
    outstation_labels = [entry["church_member__cell__outstation__name"] for entry in leaders_by_outstation if entry["church_member__cell__outstation__name"]]
    outstation_counts = [entry["count"] for entry in leaders_by_outstation if entry["church_member__cell__outstation__name"]]
    if unassigned_count > 0:
        outstation_labels.append("Unassigned")
        outstation_counts.append(unassigned_count)

    # Fallback if no data
    if not cell_labels:
        cell_labels = ["No Cells"]
        cell_counts = [0]
    if not outstation_labels:
        outstation_labels = ["No Outstations"]
        outstation_counts = [0]

    # Identify the cells with the most and least leaders
    largest_cell = cell_labels[0] if cell_labels and cell_counts[0] > 0 else "N/A"
    smallest_cell = cell_labels[-1] if cell_labels and cell_counts[-1] > 0 else "N/A"

    # Identify the outstations with the most and least leaders
    largest_outstation = outstation_labels[0] if outstation_labels and outstation_counts[0] > 0 else "N/A"
    smallest_outstation = outstation_labels[-1] if outstation_labels and outstation_counts[-1] > 0 else "N/A"

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
        "cell_labels": cell_labels,
        "cell_data": cell_counts,
        "outstation_labels": outstation_labels,
        "outstation_data": outstation_counts,
        "largest_cell": largest_cell,
        "smallest_cell": smallest_cell,
        "largest_outstation": largest_outstation,
        "smallest_outstation": smallest_outstation,
        "analysis": analysis
    })