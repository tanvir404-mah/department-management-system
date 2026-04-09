import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import csv, io
from django.db.models import Count, Q, F, Sum, Avg
from django.contrib.sessions.models import Session

from django.conf import settings
from .models import (
    CustomUser, Student, Teacher, Department, Course, 
    Attendance, Result, Assignment, Notice, Resource, 
    Post, ProjectThesis, LabAssistant, LabItem, 
    LabSchedule, LabReport, ResourceRequisition, 
    AlumniJobBoard, ClassRoutine, AuditLog, AccessLog,
    HomeBanner, GlobalNotice, HOD
)
from .forms import (
    StudentRegistrationForm, TeacherRegistrationForm, StudentForm, 
    TeacherForm, DepartmentForm, NoticeForm, ResourceForm, 
    CourseForm, ProjectThesisForm, LabItemForm, AlumniJobBoardForm,
    AssignmentForm, OTPStep1Form, OTPStep2Form, OTPStep3Form,
    HomeBannerForm, GlobalNoticeForm
)
from .utils import send_otp_sms, send_broadcast_sms
import random


User = get_user_model()





# ================= General Pages =================
def home(request):
    banners = HomeBanner.objects.filter(is_active=True).order_by('-created_at')
    latest_ticker = GlobalNotice.objects.filter(is_latest=True).order_by('-created_at').first()
    return render(request, 'home.html', {
        'banners': banners,
        'latest_ticker': latest_ticker
    })


@login_required
def profile(request):
    user = request.user
    student = getattr(user, 'student_profile', None)
    teacher = getattr(user, 'teacher_profile', None)
    lab_assistant = getattr(user, 'lab_assistant_profile', None)
    
    if request.method == "POST":
        # Common User Fields
        user.phone = request.POST.get("phone")
        user.address = request.POST.get("address")
        user.email = request.POST.get("email")
        
        if "profile_picture" in request.FILES:
            user.profile_picture = request.FILES["profile_picture"]
        user.save()
        
        # Role-specific fields
        if student:
            student.guardian_name = request.POST.get("guardian_name")
            student.guardian_phone = request.POST.get("guardian_phone")
            student.save()
        elif teacher:
            teacher.designation = request.POST.get("designation")
            teacher.bio = request.POST.get("bio")
            teacher.save()
        elif lab_assistant:
            lab_assistant.bio = request.POST.get("bio")
            lab_assistant.save()
            
        messages.success(request, "Profile updated successfully")
        return redirect("profile")

    return render(request, "profile.html", {
        "student": student, 
        "teacher": teacher, 
        "lab_assistant": lab_assistant,
        "user": user
    })

# ================= Authentication =================

def student_login(request):
    if request.method == "POST":
        username_input = request.POST.get("username")
        password = request.POST.get("password")
        
        student = Student.objects.filter(roll_no=username_input).first()
        if student:
            user = authenticate(request, username=student.user.username, password=password)
            if user and user.role == 'student':
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                return redirect('student_dashboard')
        
        messages.error(request, "Invalid roll number or password. Please try again.")
    return render(request, 'registration/student_login.html')

