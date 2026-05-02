from django.contrib import admin
from django.urls import path
from spanishapp import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('register/', views.register_student, name='register_student'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/timeslot/create/', views.create_timeslot, name='create_timeslot'),
    path('booking/', views.booking, name='booking'),
    path('booking/teachers/<int:course_id>/', views.booking_teachers, name='booking_teachers'),
    path('booking/timeslots/<int:course_id>/<int:teacher_id>/', views.booking_timeslot, name='bookingtimeslot'),
    path('booking/confirm/<int:course_id>/<int:teacher_id>/<int:timeslot_id>/', views.booking_confirm, name='booking_confirm'),
    path('my_bookings/', views.my_bookings, name='my_bookings'),
    path('booking/confirm/<int:booking_id>/', views.confirm_booking, name='confirm_booking'),
    path('booking/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('booking/delete/<int:booking_id>/', views.delete_booking, name='delete_booking'),
   path('booking/request_cancellation/<int:booking_id>/', views.request_cancellation, name='request_cancellation'),
    
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
