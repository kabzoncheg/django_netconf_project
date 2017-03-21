from django import forms
from devices.models import Device

from .models import Configurations


class UploadConfigForm(forms.Form):
    config_description = forms.CharField(label='Configuration description', max_length=200, required=False,
                                         widget=forms.TextInput(attrs={'class': 'form_base'}))
    config = forms.FileField(label='', widget=forms.ClearableFileInput(attrs={'multiple': True, 'class': 'form_upload'}))


class SingleSETRequestForm(forms.Form):
    ip_address = forms.ModelChoiceField(label='Device IP-address', required=True,
                                        queryset=Device.objects.all().order_by('ip_address'),
                                        widget=forms.Select(attrs={'class': 'form_base'}))
    config = forms.ModelChoiceField(label='Device Configuration', required=True,
                                        queryset=Configurations.objects.none(),
                                        widget=forms.Select(attrs={'class': 'form_base'}))

    def __init__(self, user_id, *args, **kwargs):
        # This construction is needed to pass queryset into form
        super(SingleSETRequestForm, self).__init__(user_id, *args, **kwargs)
        print('user_ID:', user_id)
        query_set = Configurations.objects.filter(user_id=user_id)
        print('Config objs __dict__ for query set:', query_set.__dict__)
        self.fields['config'].queryset = query_set
        print('self.fields config __dict__:', self.fields['config'].__dict__)
        print('self QS DICT:', self.fields['config'].queryset)


class ChainCreateForm(forms.Form):
    name = forms.CharField(label='Chain name', max_length=100,
                           widget=forms.TextInput(attrs={'class': 'form_base'}))
    description = forms.CharField(label='Chain description', max_length=200, required=False,
                           widget=forms.Textarea(attrs={'class': 'form_base'}))