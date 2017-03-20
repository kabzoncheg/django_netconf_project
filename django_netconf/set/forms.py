from django import forms
from devices.models import Device

from .models import Configurations


class UploadConfigForm(forms.Form):
    config_description = forms.CharField(label='Configuration description', max_length=200, required=False,
                                         widget=forms.TextInput(attrs={'class': 'form_base'}))
    config = forms.FileField(label='', widget=forms.ClearableFileInput(attrs={'multiple': True, 'class': 'form_upload'}))


class SingleSETRequestForm(forms.Form):
    #THINK ABOUT USER!
    ip_address = forms.ModelChoiceField(label='Device IP-address', required=True,
                                        queryset=Device.objects.all().order_by('ip_address'),
                                        widget=forms.Select(attrs={'class': 'form_base'}))
    config = forms.ModelChoiceField(label='Device Configuration', required=True,
                                        queryset=Configurations.objects.all().order_by('name'),
                                        widget=forms.Select(attrs={'class': 'form_base'}))


class ChainCreateForm(forms.Form):
    name = forms.CharField(label='Chain name', max_length=100,
                           widget=forms.TextInput(attrs={'class': 'form_base'}))
    description = forms.CharField(label='Chain description', max_length=200, required=False,
                           widget=forms.Textarea(attrs={'class': 'form_base'}))