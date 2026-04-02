from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
import uuid

# -----------------------
# Custom User & Roles
# -----------------------
def generate_student_id():
    return "FPI-CST-" + str(uuid.uuid4().hex)[:8].upper()

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('hod', 'Head of Department'),
        ('lab_assistant', 'Lab Assistant'),
        ('admin', 'Admin'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

# -----------------------
# Academic Module
# -----------------------
class Department(models.Model):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=10, unique=True, null=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    credits = models.DecimalField(max_digits=3, decimal_places=1)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="courses")
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True)
    is_obe_mapped = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.code}: {self.title}"

class ClassRoutine(models.Model):
    DAY_CHOICES = [
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
    ]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="routines")
    teacher = models.ForeignKey('Teacher', on_delete=models.SET_NULL, null=True)
    day_of_week = models.CharField(max_length=15, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room_number = models.CharField(max_length=20, blank=True, null=True)
    semester = models.IntegerField(default=1)
    shift = models.CharField(max_length=10, choices=[('1st', '1st'), ('2nd', '2nd')])

    def __str__(self):
        return f"{self.day_of_week} - {self.course.code} ({self.start_time})"

class Teacher(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="teacher_profile")
    designation = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    courses = models.ManyToManyField(Course, blank=True, related_name="teachers")
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.designation} {self.user.get_full_name() or self.user.username}"

class HOD(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hod_profile")
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"HOD {self.department.name} - {self.user.username}"

class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")
    student_id = models.CharField(max_length=20, unique=True, default=generate_student_id, null=True, blank=True)
    roll_number = models.CharField(max_length=20, blank=True, null=True)
    registration_number = models.CharField(max_length=20, blank=True, null=True)
    semester = models.IntegerField(default=1)
    shift = models.CharField(max_length=10, choices=[('1st', '1st'), ('2nd', '2nd')])
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    courses = models.ManyToManyField(Course, blank=True, related_name="students")
    guardian_name = models.CharField(max_length=100, blank=True, null=True)
    guardian_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Academic Standing
    cgpa = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)

    def calculate_cgpa(self):
        results = self.results.all()
        if not results:
            return 0.00
        total_points = sum(r.grade_point * r.course.credits for r in results if r.grade_point)
        total_credits = sum(r.course.credits for r in results if r.grade_point)
        if total_credits == 0:
            return 0.00
        self.cgpa = total_points / total_credits
        self.save()
        return self.cgpa

    def __str__(self):
        return f"{self.user.username} - {self.roll_number}"

# -----------------------
# Attendance & Results
# -----------------------
class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendances")
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    date = models.DateField(default=timezone.now)
    status = models.CharField(
        max_length=10,
        choices=[('Present','Present'), ('Absent','Absent'), ('Late','Late')]
    )

    class Meta:
        unique_together = ('student', 'course', 'date')

    def __str__(self):
        return f"{self.student.user.username} - {self.course.code} - {self.date}"

class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="results")
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    marks = models.FloatField()
    ca_marks = models.FloatField(default=0.0, help_text="Continuous Assessment Marks")
    semester = models.IntegerField(default=1) # Added to track results per semester
    grade_point = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    letter_grade = models.CharField(max_length=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Total marks including CA
        total = self.marks + self.ca_marks
        if total >= 80: self.grade_point, self.letter_grade = 4.00, 'A+'
        elif total >= 75: self.grade_point, self.letter_grade = 3.75, 'A'
        elif total >= 70: self.grade_point, self.letter_grade = 3.50, 'A-'
        elif total >= 65: self.grade_point, self.letter_grade = 3.25, 'B+'
        elif total >= 60: self.grade_point, self.letter_grade = 3.00, 'B'
        elif total >= 55: self.grade_point, self.letter_grade = 2.75, 'B-'
        elif total >= 50: self.grade_point, self.letter_grade = 2.50, 'C+'
        elif total >= 45: self.grade_point, self.letter_grade = 2.25, 'C'
        elif total >= 40: self.grade_point, self.letter_grade = 2.00, 'D'
        else: self.grade_point, self.letter_grade = 0.00, 'F'
        super().save(*args, **kwargs)
        self.student.calculate_cgpa()

# -----------------------
# Project & Thesis
# -----------------------
class ProjectThesis(models.Model):
    STATUS_CHOICES = (
        ('proposal', 'Proposal Stage'),
        ('ongoing', 'Ongoing'),
        ('submitted', 'Submitted'),
        ('defended', 'Defended'),
    )
    title = models.CharField(max_length=255)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="projects")
    supervisor = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name="supervised_projects")
    description = models.TextField()
    github_link = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='proposal')
    defense_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title

