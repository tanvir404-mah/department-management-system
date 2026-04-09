import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cpnfig.settings')
django.setup()

from myapp.models import Student

students = Student.objects.all()
print(f"Total students: {students.count()}")
for student in students:
    print(f"Roll: {student.roll_number}, Semester: {student.semester}, Session: {student.session}, Shift: {student.shift}")
