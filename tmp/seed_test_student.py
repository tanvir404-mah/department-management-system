import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cpnfig.settings')
django.setup()

from myapp.models import Student, CustomUser, Department

def seed_test_student():
    # 1. Ensure a department exists
    dept, _ = Department.objects.get_or_create(name="Computer Science & Technology", code="CST")
    
    # 2. Create a User for the student
    username = "teststudent"
    if not CustomUser.objects.filter(username=username).exists():
        user = CustomUser.objects.create_user(
            username=username, 
            password="password123",
            first_name="Rahat",
            last_name="Hossain",
            role="student"
        )
    else:
        user = CustomUser.objects.get(username=username)

    # 3. Create/Update the Student record with search criteria
    student, created = Student.objects.update_or_create(
        user=user,
        defaults={
            'roll_number': '749001',
            'semester': 5,
            'session': '2021-22',
            'department': dept,
            'shift': '1st'
        }
    )
    
    if created:
        print("Test student Rahat (Roll: 749001, Sem: 5, Session: 2021-22) created!")
    else:
        print("Updated student Rahat with: Roll: 749001, Sem: 5, Session: 2021-22")

if __name__ == "__main__":
    seed_test_student()
