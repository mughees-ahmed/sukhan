        return redirect('home')
        else:   
            messages.error(request,'user already exists')
    else:
        form=UserCreation