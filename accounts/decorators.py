# accounts/decorators.py

from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def church_member_required(view_func):
    """
    Decorator to ensure the view is accessible only by Church Members.
    Redirects to the dashboard with an error message if the user is not a Church Member.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.user_type == 'CHURCH_MEMBER':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "❌ You are not authorized to access this page.")
            return redirect('login')  # Redirect non-members to a safe page
    return _wrapped_view


def admin_required(view_func):
    """
    Decorator to restrict access to Admins and Superusers only.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.user_type == 'ADMIN' or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "🚫 You are not authorized to access this page.")
            return redirect('login')  # Redirect unauthorized users to the member dashboard
    return _wrapped_view