from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import StudentRegistrationForm
from .models import LanguageLevel, CourseType, StudentProfile, TeacherProfile, Status, TimeSlot, Booking 

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

@login_required
def booking (request):
    courses = CourseType.objects.all()
    return render(request, "spanishapp/booking.html", {"courses": courses} )

@login_required
def booking_teachers (request, course_id):
    course = CourseType.objects.get(id=course_id)
    teachers= TeacherProfile.objects.filter(courses=course)
    return render(request, "spanishapp/booking_teachers.html", {"course": course, "teachers": teachers})

@login_required
def booking_timeslot (request, course_id, teacher_id):
    course = CourseType.objects.get(id=course_id)
    teacher= TeacherProfile.objects.get(id=teacher_id)
    time_slots=TimeSlot.objects.filter(teacher=teacher,is_available=True)
    return render(request, "spanishapp/booking_timeslot.html", {"course":course, "teacher":teacher, "time_slots":time_slots})

@login_required
def booking_confirm (request, course_id, teacher_id, timeslot_id):
    course = CourseType.objects.get(id=course_id)
    teacher= TeacherProfile.objects.get(id=teacher_id)
    timeslot=TimeSlot.objects.get(id=timeslot_id)
    
    if request.method == "POST":
        already_booked = Booking.objects.filter(time_slot=timeslot).exists()
        
        if already_booked:
            return redirect("/my_bookings/")
        
        student=StudentProfile.objects.get(id=request.user.id)
        status=Status.objects.get(title="Pending")
        Booking.objects.create(student=student, course=course, time_slot=timeslot, status=status)
        
        timeslot.is_available=False
        timeslot.save()
        return redirect("/my_bookings/") 
    return render(request, "spanishapp/booking_confirm.html", {"course":course, "teacher":teacher, "timeslot":timeslot})


@login_required
def my_bookings (request):
    student = StudentProfile.objects.get(id=request.user.id)
    bookings = Booking.objects.filter(student=student)
    return render(request, "spanishapp/my_bookings.html", {"bookings": bookings})

