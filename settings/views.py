# settings/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import YearForm
from django.contrib.auth.decorators import login_required, user_passes_test

# ✅ Access Control: Only Admins & Superusers Allowed
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')


# 📅 **Create Year (Admin/Superuser Only)**
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def create_year(request):
    """
    View for creating a Year instance.
    Ensures only one year is set as current.
    Only accessible by Admins and Superusers.
    """
    print("🔍 Accessing Create Year View")

    if request.method == 'POST':
        print("📥 Received POST request to create a new year")
        form = YearForm(request.POST)

        if form.is_valid():
            # ✅ Ensure only one year is set as current
            if form.cleaned_data.get('is_current'):
                print("⚠️ Setting this year as current. Unsetting others...")
                from .models import Year
                Year.objects.filter(is_current=True).update(is_current=False)  # Unset all other current years

            form.save()
            print("✅ Year created successfully!")

            messages.success(request, "🎉 Year created successfully!")
            return redirect('year_list')  # Redirect to the year list page
        else:
            print("❌ Form validation failed:", form.errors)
            messages.error(request, "❌ Failed to create year. Please correct the errors.")
    else:
        print("🗒️ Displaying empty form for new year creation")
        form = YearForm()

    return render(request, 'settings/create_year.html', {'form': form})

# settings/views.py

from django.shortcuts import render
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Year

# ✅ Access Control: Only Admins & Superusers Allowed
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')