# -----------------------
# Resource & Inventory
# -----------------------
class LabAssistant(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lab_assistant_profile")
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"LA {self.user.username}"

class LabItem(models.Model):
    STATUS_CHOICES = (
        ('Functional', 'Functional'),
        ('Repair', 'Repair'),
        ('Damaged', 'Damaged'),
    )
    item_name = models.CharField(max_length=200)
    serial_number = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100) # PC, Router, IoT Kit, etc.
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Functional')
    last_checked = models.DateTimeField(auto_now=True)
    last_checked_by = models.ForeignKey(LabAssistant, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.item_name} ({self.serial_number})"

class LabSchedule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.IntegerField(default=1)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    time_slot = models.CharField(max_length=100) # e.g. "10:00 AM - 12:00 PM"
    is_occupied = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.course.code} Lab - {self.time_slot}"

class LabReport(models.Model):
    item = models.ForeignKey(LabItem, on_delete=models.CASCADE, related_name="maintenance_logs")
    reported_by = models.ForeignKey(LabAssistant, on_delete=models.CASCADE)
    problem_description = models.TextField()
    report_date = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    resolution_details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Report: {self.item.item_name} on {self.report_date.date()}"

class ResourceRequisition(models.Model):
    item = models.ForeignKey(LabItem, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    request_date = models.DateTimeField(auto_now_add=True)
    return_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('pending','Pending'), ('approved','Approved'), ('returned','Returned')], default='pending')

# -----------------------
# Communication & Career
# -----------------------
class Notice(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_global = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Post(models.Model):
    CATEGORY_CHOICES = (
        ('notice', 'Notice'),
        ('assignment', 'Assignment'),
        ('exam', 'Exam Info'),
        ('message', 'Message'),
        ('other', 'Other'),
    )

    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='notice')
    created_at = models.DateTimeField(auto_now_add=True)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.title} ({self.category})"

class AlumniJobBoard(models.Model):

    job_title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    description = models.TextField()
    apply_link = models.URLField()
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    posted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.job_title} at {self.company}"

class Resource(models.Model):
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="resources/")
    description = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Assignment(models.Model):

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    file = models.FileField(upload_to="assignments/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()

    def __str__(self):
        return self.title
# -----------------------
# System Governance & Logging
# -----------------------
class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.action} @ {self.timestamp}"

class AccessLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    username_attempted = models.CharField(max_length=150, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    status = models.CharField(max_length=20, default='success') # success, failed
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ip_address} -> {self.status} @ {self.timestamp}"

# -----------------------
# CMS & Portal Management
# -----------------------
class HomeBanner(models.Model):
    image = models.ImageField(upload_to='banners/')
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class GlobalNotice(models.Model):
    CATEGORY_CHOICES = (
        ('ACADEMIC', 'Academic'),
        ('EXAMINATION', 'Examination'),
        ('REGISTRATION', 'Registration'),
        ('MAINTENANCE', 'Maintenance'),
        ('EVENT', 'Event'),
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='ACADEMIC')
    title = models.CharField(max_length=255)
    content = models.TextField()
    file_attachment = models.FileField(upload_to='notices/files/', blank=True, null=True)
    is_latest = models.BooleanField(default=True, help_text="Show in the 'Latest' ticker")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.category}] {self.title}"
