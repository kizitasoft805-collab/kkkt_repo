# accounts/middleware.py

from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse
from .models import LoginHistory
from .views import get_client_ip, get_ignored_paths, get_user_last_path

class LastPathMiddleware(MiddlewareMixin):
    """
    Middleware to store the last visited path for authenticated users
    in both session and LoginHistory. Ensures ignored paths are not stored.
    """

    def process_request(self, request):
        user = request.user
        if user.is_authenticated:
            path = request.path

            # 🛑 List of ignored paths (redirect user to dashboard instead)
            ignored_paths = get_ignored_paths()

            # If the user is on an ignored path, remove last_visited_path from session
            if path in ignored_paths:
                request.session.pop('last_visited_path', None)
                return None  # Do not store these paths

            # ✅ Store last visited path in session for redirection after logout/login
            request.session['last_visited_path'] = path

            # ✅ Update the latest LoginHistory record for this user
            try:
                last_login_record = user.login_history.latest('login_time')
                last_login_record.last_visited_path = path
                last_login_record.save(update_fields=['last_visited_path'])
            except LoginHistory.DoesNotExist:
                pass  # No login record exists yet

        return None
