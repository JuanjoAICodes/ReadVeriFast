from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

class ArticleURLForm(forms.Form):
    url = forms.URLField(
        label=_('Article URL'),
        required=True,
        widget=forms.URLInput(attrs={'placeholder': _('https://example.com/news/article')})
    )

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text=_('Required. Enter a valid email address.')
    )
    preferred_language = forms.ChoiceField(
        choices=[('en', _('English')), ('es', _('Spanish'))],
        initial='en',
        help_text=_('Choose your preferred language for content and interface.')
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'preferred_language')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.preferred_language = self.cleaned_data['preferred_language']
        # Set initial gamification values
        user.current_wpm = 250
        user.max_wpm = 250
        user.total_xp = 0
        user.current_xp_points = 0
        if commit:
            user.save()
        return user

class FeatureControlForm(forms.ModelForm):
    font_choice = forms.ChoiceField(
        choices=[
            ('default', _('Default')),
            ('has_font_opensans', _('OpenSans')),
            ('has_font_opendyslexic', _('OpenDyslexic')),
            ('has_font_roboto', _('Roboto')),
            ('has_font_merriweather', _('Merriweather')),
            ('has_font_playfair', _('Playfair Display')),
        ],
        widget=forms.RadioSelect,
        required=False,
        label=_("Font Choice")
    )
    chunking_choice = forms.ChoiceField(
        choices=[
            ('default', _('1-Word')),
            ('has_2word_chunking', _('2-Word')),
            ('has_3word_chunking', _('3-Word')),
            ('has_4word_chunking', _('4-Word')),
            ('has_5word_chunking', _('5-Word')),
        ],
        widget=forms.RadioSelect,
        required=False,
        label=_("Word Chunking")
    )

    class Meta:
        model = CustomUser
        fields = ['has_smart_connector_grouping', 'has_smart_symbol_handling']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            # Initialize font_choice
            if self.instance.has_font_opensans:
                self.initial['font_choice'] = 'has_font_opensans'
            elif self.instance.has_font_opendyslexic:
                self.initial['font_choice'] = 'has_font_opendyslexic'
            elif self.instance.has_font_roboto:
                self.initial['font_choice'] = 'has_font_roboto'
            elif self.instance.has_font_merriweather:
                self.initial['font_choice'] = 'has_font_merriweather'
            elif self.instance.has_font_playfair:
                self.initial['font_choice'] = 'has_font_playfair'
            else:
                self.initial['font_choice'] = 'default'

            # Initialize chunking_choice
            if self.instance.has_2word_chunking:
                self.initial['chunking_choice'] = 'has_2word_chunking'
            elif self.instance.has_3word_chunking:
                self.initial['chunking_choice'] = 'has_3word_chunking'
            elif self.instance.has_4word_chunking:
                self.initial['chunking_choice'] = 'has_4word_chunking'
            elif self.instance.has_5word_chunking:
                self.initial['chunking_choice'] = 'has_5word_chunking'
            else:
                self.initial['chunking_choice'] = 'default'

    def save(self, commit=True):
        user = super().save(commit=False)

        # Handle font_choice
        font_choice = self.cleaned_data.get('font_choice', 'default')
        user.has_font_opensans = (font_choice == 'has_font_opensans')
        user.has_font_opendyslexic = (font_choice == 'has_font_opendyslexic')
        user.has_font_roboto = (font_choice == 'has_font_roboto')
        user.has_font_merriweather = (font_choice == 'has_font_merriweather')
        user.has_font_playfair = (font_choice == 'has_font_playfair')

        # Handle chunking_choice
        chunking_choice = self.cleaned_data.get('chunking_choice', 'default')
        user.has_2word_chunking = (chunking_choice == 'has_2word_chunking')
        user.has_3word_chunking = (chunking_choice == 'has_3word_chunking')
        user.has_4word_chunking = (chunking_choice == 'has_4word_chunking')
        user.has_5word_chunking = (chunking_choice == 'has_5word_chunking')

        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 
            'preferred_language', 'theme', 'current_wpm',
        ]
        widgets = {
            'current_wpm': forms.NumberInput(attrs={'min': 100, 'max': 1000, 'step': 10}),
            'preferred_language': forms.Select(choices=[('en', _('English')), ('es', _('Spanish'))]),
            'theme': forms.Select(choices=[('light', _('Light')), ('dark', _('Dark'))]),
        }
        help_texts = {
            'current_wpm': _('Your preferred reading speed (100-1000 words per minute)'),
            'preferred_language': _('Language for content and interface'),
            'theme': _('Visual theme preference'),
        }