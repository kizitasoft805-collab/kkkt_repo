from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import NewsForm, NewsMediaForm
from .models import News, NewsMedia

def is_admin_or_superuser(user):
    """
    Helper function to check if the user is a superuser or an admin.
    """
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required
@user_passes_test(is_admin_or_superuser)
def create_news_view(request, pk=None):
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

            return redirect("news_list")  # Redirect to news list after saving
        else:
            messages.error(request, "❌ Please correct the errors in the form.")

    else:
        form = NewsForm(instance=news)  # Pre-fill form if updating

    return render(request, "news/create_news.html", {"form": form, "news": news})

from django.shortcuts import render
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import timedelta
from .models import News

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
@user_passes_test(lambda user: user.is_superuser or user.user_type == 'ADMIN')
def news_list_view(request):
    """
    View to display a list of news articles (without media) with the time since creation.
    Only accessible to superusers and admins.
    """
    news_list = News.objects.all()

    # Calculate "time since created" for each news
    for news in news_list:
        news.time_since_created = calculate_time_since(news.created_at)

    return render(request, "news/news_list.html", {"news_list": news_list})

from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import News

# ✅ Helper function to allow only Admins and Superusers
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

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
@user_passes_test(is_admin_or_superuser, login_url='login')
def news_detail_view(request, pk):
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

    return render(request, "news/news_detail.html", {
        "news": news,
        "images": images,
        "videos": videos,
        "documents": documents,
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import News, NewsMedia

# Helper function to check if user is an admin or superuser
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required
@user_passes_test(is_admin_or_superuser)
def delete_news_view(request, pk):
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
        return redirect("news_list")

    return render(request, "news/delete_news.html", {"news": news})

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from datetime import timedelta
from .models import News, Like
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils.timezone import now
from datetime import timedelta
from .models import News, Like, Comment

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

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils.timezone import now
from datetime import timedelta
from .models import News, Like, Comment

def view_posts_public(request):
    """
    Publicly accessible view to display a list of news articles.
    """
    news_list = News.objects.all()

    liked_news_ids = request.COOKIES.get("liked_news", "").split(",") if request.COOKIES.get("liked_news") else []

    for news in news_list:
        news.time_since_created = calculate_time_since(news.created_at)
        news.like_count = news.likes.count()
        news.comment_count = news.comments.count()
        news.user_has_liked = str(news.id) in liked_news_ids

    response = render(request, "news/public_news_list.html", {"news_list": news_list})
    return response

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils.timezone import now
from datetime import timedelta
from .models import News, Like, Comment

def view_posts_public(request):
    """
    Publicly accessible view to display a list of news articles.
    """
    news_list = News.objects.all()

    liked_news_ids = request.COOKIES.get("liked_news", "").split(",") if request.COOKIES.get("liked_news") else []

    for news in news_list:
        news.time_since_created = calculate_time_since(news.created_at)
        news.like_count = news.likes.count()
        news.comment_count = news.comments.count()
        news.user_has_liked = str(news.id) in liked_news_ids

    response = render(request, "news/public_news_list.html", {"news_list": news_list})
    return response

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@csrf_exempt  # Only for debugging, remove this in production
def like_news(request, news_id):
    """
    Handles the liking of a news article via AJAX.
    Uses cookies to track likes persistently.
    """
    if request.method == "POST":
        news = get_object_or_404(News, id=news_id)

        # Get liked news from cookies (Convert from string to list)
        liked_news_ids = request.COOKIES.get("liked_news", "").split(",") if request.COOKIES.get("liked_news") else []

        if str(news_id) in liked_news_ids:
            liked_news_ids.remove(str(news_id))  # Unlike
            liked = False
        else:
            liked_news_ids.append(str(news_id))  # Like
            liked = True

        # Update database tracking for session-based likes
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key

        if liked:
            Like.objects.get_or_create(news=news, session_id=session_id)
        else:
            Like.objects.filter(news=news, session_id=session_id).delete()

        # Convert list back to string
        liked_news_str = ",".join(liked_news_ids)

        response = JsonResponse({"liked": liked, "total_likes": news.likes.count()})
        response.set_cookie("liked_news", liked_news_str, max_age=365 * 24 * 60 * 60)  # Store for 1 year

        return response

    return JsonResponse({"error": "Invalid request"}, status=400)

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # Remove this in production
def submit_comment(request, news_id):
    """
    Handles AJAX submission of comments.
    """
    if request.method == "POST":
        news = get_object_or_404(News, id=news_id)
        comment_text = request.POST.get("comment_text", "").strip()
        name = request.POST.get("name", "Anonymous").strip()

        if comment_text:
            comment = Comment.objects.create(news=news, name=name, comment_text=comment_text)
            return JsonResponse({
                "success": True,
                "comment_id": comment.id,
                "name": comment.name,
                "text": comment.comment_text,
                "created_at": comment.created_at.strftime("%b %d, %Y %H:%M"),
                "total_comments": news.comments.count()
            })

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import News  # <-- Import News model

def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == 'ADMIN')

@login_required(login_url='login')
@user_passes_test(is_admin_or_superuser, login_url='login')
def news_home(request):
    """
    View for the News Home Page.
    Only accessible to Admins and Superusers.
    """
    # 📰 Retrieve total number of news articles
    news_count = News.objects.count()

    return render(request, 'news/news_home.html', {
        'news_count': news_count
    })
