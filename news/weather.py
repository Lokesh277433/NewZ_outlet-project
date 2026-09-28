"""Small, cached adapter for OpenWeatherMap's current-weather endpoint."""

from django.conf import settings
from django.core.cache import cache
from django.utils.text import slugify

import requests


def fetch_current_weather():
    api_key = getattr(settings, 'WEATHER_API_KEY', '')
    city = getattr(settings, 'WEATHER_CITY', 'New Delhi')
    if not api_key or api_key.startswith('put-your'):
        return None

    cache_key = f'weather:current:{slugify(city)}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        response = requests.get(
            'https://api.openweathermap.org/data/2.5/weather',
            params={'q': city, 'appid': api_key, 'units': 'metric'},
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()
        weather = {
            'city': payload.get('name') or city,
            'temperature': round(payload['main']['temp']),
            'description': (payload.get('weather') or [{}])[0].get('description', ''),
        }
    except (requests.RequestException, ValueError, KeyError, TypeError):
        weather = None

    cache.set(cache_key, weather, getattr(settings, 'WEATHER_CACHE_SECONDS', 900))
    return weather
