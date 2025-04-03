import json
from django.db.models import Count
from properties.models import ChurchAsset

def get_properties_radar_analysis():
    """
    Fetches the count of Good, Needs Repair, Damaged, Sold, and Donated assets.
    Returns JSON data for visualization in a Radar Chart.
    """

    # Get total number of church assets
    total_assets = ChurchAsset.objects.count()

    # Get property counts by status
    statuses = ["Good", "Needs Repair", "Damaged", "Sold", "Donated"]
    asset_counts = {status: ChurchAsset.objects.filter(status=status).count() for status in statuses}

    # Data Labels and Values
    labels = list(asset_counts.keys())
    data = list(asset_counts.values())

    # Generate an analysis message
    analysis = (
        f"The church currently has a total of **{total_assets}** registered assets. "
        f"Among them, **{asset_counts['Good']}** are in good condition, **{asset_counts['Needs Repair']}** require repairs, "
        f"**{asset_counts['Damaged']}** are damaged, **{asset_counts['Sold']}** have been sold, and **{asset_counts['Donated']}** have been donated."
    )

    # Return JSON data for Chart.js
    return json.dumps({
        "labels": labels,
        "data": data,
        "total_assets": total_assets,
        "analysis": analysis
    })