def unified_staff_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        
        if user:
            if user.is_superuser:
                login(request, user)
                messages.success(request, f"System access granted. Welcome, Admin {user.username}.")
                return redirect('staff_dashboard')
            
            role = getattr(user, 'role', None)
            if role in ['teacher', 'lab_assistant', 'hod','admin']:
                login(request, user)
                messages.success(request, f"Authentication successful. Welcome Back, {user.get_full_name() or user.username}!")
                
                if role == 'teacher': return redirect('teacher_dashboard')
                if role == 'lab_assistant': return redirect('lab_assistant_dashboard')
                if role == 'hod': return redirect('hod_dashboard')
                if role == 'admin': return redirect('staff_dashboard')
            
        messages.error(request, "Invalid departmental credentials. Please ensure you are using your Staff Username.")
    return render(request, 'registration/staff_login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

# Fallback views for old URLs (redirect to unified)
def teacher_login(request): return redirect('unified_staff_login')
def hod_login(request): return redirect('unified_staff_login')
def principal_login(request): return redirect('unified_staff_login')
def lab_assistant_login(request): return redirect('unified_staff_login')


# ================= Lab Assistant Views =================

@login_required
def lab_assistant_dashboard(request):
    la_profile = getattr(request.user, 'lab_assistant_profile', None)
    
    # Allow all staff roles (Teacher, LA, HOD, Admin) to see the dashboard
    if request.user.role not in ['lab_assistant', 'teacher', 'hod', 'admin'] and not request.user.is_superuser:
        messages.error(request, "Access denied. Professional credentials required.")
        return redirect('home')

    items = LabItem.objects.all()
    schedules = LabSchedule.objects.all()
    maintenance_reports = LabReport.objects.filter(is_resolved=False).order_by('-report_date')
    
    stats = {
        'total_items': items.count(),
        'repair_count': items.filter(status='Repair').count(),
        'damaged_count': items.filter(status='Damaged').count(),
        'functional_count': items.filter(status='Functional').count()
    }

    return render(request, 'lab_assistant/dashboard.html', {
        "la_profile": la_profile,
        "items": items,
        "schedules": schedules,
        "maintenance_reports": maintenance_reports,
        "stats": stats
    })

@login_required
@require_POST
def lab_update_item_status(request):
    if request.user.role != 'lab_assistant':
        return JsonResponse({'status': 'error'}, status=403)
    
    item_id = request.POST.get('item_id')
    new_status = request.POST.get('status')
    item = get_object_or_404(LabItem, id=item_id)
    item.status = new_status
    item.save()
    return JsonResponse({'status': 'success', 'new_status': item.status})

@login_required
@require_POST
def lab_toggle_status(request, schedule_id):
    if request.user.role != 'lab_assistant':
        return JsonResponse({'status': 'error'}, status=403)
    
    schedule = get_object_or_404(LabSchedule, id=schedule_id)
    schedule.is_occupied = not schedule.is_occupied
    schedule.save()
    return JsonResponse({'status': 'success', 'is_occupied': schedule.is_occupied})

@login_required
def lab_report_issue(request):
    if request.method == "POST":
        item_id = request.POST.get('item_id')
        description = request.POST.get('description')
        la_profile = request.user.lab_assistant_profile
        
        item = get_object_or_404(LabItem, id=item_id)
        LabReport.objects.create(
            item=item,
            reported_by=la_profile,
            problem_description=description
        )
        item.status = 'Repair'
        item.save()
        messages.success(request, f"Maintenance report filed for {item.item_name}")
        return redirect('lab_assistant_dashboard')

@login_required
def lab_mark_ca(request, course_id):
    la_profile = getattr(request.user, 'lab_assistant_profile', None)
    if not la_profile:
        return redirect('home')
        
    course = get_object_or_404(Course, id=course_id)
    students = Student.objects.filter(courses=course)

    if request.method == "POST":
        for student in students:
            ca_marks = request.POST.get(f'ca_{student.id}')
            if ca_marks:
                Result.objects.update_or_create(
                    student=student, course=course,
                    defaults={'ca_marks': float(ca_marks), 'semester': student.semester}
                )
        messages.success(request, f"CA Marks updated for {course.title}")
        return redirect('lab_assistant_dashboard')

    return render(request, 'lab_assistant/mark_ca.html', {
        "course": course,
        "students": students
    })


def result_view(request):
    results_by_semester = {}
    cgpa = 0.0
    total_credits_earned = 0
    student = getattr(request.user, 'student_profile', None)

    if request.user.is_authenticated and student:
        all_results = student.results.select_related('course').all().order_by('-semester', 'course__title')
        
        # Grouping and Calculations
        semesters = all_results.values_list('semester', flat=True).distinct().order_by('-semester')
        
        total_grade_points = 0
        total_credits = 0

        for sem in semesters:
            sem_results = all_results.filter(semester=sem)
            sem_total_gp = 0
            sem_total_credits = 0
            
            for res in sem_results:
                gp = float(res.grade_point or 0)
                credits = float(res.course.credits or 0)
                sem_total_gp += gp * credits
                sem_total_credits += credits
                
                # Global calculation
                total_grade_points += gp * credits
                total_credits += credits
            
            sem_gpa = round(sem_total_gp / sem_total_credits, 2) if sem_total_credits > 0 else 0.00
            results_by_semester[sem] = {
                'results': sem_results,
                'gpa': sem_gpa,
                'credits': sem_total_credits
            }
        
        cgpa = round(total_grade_points / total_credits, 2) if total_credits > 0 else 0.00
        total_credits_earned = total_credits

    context = {
        "student": student,
        "results_by_semester": results_by_semester,
        "cgpa": cgpa,
        "total_credits_earned": total_credits_earned,
    }
    return render(request, 'result.html', context)

@login_required
def routine(request):
    """
    Comprehensive dynamic routine view for Students and Teachers.
    Organizes ClassRoutine objects by day and time for the logged-in user.
    """
    user = request.user
    role = getattr(user, 'role', None)
    
    routine_data = {}
    days = ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    student = None
    teacher = None
    
    if role == 'student':
        student = getattr(user, 'student_profile', None)
        if student:
            routines = ClassRoutine.objects.filter(
                semester=student.semester,
                shift=student.shift
            ).select_related('course', 'teacher__user').order_by('day_of_week', 'start_time')
            
            # Reorganization for UI
            for day in days:
                routine_data[day] = routines.filter(day_of_week=day)
                
    elif role == 'teacher':
        teacher = getattr(user, 'teacher_profile', None)
        if teacher:
            routines = ClassRoutine.objects.filter(
                teacher=teacher
            ).select_related('course').order_by('day_of_week', 'start_time')
            
            for day in days:
                routine_data[day] = routines.filter(day_of_week=day)
    
    context = {
        'routine_data': routine_data,
        'days': days,
        'is_empty': not any(routine_data.values()),
        'student': student if role == 'student' else None,
        'teacher': teacher if role == 'teacher' else None,
    }
    
    return render(request, 'routine.html', context)

def teacher_view(request):
    teachers = Teacher.objects.all()
    return render(request, 'teacher.html', {"teachers": teachers})

def student_view(request):
    students = Student.objects.all()
    return render(request, 'student.html', {"students": students})

def search_student(request):
    """
    Flexible internal student search for directory.
    Uses OR logic for identification fields (Roll, ID, Reg).
    """
    q = request.GET.get('q', '').strip()
    semester = request.GET.get('semester', '').strip()
    shift = request.GET.get('shift', '').strip()
    roll = request.GET.get('roll', '').strip()
    session = request.GET.get('session', '').strip()

    students = Student.objects.all().select_related('user', 'department')
    
    # 1. Identity Search (Muti-field Roll/ID/Reg lookup)
    if roll:
        students = students.filter(
            Q(roll_no__icontains=roll) | 
            Q(student_id__icontains=roll) | 
            Q(reg_no__icontains=roll)
        )
    
    # 2. Name Search
    if q:
        students = students.filter(
            Q(user__first_name__icontains=q) | 
            Q(user__last_name__icontains=q) |
            Q(user__username__icontains=q)
        )

    # 3. Academic Filters (Only apply if explicitly selected)
    if semester and semester != "":
        try:
            students = students.filter(current_semester=int(semester))
        except (ValueError, TypeError):
            pass
            
    if shift and shift != "":
        # Flexible shift matching (1st, 2nd, Morning, Day)
        if "1st" in shift or "Morning" in shift:
            students = students.filter(Q(shift='1st') | Q(shift__icontains='Morning'))
        elif "2nd" in shift or "Day" in shift:
            students = students.filter(Q(shift='2nd') | Q(shift__icontains='Day'))
        else:
            students = students.filter(shift__icontains=shift)

    if session:
        students = students.filter(session__icontains=session)

    return render(request, 'student.html', {'students': students, 'searched': True})

def notice(request):
    """Notice Board: Displays both departmental and global system notices.
    Filtered: Public board only shows Admin and HOD notices.
    """
    global_notices = GlobalNotice.objects.all().order_by('-created_at')
    # Filter by search if provided
    query = request.GET.get('q')
    if query:
        global_notices = global_notices.filter(Q(title__icontains=query) | Q(content__icontains=query))
    
    # Standard departmental notices - ONLY Admin and HOD for public view
    internal_notices = Notice.objects.filter(created_by__role__in=['admin', 'hod']).order_by('-created_at')
    if query:
        internal_notices = internal_notices.filter(Q(title__icontains=query) | Q(content__icontains=query))

    # We merge them in the view (this is easier for the template)
    all_notices = list(global_notices) + list(internal_notices)
    all_notices.sort(key=lambda x: x.created_at, reverse=True)

    return render(request, 'notice.html', {
        "notices": all_notices,
        "query": query or ""
    })

def contact(request):
    return render(request, 'contact.html')

def lab_view(request):
    inventory = LabItem.objects.all()
    return render(request, 'lab.html', {"inventory": inventory})

def club(request):
    return render(request, 'club.html')

def developer(request):
    return render(request, 'developer.html')

# Documentation of Unified Redirect Manager
# Students -> Roll Number + Password -> student_dashboard
# Staff (Teacher, LA, HOD, Admin) -> Username + Password -> unified_staff_login -> role redirection

# ================= 3-Step Registration =================

def student_registration_step1(request):
    """
    Step 1: Input Roll & Phone, Send OTP.
    """
    if request.method == "POST":
        form = OTPStep1Form(request.POST)
        if form.is_valid():
            roll = form.cleaned_data['roll_number']
            phone = form.cleaned_data['phone_number']
            
            otp = str(random.randint(100000, 999999))
            request.session['reg_roll'] = roll
            request.session['reg_phone'] = phone
            request.session['reg_otp'] = otp
            request.session['otp_verified'] = False
            
            if send_otp_sms(phone, otp):
                messages.success(request, f"Verification code sent to {phone}")
                return redirect('student_registration_step2')
            else:
                messages.error(request, "Failed to send SMS. Try again.")
    else:
        form = OTPStep1Form()
    return render(request, 'registration/student_register.html', {'form': form})

def student_registration_step2(request):
    """
    Step 2: Verify the 6-digit OTP.
    """
    reg_otp = request.session.get('reg_otp')
    if not reg_otp:
        return redirect('student_registration_step1')
        
    if request.method == "POST":
        form = OTPStep2Form(request.POST)
        if form.is_valid():
            if form.cleaned_data['otp_code'] == reg_otp:
                request.session['otp_verified'] = True
                return redirect('student_registration_step3')
            else:
                messages.error(request, "Invalid OTP code!")
    else:
        form = OTPStep2Form()
    return render(request, 'registration/register_step2.html', {'form': form})

def student_registration_step3(request):
    """
    Step 3: Set Password and Create account.
    """
    if not request.session.get('otp_verified'):
        return redirect('student_registration_step1')
        
    roll = request.session.get('reg_roll')
    phone = request.session.get('reg_phone')

    if request.method == "POST":
        form = OTPStep3Form(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            confirm = form.cleaned_data['confirm_password']
            
            if password != confirm:
                messages.error(request, "Passwords do not match!")
            else:
                username = f"std_{roll}"
                if User.objects.filter(username=username).exists():
                    messages.error(request, "Already registered with this roll.")
                else:
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        role='student',
                        phone=phone
                    )
                    Student.objects.create(user=user, roll_no=roll)
                    login(request, user)
                    
                    # Cleanup
                    for key in ['reg_otp', 'reg_roll', 'reg_phone', 'otp_verified']:
                        request.session.pop(key, None)
                        
                    messages.success(request, "Account created successfully!")
                    return redirect('student_dashboard')
    else:
        form = OTPStep3Form()
    return render(request, 'registration/register_step3.html', {'form': form})

def student_register(request):
    # This view is now redirected to student_registration_step1 in urls.py
    return redirect('student_registration_step1')

# def teacher_register(request):
#     if request.method == "POST":
#         username = request.POST.get("username")
#         password = request.POST.get("password1")
#         user = User.objects.create_user(username=username, password=password, role='teacher')
#         Teacher.objects.create(user=user)
#         return redirect('teacher_login')
#     return render(request, 'registration/teacher_register.html')

# ================= Dashboards =================
@login_required
def student_dashboard(request):
    """
    7-Section Professional Student Dashboard: Fetch all necessary data.
    """
    student = getattr(request.user, 'student_profile', None)
    if not student or request.user.role != 'student':
        messages.error(request, "Access denied. Student profile not found.")
        return redirect('home')

    # Section 5: Departmental Notice Board (Filtered by relevant roles)
    notice_roles = ['teacher', 'hod', 'lab_assistant', 'admin']
    all_notices = Notice.objects.filter(
        Q(created_by__role__in=notice_roles) | Q(is_global=True)
    ).distinct().order_by('-created_at')
    
    new_notices_count = all_notices.filter(created_at__gte=timezone.now() - timezone.timedelta(days=2)).count()
    recent_notices = all_notices[:5]

    # Section 4: Current Courses & Routine
    enrolled_courses = student.courses.all()
    today_name = timezone.now().strftime('%A')
    today_routine = ClassRoutine.objects.filter(
        day_of_week=today_name,
        semester=student.semester,
        shift=student.shift
    ).order_by('start_time')

    # Section 3: Quick Stats
    total_credits = sum(course.credits for course in enrolled_courses)
    
    # Calculate Attendance Percentage
    attendances = student.attendances.all()
    total_attendance = attendances.count()
    present_count = attendances.filter(status='Present').count()
    attendance_percentage = int((present_count / total_attendance * 100)) if total_attendance > 0 else 0

    # Section 6: Results Shortcut
    latest_result = student.results.all().order_by('-created_at').first()
    results_summary = student.results.all().order_by('-created_at')[:10]

    # Section 7: Specialized CST (Project List)
    my_projects = student.projects.all().order_by('-id')[:3]
    all_teachers = Teacher.objects.all()

    context = {
        "student": student,
        "recent_notices": recent_notices,
        "new_notices_count": new_notices_count,
        "enrolled_courses": enrolled_courses,
        "today_routine": today_routine,
        "today_name": today_name,
        "total_credits": total_credits,
        "attendance_percentage": attendance_percentage,
        "latest_result": latest_result,
        "results_summary": results_summary,
        "my_projects": my_projects,
        "cgpa": student.cgpa,
        "all_teachers": all_teachers,
    }
    return render(request, 'student/student_dashboard.html', context)

@login_required
def submit_project(request):
    """
    Section 7: Submit GitHub link for Lab Assignments/Projects.
    """
    if request.method == "POST":
        title = request.POST.get("title")
        github_link = request.POST.get("github_link")
        description = request.POST.get("description", "")
        supervisor_id = request.POST.get("supervisor_id")
        
        student = request.user.student_profile
        supervisor = get_object_or_404(Teacher, id=supervisor_id) if supervisor_id else None
        
        ProjectThesis.objects.create(
            student=student,
            title=title,
            github_link=github_link,
            description=description,
            supervisor=supervisor,
            status='ongoing'
        )
        messages.success(request, "Project link submitted successfully!")
    return redirect('student_dashboard')

@login_required
def request_resource(request):
    """
    Section 7: Request Lab PC/Inventory requisition.
    """
    if request.method == "POST":
        item_id = request.POST.get("item_id")
        item = LabItem.objects.get(id=item_id)
        
        ResourceRequisition.objects.create(
            item=item,
            requested_by=request.user,
            status='pending'
        )
        messages.success(request, f"Requisition for {item.item_name} sent successfully!")
    return redirect('student_dashboard')

@login_required
def teacher_dashboard(request):
    """
    Teacher & Lab Assistant Dashboard: Fetch relevant metrics.
    """
    teacher = getattr(request.user, 'teacher_profile', None)
    lab_assistant = getattr(request.user, 'lab_assistant_profile', None)
    
    if not (teacher or lab_assistant) and request.user.role not in ['teacher', 'lab_assistant']:
        messages.error(request, "Access denied. Professional profile not found.")
        return redirect('home')

    # Section 3: Quick Stats
    assigned_courses = teacher.courses.all() if teacher else []
    assigned_courses_count = assigned_courses.count() if teacher else 0
    
    # Total students enrolled in all teacher's courses
    total_students = Student.objects.filter(courses__in=assigned_courses).distinct().count() if teacher else 0
    
    # Today's Classes (Section 4) - Showing routines for all allotted courses
    today_name = timezone.now().strftime('%A')
    today_schedule = ClassRoutine.objects.filter(
        Q(teacher=teacher) | Q(course__in=assigned_courses),
        day_of_week=today_name
    ).distinct().order_by('start_time') if teacher else []
    today_classes_count = today_schedule.count() if teacher else 0

    # Pending Reviews (Section 7)
    pending_reviews_count = teacher.supervised_projects.filter(status='ongoing').count() if teacher else 0
    recent_reviews = teacher.supervised_projects.all().order_by('-id')[:5] if teacher else []

    # Notices (From HOD, Admin)
    notice_roles = ['hod', 'admin']
    all_notices = Notice.objects.filter(
        Q(created_by__role__in=notice_roles) | Q(is_global=True)
    ).distinct().order_by('-created_at')
    
    new_notices_count = all_notices.filter(created_at__gte=timezone.now() - timezone.timedelta(days=2)).count()
    recent_notices = all_notices[:5]

    context = {
        "teacher": teacher,
        "lab_assistant": lab_assistant,
        "assigned_courses": assigned_courses,
        "assigned_courses_count": assigned_courses_count,
        "total_students": total_students,
        "today_schedule": today_schedule,
        "today_classes_count": today_classes_count,
        "pending_reviews_count": pending_reviews_count,
        "recent_reviews": recent_reviews,
        "today_name": today_name,
        "recent_notices": recent_notices,
        "new_notices_count": new_notices_count,
    }
    return render(request, 'teacher/teacher_dashboard.html', context)

@login_required
def teacher_mark_attendance(request, course_id):
    """
    Batch Attendance Entry for a specific course.
    """
    teacher = getattr(request.user, 'teacher_profile', None)
    if not teacher:
        messages.error(request, "Authorized teacher profile not found. Please contact Admin.")
        return redirect('home')

    course = get_object_or_404(Course, id=course_id)
    students = course.students.all()
    
    # Fallback: If 0 students enrolled, show all students in the course's department
    if not students.exists():
        students = Student.objects.filter(department=course.department)

    if request.method == "POST":
        date_str = request.POST.get('date', timezone.now().date().isoformat())
        date = parse_date(date_str)
        
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'Absent')
            Attendance.objects.update_or_create(
                student=student, course=course, date=date,
                defaults={'status': status, 'teacher': teacher}
            )
        messages.success(request, f"Attendance marked for {course.code} on {date_str}")
        return redirect('teacher_dashboard')

    return render(request, 'teacher/mark_attendance.html', {
        "course": course, 
        "students": students, 
        "today": timezone.now().date().isoformat(),
        "teacher": teacher
    })

