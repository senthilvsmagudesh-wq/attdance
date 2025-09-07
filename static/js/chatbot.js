/**
 * Chatbot functionality for Department Attendance Management System
 * Handles AI assistant interactions and responses
 */

class AttendanceChatbot {
    constructor() {
        this.isTyping = false;
        this.messageHistory = [];
        this.currentQuery = '';
        
        // Initialize the chatbot
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadWelcomeMessage();
        this.initQuickSuggestions();
    }

    bindEvents() {
        // Chat form submission
        const chatForm = document.getElementById('chatForm');
        if (chatForm) {
            chatForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleUserMessage();
            });
        }

        // Input field events
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleUserMessage();
                }
            });

            messageInput.addEventListener('input', () => {
                this.autoResizeInput();
            });
        }

        // Clear chat button
        const clearChatBtn = document.getElementById('clearChat');
        if (clearChatBtn) {
            clearChatBtn.addEventListener('click', () => {
                this.clearChat();
            });
        }

        // Quick suggestion buttons
        document.querySelectorAll('.suggestion-btn, .quick-action').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const query = e.target.getAttribute('data-query');
                if (query) {
                    this.sendMessage(query);
                }
            });
        });
    }

    loadWelcomeMessage() {
        const welcomeMessage = {
            type: 'bot',
            content: `Hello! I'm your AI assistant for attendance management. I can help you with:
            
• View attendance summaries and reports
• Find specific student information
• Check latecomer records
• Analyze attendance trends
• Generate custom reports

Try asking me something like "Show today's attendance summary" or click on the suggestions below!`,
            timestamp: new Date()
        };

        this.addMessageToChat(welcomeMessage);
    }

    initQuickSuggestions() {
        const suggestions = [
            "Show today's attendance summary",
            "Show all latecomers today",
            "Show students with attendance below 75%",
            "Show CS 2A attendance today",
            "Generate department report",
            "Show perfect attendance classes"
        ];

        this.updateQuickSuggestions(suggestions);
    }

    handleUserMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();

        if (!message) return;

        // Add user message to chat
        this.addMessageToChat({
            type: 'user',
            content: message,
            timestamp: new Date()
        });

        // Clear input
        messageInput.value = '';
        this.autoResizeInput();

        // Send message to chatbot
        this.sendMessage(message);
    }

    async sendMessage(message) {
        this.currentQuery = message;
        
        // Show typing indicator
        this.showTypingIndicator();

        try {
            const response = await fetch('/chatbot-query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: message
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Process and display response
            this.processResponse(data);

        } catch (error) {
            console.error('Chatbot error:', error);
            this.hideTypingIndicator();
            
            this.addMessageToChat({
                type: 'bot',
                content: 'Sorry, I encountered an error while processing your request. Please try again.',
                timestamp: new Date(),
                isError: true
            });
        }
    }

    processResponse(data) {
        let responseContent = '';
        let hasCharts = false;
        let hasTable = false;

        switch (data.type) {
            case 'department_attendance':
                responseContent = this.formatDepartmentResponse(data);
                hasTable = true;
                break;
            case 'class_attendance':
                responseContent = this.formatClassResponse(data);
                hasTable = true;
                break;
            case 'all_latecomers':
            case 'class_latecomers':
                responseContent = this.formatLatecomersResponse(data);
                hasTable = true;
                break;
            case 'student_info':
                responseContent = this.formatStudentResponse(data);
                hasCharts = true;
                break;
            case 'summary':
                responseContent = this.formatSummaryResponse(data);
                hasCharts = true;
                hasTable = true;
                break;
            case 'analytics':
                responseContent = this.formatAnalyticsResponse(data);
                hasCharts = true;
                break;
            case 'predictions':
                responseContent = this.formatPredictionsResponse(data);
                hasCharts = true;
                break;
            case 'insights':
                responseContent = this.formatInsightsResponse(data);
                break;
            case 'comparison':
                responseContent = this.formatComparisonResponse(data);
                hasTable = true;
                hasCharts = true;
                break;
            case 'help':
                responseContent = this.formatHelpResponse(data);
                break;
            case 'error':
                responseContent = data.message;
                break;
            default:
                responseContent = data.message || 'Here\'s what I found for you.';
        }

        // Add bot response to chat
        this.addMessageToChat({
            type: 'bot',
            content: responseContent,
            timestamp: new Date(),
            hasCharts,
            hasTable,
            data: data
        });

        // Update suggestions based on response
        this.updateContextualSuggestions(data.type);
    }

    formatDepartmentResponse(data) {
        const summary = data.summary;
        let response = `**Department Attendance Summary - ${data.date}**\n\n`;
        
        response += `📊 **Overall Statistics:**\n`;
        response += `• Total Students: ${summary.total_students}\n`;
        response += `• Present: ${summary.total_present}\n`;
        response += `• Overall Attendance: ${summary.overall_percentage.toFixed(1)}%\n\n`;

        if (summary.classes && summary.classes.length > 0) {
            response += `📋 **Class-wise Breakdown:**\n`;
            summary.classes.forEach(cls => {
                const status = cls.percentage >= 90 ? '🟢' : cls.percentage >= 75 ? '🟡' : '🔴';
                response += `${status} ${cls.class_name}: ${cls.percentage.toFixed(1)}% (${cls.present}/${cls.total_students})\n`;
            });
        }

        return response;
    }

    formatClassResponse(data) {
        let response = `**${data.class_name} - ${data.date}**\n\n`;
        
        response += `📊 **Class Statistics:**\n`;
        response += `• Total Students: ${data.summary.total_students}\n`;
        response += `• Present: ${data.summary.present}\n`;
        response += `• Absent: ${data.summary.absent}\n`;
        response += `• Late: ${data.summary.late}\n`;
        response += `• Attendance Rate: ${data.summary.percentage.toFixed(1)}%\n\n`;

        if (data.students && data.students.length > 0) {
            const presentStudents = data.students.filter(s => s.status === 'present');
            const absentStudents = data.students.filter(s => s.status === 'absent');
            const lateStudents = data.students.filter(s => s.is_late);

            if (presentStudents.length > 0) {
                response += `✅ **Present Students:**\n`;
                presentStudents.forEach(student => {
                    const lateIndicator = student.is_late ? ' (Late)' : '';
                    response += `• ${student.name}${lateIndicator}\n`;
                });
                response += '\n';
            }

            if (absentStudents.length > 0) {
                response += `❌ **Absent Students:**\n`;
                absentStudents.forEach(student => {
                    response += `• ${student.name}\n`;
                });
            }
        }

        return response;
    }

    formatLatecomersResponse(data) {
        let response = `**Latecomers Report - ${data.date}**\n\n`;

        if (data.latecomers && data.latecomers.length > 0) {
            response += `⏰ **Late Arrivals (${data.latecomers.length}):**\n\n`;
            
            data.latecomers.forEach(student => {
                response += `• **${student.name}** (${student.roll})\n`;
                response += `  Class: ${student.class}\n`;
                if (student.time) {
                    const time = new Date(student.time).toLocaleTimeString();
                    response += `  Time: ${time}\n`;
                }
                response += '\n';
            });
        } else {
            response += `🎉 **Great news!** No latecomers found for ${data.date}.`;
        }

        return response;
    }

    formatStudentResponse(data) {
        const student = data.student;
        const stats = data.stats;
        
        let response = `**Student Profile: ${student.name}**\n\n`;
        response += `🆔 **Details:**\n`;
        response += `• Roll Number: ${student.roll}\n`;
        response += `• Class: ${student.class_id}\n\n`;
        
        response += `📊 **Attendance Statistics:**\n`;
        response += `• Overall Attendance: ${stats.attendance_percentage.toFixed(1)}%\n`;
        response += `• Total Days: ${stats.total_days}\n`;
        response += `• Present Days: ${stats.present_days}\n`;
        response += `• Absent Days: ${stats.absent_days}\n`;
        response += `• Late Arrivals: ${stats.late_count}\n\n`;

        const performanceLevel = stats.attendance_percentage >= 90 ? 'Excellent 🌟' :
                                stats.attendance_percentage >= 75 ? 'Good 👍' :
                                stats.attendance_percentage >= 60 ? 'Average 📊' : 'Needs Improvement 📈';
        
        response += `🎯 **Performance Level:** ${performanceLevel}\n\n`;

        if (data.recent_history && data.recent_history.length > 0) {
            response += `📅 **Recent Attendance:**\n`;
            data.recent_history.slice(0, 5).forEach(record => {
                const status = record.status === 'present' ? 
                              (record.is_late ? '🟡 Present (Late)' : '✅ Present') : '❌ Absent';
                response += `• ${record.date}: ${status}\n`;
            });
        }

        return response;
    }

    formatSummaryResponse(data) {
        const summary = data.summary;
        let response = `**Department Summary - ${data.date}**\n\n`;
        
        response += `📊 **Key Metrics:**\n`;
        response += `• Overall Attendance: ${summary.overall_percentage.toFixed(1)}%\n`;
        response += `• Total Students: ${summary.total_students}\n`;
        response += `• Present Today: ${summary.total_present}\n`;
        response += `• Active Classes: ${summary.classes.length}\n\n`;

        if (data.trend && data.trend.length > 0) {
            response += `📈 **7-Day Trend:**\n`;
            data.trend.slice(-3).forEach(day => {
                const trend = day.percentage >= 80 ? '📈' : day.percentage >= 60 ? '📊' : '📉';
                response += `${trend} ${day.date}: ${day.percentage.toFixed(1)}%\n`;
            });
        }

        // Highlight classes needing attention
        const lowAttendance = summary.classes.filter(cls => cls.percentage < 75);
        if (lowAttendance.length > 0) {
            response += `\n⚠️ **Classes Needing Attention:**\n`;
            lowAttendance.forEach(cls => {
                response += `• ${cls.class_name}: ${cls.percentage.toFixed(1)}%\n`;
            });
        }

        return response;
    }

    formatHelpResponse(data) {
        let response = `**How to Use the AI Assistant**\n\n`;
        response += `I can help you with various attendance-related queries. Here are some examples:\n\n`;

        if (data.commands && data.commands.length > 0) {
            response += `💡 **Sample Questions:**\n`;
            data.commands.forEach(cmd => {
                response += `• "${cmd}"\n`;
            });
        }

        response += `\n🔍 **Tips:**\n`;
        response += `• Be specific with class names and dates\n`;
        response += `• Use "today" or "yesterday" for recent data\n`;
        response += `• Ask for help anytime by typing "help"\n`;
        response += `• I can generate reports and export data\n\n`;

        response += `📝 **Report Types:**\n`;
        response += `• Daily attendance summaries\n`;
        response += `• Student performance analysis\n`;
        response += `• Latecomer tracking\n`;
        response += `• Trend analysis\n`;

        return response;
    }

    formatAnalyticsResponse(data) {
        let response = `**📊 Attendance Analytics Report**\n\n`;
        
        if (data.statistics) {
            response += `**📈 Key Statistics:**\n`;
            response += `• Average Attendance: ${data.statistics.average_attendance}%\n`;
            response += `• Trend Direction: ${data.statistics.trend_direction.charAt(0).toUpperCase() + data.statistics.trend_direction.slice(1)} 📊\n`;
            
            if (data.statistics.best_day) {
                response += `• Best Day: ${data.statistics.best_day.date} (${data.statistics.best_day.percentage.toFixed(1)}%) 🌟\n`;
            }
            if (data.statistics.worst_day) {
                response += `• Needs Focus: ${data.statistics.worst_day.date} (${data.statistics.worst_day.percentage.toFixed(1)}%) 📉\n`;
            }
        }
        
        if (data.patterns) {
            response += `\n**📅 Weekly Patterns:**\n`;
            response += `• Best Day: ${data.patterns.best_day}\n`;
            response += `• Most Challenging: ${data.patterns.worst_day}\n`;
        }
        
        response += `\n📊 **Chart:** Showing attendance trends over the past 2 weeks\n`;
        response += `📁 **Period:** ${data.date_range}`;
        
        return response;
    }

    formatPredictionsResponse(data) {
        let response = `**🔮 Attendance Predictions**\n\n`;
        
        response += `**📊 Current Trend:** ${data.current_trend.charAt(0).toUpperCase() + data.current_trend.slice(1)}\n`;
        response += `**📈 Historical Average:** ${data.historical_average}%\n\n`;
        
        if (data.predictions && data.predictions.length > 0) {
            response += `**🗓️ Next 7 Days Forecast:**\n`;
            data.predictions.slice(0, 5).forEach(prediction => {
                const confidence = prediction.confidence;
                const confidenceIcon = confidence > 80 ? '🟢' : confidence > 60 ? '🟡' : '🔴';
                response += `${confidenceIcon} ${prediction.date}: ${prediction.predicted_attendance}% (${confidence}% confidence)\n`;
            });
        }
        
        response += `\n**💡 Prediction Note:** Based on recent ${data.current_trend} trend patterns`;
        
        return response;
    }

    formatInsightsResponse(data) {
        let response = `**💡 Smart Attendance Insights**\n\n`;
        
        response += `**📊 Current Performance:** ${data.current_average}% average attendance\n\n`;
        
        if (data.insights && data.insights.length > 0) {
            response += `**🔍 Key Insights:**\n`;
            data.insights.forEach(insight => {
                const icon = insight.type === 'positive' ? '✅' : 
                           insight.type === 'warning' ? '⚠️' : 'ℹ️';
                response += `${icon} **${insight.title}:** ${insight.message}\n`;
            });
        }
        
        if (data.recommendations && data.recommendations.length > 0) {
            response += `\n**📝 Recommendations:**\n`;
            data.recommendations.forEach(rec => {
                response += `• ${rec}\n`;
            });
        }
        
        return response;
    }

    formatComparisonResponse(data) {
        let response = `**🆚 Comparative Analysis**\n\n`;
        
        if (data.week_comparison) {
            const change = data.week_comparison.change;
            const changeIcon = change > 0 ? '📈' : change < 0 ? '📉' : '➖';
            response += `**📊 Week-over-Week:**\n`;
            response += `• This Week: ${data.week_comparison.current_week.toFixed(1)}%\n`;
            response += `• Last Week: ${data.week_comparison.last_week.toFixed(1)}%\n`;
            response += `• Change: ${changeIcon} ${change.toFixed(1)} percentage points\n\n`;
        }
        
        if (data.top_performer) {
            response += `**🏆 Top Performer:**\n`;
            response += `${data.top_performer.class_name}: ${data.top_performer.attendance_percentage.toFixed(1)}%\n\n`;
        }
        
        if (data.needs_attention) {
            response += `**⚠️ Needs Attention:**\n`;
            response += `${data.needs_attention.class_name}: ${data.needs_attention.attendance_percentage.toFixed(1)}%\n\n`;
        }
        
        response += `**📋 See table below for complete class rankings**`;
        
        return response;
    }

    addMessageToChat(message) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.type}-message`;

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.innerHTML = message.type === 'bot' ? 
            '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        
        // Process markdown-like formatting
        const formattedContent = this.formatMessageContent(message.content);
        textDiv.innerHTML = formattedContent;

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.innerHTML = `<small class="text-muted">${message.timestamp.toLocaleTimeString()}</small>`;

        contentDiv.appendChild(textDiv);
        contentDiv.appendChild(timeDiv);

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        // Add interactive elements if needed
        if (message.hasTable && message.data) {
            const tableDiv = this.createInteractiveTable(message.data);
            if (tableDiv) {
                contentDiv.appendChild(tableDiv);
            }
        }

        if (message.hasCharts && message.data) {
            const chartDiv = this.createMiniChart(message.data);
            if (chartDiv) {
                contentDiv.appendChild(chartDiv);
            }
        }

        // Add export buttons if relevant
        if (message.data && (message.hasTable || message.hasCharts)) {
            const actionsDiv = this.createMessageActions(message.data);
            contentDiv.appendChild(actionsDiv);
        }

        chatMessages.appendChild(messageDiv);
        this.scrollToBottom();

        // Add to history
        this.messageHistory.push(message);
    }

    formatMessageContent(content) {
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/^• /gm, '<li>')
            .replace(/\n• /g, '</li>\n<li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
            .replace(/\n\n/g, '<br><br>')
            .replace(/\n/g, '<br>');
    }

    createInteractiveTable(data) {
        if (!data.summary || !data.summary.classes) return null;

        const tableDiv = document.createElement('div');
        tableDiv.className = 'table-responsive mt-3';

        const table = document.createElement('table');
        table.className = 'table table-sm table-striped';

        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th>Class</th>
                <th>Present</th>
                <th>Absent</th>
                <th>Attendance %</th>
            </tr>
        `;

        const tbody = document.createElement('tbody');
        data.summary.classes.forEach(cls => {
            const row = document.createElement('tr');
            const percentage = cls.percentage || 0;
            const statusClass = percentage >= 90 ? 'table-success' : 
                              percentage >= 75 ? 'table-warning' : 'table-danger';
            row.className = statusClass;
            
            row.innerHTML = `
                <td>${cls.class_name}</td>
                <td><span class="badge bg-success">${cls.present}</span></td>
                <td><span class="badge bg-danger">${cls.absent}</span></td>
                <td><strong>${percentage.toFixed(1)}%</strong></td>
            `;
            tbody.appendChild(row);
        });

        table.appendChild(thead);
        table.appendChild(tbody);
        tableDiv.appendChild(table);

        return tableDiv;
    }

    createMiniChart(data) {
        if (!data.summary) return null;

        const chartDiv = document.createElement('div');
        chartDiv.className = 'mini-chart mt-3';
        chartDiv.style.height = '200px';

        const canvas = document.createElement('canvas');
        const chartId = `mini-chart-${Date.now()}`;
        canvas.id = chartId;

        chartDiv.appendChild(canvas);

        // Create the chart after DOM insertion
        setTimeout(() => {
            if (data.type === 'department_attendance' && data.summary.classes) {
                const ctx = canvas.getContext('2d');
                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Present', 'Absent'],
                        datasets: [{
                            data: [data.summary.total_present, data.summary.total_students - data.summary.total_present],
                            backgroundColor: ['#198754', '#dc3545'],
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            }
                        }
                    }
                });
            }
        }, 100);

        return chartDiv;
    }

    createMessageActions(data) {
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'message-actions mt-2';

        const exportBtn = document.createElement('button');
        exportBtn.className = 'btn btn-outline-primary btn-sm me-2';
        exportBtn.innerHTML = '<i class="fas fa-download me-1"></i>Export';
        exportBtn.addEventListener('click', () => {
            this.exportData(data);
        });

        const shareBtn = document.createElement('button');
        shareBtn.className = 'btn btn-outline-secondary btn-sm';
        shareBtn.innerHTML = '<i class="fas fa-share me-1"></i>Share';
        shareBtn.addEventListener('click', () => {
            this.shareData(data);
        });

        actionsDiv.appendChild(exportBtn);
        actionsDiv.appendChild(shareBtn);

        return actionsDiv;
    }

    showTypingIndicator() {
        if (this.isTyping) return;
        this.isTyping = true;

        const chatMessages = document.getElementById('chatMessages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot-message typing-indicator';
        typingDiv.id = 'typing-indicator';

        typingDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-text">
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `;

        chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.isTyping = false;
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    autoResizeInput() {
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.style.height = 'auto';
            messageInput.style.height = (messageInput.scrollHeight) + 'px';
        }
    }

    scrollToBottom() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    clearChat() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = '';
            this.messageHistory = [];
            this.loadWelcomeMessage();
            AttendanceApp.utils.showToast('Chat cleared', 'info');
        }
    }

    updateQuickSuggestions(suggestions) {
        const suggestionsContainer = document.getElementById('quickSuggestions');
        if (!suggestionsContainer) return;

        suggestionsContainer.innerHTML = '';
        suggestions.forEach(suggestion => {
            const col = document.createElement('div');
            col.className = 'col-lg-3 col-md-6 mb-2';

            const button = document.createElement('button');
            button.className = 'btn btn-outline-primary btn-sm w-100 suggestion-btn';
            button.setAttribute('data-query', suggestion);
            button.innerHTML = `<i class="fas fa-lightbulb me-1"></i>${suggestion}`;
            
            button.addEventListener('click', (e) => {
                this.sendMessage(suggestion);
            });

            col.appendChild(button);
            suggestionsContainer.appendChild(col);
        });
    }

    updateContextualSuggestions(responseType) {
        let suggestions = [];

        switch (responseType) {
            case 'department_attendance':
                suggestions = [
                    "Show latecomers today",
                    "Show classes with low attendance",
                    "Generate detailed report",
                    "Show yesterday's comparison"
                ];
                break;
            case 'class_attendance':
                suggestions = [
                    "Show this class's weekly trend",
                    "Show latecomers in this class",
                    "Compare with other classes",
                    "Show absent students details"
                ];
                break;
            case 'student_info':
                suggestions = [
                    "Show class average",
                    "Show similar performing students",
                    "Generate student report",
                    "Show monthly trend"
                ];
                break;
            default:
                suggestions = [
                    "Show today's summary",
                    "Show department overview",
                    "Help",
                    "Show reports menu"
                ];
        }

        this.updateQuickSuggestions(suggestions);
    }

    exportData(data) {
        // Convert data to CSV format
        let csvContent = '';
        
        if (data.summary && data.summary.classes) {
            csvContent = 'Class Name,Total Students,Present,Absent,Attendance %\n';
            data.summary.classes.forEach(cls => {
                csvContent += `"${cls.class_name}",${cls.total_students},${cls.present},${cls.absent},${cls.percentage.toFixed(1)}\n`;
            });
        } else if (data.latecomers) {
            csvContent = 'Student Name,Roll Number,Class,Time\n';
            data.latecomers.forEach(student => {
                csvContent += `"${student.name}","${student.roll}","${student.class}","${student.time || 'N/A'}"\n`;
            });
        }

        if (csvContent) {
            const blob = new Blob([csvContent], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `attendance_data_${new Date().toISOString().split('T')[0]}.csv`;
            link.click();
            window.URL.revokeObjectURL(url);
            
            AttendanceApp.utils.showToast('Data exported successfully!', 'success');
        }
    }

    shareData(data) {
        const shareText = `Attendance Data - ${data.date || 'Today'}\n\nGenerated by Department Attendance Management System`;
        
        if (navigator.share) {
            navigator.share({
                title: 'Attendance Report',
                text: shareText,
                url: window.location.href
            });
        } else {
            // Fallback to copying to clipboard
            AttendanceApp.utils.copyToClipboard(shareText);
        }
    }
}

// CSS for typing indicator
const typingCSS = `
    .typing-dots {
        display: inline-block;
        position: relative;
        width: 60px;
        height: 20px;
    }
    .typing-dots span {
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #999;
        animation: typing 1.4s infinite both;
        margin-right: 4px;
    }
    .typing-dots span:nth-child(1) {
        animation-delay: 0s;
    }
    .typing-dots span:nth-child(2) {
        animation-delay: 0.2s;
    }
    .typing-dots span:nth-child(3) {
        animation-delay: 0.4s;
    }
    @keyframes typing {
        0%, 80%, 100% {
            transform: scale(0.8);
            opacity: 0.5;
        }
        40% {
            transform: scale(1);
            opacity: 1;
        }
    }
    .mini-chart {
        background: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-top: 1rem;
    }
    .message-actions {
        border-top: 1px solid #e9ecef;
        padding-top: 0.5rem;
    }
`;

// Inject CSS
const style = document.createElement('style');
style.textContent = typingCSS;
document.head.appendChild(style);

// Export the class
window.AttendanceChatbot = AttendanceChatbot;
