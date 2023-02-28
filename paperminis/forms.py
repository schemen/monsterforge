import os
from urllib.parse import urlparse
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from constrainedfilefield.fields import ConstrainedFileField
from django.conf import settings
from django.template.defaultfilters import filesizeformat
from django.core.exceptions import ValidationError
from .models import Creature, Bestiary, CreatureQuantity, PrintSettings

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class UserDeleteForm(forms.Form):

    error_messages = {
        'password_incorrect': _("Your password was entered incorrectly. Please enter it again."),
    }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'autofocus': True}),
    )

    def clean_password(self):
        """
        Validate that the password field is correct.
        """
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise ValidationError(
                self.error_messages['password_incorrect'],
                code='password_incorrect',
            )
        return password

    class Meta:
        fields = ['password']

class SignUpForm(UserCreationForm):
    """Used to register new users"""
    # email
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2',)


class CreatureModifyForm(forms.ModelForm):
    """Add or Update creatures"""
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'size': '60%'}))

    class Meta:
        model = Creature
        fields = ['name', 'show_name', 'img_url', 'size', 'position', 'background_color', 'color', 'cavalry_mode']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')  # To get request.user. Do not use kwargs.pop('user', None) due to potential security hole
        # self.method = kwargs.pop('method') # To get create or update
        super(CreatureModifyForm, self).__init__(*args, **kwargs)
        self.fields['color'].required = False
        self.fields['background_color'].required = False
        self.fields['position'].required = False

    def clean(self):
        cleaned_data = super(CreatureModifyForm, self).clean()
        if self.user:
            name = cleaned_data.get("name")
            img_url = cleaned_data.get("img_url")
            # name + img_url must be unique. Otherwise raise a ValidationError
            count = Creature.objects.filter(owner=self.user, name=name, img_url=img_url).exclude(
                id=self.instance.id).count()
            if count == 1:
                raise forms.ValidationError(('This creature already exists. Use a different name or image url.'),
                                            code='exists', )

            # patreon early access backend validation
            # if self.user.groups.filter(name='Patrons').count() <= 0:
            #     cleaned_data['show_name'] = True
            #     cleaned_data['position'] = Creature.WALKING

        return cleaned_data


class BestiaryModifyForm(forms.ModelForm):
    """Simple bestiary create/update form"""
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'size': '80%'}))

    class Meta:
        model = Bestiary
        fields = ['name', ]


def validate_ddbenc_url(value):
    if not value:
        return  # Required error is done the field
    obj = urlparse(value)
    if not 'dndbeyond.com' in obj.netloc or not ('encounters/') in obj.path:
        raise ValidationError('Only DDB Encounter URLS are allowed!')


class DDBEncounterBestiaryCreate(forms.Form):
    """create bestiary and monsters from ddb encounter"""
    # URL
    ddb_enc_url = forms.URLField(help_text="Required. Enter a Dndbeyond Encounter URL.",
                                 validators=[validate_ddbenc_url])


class QuantityForm(forms.ModelForm):
    """Form to link creatures to bestiary. Most of this is done in views. """
    quantity = forms.IntegerField()

    # name = forms.CharField(max_length=150)
    class Meta:
        model = Creature
        fields = ['name', ]


class PrintForm(forms.ModelForm):
    """Simple Form for print settings."""

    class Meta:
        model = PrintSettings
        exclude = ['user']

    def clean_darken(self):
        darken = self.cleaned_data['darken']
        if not 0 <= darken <= 100:
            raise forms.ValidationError("Enter a value between 0 and 100")

        if not darken % 1 == 0:
            raise forms.ValidationError("Enter a multiple of 1")
        return darken


def validate_file_extension(value):
    """Function to validate json file extension and size."""
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.json']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension. Please only upload .json files.')
    if value.size > settings.MAX_UPLOAD_SIZE:
        raise forms.ValidationError(_('Please keep filesize under %s. Current filesize %s') % (
        filesizeformat(settings.MAX_UPLOAD_SIZE), filesizeformat(value._size)))