@login_required
def teacher_add_results(request, course_id):
    """
    Batch Mark Entry for a specific course.
    """
    teacher = getattr(request.user, 'teacher_profile', None)
    if not teacher:
        messages.error(request, "Authorized teacher profile not found. Please contact Admin.")
        return redirect('home')

    course = get_object_or_404(Course, id=course_id)
    students = course.students.all()

    # Fallback: If 0 students enrolled, show all students in the course's department
    if not students.exists():
        students = Student.objects.filter(department=course.department)

    if request.method == "POST":
        for student in students:
            marks = request.POST.get(f'marks_{student.id}')
            if marks:
                Result.objects.update_or_create(
                    student=student, course=course,
                    defaults={'marks': float(marks), 'semester': student.semester}
                )
        messages.success(request, f"Results updated for {course.code}")
        return redirect('teacher_dashboard')

    return render(request, 'teacher/add_results.html', {
        "course": course, "students": students, "teacher": teacher
    })

@login_required
def teacher_review_project(request, project_id):
    """
    View and Update Project/Thesis submission status.
    """
    teacher = getattr(request.user, 'teacher_profile', None)
    if not teacher:
        messages.error(request, "Authorized teacher profile not found. Please contact Admin.")
        return redirect('home')

    project = get_object_or_404(ProjectThesis, id=project_id)
    
    if request.method == "POST":
        project.status = request.POST.get('status')
        project.description += f"\n\nReview by {teacher.user.username}: " + request.POST.get('feedback', '')
        project.save()
        messages.success(request, f"Review for '{project.title}' submitted.")
        return redirect('teacher_dashboard')

    return render(request, 'teacher/review_project.html', {"project": project, "teacher": teacher})

@login_required
def teacher_publish_notice(request):
    """
    Post a new departmental or course notice.
    """
    if request.method == "POST":
        title = request.POST.get('title')
        content = request.POST.get('content')
        is_global = request.POST.get('is_global') == 'on'
        
        Notice.objects.create(
            title=title, content=content, is_global=is_global, created_by=request.user
        )
        messages.success(request, "Notice published successfully!")
        return redirect('teacher_dashboard')

    teacher = getattr(request.user, 'teacher_profile', None)
    return render(request, 'teacher/publish_notice.html', {"teacher": teacher})

