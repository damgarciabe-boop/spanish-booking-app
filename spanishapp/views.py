from urllib import request

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from .forms import StudentRegistrationForm, TimeSlotForm
from .models import LanguageLevel, CourseType, StudentProfile, TeacherProfile, Status, TimeSlot, Booking
from django.utils import timezone
from datetime import timedelta 
from django.core.mail import send_mail
from django.contrib import messages
from .forms import StudentRegistrationForm, TimeSlotForm, EditStudentProfileForm, EditTeacherProfileForm


def home(request):
    return render(request, 'spanishapp/home.html')

def about(request):
    teachers = TeacherProfile.objects.all()
    return render(request, 'spanishapp/about.html', {'teachers': teachers})

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
    error= None 
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
        else:
            error="Invalid username or password. Please try again"
    return render(request, 'spanishapp/login.html', {"error": error})

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def student_dashboard(request):
    if TeacherProfile.objects.filter(id=request.user.id).exists():
        return redirect('teacher_dashboard')
    try:
        StudentProfile.objects.get(id=request.user.id)
    except StudentProfile.DoesNotExist:
        return redirect('/admin/')
    return render(request, 'spanishapp/student_dashboard.html')

@login_required
def teacher_dashboard(request):
    if not TeacherProfile.objects.filter(id=request.user.id).exists():
        return redirect('student_dashboard')
    return render(request, "spanishapp/teacher_dashboard.html")

@login_required
def booking(request):
    if TeacherProfile.objects.filter(id=request.user.id).exists():
        return redirect('teacher_dashboard')
    try:
        student = StudentProfile.objects.get(id=request.user.id)
    except StudentProfile.DoesNotExist:
        return redirect('/admin/')
    if student.level is None:
        return render(request, 'spanishapp/booking.html', {'no_level': True})
    courses = CourseType.objects.filter(min_level__order__lte=student.level.order)
    last_booking = Booking.objects.filter(student=student).order_by('-id').first()
    last_teacher = last_booking.time_slot.teacher if last_booking else None
    return render(request, "spanishapp/booking.html", {
    "courses": courses,
    "student": student,
    "last_teacher": last_teacher,
    "last_booking": last_booking,
})
    
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
        messages.success(request, "Your booking was successful!")
        return redirect("/my_bookings/") 
    return render(request, "spanishapp/booking_confirm.html", {"course":course, "teacher":teacher, "timeslot":timeslot})


@login_required
def my_bookings (request):
    student = StudentProfile.objects.get(id=request.user.id)
    bookings = Booking.objects.filter(student=student)
    return render(request, "spanishapp/my_bookings.html", {"bookings": bookings})


@login_required
def create_timeslot(request):
    teacher = TeacherProfile.objects.get(id=request.user.id)
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
def delete_timeslot(request, timeslot_id):
    timeslot = TimeSlot.objects.get(id=timeslot_id)
    has_booking = Booking.objects.filter(
        time_slot=timeslot,
        status__title__in=["Pending", "Confirmed", "Cancellation Requested"]
    ).exists()
    if not has_booking:
        timeslot.delete()
    return redirect('teacher_dashboard')

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


@login_required
def my_profile(request):
    is_teacher = TeacherProfile.objects.filter(id=request.user.id).exists()
    if is_teacher:
        profile = TeacherProfile.objects.get(id=request.user.id)
    else:
        profile = StudentProfile.objects.get(id=request.user.id)
    return render(request, 'spanishapp/my_profile.html', {'profile': profile, 'is_teacher': is_teacher})

@login_required
def edit_profile(request):
    is_teacher = TeacherProfile.objects.filter(id=request.user.id).exists()
    if is_teacher:
        profile = TeacherProfile.objects.get(id=request.user.id)
        FormClass = EditTeacherProfileForm
    else:
        profile = StudentProfile.objects.get(id=request.user.id)
        FormClass = EditStudentProfileForm

    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            if new_password:
                if new_password == confirm_password:
                    profile.set_password(new_password)
                    profile.save()
                else:
                    return render(request, 'spanishapp/edit_profile.html', {
                        'form': form,
                        'is_teacher': is_teacher,
                        'error': 'Passwords do not match'
                    })
            return redirect('my_profile')
    else:
        form = FormClass(instance=profile)

    return render(request, 'spanishapp/edit_profile.html', {
        'form': form,
        'is_teacher': is_teacher,
        'profile': profile
    })

@login_required
def teacher_availability(request):
    if not TeacherProfile.objects.filter(id=request.user.id).exists():
        return redirect('student_dashboard')
    teacher = TeacherProfile.objects.get(id=request.user.id)
    
    time_slots = TimeSlot.objects.filter(
        teacher=teacher,
        end_date_time__gte=timezone.now()
    ).order_by('start_date_time')
    
    return render(request, "spanishapp/teacher_availability.html", {"time_slots": time_slots})

@login_required
def teacher_bookings(request):
    if not TeacherProfile.objects.filter(id=request.user.id).exists():
        return redirect('student_dashboard')
    teacher = TeacherProfile.objects.get(id=request.user.id)
    
    past_bookings = Booking.objects.filter(
        time_slot__teacher=teacher,
        time_slot__end_date_time__lt=timezone.now(),
        status__title__in=["Pending", "Confirmed"]
    )
    completed_status = Status.objects.get(title="Completed")
    for booking in past_bookings:
        booking.status = completed_status
        booking.save()

    pending = Booking.objects.filter(time_slot__teacher=teacher, status__title="Pending").order_by('time_slot__start_date_time')
    confirmed = Booking.objects.filter(time_slot__teacher=teacher, status__title="Confirmed").order_by('time_slot__start_date_time')
    cancellation_requested = Booking.objects.filter(time_slot__teacher=teacher, status__title="Cancellation Requested").order_by('time_slot__start_date_time')
    completed = Booking.objects.filter(time_slot__teacher=teacher, status__title="Completed").order_by('time_slot__start_date_time')
    cancelled = Booking.objects.filter(time_slot__teacher=teacher, status__title="Cancelled").order_by('time_slot__start_date_time')

    return render(request, "spanishapp/teacher_bookings.html", {
        "pending": pending,
        "confirmed": confirmed,
        "cancellation_requested": cancellation_requested,
        "completed": completed,
        "cancelled": cancelled,
    })













