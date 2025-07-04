from django.shortcuts import render
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate
from poetry_app.models import *
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import *
from django.db import models
from auth_app.forms import*
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from auth_app import *
# Create your views here.



def login_view(request):
    if request.method=='POST':
        form=loginform(request.POST)
        if form.is_valid():
           username=request.POST['username']
           password=request.POST['password']
           user=authenticate(request,username=username,password=password)
           if user is not None:
               login(request,user)
               return( redirect('home'))
           else:
               messages.error(request,'Invalid Username or Password')

    else:
        form=loginform()
    
    return render (request,'auth_app/login.html',{'form':form})

def register_view(request):
    if request.method=='POST':
        form=UserCreationForm(request.POST)
        if form.is_valid():
                form.save()

                return redirect('home')
        else:   
            messages.error(request,form.errors)

    else:
        form=UserCreationForm()
        
    return render(request,'auth_app/register.html',{'form':form})
     






