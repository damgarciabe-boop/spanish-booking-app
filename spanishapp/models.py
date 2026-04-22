from django.db import models
from django.contrib.auth.models import User
from django_countries.fields import CountryField


class LanguageLevel(models.Model):
    name_level = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return self.name_level


class CourseType(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    min_level = models.ForeignKey(
        LanguageLevel,
        on_delete=models.PROTECT
    )

    def __str__(self):
        return self.title


class StudentProfile(User):
    photo = models.ImageField(upload_to='student_photos/', null=True, blank=True)
    nationality = CountryField()
    level = models.ForeignKey(
        LanguageLevel,
        on_delete=models.PROTECT
    )

    class Meta:
        verbose_name = "Student"


class TeacherProfile(User):
    photo = models.ImageField(upload_to='teacher_photos/')
    biography = models.TextField()
    nationality = CountryField()
    courses = models.ManyToManyField(CourseType, blank=True)

    class Meta:
        verbose_name = "Teacher"


class Status(models.Model):
    title = models.CharField(max_length=50)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Statuses"


class TimeSlot(models.Model):
    start_date_time = models.DateTimeField()
    end_date_time = models.DateTimeField()
    is_available = models.BooleanField(default=True)
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.teacher} | {self.start_date_time}"


class Booking(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        CourseType,
        on_delete=models.PROTECT
    )
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.PROTECT
    )
    status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT
    )

    def __str__(self):
        return f"{self.student} | {self.course} | {self.status}"