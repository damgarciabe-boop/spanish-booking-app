from datetime import timedelta
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from spanishapp.models import Booking
class Command(BaseCommand):
    help = "Send email reminders to students with bookings in the next 24 hours."

    def handle(self, *args, **kwargs):
        now = timezone.now()
        tomorrow = now + timedelta(days=1)
        bookings = Booking.objects.filter(
            status__title='Confirmed', 
            time_slot__start_date_time__range=(now, tomorrow)
            )
        for booking in bookings:
            student_email = booking.student.email
            send_mail(
                'Reminder: Upcoming Spanish Class',
                f'Hola! {booking.student.first_name}, this is a reminder for your upcoming Spanish class on {booking.course.title} with {booking.time_slot.teacher.first_name} at {booking.time_slot.start_date_time.strftime("%Y-%m-%d %H:%M")} ¡Nos vemos pronto!',
                'noreply@spanish1to1.com',
                [booking.student.email],
                fail_silently=False,
            )
        self.stdout.write(self.style.SUCCESS(f'Successfully sent {bookings.count()} reminders to students with upcoming bookings.'))