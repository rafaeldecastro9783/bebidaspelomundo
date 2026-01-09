from django import forms
from.models import OrdemPedido, Cliente
from django.db.models import fields
from django.forms import ModelForm, TextInput, EmailInput, PasswordInput
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password

class registrar_cliente_form(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Usuário', 'class': 'form-control', 'style': 'width : 300px; display : flex;'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Sua Senha', 'class': 'form-control', 'style': 'width : 300px; display : flex;'}))
    email = forms.CharField(widget=forms.EmailInput(attrs={'placeholder': 'exaemplo@exemplo.com', 'class': 'form-control', 'style': 'width : 300px; display : flex;'}))
    class Meta:
        model = Cliente
        fields = ["username", "password", "email", "nome_completo", "endereco"]
        widgets = {
            'nome_completo': TextInput(attrs={
                'class': 'form-control',
                'style': 'max-width: 300px',
                'placeholder': 'Seu nome completo'
            }),
            'endereco': TextInput(attrs={
                'class': 'form-control',
                'style': 'max-width: 300px',
                'placeholder': 'Rua, N, Bairro, Cidade - EStado + CEP'
            }),
        }

    def clean_username(self):
        unome = self.cleaned_data.get("username")
        if User.objects.filter(username=unome).exists():
            raise forms.ValidationError('Este cliente já existe')
        return unome
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Hash the password before saving to the database
        instance.password = make_password(self.cleaned_data["password"])
        if commit:
            instance.save()
        return instance

class ClienteEntrarForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Usuário', 'class': 'form-control', 'style': 'width : 300px; display : flex;'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Sua Senha', 'class': 'form-control', 'style': 'width : 300px; display : flex;'}))
    


