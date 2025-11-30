from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('profile/', views.profile, name='profile'),
    path('result/', views.result, name='result'),
    path('routine/', views.routine, name='routine'),
    path('teacher/', views.teacher_view, name='teacher'),
    path('student/', views.student_view, name='student'),
    path('student/search/', views.search_student, name='search_student'),
    path('notice/', views.notice, name='notice'),
    path('contact/', views.contact, name='contact'),
    path('lab/', views.lab_view, name='lab'),
    path('club/', views.club, name='club'),
    path('developer/', views.developer, name='developer'),
    path('attendance/', views.attendance_show, name='attendance_show'),
    path('classroom/', views.classroom, name='classroom'),
    path('curriculum/', views.curriculum, name='curriculum'),
    path('success/', views.success, name='success'),
    path('internships/', views.internships, name='internships'),
    path('assignments/', views.assignments, name='assignments'),
    path('create-assignment/', views.create_assignment, name='create_assignment'),
    path('subjects/', views.subjects, name='subjects'),
    
    path('attendance/mark/', views.attendance, name='attendance'),
    path('attendance/summary/', views.attendance_summary, name='attendance_summary'),
    
    # Authentication (Login/Logout)
    path('student/login/', views.student_login, name='student_login'),
    path('teacher/login/', views.teacher_login, name='teacher_login'),
    path('principal/login/', views.principal_login, name='principal_login'),

    path('logout/', views.logout_view, name='logout'),


    # Registration
    path('Student/register/', views.student_register, name='student_register'),
    path('teacher/register/', views.teacher_register, name='teacher_register'),

    # Dashboards
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('principal/dashboard/', views.principal_dashboard, name='principal_dashboard'),


    # Students
    path('add-student/', views.add_student_ajax, name='add_student_ajax'),
    path('get-students/', views.get_students_ajax, name='get_students_ajax'),

    # Teachers
    path('add-teacher/', views.add_teacher_ajax, name='add_teacher_ajax'),
    path('get-teachers/', views.get_teachers_ajax, name='get_teachers_ajax'),

    # Attendance
    path('add-attendance/', views.add_attendance_ajax, name='add_attendance_ajax'),
    path('get-attendance/', views.get_attendance_ajax, name='get_attendance_ajax'),

    # Notices
       
    path('teacher/notices/ajax', views.get_teacher_notices_ajax, name='get_teacher_notices_ajax'),
    path('notices/publish/', views.publish_notice, name='publish_notice'),
    path('student/notices/', views.get_student_notices, name='get_student_notices'),
    path('add-notice/', views.add_notice_ajax, name='add_notice_ajax'),
    path('get-notices/', views.get_notices_ajax, name='get_notices_ajax'),
    path("publish-post/", views.publish_post, name="publish_post"),
    # Results
    path('add-result/', views.add_result_ajax, name='add_result_ajax'),
    path('get-results/', views.get_results_ajax, name='get_results_ajax'),


    # Custom Admin Panel
    path('custom-admin/', views.custom_admin_dashboard, name='custom_admin_dashboard'),

]
