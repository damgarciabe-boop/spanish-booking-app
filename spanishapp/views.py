from urllib import request

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from .forms import StudentRegistrationForm, TimeSlotForm
from .models import LanguageLevel, CourseType, StudentProfile, TeacherProfile, Status, TimeSlot, Booking, ClassPackage
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
            reference_code = form.cleaned_data['reference_code']
            try:
                package = ClassPackage.objects.get(code=reference_code)
                student.package = package
            except ClassPackage.DoesNotExist:
                form.add_error('reference_code', 'Invalid reference code')
                return render(request, 'spanishapp/register_student.html', {'form': form})
            student.save()
            return render(request, 'spanishapp/register_student.html', {'success': True})
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
       student = StudentProfile.objects.get(id=request.user.id)
    except StudentProfile.DoesNotExist:
        return redirect('/admin/')
    completed = Booking.objects.filter(
        student=student,
        status__title="Completed"
    ).count()
    return render(request, 'spanishapp/student_dashboard.html', {
        'student': student,
        'completed': completed
        })

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

    completed_count = Booking.objects.filter(
        student=student,
        status__title="Completed"
    ).count()

    if student.package and completed_count >= student.package.total_classes:
        return render(request, 'spanishapp/booking.html', {'no_classes_left': True})

    age = student.get_age()
    if age and age < 18:
        courses = CourseType.objects.filter(title__icontains="Children")
    else:
        courses = CourseType.objects.exclude(title__icontains="Children")
    
    courses = courses.filter(min_level__order__lte=student.level.order)
    
    last_booking = Booking.objects.filter(student=student).order_by('-id').first()
    last_teacher = last_booking.time_slot.teacher if last_booking else None
    
    return render(request, "spanishapp/booking.html", {
        "courses": courses,
        "student": student,
        "last_teacher": last_teacher,
        "last_booking": last_booking,
    })
    
 
@login_required
def booking_teachers(request, course_id):
    course = CourseType.objects.get(id=course_id)
    teachers = TeacherProfile.objects.filter(courses=course)
    return render(request, "spanishapp/booking_teachers.html", {"course": course, "teachers": teachers})

@login_required
def booking_timeslot(request, course_id, teacher_id):
    course = CourseType.objects.get(id=course_id)
    teacher = TeacherProfile.objects.get(id=teacher_id)
    time_slots = TimeSlot.objects.filter(
        teacher=teacher,
        is_available=True,
        start_date_time__gt=timezone.now()
    ).order_by('start_date_time')
    return render(request, "spanishapp/booking_timeslot.html", {"course": course, "teacher": teacher, "time_slots": time_slots})

@login_required
def booking_confirm(request, course_id, teacher_id, timeslot_id):
    course = CourseType.objects.get(id=course_id)
    teacher = TeacherProfile.objects.get(id=teacher_id)
    timeslot = TimeSlot.objects.get(id=timeslot_id)
    
    if request.method == "POST":
        already_booked = Booking.objects.filter(time_slot=timeslot, status__title__in=["Pending", "Confirmed"]).exists()
        
        if already_booked:
            return redirect("/my_bookings/")
        
        student = StudentProfile.objects.get(id=request.user.id)
        status = Status.objects.get(title="Pending")
        Booking.objects.create(student=student, course=course, time_slot=timeslot, status=status)
        
        timeslot.is_available = False
        timeslot.save()

        send_mail(
            'New Booking Pending Confirmation',
            f'You have a new booking request from {student.first_name} {student.last_name}.',
            'noreply@spanish1to1.com',
            [teacher.email],
            fail_silently=False,
            html_message=f'''
            <div style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color: #C47A7A;">New Booking Request</h2>
                <p>Hola {teacher.first_name},</p>
                <p>You have a new booking request pending confirmation.</p>
                <hr>
                <p><strong>Student:</strong> {student.first_name} {student.last_name}</p>
                <p><strong>Course:</strong> {course.title}</p>
                <p><strong>Date:</strong> {timeslot.start_date_time.strftime("%B %d, %Y")}</p>
                <p><strong>Time:</strong> {timeslot.start_date_time.strftime("%I:%M %p")} - {timeslot.end_date_time.strftime("%I:%M %p")}</p>
                <hr>
                <p>Please log in to confirm or cancel this booking.</p>
                <hr>
                <p style="font-size: 0.8em; color: #777;">This is an automated message, please do not reply.</p>
            </div>
            ''',
        )

        return redirect("/my_bookings/")
    return render(request, "spanishapp/booking_confirm.html", {"course": course, "teacher": teacher, "timeslot": timeslot})

