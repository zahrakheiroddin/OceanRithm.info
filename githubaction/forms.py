from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import GitHubConfig, Repository


class GitHubConfigForm(forms.ModelForm):
    class Meta:
        model = GitHubConfig
        fields = ('github_token', 'github_username')
        widgets = {
            'github_token': forms.PasswordInput(render_value=True),
        }


class NewRepositoryForm(forms.ModelForm):
    class Meta:
        model = Repository
        fields = ('name', 'description', 'is_private')


class ExistingRepositoryForm(forms.Form):
    name = forms.CharField(max_length=255)
    
    
class FileUploadForm(forms.Form):
    file = forms.FileField()
    
    
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class FolderUploadForm(forms.Form):
    folder = forms.FileField(
        widget=MultipleFileInput(attrs={'multiple': True}),
        label="Select multiple files"
    ) 