from django import forms


SEARCH_CRITERIA = (
    ('model', 'Model name'),
    ('instance-name', 'Instance name'),
    ('mac-address', 'MAC address'),
    ('interface-ip-address', 'IP address'),
)


class SearchForm(forms.Form):

    criteria = forms.ChoiceField(label='criteria', choices=SEARCH_CRITERIA, required=True)
    pattern = forms.CharField(label='pattern ', max_length=150, required=True)
