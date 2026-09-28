from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from django.utils.text import slugify

from accounts.permissions import EDITOR_GROUP, JOURNALIST_GROUP, READER_GROUP
from news.models import Article, Category, Tag

User = get_user_model()

SAMPLE_BODY = """
<p>In a development that could reshape the political landscape, leaders from across the spectrum convened today for urgent talks on economic reform and national security.</p>
<p>Analysts say the outcome of these negotiations will set the tone for the coming parliamentary session, with opposition parties demanding greater transparency on fiscal policy.</p>
<h2>What happens next</h2>
<p>Officials indicated that a formal announcement is expected within 48 hours. Markets responded cautiously, with the benchmark index closing marginally higher.</p>
<blockquote>"This is a moment that demands clarity and courage," said one senior minister.</blockquote>
<p>Regional correspondents report widespread public interest, with citizen groups organising town halls in major cities.</p>
"""


class Command(BaseCommand):
    help = 'Seed categories, demo users, and sample articles'

    def handle(self, *args, **options):
        categories_data = [
            ('World', 'world', 'Global news and international affairs', 1),
            ('India', 'india', 'News from across the nation', 2),
            ('Politics', 'politics', 'Parliament, policy, and power', 3),
            ('Business', 'business', 'Markets, economy, and enterprise', 4),
            ('Sport', 'sport', 'Cricket, football, and more', 5),
            ('Tech', 'tech', 'Technology and innovation', 6),
            ('Culture', 'culture', 'Arts, books, and lifestyle', 7),
            ('Opinion', 'opinion', 'Editorials and commentary', 8),
        ]

        categories = {}
        for name, slug, desc, order in categories_data:
            cat, _ = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'description': desc, 'order': order},
            )
            categories[slug] = cat

        for name in ('World', 'India', 'Politics', 'Business', 'Sport', 'Tech', 'Culture', 'Opinion'):
            Tag.objects.get_or_create(name=name, defaults={'slug': name.lower()})

        reader_group, _ = Group.objects.get_or_create(name=READER_GROUP)
        journalist_group, _ = Group.objects.get_or_create(name=JOURNALIST_GROUP)
        editor_group, _ = Group.objects.get_or_create(name=EDITOR_GROUP)

        editor, created = User.objects.get_or_create(
            email='editor@newsoutlet.local',
            defaults={
                'username': 'editor',
                'first_name': 'Priya',
                'last_name': 'Sharma',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            editor.set_password('editor123')
            editor.save()
        else:
            editor.is_staff = True
            editor.is_superuser = True
            editor.save(update_fields=['is_staff', 'is_superuser'])
        editor.groups.add(editor_group, journalist_group, reader_group)

        journalist, created = User.objects.get_or_create(
            email='journalist@newsoutlet.local',
            defaults={
                'username': 'journalist',
                'first_name': 'Arjun',
                'last_name': 'Mehta',
                'is_staff': True,
            },
        )
        if created:
            journalist.set_password('journalist123')
            journalist.save()
        else:
            journalist.is_staff = True
            journalist.save(update_fields=['is_staff'])
        journalist.groups.add(journalist_group, reader_group)

        articles_data = [
            ('India', 'india', 'Historic reform bill passes with bipartisan support', 'Parliament', True, True, True),
            ('Politics', 'politics', 'Opposition calls for emergency debate on inflation', 'Economy', True, False, False),
            ('Business', 'business', 'Sensex hits record high amid foreign inflows', 'Markets', False, True, False),
            ('World', 'world', 'Global leaders agree on climate finance framework', 'COP summit', False, False, False),
            ('Sport', 'sport', 'India clinches series in dramatic final over', 'Cricket', False, True, False),
            ('Tech', 'tech', 'Homegrown AI startup raises $200M in Series C', 'Startups', False, False, False),
            ('Culture', 'culture', 'Festival season kicks off with record bookings', 'Arts', False, False, False),
            ('Opinion', 'opinion', 'Why India needs a new urban mobility compact', 'Editorial', False, False, False),
            ('India', 'india', 'Monsoon advances; IMD issues alert for coastal states', 'Weather', True, False, False),
            ('Politics', 'politics', 'Cabinet reshuffle expected ahead of state polls', 'Government', False, False, False),
        ]

        now = timezone.now()
        for i, (cat_name, cat_slug, title, kicker, breaking, featured, is_lead) in enumerate(articles_data):
            slug = slugify(title)[:80]
            author = journalist if i % 2 == 0 else editor
            Article.objects.get_or_create(
                slug=slug,
                defaults={
                    'title': title,
                    'kicker': kicker,
                    'excerpt': f'A comprehensive look at {title.lower()}.',
                    'body': SAMPLE_BODY,
                    'category': categories[cat_slug],
                    'author': author,
                    'status': Article.STATUS_PUBLISHED,
                    'is_breaking': breaking,
                    'is_featured': featured or is_lead,
                    'published_at': now - timezone.timedelta(hours=i * 3),
                },
            )

        self.stdout.write(self.style.SUCCESS('Seed data created.'))
        self.stdout.write('Demo accounts (email + password):')
        self.stdout.write('  editor@newsoutlet.local / editor123 (superuser)')
        self.stdout.write('  journalist@newsoutlet.local / journalist123 (staff)')
        self.stdout.write('Create a superuser with: python manage.py createsuperuser')
