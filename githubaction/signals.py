from django.dispatch import receiver
from django.db.models.signals import post_migrate
from django import forms

# Function to set form field classes
def set_form_field_classes():
    # Add Bootstrap classes to form fields
    forms.TextInput.attrs = {'class': 'form-control'}
    forms.EmailInput.attrs = {'class': 'form-control'}
    forms.PasswordInput.attrs = {'class': 'form-control'}
    forms.NumberInput.attrs = {'class': 'form-control'}
    forms.DateInput.attrs = {'class': 'form-control'}
    forms.DateTimeInput.attrs = {'class': 'form-control'}
    forms.Textarea.attrs = {'class': 'form-control'}
    forms.Select.attrs = {'class': 'form-select'}
    forms.CheckboxInput.attrs = {'class': 'form-check-input'}
    forms.ClearableFileInput.attrs = {'class': 'form-control'}
    forms.FileInput.attrs = {'class': 'form-control'}

# Apply form field styling immediately
set_form_field_classes()

# Also run it after migrations in case it's needed
@receiver(post_migrate)
def apply_form_styles(sender, **kwargs):
    set_form_field_classes() 