@login_required
def my_bookings(request):
    student = StudentProfile.objects.get(id=request.user.id)

    past_bookings = Booking.objects.filter(
        student=student,
        time_slot__end_date_time__lt=timezone.now(),
        status__title="Confirmed"
    )
    completed_status = Status.objects.get(title="Completed")
    for booking in past_bookings:
        booking.status = completed_status
        booking.save()

        if student.package:
            total_classes = student.package.total_classes
            completed_count = Booking.objects.filter(
                student=student,
                status__title="Completed"
            ).count()

            if completed_count == total_classes:
                send_mail(
                    'Your class package is complete',
                    f'Hola {student.first_name}, you have completed all your classes.',
                    'noreply@spanish1to1.com',
                    [student.email],
                    fail_silently=False,
                    html_message=f'''
                    <div style="font-family: Arial, sans-serif; color: #333;">
                        <h2 style="color: #C47A7A;">You have completed your class package!</h2>
                        <p>Hola {student.first_name},</p>
                        <p>You have completed all <strong>{total_classes} classes</strong> in your package. We hope you enjoyed your Spanish learning journey!</p>
                        <hr>
                        <p>If you would like to continue learning, please contact us at <a href="mailto:admin@spanish1to1.com">admin@spanish1to1.com</a> to renew your package.</p>
                        <hr>
                        <p>Best regards,</p>
                        <p><strong>Spanish Lessons One to One</strong></p>
                        <hr>
                        <p style="font-size: 0.8em; color: #777;">This is an automated message, please do not reply.</p>
                    </div>
                    ''',
                )
            elif completed_count == total_classes - 1:
                send_mail(
                    'You have 1 class left in your package',
                    f'Hola {student.first_name}, you have 1 class left in your package.',
                    'noreply@spanish1to1.com',
                    [student.email],
                    fail_silently=False,
                    html_message=f'''
                    <div style="font-family: Arial, sans-serif; color: #333;">
                        <h2 style="color: #C47A7A;">Only 1 class left!</h2>
                        <p>Hola {student.first_name},</p>
                        <p>You have only <strong>1 class remaining</strong> in your package of {total_classes} classes.</p>
                        <hr>
                        <p>We recommend contacting us soon to renew your package so you don't lose your learning momentum!</p>
                        <p>Contact us at <a href="mailto:admin@spanish1to1.com">admin@spanish1to1.com</a> to renew.</p>
                        <hr>
                        <p>Best regards,</p>
                        <p><strong>Spanish Lessons One to One</strong></p>
                        <hr>
                        <p style="font-size: 0.8em; color: #777;">This is an automated message, please do not reply.</p>
                    </div>
                    ''',
                )

    Booking.objects.filter(
        student=student,
        status__title="Cancelled"
    ).delete()

    pending = Booking.objects.filter(student=student, status__title="Pending").order_by('time_slot__start_date_time')
    confirmed = Booking.objects.filter(student=student, status__title="Confirmed").order_by('time_slot__start_date_time')
    cancellation_requested = Booking.objects.filter(student=student, status__title="Cancellation Requested").order_by('time_slot__start_date_time')
    completed = Booking.objects.filter(student=student, status__title="Completed").order_by('time_slot__start_date_time')

    return render(request, "spanishapp/my_bookings.html", {
        "pending": pending,
        "confirmed": confirmed,
        "cancellation_requested": cancellation_requested,
        "completed": completed,
    })
    
