from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from data_manager import data_manager
import re
import json
import statistics

class AttendanceChatbot:
    def __init__(self):
        self.commands = {
            'attendance': self._get_attendance_info,
            'latecomers': self._get_latecomer_info,
            'summary': self._get_summary_info,
            'student': self._get_student_info,
            'class': self._get_class_info,
            'help': self._get_help_info,
            'analytics': self._get_analytics_info,
            'predictions': self._get_predictions_info,
            'insights': self._get_insights_info,
            'compare': self._get_comparison_info
        }
        
        # Enhanced NLP patterns for better intent recognition
        self.intent_patterns = {
            'attendance_query': [
                r'(?:show|get|what|how).*attendance.*(?:for|of|in)\s*(.*?)(?:today|yesterday|\d{4}-\d{2}-\d{2})?',
                r'attendance.*(?:for|of|in)\s*(.*?)(?:today|yesterday|\d{4}-\d{2}-\d{2})?',
                r'(?:how many|who).*(?:present|absent).*(?:in|for)\s*(.*?)'
            ],
            'latecomer_query': [
                r'(?:show|get|who|list).*(?:late|latecomer|tardy).*(?:in|for)\s*(.*?)',
                r'(?:late|latecomer|tardy).*(?:students|people).*(?:in|for)\s*(.*?)'
            ],
            'student_query': [
                r'(?:show|get|find).*(?:student|info|details).*(?:for|of|about)\s*(\w+)',
                r'(?:student|info|details).*(?:for|of|about)\s*(\w+)',
                r'attendance.*(?:for|of).*student\s*(\w+)'
            ],
            'analytics_query': [
                r'(?:analytics|analysis|trend|pattern|statistics)',
                r'(?:show|get).*(?:chart|graph|visualization)',
                r'(?:performance|improvement|decline).*(?:over|in).*(?:time|period)'
            ],
            'prediction_query': [
                r'(?:predict|forecast|estimate|expect)',
                r'(?:what|how).*(?:will|might|could).*(?:happen|be)',
                r'(?:future|upcoming|next).*(?:attendance|performance)'
            ],
            'comparison_query': [
                r'(?:compare|comparison|versus|vs|against)',
                r'(?:better|worse|higher|lower).*(?:than|compared)',
                r'(?:which|what).*(?:best|worst|highest|lowest)'
            ]
        }
        
        # Conversation context storage
        self.conversation_context = {
            'last_query': '',
            'last_class': '',
            'last_student': '',
            'last_date': '',
            'preferences': {}
        }

    def process_query(self, query: str, user_role: str = 'hod') -> Dict[str, Any]:
        """Process user query and return appropriate response with enhanced NLP"""
        original_query = query
        query = query.lower().strip()
        
        # Update conversation context
        self.conversation_context['last_query'] = original_query
        
        # Extract entities from query
        entities = self._extract_entities(query)
        
        # Determine intent using advanced pattern matching
        intent, confidence = self._identify_intent(query)
        
        # Extract date from query if present
        target_date = entities.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Handle follow-up questions using context
        if self._is_follow_up_question(query):
            return self._handle_follow_up(query, target_date, user_role)
        
        # Map intent to command
        command = self._intent_to_command(intent)
        
        if command in self.commands:
            response = self.commands[command](query, target_date, user_role, entities)
            # Add intelligent suggestions
            response['suggestions'] = self._generate_suggestions(intent, entities, user_role)
            return response
        else:
            return self._get_intelligent_response(query, target_date, entities, user_role)

    def _extract_date(self, query: str) -> str:
        """Extract date from query string"""
        # Look for date patterns like "today", "yesterday", "2024-09-05"
        if 'today' in query:
            return datetime.now().strftime('%Y-%m-%d')
        elif 'yesterday' in query:
            yesterday = datetime.now() - timedelta(days=1)
            return yesterday.strftime('%Y-%m-%d')
        
        # Look for date in YYYY-MM-DD format
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        match = re.search(date_pattern, query)
        if match:
            return match.group()
        
        return datetime.now().strftime('%Y-%m-%d')

    def _identify_command(self, query: str) -> str:
        """Identify the main command from the query"""
        if any(word in query for word in ['late', 'latecomer', 'latecomers']):
            return 'latecomers'
        elif any(word in query for word in ['student', 'students']):
            return 'student'
        elif any(word in query for word in ['class', 'classes']):
            return 'class'
        elif any(word in query for word in ['summary', 'overview', 'report']):
            return 'summary'
        elif any(word in query for word in ['attendance', 'present', 'absent']):
            return 'attendance'
        elif 'help' in query:
            return 'help'
        else:
            return 'attendance'

    def _get_attendance_info(self, query: str, date_str: str, user_role: str) -> Dict[str, Any]:
        """Get attendance information"""
        class_name = self._extract_class_name(query)
        
        if class_name:
            # Get specific class attendance
            class_obj = self._find_class_by_name(class_name)
            if class_obj:
                summary = data_manager.get_class_attendance_summary(class_obj.class_id, date_str)
                students = data_manager.get_students_by_class(class_obj.class_id)
                records = data_manager.get_attendance_records(class_obj.class_id, date_str)
                
                student_status = {}
                for student in students:
                    student_status[student.student_id] = {
                        'name': student.name,
                        'roll': student.roll_number,
                        'status': 'absent',
                        'is_late': False
                    }
                
                for record in records:
                    if record.student_id in student_status:
                        student_status[record.student_id]['status'] = record.status
                        student_status[record.student_id]['is_late'] = record.is_late
                
                return {
                    'type': 'class_attendance',
                    'class_name': class_obj.class_name,
                    'date': date_str,
                    'summary': summary,
                    'students': list(student_status.values()),
                    'message': f"Attendance for {class_obj.class_name} on {date_str}"
                }
        
        # Get department-wide attendance
        dept_summary = data_manager.get_department_attendance_summary(date_str)
        return {
            'type': 'department_attendance',
            'date': date_str,
            'summary': dept_summary,
            'message': f"Department attendance summary for {date_str}"
        }

    def _get_latecomer_info(self, query: str, date_str: str, user_role: str) -> Dict[str, Any]:
        """Get latecomer information"""
        class_name = self._extract_class_name(query)
        latecomers = []
        
        if class_name:
            # Get latecomers for specific class
            class_obj = self._find_class_by_name(class_name)
            if class_obj:
                records = data_manager.get_attendance_records(class_obj.class_id, date_str)
                for record in records:
                    if record.is_late and record.status == 'present':
                        student = data_manager.get_student_by_id(record.student_id)
                        if student:
                            latecomers.append({
                                'name': student.name,
                                'roll': student.roll_number,
                                'class': class_obj.class_name,
                                'time': record.created_at
                            })
                
                return {
                    'type': 'class_latecomers',
                    'class_name': class_obj.class_name,
                    'date': date_str,
                    'latecomers': latecomers,
                    'message': f"Latecomers in {class_obj.class_name} on {date_str}"
                }
        
        # Get all latecomers
        all_classes = data_manager.get_all_classes()
        for class_obj in all_classes:
            records = data_manager.get_attendance_records(class_obj.class_id, date_str)
            for record in records:
                if record.is_late and record.status == 'present':
                    student = data_manager.get_student_by_id(record.student_id)
                    if student:
                        latecomers.append({
                            'name': student.name,
                            'roll': student.roll_number,
                            'class': class_obj.class_name,
                            'time': record.created_at
                        })
        
        return {
            'type': 'all_latecomers',
            'date': date_str,
            'latecomers': latecomers,
            'message': f"All latecomers on {date_str}"
        }

    def _get_student_info(self, query: str, date_str: str, user_role: str) -> Dict[str, Any]:
        """Get student-specific information"""
        # Try to extract student name or roll number from query
        words = query.split()
        student_query = ""
        for word in words:
            if len(word) > 2 and word.isalnum():
                student_query = word
                break
        
        if student_query:
            students = data_manager.search_students(student_query)
            if students:
                student = students[0]  # Take the first match
                
                # Get recent attendance history
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                history = data_manager.get_student_attendance_history(student.student_id, start_date, end_date)
                
                # Calculate attendance percentage
                total_days = len(set(record.date for record in history))
                present_days = len(set(record.date for record in history if record.status == 'present'))
                percentage = (present_days / total_days * 100) if total_days > 0 else 0
                
                late_count = sum(1 for record in history if record.is_late)
                
                return {
                    'type': 'student_info',
                    'student': {
                        'name': student.name,
                        'roll': student.roll_number,
                        'class_id': student.class_id
                    },
                    'stats': {
                        'attendance_percentage': percentage,
                        'total_days': total_days,
                        'present_days': present_days,
                        'absent_days': total_days - present_days,
                        'late_count': late_count
                    },
                    'recent_history': [
                        {
                            'date': record.date,
                            'status': record.status,
                            'is_late': record.is_late
                        } for record in history[:10]
                    ],
                    'message': f"Attendance information for {student.name}"
                }
        
        return {
            'type': 'error',
            'message': "Student not found. Please provide a valid student name or roll number."
        }

    def _get_class_info(self, query: str, date_str: str, user_role: str) -> Dict[str, Any]:
        """Get class-specific information"""
        class_name = self._extract_class_name(query)
        if class_name:
            class_obj = self._find_class_by_name(class_name)
            if class_obj:
                return self._get_attendance_info(query, date_str, user_role)
        
        # Return all classes summary
        dept_summary = data_manager.get_department_attendance_summary(date_str)
        return {
            'type': 'all_classes',
            'date': date_str,
            'classes': dept_summary['classes'],
            'message': f"All classes attendance for {date_str}"
        }

    def _get_summary_info(self, query: str, date_str: str, user_role: str) -> Dict[str, Any]:
        """Get summary information"""
        dept_summary = data_manager.get_department_attendance_summary(date_str)
        
        # Get trend data for the past week
        trend_data = []
        for i in range(7):
            check_date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            day_summary = data_manager.get_department_attendance_summary(check_date)
            trend_data.append({
                'date': check_date,
                'percentage': day_summary['overall_percentage']
            })
        
        return {
            'type': 'summary',
            'date': date_str,
            'summary': dept_summary,
            'trend': trend_data,
            'message': f"Department attendance summary for {date_str}"
        }

    def _get_help_info(self, query: str, date_str: str, user_role: str, entities: Dict = None) -> Dict[str, Any]:
        """Get help information"""
        help_commands = [
            "Show attendance for [class name] today",
            "Show latecomers in [class name]",
            "Show student info for [student name/roll]",
            "Show summary for today",
            "Show all classes attendance",
            "Show attendance for yesterday",
            "Show latecomers today",
            "Show analytics for attendance trends",
            "Predict attendance for tomorrow",
            "Compare classes performance",
            "Show insights for this month"
        ]
        
        return {
            'type': 'help',
            'commands': help_commands,
            'message': "Here are some things you can ask me:"
        }

    def _get_default_response(self, query: str, date_str: str) -> Dict[str, Any]:
        """Get default response for unrecognized queries"""
        # Try to provide attendance summary as default
        dept_summary = data_manager.get_department_attendance_summary(date_str)
        return {
            'type': 'default',
            'date': date_str,
            'summary': dept_summary,
            'message': f"Here's the attendance overview for {date_str}. Type 'help' for more options."
        }

    def _extract_class_name(self, query: str) -> str:
        """Extract class name from query"""
        class_keywords = ['2nd year', '3rd year', 'computer science', 'information technology', 
                         'cs', 'it', 'section a', 'section b']
        
        query_lower = query.lower()
        
        # Look for specific class patterns
        if '2nd year' in query_lower and 'computer science' in query_lower:
            if 'section a' in query_lower or ' a' in query_lower:
                return '2nd Year Computer Science A'
            elif 'section b' in query_lower or ' b' in query_lower:
                return '2nd Year Computer Science B'
            return '2nd Year Computer Science A'
        elif '3rd year' in query_lower and 'computer science' in query_lower:
            return '3rd Year Computer Science A'
        elif '2nd year' in query_lower and ('information technology' in query_lower or 'it' in query_lower):
            return '2nd Year Information Technology A'
        elif 'cs' in query_lower and '2' in query_lower:
            if 'b' in query_lower:
                return '2nd Year Computer Science B'
            return '2nd Year Computer Science A'
        elif 'cs' in query_lower and '3' in query_lower:
            return '3rd Year Computer Science A'
        elif 'it' in query_lower and '2' in query_lower:
            return '2nd Year Information Technology A'
        
        return ""

    def _find_class_by_name(self, class_name: str) -> Any:
        """Find class object by partial name match"""
        all_classes = data_manager.get_all_classes()
        class_name_lower = class_name.lower()
        
        for class_obj in all_classes:
            if class_name_lower in class_obj.class_name.lower():
                return class_obj
        
        return None

    def _get_analytics_info(self, query: str, date_str: str, user_role: str, entities: Dict = None) -> Dict[str, Any]:
        """Get advanced analytics and trends"""
        # Get trend data for the past 30 days
        trend_data = []
        for i in range(30):
            check_date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            day_summary = data_manager.get_department_attendance_summary(check_date)
            trend_data.append({
                'date': check_date,
                'percentage': day_summary['overall_percentage'],
                'total_students': day_summary['total_students'],
                'present_students': day_summary['present_students']
            })
        
        # Calculate statistics
        percentages = [day['percentage'] for day in trend_data if day['percentage'] > 0]
        avg_attendance = statistics.mean(percentages) if percentages else 0
        best_day = max(trend_data, key=lambda x: x['percentage'])
        worst_day = min(trend_data, key=lambda x: x['percentage'] if x['percentage'] > 0 else 100)
        
        # Identify patterns
        weekday_patterns = self._analyze_weekday_patterns(trend_data)
        
        return {
            'type': 'analytics',
            'date_range': f"{trend_data[-1]['date']} to {trend_data[0]['date']}",
            'statistics': {
                'average_attendance': round(avg_attendance, 2),
                'best_day': best_day,
                'worst_day': worst_day,
                'trend_direction': self._calculate_trend_direction(percentages[:7])
            },
            'patterns': weekday_patterns,
            'chart_data': trend_data[:14],  # Last 14 days for chart
            'message': "Here's your attendance analytics for the past month"
        }

    def _get_predictions_info(self, query: str, date_str: str, user_role: str, entities: Dict = None) -> Dict[str, Any]:
        """Get attendance predictions using simple algorithms"""
        # Get historical data for prediction
        historical_data = []
        for i in range(14):
            check_date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            day_summary = data_manager.get_department_attendance_summary(check_date)
            if day_summary['overall_percentage'] > 0:
                historical_data.append(day_summary['overall_percentage'])
        
        if len(historical_data) < 3:
            return {
                'type': 'error',
                'message': "Not enough historical data for predictions"
            }
        
        # Simple moving average prediction
        avg_attendance = statistics.mean(historical_data[:7])
        trend = self._calculate_trend_direction(historical_data[:7])
        
        # Predict next few days
        predictions = []
        base_prediction = avg_attendance
        
        for i in range(1, 8):  # Next 7 days
            future_date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
            # Adjust prediction based on trend
            if trend == 'improving':
                predicted = min(100, base_prediction + (i * 2))
            elif trend == 'declining':
                predicted = max(60, base_prediction - (i * 1.5))
            else:
                predicted = base_prediction + ((i % 2) * 3 - 1.5)  # Small variation
            
            predictions.append({
                'date': future_date,
                'predicted_attendance': round(predicted, 1),
                'confidence': max(60, 90 - (i * 5))  # Decreasing confidence over time
            })
        
        return {
            'type': 'predictions',
            'current_trend': trend,
            'historical_average': round(avg_attendance, 2),
            'predictions': predictions,
            'message': f"Attendance predictions based on recent {trend} trend"
        }

    def _get_insights_info(self, query: str, date_str: str, user_role: str, entities: Dict = None) -> Dict[str, Any]:
        """Get intelligent insights about attendance patterns"""
        # Analyze various aspects of attendance data
        insights = []
        
        # Get recent data
        recent_summaries = []
        for i in range(14):
            check_date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            summary = data_manager.get_department_attendance_summary(check_date)
            if summary['overall_percentage'] > 0:
                recent_summaries.append(summary)
        
        if not recent_summaries:
            return {
                'type': 'error',
                'message': "No recent attendance data available for insights"
            }
        
        # Generate insights
        avg_attendance = statistics.mean([s['overall_percentage'] for s in recent_summaries])
        
        if avg_attendance > 90:
            insights.append({
                'type': 'positive',
                'title': 'Excellent Attendance',
                'message': f'Your department maintains excellent attendance at {avg_attendance:.1f}%'
            })
        elif avg_attendance < 75:
            insights.append({
                'type': 'warning',
                'title': 'Low Attendance Alert',
                'message': f'Department attendance is below target at {avg_attendance:.1f}%'
            })
        
        # Identify best performing classes
        best_classes = self._identify_best_performing_classes(date_str)
        if best_classes:
            insights.append({
                'type': 'info',
                'title': 'Top Performing Classes',
                'message': f'Classes with highest attendance: {", ".join(best_classes[:3])}'
            })
        
        # Check for improvement opportunities
        improvement_tips = self._generate_improvement_tips(recent_summaries)
        insights.extend(improvement_tips)
        
        return {
            'type': 'insights',
            'current_average': round(avg_attendance, 2),
            'insights': insights,
            'recommendations': self._generate_recommendations(avg_attendance),
            'message': "Here are intelligent insights based on your attendance data"
        }

    def _get_comparison_info(self, query: str, date_str: str, user_role: str, entities: Dict = None) -> Dict[str, Any]:
        """Get comparative analysis of different aspects"""
        # Compare classes performance
        all_classes = data_manager.get_all_classes()
        class_comparisons = []
        
        for class_obj in all_classes:
            summary = data_manager.get_class_attendance_summary(class_obj.class_id, date_str)
            class_comparisons.append({
                'class_name': class_obj.class_name,
                'attendance_percentage': summary['attendance_percentage'],
                'total_students': summary['total_students'],
                'present_students': summary['present_students'],
                'late_students': summary['late_students']
            })
        
        # Sort by attendance percentage
        class_comparisons.sort(key=lambda x: x['attendance_percentage'], reverse=True)
        
        # Week-over-week comparison
        last_week_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        current_summary = data_manager.get_department_attendance_summary(date_str)
        last_week_summary = data_manager.get_department_attendance_summary(last_week_date)
        
        week_comparison = {
            'current_week': current_summary['overall_percentage'],
            'last_week': last_week_summary['overall_percentage'],
            'change': current_summary['overall_percentage'] - last_week_summary['overall_percentage']
        }
        
        return {
            'type': 'comparison',
            'class_rankings': class_comparisons,
            'week_comparison': week_comparison,
            'top_performer': class_comparisons[0] if class_comparisons else None,
            'needs_attention': class_comparisons[-1] if class_comparisons else None,
            'message': "Here's a comparative analysis of attendance performance"
        }

    # Enhanced NLP helper methods
    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities like dates, class names, student names from query"""
        entities = {}
        
        # Extract date
        entities['date'] = self._extract_date(query)
        
        # Extract class name
        class_name = self._extract_class_name(query)
        if class_name:
            entities['class'] = class_name
            self.conversation_context['last_class'] = class_name
        
        # Extract student name/roll
        student_match = re.search(r'(?:student|for|about)\s+(\w+)', query)
        if student_match:
            entities['student'] = student_match.group(1)
            self.conversation_context['last_student'] = student_match.group(1)
        
        # Extract numbers
        numbers = re.findall(r'\d+', query)
        if numbers:
            entities['numbers'] = [int(n) for n in numbers]
        
        return entities

    def _identify_intent(self, query: str) -> Tuple[str, float]:
        """Identify user intent with confidence score"""
        max_confidence = 0
        best_intent = 'attendance'
        
        for intent, patterns in self.intent_patterns.items():
            confidence = 0
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    confidence = max(confidence, 0.8)
            
            # Keyword-based confidence boost
            intent_keywords = {
                'attendance_query': ['attendance', 'present', 'absent', 'show'],
                'latecomer_query': ['late', 'latecomer', 'tardy'],
                'student_query': ['student', 'info', 'details'],
                'analytics_query': ['analytics', 'trend', 'pattern', 'chart'],
                'prediction_query': ['predict', 'forecast', 'future'],
                'comparison_query': ['compare', 'versus', 'better', 'best']
            }
            
            if intent in intent_keywords:
                keyword_matches = sum(1 for keyword in intent_keywords[intent] if keyword in query)
                confidence += keyword_matches * 0.2
            
            if confidence > max_confidence:
                max_confidence = confidence
                best_intent = intent
        
        return best_intent.replace('_query', ''), min(max_confidence, 1.0)

    def _intent_to_command(self, intent: str) -> str:
        """Map intent to command"""
        intent_command_map = {
            'attendance': 'attendance',
            'latecomer': 'latecomers',
            'student': 'student',
            'analytics': 'analytics',
            'prediction': 'predictions',
            'comparison': 'compare',
            'help': 'help'
        }
        return intent_command_map.get(intent, 'attendance')

    def _is_follow_up_question(self, query: str) -> bool:
        """Check if this is a follow-up question"""
        follow_up_indicators = ['what about', 'how about', 'and', 'also', 'more', 'details', 'explain']
        return any(indicator in query for indicator in follow_up_indicators) and len(self.conversation_context['last_query']) > 0

    def _handle_follow_up(self, query: str, date_str: str, user_role: str) -> Dict[str, Any]:
        """Handle follow-up questions using context"""
        if 'what about' in query or 'how about' in query:
            # Extract the new subject from the follow-up
            new_class = self._extract_class_name(query)
            if new_class:
                return self._get_attendance_info(query, date_str, user_role, {'class': new_class})
        
        # Default to previous context
        if self.conversation_context['last_class']:
            return self._get_attendance_info(f"attendance for {self.conversation_context['last_class']}", date_str, user_role, {})
        
        return self._get_default_response(query, date_str)

    def _generate_suggestions(self, intent: str, entities: Dict, user_role: str) -> List[str]:
        """Generate intelligent suggestions based on current query"""
        suggestions = []
        
        if intent == 'attendance':
            suggestions = [
                "Show latecomers for this class",
                "Compare with other classes",
                "Show attendance trend",
                "Get improvement suggestions"
            ]
        elif intent == 'analytics':
            suggestions = [
                "Predict future attendance",
                "Compare class performance",
                "Show improvement tips",
                "Get weekly trends"
            ]
        elif intent == 'student':
            suggestions = [
                "Show class performance",
                "Compare with peers",
                "Show attendance history",
                "Get improvement plan"
            ]
        
        return suggestions[:3]  # Limit to 3 suggestions

    def _get_intelligent_response(self, query: str, date_str: str, entities: Dict, user_role: str) -> Dict[str, Any]:
        """Generate intelligent response for unrecognized queries"""
        # Try to understand what user wants based on keywords
        if any(word in query for word in ['help', 'what', 'how', 'can']):
            return self._get_help_info(query, date_str, user_role, entities)
        
        # Default to attendance summary with context
        return self._get_default_response(query, date_str)

    # Helper methods for analytics
    def _analyze_weekday_patterns(self, trend_data: List[Dict]) -> Dict[str, Any]:
        """Analyze attendance patterns by weekday"""
        weekday_data = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
        
        for day_data in trend_data:
            try:
                date_obj = datetime.strptime(day_data['date'], '%Y-%m-%d')
                weekday = date_obj.weekday()
                if day_data['percentage'] > 0:
                    weekday_data[weekday].append(day_data['percentage'])
            except:
                continue
        
        weekday_averages = {}
        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day, percentages in weekday_data.items():
            if percentages:
                weekday_averages[weekday_names[day]] = round(statistics.mean(percentages), 2)
        
        best_day = max(weekday_averages.items(), key=lambda x: x[1]) if weekday_averages else ('Monday', 0)
        worst_day = min(weekday_averages.items(), key=lambda x: x[1]) if weekday_averages else ('Monday', 0)
        
        return {
            'averages': weekday_averages,
            'best_day': best_day[0],
            'worst_day': worst_day[0]
        }

    def _calculate_trend_direction(self, recent_percentages: List[float]) -> str:
        """Calculate if attendance is improving, declining, or stable"""
        if len(recent_percentages) < 3:
            return 'stable'
        
        first_half = statistics.mean(recent_percentages[:len(recent_percentages)//2])
        second_half = statistics.mean(recent_percentages[len(recent_percentages)//2:])
        
        difference = second_half - first_half
        
        if difference > 2:
            return 'improving'
        elif difference < -2:
            return 'declining'
        else:
            return 'stable'

    def _identify_best_performing_classes(self, date_str: str) -> List[str]:
        """Identify classes with best attendance"""
        all_classes = data_manager.get_all_classes()
        class_performance = []
        
        for class_obj in all_classes:
            summary = data_manager.get_class_attendance_summary(class_obj.class_id, date_str)
            if summary['attendance_percentage'] > 0:
                class_performance.append((class_obj.class_name, summary['attendance_percentage']))
        
        class_performance.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in class_performance if class_performance[0][1] - _[1] <= 5]  # Top performing within 5%

    def _generate_improvement_tips(self, recent_summaries: List[Dict]) -> List[Dict]:
        """Generate actionable improvement tips"""
        tips = []
        avg_attendance = statistics.mean([s['overall_percentage'] for s in recent_summaries])
        
        if avg_attendance < 85:
            tips.append({
                'type': 'suggestion',
                'title': 'Engagement Strategy',
                'message': 'Consider implementing attendance incentives or morning activities to boost participation'
            })
        
        # Check for consistency
        percentages = [s['overall_percentage'] for s in recent_summaries]
        if statistics.stdev(percentages) > 10:
            tips.append({
                'type': 'warning',
                'title': 'Inconsistent Attendance',
                'message': 'Attendance varies significantly. Review scheduling and communication strategies'
            })
        
        return tips

    def _generate_recommendations(self, avg_attendance: float) -> List[str]:
        """Generate specific recommendations based on attendance levels"""
        if avg_attendance > 90:
            return [
                "Maintain current excellent practices",
                "Consider sharing strategies with other departments",
                "Monitor for any declining trends"
            ]
        elif avg_attendance > 80:
            return [
                "Focus on reducing absenteeism",
                "Implement early intervention for at-risk students",
                "Review scheduling conflicts"
            ]
        else:
            return [
                "Urgent attention needed for attendance improvement",
                "Conduct detailed analysis of absence reasons",
                "Implement comprehensive attendance strategy",
                "Consider additional support for students"
            ]

    # Update existing methods to accept entities parameter
    def _get_attendance_info(self, query: str, date_str: str, user_role: str, entities: Dict = None) -> Dict[str, Any]:
        """Get attendance information"""
        entities = entities or {}
        class_name = entities.get('class') or self._extract_class_name(query)
        
        if class_name:
            # Get specific class attendance
            class_obj = self._find_class_by_name(class_name)
            if class_obj:
                summary = data_manager.get_class_attendance_summary(class_obj.class_id, date_str)
                students = data_manager.get_students_by_class(class_obj.class_id)
                records = data_manager.get_attendance_records(class_obj.class_id, date_str)
                
                student_status = {}
                for student in students:
                    student_status[student.student_id] = {
                        'name': student.name,
                        'roll': student.roll_number,
                        'status': 'absent',
                        'is_late': False
                    }
                
                for record in records:
                    if record.student_id in student_status:
                        student_status[record.student_id]['status'] = record.status
                        student_status[record.student_id]['is_late'] = record.is_late
                
                return {
                    'type': 'class_attendance',
                    'class_name': class_obj.class_name,
                    'date': date_str,
                    'summary': summary,
                    'students': list(student_status.values()),
                    'message': f"Attendance for {class_obj.class_name} on {date_str}"
                }
        
        # Get department-wide attendance
        dept_summary = data_manager.get_department_attendance_summary(date_str)
        return {
            'type': 'department_attendance',
            'date': date_str,
            'summary': dept_summary,
            'message': f"Department attendance summary for {date_str}"
        }

    def _get_latecomer_info(self, query: str, date_str: str, user_role: str, entities: Dict = None) -> Dict[str, Any]:
        """Get latecomer information"""
        entities = entities or {}
        class_name = entities.get('class') or self._extract_class_name(query)
        latecomers = []
        
        if class_name:
            # Get latecomers for specific class
            class_obj = self._find_class_by_name(class_name)
            if class_obj:
                records = data_manager.get_attendance_records(class_obj.class_id, date_str)
                for record in records:
                    if record.is_late and record.status == 'present':
                        student = data_manager.get_student_by_id(record.student_id)
                        if student:
                            latecomers.append({
                                'name': student.name,
                                'roll': student.roll_number,
                                'class': class_obj.class_name,
                                'time': record.created_at
                            })
                
                return {
                    'type': 'class_latecomers',
                    'class_name': class_obj.class_name,
                    'date': date_str,
                    'latecomers': latecomers,
                    'message': f"Latecomers in {class_obj.class_name} on {date_str}"
                }
        
        # Get all latecomers
        all_classes = data_manager.get_all_classes()
        for class_obj in all_classes:
            records = data_manager.get_attendance_records(class_obj.class_id, date_str)
            for record in records:
                if record.is_late and record.status == 'present':
                    student = data_manager.get_student_by_id(record.student_id)
                    if student:
                        latecomers.append({
                            'name': student.name,
                            'roll': student.roll_number,
                            'class': class_obj.class_name,
                            'time': record.created_at
                        })
        
        return {
            'type': 'all_latecomers',
            'date': date_str,
            'latecomers': latecomers,
            'message': f"All latecomers on {date_str}"
        }

    def _get_student_info(self, query: str, date_str: str, user_role: str, entities: Dict = None) -> Dict[str, Any]:
        """Get student-specific information"""
        entities = entities or {}
        # Try to extract student name or roll number from query
        student_query = entities.get('student', "")
        if not student_query:
            words = query.split()
            for word in words:
                if len(word) > 2 and word.isalnum():
                    student_query = word
                    break
        
        if student_query:
            students = data_manager.search_students(student_query)
            if students:
                student = students[0]  # Take the first match
                
                # Get recent attendance history
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                history = data_manager.get_student_attendance_history(student.student_id, start_date, end_date)
                
                # Calculate attendance percentage
                total_days = len(set(record.date for record in history))
                present_days = len(set(record.date for record in history if record.status == 'present'))
                percentage = (present_days / total_days * 100) if total_days > 0 else 0
                
                late_count = sum(1 for record in history if record.is_late)
                
                return {
                    'type': 'student_info',
                    'student': {
                        'name': student.name,
                        'roll': student.roll_number,
                        'class_id': student.class_id
                    },
                    'stats': {
                        'attendance_percentage': percentage,
                        'total_days': total_days,
                        'present_days': present_days,
                        'absent_days': total_days - present_days,
                        'late_count': late_count
                    },
                    'recent_history': [
                        {
                            'date': record.date,
                            'status': record.status,
                            'is_late': record.is_late
                        } for record in history[:10]
                    ],
                    'message': f"Attendance information for {student.name}"
                }
        
        return {
            'type': 'error',
            'message': "Student not found. Please provide a valid student name or roll number."
        }

    def _get_class_info(self, query: str, date_str: str, user_role: str, entities: Dict = None) -> Dict[str, Any]:
        """Get class-specific information"""
        entities = entities or {}
        class_name = entities.get('class') or self._extract_class_name(query)
        if class_name:
            class_obj = self._find_class_by_name(class_name)
            if class_obj:
                return self._get_attendance_info(query, date_str, user_role, entities)
        
        # Return all classes summary
        dept_summary = data_manager.get_department_attendance_summary(date_str)
        return {
            'type': 'all_classes',
            'date': date_str,
            'classes': dept_summary['classes'],
            'message': f"All classes attendance for {date_str}"
        }

    def _get_summary_info(self, query: str, date_str: str, user_role: str, entities: Dict = None) -> Dict[str, Any]:
        """Get summary information"""
        dept_summary = data_manager.get_department_attendance_summary(date_str)
        
        # Get trend data for the past week
        trend_data = []
        for i in range(7):
            check_date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            day_summary = data_manager.get_department_attendance_summary(check_date)
            trend_data.append({
                'date': check_date,
                'percentage': day_summary['overall_percentage']
            })
        
        return {
            'type': 'summary',
            'date': date_str,
            'summary': dept_summary,
            'trend': trend_data,
            'message': f"Department attendance summary for {date_str}"
        }

# Global chatbot instance
chatbot = AttendanceChatbot()
