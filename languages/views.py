from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import LanguageSetting
from .forms import LanguageSelectForm
from members.models import ChurchMember
from leaders.models import Leader

@login_required
def select_language_view(request):
    """
    Allows the user to select a language (English or Kiswahili).
    Saves the result in the LanguageSetting model, then redirects
    to different dashboards based on user type/leader occupation.
    """
    # 1) Get or create the user's LanguageSetting
    language_setting, created = LanguageSetting.objects.get_or_create(user=request.user)

    # 2) Decide which template to use, based on user type and leader occupation
    if request.user.is_superuser or request.user.user_type == 'ADMIN':
        template_name = 'languages/select_language_admin.html'
        dashboard_redirect = 'admin_dashboard'
    else:
        # It's a CHURCH_MEMBER user
        # Check if they are a leader and what occupation
        if request.user.church_member and request.user.church_member.is_the_member_a_leader_of_the_movement:
            # They are a leader, fetch occupation
            leader = getattr(request.user.church_member, 'leader', None)
            if leader and leader.occupation == 'Parish Council Secretary':
                template_name = 'languages/select_language_secretary.html'
                dashboard_redirect = 'secretary_dashboard'
            elif leader and leader.occupation == 'Parish Treasurer':
                template_name = 'languages/select_language_accountant.html'
                dashboard_redirect = 'accountant_dashboard'
            else:
                # Leader with a different occupation
                template_name = 'languages/select_language_member.html'
                dashboard_redirect = 'member_dashboard'
        else:
            # Normal church member, not a leader
            template_name = 'languages/select_language_member.html'
            dashboard_redirect = 'member_dashboard'

    if request.method == "POST":
        form = LanguageSelectForm(request.POST)
        if form.is_valid():
            selected_lang = form.cleaned_data['preferred_language']
            # Update booleans
            if selected_lang == 'en':
                language_setting.is_english = True
                language_setting.is_kiswahili = False
            else:
                language_setting.is_english = False
                language_setting.is_kiswahili = True

            language_setting.save()
            # Redirect to the chosen dashboard
            return redirect(dashboard_redirect)
    else:
        # Pre-fill the form
        initial_value = 'en' if language_setting.is_english else 'sw'
        form = LanguageSelectForm(initial={'preferred_language': initial_value})

    return render(request, template_name, {'form': form})
