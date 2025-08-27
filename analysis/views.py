# analysis/views.py or wherever your main analysis view resides
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

# Import your existing analysis functions with corrected names, removing get_movements_analysis
from analysis.utils import (
    get_outstations_analysis,  # Updated from get_zones_analysis
    get_cells_analysis,       # Updated from get_communities_analysis
    get_active_inactive_analysis,
    get_leaders_active_inactive_analysis,
    get_offerings_analysis,
    get_facility_renting_analysis,
    get_special_contribution_funds_analysis
)

def is_admin_or_superuser(user):
    """
    Restrict access to Admins or Superusers only.
    """
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required(login_url='login')
@user_passes_test(is_admin_or_superuser, login_url='login')
def general_analysis_view(request):
    """
    This view collects all analysis data and renders them on 'analysis/general_analysis.html'.
    The data includes:
      1. Zones Analysis (Line Chart)
      2. Communities Analysis (Bar Chart)
      3. Movements Analysis (Combined)
      4. Active vs. Inactive Members (Pie)
      5. Leaders Active vs. Inactive (Doughnut)
      6. Offerings Analysis (Line chart + Summaries for current year)
      7. Tithes Monthly Analysis (Combined for current year)
      8. Facility Renting Analysis (Bar chart for current year)
      9. Special Contribution Funds Analysis (Radar chart for current year)
    """

    # 1. Zones Analysis (Line)
    zones_data_json = get_outstations_analysis()

    # 2. Communities Analysis (Bar)
    communities_data_json = get_cells_analysis()

    # 4. Active vs Inactive Members (Pie)
    active_inactive_data_json = get_active_inactive_analysis()

    # 5. Leaders Active vs Inactive (Doughnut)
    leaders_active_inactive_data_json = get_leaders_active_inactive_analysis()

    # 6. Offerings (Line chart + Summaries for current year)
    offerings_data_json = get_offerings_analysis()


    # 8. Facility Renting Analysis (Bar chart for current year)
    facility_data_json = get_facility_renting_analysis()

    # 9. Special Contribution Funds Analysis (Radar chart for current year)
    donation_fund_data_json = get_special_contribution_funds_analysis()

    return render(
        request,
        'analysis/general_analysis.html',
        {
            'zones_data': zones_data_json,
            'communities_data': communities_data_json,
            'active_inactive_data': active_inactive_data_json,
            'leaders_active_inactive_data': leaders_active_inactive_data_json,
            'offerings_data': offerings_data_json,
            'facility_data': facility_data_json,
            'donation_fund_data': donation_fund_data_json,  # <-- pass radar chart data to template
        }
    )

# analysis/views.py or wherever your main analysis view resides
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

# Import your existing analysis functions with corrected names, removing get_movements_analysis
from analysis.utils import (
    get_outstations_analysis,  # Updated from get_zones_analysis
    get_cells_analysis,       # Updated from get_communities_analysis
    get_active_inactive_analysis,
    get_leaders_active_inactive_analysis,
    get_offerings_analysis,
    get_facility_renting_analysis,
    get_special_contribution_funds_analysis
)

@login_required(login_url='login')
def secretary_general_analysis_view(request):
    """
    This view collects all analysis data and renders them on 'analysis/general_analysis.html'.
    The data includes:
      1. Zones Analysis (Line Chart)
      2. Communities Analysis (Bar Chart)
      3. Movements Analysis (Combined)
      4. Active vs. Inactive Members (Pie)
      5. Leaders Active vs. Inactive (Doughnut)
      6. Offerings Analysis (Line chart + Summaries for current year)
      7. Tithes Monthly Analysis (Combined for current year)
      8. Facility Renting Analysis (Bar chart for current year)
      9. Special Contribution Funds Analysis (Radar chart for current year)
    """

    # 1. Zones Analysis (Line)
    zones_data_json = get_outstations_analysis()

    # 2. Communities Analysis (Bar)
    communities_data_json = get_cells_analysis()

    # 4. Active vs Inactive Members (Pie)
    active_inactive_data_json = get_active_inactive_analysis()

    # 5. Leaders Active vs Inactive (Doughnut)
    leaders_active_inactive_data_json = get_leaders_active_inactive_analysis()

    # 6. Offerings (Line chart + Summaries for current year)
    offerings_data_json = get_offerings_analysis()

    # 8. Facility Renting Analysis (Bar chart for current year)
    facility_data_json = get_facility_renting_analysis()

    # 9. Special Contribution Funds Analysis (Radar chart for current year)
    donation_fund_data_json = get_special_contribution_funds_analysis()

    return render(
        request,
        'analysis/secretary_general_analysis.html',
        {
            'zones_data': zones_data_json,
            'communities_data': communities_data_json,
            'active_inactive_data': active_inactive_data_json,
            'leaders_active_inactive_data': leaders_active_inactive_data_json,
            'offerings_data': offerings_data_json,
            'facility_data': facility_data_json,
            'donation_fund_data': donation_fund_data_json,  # <-- pass radar chart data to template
        }
    )

# analysis/views.py or wherever your main analysis view resides
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

# Import your existing analysis functions with corrected names, removing get_movements_analysis
from analysis.utils import (
    get_outstations_analysis,  # Updated from get_zones_analysis
    get_cells_analysis,       # Updated from get_communities_analysis
    get_active_inactive_analysis,
    get_leaders_active_inactive_analysis,
    get_offerings_analysis,
    get_facility_renting_analysis,
    get_special_contribution_funds_analysis
)

@login_required(login_url='login')
def accountant_general_analysis_view(request):
    """
    This view collects all analysis data and renders them on 'analysis/general_analysis.html'.
    The data includes:
      1. Zones Analysis (Line Chart)
      2. Communities Analysis (Bar Chart)
      3. Movements Analysis (Combined)
      4. Active vs. Inactive Members (Pie)
      5. Leaders Active vs. Inactive (Doughnut)
      6. Offerings Analysis (Line chart + Summaries for current year)
      7. Tithes Monthly Analysis (Combined for current year)
      8. Facility Renting Analysis (Bar chart for current year)
      9. Special Contribution Funds Analysis (Radar chart for current year)
    """

    # 1. Zones Analysis (Line)
    zones_data_json = get_outstations_analysis()

    # 2. Communities Analysis (Bar)
    communities_data_json = get_cells_analysis()

    # 4. Active vs Inactive Members (Pie)
    active_inactive_data_json = get_active_inactive_analysis()

    # 5. Leaders Active vs Inactive (Doughnut)
    leaders_active_inactive_data_json = get_leaders_active_inactive_analysis()

    # 6. Offerings (Line chart + Summaries for current year)
    offerings_data_json = get_offerings_analysis()

    # 8. Facility Renting Analysis (Bar chart for current year)
    facility_data_json = get_facility_renting_analysis()

    # 9. Special Contribution Funds Analysis (Radar chart for current year)
    donation_fund_data_json = get_special_contribution_funds_analysis()

    return render(
        request,
        'analysis/accountant_general_analysis.html',
        {
            'zones_data': zones_data_json,
            'communities_data': communities_data_json,
            'active_inactive_data': active_inactive_data_json,
            'leaders_active_inactive_data': leaders_active_inactive_data_json,
            'offerings_data': offerings_data_json,
            'facility_data': facility_data_json,
            'donation_fund_data': donation_fund_data_json,  # <-- pass radar chart data to template
        }
    )