from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from accounts.permissions import ADMIN_GROUP, EDITOR_GROUP, JOURNALIST_GROUP, READER_GROUP
from news.models import Article, Comment


class Command(BaseCommand):
    help = 'Create role groups with permissions'

    def handle(self, *args, **options):
        article_ct = ContentType.objects.get_for_model(Article)
        comment_ct = ContentType.objects.get_for_model(Comment)

        groups_config = {
            READER_GROUP: [],
            JOURNALIST_GROUP: [
                ('add_article', article_ct),
                ('change_article', article_ct),
                ('view_article', article_ct),
            ],
            EDITOR_GROUP: [
                ('add_article', article_ct),
                ('change_article', article_ct),
                ('delete_article', article_ct),
                ('view_article', article_ct),
                ('change_comment', comment_ct),
            ],
            ADMIN_GROUP: [],
        }

        for name, perms in groups_config.items():
            group, created = Group.objects.get_or_create(name=name)
            if perms:
                permission_objs = []
                for codename, ct in perms:
                    try:
                        perm = Permission.objects.get(codename=codename, content_type=ct)
                        permission_objs.append(perm)
                    except Permission.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'Permission {codename} not found'))
                group.permissions.set(permission_objs)
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{status} group: {name}'))

        self.stdout.write(self.style.SUCCESS('Role groups are ready.'))
