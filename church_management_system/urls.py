from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# 1. Import the login view
from accounts.views import welcome_page
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    # 2. Make the root URL ('') point to the login view
    path('', welcome_page, name='welcome'),

    path('accounts/', include('accounts.urls')),
    path('settings/', include('settings.urls')),
    path('members/', include('members.urls')),
    path('leaders/', include('leaders.urls')),
    path('news/', include('news.urls')),
    path('finance/', include('finance.urls')),
    path('sacraments/', include('sacraments.urls')),
    path('properties/', include('properties.urls')),
    path('notifications/', include('notifications.urls')),
    path('sms/', include('sms.urls')),
    path('churchmember/', include('churchmember.urls')),
    path('secretary/', include('secretary.urls')),
    path('accountant/', include('accountant.urls')),
    path('analysis/', include('analysis.urls')),
    path('i18n/', include('django.conf.urls.i18n')),  # For language switching
    path('languages/', include('languages.urls')),
    path('pastor/', include('pastor.urls')),
    path('evengelist/', include('evangelist.urls'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)