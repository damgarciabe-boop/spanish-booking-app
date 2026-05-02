from django import forms
from .models import StudentProfile, TimeSlot

class StudentRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = StudentProfile
        fields = ['username', 'first_name', 'last_name', 'email', 'date_of_birth',
                  'country_of_birth', 'country_of_residence', 'level', 'photo', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password != confirm_password:
            raise forms.ValidationError('Passwords do not match')
        return cleaned_data
    
class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = ['course','start_date_time', 'end_date_time']
        widgets = {
            'start_date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }