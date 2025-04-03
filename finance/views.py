# finance/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .utils import (
    get_offerings_data,
    get_special_contributions_data,  # <-- NEW
    get_asset_finance_data
)

def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required(login_url='login')
@user_passes_test(is_admin_or_superuser, login_url='login')
def finance_home(request):
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
    return render(request, 'finance/finance_home.html', context)

# finance/views.py

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib import messages

from .models import Offerings, OfferingCategory
from .forms import OfferingsForm

def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

class AdminOrSuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    def handle_no_permission(self):
        from django.shortcuts import redirect
        return redirect('login')

class OfferingsCreateByCategoryView(
    LoginRequiredMixin, 
    AdminOrSuperuserRequiredMixin, 
    CreateView
):
    """
    Create an Offerings record for a specific OfferingCategory.
    The category is determined by 'cat_pk' in the URL.
    """
    model = Offerings
    form_class = OfferingsForm
    template_name = 'finance/offering_form.html'
    # You might have a success URL referencing an "offerings_list" or 
    # "category_expenditure_list" or some relevant place:
    success_url = reverse_lazy('offering_category_list')

    def dispatch(self, request, *args, **kwargs):
        self.cat_pk = kwargs.get('cat_pk')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # 1) Fetch the category
        category = get_object_or_404(OfferingCategory, pk=self.cat_pk)
        # 2) Assign it to the new Offering
        form.instance.offering_category = category
        
        # 3) Optionally do anything else (like set year automatically)
        #    But if your model does it in save(), that’s fine.
        
        response = super().form_valid(form)
        messages.success(self.request, f"✅ Offering created in category: {category.name}")
        return response

    # If you want some custom context (e.g. display category name in template):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chosen_category'] = get_object_or_404(OfferingCategory, pk=self.cat_pk)
        return context


from django.utils.timezone import now
from django.utils.timesince import timesince
from django.views.generic import ListView
from django.db.models import Sum
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Offerings
from settings.models import Year
from members.models import ChurchMember

# ✅ Custom Mixin to Restrict Access to Admins/Superusers
class AdminOrSuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_superuser or self.request.user.user_type == 'ADMIN')

    def handle_no_permission(self):
        from django.shortcuts import redirect
        return redirect('login')  # Redirect unauthorized users to login

class OfferingsListView(LoginRequiredMixin, AdminOrSuperuserRequiredMixin, ListView):
    """
    View to list all offerings from all years.
    Only accessible by Admins and Superusers.
    """
    model = Offerings
    template_name = "finance/offerings_list.html"
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

        # NEW: Retrieve all OfferingCategory objects (for category filter)
        context["all_offering_categories"] = OfferingCategory.objects.all()

        # Calculate total amount
        context["total_offerings"] = offerings_qs.aggregate(Sum('amount'))['amount__sum'] or 0

        # Annotate offerings with time since created and updated
        for offering in context["offerings"]:
            offering.time_since_created = timesince(offering.date_created, now())
            offering.time_since_updated = timesince(offering.date_updated, now())

        return context


# finance/views.py
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.timezone import now
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import Offerings, OfferingCategory
from .forms import OfferingsForm

def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

class AdminOrSuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_admin_or_superuser(self.request.user)

    def handle_no_permission(self):
        return redirect('login')

class OfferingsUpdateByCategoryView(
    LoginRequiredMixin,
    AdminOrSuperuserRequiredMixin,
    UpdateView
):
    """
    Update an existing Offering record, forcibly linking it
    to an OfferingCategory determined by <cat_pk> in the URL.
    The user does NOT see 'offering_category' in the form.
    """
    model = Offerings
    form_class = OfferingsForm
    template_name = "finance/offering_form.html"
    success_url = reverse_lazy('offering_category_list')

    def dispatch(self, request, *args, **kwargs):
        # We'll store cat_pk from the URL for use in form_valid
        self.cat_pk = kwargs.get('cat_pk')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Force this record to use the chosen category
        chosen_category = get_object_or_404(OfferingCategory, pk=self.cat_pk)

        # The instance is the specific Offerings record being updated
        offering = form.save(commit=False)
        offering.offering_category = chosen_category
        
        # For example, we might manually update the date_updated:
        offering.date_updated = now()  
        
        offering.save()  # Now the category is set
        messages.success(self.request, f"✅ Offering record updated in category {chosen_category.name}!")
        return super().form_valid(form)