@login_required
def create_timeslot(request):
    teacher = TeacherProfile.objects.get(id=request.user.id)
    if request.method == "POST":
        form = TimeSlotForm(request.POST)
        if form.is_valid():
            start = form.cleaned_data['start_date_time']
            duplicate = TimeSlot.objects.filter(teacher=teacher, start_date_time=start).exists()
            if duplicate:
                form.add_error('start_date_time', 'You already have a time slot at this date and time.')
                return render(request, "spanishapp/create_timeslot.html", {"form": form, "teacher": teacher})
            timeslot = form.save(commit=False)
            timeslot.teacher = teacher
            timeslot.is_available = True
            timeslot.save()
            return render(request, "spanishapp/create_timeslot.html", {"form": TimeSlotForm(), "success": True, "teacher": teacher})
    else:
        form = TimeSlotForm()
    return render(request, "spanishapp/create_timeslot.html", {"form": form, "teacher": teacher})


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
            <h2 style="color: #3776ab;">Booking Confirmed</h2>
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
            <h2 style="color: #3776ab;">Booking Cancelled</h2>
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
    teacher = booking.time_slot.teacher
    student = booking.student

    if booking.status.title == "Pending":
        cancelled_status = Status.objects.get(title="Cancelled")
        booking.status = cancelled_status
        booking.save()
        booking.time_slot.is_available = True
        booking.time_slot.save()
        send_mail(
            'Booking Cancelled by Student',
            f'{student.first_name} {student.last_name} has cancelled their booking.',
            'noreply@spanish1to1.com',
            [teacher.email],
            fail_silently=False,
            html_message=f'''
            <div style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color: #C47A7A;">Booking Cancelled</h2>
                <p>Hola {teacher.first_name},</p>
                <p>A student has cancelled their booking before confirmation.</p>
                <hr>
                <p><strong>Student:</strong> {student.first_name} {student.last_name}</p>
                <p><strong>Course:</strong> {booking.course.title}</p>
                <p><strong>Date:</strong> {booking.time_slot.start_date_time.strftime("%B %d, %Y")}</p>
                <p><strong>Time:</strong> {booking.time_slot.start_date_time.strftime("%I:%M %p")} - {booking.time_slot.end_date_time.strftime("%I:%M %p")}</p>
                <hr>
                <p style="font-size: 0.8em; color: #777;">This is an automated message, please do not reply.</p>
            </div>
            ''',
        )
        return redirect('my_bookings')

    if booking.time_slot.start_date_time - timezone.now() < timedelta(hours=24):
        return render(request, 'spanishapp/request_cancellation.html', {
            'booking': booking,
            'too_late': True
        })

    if request.method == 'POST':
        reason = request.POST.get('reason')
        cancelled_status = Status.objects.get(title="Cancellation Requested")
        booking.status = cancelled_status
        booking.cancellation_reason = reason
        booking.save()
        send_mail(
            'Cancellation Request',
            f'{student.first_name} {student.last_name} has requested to cancel their booking.',
            'noreply@spanish1to1.com',
            [teacher.email],
            fail_silently=False,
            html_message=f'''
            <div style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color: #C47A7A;">Cancellation Request</h2>
                <p>Hola {teacher.first_name},</p>
                <p>A student has requested to cancel their booking.</p>
                <hr>
                <p><strong>Student:</strong> {student.first_name} {student.last_name}</p>
                <p><strong>Course:</strong> {booking.course.title}</p>
                <p><strong>Date:</strong> {booking.time_slot.start_date_time.strftime("%B %d, %Y")}</p>
                <p><strong>Time:</strong> {booking.time_slot.start_date_time.strftime("%I:%M %p")} - {booking.time_slot.end_date_time.strftime("%I:%M %p")}</p>
                <p><strong>Reason:</strong> {reason}</p>
                <hr>
                <p>Please log in to confirm or cancel this booking.</p>
                <hr>
                <p style="font-size: 0.8em; color: #777;">This is an automated message, please do not reply.</p>
            </div>
            ''',
        )
        return redirect('my_bookings')

    return render(request, 'spanishapp/request_cancellation.html', {
        'booking': booking,
        'too_late': False
    })

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


@login_required
def teacher_students(request):
    if not TeacherProfile.objects.filter(id=request.user.id).exists():
        return redirect('student_dashboard')
    teacher = TeacherProfile.objects.get(id=request.user.id)
    
    student_ids = Booking.objects.filter(
        time_slot__teacher=teacher
    ).values_list('student', flat=True).distinct()
    
    students_data = []
    for student_id in student_ids:
        student = StudentProfile.objects.get(id=student_id)
        completed_count = Booking.objects.filter(
            time_slot__teacher=teacher,
            student=student,
            status__title="Completed"
        ).count()
        cancelled_count = Booking.objects.filter(
            time_slot__teacher=teacher,
            student=student,
            status__title="Cancelled"
        ).count()
        next_booking = Booking.objects.filter(
            time_slot__teacher=teacher,
            student=student,
            status__title__in=["Confirmed", "Pending"],
            time_slot__start_date_time__gte=timezone.now()
        ).order_by('time_slot__start_date_time').first()
        students_data.append({
            'student': student,
            'completed': completed_count,
            'cancelled': cancelled_count,
            'next_booking': next_booking,
        })
    
    return render(request, "spanishapp/teacher_students.html", {'students_data': students_data})

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        send_mail(
            f'Contact Form - {subject}',
            f'From: {name} ({email})\n\nMessage:\n{message}',
            email,
            ['admin@spanish1to1.com'],
            fail_silently=False,
        )
        return render(request, 'spanishapp/contact.html', {'success': True})
    return render(request, 'spanishapp/contact.html')






