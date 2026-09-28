import random
import string

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import OTPRequestLog, PasswordResetOTP, hash_otp


def client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _window_start():
    minutes = getattr(settings, 'OTP_RATE_WINDOW_MINUTES', 15)
    return timezone.now() - timezone.timedelta(minutes=minutes)


def otp_rate_limited(email, ip):
    window = _window_start()
    email_limit = getattr(settings, 'OTP_MAX_PER_EMAIL', 3)
    ip_limit = getattr(settings, 'OTP_MAX_PER_IP', 10)
    email_count = OTPRequestLog.objects.filter(
        email__iexact=email, created_at__gte=window
    ).count()
    if email_count >= email_limit:
        return True
    if ip:
        ip_count = OTPRequestLog.objects.filter(
            ip_address=ip, created_at__gte=window
        ).count()
        if ip_count >= ip_limit:
            return True
    return False


def issue_otp(user, ip=None):
    PasswordResetOTP.objects.filter(user=user, used_at__isnull=True).update(
        used_at=timezone.now()
    )
    code = ''.join(random.choices(string.digits, k=6))
    minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
    otp = PasswordResetOTP.objects.create(
        user=user,
        code_hash=hash_otp(code, user.email),
        expires_at=timezone.now() + timezone.timedelta(minutes=minutes),
        request_ip=ip,
    )
    OTPRequestLog.objects.create(email=user.email, ip_address=ip)
    send_mail(
        subject='Your News Outlet password reset code',
        message=(
            f'Your password reset code is: {code}\n\n'
            f'This code expires in {minutes} minutes and can be used only once.\n'
            'If you did not request a reset, you can ignore this email.'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return otp
