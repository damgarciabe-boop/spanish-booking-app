from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import StudentRegistrationForm

def home(request):
    return render(request, 'spanishapp/home.html')

def register_student(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)
            student.set_password(form.cleaned_data['password'])
            student.save()
            return redirect('login')
    else:
        form = StudentRegistrationForm()
    return render(request, 'spanishapp/register_student.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if hasattr(user, 'teacherprofile'):
                return redirect('teacher_dashboard')
            else:
                return redirect('student_dashboard')
    return render(request, 'spanishapp/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def student_dashboard(request):
    return render(request, 'spanishapp/student_dashboard.html')

@login_required
def teacher_dashboard(request):
    return render(request, 'spanishapp/teacher_dashboard.html')