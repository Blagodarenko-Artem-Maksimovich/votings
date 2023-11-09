from django import forms
from django_registration.forms import RegistrationForm

from main.models import User


class VotingNameTypeForm(forms.Form):
    name = forms.CharField(label='Введите название голосования:', max_length=63)
    type = forms.IntegerField(label='Введите номер выбранного варианта:', min_value=1, max_value=3)
    description = forms.CharField(label='Введите вопрос голосования:', max_length=255)


class OptionsCountForm(forms.Form):
    choice = forms.IntegerField(label='Введите количество вариантов ответа:', min_value=3, max_value=10)


class VotingRegistrationForm(RegistrationForm):
    class Meta(RegistrationForm.Meta):
        model = User
