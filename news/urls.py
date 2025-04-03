from django.urls import path
from .views import create_news_view, news_list_view, news_detail_view, delete_news_view, view_posts_public, like_news, submit_comment
from . import views

urlpatterns = [
    path("like/<int:news_id>/", like_news, name="like_news"),  # Remove "news/" from the path
    path('create/news/', create_news_view, name='create_news'),
    path('news/list/', news_list_view, name='news_list'),
    path("news/<int:pk>/", news_detail_view, name="news_detail"),
    path("news/<int:pk>/delete/", delete_news_view, name="delete_news"),
    path("news/<int:pk>/edit/", create_news_view, name="edit_news"),
    path("public-news/", view_posts_public, name="public_news_list"),
    path("comment/<int:news_id>/", submit_comment, name="submit_comment"),  # Ensure this is correct
    path('home/news/', views.news_home, name='news_home'),
]
