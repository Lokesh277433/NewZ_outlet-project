from django import forms

from .models import Article, Category, Comment, Tag
from .utils import sanitize_html


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = [
            'title', 'kicker', 'excerpt', 'body', 'hero_image',
            'category', 'tags', 'is_breaking',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Headline'}),
            'kicker': forms.TextInput(attrs={'placeholder': 'Kicker / standfirst'}),
            'excerpt': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Short summary for cards'}),
            'body': forms.Textarea(attrs={'rows': 20, 'placeholder': 'Article body (HTML allowed)'}),
            'tags': forms.SelectMultiple(attrs={'size': 8}),
        }
        help_texts = {
            'category': 'Choose the homepage section this story belongs in (World, India, Politics, …).',
            'tags': 'Optional extra labels. Hold Ctrl/Cmd to select more than one.',
            'is_breaking': 'Show this story on the breaking news bar once it is published.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['tags'].queryset = Tag.objects.all()
        self.fields['category'].empty_label = 'Select a section'

    def clean_body(self):
        return sanitize_html(self.cleaned_data.get('body', ''))


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Join the discussion…',
                'class': 'comment-input',
            }),
        }


class SearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search news…', 'class': 'search-input'}),
    )


class RejectForm(forms.Form):
    review_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Optional note for the author',
            'class': 'form-control',
        }),
    )
