from django import forms
from .models import (
    Student, Teacher, Department, Notice, Resource, 
    CustomUser, Course, ProjectThesis, LabItem, 
    ResourceRequisition, AlumniJobBoard, Assignment,
    HomeBanner, GlobalNotice
)
from django.contrib.auth.forms import UserCreationForm

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'role', 'phone')

class OTPStep1Form(forms.Form):
    roll_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 outline-none',
            'placeholder': 'Enter roll number'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 outline-none',
            'placeholder': 'Enter phone number'
        })
    )

class OTPStep2Form(forms.Form):
    otp_code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-4 text-center text-2xl font-bold tracking-widest rounded-lg border-2 border-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200 outline-none',
            'placeholder': '· · · · · ·',
            'autocomplete': 'off'
        })
    )

class OTPStep3Form(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 outline-none',
            'placeholder': 'Choose a Strong Password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 outline-none',
            'placeholder': 'Confirm Password'
        })
    )

class StudentRegistrationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ['username', 'email', 'phone']

class TeacherRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ['username', 'email', 'phone']

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = '__all__'

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = '__all__'

class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = '__all__'

class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = '__all__'

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = '__all__'

class ProjectThesisForm(forms.ModelForm):
    class Meta:
        model = ProjectThesis
        fields = '__all__'

class LabItemForm(forms.ModelForm):
    class Meta:
        model = LabItem
        fields = '__all__'

class AlumniJobBoardForm(forms.ModelForm):
    class Meta:
        model = AlumniJobBoard
        fields = '__all__'

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = '__all__'

class HomeBannerForm(forms.ModelForm):
    class Meta:
        model = HomeBanner
        fields = ['image', 'title', 'subtitle', 'is_active']

class GlobalNoticeForm(forms.ModelForm):
    class Meta:
        model = GlobalNotice
        fields = ['category', 'title', 'content', 'file_attachment', 'is_latest']
