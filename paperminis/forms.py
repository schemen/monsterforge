from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from constrainedfilefield.fields import ConstrainedFileField
from django.conf import settings
from django.template.defaultfilters import filesizeformat
import os
from django.core.exceptions import ValidationError

from .models import Creature, Bestiary, CreatureQuantity, PrintSettings

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
User = get_user_model()

class SignUpForm(UserCreationForm):
    """Used to register new users"""
    # email
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2', )


class CreatureModifyForm(forms.ModelForm):
    """Add or Update creatures"""
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'size': '60%'}))
    class Meta:
        model = Creature
        fields = ['name', 'show_name', 'img_url', 'creature_type', 'size', 'CR', 'position', 'color']
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')  # To get request.user. Do not use kwargs.pop('user', None) due to potential security hole
        #self.method = kwargs.pop('method') # To get create or update
        super(CreatureModifyForm, self).__init__(*args, **kwargs)
        self.fields['color'].required = False
        self.fields['position'].required = False
    def clean(self):
        cleaned_data = super(CreatureModifyForm, self).clean()
        if self.user:
            name = cleaned_data.get("name")
            img_url = cleaned_data.get("img_url")
            cr = cleaned_data.get("CR")
            # name + img_url must be unique. Otherwise raise a ValidationError
            count = Creature.objects.filter(owner=self.user,name=name,img_url=img_url).exclude(id=self.instance.id).count()
            if count == 1:
                raise forms.ValidationError(('This creature already exists. Use a different name or image url.'), code='exists',)

            # patreon early access backend validation
            if self.user.groups.filter(name='Patrons').count() <= 0:
                cleaned_data['show_name'] = True
                cleaned_data['position'] = Creature.WALKING

            # validate CR
            if not isinstance(cr, float) or cr < 0 or cr > 1000:
                raise forms.ValidationError(('CR must a number be between 0 and 1000.'), code='value error', )


        return cleaned_data

class BestiaryModifyForm(forms.ModelForm):
    """Simple bestiary create/update form"""
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'size': '80%'}))
    class Meta:
        model = Bestiary
        fields = ['name', ]


class QuantityForm(forms.ModelForm):
    """Form to link creatures to bestiary. Most of this is done in views. """
    quantity = forms.IntegerField()
    #name = forms.CharField(max_length=150)
    class Meta:
        model = Creature
        fields = ['name',]



class PrintForm(forms.ModelForm):
    """Simple Form for print settings."""
    class Meta:
        model = PrintSettings
        exclude = ['user']

def validate_file_extension(value):
    """Function to validate json file extension and size."""
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.json']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension. Please only upload .json files.')
    if value.size > settings.MAX_UPLOAD_SIZE:
        raise forms.ValidationError(_('Please keep filesize under %s. Current filesize %s') % (filesizeformat(settings.MAX_UPLOAD_SIZE), filesizeformat(value._size)))

class UploadFileForm(forms.Form):
    """Upload form with validator."""
    file = forms.FileField(validators=[validate_file_extension])
