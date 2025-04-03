from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from .models import ChurchAsset
from .forms import ChurchAssetFormSet
from datetime import datetime
import pytz
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .utils import get_properties_radar_analysis

# ✅ Helper Function: Check if user is Admin or Superuser
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required(login_url='login')
@user_passes_test(is_admin_or_superuser, login_url='login')
def properties_home(request):
    """
    View for the Properties home page, displaying church properties section.
    Accessible only by Admins and Superusers.
    """
    properties_radar_data = get_properties_radar_analysis()

    return render(request, 'properties/properties_home.html', {
        'properties_radar_data': properties_radar_data
    })

# 🏗️ View: Create Church Assets (Restricted)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def create_church_assets(request):
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
            return redirect('upload_church_asset_media')
        else:
            messages.error(request, 'Failed to save assets. Please correct the errors below.')
    else:
        formset = ChurchAssetFormSet()

    return render(request, 'properties/create_church_assets.html', {'formset': formset})


# 📊 View: Display Church Assets (Restricted)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def church_assets_view(request):
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

    return render(request, 'properties/church_assets_list.html', {
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

from .models import ChurchAsset, ChurchAssetMedia
from .forms import UpdateChurchAssetForm

# ✅ Access Control for Admins & Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

# 🌍 Timezone for Tanzania
TZ_TZ = pytz.timezone('Africa/Dar_es_Salaam')


# 🔄 Update Church Asset (Restricted)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def update_church_asset(request, asset_id):
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
            return redirect('church_assets_list')
        else:
            messages.error(request, "❌ Failed to update asset. Please correct the errors.")
    else:
        form = UpdateChurchAssetForm(instance=church_asset)

    return render(request, 'properties/update_church_asset.html', {
        'form': form,
        'church_asset': church_asset
    })


# 📋 Church Asset Details (Restricted)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def church_asset_detail(request, asset_id):
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

    return render(request, "properties/church_asset_detail.html", {
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

from .models import ChurchAsset, ChurchAssetMedia
from .forms import ChurchAssetMediaForm

# ✅ Access Control for Admins & Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')


# 🚮 Delete Church Asset (Restricted)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def delete_church_asset(request, asset_id):
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
        return redirect('church_assets_list')

    return render(request, 'properties/church_asset_confirm_delete.html', {
        'church_asset': church_asset,
    })


# 📤 Upload Additional Media for Church Asset (Restricted)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def upload_additional_church_asset_media(request, asset_id):
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
                return redirect('church_asset_detail', asset_id=church_asset.id)
            else:
                messages.warning(request, "⚠️ No media uploaded. Please select an image.")

        else:
            messages.error(request, "❌ Failed to upload media. Please check the form.")

    else:
        formset = ChurchAssetMediaFormSet(queryset=existing_media)

    return render(request, 'properties/upload_additional_church_asset_media.html', {
        'formset': formset,
        'church_asset': church_asset,
        'existing_media': existing_media,
    })


# 🗑️ Delete Church Asset Media (Restricted)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def delete_church_asset_media(request, media_id):
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
from .models import ChurchAsset, ChurchAssetMedia
from .forms import ChurchAssetMediaForm


# ✅ Access Control for Admins & Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')


# 📤 Upload Media for Church Assets (Restricted)
@login_required
@user_passes_test(is_admin_or_superuser, login_url='login')
def upload_church_asset_media(request):
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

        return redirect('church_assets_list')  # Redirect to the assets list

    return render(request, 'properties/upload_church_asset_media.html', {
        'latest_assets': latest_assets,
        'total_assets': total_assets,
    })
