from django.shortcuts import redirect
from django.urls import reverse

class ParishTreasurerRequiredMixin:
    """
    Mixin to restrict access to:
    - Church Members
    - Leaders with the occupation 'Parish Treasurer'
    Redirects unauthorized users to the login page.
    """

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        # Check if the user is authenticated, a church member, and a leader with 'Parish Treasurer' occupation
        if (
            user.is_authenticated
            and user.user_type == 'CHURCH_MEMBER'
            and hasattr(user, 'church_member')
            and hasattr(user.church_member, 'leader')
            and user.church_member.leader.occupation == 'Parish Treasurer'
        ):
            return super().dispatch(request, *args, **kwargs)
        
        # Redirect unauthorized users to the login page
        return redirect(f"{reverse('login')}?next={request.path}")
