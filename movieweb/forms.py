from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from .models import Actor, Movie, Role
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignupForm(UserCreationForm):
    email = forms.EmailField(max_length=200, help_text='Required')
    birthday = forms.DateField()
    class Meta:
        model = User
        fields = ('username', 'email', 'birthday', 'password1', 'password2')

class ActorForm(forms.ModelForm):
    class Meta:
        model = Actor
        exclude = ['count', 'discovered_by', 'tmdbID']

class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        exclude = ['count', 'discovered_by', 'tmdbID']

class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        exclude = ['count', 'discovered_by', 'tmdbID']


