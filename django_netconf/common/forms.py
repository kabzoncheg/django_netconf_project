from django import forms


class CustomModelChoiceFieldForm(forms.ModelChoiceField):
    # Checks model object for specific "name customizer"
    def label_from_instance(self, obj):
        if hasattr(obj, 'get_form_name'):
            return obj.get_form_name()
        else:
            return super(CustomModelChoiceFieldForm, self).label_from_instance(obj)
