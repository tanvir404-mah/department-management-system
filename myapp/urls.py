from django.urls import path
from django.views.generic import RedirectView
from . import views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),

    path('profile/', views.profile, name='profile'),
    path('result/', views.result_view, name='result'),
    path('routine/', views.routine, name='routine'),
    path('students/', views.student_lookup, name='student_lookup'),
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
    path('student_subjects/', views.subjects, name='student_subjects'),
    
    path('attendance/mark/', views.attendance, name='attendance'),
    path('attendance/summary/', views.attendance_summary, name='attendance_summary'),
    
    # Authentication (Login/Logout)
    path('student/login/', views.student_login, name='student_login'),
    path('staff-login/', views.unified_staff_login, name='unified_staff_login'),
    path('teacher/login/', views.teacher_login, name='teacher_login'),
    path('hod/login/', views.hod_login, name='hod_login'),
    path('principal/login/', views.principal_login, name='principal_login'),
    path('lab-assistant/login/', views.lab_assistant_login, name='lab_assistant_login'),
    
    path('Student/register/verification/', views.verification_view, name='verification'),
    path('logout/', views.logout_view, name='logout'),
    
    # Financials
    path('payment/', views.payment, name='payment'),

    # 3-Step Registration Flow
    path('student/register-otp/', views.student_registration_step1, name='student_registration_step1'),
    path('student/verify-otp/', views.student_registration_step2, name='student_registration_step2'),
    path('student/set-password/', views.student_registration_step3, name='student_registration_step3'),

    # Registration Aliases
    path('Student/register/', views.student_registration_step1, name='student_register'),

    # Dashboards & Specialized CST Apps
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('student/project/submit/', views.submit_project, name='submit_project'),
    path('student/resource/request/', views.request_resource, name='request_resource'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/attendance/mark/<int:course_id>/', views.teacher_mark_attendance, name='teacher_mark_attendance'),
    path('teacher/results/add/<int:course_id>/', views.teacher_add_results, name='teacher_add_results'),
    path('teacher/project/review/<int:project_id>/', views.teacher_review_project, name='teacher_review_project'),
    path('teacher/notice/publish/', views.teacher_publish_notice, name='teacher_publish_notice'),
    
    # HOD Portal (Department Scoped)
    path('hod/dashboard/', views.hod_dashboard, name='hod_dashboard'),
    path('hod/faculty/', views.hod_faculty_mgmt, name='hod_faculty_mgmt'),
    path('hod/students/', views.hod_student_mgmt, name='hod_student_mgmt'),
    path('hod/departments/', views.hod_dept_mgmt, name='hod_dept_mgmt'),
    path('hod/courses/', views.hod_course_mgmt, name='hod_course_mgmt'),
    path('hod/routine/', views.hod_routine_mgmt, name='hod_routine_mgmt'),
    path('hod/routine/upload-image/', views.upload_routine_image, name='upload_routine_image'),
    path('hod/routine/delete/<int:routine_id>/', views.delete_routine, name='delete_routine'),
    path('hod/allotment/', views.hod_course_allotment, name='hod_course_allotment'),
    path('hod/lab/', views.hod_lab_mgmt, name='hod_lab_mgmt'),
    path('hod/broadcast/', views.hod_broadcast_notice, name='hod_broadcast_notice'),
    path('hod/parents-alert/', views.hod_parents_alert, name='hod_parents_alert'),

    # ════════════════════════════════════════════════════
    #  STAFF DASHBOARD — Full Admin Command Center
    # ════════════════════════════════════════════════════
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff-dashboard/', views.staff_dashboard, name='admin_dashboard'),
    path('staff-dashboard/users/', views.admin_user_mgmt, name='admin_user_mgmt'),
    path('staff-dashboard/security/', views.admin_security_logs, name='admin_security_logs'),
    path('staff-dashboard/bulk-import/', views.admin_bulk_import, name='admin_bulk_import'),
    path('staff-dashboard/semester-transition/', views.admin_semester_transition, name='admin_semester_transition'),
    path('staff-dashboard/reset-password/', views.admin_reset_password, name='admin_reset_password'),

    # CMS & Portal Management
    path('staff-dashboard/cms/banners/', views.admin_manage_banners, name='admin_manage_banners'),
    path('staff-dashboard/cms/banners/<int:banner_id>/delete/', views.admin_delete_banner, name='admin_delete_banner'),
    path('staff-dashboard/cms/notices/', views.admin_manage_notices, name='admin_manage_notices'),
    path('staff-dashboard/cms/notices/<int:notice_id>/delete/', views.admin_delete_global_notice, name='admin_delete_global_notice'),

    # System Administration (Full CRUD)
    path('staff-dashboard/system/', views.admin_system_mgmt, name='admin_system_mgmt'),
    # ... previous user/dept/course CRUD ...
    path('staff-dashboard/users/create/', views.admin_create_user, name='admin_create_user'),
    path('staff-dashboard/users/<int:user_id>/edit/', views.admin_edit_user, name='admin_edit_user'),
    path('staff-dashboard/users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    path('staff-dashboard/users/<int:user_id>/toggle-superuser/', views.admin_toggle_superuser, name='admin_toggle_superuser'),
    path('staff-dashboard/departments/create/', views.admin_create_dept, name='admin_create_dept'),
    path('staff-dashboard/departments/<int:dept_id>/edit/', views.admin_edit_dept, name='admin_edit_dept'),
    path('staff-dashboard/departments/<int:dept_id>/delete/', views.admin_delete_dept, name='admin_delete_dept'),
    path('staff-dashboard/courses/create/', views.admin_create_course, name='admin_create_course'),
    path('staff-dashboard/courses/<int:course_id>/edit/', views.admin_edit_course, name='admin_edit_course'),
    path('staff-dashboard/courses/<int:course_id>/delete/', views.admin_delete_course, name='admin_delete_course'),
    path('staff-dashboard/notices/', views.admin_notices, name='admin_notices'),
    path('staff-dashboard/notices/<int:notice_id>/delete/', views.admin_delete_notice, name='admin_delete_notice'),

    # Public CMS Pages

    # Legacy /admin-portal/ redirects to staff-dashboard
    path('admin-portal/', RedirectView.as_view(url='/staff-dashboard/', permanent=False)),
    path('custom-admin/', RedirectView.as_view(url='/staff-dashboard/', permanent=False), name='custom_admin_dashboard'),

    # Personnel AJAX
    path('add-student/', views.add_student_ajax, name='add_student_ajax'),
    path('get-students/', views.get_students_ajax, name='get_students_ajax'),
    path('student/delete/', views.student_delete, name='student_delete'),
    path('teacher/delete/', views.teacher_delete, name='teacher_delete'),
    path('teacher/edit/', views.teacher_edit, name='teacher_edit'),
    path('send/meaasge/', views.send_meaasge, name='send_message'),
    path('edit/student/', views.edit_student, name='edit_student'),
    path('add-teacher/', views.add_teacher_ajax, name='add_teacher_ajax'),
    path('get-teachers/', views.get_teachers_ajax, name='get_teachers_ajax'),

    # Attendance AJAX
    path('add-attendance/', views.add_attendance_ajax, name='add_attendance_ajax'),
    path('get-attendance/', views.get_attendance_ajax, name='get_attendance_ajax'),

    # Communications
    path('teacher/notices/ajax', views.get_teacher_notices_ajax, name='get_teacher_notices_ajax'),
    path('notices/publish/', views.publish_notice, name='publish_notice'),
    path('student/notices/', views.get_student_notices, name='get_student_notices'),
    path('add-notice/', views.add_notice_ajax, name='add_notice_ajax'),
    path('get-notices/', views.get_notices_ajax, name='get_notices_ajax'),
    path("publish-post/", views.publish_post, name="publish_post"),
    
    # Results
    path('add-result/', views.add_result_ajax, name='add_result_ajax'),
    path('get-results/', views.get_results_ajax, name='get_results_ajax'),

    # Lab Assistant Hub
    path('lab-assistant/dashboard/', views.lab_assistant_dashboard, name='lab_assistant_dashboard'),
    path('lab-assistant/toggle-status/<int:schedule_id>/', views.lab_toggle_status, name='lab_toggle_status'),
    path('lab-assistant/update-item-status/', views.lab_update_item_status, name='lab_update_item_status'),
    path('lab-assistant/report-issue/', views.lab_report_issue, name='lab_report_issue'),
    path('lab-assistant/mark-ca/<int:course_id>/', views.lab_mark_ca, name='lab_mark_ca'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
