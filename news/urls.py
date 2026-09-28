from django.urls import path

from . import views

app_name = 'news'

urlpatterns = [
    path('', views.home, name='home'),
    path('section/<slug:slug>/', views.section_list, name='section'),
    path('wire/<int:pk>/', views.wire_story_detail, name='wire_story'),
    path('article/<slug:slug>/', views.article_detail, name='article'),
    path('article/<slug:slug>/comment/', views.add_comment, name='add_comment'),
    path('article/<slug:slug>/bookmark/', views.toggle_bookmark, name='toggle_bookmark'),
    path('search/', views.search, name='search'),
    path('search/suggest/', views.search_suggest, name='search_suggest'),
    path('author/<str:username>/', views.author_page, name='author'),
    path('newsroom/', views.newsroom_dashboard, name='newsroom_dashboard'),
    path('newsroom/articles/new/', views.article_create, name='newsroom_create'),
    path('newsroom/articles/<int:pk>/edit/', views.article_edit, name='newsroom_edit'),
    path('newsroom/articles/<int:pk>/submit/', views.article_submit, name='newsroom_submit'),
    path('newsroom/articles/<int:pk>/publish/', views.article_publish, name='newsroom_publish'),
    path('newsroom/articles/<int:pk>/reject/', views.article_reject, name='newsroom_reject'),
    path('newsroom/articles/<int:pk>/unpublish/', views.article_unpublish, name='newsroom_unpublish'),
    path('newsroom/articles/<int:pk>/pin/', views.article_pin, name='newsroom_pin'),
    path('newsroom/articles/<int:pk>/unpin/', views.article_unpin, name='newsroom_unpin'),
    path('newsroom/auto-approve/', views.toggle_auto_approve, name='newsroom_auto_approve'),
    path('newsroom/staff/<int:user_id>/toggle/', views.toggle_staff, name='newsroom_toggle_staff'),
    path(
        'newsroom/staff/<int:user_id>/auto-approve/',
        views.toggle_user_auto_approve,
        name='newsroom_user_auto_approve',
    ),
]
