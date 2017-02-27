from django import forms
from devices.models import Device

INPUT_TYPE = (
    ('xml', 'raw XML'),
    ('rpc', 'RPC on demand'),
    ('cli', 'CLI  show command'),
)


class SingleGETRequestForm(forms.Form):
    ip_address = forms.ModelChoiceField(label='Device IP-address', required=True,
                                        queryset=Device.objects.all().order_by('ip_address'),
                                        widget=forms.Select(attrs={'class': 'form_ip'}))

    input_type = forms.ChoiceField(label='Input type', choices=INPUT_TYPE, required=True,
                                   widget=forms.Select(attrs={'class': 'form_inp_type'}))

    input_value = forms.CharField(label='Actual input', max_length=1000, required=True,
                                  widget=forms.Textarea(attrs={'class': 'form_inp_val'}))

    additional_input_value = forms.CharField(label='Additional input', max_length=200, required=False,
                                             widget=forms.TextInput(attrs={'class': 'form_add_inp_val'}))


class ChainCreateForm(forms.Form):
    name = forms.CharField(label='Chain name', max_length=100,
                           widget=forms.TextInput(attrs={'class': 'form_base'}))
    description = forms.CharField(label='Chain description', max_length=200, required=False,
                           widget=forms.Textarea(attrs={'class': 'form_base'}))
