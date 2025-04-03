from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.models import CustomUser
from members.models import ChurchMember
from accounts.decorators import church_member_required

# ✅ Helper function to allow only church members
def is_church_member(user):
    return user.is_authenticated and user.user_type == 'CHURCH_MEMBER'

@login_required
@user_passes_test(is_church_member)
def logged_member_details(request):
    """
    View to retrieve and display all details of the logged-in church member,
    including documents like baptism, communion, confirmation, and marriage certificates.
    """

    user = request.user  # Get logged-in user
    church_member = user.church_member  # Get church member linked to the user

    # ✅ Helper to format boolean values with icons
    def format_boolean(value):
        return '✅' if value else '❌'

    # 📋 Prepare context with formatted labels
    member_details = {
        "Username": user.username,
        "Full Name": church_member.full_name,
        "Member ID": church_member.member_id,
        "Date of Birth": church_member.date_of_birth,
        "Gender": church_member.gender,
        "Phone Number": church_member.phone_number,
        "Email": church_member.email or "Not provided",
        "Address": church_member.address,
        "Community": church_member.community.name if church_member.community else "Not Assigned",
        "Apostolic Movement": church_member.apostolic_movement.name if church_member.apostolic_movement else "Not Assigned",
        "Leader of Movement": format_boolean(church_member.is_the_member_a_leader_of_the_movement),
        "Baptized": format_boolean(church_member.is_baptised),
        "Date of Baptism": church_member.date_of_baptism or "Not Available",
        "Confirmed": format_boolean(church_member.is_confirmed),
        "Date Confirmed": church_member.date_confirmed or "Not Available",
        "Marital Status": church_member.marital_status,
        "Spouse Name": church_member.spouse_name or "Not provided",
        "Number of Children": church_member.number_of_children or "Not provided",
        "Job": church_member.job,
        "Talent": church_member.talent or "Not Provided",
        "Church Services": church_member.services or "Not Involved",
        "Emergency Contact Name": church_member.emergency_contact_name,
        "Emergency Contact Phone": church_member.emergency_contact_phone,
        "Disability": church_member.disability or "None",
        "Special Interests": church_member.special_interests or "None",
        "Passport": church_member.passport.url if church_member.passport else None,
        "Date Created": church_member.date_created.strftime("%d %B %Y"),
    }

    # 📂 Add Certificates
    certificates = {
        "Baptism Certificate": church_member.baptism_certificate.url if church_member.baptism_certificate else None,
        "Confirmation Certificate": church_member.confirmation_certificate.url if church_member.confirmation_certificate else None,
        "Marriage Certificate": church_member.marriage_certificate.url if church_member.marriage_certificate else None,
    }

    return render(request, "churchmember/logged_member_details.html", {
        "user": user,
        "member_details": member_details,
        "certificates": certificates,
    })



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from news.forms import NewsForm
from news.models import News, NewsMedia

def is_church_member(user):
    """
    Helper function to check if the user is a church member.
    """
    return user.is_authenticated and user.user_type == 'CHURCH_MEMBER'

