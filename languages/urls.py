# languages/urls.py

from django.urls import path
from .views import select_language_view


urlpatterns = [
    path('select/', select_language_view, name='select_language'),
]
