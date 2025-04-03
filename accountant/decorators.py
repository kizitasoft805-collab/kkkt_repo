from django.core.exceptions import PermissionDenied

def parish_treasurer_required(view_func):
    """
    Decorator to allow access only to church members 
    who are leaders and Parish Treasurers.
    """
    def _wrapped_view(request, *args, **kwargs):
        user = request.user

        # Ensure the user is authenticated and a church member
        if not user.is_authenticated or user.user_type != 'CHURCH_MEMBER':
            raise PermissionDenied("Access denied. You must be a church member.")

        # Check if the user is a leader
        church_member = user.church_member
        if not hasattr(church_member, 'leader'):
            raise PermissionDenied("Access denied. You are not a leader.")

        # Verify the leader's occupation
        if church_member.leader.occupation != 'Parish Treasurer':
            raise PermissionDenied("Access denied. Only Parish Treasurers can view this page.")

        return view_func(request, *args, **kwargs)

    return _wrapped_view
