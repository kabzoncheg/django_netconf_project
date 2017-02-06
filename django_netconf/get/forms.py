from django import forms
from devices.models import Device

INPUT_TYPE = (
    ('xml', 'raw XML'),
    ('rpc', 'RPC on demand'),
    ('cli', 'CLI  show command'),
)


class SingleGETRequestForm(forms.Form):

    ip_address = forms.ModelChoiceField(label='Device IP-address', required=True,
                                        queryset=Device.objects.all().order_by('ip_address'))
    input_type = forms.ChoiceField(label='Input type', choices=INPUT_TYPE, required=True)
    input_value = forms.CharField(label='Actual input', max_length=1000, required=True)
    additional_input_value = forms.CharField(label='Additional input', max_length=200, required=False)
