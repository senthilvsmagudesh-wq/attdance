from datetime import datetime, date
from typing import Dict, List, Optional
import json
import os

class User:
    def __init__(self, user_id: str, username: str, password: str, role: str, name: str, assigned_classes: List[str] = None):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.role = role  # 'staff', 'hod', 'admin'
        self.name = name
        self.assigned_classes = assigned_classes or []

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'password': self.password,
            'role': self.role,
            'name': self.name,
            'assigned_classes': self.assigned_classes
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

class Class:
    def __init__(self, class_id: str, class_name: str, department: str, semester: int, section: str, students: List[str] = None):
        self.class_id = class_id
        self.class_name = class_name
        self.department = department
        self.semester = semester
        self.section = section
        self.students = students or []

    def to_dict(self):
        return {
            'class_id': self.class_id,
            'class_name': self.class_name,
            'department': self.department,
            'semester': self.semester,
            'section': self.section,
            'students': self.students
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

class Student:
    def __init__(self, student_id: str, roll_number: str, name: str, class_id: str, email: str = "", phone: str = ""):
        self.student_id = student_id
        self.roll_number = roll_number
        self.name = name
        self.class_id = class_id
        self.email = email
        self.phone = phone

    def to_dict(self):
        return {
            'student_id': self.student_id,
            'roll_number': self.roll_number,
            'name': self.name,
            'class_id': self.class_id,
            'email': self.email,
            'phone': self.phone
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

class AttendanceRecord:
    def __init__(self, record_id: str, class_id: str, date: str, attendance_type: str, 
                 period: int = None, student_id: str = "", status: str = "", 
                 is_late: bool = False, marked_by: str = "", locked: bool = False,
                 submitted_as_type: str = "period"): # New parameter
        self.record_id = record_id
        self.class_id = class_id
        self.date = date
        self.attendance_type = attendance_type  # 'day' or 'period'
        self.period = period  # None for day attendance, 1-8 for period
        self.student_id = student_id
        self.status = status  # 'present', 'absent'
        self.is_late = is_late
        self.marked_by = marked_by
        self.locked = locked
        self.submitted_as_type = submitted_as_type
        self.created_at = datetime.now().isoformat()

    def to_dict(self):
        return {
            'record_id': self.record_id,
            'class_id': self.class_id,
            'date': self.date,
            'attendance_type': self.attendance_type,
            'period': self.period,
            'student_id': self.student_id,
            'status': self.status,
            'is_late': self.is_late,
            'marked_by': self.marked_by,
            'locked': self.locked,
            'created_at': self.created_at,
            'submitted_as_type': self.submitted_as_type # New field
        }

    @classmethod
    def from_dict(cls, data):
        record = cls(
            data['record_id'], data['class_id'], data['date'], 
            data['attendance_type'], data.get('period'), data.get('student_id', ''),
            data.get('status', ''), data.get('is_late', False), 
            data.get('marked_by', ''), data.get('locked', False),
            data.get('submitted_as_type', 'period') # New field
        )
        record.created_at = data.get('created_at', datetime.now().isoformat())
        return record
