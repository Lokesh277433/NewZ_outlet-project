from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from accounts.models import User
from accounts.permissions import user_can_edit_article, user_is_editor, user_is_journalist

from .forms import ArticleForm, CommentForm, RejectForm
from .gnews import fetch_for_category_slug, fetch_headlines
from .models import Article, Bookmark, Category, EditorialSettings, Tag, WireStory


def _published_qs():
    return Article.objects.filter(status=Article.STATUS_PUBLISHED).select_related(
        'category', 'author'
    )


def _should_auto_publish(user):
    settings_obj = EditorialSettings.load()
    return bool(settings_obj.auto_approve_staff or user.auto_approve)


def home(request):
    published = _published_qs()
    lead = published.filter(is_featured=True).first() or published.first()
    secondary_ids = []
    if lead:
        secondary_ids.append(lead.pk)
    secondary = list(published.exclude(pk__in=secondary_ids)[:3])
    secondary_ids.extend(a.pk for a in secondary)
    latest = published.exclude(pk__in=secondary_ids)[:6]

    section_blocks = []
    for category in Category.objects.filter(is_active=True):
        articles = published.filter(category=category)[:4]
        if articles:
            section_blocks.append({'category': category, 'articles': articles})

    wire_stories = []
    if request.user.is_authenticated:
        wire_stories = fetch_headlines(max_items=8)

    return render(request, 'news/home.html', {
        'lead': lead,
        'secondary': secondary,
        'latest': latest,
        'section_blocks': section_blocks,
        'wire_stories': wire_stories,
    })


def section_list(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    articles = _published_qs().filter(category=category)
    paginator = Paginator(articles, 12)
    page = paginator.get_page(request.GET.get('page'))
    wire_stories = []
    if request.user.is_authenticated:
        wire_stories = fetch_for_category_slug(category.slug, max_items=6)
    return render(request, 'news/section.html', {
        'category': category,
        'page_obj': page,
        'wire_stories': wire_stories,
    })


def article_detail(request, slug):
    if request.user.is_authenticated and user_is_editor(request.user):
        article = get_object_or_404(
            Article.objects.select_related('category', 'author').prefetch_related('tags'),
            slug=slug,
        )
    else:
        article = get_object_or_404(
            _published_qs().prefetch_related('tags'),
            slug=slug,
        )

    Article.objects.filter(pk=article.pk).update(views_count=F('views_count') + 1)
    article.refresh_from_db(fields=['views_count'])

    related = _published_qs().filter(category=article.category).exclude(pk=article.pk)[:4]
    comments = article.comments.filter(is_approved=True).select_related('user')
    comment_form = CommentForm() if request.user.is_authenticated else None
    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = Bookmark.objects.filter(
            user=request.user, article=article
        ).exists()

    return render(request, 'news/article.html', {
        'article': article,
        'related': related,
        'comments': comments,
        'comment_form': comment_form,
        'is_bookmarked': is_bookmarked,
    })


def wire_story_detail(request, pk):
    story = get_object_or_404(WireStory, pk=pk)
    return render(request, 'news/wire_story.html', {'story': story})


def search(request):
    query = request.GET.get('q', '').strip()
    results = _published_qs()
    if query:
        results = results.filter(
            Q(title__icontains=query)
            | Q(kicker__icontains=query)
            | Q(excerpt__icontains=query)
            | Q(body__icontains=query)
            | Q(tags__name__icontains=query)
        ).distinct()
    paginator = Paginator(results, 12)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'news/search.html', {
        'query': query,
        'page_obj': page,
    })


@require_GET
def search_suggest(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})
    articles = _published_qs().filter(
        Q(title__icontains=query) | Q(kicker__icontains=query)
    )[:6]
    return JsonResponse({
        'results': [
            {'title': a.title, 'url': a.get_absolute_url(), 'category': a.category.name}
            for a in articles
        ]
    })


def author_page(request, username):
    author = get_object_or_404(User, username=username)
    articles = _published_qs().filter(author=author)
    paginator = Paginator(articles, 12)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'news/author.html', {
        'author': author,
        'page_obj': page,
    })


