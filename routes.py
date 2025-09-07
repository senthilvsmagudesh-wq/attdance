from flask import render_template, request, redirect, url_for, session, flash, jsonify, make_response
from datetime import datetime, timedelta
import uuid
import json
from app import app
from data_manager import data_manager
from chatbot import chatbot
from models import AttendanceRecord

@app.route('/')
def index():
    """Home page - redirect to login if not authenticated"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    if user.role == 'staff':
        return redirect(url_for('staff_dashboard'))
    elif user.role == 'hod':
        return redirect(url_for('hod_dashboard'))
    else:
        return redirect(url_for('hod_dashboard'))  # Admin also goes to HOD dashboard

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return render_template('login.html')
        
        user = data_manager.get_user_by_username(username)
        if user and user.password == password:
            session['user_id'] = user.user_id
            session['username'] = user.username
            session['user_role'] = user.role
            session['user_name'] = user.name
            
            flash(f'Welcome, {user.name}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))



@app.route('/staff')
def staff_dashboard():
    """Staff dashboard - shows assigned classes and allows selection"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    if not user or user.role != 'staff':
        flash('Access denied. Staff access required.', 'error')
        return redirect(url_for('login'))
    
    assigned_classes = data_manager.get_classes_by_ids(user.assigned_classes)
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get today's attendance summary for assigned classes (for display in cards)
    class_summaries = []
    for class_obj in assigned_classes: # Iterate through assigned classes
        summary = data_manager.get_class_attendance_summary(class_obj.class_id, today, attendance_type='day', period=None)
        summary['class'] = class_obj
        class_summaries.append(summary)
    
    return render_template('staff_dashboard.html', 
                         user=user, 
                         class_summaries=class_summaries,
                         all_classes=assigned_classes, # Pass assigned classes for selection
                         today=today)



@app.route('/mark-attendance/<class_id>')
def mark_attendance(class_id):
    """Mark attendance page"""
    with open("debug_log.txt", "a") as f:
        f.write(f"DEBUG: mark_attendance - class_id received: {class_id}\n")
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    if not user or user.role != 'staff':
        flash('Access denied. Staff access required.', 'error')
        return redirect(url_for('login'))
    
    # Removed check for user.assigned_classes as all staff can access all classes
    # if class_id not in user.assigned_classes:
    #     flash('Access denied. You are not assigned to this class.', 'error')
    #     return redirect(url_for('staff_dashboard'))
    
    class_obj = data_manager.get_class_by_id(class_id)
    if not class_obj:
        flash('Class not found', 'error')
        return redirect(url_for('staff_dashboard'))
    
    students = data_manager.get_students_by_class(class_id)
    with open("debug_log.txt", "a") as f:
        f.write(f"DEBUG: mark_attendance - students fetched: {len(students)}\n")
        for student in students:
            f.write(f"  Student: {student.name}, Class ID: {student.class_id}\n")

    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    attendance_type = request.args.get('type', 'day')
    
    period = None
    if attendance_type == 'period':
        period = int(request.args.get('period', 1))
    elif attendance_type == 'day':
        period = 1 # Day attendance is first period attendance
    
    # Check if attendance is already locked
    locked = data_manager.is_attendance_locked(class_id, date_str, attendance_type, period)
    
    # Get existing attendance records
    existing_records = data_manager.get_attendance_records(class_id, date_str, attendance_type)
    if attendance_type == 'period' and period:
        existing_records = [r for r in existing_records if r.period == period]
    
    # Create attendance status map
    attendance_status = {}
    for student in students:
        attendance_status[student.student_id] = 'absent'  # Default to absent
    
    for record in existing_records:
        if record.student_id in attendance_status:
            attendance_status[record.student_id] = 'present' if record.status == 'present' else 'absent'
    
    return render_template('mark_attendance.html',
                         class_obj=class_obj,
                         students=students,
                         date_str=date_str,
                         attendance_type=attendance_type,
                         period=period,
                         locked=locked,
                         attendance_status=attendance_status,
                         user=user)