@login_required
def staff_dashboard(request):
    """
    Global Admin Command Center: Total system oversight.
    """
    if not request.user.is_superuser and request.user.role != 'admin':
        messages.error(request, "Superuser access required.")
        return redirect('home')

    # ─── 1. System Overview Stats ───────────────────────────────────────
    total_users     = CustomUser.objects.count()
    total_students  = Student.objects.count()
    total_teachers  = Teacher.objects.count()
    user_stats      = CustomUser.objects.values('role').annotate(count=Count('id'))
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now()).count()

    # ─── 2. Maintenance & Lab Inventory ─────────────────────────────────
    pending_reports    = LabReport.objects.filter(is_resolved=False).count()
    damaged_items      = LabItem.objects.filter(status='Damaged').select_related('last_checked_by')
    repair_items       = LabItem.objects.filter(status='Repair').count()
    damaged_items_count = damaged_items.count()
    low_stock_warning  = (damaged_items_count + repair_items) > 5
 
    # ─── 3. CMS & Portal Content ────────────────────────────────────────
    cms_banners = HomeBanner.objects.all().order_by('-created_at')
    cms_notices = GlobalNotice.objects.all().order_by('-created_at')
    
    # ─── 4. Department-wise Growth (Chart) ──────────────────────────────
    dept_distribution = list(Department.objects.annotate(
        student_count=Count('student'),
        teacher_count=Count('teacher')
    ).values('name', 'student_count', 'teacher_count'))

    # ─── 4. Recent Notices ───────────────────────────────────────────────
    recent_notices = Notice.objects.order_by('-created_at')[:5]

    # ─── 5. Security & Audit ────────────────────────────────────────────
    security_alerts = AccessLog.objects.filter(status='failed').order_by('-timestamp')[:8]
    audit_logs      = AuditLog.objects.order_by('-timestamp')[:8]

    # Handle global notice broadcast from admin
    if request.method == "POST" and request.POST.get('action') == 'broadcast':
        title   = request.POST.get('title')
        content = request.POST.get('content')
        Notice.objects.create(title=title, content=content, is_global=True, created_by=request.user)
        AuditLog.objects.create(user=request.user, action=f"Broadcast notice: {title}",
                                ip_address=request.META.get('REMOTE_ADDR'))
        messages.success(request, "Global notice broadcasted successfully.")
        return redirect('staff_dashboard')

    context = {
        "total_users":          total_users,
        "total_students":       total_students,
        "total_teachers":       total_teachers,
        "user_stats":           user_stats,
        "active_sessions":      active_sessions,
        "pending_reports":      pending_reports,
        "damaged_items":        damaged_items[:10],
        "damaged_items_count":  damaged_items_count,
        "repair_items":         repair_items,
        "low_stock_warning":    low_stock_warning,
        "dept_distribution":    dept_distribution,
        "recent_notices":       recent_notices,
        "security_alerts":      security_alerts,
        "audit_logs":           audit_logs,
        "cms_banners":          cms_banners,
        "cms_notices":          cms_notices,
    }
    return render(request, 'admin/dashboard.html', context)

@login_required
def hod_dashboard(request):
    """
    HOD Dashboard: Scoped to the individual department.
    """
    if request.user.role != 'hod' and not request.user.is_staff:
        return redirect('home')

    # Department Scoping — safely get HOD profile
    hod_profile = getattr(request.user, 'hod_profile', None)
    dept = hod_profile.department if hod_profile else None

    # Master view logic for Admins and superusers if they don't have a specific dept profile
    is_admin = request.user.is_superuser or request.user.role == 'admin' or request.user.is_staff

    if dept:
        students = Student.objects.filter(department=dept)
        teachers = Teacher.objects.filter(department=dept)
        courses = Course.objects.filter(department=dept)
        dept_name_display = dept.name
    elif is_admin:
        students = Student.objects.all()
        teachers = Teacher.objects.all()
        courses = Course.objects.all()
        dept_name_display = "Global (All Depts)"
    else:
        messages.warning(request, "Your account is not linked to any department yet.")
        students = Student.objects.none()
        teachers = Teacher.objects.none()
        courses = Course.objects.none()
        dept_name_display = "N/A"

    # Faculty workload for the dashboard table
    faculty_workload = teachers.prefetch_related('courses')

    # Notices for notification dropdown
    recent_notices = Notice.objects.all().order_by('-created_at')[:5]
    new_notices_count = Notice.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=2)).count()

    # Pending resource requisitions (status is lowercase 'pending' in model)
    if dept:
        pending_req_count = ResourceRequisition.objects.filter(
            requested_by__student_profile__department=dept,
            status='pending'
        ).count()
    elif is_admin:
        pending_req_count = ResourceRequisition.objects.filter(status='pending').count()
    else:
        pending_req_count = 0

    context = {
        "dept_name": dept_name_display,
        "total_students": students.count(),
        "total_faculty": teachers.count(),
        "total_courses": courses.count(),
        "pending_requisitions": pending_req_count,
        "faculty_workload": faculty_workload,
        "recent_notices": recent_notices,
        "new_notices_count": new_notices_count,
        "cms_banners": HomeBanner.objects.all().order_by('-created_at')[:3],
        "cms_notices": GlobalNotice.objects.all().order_by('-created_at')[:3],
    }
    return render(request, 'hod/hod_dashboard.html', context)

@login_required
def hod_faculty_mgmt(request):
    """
    Departmental Faculty Management.
    """
    if request.user.role != 'hod' and not request.user.is_staff:
        return redirect('home')
    hod_profile = getattr(request.user, 'hod_profile', None)
    hod_dept = hod_profile.department if hod_profile else None
    
    # Check for admin role as well
    is_admin = request.user.is_superuser or request.user.role == 'admin' or request.user.is_staff
    
    if hod_dept:
        faculty = Teacher.objects.filter(department=hod_dept)
    elif is_admin:
        faculty = Teacher.objects.all()
    else:
        faculty = Teacher.objects.none()
    
    return render(request, 'hod/faculty_mgmt.html', {"faculty": faculty})

@login_required
def hod_student_mgmt(request):
    """Management of students within the HOD's department."""
    if not _admin_guard(request): return redirect('home')

    hod_profile = getattr(request.user, 'hod_profile', None)
    dept = hod_profile.department if hod_profile else None

    # If it's a superuser/admin without HOD profile, show all students
    # Use role and is_staff/is_superuser for global admin access
    is_admin = request.user.is_superuser or request.user.role == 'admin' or request.user.is_staff
    
    if is_admin and not dept:
        students = Student.objects.all()
        dept_name = "System Global (Master view)"
    elif not dept:
        messages.error(request, "Your HOD account is not linked to any department.")
        return redirect('home')
    else:
        students = Student.objects.filter(department=dept)
        dept_name = dept.name

    return render(request, 'hod/student_mgmt.html', {
        'students': students, 
        'dept_name': dept_name
    })

@login_required
def hod_course_allotment(request):
    if request.user.role != 'hod' and not request.user.is_staff:
        return redirect('home')
    
    teachers = Teacher.objects.all()
    courses = Course.objects.all()

    if request.method == "POST":
        teacher_id = request.POST.get('teacher_id')
        course_ids = request.POST.getlist('course_ids')
        
        teacher = get_object_or_404(Teacher, id=teacher_id)
        teacher.courses.set(course_ids)
        messages.success(request, f"Course allotment updated for {teacher.user.username}")
        return redirect('hod_dashboard')

    return render(request, 'hod/course_allotment.html', {
        "teachers": teachers,
        "courses": courses
    })

@login_required
def hod_lab_mgmt(request):
    """
    Departmental Lab Control.
    """
    if request.user.role != 'hod' and not request.user.is_staff:
        return redirect('home')
    hod_profile = getattr(request.user, 'hod_profile', None)
    hod_dept = hod_profile.department if hod_profile else None
    inventory = LabItem.objects.all()
    requisitions = ResourceRequisition.objects.filter(requested_by__student_profile__department=hod_dept).order_by('-id') if hod_dept else ResourceRequisition.objects.none()
    return render(request, 'hod/lab_mgmt.html', {
        "inventory": inventory,
        "requisitions": requisitions
    })

@login_required
def hod_broadcast_notice(request):
    if request.method == "POST" and (request.user.role == 'hod' or request.user.is_staff):
        title = request.POST.get('title')
        content = request.POST.get('content')
        Notice.objects.create(
            title=title, 
            content=content, 
            is_global=True, 
            created_by=request.user
        )
        messages.success(request, "Global notice broadcasted to all users.")
    return redirect('hod_dashboard')

@login_required
def hod_dept_mgmt(request):
    if request.user.role != 'hod' and not request.user.is_superuser:
        return redirect('home')
    depts = Department.objects.all()
    if request.method == "POST":
        name = request.POST.get('name')
        code = request.POST.get('code')
        Department.objects.create(name=name, code=code)
        messages.success(request, f"Department '{name}' created.")
        return redirect('hod_dept_mgmt')
    return render(request, 'hod/dept_mgmt.html', {"departments": depts})

@login_required
def hod_course_mgmt(request):
    if request.user.role != 'hod' and not request.user.is_superuser:
        return redirect('home')
    courses = Course.objects.all()
    depts = Department.objects.all()
    if request.method == "POST":
        title = request.POST.get('title')
        code = request.POST.get('code')
        credits = request.POST.get('credits')
        dept_id = request.POST.get('department')
        dept = get_object_or_404(Department, id=dept_id)
        Course.objects.create(title=title, code=code, credits=credits, department=dept)
        messages.success(request, f"Course '{title}' added.")
        return redirect('hod_course_mgmt')
    return render(request, 'hod/course_mgmt.html', {"courses": courses, "departments": depts})

