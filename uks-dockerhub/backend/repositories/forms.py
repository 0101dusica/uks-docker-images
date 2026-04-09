from django import forms
from .models import Repository, Visibility


class RepositoryCreateForm(forms.ModelForm):
    class Meta:
        model = Repository
        fields = ['name', 'description', 'visibility']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'visibility': forms.Select(choices=Visibility.choices),
        }

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name']
        if Repository.objects.filter(owner=self.owner, name=name).exists():
            raise forms.ValidationError('You already have a repository with this name.')
        return name

    def save(self, commit=True):
        repo = super().save(commit=False)
        repo.owner = self.owner
        if commit:
            repo.save()
        return repo


class RepositoryEditForm(forms.ModelForm):
    class Meta:
        model = Repository
        fields = ['description', 'visibility']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'visibility': forms.Select(choices=Visibility.choices),
        }