@app.route('/submit-attendance', methods=['POST'])
def submit_attendance():
    """Submit attendance records"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    if not user or user.role != 'staff':
        flash('Access denied. Staff access required.', 'error')
        return redirect(url_for('login'))
    
    class_id = request.form.get('class_id')
    date_str = request.form.get('date')
    attendance_type = request.form.get('attendance_type')
    period = int(request.form.get('period')) if request.form.get('period') else None
    
    # Check access permissions
    if class_id not in user.assigned_classes:
        flash('Access denied. You are not assigned to this class.', 'error')
        return redirect(url_for('staff_dashboard'))
    
    # Check if already locked
    if data_manager.is_attendance_locked(class_id, date_str, attendance_type, period):
        flash('Attendance is already locked for this class and date.', 'error')
        return redirect(url_for('mark_attendance', class_id=class_id))
    
    students = data_manager.get_students_by_class(class_id)
    records = []
    
    # Process attendance data
    for student in students:
        status = request.form.get(f'student_{student.student_id}', 'absent')
        
        record = AttendanceRecord(
            record_id=str(uuid.uuid4()),
            class_id=class_id,
            date=date_str,
            attendance_type=attendance_type,
            period=period,
            student_id=student.student_id,
            status=status,
            is_late=False,
            marked_by=user.user_id,
            locked=True  # Lock immediately after submission
        )
        records.append(record)
    
    # Save records
    data_manager.save_attendance_records(records)
    
    flash('Attendance submitted successfully!', 'success')
    return redirect(url_for('staff_dashboard'))

@app.route('/latecomer-attendance/<class_id>')
def latecomer_attendance(class_id):
    """Latecomer attendance page - only shows absent students"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    if not user or user.role != 'staff':
        flash('Access denied. Staff access required.', 'error')
        return redirect(url_for('login'))
    
    # Check access permissions
    if class_id not in user.assigned_classes:
        flash('Access denied. You are not assigned to this class.', 'error')
        return redirect(url_for('staff_dashboard'))
    
    class_obj = data_manager.get_class_by_id(class_id)
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    attendance_type = request.args.get('type', 'day')
    
    period = None
    if attendance_type == 'period':
        period = int(request.args.get('period', 1))
    elif attendance_type == 'day':
        period = 1 # Day attendance is first period attendance
    
    # Check if main attendance is locked (prerequisite for latecomer marking)
    if not data_manager.is_attendance_locked(class_id, date_str, attendance_type, period):
        flash('Please submit the main attendance first before marking latecomers.', 'error')
        return redirect(url_for('mark_attendance', class_id=class_id))
    
    # Get absent students only
    all_students = data_manager.get_students_by_class(class_id)
    existing_records = data_manager.get_attendance_records(class_id, date_str, attendance_type)
    if attendance_type == 'period' and period:
        existing_records = [r for r in existing_records if r.period == period]
    
    present_student_ids = set(r.student_id for r in existing_records if r.status == 'present')
    absent_students = [s for s in all_students if s.student_id not in present_student_ids]
    
    return render_template('latecomer_attendance.html',
                         class_obj=class_obj,
                         absent_students=absent_students,
                         date_str=date_str,
                         attendance_type=attendance_type,
                         period=period,
                         user=user)

