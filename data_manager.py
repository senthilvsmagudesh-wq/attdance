import json
import os
from typing import Dict, List, Optional
from datetime import datetime, date
from models import User, Class, Student, AttendanceRecord

class DataManager:
    def __init__(self):
        self.data_dir = 'data'
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Initialize data files if they don't exist
        self._initialize_data_files()

    def _initialize_data_files(self):
        """Initialize data files with default data if they don't exist"""
        default_data = {
            'users.json': self._get_default_users(),
            'classes.json': self._get_default_classes(),
            'students.json': [], # Initialize as empty, will be populated from CSV if file doesn't exist
            'attendance.json': []
        }
        
        for filename, default_content in default_data.items():
            filepath = os.path.join(self.data_dir, filename)
            if not os.path.exists(filepath):
                if filename == 'students.json':
                    # Save an empty students.json first, then import from CSV
                    self._save_json(filename, [])
                    csv_path = os.path.join(os.path.dirname(filepath), '..', 'students.csv') # Assuming students.csv is in the project root
                    self.import_students_from_csv(csv_path)
                else:
                    self._save_json(filename, default_content)

    def _get_default_users(self):
        """Generate default users for the system"""
        return [
            {
                'user_id': 'admin1',
                'username': 'admin',
                'password': 'admin123',
                'role': 'admin',
                'name': 'System Administrator',
                'assigned_classes': []
            },
            {
                'user_id': 'hod1',
                'username': 'hod',
                'password': 'hod123',
                'role': 'hod',
                'name': 'Head of Department',
                'assigned_classes': []
            },
            {
                'user_id': 'staff1',
                'username': 'staff1',
                'password': 'staff123',
                'role': 'staff',
                'name': 'Prof. John Smith',
                'assigned_classes': ['CS_2A', 'CS_2B']
            },
            {
                'user_id': 'staff2',
                'username': 'staff2',
                'password': 'staff123',
                'role': 'staff',
                'name': 'Prof. Sarah Johnson',
                'assigned_classes': ['CS_3A', 'IT_2A']
            }
        ]

    def _get_default_classes(self):
        """Generate default classes for the system"""
        return [
            {
                'class_id': '2nd Year A',
                'class_name': '2nd Year A',
                'department': 'General',
                'semester': 2,
                'section': 'A',
                'students': []
            },
            {
                'class_id': '2nd Year B',
                'class_name': '2nd Year B',
                'department': 'General',
                'semester': 2,
                'section': 'B',
                'students': []
            },
            {
                'class_id': '2nd Year C',
                'class_name': '2nd Year C',
                'department': 'General',
                'semester': 2,
                'section': 'C',
                'students': []
            },
            {
                'class_id': '3rd Year',
                'class_name': '3rd Year',
                'department': 'General',
                'semester': 3,
                'section': '',
                'students': []
            },
            {
                'class_id': 'Final Year',
                'class_name': 'Final Year',
                'department': 'General',
                'semester': 4,
                'section': '',
                'students': []
            }
        ]

    def _get_default_students(self):
        """Generate default students for the system"""
        students = []
        
        # CS 2A students
        for i in range(1, 6):
            students.append({
                'student_id': f'CS2A00{i}',
                'roll_number': f'CS2A00{i}',
                'name': f'Student CS2A {i}',
                'class_id': 'CS_2A',
                'email': f'cs2a{i}@college.edu',
                'phone': f'9876543{i:03d}'
            })
        
        # CS 2B students
        for i in range(1, 6):
            students.append({
                'student_id': f'CS2B00{i}',
                'roll_number': f'CS2B00{i}',
                'name': f'Student CS2B {i}',
                'class_id': 'CS_2B',
                'email': f'cs2b{i}@college.edu',
                'phone': f'9876544{i:03d}'
            })
        
        # CS 3A students
        for i in range(1, 6):
            students.append({
                'student_id': f'CS3A00{i}',
                'roll_number': f'CS3A00{i}',
                'name': f'Student CS3A {i}',
                'class_id': 'CS_3A',
                'email': f'cs3a{i}@college.edu',
                'phone': f'9876545{i:03d}'
            })
        
        # IT 2A students
        for i in range(1, 6):
            students.append({
                'student_id': f'IT2A00{i}',
                'roll_number': f'IT2A00{i}',
                'name': f'Student IT2A {i}',
                'class_id': 'IT_2A',
                'email': f'it2a{i}@college.edu',
                'phone': f'9876546{i:03d}'
            })
        
        return students

    def import_students_from_csv(self, csv_filepath: str):
        """Import student data from a CSV file and save to students.json"""
        import csv
        students = []
        try:
            with open(csv_filepath, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    student_id = row['student_id']
                    student_name = row['student_name']
                    class_name = row['class_name'] # This will be used as class_id for now

                    # Generate dummy data for missing fields
                    email = f"{student_id.lower()}@college.edu"
                    phone = f"9876543{student_id[-3:]}" # Use last 3 digits of student_id for phone

                    students.append({
                        'student_id': student_id,
                        'roll_number': student_id, # Using student_id as roll_number
                        'name': student_name,
                        'class_id': class_name, # Assuming class_name from CSV can be class_id
                        'email': email,
                        'phone': phone
                    })
            self._save_json('students.json', students)
            print(f"Successfully imported {len(students)} students from {csv_filepath}")
        except FileNotFoundError:
            print(f"Error: CSV file not found at {csv_filepath}")
        except Exception as e:
            print(f"Error importing students from CSV: {e}")

    def _load_json(self, filename: str) -> List[Dict]:
        """Load data from JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_json(self, filename: str, data: List[Dict]):
        """Save data to JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    # User management methods
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        users_data = self._load_json('users.json')
        for user_data in users_data:
            if user_data['username'] == username:
                return User.from_dict(user_data)
        return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by user_id"""
        users_data = self._load_json('users.json')
        for user_data in users_data:
            if user_data['user_id'] == user_id:
                return User.from_dict(user_data)
        return None

    def get_user_name_by_id(self, user_id: str) -> str:
        """Get user name by user_id"""
        user = self.get_user_by_id(user_id)
        return user.name if user else "Unknown"

    # Class management methods
    def get_all_classes(self) -> List[Class]:
        """Get all classes"""
        classes_data = self._load_json('classes.json')
        return [Class.from_dict(class_data) for class_data in classes_data]

    def get_class_by_id(self, class_id: str) -> Optional[Class]:
        """Get class by class_id"""
        classes_data = self._load_json('classes.json')
        for class_data in classes_data:
            if class_data['class_id'] == class_id:
                return Class.from_dict(class_data)
        return None

    def get_classes_by_ids(self, class_ids: List[str]) -> List[Class]:
        """Get multiple classes by their IDs"""
        all_classes = self.get_all_classes()
        return [cls for cls in all_classes if cls.class_id in class_ids]

    # Student management methods
    def get_students_by_class(self, class_id: str) -> List[Student]:
        """Get all students in a class"""
        students_data = self._load_json('students.json')
        return [Student.from_dict(student_data) for student_data in students_data 
                if student_data['class_id'] == class_id]

    def get_student_by_id(self, student_id: str) -> Optional[Student]:
        """Get student by student_id"""
        students_data = self._load_json('students.json')
        for student_data in students_data:
            if student_data['student_id'] == student_id:
                return Student.from_dict(student_data)
        return None

    def search_students(self, query: str) -> List[Student]:
        """Search students by name or roll number"""
        students_data = self._load_json('students.json')
        query = query.lower()
        results = []
        for student_data in students_data:
            if (query in student_data['name'].lower() or 
                query in student_data['roll_number'].lower()):
                results.append(Student.from_dict(student_data))
        return results

    # Attendance management methods
    def save_attendance_records(self, records: List[AttendanceRecord]):
        """Save attendance records"""
        attendance_data = self._load_json('attendance.json')
        for record in records:
            attendance_data.append(record.to_dict())
        self._save_json('attendance.json', attendance_data)

    def get_attendance_records(self, class_id: str = None, date_str: str = None, 
                             attendance_type: str = None, period: int = None) -> List[AttendanceRecord]:
        """Get attendance records with optional filters"""
        attendance_data = self._load_json('attendance.json')
        records = []
        for record_data in attendance_data:
            record = AttendanceRecord.from_dict(record_data)
            if class_id and record.class_id != class_id:
                continue
            if date_str and record.date != date_str:
                continue
            
            # Filter by attendance_type and period if specified
            if attendance_type:
                if record.attendance_type != attendance_type:
                    continue
                if attendance_type == 'period' and period and record.period != period:
                    continue
                elif attendance_type == 'day' and record.period != 1: # Day attendance is Period 1
                    continue
            
            records.append(record)
        return records

    def is_attendance_locked(self, class_id: str, date_str: str, attendance_type: str, period: int = None) -> bool:
        """Check if attendance is locked for a specific class, date, and type"""
        records = self.get_attendance_records(class_id, date_str, attendance_type)
        if attendance_type == 'period' and period:
            records = [r for r in records if r.period == period]
        return any(r.locked for r in records)

    def lock_attendance(self, class_id: str, date_str: str, attendance_type: str, period: int = None):
        """Lock attendance for a specific class, date, and type"""
        attendance_data = self._load_json('attendance.json')
        for record_data in attendance_data:
            if (record_data['class_id'] == class_id and 
                record_data['date'] == date_str and 
                record_data['attendance_type'] == attendance_type):
                if attendance_type == 'period' and period and record_data.get('period') != period:
                    continue
                record_data['locked'] = True
        self._save_json('attendance.json', attendance_data)

    def update_attendance_record(self, record_id: str, updates: Dict):
        """Update an existing attendance record"""
        attendance_data = self._load_json('attendance.json')
        for i, record_data in enumerate(attendance_data):
            if record_data['record_id'] == record_id:
                attendance_data[i].update(updates)
                break
        self._save_json('attendance.json', attendance_data)

    def get_class_attendance_summary(self, class_id: str, date_str: str, attendance_type: str = 'day', period: int = None) -> Dict:
        """Get attendance summary for a class on a specific date"""
        records = self.get_attendance_records(class_id, date_str, attendance_type)
        if attendance_type == 'period' and period:
            records = [r for r in records if r.period == period]
        elif attendance_type == 'day':
            records = [r for r in records if r.period == 1] # Day attendance is first period
            
        students = self.get_students_by_class(class_id)
        
        summary = {
            'total_students': len(students),
            'present': 0,
            'absent': 0,
            'late': 0,
            'percentage': 0.0,
            'locked': False,
            'marked_by_user': 'N/A' # Initialize
        }
        
        if records:
            present_students = set()
            late_students = set()
            
            for record in records:
                if record.status == 'present':
                    present_students.add(record.student_id)
                    if record.is_late:
                        late_students.add(record.student_id)
                summary['locked'] = summary['locked'] or record.locked
            
            summary['present'] = len(present_students)
            summary['late'] = len(late_students)
            summary['absent'] = summary['total_students'] - summary['present']
            summary['percentage'] = (summary['present'] / summary['total_students']) * 100 if summary['total_students'] > 0 else 0
            
            # Get the user who marked the attendance (assuming one user marks per class/period)
            if records: # Check if records exist before trying to access first element
                summary['marked_by_user'] = self.get_user_name_by_id(records[0].marked_by)
        
        return summary

    def get_student_attendance_history(self, student_id: str, start_date: str = None, end_date: str = None) -> List[AttendanceRecord]:
        """Get attendance history for a specific student"""
        attendance_data = self._load_json('attendance.json')
        records = []
        
        for record_data in attendance_data:
            if record_data.get('student_id') == student_id:
                record_date = record_data['date']
                if start_date and record_date < start_date:
                    continue
                if end_date and record_date > end_date:
                    continue
                records.append(AttendanceRecord.from_dict(record_data))
        
        return sorted(records, key=lambda x: x.date, reverse=True)

    def get_department_attendance_summary(self, date_str: str, attendance_type: str = 'day', period: int = None) -> Dict:
        """Get attendance summary for all classes in the department"""
        all_classes = self.get_all_classes()
        summary = {
            'classes': [],
            'total_students': 0,
            'total_present': 0,
            'overall_percentage': 0.0
        }
        
        for class_obj in all_classes:
            class_summary = self.get_class_attendance_summary(class_obj.class_id, date_str, attendance_type, period)
            class_summary['class_name'] = class_obj.class_name
            class_summary['class_id'] = class_obj.class_id
            summary['classes'].append(class_summary)
            summary['total_students'] += class_summary['total_students']
            summary['total_present'] += class_summary['present']
        
        if summary['total_students'] > 0:
            summary['overall_percentage'] = (summary['total_present'] / summary['total_students']) * 100
        
        return summary

# Global instance
data_manager = DataManager()