@login_required
@user_passes_test(is_church_member)
def member_create_news_view(request, pk=None):
    """
    View to create or update a news post with multiple media uploads.
    Only accessible to church members.
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

            return redirect("member_news_list")  # Redirect to news list after saving
        else:
            messages.error(request, "❌ Please correct the errors in the form.")

    else:
        form = NewsForm(instance=news)  # Pre-fill form if updating

    return render(request, "churchmember/member_create_news.html", {"form": form, "news": news})

from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import timedelta
from news.models import News

# ✅ Helper function to allow only church members
def is_church_member(user):
    return user.is_authenticated and user.user_type == 'CHURCH_MEMBER'

# 🕰️ Time calculation helper
def calculate_time_since(created_at):
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

# 📋 View: Member News List (Restricted to Church Members)
@login_required
@user_passes_test(is_church_member)
def member_news_list_view(request):
    news_list = News.objects.all()

    # Add "time since created" for each news item
    for news in news_list:
        news.time_since_created = calculate_time_since(news.created_at)

    return render(request, "churchmember/member_news_list.html", {"news_list": news_list})

# 📄 View: Member News Detail (Restricted to Church Members)
@login_required
@user_passes_test(is_church_member)
def member_news_detail_view(request, pk):
    news = get_object_or_404(News, pk=pk)
    news.time_since_created = calculate_time_since(news.created_at)

    # Separate media types
    images = news.media.filter(media_type='image')
    videos = news.media.filter(media_type='video')
    documents = news.media.filter(media_type='document')

    return render(request, "churchmember/member_news_detail.html", {
        "news": news,
        "images": images,
        "videos": videos,
        "documents": documents,
    })


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from news.models import News, NewsMedia

# ✅ Helper function to allow only church members
def is_church_member(user):
    return user.is_authenticated and user.user_type == 'CHURCH_MEMBER'

# 🗑️ View: Member Delete News (Restricted to Church Members)
@login_required
@user_passes_test(is_church_member)
def member_delete_news_view(request, pk):
    """
    View to delete a news article and all associated media.
    Only accessible to logged-in church members.
    """
    news = get_object_or_404(News, pk=pk)

    if request.method == "POST":
        # Delete all associated media files
        news.media.all().delete()
        
        # Delete the news post
        news.delete()

        messages.success(request, "🗑️ News post and all associated media deleted successfully!")
        return redirect("member_news_list")

    return render(request, "churchmember/member_delete_news.html", {"news": news})


from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from notifications.models import Notification

# ✅ Helper function to allow only church members
def is_church_member(user):
    return user.is_authenticated and user.user_type == 'CHURCH_MEMBER'

@login_required
@user_passes_test(is_church_member)
def member_notifications_view(request):
    """
    View to retrieve all notifications for the logged-in church member.
    Automatically marks all unread notifications as read when accessed.
    """
    user = request.user
    church_member = user.church_member

    # ✅ Get notifications for the logged-in church member only
    notifications = Notification.objects.filter(church_member=church_member).order_by('-created_at')

    # ✅ Mark unread notifications (for this member only) as read
    notifications.filter(is_read=False).update(is_read=True)

    return render(request, "churchmember/member_notifications.html", {
        "notifications": notifications,
    })


from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

# ✅ Helper function to allow only church members
def is_church_member(user):
    return user.is_authenticated and user.user_type == 'CHURCH_MEMBER'

@login_required
@user_passes_test(is_church_member)
def member_tithes_view(request):
    """
    View to retrieve all tithes for the logged-in church member.
    """
    user = request.user
    church_member = user.church_member

    # Get all tithes for the logged-in church member
    tithes = Tithe.objects.filter(member=church_member).order_by('-date_given')

    return render(request, "churchmember/member_tithes.html", {
        "tithes": tithes,
    })

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
@church_member_required
def chatbot_view(request):
    user = request.user

    # Predefined questions and answers
    faq = {
        "How can I see my details?": "You can see your details by simply pressing the dashboard details box, or using the sidebar by pressing the toggle button and then pressing the details button, or using the arrow icon located at the bottom right-hand side of your viewport by pressing it and then selecting the details button.",
        "How can I see the posts?": "You can see and create the posts by just simply pressing the Posts box in your dashboard, or pressing the toggle button of the sidebar located at the top-left-hand side then press the posts button, or using the bottom bar by pressing the arrow icon located at the bottom right-hand side then pressing the posts button.",
        "How can I see the notifications?": "You can see the notifications by pressing the notifications button on your dashboard, the sidebar toggle button, or the bottom bar arrow icon.",
        "How can I see my tithe history?": "You can see your tithe history by pressing the tithe history button on your dashboard, the sidebar toggle button, or the bottom bar arrow icon.",
        "How can I create my posts?": "You can create posts by going to the posts list and then pressing the create new post button. You will visit the page for creating a post. Note that you cannot update or delete your post. Make sure your posts are related to religious matters.",
        "How can I get more support?": "You can get more support by contacting the church directly via email at <a href='mailto:kigangomkwawa123@gmail.com'>kigangomkwawa123@gmail.com</a> or by calling <a href='tel:+255767972343'>+255767972343</a>.",
        "Where can I get services like this?": "You can get services like this by contacting Kizitasoft Company Limited at <a href='tel:+255762023662'>+255762023662</a>, <a href='tel:+255741943155'>+255741943155</a>, or <a href='tel:+255763968849'>+255763968849</a>. You can also reach them via email at <a href='mailto:kizitasoft805@gmail.com'>kizitasoft805@gmail.com</a> or <a href='mailto:kizitasoft@gmail.com'>kizitasoft@gmail.com</a>."
    }

    context = {
        "user": user,
        "faq": faq
    }
    return render(request, "churchmember/chatbot.html", context)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def public_chatbot_view(request):

    # Predefined questions and answers
    faq = {
        "How can i request an account?": "You can request an account by simply pressing the request account button of the button located at the bottom right hand side of the viewport, make sure you rember your member id which is sent as a message when you are registered in the application or if you dont rember you can ask the admin or the chairman of the church, then in the page to request the account you will be asked to einter your id if it is valid then you will enter your prefference username, and password to get your account.",
        "How can I see the posts?": "You can see and create the posts by just using the bottom bar by pressing the arrow icon located at the bottom right-hand side then pressing the posts button.",
        "How can I recorver the forgiten username & password?": "You can get the new username and password by going to the forgot password, then in the page you will be asked to enter the new username, the new password and confirm the new password, then these will be your new username and new password that you can use to loggin.",
        "How can i see the church in the map & my location?": "You can see the church location and your location by pressing the arrow icon at the bottom of the viewport then press view in map button then you will see the church in the map, and if want to know your location then you will see by pressing the location red icon then your location will be shown",
        "How can I see and create my comments and likes?": "You can create the comments & likes of the posts by pressing the message icon of the given post then the comment section will come, and if you want to like then you can just press the like heart icon then your like will be saved and conted.",
        "How can I get more support?": "You can get more support by contacting the church directly via email at <a href='mailto:kigangomkwawa123@gmail.com'>kigangomkwawa123@gmail.com</a> or by calling <a href='tel:+255767972343'>+255767972343</a>.",
        "Where can I get services like this?": "You can get services like this by contacting Kizitasoft Company Limited at <a href='tel:+255762023662'>+255762023662</a>, <a href='tel:+255741943155'>+255741943155</a>, or <a href='tel:+255763968849'>+255763968849</a>. You can also reach them via email at <a href='mailto:kizitasoft805@gmail.com'>kizitasoft805@gmail.com</a> or <a href='mailto:kizitasoft@gmail.com'>kizitasoft@gmail.com</a>."
    }

    context = {
        "faq": faq
    }
    return render(request, "churchmember/public_chatbot.html", context)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.decorators import admin_required

@login_required
@admin_required  # 🔒 Requires authentication
def admin_chatbot_view(request):
    """
    🤖 Admin Chatbot View for Quick FAQs

    - Provides instant responses to common admin queries.
    - Ensures secure access with login required.
    - Supports clickable links for easy contact.
    """
    print("🤖 Loading Admin Chatbot...")

    # Predefined FAQs (Frequently Asked Questions)
    faq = {
        "How can I register a church member?": (
            "You can register a member by going to the Member List page. "
            "Click on the Members box from your dashboard (Admin/Superuser), "
            "or use the toggle button (three bars icon) to access Members. "
            "Then click 'Create New Member' and fill out the form."
        ),
        "How can I register leaders?": (
            "Go to the Leaders page and click 'Create New Leader'. "
            "Fill in the leader's credentials and save."
        ),
        "How can I send messages and notifications to church members?": (
            "Navigate to the Notifications page and click 'Send SMS & Notification'. "
            "Fill in the title, message, select recipients, and send."
        ),
        "How can I create the church location on the map?": (
            "Go to Settings > Church Location. Click the '+' icon to open the map. "
            "Select the location, and the latitude/longitude will be saved automatically."
        ),
        "What is Finance specialized with?": (
            "Finance manages all aspects related to the church's income and financial records."
        ),
        "Am I required to update settings all the time?": (
            "No, only when necessary. For example, update the current year when a new year starts."
        ),
        "What is Sacraments based on?": (
            "Sacraments manage records for Baptism, First Communion, Confirmation, and Marriage."
        ),
        "What rules should I follow when registering a church member?": (
            "Ensure logical consistency: "
            "- A member with First Communion must be baptized. "
            "- A married member should be confirmed and have received sacraments in sequence."
        ),
        "What if I make mistakes when registering or saving data?": (
            "You can correct mistakes by clicking the 'Edit' (pencil) icon, "
            "making changes, and saving the update."
        ),
        "What do the Eye, Pencil, and Trash icons mean?": (
            "👁️ Eye: View details\n"
            "✏️ Pencil: Edit/Update\n"
            "🗑️ Trash: Delete the record"
        ),
        "How can I get more support?": (
            "📧 Email: <a href='mailto:kigangomkwawa123@gmail.com'>kigangomkwawa123@gmail.com</a><br>"
            "📞 Call: <a href='tel:+255767972343'>+255767972343</a>"
        ),
        "Where can I get services like this?": (
            "Contact Kizita Soft Limited:<br>"
            "📞 <a href='tel:+255762023662'>+255762023662</a>, "
            "<a href='tel:+255741943155'>+255741943155</a>, "
            "<a href='tel:+255763968849'>+255763968849</a><br>"
            "📧 Email: <a href='mailto:kizitasoft805@gmail.com'>kizitasoft805@gmail.com</a>, "
            "<a href='mailto:kizitasoft@gmail.com'>kizitasoft@gmail.com</a>"
        )
    }

    print(f"✅ Loaded {len(faq)} FAQ entries.")

    context = {
        "faq": faq
    }
    return render(request, "churchmember/admin_chatbot.html", context)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.decorators import admin_required

@login_required
def secretary_chatbot_view(request):
    """
    🤖 Admin Chatbot View for Quick FAQs

    - Provides instant responses to common admin queries.
    - Ensures secure access with login required.
    - Supports clickable links for easy contact.
    """
    print("🤖 Loading Admin Chatbot...")

    # Predefined FAQs (Frequently Asked Questions)
    faq = {
        "How can I register a church member?": (
            "You can register a member by going to the Member List page. "
            "Click on the Members box from your dashboard (Admin/Superuser), "
            "or use the toggle button (three bars icon) to access Members. "
            "Then click 'Create New Member' and fill out the form."
        ),
        "How can I register leaders?": (
            "Go to the Leaders page and click 'Create New Leader'. "
            "Fill in the leader's credentials and save."
        ),
        "How can I send messages and notifications to church members?": (
            "Navigate to the Notifications page and click 'Send SMS & Notification'. "
            "Fill in the title, message, select recipients, and send."
        ),
        "How can I create the church location on the map?": (
            "Go to Settings > Church Location. Click the '+' icon to open the map. "
            "Select the location, and the latitude/longitude will be saved automatically."
        ),
        "What is Finance specialized with?": (
            "Finance manages all aspects related to the church's income and financial records."
        ),
        "Am I required to update settings all the time?": (
            "No, only when necessary. For example, update the current year when a new year starts."
        ),
        "What is Sacraments based on?": (
            "Sacraments manage records for Baptism, First Communion, Confirmation, and Marriage."
        ),
        "What rules should I follow when registering a church member?": (
            "Ensure logical consistency: "
            "- A member with First Communion must be baptized. "
            "- A married member should be confirmed and have received sacraments in sequence."
        ),
        "What if I make mistakes when registering or saving data?": (
            "You can correct mistakes by clicking the 'Edit' (pencil) icon, "
            "making changes, and saving the update."
        ),
        "What do the Eye, Pencil, and Trash icons mean?": (
            "👁️ Eye: View details\n"
            "✏️ Pencil: Edit/Update\n"
            "🗑️ Trash: Delete the record"
        ),
        "How can I get more support?": (
            "📧 Email: <a href='mailto:kigangomkwawa123@gmail.com'>kigangomkwawa123@gmail.com</a><br>"
            "📞 Call: <a href='tel:+255767972343'>+255767972343</a>"
        ),
        "Where can I get services like this?": (
            "Contact Kizita Soft Limited:<br>"
            "📞 <a href='tel:+255762023662'>+255762023662</a>, "
            "<a href='tel:+255741943155'>+255741943155</a>, "
            "<a href='tel:+255763968849'>+255763968849</a><br>"
            "📧 Email: <a href='mailto:kizitasoft805@gmail.com'>kizitasoft805@gmail.com</a>, "
            "<a href='mailto:kizitasoft@gmail.com'>kizitasoft@gmail.com</a>"
        )
    }

    print(f"✅ Loaded {len(faq)} FAQ entries.")

    context = {
        "faq": faq
    }
    return render(request, "secretary/churchmember/chatbot.html", context)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.decorators import admin_required

@login_required
def accountant_chatbot_view(request):
    """
    🤖 Admin Chatbot View for Quick FAQs

    - Provides instant responses to common admin queries.
    - Ensures secure access with login required.
    - Supports clickable links for easy contact.
    """
    print("🤖 Loading Admin Chatbot...")

    # Predefined FAQs (Frequently Asked Questions)
    faq = {
        "How can I register a church member?": (
            "You can register a member by going to the Member List page. "
            "Click on the Members box from your dashboard (Admin/Superuser), "
            "or use the toggle button (three bars icon) to access Members. "
            "Then click 'Create New Member' and fill out the form."
        ),
        "How can I register leaders?": (
            "Go to the Leaders page and click 'Create New Leader'. "
            "Fill in the leader's credentials and save."
        ),
        "How can I send messages and notifications to church members?": (
            "Navigate to the Notifications page and click 'Send SMS & Notification'. "
            "Fill in the title, message, select recipients, and send."
        ),
        "How can I create the church location on the map?": (
            "Go to Settings > Church Location. Click the '+' icon to open the map. "
            "Select the location, and the latitude/longitude will be saved automatically."
        ),
        "What is Finance specialized with?": (
            "Finance manages all aspects related to the church's income and financial records."
        ),
        "Am I required to update settings all the time?": (
            "No, only when necessary. For example, update the current year when a new year starts."
        ),
        "What is Sacraments based on?": (
            "Sacraments manage records for Baptism, First Communion, Confirmation, and Marriage."
        ),
        "What rules should I follow when registering a church member?": (
            "Ensure logical consistency: "
            "- A member with First Communion must be baptized. "
            "- A married member should be confirmed and have received sacraments in sequence."
        ),
        "What if I make mistakes when registering or saving data?": (
            "You can correct mistakes by clicking the 'Edit' (pencil) icon, "
            "making changes, and saving the update."
        ),
        "What do the Eye, Pencil, and Trash icons mean?": (
            "👁️ Eye: View details\n"
            "✏️ Pencil: Edit/Update\n"
            "🗑️ Trash: Delete the record"
        ),
        "How can I get more support?": (
            "📧 Email: <a href='mailto:kigangomkwawa123@gmail.com'>kigangomkwawa123@gmail.com</a><br>"
            "📞 Call: <a href='tel:+255767972343'>+255767972343</a>"
        ),
        "Where can I get services like this?": (
            "Contact Kizita Soft Limited:<br>"
            "📞 <a href='tel:+255762023662'>+255762023662</a>, "
            "<a href='tel:+255741943155'>+255741943155</a>, "
            "<a href='tel:+255763968849'>+255763968849</a><br>"
            "📧 Email: <a href='mailto:kizitasoft805@gmail.com'>kizitasoft805@gmail.com</a>, "
            "<a href='mailto:kizitasoft@gmail.com'>kizitasoft@gmail.com</a>"
        )
    }

    print(f"✅ Loaded {len(faq)} FAQ entries.")

    context = {
        "faq": faq
    }
    return render(request, "accountant/churchmember/chatbot.html", context)


# finance/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser
from members.models import ChurchMember
from .forms import MemberPledgeForm

@login_required
@church_member_required
def member_pledge_create_view(request):
    """
    Allows a logged-in CHURCH_MEMBER to create a pledge for themselves.
    """
    # Ensure user is a CHURCH_MEMBER (optional check, if you want to restrict)
    if request.user.user_type != "CHURCH_MEMBER":
        messages.error(request, "Only Church Members can create pledges here.")
        return redirect("pledge_list")  # or some other page

    # Get the ChurchMember linked to this user
    church_member = request.user.church_member  

    if request.method == "POST":
        form = MemberPledgeForm(request.POST, member=church_member)
        if form.is_valid():
            form.save()
            messages.success(request, "Pledge successfully recorded!")
            return redirect("member_pledge_list")  
            # or redirect anywhere you prefer
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = MemberPledgeForm(member=church_member)

    context = {
        "form": form,
        "church_member": church_member,  # So we can display name/phone/address
    }
    return render(request, "churchmember/member_pledge_form.html", context)


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from finance.models import Pledge
from settings.models import Year
from accounts.models import CustomUser

@login_required
def member_pledge_list_view(request):
    """
    Lists all pledges for the currently logged-in church member.
    Includes additional context (all_years, months_list, current_year_val)
    needed for filtering in the template.
    """
    # Optionally, ensure user is CHURCH_MEMBER
    if request.user.user_type != "CHURCH_MEMBER":
        messages.error(request, "Only Church Members can view this page.")
        return redirect("member_dashboard")

    # Get the ChurchMember linked to this user
    church_member = request.user.church_member

    # Retrieve all pledges for this member
    pledges = Pledge.objects.filter(member=church_member).order_by('-date_created')

    # Fetch all Year objects from the database for the "Filter by Year" dropdown
    all_years = Year.objects.all().order_by('year')

    # Hardcode the 12 months in Python for the "Filter by Month" dropdown
    months_list = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    # Get the "current" year if it exists, so we can default the filter
    current_year_obj = Year.objects.filter(is_current=True).first()
    current_year_val = str(current_year_obj.year) if current_year_obj else ""

    context = {
        "church_member": church_member,
        "pledges": pledges,
        "all_years": all_years,
        "months_list": months_list,
        "current_year_val": current_year_val,  # for pre-selecting the year filter
    }
    return render(request, "churchmember/member_pledge_list.html", context)
