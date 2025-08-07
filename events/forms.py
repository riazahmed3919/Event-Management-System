from django import forms
from events.models import Event, Category
from django.forms.widgets import ClearableFileInput
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

class StyledFormMixin:
    default_classes = "border border-gray-300 p-3 w-full rounded-md focus:outline-none focus:ring-2 focus:ring-rose-500"

    def apply_styled_widget(self):
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.DateInput, forms.TimeInput)):
                field.widget.attrs.update({
                    'class': self.default_classes,
                    'placeholder': f"Enter {field.label.lower()}"
                })
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({
                    'class': f"{self.default_classes}",
                    'placeholder': f"Enter {field.label.lower()}",
                    'rows': 4,
                    'style': "resize: none;"
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': self.default_classes
                })

class EventForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Event
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'image': ClearableFileInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styled_widget()

class CategoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styled_widget()

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'profile_image', 'phone_number']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            existing_classes = field.widget.attrs.get('class', '')
            base_classes = (
                "block w-full rounded-md border border-rose-300 "
                "focus:border-rose-500 focus:ring-1 focus:ring-rose-500 p-2"
            )
            field.widget.attrs['class'] = (existing_classes + " " + base_classes).strip()

class CustomPasswordChangeForm( PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'border border-gray-300 p-3 w-full rounded-md focus:outline-none focus:ring-2 focus:ring-rose-500',
                'placeholder': field.label,
                'autocomplete': 'off',
            })

class CustomPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing_classes = field.widget.attrs.get('class', '')
            base_classes = (
                "block w-full rounded-md border border-rose-300 "
                "focus:border-rose-500 focus:ring-1 focus:ring-rose-500 p-2"
            )
            field.widget.attrs['class'] = (existing_classes + " " + base_classes).strip()

class CustomPasswordResetConfirmForm(StyledFormMixin, SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styled_widget()
