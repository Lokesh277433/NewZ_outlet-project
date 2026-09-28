from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import AdminUserChangeForm, AdminUserCreationForm
from .models import OTPRequestLog, PasswordResetOTP, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    form = AdminUserChangeForm
    add_form = AdminUserCreationForm
    ordering = ('email',)
    list_display = (
        'email', 'first_name', 'last_name', 'is_staff',
        'is_superuser', 'auto_approve', 'is_active',
    )
    search_fields = ('email', 'first_name', 'last_name', 'username')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name', 'bio', 'avatar')}),
        ('Newsroom', {'fields': ('auto_approve',)}),
        ('Permissions', {'fields': (
            'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',
        )}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'expires_at', 'verified_at', 'used_at', 'attempts']
    readonly_fields = ['code_hash', 'created_at']


@admin.register(OTPRequestLog)
class OTPRequestLogAdmin(admin.ModelAdmin):
    list_display = ['email', 'ip_address', 'created_at']
    readonly_fields = ['email', 'ip_address', 'created_at']