@app.route('/submit-latecomer', methods=['POST'])
def submit_latecomer():
    """Submit latecomer attendance"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    if not user or user.role != 'staff':
        flash('Access denied. Staff access required.', 'error')
        return redirect(url_for('login'))
    
    class_id = request.form.get('class_id')
    date_str = request.form.get('date')
    attendance_type = request.form.get('attendance_type')
    period = int(request.form.get('period')) if request.form.get('period') else None
    
    # Check access permissions
    if class_id not in user.assigned_classes:
        flash('Access denied. You are not assigned to this class.', 'error')
        return redirect(url_for('staff_dashboard'))
    
    # Get selected latecomers
    latecomer_student_ids = request.form.getlist('latecomers')
    
    if latecomer_student_ids:
        records = []
        for student_id in latecomer_student_ids:
            record = AttendanceRecord(
                record_id=str(uuid.uuid4()),
                class_id=class_id,
                date=date_str,
                attendance_type=attendance_type,
                period=period,
                student_id=student_id,
                status='present',
                is_late=True,
                marked_by=user.user_id,
                locked=True
            )
            records.append(record)
        
        data_manager.save_attendance_records(records)
        flash(f'{len(latecomer_student_ids)} latecomer(s) marked successfully!', 'success')
    else:
        flash('No latecomers selected.', 'info')
    
    return redirect(url_for('staff_dashboard'))

@app.route('/hod')
def hod_dashboard():
    """HOD dashboard with class overview cards"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    if not user or user.role not in ['hod', 'admin']:
        flash('Access denied. HOD access required.', 'error')
        return redirect(url_for('login'))
    
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    attendance_type = request.args.get('type', 'day')
    period = None
    if attendance_type == 'period':
        period = int(request.args.get('period', 1))
    elif attendance_type == 'day':
        period = 1 # Day attendance is first period attendance
    
    # Get department summary for the selected date and type/period
    dept_summary = data_manager.get_department_attendance_summary(date_str, attendance_type, period)
    
    # For yesterday's summary, always use day attendance (period 1)
    yesterday = (datetime.strptime(date_str, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
    yesterday_summary = data_manager.get_department_attendance_summary(yesterday, 'day', 1)
    
    # Calculate trends for each class
    for i, class_summary in enumerate(dept_summary['classes']):
        class_id = class_summary['class_id']
        yesterday_class = next((c for c in yesterday_summary['classes'] if c['class_id'] == class_id), None)
        
        if yesterday_class:
            trend = class_summary['percentage'] - yesterday_class['percentage']
            dept_summary['classes'][i]['trend'] = trend
        else:
            dept_summary['classes'][i]['trend'] = 0
    
    return render_template('hod_dashboard.html',
                         user=user,
                         dept_summary=dept_summary,
                         today=date_str, # Pass the selected date
                         yesterday_summary=yesterday_summary)

@app.route('/class-details/<class_id>')
def class_details(class_id):
    """Class details page with attendance drilldown"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    if not user or user.role not in ['hod', 'admin']:
        flash('Access denied. HOD access required.', 'error')
        return redirect(url_for('login'))
    
    class_obj = data_manager.get_class_by_id(class_id)
    if not class_obj:
        flash('Class not found', 'error')
        return redirect(url_for('hod_dashboard'))
    
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Get class attendance summary and student details
    summary = data_manager.get_class_attendance_summary(class_id, date_str)
    students = data_manager.get_students_by_class(class_id)
    records = data_manager.get_attendance_records(class_id, date_str)
    
    # Create student attendance map
    student_attendance = {}
    for student in students:
        student_attendance[student.student_id] = {
            'student': student,
            'status': 'absent',
            'is_late': False
        }
    
    for record in records:
        if record.student_id in student_attendance:
            student_attendance[record.student_id]['status'] = record.status
            student_attendance[record.student_id]['is_late'] = record.is_late
    
    # Get weekly attendance trend
    weekly_trend = []
    for i in range(7):
        check_date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_summary = data_manager.get_class_attendance_summary(class_id, check_date)
        weekly_trend.append({
            'date': check_date,
            'percentage': day_summary['percentage']
        })
    weekly_trend.reverse()
    
    return render_template('class_details.html',
                         class_obj=class_obj,
                         summary=summary,
                         student_attendance=student_attendance,
                         weekly_trend=weekly_trend,
                         date_str=date_str,
                         user=user)

@app.route('/student-details/<student_id>')
def student_details(student_id):
    """Student details page with attendance history"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    if not user or user.role not in ['hod', 'admin']:
        flash('Access denied. HOD access required.', 'error')
        return redirect(url_for('login'))
    
    student = data_manager.get_student_by_id(student_id)
    if not student:
        flash('Student not found', 'error')
        return redirect(url_for('hod_dashboard'))
    
    # Get attendance history for the past 30 days
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    history = data_manager.get_student_attendance_history(student_id, start_date, end_date)
    
    # Calculate statistics
    total_days = len(set(record.date for record in history))
    present_days = len(set(record.date for record in history if record.status == 'present'))
    absent_days = total_days - present_days
    late_count = sum(1 for record in history if record.is_late)
    percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    # Group history by date
    daily_attendance = {}
    for record in history:
        if record.date not in daily_attendance:
            daily_attendance[record.date] = []
        daily_attendance[record.date].append(record)
    
    # Create daily summary
    daily_summary = []
    for date_str in sorted(daily_attendance.keys(), reverse=True):
        day_records = daily_attendance[date_str]
        is_present = any(r.status == 'present' for r in day_records)
        is_late = any(r.is_late for r in day_records)
        
        # Convert AttendanceRecord objects to dictionaries
        serializable_records = []
        for record in day_records:
            serializable_records.append({
                'record_id': record.record_id,
                'class_id': record.class_id,
                'date': record.date,
                'attendance_type': record.attendance_type,
                'period': record.period,
                'student_id': record.student_id,
                'status': record.status,
                'is_late': record.is_late,
                'marked_by': record.marked_by,
                'locked': record.locked
            })

        daily_summary.append({
            'date': date_str,
            'status': 'present' if is_present else 'absent',
            'is_late': is_late,
            'records': serializable_records # Use serializable records here
        })
    
    stats = {
        'total_days': total_days,
        'present_days': present_days,
        'absent_days': absent_days,
        'late_count': late_count,
        'percentage': percentage
    }
    
    class_obj = data_manager.get_class_by_id(student.class_id)
    
    return render_template('student_details.html',
                         student=student,
                         class_obj=class_obj,
                         stats=stats,
                         daily_summary=daily_summary[:20],  # Show last 20 days
                         user=user)

@app.route('/search-student')
def search_student():
    """Search for students"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    if not user or user.role not in ['hod', 'admin']:
        flash('Access denied. HOD access required.', 'error')
        return redirect(url_for('login'))
    
    query = request.args.get('q', '').strip()
    students = []
    
    if query and len(query) >= 2:
        students = data_manager.search_students(query)
    
    if request.args.get('format') == 'json':
        return jsonify([{
            'student_id': s.student_id,
            'name': s.name,
            'roll_number': s.roll_number,
            'class_id': s.class_id
        } for s in students])
    
    return render_template('student_search.html', students=students, query=query, user=user)

@app.route('/chatbot')
def chatbot_page():
    """Chatbot interface page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    if not user or user.role not in ['hod', 'admin']:
        flash('Access denied. HOD access required.', 'error')
        return redirect(url_for('login'))
    
    return render_template('chatbot.html', user=user)

@app.route('/chatbot-query', methods=['POST'])
def chatbot_query():
    """Process chatbot query"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = data_manager.get_user_by_id(session['user_id'])
    if not user or user.role not in ['hod', 'admin']:
        return jsonify({'error': 'Access denied'}), 403
    
    query = request.json.get('query', '').strip()
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    response = chatbot.process_query(query, user.role)
    return jsonify(response)

@app.route('/reports')
def reports():
    """Reports page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    if not user or user.role not in ['hod', 'admin']:
        flash('Access denied. HOD access required.', 'error')
        return redirect(url_for('login'))
    
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    report_type = request.args.get('type', 'department')
    
    if report_type == 'department':
        dept_summary = data_manager.get_department_attendance_summary(date_str)
        return render_template('reports.html',
                             user=user,
                             report_data=dept_summary,
                             date_str=date_str,
                             report_type=report_type)
    
    return render_template('reports.html', user=user)

@app.route('/download-report-jpg')
def download_report_jpg():
    """Download today's report as a JPG image"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    if not user or user.role not in ['hod', 'admin']:
        flash('Access denied. HOD access required.', 'error')
        return redirect(url_for('login'))

    try:
        import imgkit
    except ImportError:
        flash('The image generation library is not installed. Please contact the administrator.', 'error')
        return redirect(url_for('reports'))

    date_str = datetime.now().strftime('%Y-%m-%d')
    day_of_week = datetime.now().strftime('%A')
    dept_summary = data_manager.get_department_attendance_summary(date_str)

    html = render_template('report_print_template.html', report_data=dept_summary, date_str=date_str, day_of_week=day_of_week)

    try:
        image = imgkit.from_string(html, False, options={'format': 'jpg'})
        
        response = make_response(image)
        response.headers['Content-Type'] = 'image/jpeg'
        response.headers['Content-Disposition'] = f'attachment; filename=daily_attendance_report_{date_str}.jpg'
        
        return response
    except Exception as e:
        flash(f'Error generating image: {e}', 'error')
        return redirect(url_for('reports'))

@app.route('/print-report')
def print_report():
    """Print today's report"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = data_manager.get_user_by_id(session['user_id'])
    if not user or user.role not in ['hod', 'admin']:
        flash('Access denied. HOD access required.', 'error')
        return redirect(url_for('login'))

    date_str = datetime.now().strftime('%Y-%m-%d')
    day_of_week = datetime.now().strftime('%A')
    dept_summary = data_manager.get_department_attendance_summary(date_str)

    return render_template('report_print_template.html', report_data=dept_summary, date_str=date_str, day_of_week=day_of_week)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500
