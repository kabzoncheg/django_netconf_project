from django import forms


class UploadConfigForm(forms.Form):
    # config_name = forms.CharField(label='Configuration name', max_length=100, required=True)
    config_description = forms.CharField(label='Configuration description', max_length=200, required=False)
    config = forms.FileField()
