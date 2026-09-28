from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import (
    ForgotPasswordForm,
    LoginForm,
    OTPVerifyForm,
    ProfileForm,
    RegisterForm,
    ResetPasswordForm,
    StyledPasswordChangeForm,
)
from .models import OTPRequestLog, PasswordResetOTP, User
from .otp import client_ip, issue_otp, otp_rate_limited
from .permissions import READER_GROUP


def post_login_url(user, next_url=None):
    if next_url:
        return next_url
    if user.is_superuser or user.is_staff:
        return reverse('news:newsroom_dashboard')
    return reverse('news:home')




def login_view(request):
    if request.user.is_authenticated:
        return redirect(post_login_url(request.user))
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user,backend='accounts.backends.EmailBackend')



            messages.success(request, 'You are now signed in.')
            next_url = request.GET.get('next')
            return redirect(post_login_url(user, next_url))
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()

            reader_group = Group.objects.get(name="Reader")
            user.groups.add(reader_group)

            login(
                request,
                user,
                backend="accounts.backends.EmailBackend"
            )

            return redirect("news:home")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been signed out.')
    return redirect('news:home')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)
    password_form = StyledPasswordChangeForm(user=request.user)
    bookmarks = request.user.bookmarks.select_related('article', 'article__category')[:12]
    return render(request, 'accounts/profile.html', {
        'form': form,
        'password_form': password_form,
        'bookmarks': bookmarks,
    })


@login_required
@require_POST
def change_password_view(request):
    form = StyledPasswordChangeForm(user=request.user, data=request.POST)
    ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        if ajax:
            return JsonResponse({'success': True, 'message': 'Password updated.'})
        messages.success(request, 'Password updated.')
        return redirect('accounts:profile')
    if ajax:
        errors = {field: errs[0] for field, errs in form.errors.items()}
        return JsonResponse({'success': False, 'errors': errors}, status=400)
    messages.error(request, 'Could not update password. Check the form and try again.')
    return redirect('accounts:profile')


def forgot_password_view(request):
    if request.user.is_authenticated:
        return redirect('news:home')
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            ip = client_ip(request)
            if otp_rate_limited(email, ip):
                messages.error(
                    request,
                    'Too many reset requests. Please wait a few minutes and try again.',
                )
                return render(request, 'accounts/forgot_password.html', {'form': form})
            user = User.objects.filter(email__iexact=email).first()
            if user:
                try:
                    issue_otp(user, ip=ip)
                except Exception:
                    messages.error(request, 'Could not send the reset email. Try again later.')
                    return render(request, 'accounts/forgot_password.html', {'form': form})
            else:
                OTPRequestLog.objects.create(email=email, ip_address=ip)
            request.session['password_reset_email'] = email
            messages.success(
                request,
                'If an account exists for that email, a 6-digit code has been sent.',
            )
            return redirect('accounts:verify_otp')
    else:
        form = ForgotPasswordForm()
    return render(request, 'accounts/forgot_password.html', {'form': form})


def verify_otp_view(request):
    if request.user.is_authenticated:
        return redirect('news:home')
    email = request.session.get('password_reset_email')
    if not email:
        return redirect('accounts:forgot_password')
    if request.method == 'POST':
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            user = User.objects.filter(email__iexact=email).first()
            otp = (
                PasswordResetOTP.objects.filter(user=user, used_at__isnull=True).first()
                if user else None
            )
            max_attempts = getattr(settings, 'OTP_MAX_VERIFY_ATTEMPTS', 5)
            if otp and otp.attempts >= max_attempts:
                messages.error(request, 'Too many incorrect attempts. Request a new code.')
                return redirect('accounts:forgot_password')
            if otp and otp.verify(form.cleaned_data['code']):
                request.session['password_reset_otp_id'] = otp.pk
                request.session['password_reset_user_id'] = user.pk
                return redirect('accounts:reset_password')
            messages.error(request, 'That code is invalid or has expired.')
    else:
        form = OTPVerifyForm()
    return render(request, 'accounts/verify_otp.html', {'form': form, 'email': email})


def reset_password_view(request):
    if request.user.is_authenticated:
        return redirect('news:home')
    user_id = request.session.get('password_reset_user_id')
    otp_id = request.session.get('password_reset_otp_id')
    if not user_id or not otp_id:
        return redirect('accounts:forgot_password')
    user = User.objects.filter(pk=user_id).first()
    otp = PasswordResetOTP.objects.filter(pk=otp_id, user=user).first()
    if not user or not otp or not otp.is_reset_usable():
        messages.error(request, 'Your reset session expired. Request a new code.')
        return redirect('accounts:forgot_password')
    if request.method == 'POST':
        form = ResetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            otp.mark_used()
            for key in (
                'password_reset_email',
                'password_reset_otp_id',
                'password_reset_user_id',
            ):
                request.session.pop(key, None)
            messages.success(request, 'Password reset. You can sign in with your new password.')
            return redirect('accounts:login')
    else:
        form = ResetPasswordForm(user)
    return render(request, 'accounts/reset_password.html', {'form': form})