class UploadFileForm(forms.Form):
    """Upload form with validator."""
    file = forms.FileField(validators=[validate_file_extension])


class QuickCreateSettingsForm(forms.Form):
    # paper format
    A4 = 'a4'
    A3 = 'a3'
    LETTER = 'letter'
    LEGAL = 'legal'
    TABLOID = 'tabloid'
    PAPER_FORMAT_CHOICES = (
        (A4, 'A4'),
        (A3, 'A3'),
        (LETTER, 'Letter'),
        (LEGAL, 'Legal'),
        (TABLOID, 'Tabloid')
    )
    # grid size
    GRID28 = 28
    GRID24 = 24
    GRID18 = 18
    GRID12 = 12
    GRID_SIZE_CHOICES = (
        (GRID28, '28 mm ~ 1.1 inch'),
        (GRID24, '24 mm ~ 1 inch'),
        (GRID18, '18 mm ~ 3/4 inch'),
        (GRID12, '12 mm ~ 1/2 inch')
    )
    # base shape
    SQUARE = 'square'
    HEXAGONAL = 'hexagon'
    CIRCLE = 'circle'
    BASE_SHAPE_CHOICES = (
        (SQUARE, 'Square'),
        (HEXAGONAL, 'Hexagon'),
        (CIRCLE, 'Circle')
    )

    # Print Settings
    paper_format = forms.ChoiceField(choices=PAPER_FORMAT_CHOICES, required=True)
    grid_size = forms.ChoiceField(choices=GRID_SIZE_CHOICES, required=True, initial=GRID24)
    base_shape = forms.ChoiceField(choices=BASE_SHAPE_CHOICES, required=True)
    enumerate = forms.BooleanField(required=False)


class QuickCreateCreatureForm(forms.Form):
    # Size
    TINY = 'T'
    SMALL = 'S'
    MEDIUM = 'M'
    LARGE = 'L'
    HUGE = 'H'
    GARGANTUAN = 'G'

    CREATURE_SIZE_CHOICES = (
        (TINY, 'Tiny'),
        (SMALL, 'Small'),
        (MEDIUM, 'Medium'),
        (LARGE, 'Large'),
        (HUGE, 'Huge'),
        (GARGANTUAN, 'Gargantuan')
    )

    # Base Color
    GREEN = '228b22'
    RED = 'aa3939'
    BLUE = '005b96'
    LIGHTGRAY = 'd3d3d3'
    DARKGRAY = 'a9a9a9'
    BLACK = '000000'
    WHITE = 'ffffff'

    COLOR_CHOICES = (
        (GREEN, 'Green'),
        (RED, 'Red'),
        (BLUE, 'Blue'),
        (LIGHTGRAY, 'Light Gray'),
        (DARKGRAY, 'Dark Gray'),
        (BLACK, 'Black'),
        (WHITE, 'White')
    )

    # Alignment
    FLYING = 'top'
    HOVERING = 'center'
    WALKING = 'bottom'

    POSITION_CHOICES = (
        (FLYING, 'Flying (Top)'),
        (HOVERING, 'Hovering (Middle)'),
        (WALKING, 'Walking (Bottom)')
    )
    # Creature Data
    img_url = forms.URLField(label='Image direct URL', required=False)
    position = forms.ChoiceField(choices=POSITION_CHOICES, initial="bottom")
    name = forms.CharField(max_length=100, required=False)
    size = forms.ChoiceField(choices=CREATURE_SIZE_CHOICES, initial="M")
    quantity = forms.IntegerField(max_value=100, min_value=1, required=False, initial=1)
    color = forms.ChoiceField(choices=COLOR_CHOICES, initial=DARKGRAY)
    background_color = forms.ChoiceField(choices=COLOR_CHOICES, initial=WHITE)
    cavalry_mode = forms.BooleanField(required=False)