from django.urls import reverse_lazy
from django.views.generic import DeleteView
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Offerings

# ✅ Custom Mixin to Restrict Access to Admins/Superusers
class AdminOrSuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_superuser or self.request.user.user_type == 'ADMIN')

    def handle_no_permission(self):
        return redirect('login')  # Redirect unauthorized users to login

class OfferingsDeleteView(LoginRequiredMixin, AdminOrSuperuserRequiredMixin, DeleteView):
    """
    View to delete an existing offering record.
    Only accessible by Admins and Superusers.
    """
    model = Offerings
    template_name = "finance/offerings_confirm_delete.html"
    success_url = reverse_lazy('offerings_list')  # Redirect after deletion

    def delete(self, request, *args, **kwargs):
        """
        Override delete method to add a success message.
        """
        messages.success(request, "✅ Offering record deleted successfully.")
        return super().delete(request, *args, **kwargs)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from .models import FacilityRenting
from .forms import FacilityRentingForm

# ✅ Helper function to allow only Admins and Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# 🏠 View to Create a New Facility Renting
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def facility_renting_create(request):
    """
    View for creating a new facility renting, accessible only to Admins and Superusers.
    """
    if request.method == 'POST':
        form = FacilityRentingForm(request.POST)
        if form.is_valid():
            renting = form.save(commit=False)
            renting.save()
            messages.success(request, '✅ Facility renting record created successfully.')
            return redirect('facility_renting_list')
        else:
            messages.error(request, '❌ Failed to create record. Please check the form fields.')
    else:
        form = FacilityRentingForm()

    context = {
        'form': form,
        'title': 'Create Facility Renting',
        'submit_text': 'Create Record'
    }
    return render(request, 'finance/facility_renting_form.html', context)

