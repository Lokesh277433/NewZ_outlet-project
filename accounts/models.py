import hashlib
import secrets

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _unique_username(self, email):
        base = slugify(email.split('@')[0])[:140] or 'user'
        username = base
        counter = 1
        while self.model.objects.filter(username=username).exists():
            username = f'{base}{counter}'
            counter += 1
        return username

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('An email address is required.')
        email = self.normalize_email(email).lower()
        username = extra_fields.get('username')
        if not username:
            extra_fields['username'] = self._unique_username(email)
        else:
            extra_fields['username'] = username
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField('email address', unique=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    auto_approve = models.BooleanField(
        default=False,
        help_text='If enabled, this staff member’s articles publish without superuser review.',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ['email']

    def __str__(self):
        return self.get_full_name() or self.email

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        if not self.username and self.email:
            self.username = User.objects._unique_username(self.email)
        super().save(*args, **kwargs)

    def role_names(self):
        names = list(self.groups.values_list('name', flat=True))
        if self.is_superuser and 'Superuser' not in names:
            names.insert(0, 'Superuser')
        elif self.is_staff and 'Staff' not in names:
            names.insert(0, 'Staff')
        elif not names:
            names = ['Reader']
        return names

    def is_journalist(self):
        return self.is_authenticated and (self.is_staff or self.is_superuser)

    def is_editor(self):
        return self.is_authenticated and self.is_superuser

    def is_admin_role(self):
        return self.is_superuser


def hash_otp(code, email):
    payload = f'{code}:{email.lower()}:{settings.SECRET_KEY}'
    return hashlib.sha256(payload.encode()).hexdigest()


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='password_reset_otps',
    )
    code_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(blank=True, null=True)
    used_at = models.DateTimeField(blank=True, null=True)
    request_ip = models.GenericIPAddressField(blank=True, null=True)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def is_usable(self):
        return (
            self.used_at is None
            and self.verified_at is None
            and not self.is_expired()
        )

    def is_reset_usable(self):
        """Return whether this OTP has been verified and can reset one password."""
        return (
            self.used_at is None
            and self.verified_at is not None
            and not self.is_expired()
        )

    def verify(self, code):
        self.attempts += 1
        self.save(update_fields=['attempts'])
        if not self.is_usable():
            return False
        if self.attempts > getattr(settings, 'OTP_MAX_VERIFY_ATTEMPTS', 5):
            return False
        if not secrets.compare_digest(self.code_hash, hash_otp(code, self.user.email)):
            return False
        self.verified_at = timezone.now()
        self.save(update_fields=['verified_at'])
        return True

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=['used_at'])


class OTPRequestLog(models.Model):
    email = models.EmailField(db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
