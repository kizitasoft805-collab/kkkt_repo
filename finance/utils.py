from .models import Offerings, SpecialContribution, DonationItemFund
from django.utils.timezone import now


import json
from .models import Offerings


def get_offerings_data():
    """
    Fetches total offerings per date for the current year and returns JSON data
    for visualization with JavaScript.
    """
    current_year = now().year

    # Query the total amount collected per date in the current year
    offerings_data = Offerings.objects.filter(date_given__year=current_year).values(
        'date_given'
    ).annotate(total_amount=models.Sum('amount')).order_by('date_given')

    if not offerings_data:
        return json.dumps({"labels": [], "data": [], "highest_date": None, "lowest_date": None, "analysis": "No offerings data available for the current year."})

    # Convert QuerySet to dictionary
    offerings_list = list(offerings_data)

    # Extract labels (Dates) and values (Total Offerings)
    labels = [item['date_given'].strftime('%Y-%m-%d') for item in offerings_list]
    data = [float(item['total_amount']) for item in offerings_list]

    # Identify highest and lowest offerings
    highest_index = data.index(max(data))
    lowest_index = data.index(min(data))

    highest_date = labels[highest_index]
    highest_amount = data[highest_index]

    lowest_date = labels[lowest_index]
    lowest_amount = data[lowest_index]

    # Generate analysis
    analysis = (
        f"The highest offering was on **{highest_date}**, with a total amount of **TZS {highest_amount:,.2f}**. "
        f"The lowest offering was on **{lowest_date}**, with **TZS {lowest_amount:,.2f}**. "
        f"This analysis helps track offering trends and financial growth in the church."
    )

    return json.dumps({"labels": labels, "data": data, "highest_date": highest_date, "lowest_date": lowest_date, "analysis": analysis})


import json
from django.db.models import Sum
from django.utils.timezone import now
from finance.models import DonationItemFund

def get_special_contributions_data():
    """
    Fetches total funds per Special Contribution for the current year and
    returns JSON data for visualization with Chart.js.
    """
    # Get the current year
    current_year = now().year
    
    # Query all DonationItemFund for the current year
    item_funds = DonationItemFund.objects.filter(year__is_current=True)

    if not item_funds.exists():
        return json.dumps({
            "labels": [],
            "data": [],
            "highest_contribution": None,
            "lowest_contribution": None,
            "analysis": "No Special Contributions data available for the current year."
        })

    # Group and sum by SpecialContribution name
    grouped_data = (
        item_funds
        .values('contribution_type__name')
        .annotate(total_amount=Sum('amount'))
        .order_by('-total_amount')
    )

    # Convert QuerySet to a list of dicts
    grouped_list = list(grouped_data)

    # Extract labels (contribution names) and values (total amounts)
    labels = [item['contribution_type__name'] for item in grouped_list]
    data = [float(item['total_amount']) for item in grouped_list]

    # Identify highest and lowest
    highest_index = data.index(max(data))
    lowest_index = data.index(min(data))

    highest_contribution = labels[highest_index]
    highest_amount = data[highest_index]

    lowest_contribution = labels[lowest_index]
    lowest_amount = data[lowest_index]

    # Generate an analysis message
    analysis = (
        f"The highest special contribution is **{highest_contribution}** at "
        f"**TZS {highest_amount:,.2f}**, while the lowest is **{lowest_contribution}** with "
        f"**TZS {lowest_amount:,.2f}**. This helps the church understand the distribution of special contributions."
    )

    # Return as JSON
    return json.dumps({
        "labels": labels,
        "data": data,
        "highest_contribution": highest_contribution,
        "lowest_contribution": lowest_contribution,
        "analysis": analysis
    })

# finance/utils.py

from django.utils.timezone import now
from finance.models import FacilityRenting
import json
from django.db import models

def get_asset_finance_data():
    """
    Retrieves total financial data for each church asset in the current year.
    Returns JSON data for frontend visualization.
    """
    current_year = now().year

    # Fetch total rental income per asset in the current year
    assets_data = FacilityRenting.objects.filter(year__is_current=True).values('property_rented__name').annotate(total_income=models.Sum('amount'))

    # If no data exists, return an empty dataset
    if not assets_data:
        return json.dumps({"labels": [], "data": [], "highest_asset": None, "lowest_asset": None, "analysis": "No asset financial data available for the current year."})

    # Convert QuerySet to dictionary
    asset_finance = list(assets_data)

    # Extract labels (Asset Names) and values (Total Income)
    labels = [item['property_rented__name'] for item in asset_finance]
    data = [float(item['total_income']) for item in asset_finance]

    # Determine highest and lowest asset values
    highest_asset_index = data.index(max(data))
    lowest_asset_index = data.index(min(data))
    
    highest_asset = labels[highest_asset_index]
    highest_income = data[highest_asset_index]
    
    lowest_asset = labels[lowest_asset_index]
    lowest_income = data[lowest_asset_index]

    # Generate Analysis
    analysis = (
        f"The asset with the highest financial contribution is **{highest_asset}** with **TZS {highest_income:,.2f}**. "
        f"The asset with the lowest financial contribution is **{lowest_asset}** with **TZS {lowest_income:,.2f}**. "
        f"This analysis helps in decision-making regarding property utilization and rental strategy."
    )

    return json.dumps({"labels": labels, "data": data, "highest_asset": highest_asset, "lowest_asset": lowest_asset, "analysis": analysis})