import traceback
MISSING_LIB = None

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    MISSING_LIB = "google-generativeai"

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    if not MISSING_LIB: MISSING_LIB = "Pillow"

# Final AI Status check
AI_READY = HAS_GENAI and HAS_PIL

# ──────── AI Configuration ──────────────────────────────────────────
GEMINI_API_KEY = "AIzaSyCBYF7km4jixjR4cxam66w3FpbH-JGD52o"

def mock_extract_routine_from_image():
    """
    Simulated data based on Faridpur Polytechnic Institute CST 6th Sem, 2nd Shift.
    Data extracted manually from the user's provided PNG.
    """
    return [
        {
            "course_code": "28563",
            "teacher_initials": "TH",
            "day": "Sunday",
            "start_time": "14:15",
            "end_time": "15:00",
            "room_no": "Com-101",
            "semester": 6,
            "shift": "2nd"
        },
        {
            "course_code": "28564",
            "teacher_initials": "TH",
            "day": "Sunday",
            "start_time": "15:00",
            "end_time": "16:30",
            "room_no": "NL",
            "semester": 6,
            "shift": "2nd"
        },
        {
            "course_code": "28565",
            "teacher_initials": "AR",
            "day": "Sunday",
            "start_time": "16:30",
            "end_time": "17:15",
            "room_no": "Com-301",
            "semester": 6,
            "shift": "2nd"
        },
        {
            "course_code": "28561",
            "teacher_initials": "SI",
            "day": "Sunday",
            "start_time": "17:15",
            "end_time": "18:45",
            "room_no": "SL-3",
            "semester": 6,
            "shift": "2nd"
        },
        {
            "course_code": "28564",
            "teacher_initials": "TH",
            "day": "Monday",
            "start_time": "13:30",
            "end_time": "14:15",
            "room_no": "Com-301",
            "semester": 6,
            "shift": "2nd"
        }
    ]

@login_required
def upload_routine_image(request):
    """
    Experimental: Image-to-Routine AI Processing Hub for HOD.
    """
    if request.user.role != 'hod' and not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Permission denied for AI routine processing.")
        return redirect('home')

    if request.method == "POST" and request.FILES.get('routine_image'):
        try:
            force_mock = request.POST.get('force_mock') == 'on'
            
            if not AI_READY or force_mock:
                # Use Mock data if library is missing or forced
                mode_str = "Forced Mock" if force_mock else "Missing Library Mock"
                messages.warning(request, f"Using {mode_str} data for demonstration.")
                routine_json = mock_extract_routine_from_image()
            else:
                genai.configure(api_key=GEMINI_API_KEY)
                image_file = request.FILES['routine_image']
                img = Image.open(image_file)
                
                # Production Fallback with LITE models (Higher Quota Availability)
                models_to_try = [
                    'gemini-2.0-flash-lite', 
                    'gemini-flash-lite-latest',
                    'gemini-pro-latest',
                    'gemini-flash-latest'
                ]
                
                response = None
                diag_errors = []
                
                for model_name in models_to_try:
                    try:
                        # Attempting exact model identifier
                        model = genai.GenerativeModel(model_name)
                        prompt = "Extract class timetable from image. Format as a strict JSON array with course_code, teacher_initials, day, start_time, end_time, room_no, semester, shift. Return raw JSON only."
                        
                        response = model.generate_content([prompt, img])
                        if response: break
                    except Exception as inner_e:
                        err_msg = str(inner_e)
                        diag_errors.append(f"{model_name}: {err_msg[:100]}...")
                        # If Rate Limit, wait a tiny bit and try next model
                        import time
                        time.sleep(1)
                        continue
                
                # Check which models are REALLY available for this key
                try:
                    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    model_list_str = ", ".join(available_models)
                except Exception as list_e:
                    model_list_str = f"Could not list models: {str(list_e)}"

                # Final failure with DISCOVERED models info
                detailed_err = " | ".join(diag_errors)
                raise Exception(f"API 404 Conflict. Available Models found: [{model_list_str}]. Trials Errors: {detailed_err}")
                
                # Check for empty response (Unreachable if all trial models failed)
                if not response.text:
                    raise Exception("AI returned empty content. Try a clearer image.")
                
                raw_text = response.text.replace('```json', '').replace('```', '').strip()
                routine_json = json.loads(raw_text)
            
            count = 0
            for item in routine_json:
                course = Course.objects.filter(code=item.get('course_code')).first()
                teacher = Teacher.objects.filter(user__username=item.get('teacher_initials')).first()
                if course:
                    ClassRoutine.objects.create(
                        course=course, teacher=teacher,
                        day_of_week=item.get('day'),
                        start_time=item.get('start_time'),
                        end_time=item.get('end_time'),
                        room_number=item.get('room_no'),
                        semester=item.get('semester', 1),
                        shift=item.get('shift', '1st')
                    )
                    count += 1
            
            messages.success(request, f"Extracted {count} slots successfully.")
            return redirect('hod_routine_mgmt')
            
        except Exception as e:
            traceback.print_exc()
            messages.error(request, f"AI Processing Error: {str(e)}")
            return redirect('hod_routine_mgmt')

    return render(request, 'hod/upload_routine.html', {
        'ai_ready': AI_READY, 
        'missing_lib': MISSING_LIB
    })

@login_required
def hod_routine_mgmt(request):
    if request.user.role != 'hod' and not request.user.is_superuser and not request.user.is_staff:
        return redirect('home')
    
    # Department Scoping
    hod_profile = getattr(request.user, 'hod_profile', None)
    dept = hod_profile.department if hod_profile else None
    is_admin = request.user.is_superuser or request.user.role == 'admin' or request.user.is_staff
    
    if dept:
        routines = ClassRoutine.objects.filter(course__department=dept).select_related('course', 'teacher__user')
        courses = Course.objects.filter(department=dept)
        teachers = Teacher.objects.filter(department=dept)
    elif is_admin:
        routines = ClassRoutine.objects.all().select_related('course', 'teacher__user')
        courses = Course.objects.all()
        teachers = Teacher.objects.all()
    else:
        routines = ClassRoutine.objects.none()
        courses = Course.objects.none()
        teachers = Teacher.objects.none()
    
    if request.method == "POST":
        # Bulk Upload Logic (Custom Format: Day, Time_Slot, Time, Code, Teacher_Short, Location)
        if request.FILES.get('csv_file'):
            try:
                csv_file = request.FILES['csv_file']
                content = csv_file.read().decode('utf-8', errors='ignore')
                io_string = io.StringIO(content)
                reader = csv.reader(io_string)
                
                # Check for header
                header = next(reader)
                if 'day' not in header[0].lower() and 'time' not in header[0].lower():
                    io_string.seek(0)
                
                count = 0
                for row in reader:
                    if len(row) < 6: continue
                    # Format: Day, Slot, Time, Code, Teacher, Room
                    day_ref, slot, time_range, c_code, t_ref, room = [x.strip() for x in row[:6]]
                    
                    # Manual Time Splitter (e.g. "1:30-2:15" -> ["13:30", "14:15"])
                    try:
                        times = time_range.replace(" ", "").split("-")
                        if len(times) == 2:
                            # Heuristic: 1:30 in polytechnic often means PM (13:30)
                            def convert_to_24h(t):
                                hr, mn = [int(p) for p in t.split(":")]
                                if hr < 7: hr += 12 # 1:30 -> 13:30, 2:15 -> 14:15
                                return f"{hr:02d}:{mn:02d}"
                            start = convert_to_24h(times[0])
                            end = convert_to_24h(times[1])
                        else:
                            start, end = "13:30", "14:15" # Fallback
                    except:
                        start, end = "13:30", "14:15"

                    course = Course.objects.filter(code=c_code).first()
                    teacher = Teacher.objects.filter(initials=t_ref).first() or \
                             Teacher.objects.filter(user__username=t_ref).first()
                    
                    if course:
                        ClassRoutine.objects.create(
                            course=course, teacher=teacher, day_of_week=day_ref,
                            start_time=start, end_time=end, room_number=room,
                            semester=6, # Default to 6 for the uploaded image
                            shift='2nd'  # Default to 2nd shift
                        )
                        count += 1
                messages.success(request, f"Bulk Sync: {count} slots added to 6th Sem, 2nd Shift.")
            except Exception as e:
                messages.error(request, f"Sync Crash: {str(e)}")
            return redirect('hod_routine_mgmt')

        # Individual Slot Logic
        try:
            course_id = request.POST.get('course')
            teacher_id = request.POST.get('teacher')
            ClassRoutine.objects.create(
                course_id=course_id, 
                teacher_id=teacher_id if teacher_id else None,
                day_of_week=request.POST.get('day_of_week'),
                start_time=request.POST.get('start_time'),
                end_time=request.POST.get('end_time'),
                room_number=request.POST.get('room_number'),
                semester=request.POST.get('semester'),
                shift=request.POST.get('shift')
            )
            messages.success(request, "New class slot scheduled successfully.")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
        return redirect('hod_routine_mgmt')
        
    return render(request, 'hod/routine_mgmt.html', {
        "routines": routines, "courses": courses, "teachers": teachers
    })