@login_required
@require_POST
def add_comment(request, slug):
    article = get_object_or_404(Article, slug=slug, status=Article.STATUS_PUBLISHED)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.article = article
        comment.user = request.user
        comment.is_approved = True
        comment.save()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'comment': {
                    'body': comment.body,
                    'user': comment.user.get_full_name() or comment.user.email,
                    'created_at': comment.created_at.strftime('%d %b %Y, %H:%M'),
                },
            })
        return redirect(article.get_absolute_url() + '#comments')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return redirect(article.get_absolute_url())


@login_required
@require_POST
def toggle_bookmark(request, slug):
    article = get_object_or_404(Article, slug=slug, status=Article.STATUS_PUBLISHED)
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, article=article)
    if not created:
        bookmark.delete()
        bookmarked = False
    else:
        bookmarked = True
    return JsonResponse({'bookmarked': bookmarked})


# --- Newsroom ---

def _ensure_default_tags():
    for name in (
        'World', 'India', 'Politics', 'Business', 'Sport', 'Tech', 'Culture', 'Opinion',
    ):
        Tag.objects.get_or_create(name=name, defaults={'slug': name.lower()})


@login_required
@user_passes_test(user_is_journalist)
def newsroom_dashboard(request):
    is_super = user_is_editor(request.user)
    if is_super:
        articles = Article.objects.select_related('category', 'author').all()
        week_ago = timezone.now() - timedelta(days=7)
        stats = {
            'pending': Article.objects.filter(status=Article.STATUS_REVIEW).count(),
            'published_week': Article.objects.filter(
                status=Article.STATUS_PUBLISHED, published_at__gte=week_ago
            ).count(),
            'active_staff': User.objects.filter(is_staff=True, is_active=True, is_superuser=False).count(),
            'drafts': Article.objects.filter(status=Article.STATUS_DRAFT).count(),
            'rejected': Article.objects.filter(status=Article.STATUS_REJECTED).count(),
        }
        editorial = EditorialSettings.load()
        staff_users = User.objects.filter(is_superuser=False).order_by('email')
        pending = articles.filter(status=Article.STATUS_REVIEW)
        return render(request, 'newsroom/dashboard.html', {
            'articles': articles,
            'pending': pending,
            'stats': stats,
            'editorial': editorial,
            'staff_users': staff_users,
            'is_super': True,
            'reject_form': RejectForm(),
        })

    status_filter = request.GET.get('status', '')
    articles = Article.objects.filter(author=request.user).select_related('category')
    if status_filter in dict(Article.STATUS_CHOICES):
        articles = articles.filter(status=status_filter)
    counts = (
        Article.objects.filter(author=request.user)
        .values('status')
        .annotate(total=Count('id'))
    )
    status_counts = {row['status']: row['total'] for row in counts}
    return render(request, 'newsroom/dashboard.html', {
        'articles': articles,
        'is_super': False,
        'status_filter': status_filter,
        'status_counts': status_counts,
    })


@login_required
@user_passes_test(user_is_journalist)
def article_create(request):
    _ensure_default_tags()
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.status = Article.STATUS_DRAFT
            article.save()
            form.save_m2m()
            messages.success(request, 'Draft saved.')
            return redirect('news:newsroom_edit', pk=article.pk)
    else:
        form = ArticleForm()
    return render(request, 'newsroom/article_form.html', {
        'form': form,
        'is_new': True,
    })


@login_required
def article_edit(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if not user_can_edit_article(request.user, article):
        return redirect('news:newsroom_dashboard')
    _ensure_default_tags()
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, 'Article saved.')
            return redirect('news:newsroom_dashboard')
    else:
        form = ArticleForm(instance=article)
    return render(request, 'newsroom/article_form.html', {
        'form': form,
        'article': article,
        'is_new': False,
        'reject_form': RejectForm(initial={'review_note': article.review_note}),
    })


def _publish_article(article):
    article.status = Article.STATUS_PUBLISHED
    if not article.published_at:
        article.published_at = timezone.now()
    article.save()


