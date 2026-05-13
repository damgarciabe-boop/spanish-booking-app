from django.contrib import admin
from django.urls import path
from spanishapp import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('register/', views.register_student, name='register_student'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/timeslot/create/', views.create_timeslot, name='create_timeslot'),
    path('teacher/timeslot/delete/<int:timeslot_id>/', views.delete_timeslot, name='delete_timeslot'),
    path('booking/', views.booking, name='booking'),
    path('booking/teachers/<int:course_id>/', views.booking_teachers, name='booking_teachers'),
    path('booking/timeslots/<int:course_id>/<int:teacher_id>/', views.booking_timeslot, name='bookingtimeslot'),
    path('booking/confirm/<int:course_id>/<int:teacher_id>/<int:timeslot_id>/', views.booking_confirm, name='booking_confirm'),
    path('my_bookings/', views.my_bookings, name='my_bookings'),
    path('booking/confirm/<int:booking_id>/', views.confirm_booking, name='confirm_booking'),
    path('booking/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('booking/delete/<int:booking_id>/', views.delete_booking, name='delete_booking'),
    path('booking/request_cancellation/<int:booking_id>/', views.request_cancellation, name='request_cancellation'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='spanishapp/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='spanishapp/password_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='spanishapp/password_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='spanishapp/password_complete.html'), name='password_reset_complete'),
    path('profile/', views.my_profile, name='my_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('teacher/availability/', views.teacher_availability, name='teacher_availability'),
    path('teacher/bookings/', views.teacher_bookings, name='teacher_bookings'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
