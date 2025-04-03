# accounts/admin.py
from django.contrib import admin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone_number', 'user_type', 'date_created')
    list_filter = ('user_type', 'date_created')
    search_fields = ('username', 'email', 'phone_number')
    readonly_fields = ('date_created',)
