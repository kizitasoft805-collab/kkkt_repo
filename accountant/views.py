from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .decorators import parish_treasurer_required

# finance/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from finance.utils import (
    get_offerings_data,
    get_special_contributions_data,  # <-- NEW
    get_asset_finance_data
)

@login_required
@parish_treasurer_required
def accountant_finance_home(request):
    """
    View to display the finance dashboard with Offerings, Tithes,
    Special Contributions, and Church Assets data.
    """
    # Offerings Data (Chart.js)
    offerings_data = get_offerings_data()

    # Tithes Data (Chart.js)

    # Special Contributions Data (Chart.js)
    special_contributions_data = get_special_contributions_data()

    # Church Assets Data (Chart.js)
    asset_finance_data = get_asset_finance_data()

    context = {
        'offerings_data': offerings_data,
        'special_contributions_data': special_contributions_data,  # Pass to template
        'asset_finance_data': asset_finance_data,
    }
    return render(request, 'accountant/finance/finance_home.html', context)

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib import messages
from finance.models import Offerings
from finance.forms import OfferingsForm
from .mixins import ParishTreasurerRequiredMixin  # Import the custom mixin


class AccountantOfferingsCreateView(LoginRequiredMixin, ParishTreasurerRequiredMixin, CreateView):
    """
    View to create a new offering.
    Only accessible by Church Members who are Leaders with the occupation 'Parish Treasurer'.
    Redirects unauthorized users to the login page.
    """
    model = Offerings
    form_class = OfferingsForm
    template_name = 'accountant/finance/offering_form.html'
    success_url = reverse_lazy('accountant_offerings_list')  # Redirect after success

    def form_valid(self, form):
        form.instance.created_by = self.request.user

        # Ensure offering is assigned to the current year
        from settings.models import Year
        current_year = Year.objects.filter(is_current=True).first()
        if current_year:
            form.instance.year = current_year

        response = super().form_valid(form)
        messages.success(self.request, "✅ Offering record created successfully.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "❌ Error: Please check the form fields.")
        return super().form_invalid(form)

from django.utils.timezone import now
from django.utils.timesince import timesince
from django.views.generic import ListView
from django.db.models import Sum
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from finance.models import Offerings
from settings.models import Year
from members.models import ChurchMember

class AccountantOfferingsListView(LoginRequiredMixin, ParishTreasurerRequiredMixin, ListView):
    """
    View to list all offerings from all years.
    Only accessible by Admins and Superusers.
    """
    model = Offerings
    template_name = "accountant/finance/offerings_list.html"
    context_object_name = "offerings"
    ordering = ['-date_given']  # Display newest offerings first

    def get_context_data(self, **kwargs):
        """
        Add additional data to the template context.
        """
        context = super().get_context_data(**kwargs)

        # Retrieve all offerings
        offerings_qs = Offerings.objects.all().order_by('-date_given')
        context["offerings"] = offerings_qs

        # Retrieve all years
        context["years"] = Year.objects.all()

        # Retrieve all active church members for collected_by filter
        context["collected_by_members"] = ChurchMember.objects.filter(status="Active")

        # Retrieve all active church leaders for recorded_by filter
        context["recorded_by_leaders"] = ChurchMember.objects.filter(leader__isnull=False, status="Active")

        # Calculate total amount
        context["total_offerings"] = offerings_qs.aggregate(Sum('amount'))['amount__sum'] or 0

        # Annotate offerings with time since created and updated
        for offering in context["offerings"]:
            offering.time_since_created = timesince(offering.date_created, now())
            offering.time_since_updated = timesince(offering.date_updated, now())

        return context

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from django.contrib import messages
from django.utils.timezone import now
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from finance.models import Offerings
from finance.forms import OfferingsForm

class AccountantOfferingsUpdateView(LoginRequiredMixin, ParishTreasurerRequiredMixin, UpdateView):
    """
    View to update an existing offering record.
    Only accessible by Admins and Superusers.
    """
    model = Offerings
    form_class = OfferingsForm
    template_name = "accountant/finance/offering_form.html"

    def form_valid(self, form):
        """
        Logic before saving the updated offering.
        """
        offering = form.save(commit=False)
        offering.date_updated = now()  # Update the timestamp
        offering.save()
        messages.success(self.request, "✅ Offering record updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        """
        Redirect to the list of offerings after updating.
        """
        return reverse_lazy('accountant_offerings_list')

from django.urls import reverse_lazy
from django.views.generic import DeleteView
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from finance.models import Offerings

class AccountantOfferingsDeleteView(LoginRequiredMixin,ParishTreasurerRequiredMixin, DeleteView):
    """
    View to delete an existing offering record.
    Only accessible by Admins and Superusers.
    """
    model = Offerings
    template_name = "accountant/finance/offerings_confirm_delete.html"
    success_url = reverse_lazy('accountant_offerings_list')  # Redirect after deletion

    def delete(self, request, *args, **kwargs):
        """
        Override delete method to add a success message.
        """
        messages.success(request, "✅ Offering record deleted successfully.")
        return super().delete(request, *args, **kwargs)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test


@login_required
@parish_treasurer_required
def accountant_create_multiple_tithes(request):
    """
    View to create multiple tithes at once using formsets.
    Only accessible to Admins and Superusers.
    """
    print("🚀 Entered create_multiple_tithes view")

    if request.method == 'POST':
        print("📥 Handling POST request...")
        formset = TitheFormSet(request.POST)
        print("✅ Formset initialized with POST data")

        if formset.is_valid():
            print("🎯 Formset is valid. Saving data...")
            formset.save()
            messages.success(request, "✅ Tithes successfully created!")
            print("💾 Tithes saved successfully!")
            return redirect('accountant_tithe_list')  # Redirect after saving
        else:
            print("❌ Formset validation failed")
            print("📝 Formset errors:", formset.errors)

    else:
        print("📄 Handling GET request...")
        formset = TitheFormSet(queryset=Tithe.objects.none())
        print("✅ Empty formset initialized for new entries")

    return render(request, 'accountant/finance/create_multiple_tithes.html', {'formset': formset})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

@login_required
@parish_treasurer_required
def accountant_create_or_update_tithe(request, tithe_id=None):
    """
    View to create or update a tithe.
    Only accessible to Admins and Superusers.
    If tithe_id is provided, the view will update an existing tithe.
    Otherwise, it will create a new tithe.
    """
    if tithe_id:
        tithe = get_object_or_404(Tithe, id=tithe_id)
        action = "Update Tithe"
    else:
        tithe = None
        action = "Create Tithe"

    if request.method == 'POST':
        form = TitheForm(request.POST, instance=tithe)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Tithe successfully {'updated' if tithe_id else 'created'}!")
            return redirect('accountant_tithe_list')  # Redirect to the tithe list view after saving
        else:
            messages.error(request, "❌ Please correct the errors in the form.")
    else:
        form = TitheForm(instance=tithe)

    return render(request, 'accountant/finance/create_or_update_tithe.html', {
        'form': form,
        'action': action,
        'tithe': tithe,
    })


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from settings.models import Year

# 🔍 View to List All Tithes
@login_required
@parish_treasurer_required
def accountant_tithe_list(request):
    """
    View to display all tithes, accessible only to Admins and Superusers.
    """
    tithes = Tithe.objects.all().order_by('-date_given')
    years = Year.objects.all().order_by('-year')  # Get all years

    return render(request, 'accountant/finance/tithe_list.html', {
        'tithes': tithes,
        'years': years,
    })

# ❌ View to Delete a Specific Tithe
@login_required
@parish_treasurer_required
def accountant_delete_tithe(request, tithe_id):
    """
    View to delete a specific tithe, accessible only to Admins and Superusers.
    """
    tithe = get_object_or_404(Tithe, id=tithe_id)

    if request.method == 'POST':
        tithe.delete()
        messages.success(request, "✅ Tithe successfully deleted!")
        return redirect('accountant_tithe_list')  # Redirect to the tithe list after deletion
    else:
        messages.warning(request, "⚠️ Are you sure you want to delete this tithe?")

    return render(request, 'accountant/finance/delete_tithe.html', {'tithe': tithe})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from finance.models import FacilityRenting
from finance.forms import FacilityRentingForm

# 🏠 View to Create a New Facility Renting
@login_required
@parish_treasurer_required
def accountant_facility_renting_create(request):
    """
    View for creating a new facility renting, accessible only to Admins and Superusers.
    """
    if request.method == 'POST':
        form = FacilityRentingForm(request.POST)
        if form.is_valid():
            renting = form.save(commit=False)
            renting.save()
            messages.success(request, '✅ Facility renting record created successfully.')
            return redirect('accountant_facility_renting_list')
        else:
            messages.error(request, '❌ Failed to create record. Please check the form fields.')
    else:
        form = FacilityRentingForm()

    context = {
        'form': form,
        'title': 'Create Facility Renting',
        'submit_text': 'Create Record'
    }
    return render(request, 'accountant/finance/facility_renting_form.html', context)

# 🔄 View to Update an Existing Facility Renting
@login_required
@parish_treasurer_required
def accountant_facility_renting_update(request, pk):
    """
    View for updating an existing facility renting, accessible only to Admins and Superusers.
    """
    renting = get_object_or_404(FacilityRenting, pk=pk)

    if request.method == 'POST':
        form = FacilityRentingForm(request.POST, instance=renting)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Facility renting record updated successfully.')
            return redirect('accountant_facility_renting_list')
        else:
            messages.error(request, '❌ Failed to update record. Please check the form fields.')
    else:
        form = FacilityRentingForm(instance=renting)

    context = {
        'form': form,
        'title': 'Update Facility Renting',
        'submit_text': 'Update Record',
        'renting': renting
    }
    return render(request, 'accountant/finance/facility_renting_form.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from properties.models import ChurchAsset
from settings.models import Year
from finance.models import FacilityRenting

# 📋 View to List All Facility Rentings
@login_required
@parish_treasurer_required
def accountant_facility_renting_list(request):
    """
    View to display all facility renting records, accessible only to Admins and Superusers.
    """
    rentings = FacilityRenting.objects.all().order_by('-date_rented')
    years = Year.objects.all().order_by('-year')
    properties = ChurchAsset.objects.filter(asset_type__in=['Building', 'Electronics', 'Equipment', 'Vehicle'])

    context = {
        'rentings': rentings,
        'years': years,
        'properties': properties,
        'title': 'Facility Rentings'
    }
    return render(request, 'accountant/finance/facility_renting_list.html', context)

# 🗑️ View to Delete a Facility Renting Record
@login_required
@parish_treasurer_required
def accountant_facility_renting_delete(request, pk):
    """
    View to delete a specific Facility Renting record, accessible only to Admins and Superusers.
    """
    renting = get_object_or_404(FacilityRenting, pk=pk)

    if request.method == "POST":
        renting.delete()
        messages.success(request, "✅ Facility renting deleted successfully!")
        return redirect('accountant_facility_renting_list')

    return render(request, 'accountant/finance/facility_renting_delete.html', {'renting': renting})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from finance.forms import SpecialContributionForm
from finance.models import SpecialContribution

# ➕ View to Add or Update Special Contributions
@login_required
@parish_treasurer_required
def accountant_special_contribution_form(request, pk=None):
    """
    View to create or update a special contribution.
    Only accessible to Admins and Superusers.
    """
    if pk:
        # 📝 Update Mode
        contribution = get_object_or_404(SpecialContribution, pk=pk)
        form = SpecialContributionForm(request.POST or None, instance=contribution)
        title = "✏️ Update Special Contribution"
        success_message = "✅ Special contribution updated successfully!"
    else:
        # ➕ Create Mode
        contribution = None
        form = SpecialContributionForm(request.POST or None)
        title = "➕ Add Special Contribution"
        success_message = "🎉 Special contribution added successfully!"

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, success_message)
        return redirect('accountant_special_contribution_list')

    return render(request, 'accountant/finance/special_contribution_form.html', {
        'form': form,
        'title': title,
        'is_update': pk is not None
    })

# 🗑️ View to Delete a Special Contribution
@login_required
@parish_treasurer_required
def accountant_special_contribution_delete(request, pk):
    """
    View to delete a special contribution.
    Only accessible to Admins and Superusers.
    """
    contribution = get_object_or_404(SpecialContribution, pk=pk)

    if request.method == 'POST':
        contribution.delete()
        messages.success(request, '🗑️ Special contribution deleted successfully!')
        return redirect('accountant_special_contribution_list')

    return render(request, 'accountant/finance/special_contribution_delete.html', {
        'contribution': contribution
    })


from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from finance.models import SpecialContribution

# 📋 View to List All Special Contributions
@login_required
@parish_treasurer_required
def accountant_special_contribution_list(request):
    """
    View to list all special contributions.
    Only accessible to Admins and Superusers.
    """
    contributions = SpecialContribution.objects.all().order_by('-date_created')
    
    return render(request, 'accountant/finance/special_contribution_list.html', {
        'contributions': contributions
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from finance.models import DonationItemFund, SpecialContribution
from finance.forms import DonationItemFundForm
from settings.models import Year

# 📝 View to Create or Update Donation Item Fund
@login_required
@parish_treasurer_required
def accountant_donation_item_fund_form(request, contribution_id, pk=None):
    """
    View to create or update a donation item fund.
    Only accessible to Admins and Superusers.
    """
    contribution = get_object_or_404(SpecialContribution, pk=contribution_id)
    instance = get_object_or_404(DonationItemFund, pk=pk) if pk else None

    if request.method == 'POST':
        form = DonationItemFundForm(request.POST, instance=instance)
        if form.is_valid():
            donation_item = form.save(commit=False)
            donation_item.contribution_type = contribution
            donation_item.save()

            action = "updated" if instance else "created"
            messages.success(request, f"🎉 Donation Item Fund {action} successfully!")
            return redirect('accountant_special_contribution_list')
    else:
        form = DonationItemFundForm(instance=instance)

    return render(request, 'accountant/finance/donation_item_fund_form.html', {
        'form': form,
        'contribution': contribution,
        'is_update': pk is not None
    })

# 📋 View to List Donation Item Funds for a Specific Contribution
@login_required
@parish_treasurer_required
def accountant_donation_item_fund_list(request, contribution_id):
    """
    View to list all donation item funds related to a specific special contribution.
    Only accessible to Admins and Superusers.
    """
    contribution = get_object_or_404(SpecialContribution, pk=contribution_id)
    donation_items = DonationItemFund.objects.filter(contribution_type=contribution).order_by('-id')
    years = Year.objects.all().order_by('-year')
    
    # Get the current year
    current_year = Year.objects.filter(is_current=True).first()

    context = {
        'contribution': contribution,
        'donation_items': donation_items,
        'years': years,
        'current_year': current_year.year if current_year else None,
    }
    return render(request, 'accountant/finance/donation_item_fund_list.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from settings.models import Year
from finance.models import SpecialContribution, DonationItemFund


# 🗑️ View to Delete a Donation Item Fund
@login_required
@parish_treasurer_required
def accountant_donation_item_fund_delete(request, contribution_id, pk):
    """
    View to handle the deletion of a DonationItemFund associated with a specific SpecialContribution.
    Only accessible to Admins and Superusers.
    """
    contribution = get_object_or_404(SpecialContribution, pk=contribution_id)
    donation_item_fund = get_object_or_404(DonationItemFund, pk=pk, contribution_type=contribution)

    if request.method == 'POST':
        donation_item_fund.delete()
        messages.success(request, "🗑️ Donation Item Fund deleted successfully!")
        return redirect('accountant_donation_item_fund_list', contribution_id=contribution.id)

    return render(request, 'accountant/finance/donation_item_fund_delete.html', {
        'donation_item_fund': donation_item_fund,
        'contribution': contribution
    })

# 📋 View to List All Donation Item Funds Across Contributions
@login_required
@parish_treasurer_required
def accountant_all_donation_item_funds(request):
    """
    View to display all donation item funds grouped by special contributions.
    Only accessible to Admins and Superusers.
    """
    contributions = SpecialContribution.objects.all()
    years = Year.objects.all().order_by('-year')

    contribution_data = {
        contribution: DonationItemFund.objects.filter(contribution_type=contribution).order_by('-date_created')
        for contribution in contributions
    }

    context = {
        'contribution_data': contribution_data,
        'contributions': contributions,
        'years': years,
        'title': 'All Donation Item Funds'
    }

    return render(request, 'accountant/finance/all_donation_item_funds.html', context)




from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from properties.models import ChurchAsset
from properties.forms import ChurchAssetFormSet
from datetime import datetime
import pytz

# 🌍 Set timezone for Tanzania
TZ_TZ = pytz.timezone('Africa/Dar_es_Salaam')


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from properties.models import ChurchAsset
from properties.forms import ChurchAssetFormSet
from datetime import datetime
import pytz
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from properties.utils import get_properties_radar_analysis


@login_required
@parish_treasurer_required
def accountant_properties_home(request):
    """
    View for the Properties home page, displaying church properties section.
    Accessible only by Admins and Superusers.
    """
    properties_radar_data = get_properties_radar_analysis()

    return render(request, 'accountant/properties/properties_home.html', {
        'properties_radar_data': properties_radar_data
    })

# 🏗️ View: Create Church Assets (Restricted)
@login_required
@parish_treasurer_required
def accountant_create_church_assets(request):
    """
    View to create multiple church assets using a formset.
    Accessible only by Admins and Superusers.
    """
    if request.method == 'POST':
        formset = ChurchAssetFormSet(request.POST)
        if formset.is_valid():
            saved_assets = []
            for form in formset:
                if form.cleaned_data:
                    asset = form.save()
                    saved_assets.append(asset.pk)

            request.session['saved_assets'] = saved_assets
            return redirect('accountant_upload_church_asset_media')
        else:
            messages.error(request, 'Failed to save assets. Please correct the errors below.')
    else:
        formset = ChurchAssetFormSet()

    return render(request, 'accountant/properties/create_church_assets.html', {'formset': formset})


# 📊 View: Display Church Assets (Restricted)
@login_required
@parish_treasurer_required
def accountant_church_assets_view(request):
    """
    View to display a list of church assets in a structured table format with search.
    Accessible only by Admins and Superusers.
    """
    # Fetch query parameters
    search_query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', '').strip()

    # Start with all assets
    church_assets = ChurchAsset.objects.all()

    # Apply filters
    if search_query:
        church_assets = church_assets.filter(name__icontains=search_query)
    
    if search_type:
        church_assets = church_assets.filter(asset_type=search_type)

    # Time formatting
    for asset in church_assets:
        asset.time_since_acquired = time_since(asset.acquisition_date)
        asset.time_since_created = time_since(asset.created_at)

    # Calculate totals
    total_quantity = church_assets.aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_value = church_assets.aggregate(Sum('value'))['value__sum'] or 0

    return render(request, 'accountant/properties/church_assets_list.html', {
        'church_assets': church_assets,
        'total_quantity': total_quantity,
        'total_value': total_value,
        'search_query': search_query,
        'search_type': search_type
    })


# ⏳ Helper Function for Time Formatting
def time_since(past_date):
    """
    Calculate time since a given date and return a readable string.
    """
    if not past_date:
        return "N/A"

    current_date = datetime.now().date()
    if isinstance(past_date, datetime):
        past_date = past_date.date()

    days = (current_date - past_date).days

    if days < 1:
        return "Today"
    elif days == 1:
        return "Yesterday"
    elif days < 7:
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif days < 30:
        weeks = days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    else:
        years = days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.timezone import now, localtime, make_aware
from datetime import datetime, date
import pytz

from properties.models import ChurchAsset, ChurchAssetMedia
from properties.forms import UpdateChurchAssetForm

# 🌍 Timezone for Tanzania
TZ_TZ = pytz.timezone('Africa/Dar_es_Salaam')


# 🔄 Update Church Asset (Restricted)
@login_required
@parish_treasurer_required
def accountant_update_church_asset(request, asset_id):
    """
    View to update an existing church asset.
    Accessible only by Admins and Superusers.
    """
    church_asset = get_object_or_404(ChurchAsset, id=asset_id)

    if request.method == 'POST':
        form = UpdateChurchAssetForm(request.POST, instance=church_asset)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Church asset updated successfully!")
            return redirect('accountant_church_assets_list')
        else:
            messages.error(request, "❌ Failed to update asset. Please correct the errors.")
    else:
        form = UpdateChurchAssetForm(instance=church_asset)

    return render(request, 'accountant/properties/update_church_asset.html', {
        'form': form,
        'church_asset': church_asset
    })


# 📋 Church Asset Details (Restricted)
@login_required
@parish_treasurer_required
def accountant_church_asset_detail(request, asset_id):
    """
    View to retrieve details of a specific Church Asset, including uploaded media.
    Accessible only by Admins and Superusers.
    """
    church_asset = get_object_or_404(ChurchAsset, id=asset_id)
    asset_media = ChurchAssetMedia.objects.filter(church_asset=church_asset)

    # Format dates
    acquisition_since = format_time_since(church_asset.acquisition_date)
    created_since = format_time_since(church_asset.created_at)

    # Asset Details
    asset_details = {
        "📛 Name": church_asset.name,
        "📂 Type": church_asset.get_asset_type_display(),
        "🔧 Status": church_asset.get_status_display(),
        "📦 Quantity": f"{church_asset.quantity} ({church_asset.get_quantity_name_display()})",
        "💰 Value": f"{church_asset.value} TZS",
        "📅 Acquisition Date": f"{church_asset.acquisition_date} ({acquisition_since})",
        "⏳ Date Created": f"{church_asset.created_at} ({created_since})",
        "📝 Description": church_asset.description or "No description available",
    }

    return render(request, "accountant/properties/church_asset_detail.html", {
        "church_asset": church_asset,
        "asset_details": asset_details,
        "asset_media": asset_media,
    })


# ⏳ Helper Function: Format Time Since Date
def format_time_since(past_date):
    """
    Convert a date/datetime to a human-readable format.
    """
    if not past_date:
        return "N/A"

    if isinstance(past_date, date) and not isinstance(past_date, datetime):
        past_date = datetime.combine(past_date, datetime.min.time())
        past_date = make_aware(past_date, timezone=TZ_TZ)

    past_date = localtime(past_date, timezone=TZ_TZ)
    current_time = localtime(now(), timezone=TZ_TZ)

    time_difference = current_time - past_date
    seconds = time_difference.total_seconds()

    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif seconds < 2419200:
        weeks = int(seconds // 604800)
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif seconds < 29030400:
        months = int(seconds // 2419200)
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        years = int(seconds // 29030400)
        return f"{years} year{'s' if years > 1 else ''} ago"


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.forms import modelformset_factory
from django.conf import settings
import os

from properties.models import ChurchAsset, ChurchAssetMedia
from properties.forms import ChurchAssetMediaForm

# 🚮 Delete Church Asset (Restricted)
@login_required
@parish_treasurer_required
def accountant_delete_church_asset(request, asset_id):
    """
    View to delete a given Church Asset along with all associated media.
    Accessible only by Admins and Superusers.
    """
    church_asset = get_object_or_404(ChurchAsset, id=asset_id)

    if request.method == "POST":
        # Delete associated media files from storage
        asset_media = ChurchAssetMedia.objects.filter(church_asset=church_asset)
        for media in asset_media:
            if media.image:
                image_path = os.path.join(settings.MEDIA_ROOT, str(media.image))
                if os.path.exists(image_path):
                    os.remove(image_path)  # Remove image from storage

        # Delete media records & the asset itself
        asset_media.delete()
        church_asset.delete()

        messages.success(request, "✅ Church Asset and all associated media deleted successfully!")
        return redirect('accountant_church_assets_list')

    return render(request, 'accountant/properties/church_asset_confirm_delete.html', {
        'church_asset': church_asset,
    })


# 📤 Upload Additional Media for Church Asset (Restricted)
@login_required
@parish_treasurer_required
def accountant_upload_additional_church_asset_media(request, asset_id):
    """
    View to upload multiple additional media files for a ChurchAsset.
    Accessible only by Admins and Superusers.
    """
    church_asset = get_object_or_404(ChurchAsset, id=asset_id)
    existing_media = ChurchAssetMedia.objects.filter(church_asset=church_asset)

    # Define FormSet
    ChurchAssetMediaFormSet = modelformset_factory(
        ChurchAssetMedia,
        form=ChurchAssetMediaForm,
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        formset = ChurchAssetMediaFormSet(request.POST, request.FILES, queryset=existing_media)
        if formset.is_valid():
            instances = formset.save(commit=False)
            saved_count = 0

            for instance in instances:
                if instance.image:
                    instance.church_asset = church_asset
                    instance.save()
                    saved_count += 1

            if saved_count > 0:
                messages.success(request, f"✅ {saved_count} media uploaded successfully!")
                return redirect('accountant_church_asset_detail', asset_id=church_asset.id)
            else:
                messages.warning(request, "⚠️ No media uploaded. Please select an image.")

        else:
            messages.error(request, "❌ Failed to upload media. Please check the form.")

    else:
        formset = ChurchAssetMediaFormSet(queryset=existing_media)

    return render(request, 'accountant/properties/upload_additional_church_asset_media.html', {
        'formset': formset,
        'church_asset': church_asset,
        'existing_media': existing_media,
    })


# 🗑️ Delete Church Asset Media (Restricted)
@login_required
@parish_treasurer_required
def accountant_delete_church_asset_media(request, media_id):
    """
    Deletes a specific church asset media file.
    Accessible only by Admins and Superusers.
    """
    if request.method == 'POST':
        media = get_object_or_404(ChurchAssetMedia, id=media_id)

        # Delete media file from storage
        if media.image:
            image_path = os.path.join(settings.MEDIA_ROOT, str(media.image))
            if os.path.exists(image_path):
                os.remove(image_path)

        media.delete()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from properties.models import ChurchAsset, ChurchAssetMedia
from properties.forms import ChurchAssetMediaForm

# 📤 Upload Media for Church Assets (Restricted)
@login_required
@parish_treasurer_required
def accountant_upload_church_asset_media(request):
    """
    View to upload multiple media files for church assets.
    Accessible only by Admins and Superusers.
    
    - Each church asset has a block for uploading images.
    - Users can upload multiple images per asset.
    - Users can skip this step if no images are needed.
    """
    # Retrieve the latest church assets created
    latest_assets = ChurchAsset.objects.order_by('-created_at')[:5]  # Adjust the limit as needed
    total_assets = latest_assets.count()

    if request.method == 'POST':
        uploaded_files_count = 0  # Track the number of files uploaded

        for asset in latest_assets:
            files = request.FILES.getlist(f'images_{asset.id}')  # Get multiple files per asset

            if files:
                for file in files:
                    ChurchAssetMedia.objects.create(church_asset=asset, image=file)
                    uploaded_files_count += 1

        if uploaded_files_count > 0:
            messages.success(request, f'✅ {uploaded_files_count} media files uploaded successfully!')
        else:
            messages.warning(request, '⚠️ No files uploaded. Please select files to upload.')

        return redirect('accountant_church_assets_list')  # Redirect to the assets list

    return render(request, 'accountant/properties/upload_church_asset_media.html', {
        'latest_assets': latest_assets,
        'total_assets': total_assets,
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from news.forms import NewsForm, NewsMediaForm
from news.models import News, NewsMedia

@login_required
@parish_treasurer_required
def accountant_create_news_view(request, pk=None):
    """
    View to create or update a news post with multiple media uploads.
    Only accessible to superusers and admins.
    """
    news = None
    if pk:
        news = get_object_or_404(News, pk=pk)  # Get existing news for updating

    if request.method == "POST":
        form = NewsForm(request.POST, instance=news)
        media_types = request.POST.getlist('media_type')
        media_files = request.FILES.getlist('file')

        if form.is_valid():
            news = form.save()  # Save or update news post

            # If updating, delete old media
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

            return redirect("accountant_news_list")  # Redirect to news list after saving
        else:
            messages.error(request, "❌ Please correct the errors in the form.")

    else:
        form = NewsForm(instance=news)  # Pre-fill form if updating

    return render(request, "accountant/news/create_news.html", {"form": form, "news": news})

from django.shortcuts import render
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required, user_passes_test
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
@parish_treasurer_required
def accountant_news_list_view(request):
    """
    View to display a list of news articles (without media) with the time since creation.
    Only accessible to superusers and admins.
    """
    news_list = News.objects.all()

    # Calculate "time since created" for each news
    for news in news_list:
        news.time_since_created = calculate_time_since(news.created_at)

    return render(request, "accountant/news/news_list.html", {"news_list": news_list})

from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth.decorators import login_required, user_passes_test
from news.models import News

# 🕰️ Time Calculation Helper
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

# 🚀 News Detail View (Restricted to Admins/Superusers)
@login_required
@parish_treasurer_required
def accountant_news_detail_view(request, pk):
    """
    View to display the full details of a specific news article.
    Only accessible to Admins and Superusers.
    """
    news = get_object_or_404(News, pk=pk)
    news.time_since_created = calculate_time_since(news.created_at)

    # Separate media into categories
    images = news.media.filter(media_type='image')
    videos = news.media.filter(media_type='video')
    documents = news.media.filter(media_type='document')

    return render(request, "accountant/news/news_detail.html", {
        "news": news,
        "images": images,
        "videos": videos,
        "documents": documents,
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from news.models import News, NewsMedia


@login_required
@parish_treasurer_required
def accountant_delete_news_view(request, pk):
    """
    View to delete a news article and all associated media.
    """
    news = get_object_or_404(News, pk=pk)

    if request.method == "POST":
        # Delete all associated media files
        news.media.all().delete()
        
        # Delete the news post
        news.delete()

        messages.success(request, "News post and all associated media deleted successfully!")
        return redirect("accountant_news_list")

    return render(request, "accountant/news/delete_news.html", {"news": news})

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from datetime import timedelta
from news.models import News, Like
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils.timezone import now
from datetime import timedelta
from news.models import News, Like, Comment

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

# 📰 News Home View (Restricted to Admins/Superusers)
@login_required
@parish_treasurer_required
def accountant_news_home(request):
    """
    View for the News Home Page.
    Only accessible to Admins and Superusers.
    """
    return render(request, 'accountant/news/news_home.html')



from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

# 🔔 Notifications Home View (Restricted to Admins/Superusers)
@login_required
@parish_treasurer_required
def accountant_notifications_home(request):
    """
    View for the Notifications Home Page.
    Only accessible to Admins and Superusers.
    """
    return render(request, 'accountant/notifications/notifications_home.html')


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import now
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required, user_passes_test
from notifications.models import Notification
from members.models import ChurchMember
from notifications.forms import NotificationForm

# 🚀 Create Notification View (Restricted)
@login_required
@parish_treasurer_required
def accountant_create_notification(request):
    """
    View to create and send notifications to church members.
    Only accessible to Admins and Superusers.
    """
    members = ChurchMember.objects.filter(status="Active")
    leaders = members.filter(leader__isnull=False)  # Leaders are also members

    for member in members:
        member.passport_url = member.passport.url if member.passport else "/static/images/user.png"

    if request.method == 'POST':
        form = NotificationForm(request.POST)
        selected_ids = list(set(request.POST.getlist('recipients')))  # Remove duplicates

        if not selected_ids:
            messages.error(request, "⚠️ You must select at least one recipient.")
            return render(request, 'accountant/notifications/create_notification.html', {
                'form': form,
                'members': members,
                'leaders': leaders,
            })

        if form.is_valid():
            title = form.cleaned_data["title"]
            message = form.cleaned_data["message"]

            recipients = ChurchMember.objects.filter(id__in=selected_ids)
            for recipient in recipients:
                Notification.objects.create(
                    title=title,
                    message=message,
                    church_member=recipient
                )

            messages.success(request, "📩 Notification sent successfully!")
            return redirect('accountant_notification_list')
        else:
            messages.error(request, "⚠️ Failed to send notification. Please check the form.")
    else:
        form = NotificationForm()

    return render(request, 'accountant/notifications/create_notification.html', {
        'form': form,
        'members': members,
        'leaders': leaders,
    })

# 🚀 Load Recipients via AJAX (Restricted)
@login_required
@parish_treasurer_required
def load_recipients(request):
    """
    AJAX function to dynamically load active recipients based on selection.
    Only accessible to Admins and Superusers.
    """
    recipient_type = request.GET.get("type", "all")
    search_query = request.GET.get("search", "").strip().lower()

    if recipient_type == "leaders":
        recipients = ChurchMember.objects.filter(leader__isnull=False, status="Active")
    else:
        recipients = ChurchMember.objects.filter(status="Active")

    if search_query:
        recipients = recipients.filter(full_name__icontains=search_query)

    for recipient in recipients:
        recipient.passport_url = recipient.passport.url if recipient.passport else "/static/images/user.png"

    html = render_to_string("accountant/notifications/_recipients_list.html", {"members": recipients})
    return HttpResponse(html)

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils.timezone import now
from collections import defaultdict
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from notifications.models import Notification

# 🚀 View: List Notifications (Restricted)
@login_required
@parish_treasurer_required
def accountant_notification_list(request):
    """
    View to list notifications grouped by their title and calculate time since creation.
    Accessible only by Admins and Superusers.
    """
    notifications = Notification.objects.select_related('church_member').filter(
        church_member__isnull=False
    ).order_by('-created_at')

    grouped_notifications = defaultdict(list)

    for notification in notifications:
        time_diff = now() - notification.created_at
        if time_diff.days > 0:
            time_since = f"{time_diff.days} days ago"
        elif time_diff.seconds > 3600:
            time_since = f"{time_diff.seconds // 3600} hours ago"
        elif time_diff.seconds > 60:
            time_since = f"{time_diff.seconds // 60} minutes ago"
        else:
            time_since = "Just now"

        full_name = notification.church_member.full_name if notification.church_member else "Unknown"
        profile_pic = notification.church_member.passport.url if notification.church_member.passport else "/static/images/user.png"

        grouped_notifications[notification.title].append({
            "id": notification.id,
            "message": notification.message,
            "full_name": full_name,
            "profile_pic": profile_pic,
            "created_at": notification.created_at.strftime("%Y-%m-%d %H:%M"),
            "time_since": time_since
        })

    return render(request, 'accountant/notifications/notification_list.html', {
        'grouped_notifications': dict(grouped_notifications)
    })

# 🚀 View: Filter Notifications by Title (AJAX, Restricted)
@login_required
@parish_treasurer_required
def filter_notifications_by_title(request):
    """
    AJAX-based filtering of notifications by title.
    Accessible only by Admins and Superusers.
    """
    search_query = request.GET.get("title", "").strip().lower()

    notifications = Notification.objects.select_related('church_member').filter(
        church_member__isnull=False,
        title__icontains=search_query
    ).order_by('-created_at')

    grouped_notifications = defaultdict(list)

    for notification in notifications:
        time_diff = now() - notification.created_at
        if time_diff.days > 0:
            time_since = f"{time_diff.days} days ago"
        elif time_diff.seconds > 3600:
            time_since = f"{time_diff.seconds // 3600} hours ago"
        elif time_diff.seconds > 60:
            time_since = f"{time_diff.seconds // 60} minutes ago"
        else:
            time_since = "Just now"

        full_name = notification.church_member.full_name if notification.church_member else "Unknown"
        profile_pic = notification.church_member.passport.url if notification.church_member.passport else "/static/images/user.png"

        grouped_notifications[notification.title].append({
            "id": notification.id,
            "message": notification.message,
            "full_name": full_name,
            "profile_pic": profile_pic,
            "created_at": notification.created_at.strftime("%Y-%m-%d %H:%M"),
            "time_since": time_since
        })

    return JsonResponse({"grouped_notifications": dict(grouped_notifications)})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from notifications.models import Notification

# 🚀 View: Delete Notifications (Restricted)
@login_required
@parish_treasurer_required
def accountant_delete_notification(request, delete_type, identifier):
    """
    Handles both:
    - Deleting a group of notifications under a title.
    - Deleting a single notification for a member.

    Parameters:
    - `delete_type`: "group" or "member"
    - `identifier`: Title (for group) or notification ID (for member)
    Accessible only by Admins and Superusers.
    """

    # 🗑️ Deleting a Group of Notifications (by Title)
    if delete_type == "group":
        notifications = Notification.objects.filter(title=identifier)

        if request.method == "POST":
            if notifications.exists():
                notifications.delete()
                messages.success(request, f"✅ All notifications under '{identifier}' deleted successfully.")
            else:
                messages.error(request, f"⚠️ No notifications found under '{identifier}'.")
            return redirect("accountant_notification_list")

        # Render Confirmation Page (GET Request)
        return render(request, "accountant/notifications/confirm_delete_group.html", {"title": identifier})

    # 🗑️ Deleting an Individual Notification
    elif delete_type == "member":
        notification = get_object_or_404(Notification, id=identifier)

        if request.method == "POST":
            notification.delete()
            messages.success(request, "✅ Deleted the selected notification successfully.")
            return redirect("accountant_notification_list")

        # Render Confirmation Page (GET Request)
        return render(request, "accountant/notifications/confirm_delete_member.html", {"notification": notification})

    # 🚫 Invalid Deletion Type Handling
    messages.error(request, "❌ Invalid deletion request.")
    return redirect("accountant_notification_list")


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .decorators import parish_treasurer_required

@login_required
@parish_treasurer_required
def parish_treasurer_details(request):
    """
    View to retrieve all details of a Parish Treasurer:
    - Account Information
    - Membership Details
    - Leadership Details
    - Certificates
    """
    user = request.user
    church_member = user.church_member
    leader = church_member.leader  # The leader details

    # ✅ Helper function to format boolean fields
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
        "Date of Birth": church_member.date_of_birth,
        "Gender": church_member.gender,
        "Address": church_member.address,
        "Community": church_member.community.name if church_member.community else "Not Assigned",
        "Apostolic Movement": church_member.apostolic_movement.name if church_member.apostolic_movement else "Not Assigned",
        "Marital Status": church_member.marital_status,
        "Job": church_member.job,
        "Baptized": format_boolean(church_member.is_baptised),
        "Received First Communion": format_boolean(church_member.has_received_first_communion),
        "Confirmed": format_boolean(church_member.is_confirmed),
        "Married": format_boolean(church_member.is_married),
    }

    # ✅ Leadership Details
    leadership_details = {
        "Occupation": leader.occupation,
        "Start Date": leader.start_date,
        "Committee": leader.committee,
        "Responsibilities": leader.responsibilities,
        "Education Level": leader.education_level,
        "Voluntary Service": format_boolean(leader.voluntary),
    }

    # ✅ Certificates
    certificates = {
        "Baptism Certificate": church_member.baptism_certificate.url if church_member.baptism_certificate else None,
        "First Communion Certificate": church_member.communion_certificate.url if church_member.communion_certificate else None,
        "Confirmation Certificate": church_member.confirmation_certificate.url if church_member.confirmation_certificate else None,
        "Marriage Certificate": church_member.marriage_certificate.url if church_member.marriage_certificate else None,
    }

    return render(request, "accountant/parish_treasurer_details.html", {
        "passport_url": church_member.passport.url if church_member.passport else None,
        "account_details": account_details,
        "membership_details": membership_details,
        "leadership_details": leadership_details,
        "certificates": certificates,
    })