# ⏱️ **Calculate Time Since Creation**
def calculate_time_since(created_at):
    """
    Calculates how much time has passed since a year was created.
    Returns a human-readable time format.
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


# 📋 **List Years (Admin/Superuser Only)**
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def year_list(request):
    """
    View for listing all the years.
    Accessible only by Admins and Superusers.
    """
    print("📅 Accessing Year List View")

    try:
        years = Year.objects.all().order_by('year')  # Sort years in ascending order
        print(f"✅ Retrieved {years.count()} years from the database")

        # Add calculated time since creation
        for year in years:
            year.time_since_created = calculate_time_since(year.date_created)

    except Exception as e:
        print(f"❌ Error retrieving years: {e}")
        messages.error(request, "⚠️ Failed to load years. Please try again later.")
        years = []

    return render(request, 'settings/year_list.html', {'years': years})

# settings/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Year
from .forms import YearForm


# ✅ Access Control: Only Admins & Superusers Allowed
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')


# ✏️ **Update Year (Admin/Superuser Only)**
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def update_year(request, pk):
    """
    View for updating a year.
    Accessible only by Admins and Superusers.
    """
    print(f"📋 Accessing Update Year View for Year ID: {pk}")

    year = get_object_or_404(Year, pk=pk)

    if request.method == 'POST':
        form = YearForm(request.POST, instance=year)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Year updated successfully!")
            print(f"✅ Year {year.year} updated successfully!")
            return redirect('year_list')
        else:
            messages.error(request, "⚠️ Failed to update year. Please correct the errors.")
            print(f"❌ Form errors: {form.errors}")
    else:
        form = YearForm(instance=year)

    return render(request, 'settings/update_year.html', {'form': form, 'year': year})


# 🗑️ **Delete Year (Admin/Superuser Only)**
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def delete_year(request, pk):
    """
    View for confirming and deleting a year.
    Accessible only by Admins and Superusers.
    """
    print(f"🗑️ Accessing Delete Year View for Year ID: {pk}")

    year = get_object_or_404(Year, pk=pk)

    if request.method == 'POST':
        try:
            # ❌ Prevent deletion of the current year
            if year.is_current:
                raise ValidationError("⚠️ You cannot delete the current year.")

            # ✅ Delete the year if it's not current
            year.delete()
            messages.success(request, "✅ Year deleted successfully!")
            print(f"✅ Year {year.year} deleted successfully!")

        except ValidationError as e:
            messages.error(request, str(e))
            print(f"❌ Error: {e}")

        return redirect('year_list')

    return render(request, 'settings/confirm_delete_year.html', {'year': year})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from datetime import datetime, timezone
from django.utils.timezone import now

from .models import Year, OutStation, Cell  # Updated imports
from .forms import OutStationForm  # Updated import
from .utils import get_settings_distribution_analysis  # Utility for bar chart data
from accounts.decorators import admin_required  # Assuming this is still valid

def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def settings_home(request):
    """
    View to render the Settings Home Page.
    Accessible only by Admins and Superusers.
    """
    print(f"⚙️ Accessing Settings Home by {request.user.username}")

    # Get counts for each item
    years_count = Year.objects.count()
    outstations_count = OutStation.objects.count()  # Changed from zones_count
    cells_count = Cell.objects.count()  # Changed from communities_count

    # Get settings distribution data for the bar chart
    settings_distribution_data = get_settings_distribution_analysis()

    context = {
        "settings_distribution_data": settings_distribution_data,
        "years_count": years_count,
        "outstations_count": outstations_count,  # Changed from zones_count
        "cells_count": cells_count,  # Changed from communities_count
    }
    
    return render(request, "settings/settings_home.html", context)

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def create_or_update_outstation(request, outstation_id=None):  # Changed from create_or_update_zone
    """
    View for creating or updating a church outstation.
    Accessible only by Admins and Superusers.
    """
    action = "Update" if outstation_id else "Create"
    print(f"📍 {action} Outstation View Accessed by {request.user.username}")

    # Retrieve the outstation if updating
    outstation = get_object_or_404(OutStation, id=outstation_id) if outstation_id else None  # Changed from Zone

    if request.method == "POST":
        form = OutStationForm(request.POST, instance=outstation)  # Changed from ZoneForm
        if form.is_valid():
            form.save()

            if outstation:
                messages.success(request, "✅ Outstation updated successfully!")
                print(f"✅ Outstation '{outstation.name}' updated successfully.")
            else:
                messages.success(request, "✅ Outstation created successfully!")
                print("✅ New outstation created successfully.")

            return redirect("outstation_list")  # Changed from zone_list
        else:
            messages.error(request, "⚠️ Failed to save outstation. Please correct the errors.")
            print(f"❌ Form errors: {form.errors}")

    else:
        form = OutStationForm(instance=outstation)  # Changed from ZoneForm

    return render(request, "settings/create_update_outstation.html", {"form": form, "outstation": outstation})  # Updated template name

from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def outstation_list(request):
    """
    View for listing all the outstations with:
    - Total cells in each outstation
    - Total number of outstations
    - Overall total of cells across all outstations
    """
    print(f"📍 Outstation List accessed by {request.user.username}")

    # Get all outstations
    outstations = OutStation.objects.annotate(total_cells=Count('cells')).order_by('-date_created')
    total_outstations = outstations.count()
    overall_total_cells = sum(outstation.total_cells for outstation in outstations)

    print(f"✅ Total Outstations Displayed: {total_outstations}")
    print(f"🏘️ Overall Total Cells: {overall_total_cells}")

    # Add time since created and updated
    for outstation in outstations:
        outstation.time_since_created = time_since(outstation.date_created)
        outstation.time_since_updated = time_since(outstation.date_updated)

    return render(request, 'settings/outstation_list.html', {
        'outstations': outstations,
        'total_outstations': total_outstations,
        'overall_total_cells': overall_total_cells,
    })

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def delete_outstation(request, outstation_id):  # Changed from delete_zone
    """
    View for deleting an Outstation after user confirmation.
    Only accessible to Admins and Superusers.
    """
    outstation = get_object_or_404(OutStation, id=outstation_id)  # Changed from Zone
    print(f"🗑️ Deletion Requested for Outstation: {outstation.name} (ID: {outstation.id}) by {request.user.username}")

    if request.method == "POST":
        outstation_name = outstation.name  # Store for confirmation message
        outstation.delete()

        messages.success(request, f"✅ Outstation '{outstation_name}' deleted successfully.")
        print(f"✅ Outstation '{outstation_name}' deleted by {request.user.username}")
        return redirect("outstation_list")  # Changed from zone_list

    print(f"⚠️ Confirmation required for deleting Outstation: {outstation.name}")
    return render(request, "settings/delete_outstation.html", {"outstation": outstation})  # Updated template name

@login_required
@admin_required
def outstation_detail(request, pk):  # Changed from zone_detail
    """
    View for displaying the details of a specific Outstation.
    Accessible only to authenticated users with admin privileges.
    """
    print(f"🔍 Outstation Details Requested for Outstation ID: {pk} by {request.user.username}")

    # Fetch the Outstation or raise a 404 if not found
    outstation = get_object_or_404(OutStation, pk=pk)  # Changed from Zone

    # Add time since created/updated
    outstation.time_since_created = time_since(outstation.date_created)
    outstation.time_since_updated = time_since(outstation.date_updated)

    print(f"✅ Outstation '{outstation.name}' details retrieved successfully.")

    return render(request, "settings/outstation_detail.html", {"outstation": outstation})  # Updated template name

# ⏱️ **Time Since Calculation Helper**
def time_since(dt):
    """
    Calculate time since a given datetime.
    """
    now = datetime.now(timezone.utc)
    delta = now - dt

    if delta.days > 365:
        years = delta.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif delta.days > 30:
        months = delta.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif delta.days > 0:
        return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"
    
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cell, OutStation  # Updated imports
from .forms import CellForm  # Updated import
from datetime import datetime, timezone
from django.db.models import Q
from accounts.decorators import admin_required  # Assuming this is still valid

@login_required
@admin_required
def create_update_cell(request, cell_id=None):  # Changed from create_update_community
    """
    View to create or update a cell.
    - **Create Mode:** No cell_id provided.
    - **Update Mode:** cell_id is provided to fetch and update an existing cell.
    """
    if cell_id:
        print(f"✏️ Editing Cell ID: {cell_id}")
        cell = get_object_or_404(Cell, pk=cell_id)  # Changed from Community
    else:
        print("➕ Creating a new Cell")
        cell = None

    if request.method == "POST":
        print("📤 Received POST request")
        form = CellForm(request.POST, instance=cell)  # Changed from CommunityForm
        if form.is_valid():
            form.save()
            if cell:
                messages.success(request, "✅ Cell updated successfully!")
            else:
                messages.success(request, "✅ Cell created successfully!")
            return redirect("cell_list")  # Changed from community_list
        else:
            print(f"❌ Form errors: {form.errors}")
            messages.error(request, "⚠️ Failed to save the cell. Please check the form.")
    else:
        form = CellForm(instance=cell)  # Changed from CommunityForm

    return render(request, "settings/create_update_cell.html", {"form": form, "cell": cell})  # Updated template name

@login_required
@admin_required
def delete_cell(request, cell_id):  # Changed from delete_community
    """
    View to delete a cell after user confirmation.
    """
    print(f"🗑️ Attempting to delete Cell ID: {cell_id}")
    cell = get_object_or_404(Cell, id=cell_id)  # Changed from Community

    if request.method == "POST":
        cell.delete()
        print(f"✅ Cell '{cell.name}' deleted successfully.")
        messages.success(request, f"✅ The cell '{cell.name}' has been deleted successfully.")
        return redirect("cell_list")  # Changed from community_list

    return render(request, "settings/delete_cell.html", {"cell": cell})  # Updated template name

def calculate_time_since(date):
    """ 
    Returns a human-readable time difference since the given date. 
    """
    if not date:
        return "N/A"

    now = datetime.now(timezone.utc)
    diff = now - date

    days = diff.days
    seconds = diff.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    if days > 0:
        return f"{days} days ago"
    elif hours > 0:
        return f"{hours} hours ago"
    elif minutes > 0:
        return f"{minutes} minutes ago"
    else:
        return "Just now"

from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render

@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def cell_list(request):
    """
    View to display a list of cells grouped by their respective outstations.
    Features:
    - Total number of cells in the church.
    - Total number of cells per outstation.
    """
    print("📥 Processing cell list request")

    # Get all outstations and their cells
    outstations = OutStation.objects.all().order_by("name")
    outstation_cells = {}
    outstations_without_cells = []
    total_cells = Cell.objects.count()  # Overall total cells

    for outstation in outstations:
        print(f"🏠 Processing Outstation: {outstation.name}")
        cells = Cell.objects.filter(outstation=outstation).order_by('-date_created')
        cell_count = cells.count()

        if cell_count > 0:
            for cell in cells:
                cell.time_since_created = time_since(cell.date_created)
                cell.time_since_updated = time_since(cell.date_updated)
            outstation_cells[outstation] = {
                "cells": cells,
                "total": cell_count
            }
        else:
            outstations_without_cells.append(outstation.name)

    print(f"📊 Total Cells: {total_cells}")
    print(f"🚫 Outstations without Cells: {len(outstations_without_cells)}")

    return render(request, "settings/cell_list.html", {
        "outstation_cells": outstation_cells,
        "outstations_without_cells": outstations_without_cells,
        "total_cells": total_cells,
    })

@login_required
@admin_required
def cell_detail(request, cell_id):  # Changed from community_detail
    """
    View to display details of a single cell.
    
    📋 Features:
    - Displays time since the cell was created & updated.
    - Secured access for authenticated users only.
    """
    print(f"🔍 Fetching details for Cell ID: {cell_id}")

    # 🗂️ Fetch cell or raise 404 if not found
    cell = get_object_or_404(Cell, pk=cell_id)  # Changed from Community

    # ⏱️ Calculate time since created & updated
    cell.time_since_created = calculate_time_since(cell.date_created)
    cell.time_since_updated = calculate_time_since(cell.date_updated)

    print(f"✅ Retrieved cell: {cell.name}")
    print(f"⏳ Created: {cell.time_since_created}, Updated: {cell.time_since_updated}")

    return render(request, "settings/cell_detail.html", {"cell": cell})  # Updated template name


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import ChurchLocation
from .forms import ChurchLocationForm

@login_required(login_url='login')
@admin_required  # 🔒 Requires authentication
def set_church_location(request):
    """
    🚀 Allows setting the church location manually or via OpenStreetMap.
    - Secured with login requirement.
    - Updates or creates the location record.
    - Only one active location at a time.
    """
    print("📍 Accessing Church Location Setup")

    # Retrieve existing location or create a new instance
    location = ChurchLocation.objects.first()
    form = ChurchLocationForm(instance=location)

    if request.method == "POST":
        print("📥 Processing POST request to save church location")
        form = ChurchLocationForm(request.POST, instance=location)
        if form.is_valid():
            church_location = form.save(commit=False)

            # Deactivate all other locations (if any)
            ChurchLocation.objects.update(is_active=False)
            
            # Set the new location as active
            church_location.is_active = True
            church_location.save()

            messages.success(request, "✅ Church location saved successfully!")
            print("✅ Church location updated and set as active")
            return redirect("location_list")
        else:
            messages.error(request, "❌ Failed to save the location. Please correct the errors.")
            print("❌ Validation errors:", form.errors)

    return render(request, "settings/set_church_location.html", {"form": form, "location": location})

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ChurchLocation

@login_required
@admin_required  # 🔒 Requires authentication
def location_list(request):
    """
    🗺️ Displays a full-screen OpenStreetMap with the active church location.
    - Shows the most recently set active location.
    - Secured with login requirement.
    """
    print("🌍 Loading Church Location Map...")

    # Retrieve the active church location
    active_location = ChurchLocation.objects.filter(is_active=True).first()

    if active_location:
        print(f"✅ Active Location Found: ({active_location.latitude}, {active_location.longitude})")
    else:
        print("⚠️ No active church location found!")

    return render(request, "settings/location_map.html", {"active_location": active_location})

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import ChurchLocation

@login_required
@admin_required  # 🔒 Requires authentication
def update_church_location(request):
    """
    🚀 Updates the church location using OpenStreetMap.
    - Displays the current location and allows selecting a new one.
    - Handles both updates and creation of a new location if none exists.
    """
    print("📍 Accessing Church Location Update Page")

    # Fetch the currently active church location
    church_location = ChurchLocation.objects.filter(is_active=True).first()

    if request.method == "POST":
        print("📥 Received POST request to update location")

        # Get new latitude and longitude from form submission
        new_latitude = request.POST.get("latitude")
        new_longitude = request.POST.get("longitude")

        # Validate inputs
        if new_latitude and new_longitude:
            # Deactivate all existing locations
            ChurchLocation.objects.update(is_active=False)

            if church_location:
                print(f"🔄 Updating existing location: {church_location.name}")
                church_location.latitude = new_latitude
                church_location.longitude = new_longitude
                church_location.is_active = True
                church_location.save()
            else:
                print("➕ Creating a new church location")
                ChurchLocation.objects.create(latitude=new_latitude, longitude=new_longitude, is_active=True)

            messages.success(request, "✅ Church location updated successfully!")
            return redirect("location_list")

        else:
            messages.error(request, "❌ Both latitude and longitude are required.")
            print("❌ Missing latitude or longitude")

    context = {
        "church_location": church_location,
    }
    return render(request, "settings/update_location.html", context)

from django.shortcuts import render
from django.http import Http404
from django.contrib.auth.decorators import login_required
from .models import ChurchLocation

@login_required
@admin_required  # 🔒 Requires authentication
def view_church_location(request):
    """
    🗺️ Displays a full-screen OpenStreetMap with the active church location.
    - Retrieves the active location from the database.
    - Returns a 404 error if no active location is found.
    """
    print("🌍 Loading Church Location Map...")

    # Get the active church location
    active_location = ChurchLocation.objects.filter(is_active=True).first()

    if not active_location:
        print("⚠️ No active church location found!")
        raise Http404("No active church location found.")

    print(f"✅ Active Location: {active_location.latitude}, {active_location.longitude}")
    return render(request, "settings/view_church_location.html", {"active_location": active_location})

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import ChurchLocation

@login_required
@admin_required  # 🔒 Requires authentication
def delete_church_location(request):
    """
    🗑️ Deletes the existing church location if it exists.
    - Prompts for confirmation before deletion.
    - Provides feedback upon successful deletion or errors.
    """
    print("📍 Attempting to delete church location...")

    # Fetch the first saved church location
    church_location = ChurchLocation.objects.first()

    if not church_location:
        messages.error(request, "⚠️ No church location found to delete.")
        print("❌ No church location exists.")
        return redirect("view_church_location")  # Redirect to map view if no location exists

    if request.method == "POST":
        print(f"🗑️ Deleting Church Location: {church_location.latitude}, {church_location.longitude}")
        church_location.delete()
        messages.success(request, "✅ Church location has been deleted successfully.")
        return redirect("view_church_location")  # Redirect after successful deletion

    return render(request, "settings/delete_church_location.html", {"church_location": church_location})

