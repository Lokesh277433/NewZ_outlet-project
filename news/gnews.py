from django.core.cache import cache
from django.conf import settings

import requests

from .models import WireStory

GNEWS_TOPIC_MAP = {
    'world': 'world',
    'india': 'nation',
    'politics': 'nation',
    'business': 'business',
    'sport': 'sports',
    'tech': 'technology',
    'culture': 'entertainment',
}


def _normalize(raw):
    items = []
    for article in raw or []:
        url = article.get('url') or ''
        title = article.get('title') or ''
        if not url or not title:
            continue
        source = (article.get('source') or {}).get('name') or 'Wire'
        items.append({
            'title': title,
            'url': url,
            'excerpt': article.get('description') or '',
            'image': article.get('image') or '',
            'source': source,
            'published_at': article.get('publishedAt') or '',
        })
    return items


def _attach_internal_urls(items):
    """Persist the limited GNews preview and add its internal detail URL."""
    for item in items:
        story, _ = WireStory.objects.update_or_create(
            source_url=item['url'],
            defaults={
                'title': item['title'][:500],
                'source_name': item['source'][:150],
                'excerpt': item['excerpt'],
                'image_url': item['image'][:1000],
                'source_published_at': item['published_at'][:100],
            },
        )
        item['detail_url'] = story.get_absolute_url()
    return items


def fetch_headlines(topic=None, max_items=8):
    api_key = getattr(settings, 'GNEWS_API_KEY', '') or ''
    if not api_key:
        return []
    cache_key = f'gnews:{topic or "top"}:{max_items}'
    cached = cache.get(cache_key)
    if cached is not None:
        return _attach_internal_urls(cached)
    params = {
        'apikey': api_key,
        'lang': 'en',
        'country': 'in',
        'max': max_items,
    }
    if topic:
        params['topic'] = topic
    try:
        response = requests.get(
            'https://gnews.io/api/v4/top-headlines',
            params=params,
            timeout=8,
        )
        response.raise_for_status()
        items = _normalize(response.json().get('articles'))
    except (requests.RequestException, ValueError, TypeError):
        items = []
    items = _attach_internal_urls(items)
    cache.set(cache_key, items, getattr(settings, 'GNEWS_CACHE_SECONDS', 600))
    return items


def fetch_for_category_slug(slug, max_items=6):
    topic = GNEWS_TOPIC_MAP.get(slug)
    if not topic:
        return []
    return fetch_headlines(topic=topic, max_items=max_items)
