from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import OTPRequestLog, PasswordResetOTP
from accounts.otp import issue_otp

User = get_user_model()


class EmailAuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='reader@example.com',
            password='s3cretpass!',
            first_name='Ria',
        )

    def test_email_is_unique(self):
        with self.assertRaises(Exception):
            User.objects.create_user(email='reader@example.com', password='otherpass!')

    def test_login_with_email(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'reader@example.com',
            'password': 's3cretpass!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(str(self.client.session['_auth_user_id']), str(self.user.pk))

    def test_login_rejects_username_only(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': self.user.username,
            'password': 's3cretpass!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign in')

    def test_password_change_ajax(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('accounts:change_password'),
            {
                'old_password': 's3cretpass!',
                'new_password1': 'n3wSecretPass!',
                'new_password2': 'n3wSecretPass!',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('n3wSecretPass!'))


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordResetOTPTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='resetme@example.com',
            password='s3cretpass!',
        )

    def test_otp_email_sent(self):
        response = self.client.post(reverse('accounts:forgot_password'), {
            'email': 'resetme@example.com',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('password reset code', mail.outbox[0].body.lower())

    def test_otp_expires_and_is_single_use(self):
        issue_otp(self.user)
        code = mail.outbox[-1].body.split('is:')[1].split()[0]
        otp = PasswordResetOTP.objects.filter(user=self.user, used_at__isnull=True).first()
        otp.expires_at = timezone.now() - timezone.timedelta(minutes=1)
        otp.save(update_fields=['expires_at'])
        self.assertFalse(otp.verify(code))

        issue_otp(self.user)
        code = mail.outbox[-1].body.split('is:')[1].split()[0]
        otp = PasswordResetOTP.objects.filter(user=self.user, used_at__isnull=True).first()
        self.assertTrue(otp.verify(code))
        self.assertTrue(otp.is_reset_usable())
        self.assertFalse(otp.verify(code))
        otp.mark_used()
        self.assertFalse(otp.is_usable())
        self.assertFalse(PasswordResetOTP.objects.get(pk=otp.pk).is_usable())

    def test_otp_rate_limit(self):
        url = reverse('accounts:forgot_password')
        for _ in range(3):
            response = self.client.post(url, {'email': 'resetme@example.com'})
            self.assertEqual(response.status_code, 302)
        response = self.client.post(url, {'email': 'resetme@example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Too many reset requests')
        self.assertEqual(OTPRequestLog.objects.filter(email='resetme@example.com').count(), 3)
        self.assertLessEqual(PasswordResetOTP.objects.filter(user=self.user).count(), 3)
