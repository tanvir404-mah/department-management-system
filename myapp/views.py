from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


from django.conf import settings
from .models import CustomUser, Student  

from .models import Attendance, Student, Teacher, Notice, Result


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Student


User = get_user_model()





# ================= General Pages =================
def home(request):
    return render(request, 'home.html')

def profile(request):
    return render(request, 'profile.html')

def result(request):
    return render(request, 'result.html')

def routine(request):
    return render(request, 'routine.html')

def teacher_view(request):
    return render(request, 'teacher.html')

def student_view(request):
    return render(request, 'student.html')

def search_student(request):   
    semester = request.GET.get('semester')
    shift = request.GET.get('shift')
    students = Student.objects.all()
    if semester:
        students = students.filter(semester=semester)
    if shift:
        students = students.filter(shift=shift)
    return render(request, 'student.html', {'students': students})

def notice(request):
    return render(request, 'notice.html')
def contact(request):
    return render(request, 'contact.html')

def lab_view(request):
    return render(request, 'lab.html')

def club(request):
    return render(request, 'club.html')

def developer(request):
    return render(request, 'developer.html')

def classroom(request):
    return render(request, 'classroom.html')

def curriculum(request):
    return render(request, 'curriculum.html')

def success(request):
    return render(request, 'success.html')

def internships(request):
    return render(request, 'internships.html')

def attendance_show(request):
    return render(request, 'attendance_show.html')


def attendance(request):
    return render(request, 'attendance.html')

def attendance_summary(request):
    return render(request, 'attendance_summary.html')
# ==================Student Dashboard===================
@login_required
def student_profile(request):
    if not hasattr(request.user, 'student'):
        messages.error(request, "Unauthorized access")
        return redirect('home')
    student = request.user.student
    return render(request, 'profile.html', {"student": student})


def assignments(request):
    if not hasattr(request.user, 'student'):
        messages.error(request, "Unauthorized access")
        return redirect('home')
    student = request.user.student
    return render(request, 'assignments.html', {"student": student})

def subjects(request):
    if not hasattr(request.user, 'student'):
        messages.error(request, "Unauthorized access")
        return redirect('home')
    student = request.user.student
    return render(request, 'subjects.html', {"student": student})


# ================= Authentication =================

def student_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")  # Login form এ password field এর নাম 'password'

        user = authenticate(request, username=username, password=password)
        if user and hasattr(user, 'student'):
            login(request, user)
            messages.success(request, "Student login successful")
            return redirect('student_dashboard')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'registration/student_login.html')


def teacher_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            if hasattr(user, 'teacher'):
                login(request, user)
                messages.success(request, "Teacher login successful")
                return redirect('teacher_dashboard')
            else:
                messages.error(request, "This account is not a teacher account")
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'registration/teacher_login.html')

def principal_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user and user.role == "principal":
            login(request, user)
            messages.success(request, "Principal login successful")
            return redirect('custom_admin_dashboard')
        else:
            messages.error(request, "Invalid principal credentials")
    return render(request, 'registration/principal_login.html')

def logout_view(request):
    logout(request)
    return redirect('home')


# ================= Registration =================


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Student
from django.contrib.auth import get_user_model

User = get_user_model()