@login_required
def delete_routine(request, routine_id):
    if request.user.role != 'hod' and not request.user.is_superuser and not request.user.is_staff:
        return redirect('home')
    routine = get_object_or_404(ClassRoutine, id=routine_id)
    routine.delete()
    messages.success(request, "Schedule slot purged from the system.")
    return redirect('hod_routine_mgmt')

@login_required
def admin_user_mgmt(request):
    if not request.user.is_superuser and request.user.role != 'admin':
        return redirect('home')
    users = CustomUser.objects.all().order_by('-id')
    if request.method == "POST":
        user_id = request.POST.get('user_id')
        new_role = request.POST.get('role')
        target_user = get_object_or_404(CustomUser, id=user_id)
        target_user.role = new_role
        target_user.save()
        AuditLog.objects.create(user=request.user, action=f"Promoted {target_user.username} to {new_role}")
        messages.success(request, f"User {target_user.username} role updated.")
    return render(request, 'admin/user_roles.html', {"users": users})

@login_required
def admin_bulk_import(request):
    if not request.user.is_superuser and request.user.role != 'admin':
        return redirect('home')

    if request.method == "POST" and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        decoded_file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        next(io_string)
        
        count = 0
        for row in csv.reader(io_string):
            # Format: username, password, name, roll_no, reg_no, session, current_semester, shift, dept_code
            if len(row) < 9: continue
            # Handle extra columns by slicing only the first 9, and strip whitespace
            row_data = [field.strip() for field in row[:9]]
            username, password, name, roll_no, reg_no, session, current_semester, shift, dept_code = row_data
            
            dept = Department.objects.filter(code=dept_code).first()
            if dept:
                try:
                    current_sem_int = int(current_semester) if current_semester else 1
                except (ValueError, TypeError):
                    current_sem_int = 1 # Default to 1st if invalid
                
                user = CustomUser.objects.create_user(username=username, password=password, role='student')
                Student.objects.create(
                    user=user, name=name, roll_no=roll_no, reg_no=reg_no, 
                    session=session, current_semester=current_sem_int, 
                    shift=shift, department=dept
                )
                count += 1
        
        AuditLog.objects.create(user=request.user, action=f"Bulk imported {count} students")
        messages.success(request, f"Imported {count} students.")
        return redirect('staff_dashboard')

    return render(request, 'admin/bulk_actions.html')

@login_required
def admin_semester_transition(request):
    if not request.user.is_superuser and request.user.role != 'admin':
        return redirect('home')

    if request.method == "POST":
        Student.objects.filter(current_semester__lt=8).update(current_semester=F('current_semester') + 1)
        AuditLog.objects.create(user=request.user, action="Global Semester Transition")
        messages.success(request, "Global semester promotion complete.")
    return redirect('staff_dashboard')

@login_required
def admin_security_logs(request):
    if not request.user.is_superuser and request.user.role != 'admin':
        return redirect('home')
    audit_logs = AuditLog.objects.all().order_by('-timestamp')[:50]
    access_failed = AccessLog.objects.filter(status='failed').order_by('-timestamp')[:50]
    return render(request, 'admin/security_logs.html', {
        "audit_logs": audit_logs,
        "access_failed": access_failed
    })

@login_required
def admin_reset_password(request):
    if not request.user.is_superuser and request.user.role != 'admin':
        return redirect('home')

    if request.method == "POST":
        user_id = request.POST.get('user_id')
        new_pass = request.POST.get('new_password')
        target_user = get_object_or_404(CustomUser, id=user_id)
        target_user.set_password(new_pass)
        target_user.save()
        AuditLog.objects.create(user=request.user, action=f"Force reset password for {target_user.username}")
        messages.success(request, f"Password reset for {target_user.username}.")
    return redirect('admin_user_mgmt')

@login_required
def hod_parents_alert(request):
    """
    Broadcast system for student guardians. 
    Allows HOD/Admin to send custom SMS to all parents in their department.
    """
    if not _admin_guard(request): 
        return redirect('home')

    hod_profile = getattr(request.user, 'hod_profile', None)
    dept = hod_profile.department if hod_profile else None
    
    # Query all unique parent phones in the department
    if request.user.is_superuser and not dept:
        students = Student.objects.all()
    elif dept:
        students = Student.objects.filter(department=dept)
    else:
        messages.error(request, "Your account is not linked to any department.")
        return redirect('hod_dashboard')

    # Collect all unique mobile numbers from both parents
    father_phones = students.filter(father_mobile__isnull=False).values_list('father_mobile', flat=True).distinct()
    mother_phones = students.filter(mother_mobile__isnull=False).values_list('mother_mobile', flat=True).distinct()
    
    recipient_list = list(set([str(p).strip() for p in list(father_phones) + list(mother_phones) if p]))

    if request.method == "POST":
        message = request.POST.get("custom_message")
        if message and recipient_list:
            success = send_broadcast_sms(recipient_list, message)
            if success:
                messages.success(request, f"Alert broadcast successfully to {len(recipient_list)} guardians.")
            else:
                messages.error(request, "Failed to connect to the SMS gateway. Please try again.")
            return redirect('hod_dashboard')
        else:
            messages.warning(request, "Message cannot be empty or no recipients found.")

    return render(request, 'hod/parents_alert.html', {
        'recipient_count': len(recipient_list),
        'dept_name': dept.name if dept else "Global"
    })


# ════════════════════════════════════════════════════════════
#  SYSTEM ADMINISTRATION — Full CRUD (replaces Django admin)
# ════════════════════════════════════════════════════════════

def _admin_guard(request):
    """Shared guard for all admin system views."""
    return request.user.is_superuser or request.user.role in ['admin', 'hod']

@login_required
def admin_system_mgmt(request):
    """Central system management hub — overview of all models."""
    if not _admin_guard(request):
        return redirect('home')
    context = {
        "total_users":       CustomUser.objects.count(),
        "total_students":    Student.objects.count(),
        "total_teachers":    Teacher.objects.count(),
        "total_departments": Department.objects.count(),
        "total_courses":     Course.objects.count(),
        "total_notices":     Notice.objects.count(),
        "departments":       Department.objects.all(),
        "courses":           Course.objects.select_related('department').all()[:20],
        "users":             CustomUser.objects.all().order_by('-date_joined')[:30],
    }
    return render(request, 'admin/system_mgmt.html', context)

# ── Users ───────────────────────────────────────────────────
@login_required
def admin_create_user(request):
    if not _admin_guard(request):
        return redirect('home')
    departments = Department.objects.all()
    if request.method == "POST":
        username   = request.POST.get('username')
        email      = request.POST.get('email', '')
        first_name = request.POST.get('first_name', '')
        last_name  = request.POST.get('last_name', '')
        password   = request.POST.get('password')
        role       = request.POST.get('role', 'student')
        is_super   = request.POST.get('is_superuser') == 'on'
        is_staff   = request.POST.get('is_staff') == 'on'

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' already exists.")
            return redirect('admin_create_user')

        user = CustomUser.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name,
            role=role, is_superuser=is_super, is_staff=is_staff or is_super
        )
        # Auto-create profile based on role
        dept_id = request.POST.get('department')
        dept = Department.objects.filter(id=dept_id).first() if dept_id else None
        if role == 'student' and dept:
            Student.objects.create(user=user, department=dept,
                                   shift=request.POST.get('shift', '1st'))
        elif role == 'teacher' and dept:
            Teacher.objects.create(user=user, department=dept,
                                   designation=request.POST.get('designation', 'Lecturer'))
        elif role == 'lab_assistant' and dept:
            LabAssistant.objects.create(user=user, department=dept)
        elif role == 'hod' and dept:
            HOD.objects.create(user=user, department=dept)

        AuditLog.objects.create(user=request.user,
                                action=f"Created user {username} (role={role})",
                                ip_address=request.META.get('REMOTE_ADDR'))
        messages.success(request, f"User '{username}' created successfully.")
        return redirect('admin_system_mgmt')
    return render(request, 'admin/create_user.html', {'departments': departments})