# 🔄 View to Update an Existing Facility Renting
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def facility_renting_update(request, pk):
    """
    View for updating an existing facility renting, accessible only to Admins and Superusers.
    """
    renting = get_object_or_404(FacilityRenting, pk=pk)

    if request.method == 'POST':
        form = FacilityRentingForm(request.POST, instance=renting)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Facility renting record updated successfully.')
            return redirect('facility_renting_list')
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
    return render(request, 'finance/facility_renting_form.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from properties.models import ChurchAsset
from settings.models import Year
from finance.models import FacilityRenting

# ✅ Helper function to allow only Admins and Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# 📋 View to List All Facility Rentings
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def facility_renting_list(request):
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
    return render(request, 'finance/facility_renting_list.html', context)

# 🗑️ View to Delete a Facility Renting Record
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def facility_renting_delete(request, pk):
    """
    View to delete a specific Facility Renting record, accessible only to Admins and Superusers.
    """
    renting = get_object_or_404(FacilityRenting, pk=pk)

    if request.method == "POST":
        renting.delete()
        messages.success(request, "✅ Facility renting deleted successfully!")
        return redirect('facility_renting_list')

    return render(request, 'finance/facility_renting_delete.html', {'renting': renting})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import SpecialContributionForm
from .models import SpecialContribution

# ✅ Helper function to allow only Admins and Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# ➕ View to Add or Update Special Contributions
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def special_contribution_form(request, pk=None):
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
        return redirect('special_contribution_list')

    return render(request, 'finance/special_contribution_form.html', {
        'form': form,
        'title': title,
        'is_update': pk is not None
    })

# 🗑️ View to Delete a Special Contribution
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def special_contribution_delete(request, pk):
    """
    View to delete a special contribution.
    Only accessible to Admins and Superusers.
    """
    contribution = get_object_or_404(SpecialContribution, pk=pk)

    if request.method == 'POST':
        contribution.delete()
        messages.success(request, '🗑️ Special contribution deleted successfully!')
        return redirect('special_contribution_list')

    return render(request, 'finance/special_contribution_delete.html', {
        'contribution': contribution
    })


from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import SpecialContribution

# ✅ Helper function to allow only Admins and Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# 📋 View to List All Special Contributions
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def special_contribution_list(request):
    """
    View to list all special contributions.
    Only accessible to Admins and Superusers.
    """
    contributions = SpecialContribution.objects.all().order_by('-date_created')

    return render(request, 'finance/special_contribution_list.html', {
        'contributions': contributions
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import DonationItemFund, SpecialContribution
from .forms import DonationItemFundForm
from settings.models import Year

# ✅ Helper function to allow only Admins and Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# 📝 View to Create or Update Donation Item Fund
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def donation_item_fund_form(request, contribution_id, pk=None):
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
            return redirect('special_contribution_list')
    else:
        form = DonationItemFundForm(instance=instance)

    return render(request, 'finance/donation_item_fund_form.html', {
        'form': form,
        'contribution': contribution,
        'is_update': pk is not None
    })

# 📋 View to List Donation Item Funds for a Specific Contribution
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def donation_item_fund_list(request, contribution_id):
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
    return render(request, 'finance/donation_item_fund_list.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from settings.models import Year
from finance.models import SpecialContribution, DonationItemFund

# ✅ Helper function to allow only Admins and Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# 🗑️ View to Delete a Donation Item Fund
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def donation_item_fund_delete(request, contribution_id, pk):
    """
    View to handle the deletion of a DonationItemFund associated with a specific SpecialContribution.
    Only accessible to Admins and Superusers.
    """
    contribution = get_object_or_404(SpecialContribution, pk=contribution_id)
    donation_item_fund = get_object_or_404(DonationItemFund, pk=pk, contribution_type=contribution)

    if request.method == 'POST':
        donation_item_fund.delete()
        messages.success(request, "🗑️ Donation Item Fund deleted successfully!")
        return redirect('donation_item_fund_list', contribution_id=contribution.id)

    return render(request, 'finance/donation_item_fund_delete.html', {
        'donation_item_fund': donation_item_fund,
        'contribution': contribution
    })

# 📋 View to List All Donation Item Funds Across Contributions
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def all_donation_item_funds(request):
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

    return render(request, 'finance/all_donation_item_funds.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.timezone import now
from .forms import PledgeForm
from .models import Pledge

def pledge_create_view(request, pk=None):
    """
    Single view to handle both:
    - Creating a new pledge (no pk in URL)
    - Updating an existing pledge (with pk in URL)
    """
    if pk:
        # We're updating an existing pledge
        pledge_instance = get_object_or_404(Pledge, pk=pk)
        success_message = "🎉 Pledge successfully updated!"
    else:
        # We're creating a new pledge
        pledge_instance = None
        success_message = "🎉 Pledge successfully recorded!"

    if request.method == "POST":
        form = PledgeForm(request.POST, instance=pledge_instance)
        if form.is_valid():
            saved_pledge = form.save()
            messages.success(request, success_message)
            # Redirect to the 'update' URL so we can edit the same pledge if we want
            if pk:
                return redirect("pledge_update", pk=saved_pledge.pk)
            else:
                return redirect("pledge_create")
        else:
            messages.error(request, "⚠️ Please correct the errors below.")
    else:
        # If GET, pre-fill the form with the instance if updating
        form = PledgeForm(instance=pledge_instance)

    return render(request, "finance/pledge_form.html", {"form": form})


from django.shortcuts import render
from .models import Pledge
from settings.models import Year

def pledge_list_view(request):
    """
    Displays a list of pledges in a table format.
    """
    # Fetch all pledges, sorted by newest first
    pledges = Pledge.objects.all().order_by('-date_created')

    # Fetch all Year objects from the database
    all_years = Year.objects.all().order_by('year')

    # Hardcode the 12 months in Python
    months_list = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    # Get the year with is_current=True (if any)
    current_year_obj = Year.objects.filter(is_current=True).first()
    # We'll store just the year integer as a string (e.g. "2025") for easy comparison
    current_year_val = str(current_year_obj.year) if current_year_obj else ""

    context = {
        'pledges': pledges,
        'all_years': all_years,
        'months_list': months_list,
        'current_year_val': current_year_val,  # Pass the default year to the template
    }
    return render(request, 'finance/pledge_list.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Pledge

def pledge_delete_view(request, pk):
    """
    Handles deleting an existing pledge. 
    Displays a confirmation template on GET,
    and on POST actually deletes the record.
    """
    pledge_obj = get_object_or_404(Pledge, pk=pk)

    if request.method == "POST":
        # User confirmed deletion
        pledge_obj.delete()
        messages.success(request, "✅ Pledge successfully deleted!")
        return redirect("pledge_list")  # or wherever you want to go after deletion

    # If GET, render the confirmation template
    return render(request, "finance/pledge_confirm_delete.html", {"pledge": pledge_obj})


from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware, datetime, now
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import Category, Expenditure
from settings.models import Year

def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def category_expenditure_list(request, category_pk):
    """
    Displays Expenditures for a specific Category with 
    optional filtering (year, month, purpose, date range).
    The default year filter is the current system year.
    Shows a recalculated total after filtering.
    """

    # 1) Get the Category or 404
    category = get_object_or_404(Category, pk=category_pk)

    # 2) Collect filter inputs
    year_filter   = request.GET.get('year', '')
    month_filter  = request.GET.get('month', '')
    purpose_filter = request.GET.get('purpose', '')
    from_date_str = request.GET.get('from_date', '')
    to_date_str   = request.GET.get('to_date', '')

    # Base queryset only for this category
    expenditures_qs = category.expenditures.all()

    # 3) If user has not picked a year, default to current system year
    if not year_filter:
        current_year = now().year  # e.g. 2025
        year_filter = str(current_year)

    # 4) Apply filters
    # a) Year
    if year_filter:
        try:
            # Filter by year
            expenditures_qs = expenditures_qs.filter(year__year=year_filter)
        except:
            pass

    # b) Month
    if month_filter:
        expenditures_qs = expenditures_qs.filter(month=month_filter)

    # c) Purpose (icontains)
    if purpose_filter:
        expenditures_qs = expenditures_qs.filter(expenditure_purpose__icontains=purpose_filter)

    # d) Date range
    if from_date_str:
        parsed_from = parse_date(from_date_str)
        if parsed_from:
            from_dt = datetime(parsed_from.year, parsed_from.month, parsed_from.day)
            from_dt_aware = make_aware(from_dt)
            expenditures_qs = expenditures_qs.filter(date_taken__gte=from_dt_aware)

    if to_date_str:
        parsed_to = parse_date(to_date_str)
        if parsed_to:
            to_dt = datetime(parsed_to.year, parsed_to.month, parsed_to.day, 23, 59, 59)
            to_dt_aware = make_aware(to_dt)
            expenditures_qs = expenditures_qs.filter(date_taken__lte=to_dt_aware)

    # 5) Compute total of filtered expenditures
    total_filtered = expenditures_qs.aggregate(
        total=Sum('expenditure_amount')
    )['total'] or 0

    # 6) For building year/month dropdowns, if you want:
    all_years = Year.objects.order_by('year')
    all_months = [m[0] for m in Expenditure.MONTH_CHOICES]

    context = {
        'category': category,
        'expenditures': expenditures_qs.order_by('-date_created'),
        'total': total_filtered,

        # Re-display filter choices
        'year_filter': year_filter,
        'month_filter': month_filter,
        'purpose_filter': purpose_filter,
        'from_date': from_date_str,
        'to_date': to_date_str,

        # For year/month dropdown
        'all_years': all_years,
        'all_months': all_months,
    }
    return render(request, 'finance/category_expenditure_list.html', context)

# views.py

from django.shortcuts import render
from django.db.models import Sum
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware, datetime, now
from .models import Category, Expenditure
from settings.models import Year

def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def expenditure_list_all(request):
    """
    Displays all expenditures in tables grouped by category, 
    with search fields (year, month, category, purpose, date range).
    The default year is the system's current year if no year is provided.
    Shows totals per category and overall total,
    re-displaying the same filters on refresh. 
    """

    # 1) Collect Filter Inputs
    year_filter    = request.GET.get('year', '')         # e.g. "2023"
    month_filter   = request.GET.get('month', '')
    category_filter = request.GET.get('category', '')
    purpose_filter = request.GET.get('purpose', '')
    from_date_str  = request.GET.get('from_date', '')
    to_date_str    = request.GET.get('to_date', '')

    # 2) Base QuerySet
    expenditures_qs = Expenditure.objects.all()

    # 2a) If no year given, default to the current system year
    #     We check if user hasn't chosen year_filter and we do not want to override if user chooses empty.
    if not year_filter:
        # get current system year, e.g. 2025
        current_year = now().year
        # We set year_filter to that
        year_filter = str(current_year)

    # 3) Apply Filters
    # a) Year
    if year_filter:
        try:
            expenditures_qs = expenditures_qs.filter(year__year=year_filter)
        except:
            pass

    # b) Month
    if month_filter:
        expenditures_qs = expenditures_qs.filter(month=month_filter)

    # c) Category
    if category_filter:
        expenditures_qs = expenditures_qs.filter(category__pk=category_filter)

    # d) Purpose
    if purpose_filter:
        expenditures_qs = expenditures_qs.filter(expenditure_purpose__icontains=purpose_filter)

    # e) Date range
    if from_date_str:
        parsed_from = parse_date(from_date_str)
        if parsed_from:
            from_dt = datetime(parsed_from.year, parsed_from.month, parsed_from.day)
            from_dt_aware = make_aware(from_dt)
            expenditures_qs = expenditures_qs.filter(date_taken__gte=from_dt_aware)

    if to_date_str:
        parsed_to = parse_date(to_date_str)
        if parsed_to:
            to_dt = datetime(parsed_to.year, parsed_to.month, parsed_to.day, 23, 59, 59)
            to_dt_aware = make_aware(to_dt)
            expenditures_qs = expenditures_qs.filter(date_taken__lte=to_dt_aware)

    # 4) categories in the filtered queryset
    cat_ids = expenditures_qs.values_list('category', flat=True).distinct()
    categories = Category.objects.filter(pk__in=cat_ids).order_by('name')

    # 5) Overall sum
    overall_sum = expenditures_qs.aggregate(total=Sum('expenditure_amount'))['total'] or 0

    # 6) Category sums
    cat_sums = {}
    for c_id in cat_ids:
        cat_sum = expenditures_qs.filter(category_id=c_id).aggregate(cat_total=Sum('expenditure_amount'))['cat_total'] or 0
        cat_sums[c_id] = cat_sum

    # attach cat_sum
    for c in categories:
        c.cat_sum = cat_sums.get(c.pk, 0)

    # 7) Prepare context
    context = {
        'categories': categories,
        'overall_sum': overall_sum,

        # store final filter values for re-display in the form
        'year_filter': year_filter,
        'month_filter': month_filter,
        'category_filter': category_filter,
        'purpose_filter': purpose_filter,
        'from_date': from_date_str,
        'to_date': to_date_str,

        # For building dropdowns
        'all_years': Year.objects.order_by('year'),
        'all_months': [m[0] for m in Expenditure.MONTH_CHOICES],
        'all_categories': Category.objects.order_by('name'),
    }
    return render(request, 'finance/expenditure_list_all.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Expenditure

def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def expenditure_delete(request, pk):
    """
    View to delete a specific Expenditure record, prompting user confirmation.
    """
    expenditure = get_object_or_404(Expenditure, pk=pk)

    if request.method == 'POST':
        # Delete and redirect
        expenditure.delete()
        return redirect('expenditure_list_all')  # or wherever you want to go after deletion

    # If GET, show confirmation page
    return render(request, 'finance/expenditure_confirm_delete.html', {
        'expenditure': expenditure,
    })

# finance/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import ExpenditureForm
from .models import Expenditure, Category

def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def expenditure_create(request, category_pk):
    """
    View to create a new Expenditure for a given Category (category_pk).
    The category is not chosen by the user, but assigned automatically.
    """
    category = get_object_or_404(Category, pk=category_pk)

    if request.method == 'POST':
        # INCLUDE request.FILES so we process the uploaded file
        form = ExpenditureForm(request.POST, request.FILES)
        if form.is_valid():
            expenditure = form.save(commit=False)
            # assign the category automatically
            expenditure.category = category
            expenditure.save()
            # redirect to category_list or wherever you prefer
            return redirect('category_list')
    else:
        form = ExpenditureForm()

    return render(request, 'finance/expenditure_form.html', {
        'form': form,
        'title': f"Create Expenditure for {category.name}",
        'btn_label': 'Create',
    })

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def expenditure_update(request, pk):
    """
    View to update an existing Expenditure (Category can't be changed).
    """
    expenditure = get_object_or_404(Expenditure, pk=pk)

    if request.method == 'POST':
        # pass request.FILES as well
        form = ExpenditureForm(request.POST, request.FILES, instance=expenditure)
        if form.is_valid():
            form.save()  # category remains unchanged
            return redirect('category_list')
    else:
        form = ExpenditureForm(instance=expenditure)

    return render(request, 'finance/expenditure_form.html', {
        'form': form,
        'title': f"Update Expenditure: {expenditure.category.name}",
        'btn_label': 'Save Changes',
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Category

def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def category_delete(request, pk):
    """
    View to delete a Category, confirming first.
    """
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        # Delete the category and redirect
        category.delete()
        return redirect('category_list')  # or wherever you'd like to go after deletion

    # For GET requests, show the confirm page
    return render(request, 'finance/category_confirm_delete.html', {
        'category': category
    })

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def category_list(request):
    cats = Category.objects.all().order_by('name')
    return render(request, 'finance/category_list.html', {'categories': cats})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Category
from .forms import CategoryForm

def is_admin_or_superuser(user):
    # adjust per your logic
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def category_create(request):
    """
    View to create a new Category record.
    """
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category_list')  # Or wherever you'd like to go after success
    else:
        form = CategoryForm()

    return render(request, 'finance/category_form.html', {
        'form': form,
        'title': 'Create Category',
        'btn_label': 'Create',
    })


@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def category_update(request, pk):
    """
    View to update an existing Category record.
    """
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')  # or wherever you'd like to go
    else:
        form = CategoryForm(instance=category)

    return render(request, 'finance/category_form.html', {
        'form': form,
        'title': 'Update Category',
        'btn_label': 'Save Changes',
    })


# finance/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import OfferingCategoryForm
from .models import OfferingCategory

def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def offering_category_create(request):
    """
    View to create a new OfferingCategory.
    """
    if request.method == 'POST':
        form = OfferingCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('offering_category_list')  # or wherever you'd like to redirect
    else:
        form = OfferingCategoryForm()

    context = {
        'form': form,
        'title': 'Create Offering Category',
        'btn_label': 'Create'
    }
    return render(request, 'finance/offering_category_form.html', context)

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def offering_category_update(request, pk):
    """
    View to update an existing OfferingCategory.
    """
    category = get_object_or_404(OfferingCategory, pk=pk)

    if request.method == 'POST':
        form = OfferingCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('offering_category_list')  # or your chosen URL
    else:
        form = OfferingCategoryForm(instance=category)

    context = {
        'form': form,
        'title': 'Update Offering Category',
        'btn_label': 'Save Changes'
    }
    return render(request, 'finance/offering_category_form.html', context)



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import OfferingCategory

def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def offering_category_delete(request, pk):
    """
    View to delete an existing OfferingCategory, with a confirmation.
    """
    category = get_object_or_404(OfferingCategory, pk=pk)

    if request.method == 'POST':
        # User confirmed deletion
        category.delete()
        return redirect('offering_category_list')  # or your desired success URL

    # If GET, show a confirmation page
    context = {
        'category': category,
    }
    return render(request, 'finance/offering_category_confirm_delete.html', context)

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def offering_category_list(request):
    categories = OfferingCategory.objects.all().order_by('name')
    return render(request, 'finance/offering_category_list.html', 
                  {'categories': categories})

from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from django.utils.timezone import make_aware, datetime
from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required, user_passes_test

from settings.models import Year
from members.models import ChurchMember
from finance.models import OfferingCategory, Offerings

def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def offerings_by_category_list(request, cat_pk):
    category = get_object_or_404(OfferingCategory, pk=cat_pk)
    offerings_qs = category.offerings.all().order_by('-date_given')

    # Retrieve filters from GET
    year_param          = request.GET.get('year')            # this could be None or ''
    collected_by_filter = request.GET.get('collected_by', '')
    recorded_by_filter  = request.GET.get('recorded_by', '')
    mass_name_filter    = request.GET.get('mass_name', '')
    from_date_str       = request.GET.get('from_date', '')
    to_date_str         = request.GET.get('to_date', '')

    # ------------------------------------------------
    # 1) Determine the default year_filter:
    #    - If year_param is None (meaning ?year= is not in the URL at all), 
    #      use the current year's .year.
    #    - Otherwise, keep whatever the user gave (even if it's empty string).
    # ------------------------------------------------
    if year_param is None:
        # No ?year= in the querystring => default to current year
        current_year_obj = Year.objects.filter(is_current=True).first()
        if current_year_obj:
            year_filter = str(current_year_obj.year)  # e.g. "2025"
        else:
            # If there's no "current" year in DB, fallback to All Years
            year_filter = ''
    else:
        # The user explicitly provided something (?year= or ?year=2022, etc.)
        year_filter = year_param

    # ------------------------------------------------
    # 2) Apply filters
    # ------------------------------------------------
    if year_filter:
        # If it's not empty, filter by that year
        offerings_qs = offerings_qs.filter(year__year=year_filter)

    if collected_by_filter:
        offerings_qs = offerings_qs.filter(collected_by__full_name=collected_by_filter)

    if recorded_by_filter:
        offerings_qs = offerings_qs.filter(recorded_by__full_name=recorded_by_filter)

    if mass_name_filter:
        offerings_qs = offerings_qs.filter(mass_name__icontains=mass_name_filter)

    if from_date_str:
        parsed_from = parse_date(from_date_str)
        if parsed_from:
            offerings_qs = offerings_qs.filter(date_given__gte=parsed_from)

    if to_date_str:
        parsed_to = parse_date(to_date_str)
        if parsed_to:
            offerings_qs = offerings_qs.filter(date_given__lte=parsed_to)

    # 3) Compute total
    total_offerings = offerings_qs.aggregate(Sum('amount'))['amount__sum'] or 0

    # 4) Build context
    context = {
        'category': category,
        'offerings': offerings_qs,
        'total_offerings': total_offerings,

        # For building filter dropdowns
        'years': Year.objects.order_by('year'),
        'collected_by_members': ChurchMember.objects.filter(status="Active"),
        'recorded_by_members': ChurchMember.objects.filter(status="Active"),

        # Pass filter choices back to template
        'year_filter': year_filter,  # string
        'collected_by_filter': collected_by_filter,
        'recorded_by_filter': recorded_by_filter,
        'mass_name_filter': mass_name_filter,
        'from_date': from_date_str,
        'to_date': to_date_str,
    }

    return render(request, 'finance/offerings_by_category_list.html', context)

# finance/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.utils.timezone import now

# Models needed:
from members.models import ChurchMember
from finance.models import (
    OfferingCategory, Offerings,
    SpecialContribution, DonationItemFund,
    Expenditure, Category
)

def is_admin_or_superuser(user):
    """Check if the user is authenticated and is superuser or admin."""
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def finance_general_report(request):
    """
    Displays the general finance report for the church:
      - Table A: Offerings (by category, this month)
      - Table B: Special Diocesan contributions (this month)
      - Table C: Jimbo contributions (this month)
      - Table D: Fellowship contributions (this month)
      - Table E: Sum of A+B+C+D + Christians stats
      - Table H: Expenditures by Category (this month)
      - Table I: Summary of Income & Expenditure (including all-time data)
      - Table J: Signatures & Stamps (needs current date/time)
    """

    # 1) Current calendar year/month
    current_year = now().year
    current_month = now().month

    # 2) current_datetime for Table J
    current_datetime = now()

    # ----------------------------------------------------------
    # TABLE A: Offerings by OfferingCategory (Current Month)
    # ----------------------------------------------------------
    categories_data = []
    offering_categories = OfferingCategory.objects.all()

    for cat in offering_categories:
        total_amount = cat.offerings.filter(
            date_given__year=current_year,
            date_given__month=current_month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        categories_data.append({
            'category': cat,
            'total_amount': total_amount,
        })
    table_a_total = sum(item['total_amount'] for item in categories_data)

    # ----------------------------------------------------------
    # TABLE B: Special Diocesan Contributions (Current Month)
    # ----------------------------------------------------------
    diocesan_data = []
    diocesan_contributions = SpecialContribution.objects.filter(contribution_type="DIOCESAN")

    for sc in diocesan_contributions:
        total_funds = sc.donation_item_funds.filter(
            date_created__year=current_year,
            date_created__month=current_month
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        diocesan_data.append({
            'special_contribution': sc,
            'total_amount': total_funds,
        })

    diocesan_total = sum(item['total_amount'] for item in diocesan_data)
    sum_table_a_b = table_a_total + diocesan_total

    # ----------------------------------------------------------
    # TABLE C: Jimbo contributions (Current Month)
    # ----------------------------------------------------------
    jimbo_data = []
    jimbo_contributions = SpecialContribution.objects.filter(contribution_type="JIMBO")

    for sc in jimbo_contributions:
        total_funds = sc.donation_item_funds.filter(
            date_created__year=current_year,
            date_created__month=current_month
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        jimbo_data.append({
            'special_contribution': sc,
            'total_amount': total_funds,
        })

    jimbo_total = sum(item['total_amount'] for item in jimbo_data)
    sum_table_a_b_c = table_a_total + diocesan_total + jimbo_total

    # ----------------------------------------------------------
    # TABLE D: Fellowship contributions (Current Month)
    # ----------------------------------------------------------
    fellowship_data = []
    fellowship_contributions = SpecialContribution.objects.filter(contribution_type="FELLOWSHIP")

    for sc in fellowship_contributions:
        total_funds = sc.donation_item_funds.filter(
            date_created__year=current_year,
            date_created__month=current_month
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        fellowship_data.append({
            'special_contribution': sc,
            'total_amount': total_funds,
        })

    fellowship_total = sum(item['total_amount'] for item in fellowship_data)
    sum_table_a_b_c_d = table_a_total + diocesan_total + jimbo_total + fellowship_total

    # ----------------------------------------------------------
    # TABLE E: Additional Stats (members, avg. offering)
    # ----------------------------------------------------------
    total_church_members = ChurchMember.objects.filter(status="Active").count()

    if total_church_members > 0:
        average_offering_per_member = sum_table_a_b_c_d / total_church_members
    else:
        average_offering_per_member = 0

    # ----------------------------------------------------------
    # TABLE H: Expenditures by Category (Current Month)
    # ----------------------------------------------------------
    category_expenditures_data = []
    all_expenditure_categories = Category.objects.all()

    for cat in all_expenditure_categories:
        total_spent = cat.expenditures.filter(
            date_taken__year=current_year,
            date_taken__month=current_month
        ).aggregate(Sum('expenditure_amount'))['expenditure_amount__sum'] or 0

        category_expenditures_data.append({
            'category': cat,
            'total_spent': total_spent,
        })

    table_h_total = sum(item['total_spent'] for item in category_expenditures_data)

    # ----------------------------------------------------------
    # TABLE I: Summary of Income & Expenditure (All-Time)
    # ----------------------------------------------------------
    # 1) "Balance from the previous period" 
    #    = (all offerings EVER) + (all donation item funds EVER) - (all expenditures EVER)
    
    all_offerings_total = Offerings.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    all_donation_funds_total = DonationItemFund.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    all_expenditures_total = Expenditure.objects.aggregate(Sum('expenditure_amount'))['expenditure_amount__sum'] or 0

    previous_balance = all_offerings_total + all_donation_funds_total - all_expenditures_total

    # 2) "Overall monthly income" => sum_table_a_b_c_d
    # 3) "Total of prev balance & monthly income" => previous_balance + sum_table_a_b_c_d
    # 4) "Total monthly expenses" => table_h_total
    # 5) "Total remained in this month" => sum_table_a_b_c_d - table_h_total
    # 6) "Overall total remained" => previous_balance + [that remainder]

    total_of_prev_balance_and_monthly_income = previous_balance + sum_table_a_b_c_d
    total_remained_this_month = sum_table_a_b_c_d - table_h_total
    overall_total_remained = previous_balance + total_remained_this_month

    # ----------------------------------------------------------
    # TABLE J: (Signatures, Stamps) => needs current_datetime
    # ----------------------------------------------------------
    # We'll rely on the partial to display these using `current_datetime`.

    # ----------------------------------------------------------
    # Build final context
    # ----------------------------------------------------------
    context = {
        # Table A
        'categories_data': categories_data,
        'table_a_total': table_a_total,

        # Table B
        'diocesan_data': diocesan_data,
        'diocesan_total': diocesan_total,
        'sum_table_a_b': sum_table_a_b,

        # Table C
        'jimbo_data': jimbo_data,
        'jimbo_total': jimbo_total,
        'sum_table_a_b_c': sum_table_a_b_c,

        # Table D
        'fellowship_data': fellowship_data,
        'fellowship_total': fellowship_total,
        'sum_table_a_b_c_d': sum_table_a_b_c_d,

        # Table E
        'total_church_members': total_church_members,
        'average_offering_per_member': average_offering_per_member,

        # Table H
        'category_expenditures_data': category_expenditures_data,
        'table_h_total': table_h_total,

        # Table I
        'previous_balance': previous_balance,
        'overall_monthly_income': sum_table_a_b_c_d,
        'total_of_prev_balance_and_monthly_income': total_of_prev_balance_and_monthly_income,
        'total_monthly_expenses': table_h_total,
        'total_remained_this_month': total_remained_this_month,
        'overall_total_remained': overall_total_remained,

        # Table J => Current date/time for signatures, stamps
        'current_datetime': current_datetime,

        # For headings in partials
        'current_year': current_year,
        'current_month': current_month,
    }

    return render(request, 'finance/finance_general_report.html', context)
