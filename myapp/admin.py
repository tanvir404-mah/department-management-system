from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Student, Teacher, Attendance, Result, Assignment, 
    Notice, Resource, Course, Department, ProjectThesis, 
    LabAssistant, LabItem, ResourceRequisition, AlumniJobBoard
)

# CustomUser Admin
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password', 'role', 'phone', 'profile_picture', 'address')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'phone', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email', 'username')
    ordering = ('username',)

admin.site.register(CustomUser, CustomUserAdmin)

# Profile Admins
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'roll_number', 'semester', 'shift', 'cgpa')
    search_fields = ('user__username', 'roll_number')
    list_filter = ('semester', 'shift', 'department')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'designation', 'department')
    search_fields = ('user__username', 'designation')
    list_filter = ('department',)

@admin.register(LabAssistant)
class LabAssistantAdmin(admin.ModelAdmin):
    list_display = ('user', 'department')

# Academic Admins
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'credits', 'department')
    search_fields = ('code', 'title')
    list_filter = ('department',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')

# Performance Admins
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'date', 'status')
    list_filter = ('status', 'date', 'course')

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'marks', 'grade_point', 'letter_grade')
    list_filter = ('letter_grade', 'course')

# Project & Thesis
@admin.register(ProjectThesis)
class ProjectThesisAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'supervisor', 'status')
    list_filter = ('status',)

# Lab & Resources
@admin.register(LabItem)
class LabItemAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'serial_number', 'category', 'status')
    list_filter = ('category', 'status')

@admin.register(ResourceRequisition)
class ResourceRequisitionAdmin(admin.ModelAdmin):
    list_display = ('item', 'requested_by', 'request_date', 'status')
    list_filter = ('status',)

# Communication & Others
admin.site.register(Notice)
admin.site.register(Resource)
admin.site.register(AlumniJobBoard)
admin.site.register(Assignment)
