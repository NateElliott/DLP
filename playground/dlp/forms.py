from django import forms
from .models import UserProfile, InviteCode
from django.contrib.auth.models import User

from .models import Modules

class UserForm(forms.ModelForm):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username','password')


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username','password',)



class ModuleForm(forms.ModelForm):

    class Meta:
        model = Modules
        fields = ('name','description','module',)