@login_required
def admin_edit_user(request, user_id):
    if not _admin_guard(request):
        return redirect('home')
    target = get_object_or_404(CustomUser, id=user_id)
    departments = Department.objects.all()
    if request.method == "POST":
        target.first_name  = request.POST.get('first_name', target.first_name)
        target.last_name   = request.POST.get('last_name', target.last_name)
        target.email       = request.POST.get('email', target.email)
        target.role        = request.POST.get('role', target.role)
        target.is_staff    = request.POST.get('is_staff') == 'on'
        target.is_superuser = request.POST.get('is_superuser') == 'on'
        target.is_active   = request.POST.get('is_active') == 'on'
        new_pass = request.POST.get('new_password')
        if new_pass:
            target.set_password(new_pass)
        # Update/Create Profile based on role and department
        dept_id = request.POST.get('department')
        dept = Department.objects.filter(id=dept_id).first() if dept_id else None
        
        if dept:
            if target.role == 'student':
                Student.objects.update_or_create(user=target, defaults={'department': dept})
            elif target.role == 'teacher':
                Teacher.objects.update_or_create(user=target, defaults={'department': dept})
            elif target.role == 'hod':
                HOD.objects.update_or_create(user=target, defaults={'department': dept})
            elif target.role == 'lab_assistant':
                LabAssistant.objects.update_or_create(user=target, defaults={'department': dept})

        AuditLog.objects.create(user=request.user,
                                action=f"Edited user {target.username} (role={target.role})",
                                ip_address=request.META.get('REMOTE_ADDR'))
        messages.success(request, f"User '{target.username}' updated (Profile sync active).")
        return redirect('admin_system_mgmt')
    return render(request, 'admin/edit_user.html', {'target': target, 'departments': departments})

@login_required
def admin_delete_user(request, user_id):
    if not _admin_guard(request):
        return redirect('home')
    target = get_object_or_404(CustomUser, id=user_id)
    if request.method == "POST":
        username = target.username
        target.delete()
        AuditLog.objects.create(user=request.user, action=f"Deleted user {username}",
                                ip_address=request.META.get('REMOTE_ADDR'))
        messages.success(request, f"User '{username}' deleted.")
    return redirect('admin_system_mgmt')

# ── CMS CRUD Views ──────────────────────────────────────────

@login_required
def admin_manage_banners(request):
    if not _admin_guard(request): return redirect('home')
    banners = HomeBanner.objects.all().order_by('-created_at')
    if request.method == "POST":
        form = HomeBannerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Home banner added successfully!")
            return redirect('admin_manage_banners')
        else:
            messages.error(request, "Invalid form submission. Check image format or title.")
    return render(request, 'admin/cms/manage_banners.html', {'banners': banners})

@login_required
def admin_delete_banner(request, banner_id):
    if not _admin_guard(request): return redirect('home')
    banner = get_object_or_404(HomeBanner, id=banner_id)
    banner.delete()
    messages.success(request, "Banner removed.")
    return redirect('staff_dashboard')

@login_required
def admin_manage_notices(request):
    if not _admin_guard(request): return redirect('home')
    notices = GlobalNotice.objects.all().order_by('-created_at')
    if request.method == "POST":
        form = GlobalNoticeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Global notice published!")
            return redirect('admin_manage_notices')
        else:
            messages.error(request, "Invalid notice submission. Please fill all required fields.")
    return render(request, 'admin/cms/manage_notices.html', {'notices': notices})

@login_required
def admin_delete_global_notice(request, notice_id):
    if not _admin_guard(request): return redirect('home')
    notice = get_object_or_404(GlobalNotice, id=notice_id)
    notice.delete()
    messages.success(request, "Global notice deleted.")
    return redirect('staff_dashboard')

@login_required
def admin_toggle_superuser(request, user_id):
    if not _admin_guard(request):
        return redirect('home')
    target = get_object_or_404(CustomUser, id=user_id)
    if request.method == "POST":
        target.is_superuser = not target.is_superuser
        target.is_staff = target.is_superuser or target.is_staff
        target.save()
        status = "granted" if target.is_superuser else "revoked"
        AuditLog.objects.create(user=request.user,
                                action=f"Superuser {status} for {target.username}",
                                ip_address=request.META.get('REMOTE_ADDR'))
        messages.success(request, f"Superuser access {status} for '{target.username}'.")
    return redirect('admin_system_mgmt')

# ── Departments ─────────────────────────────────────────────
@login_required
def admin_create_dept(request):
    if not _admin_guard(request):
        return redirect('home')
    if request.method == "POST":
        name = request.POST.get('name')
        code = request.POST.get('code')
        if Department.objects.filter(code=code).exists():
            messages.error(request, f"Department code '{code}' already exists.")
        else:
            Department.objects.create(name=name, code=code)
            AuditLog.objects.create(user=request.user, action=f"Created department {name}",
                                    ip_address=request.META.get('REMOTE_ADDR'))
            messages.success(request, f"Department '{name}' created.")
    return redirect('admin_system_mgmt')

@login_required
def admin_edit_dept(request, dept_id):
    if not _admin_guard(request):
        return redirect('home')
    dept = get_object_or_404(Department, id=dept_id)
    if request.method == "POST":
        dept.name = request.POST.get('name', dept.name)
        dept.code = request.POST.get('code', dept.code)
        dept.save()
        AuditLog.objects.create(user=request.user, action=f"Edited department {dept.name}",
                                ip_address=request.META.get('REMOTE_ADDR'))
        messages.success(request, f"Department '{dept.name}' updated.")
    return redirect('admin_system_mgmt')

@login_required
def admin_delete_dept(request, dept_id):
    if not _admin_guard(request):
        return redirect('home')
    dept = get_object_or_404(Department, id=dept_id)
    if request.method == "POST":
        name = dept.name
        dept.delete()
        AuditLog.objects.create(user=request.user, action=f"Deleted department {name}",
                                ip_address=request.META.get('REMOTE_ADDR'))
        messages.success(request, f"Department '{name}' deleted.")
    return redirect('admin_system_mgmt')

# ── Courses ──────────────────────────────────────────────────
@login_required
def admin_create_course(request):
    if not _admin_guard(request):
        return redirect('home')
    if request.method == "POST":
        title   = request.POST.get('title')
        code    = request.POST.get('code')
        credits = request.POST.get('credits', 3)
        dept_id = request.POST.get('department')
        dept    = get_object_or_404(Department, id=dept_id)
        if Course.objects.filter(code=code).exists():
            messages.error(request, f"Course code '{code}' already exists.")
        else:
            Course.objects.create(title=title, code=code, credits=credits, department=dept)
            AuditLog.objects.create(user=request.user, action=f"Created course {code}",
                                    ip_address=request.META.get('REMOTE_ADDR'))
            messages.success(request, f"Course '{code}: {title}' created.")
    return redirect('admin_system_mgmt')

@login_required
def admin_edit_course(request, course_id):
    if not _admin_guard(request):
        return redirect('home')
    course = get_object_or_404(Course, id=course_id)
    if request.method == "POST":
        course.title   = request.POST.get('title', course.title)
        course.code    = request.POST.get('code', course.code)
        course.credits = request.POST.get('credits', course.credits)
        dept_id = request.POST.get('department')
        if dept_id:
            course.department = get_object_or_404(Department, id=dept_id)
        course.save()
        AuditLog.objects.create(user=request.user, action=f"Edited course {course.code}",
                                ip_address=request.META.get('REMOTE_ADDR'))
        messages.success(request, f"Course '{course.code}' updated.")
    return redirect('admin_system_mgmt')

@login_required
def admin_delete_course(request, course_id):
    if not _admin_guard(request):
        return redirect('home')
    course = get_object_or_404(Course, id=course_id)
    if request.method == "POST":
        code = course.code
        course.delete()
        AuditLog.objects.create(user=request.user, action=f"Deleted course {code}",
                                ip_address=request.META.get('REMOTE_ADDR'))
        messages.success(request, f"Course '{code}' deleted.")
    return redirect('admin_system_mgmt')

# ── Notices ──────────────────────────────────────────────────
@login_required
def admin_notices(request):
    if not _admin_guard(request):
        return redirect('home')
    notices = Notice.objects.all().order_by('-created_at')
    return render(request, 'admin/notices.html', {'notices': notices})

@login_required
def admin_delete_notice(request, notice_id):
    if not _admin_guard(request):
        return redirect('home')
    notice = get_object_or_404(Notice, id=notice_id)
    if request.method == "POST":
        title = notice.title
        notice.delete()
        messages.success(request, f"Notice '{title}' deleted.")
    return redirect('admin_notices')

@login_required
def hod_security_logs(request):
    if request.user.role != 'hod' and not request.user.is_superuser:
        return redirect('home')
    
    audit_logs = AuditLog.objects.all().order_by('-timestamp')[:50]
    access_failed = AccessLog.objects.filter(status='failed').order_by('-timestamp')[:50]
    
    return render(request, 'hod/security_logs.html', {
        "audit_logs": audit_logs,
        "access_failed": access_failed
    })