def student_register(request):
    if request.method == "POST":
        name = request.POST.get("name")
        roll = request.POST.get("roll_number")  # template অনুযায়ী
        semester = request.POST.get("semester")
        shift = request.POST.get("shift")
        username = request.POST.get("username")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect('student_register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect('student_register')

        if Student.objects.filter(roll_number=roll).exists():
            messages.error(request, "Roll number already exists")
            return redirect('student_register')

        # Create user
        user = User.objects.create_user(
            username=username,
            password=password1,
            first_name=name,
            role='student'  # যদি CustomUser এ role থাকে
        )

        # Create student profile
        Student.objects.create(user=user, roll_number=roll, semester=semester, shift=shift)

        messages.success(request, "✅ Student registered successfully! Please login.")
        return redirect('student_login')

    return render(request, 'registration/student_register.html')


#================= Teacher Registration =================

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Teacher

User = get_user_model()  # custom user

def teacher_register(request):
    if request.method == "POST":
        name = request.POST.get("name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect('teacher_register')

        if not username or not password1:
            messages.error(request, "Username and password are required")
            return redirect('teacher_register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect('teacher_register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect('teacher_register')

        user = User.objects.create_user(
            username=username,
            password=password1,
            email=email,
            first_name=name,
            role='teacher'  # যদি custom field থাকে
        )
        Teacher.objects.create(user=user)
        messages.success(request, "Teacher registered successfully! Please login.")
        return redirect('teacher_login')

    return render(request, 'registration/teacher_register.html')



# ================= Dashboards =================
@login_required
def student_dashboard(request):
    return render(request, 'student/student_dashboard.html')

@login_required
def teacher_dashboard(request):
    return render(request, 'teacher/teacher_dashboard.html')

@login_required
def principal_dashboard(request):
    return render(request, 'principal/principal_dashboard.html')

@login_required
def custom_admin_dashboard(request):
    if not request.user.is_superuser and request.user.role != 'principal':
        messages.error(request, "Unauthorized access")
        return redirect('home')

    students = Student.objects.all()
    teachers = Teacher.objects.all()

    return render(request, 'custom_admin_dashboard.html', {
        "students": students,
        "teachers": teachers
    })


# ================= AJAX Handlers =================

# -------- Students --------
@csrf_exempt
def add_student_ajax(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        roll_number = request.POST.get("roll_number")
        if not (first_name and last_name and roll_number):
            return JsonResponse({"message":"All fields required"}, status=400)
        user = User.objects.create_user(username=first_name+roll_number, first_name=first_name, last_name=last_name, password="1234", role='student')
        Student.objects.create(user=user, roll_number=roll_number, semester="1", shift="Morning")
        return JsonResponse({"message":"Student added successfully"})

def get_students_ajax(request):
    students = Student.objects.all()
    data = [{"first_name":s.user.first_name, "last_name":s.user.last_name, "roll_number":s.roll_number} for s in students]
    return JsonResponse(data, safe=False)

# -------- Teachers --------
@csrf_exempt
def add_teacher_ajax(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        department = request.POST.get("department")
        if not (first_name and last_name and department):
            return JsonResponse({"message":"All fields required"}, status=400)
        user = User.objects.create_user(username=first_name+last_name, first_name=first_name, last_name=last_name, password="1234", role='teacher')
        Teacher.objects.create(user=user, department=department)
        return JsonResponse({"message":"Teacher added successfully"})

def get_teachers_ajax(request):
    teachers = Teacher.objects.all()
    data = [{"first_name":t.user.first_name, "last_name":t.user.last_name, "department":t.department} for t in teachers]
    return JsonResponse(data, safe=False)


# ================= Attendance Updates =================

# Teacher marks attendance
@login_required
@csrf_exempt
def add_attendance_ajax(request):
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({"message":"Unauthorized"}, status=403)

    if request.method == "POST":
        student_name = request.POST.get("student")
        subject = request.POST.get("subject")
        date = request.POST.get("date")
        status = request.POST.get("status")
        try:
            student = Student.objects.get(user__first_name=student_name)
            Attendance.objects.create(student=student, subject=subject, date=date, status=status, teacher_name=request.user.first_name)
            return JsonResponse({"message":"Attendance added successfully"})
        except Student.DoesNotExist:
            return JsonResponse({"message":"Student not found"}, status=400)

# Attendance view for student or principal
@login_required
def view_attendance(request, student_id=None):
    if hasattr(request.user, 'student'):
        student = request.user.student
        attendances = Attendance.objects.filter(student=student)
    elif request.user.role == 'principal':
        if student_id:
            student = Student.objects.get(id=student_id)
            attendances = Attendance.objects.filter(student=student)
        else:
            students = Student.objects.all()
            summary = []
            for s in students:
                total = Attendance.objects.filter(student=s).count()
                present = Attendance.objects.filter(student=s, status='Present').count()
                percent = round((present/total*100),2) if total>0 else 0
                summary.append({'student': s, 'percentage': percent})
            return render(request, 'attendance_summary.html', {'summary': summary})
    else:
        messages.error(request, "Unauthorized access")
        return redirect('home')

    total = attendances.count()
    present = attendances.filter(status='Present').count()
    percentage = round((present/total*100),2) if total>0 else 0

    return render(request, 'attendance_show.html', {
        'attendances': attendances,
        'percentage': percentage
    })


def get_attendance_ajax(request):
    records = Attendance.objects.all()
    data = [{"student":a.student.user.first_name, "subject":a.subject, "date":str(a.date), "status":a.status, "teacher":a.teacher_name} for a in records]
    return JsonResponse(data, safe=False)


# -------- Notices --------
@csrf_exempt
def add_notice_ajax(request):
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        Notice.objects.create(title=title, content=content, created_by=request.user)
        return JsonResponse({"message":"Notice added successfully"})



def get_student_notices(request):
    notices = [
        {"id": 1, "text": "Exam on Monday", "by": "Admin"},
        {"id": 2, "text": "Submit assignment", "by": "Teacher"},
    ]
    return JsonResponse(notices, safe=False)

def publish_notice(request):
    if request.method == "POST":
        data = json.loads(request.body)
        text = data.get("text")
        # এখানে তুমি DB-এ save করতে পারো, এখন শুধু demo
        new_notice = {"id": 123, "text": text, "by": "Teacher"}
        return JsonResponse(new_notice)
    return JsonResponse({"error": "Invalid request"}, status=400)

def get_notices_ajax(request):
    notices = Notice.objects.all().order_by('-created_at')  # নতুন notice প্রথমে
    data = [{"title": n.title, "content": n.content, "by": n.created_by.first_name} for n in notices]
    return JsonResponse(data, safe=False)

def get_teacher_notices_ajax(request):
    notices = Notice.objects.filter(created_by__role='teacher')
    data = [{"text": n.content, "by": n.created_by.first_name} for n in notices]
    return JsonResponse(data, safe=False)


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Assignment
from django.contrib.auth.decorators import login_required

@login_required
def create_assignment(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        due_date = request.POST.get("due_date")

        Assignment.objects.create(
            teacher=request.user,
            title=title,
            description=description,
            due_date=due_date
        )
        messages.success(request, "Assignment created successfully!")
        return redirect('teacher_dashboard')  # Teacher dashboard page

    return render(request, 'create_assignment.html')




from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Post

@login_required
def publish_post(request):
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        category = request.POST.get("category")

        Post.objects.create(
            title=title,
            content=content,
            category=category,
            sender=request.user
        )
        # Teacher হলে নিজের dashboard এ redirect হবে
        if request.user.role == "teacher":
            return redirect("teacher_dashboard")
        # Principal হলে principal dashboard এ redirect হবে
        elif request.user.role == "principal":
            return redirect("principal_dashboard")
    return render(request, "publish_post.html")



@login_required
def student_dashboard(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, "student/student_dashboard.html", {"posts": posts})

# -------- Results --------
@csrf_exempt
def add_result_ajax(request):
    if request.method == "POST":
        student_name = request.POST.get("student")
        subject = request.POST.get("subject")
        marks = request.POST.get("marks")
        total_marks = request.POST.get("total_marks")
        try:
            student = Student.objects.get(user__first_name=student_name)
            Result.objects.create(student=student, subject=subject, marks=marks, total_marks=total_marks)
            return JsonResponse({"message":"Result added successfully"})
        except Student.DoesNotExist:
            return JsonResponse({"message":"Student not found"}, status=400)

def get_results_ajax(request):
    results = Result.objects.all()
    data = [{"student":r.student.user.first_name, "subject":r.subject, "marks":r.marks, "total":r.total_marks} for r in results]
    return JsonResponse(data, safe=False)
    def __str__(self):
        return f"{self.student.user.first_name} - {self.subject} - {self.marks}/{self.total_marks}"