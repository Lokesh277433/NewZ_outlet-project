READER_GROUP = 'Reader'
JOURNALIST_GROUP = 'Journalist'
EDITOR_GROUP = 'Editor'
ADMIN_GROUP = 'Admin'

ROLE_GROUPS = [READER_GROUP, JOURNALIST_GROUP, EDITOR_GROUP, ADMIN_GROUP]


def user_is_journalist(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def user_is_editor(user):
    return user.is_authenticated and user.is_superuser


def user_can_edit_article(user, article):
    if not user.is_authenticated:
        return False
    if user_is_editor(user):
        return True
    if not user_is_journalist(user):
        return False
    return article.author_id == user.id and article.status in (
        ArticleStatus.DRAFT,
        ArticleStatus.REVIEW,
        ArticleStatus.REJECTED,
    )


class ArticleStatus:
    DRAFT = 'draft'
    REVIEW = 'review'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'
    REJECTED = 'rejected'