@login_required
@require_POST
def article_submit(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if article.author != request.user and not user_is_editor(request.user):
        return redirect('news:newsroom_dashboard')
    if article.status in (Article.STATUS_DRAFT, Article.STATUS_REJECTED):
        if _should_auto_publish(article.author):
            _publish_article(article)
            messages.success(request, 'Article published (auto-approve is on).')
        else:
            article.status = Article.STATUS_REVIEW
            article.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Article submitted for superuser review.')
    return redirect('news:newsroom_dashboard')


@login_required
@user_passes_test(user_is_editor)
@require_POST
def article_publish(request, pk):
    article = get_object_or_404(Article, pk=pk)
    _publish_article(article)
    messages.success(request, 'Article published.')
    return redirect('news:newsroom_dashboard')


@login_required
@user_passes_test(user_is_editor)
@require_POST
def article_reject(request, pk):
    article = get_object_or_404(Article, pk=pk)
    form = RejectForm(request.POST)
    note = form.cleaned_data.get('review_note', '') if form.is_valid() else ''
    article.status = Article.STATUS_REJECTED
    article.review_note = note
    article.save(update_fields=['status', 'review_note', 'updated_at'])
    messages.info(request, 'Article sent back to the author.')
    return redirect('news:newsroom_dashboard')


@login_required
@user_passes_test(user_is_editor)
@require_POST
def article_unpublish(request, pk):
    article = get_object_or_404(Article, pk=pk)
    article.status = Article.STATUS_ARCHIVED
    article.is_featured = False
    article.save(update_fields=['status', 'is_featured', 'updated_at'])
    messages.info(request, 'Article unpublished.')
    return redirect('news:newsroom_dashboard')


@login_required
@user_passes_test(user_is_editor)
@require_POST
def article_pin(request, pk):
    article = get_object_or_404(Article, pk=pk, status=Article.STATUS_PUBLISHED)
    Article.objects.filter(is_featured=True).update(is_featured=False)
    article.is_featured = True
    article.save(update_fields=['is_featured', 'updated_at'])
    messages.success(request, f'“{article.title}” is now pinned to the homepage hero.')
    return redirect('news:newsroom_dashboard')


@login_required
@user_passes_test(user_is_editor)
@require_POST
def article_unpin(request, pk):
    article = get_object_or_404(Article, pk=pk)
    article.is_featured = False
    article.save(update_fields=['is_featured', 'updated_at'])
    messages.info(request, 'Homepage pin removed.')
    return redirect('news:newsroom_dashboard')


@login_required
@user_passes_test(user_is_editor)
@require_POST
def toggle_auto_approve(request):
    editorial = EditorialSettings.load()
    editorial.auto_approve_staff = not editorial.auto_approve_staff
    editorial.updated_by = request.user
    editorial.save()
    if editorial.auto_approve_staff:
        messages.success(request, 'Auto-approve is on. Staff posts will go live immediately.')
    else:
        messages.info(request, 'Auto-approve is off. Staff posts need your review again.')
    return redirect('news:newsroom_dashboard')


@login_required
@user_passes_test(user_is_editor)
@require_POST
def toggle_staff(request, user_id):
    target = get_object_or_404(User, pk=user_id, is_superuser=False)
    target.is_staff = not target.is_staff
    if not target.is_staff:
        target.auto_approve = False
    target.save(update_fields=['is_staff', 'auto_approve'])
    if target.is_staff:
        messages.success(request, f'{target.email} can now write articles.')
    else:
        messages.info(request, f'{target.email} is now a regular reader.')
    return redirect('news:newsroom_dashboard')


@login_required
@user_passes_test(user_is_editor)
@require_POST
def toggle_user_auto_approve(request, user_id):
    target = get_object_or_404(User, pk=user_id, is_superuser=False)
    if not target.is_staff:
        messages.error(request, 'Only staff writers can have auto-approve.')
        return redirect('news:newsroom_dashboard')
    target.auto_approve = not target.auto_approve
    target.save(update_fields=['auto_approve'])
    messages.success(
        request,
        f'Auto-approve for {target.email} is now {"on" if target.auto_approve else "off"}.',
    )
    return redirect('news:newsroom_dashboard')
