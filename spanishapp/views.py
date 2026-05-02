from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import StudentRegistrationForm, TimeSlotForm
from .models import LanguageLevel, CourseType, StudentProfile, TeacherProfile, Status, TimeSlot, Booking
from django.utils import timezone
from datetime import timedelta 
from django.core.mail import send_mail

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
    time_slots=TimeSlot.objects.filter(teacher=teacher,course=course,is_available=True)
    return render(request, "spanishapp/booking_timeslot.html", {"course":course, "teacher":teacher, "time_slots":time_slots})

@login_required
def booking_confirm (request, course_id, teacher_id, timeslot_id):
    course = CourseType.objects.get(id=course_id)
    teacher= TeacherProfile.objects.get(id=teacher_id)
    timeslot=TimeSlot.objects.get(id=timeslot_id)
    
    if request.method == "POST":
        already_booked = Booking.objects.filter(time_slot=timeslot, status__title__in=["Pending", "Confirmed"]).exists()
        
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


@login_required
def teacher_dashboard(request):
    teacher = request.user.teacherprofile
    bookings = Booking.objects.filter(time_slot__teacher=teacher)
    return render(request, "spanishapp/teacher_dashboard.html", {"bookings": bookings})


@login_required
def create_timeslot(request):
    teacher = request.user.teacherprofile
    if request.method == "POST":
        form = TimeSlotForm(request.POST)
        if form.is_valid():
            timeslot = form.save(commit=False)
            timeslot.teacher = teacher
            timeslot.is_available = True
            timeslot.save()
            return redirect('teacher_dashboard')
    else:
        form = TimeSlotForm()
        form.fields['course'].queryset = teacher.courses.all()
    return render(request, "spanishapp/create_timeslot.html", {"form": form})

@login_required
def confirm_booking(request, booking_id):
    booking = Booking.objects.get(id=booking_id)
    confirmed_status = Status.objects.get(title="Confirmed")
    booking.status = confirmed_status
    booking.save()
    send_mail(
        'Booking Confirmed',
        f'Hola! {booking.student.first_name}, your booking for {booking.course.title} with {booking.time_slot.teacher.first_name} has been confirmed.',
        'noreply@spanish1to1.com',
        [booking.student.email],
        fail_silently=False,
        html_message=f'''
        <div style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #3776ab;">Booking Confirmed</h2
            <p>Hola! {booking.student.first_name},</p>
            <p>Your booking for <strong>{booking.course.title}</strong> with <strong>{booking.time_slot.teacher.first_name}</strong> has been confirmed.</p>
            <hr>
            <p style="color:ff0000; font-style: italic;">Please remember to cancel at least 24 hours in advance if you want to reschedule or cancel your booking to avoid any cancellation fees.</p>
            <hr>
            <p>Best regards,</p>
            <p><strong>Spanish Lessons One to One</strong></p>
            <hr>
            <p style="font-size: 0.8em; color: #777;">This is an automated message, please do not reply. If you have any questions, contact us at admin@spanish1to1.com.</p>
        </div>
        ''',
    )
    return redirect('teacher_dashboard')

@login_required
def cancel_booking(request, booking_id):
    booking = Booking.objects.get(id=booking_id)
    cancelled_status = Status.objects.get(title="Cancelled")
    booking.status = cancelled_status
    booking.save()
    booking.time_slot.is_available = True
    booking.time_slot.save()
    send_mail(
        'Booking Cancelled',
        f'Hola! {booking.student.first_name}, your booking for {booking.course.title} with {booking.time_slot.teacher.first_name} has been cancelled.',
        'noreply@spanish1to1.com',
        [booking.student.email],
        fail_silently=False,
        html_message=f'''
        <div style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #3776ab;">Booking Cancelled</h2
            <p>Hola! {booking.student.first_name},</p>
            <p>Your booking for <strong>{booking.course.title}</strong> with <strong>{booking.time_slot.teacher.first_name}</strong> has been cancelled.</p>
            <hr>
            <p>Best regards,</p>
            <p><strong>Spanish Lessons One to One</strong></p>
            <hr>
            <p style="font-size: 0.8em; color: #777;">This is an automated message, please do not reply. If you have any questions, contact us at admin@spanish1to1.com.</p>
        </div>
        '''
    )
    return redirect('teacher_dashboard')

@login_required
def delete_booking(request, booking_id):
    booking = Booking.objects.get(id=booking_id)
    booking.delete()
    return redirect('teacher_dashboard')

@login_required
def request_cancellation(request, booking_id):
    booking = Booking.objects.get(id=booking_id)
    if booking.time_slot.start_date_time - timezone.now() < timedelta(hours=24):
        return redirect('my_bookings')
    cancelled_status = Status.objects.get(title="Cancellation Requested")
    booking.status = cancelled_status
    booking.save()
    return redirect('my_bookings')