@login_required
def principal_dashboard(request):
    return redirect('custom_admin_dashboard')

# ================= Academic & Resources =================
@login_required
def subjects(request):
    if hasattr(request.user, 'student_profile'):
        courses = request.user.student_profile.courses.all()
    elif hasattr(request.user, 'teacher_profile'):
        courses = request.user.teacher_profile.courses.all()
    else:
        courses = Course.objects.all()
    return render(request, 'student_subjects.html', {"courses": courses})

@login_required
def resources_view(request):
    data = Resource.objects.all()
    form = ResourceForm()
    if request.method == "POST":
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            res = form.save(commit=False)
            res.uploaded_by = request.user
            res.save()
            return redirect("resources")
    return render(request, "adminapp/resources.html", {"resources": data, "form": form})

# ================= AJAX Handlers =================
@csrf_exempt
@require_POST
def add_attendance_ajax(request):
    if request.user.role not in ["teacher", "hod", "admin"]:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    student_id = request.POST.get("student_id")
    course_code = request.POST.get("course_code")
    status = request.POST.get("status")
    date = parse_date(request.POST.get("date")) or timezone.now().date()
    try:
        student = Student.objects.get(id=student_id)
        course = Course.objects.get(code=course_code)
        Attendance.objects.update_or_create(
            student=student, course=course, date=date,
            defaults={'status': status, 'teacher': getattr(request.user, 'teacher_profile', None)}
        )
        return JsonResponse({"message": "Attendance marked"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@require_POST
def add_result_ajax(request):
    if request.user.role not in ["teacher", "hod", "admin"]:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        student = Student.objects.get(id=request.POST.get("student_id"))
        course = Course.objects.get(code=request.POST.get("course_code"))
        Result.objects.create(
            student=student, 
            course=course, 
            marks=float(request.POST.get("marks")),
            semester=student.semester
        )
        return JsonResponse({"message": "Result added"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def add_student_ajax(request):
    if request.method == "POST":
        user = User.objects.create_user(username=request.POST.get("username"), role='student')
        Student.objects.create(user=user, roll_no=request.POST.get("roll_number"))
        return JsonResponse({"message": "Student added"})
    return JsonResponse({"error": "Invalid request"}, status=400)

def get_students_ajax(request):
    data = [{"name": s.user.get_full_name() or s.user.username, "roll": s.roll_number} for s in Student.objects.all()]
    return JsonResponse(data, safe=False)

@csrf_exempt
def add_teacher_ajax(request):
    if request.method == "POST":
        user = User.objects.create_user(username=request.POST.get("username"), role='teacher')
        Teacher.objects.create(user=user, designation=request.POST.get("designation"))
        return JsonResponse({"message": "Teacher added"})
    return JsonResponse({"error": "Invalid request"}, status=400)

def get_teachers_ajax(request):
    data = [{"name": t.user.get_full_name() or t.user.username, "designation": t.designation} for t in Teacher.objects.all()]
    return JsonResponse(data, safe=False)

def get_attendance_ajax(request):
    data = [{"student": a.student.user.username, "course": a.course.code, "status": a.status, "date": a.date} for a in Attendance.objects.all()]
    return JsonResponse(data, safe=False)

@csrf_exempt
def add_notice_ajax(request):
    if request.method == "POST":
        Notice.objects.create(title=request.POST.get("title"), content=request.POST.get("content"), created_by=request.user)
        return JsonResponse({"message": "Notice added"})
    return JsonResponse({"error": "Invalid request"}, status=400)

def get_notices_ajax(request):
    # Public AJAX - only Admin and HOD notices
    notices = Notice.objects.filter(created_at__lte=timezone.now(), created_by__role__in=['admin', 'hod']).order_by('-created_at')
    data = [{"title": n.title, "content": n.content, "date": n.created_at} for n in notices]
    return JsonResponse(data, safe=False)

def publish_post(request):
    if request.method == "POST":
        Post.objects.create(title=request.POST.get("title"), content=request.POST.get("content"), sender=request.user)
        return redirect("student_dashboard")
    return render(request, "publish_post.html")

def get_results_ajax(request):
    data = [{"student": r.student.user.username, "course": r.course.code, "marks": r.marks} for r in Result.objects.all()]
    return JsonResponse(data, safe=False)

# Helpers & Auxiliary Views
def payment(request):
    return render(request, 'payment.html')

def club(request):
    return render(request, 'club.html')

def classroom(request):
    return render(request, 'classroom.html')

def curriculum(request):
    return render(request, 'curriculum.html')

def success(request):
    return render(request, 'success.html')

def internships(request):
    return render(request, 'internships.html')

def attendance(request):
    return render(request, 'attendance.html')

def attendance_show(request):
    return render(request, 'attendance_show.html')

def attendance_summary(request):
    return render(request, 'attendance_summary.html')

def assignments(request):
    return render(request, 'assignments.html')

def verification_view(request):
    return render(request, 'verification.html')

def get_student_notices(request):
    # Student dashboard AJAX - show all relevant notices (Teacher, HOD, Admin)
    notices = Notice.objects.all().order_by('-created_at')[:5]
    data = [{"title": n.title, "content": n.content} for n in notices]
    return JsonResponse(data, safe=False)

def get_teacher_notices_ajax(request):
    # Teacher AJAX - show official notices from Admin/HOD
    notices = Notice.objects.filter(created_by__role__in=['admin', 'hod']).order_by('-created_at')
    data = [{"title": n.title, "content": n.content} for n in notices]
    return JsonResponse(data, safe=False)

def publish_notice(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            Notice.objects.create(title=data.get("title", "Notice"), content=data.get("text", ""), created_by=request.user)
            return JsonResponse({"message": "Notice published"})
        except Exception:
            return JsonResponse({"error": "Invalid data"}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=400)

def send_meaasge(request):
    return JsonResponse({"message": "Feature coming soon"})

def edit_student(request, id=None):
    student = get_object_or_404(Student, id=id) if id else None
    return render(request, 'edit_student.html', {"student": student})

def teacher_edit(request, id=None):
    teacher = get_object_or_404(Teacher, id=id) if id else None
    return render(request, 'edit_teacher.html', {"teacher": teacher})

def student_delete(request, id=None):
    if not id: id = request.GET.get('id')
    if id and request.user.role in ['admin', 'hod', 'principal']:
        get_object_or_404(Student, id=id).delete()
    return redirect('hod_dashboard')

def teacher_delete(request, id=None):
    if not id: id = request.GET.get('id')
    if id and request.user.role in ['admin', 'hod', 'principal']:
        get_object_or_404(Teacher, id=id).delete()
    return redirect('hod_dashboard')

@login_required
def create_assignment(request):
    if request.method == "POST":
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            if hasattr(request.user, 'teacher_profile'):
                assignment.teacher = request.user.teacher_profile
                assignment.save()
                messages.success(request, "Assignment created")
                return redirect('teacher_dashboard')
    else:
        form = AssignmentForm()


def student_lookup(request):
    """
    Public Student Record Lookup for CST Department.
    Multi-parameter search: Roll, Semester, Session.
    """
    student = None
    search_performed = False
    error_message = None

    roll_number = request.GET.get('roll_number', '').strip()
    semester = request.GET.get('semester', '').strip()
    session = request.GET.get('session', '').strip()

    if roll_number and semester:
        search_performed = True
        try:
            # Fixing database field names (roll_no and current_semester)
            query = Q(roll_no__icontains=roll_number, current_semester=int(semester))
            if session:
                query &= Q(session__icontains=session)
            
            student = Student.objects.filter(query).first()
        except (ValueError, TypeError):
            student = None
            
        if not student:
            error_message = "No matching student found in the CST database."

    # Fetch dynamic options from the actual database to ensure perfect matching
    semesters_list = Student.objects.values_list('current_semester', flat=True).distinct().order_by('current_semester')
    sessions_list = Student.objects.values_list('session', flat=True).distinct().exclude(Q(session__isnull=True) | Q(session='')).order_by('-session')
    shifts_list = Student.objects.values_list('shift', flat=True).distinct().exclude(Q(shift__isnull=True) | Q(shift='')).order_by('shift')
    
    # Fallback to defaults if DB is empty to show at least something
    if not list(semesters_list): semesters_list = range(1, 9)
    if not list(sessions_list): sessions_list = ['2020-21', '2021-22', '2022-23', '2023-24', '2024-25']

    context = {
        'student': student,
        'search_performed': search_performed,
        'error_message': error_message,
        'semesters_list': semesters_list,
        'sessions_list': sessions_list,
        'shifts_list': shifts_list,
        'title': 'Student Record Lookup',
        'query_params': {
            'roll_number': roll_number,
            'semester': semester,
            'session': session
        }
    }
    return render(request, 'student_lookup.html', context)

