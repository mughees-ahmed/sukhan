from django.db import models
from django import forms

# Create your models here.
class login (models.Model):
    username=models.CharField(max_length=100)
    password=models.CharField(widget=forms.PasswordInput)