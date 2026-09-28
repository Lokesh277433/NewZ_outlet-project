from .models import Category
from .gnews import fetch_headlines
from .weather import fetch_current_weather


def live_ticker(request):
    return {'live_ticker_items': fetch_headlines(max_items=8)}


def nav_categories(request):
    categories = Category.objects.filter(is_active=True)
    return {'nav_categories': categories}


def site_weather(request):
    return {'site_weather': fetch_current_weather()}
