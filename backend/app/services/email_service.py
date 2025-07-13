"""
Email service for sending daily progress and motivational emails.

This module handles sending personalized daily emails to users with
progress updates, motivational messages, and task reminders.

Author: Thesis Helper Team
Date: 2024
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from datetime import datetime, date
import json

from backend.app.core.config import settings, get_email_config
from backend.app.models.schemas import DailyEmailContent


class EmailService:
    """
    Service class for handling email communications.
    
    This class manages daily email generation and delivery using Gmail SMTP.
    """
    
    def __init__(self):
        """Initialize the email service with Gmail SMTP configuration."""
        self.config = get_email_config()
        self.smtp_server = self.config["host"]
        self.smtp_port = self.config["port"]
        self.username = self.config["username"]
        self.password = self.config["password"]
        self.use_tls = self.config["use_tls"]
    
    def send_daily_progress_email(self, user_email: str, user_name: str, 
                                 progress_data: Dict, tasks_today: List[str]) -> bool:
        """
        Send daily progress and motivational email to user.
        
        Args:
            user_email: User's email address
            user_name: User's name
            progress_data: Dictionary containing progress information
            tasks_today: List of today's tasks
            
        Returns:
            bool: True if email was sent successfully
        """
        try:
            # Generate email content
            email_content = self._generate_email_content(user_name, progress_data, tasks_today)
            
            # Create email message
            message = self._create_email_message(
                to_email=user_email,
                subject=email_content.subject,
                html_content=self._create_html_email(email_content)
            )
            
            # Send email
            return self._send_email(message)
            
        except Exception as e:
            print(f"Failed to send daily email to {user_email}: {str(e)}")
            return False
    
    def _generate_email_content(self, user_name: str, progress_data: Dict, 
                               tasks_today: List[str]) -> DailyEmailContent:
        """Generate personalized email content based on user progress."""
        
        # Calculate progress metrics
        completion_rate = progress_data.get("completion_rate", 0.0)
        tasks_completed = progress_data.get("tasks_completed", 0)
        tasks_planned = progress_data.get("tasks_planned", 0)
        streak_days = progress_data.get("streak_days", 0)
        days_ahead_behind = progress_data.get("days_ahead_behind", 0)
        
        # Generate subject line
        if days_ahead_behind > 0:
            subject = f"Day {progress_data.get('day_number', 1)} - You're {days_ahead_behind} days ahead! 🎉"
        elif days_ahead_behind < 0:
            subject = f"Day {progress_data.get('day_number', 1)} - Let's catch up! 💪"
        else:
            subject = f"Day {progress_data.get('day_number', 1)} - Right on track! 🎯"
        
        # Generate greeting
        greeting = self._get_time_based_greeting(user_name)
        
        # Generate progress summary
        progress_summary = self._generate_progress_summary(
            tasks_completed, tasks_planned, completion_rate
        )
        
        # Generate motivational message
        motivational_message = self._generate_motivational_message(
            completion_rate, days_ahead_behind, streak_days
        )
        
        # Generate streak info
        streak_info = self._generate_streak_info(streak_days)
        
        # Generate overall status
        overall_status = self._generate_overall_status(days_ahead_behind, completion_rate)
        
        return DailyEmailContent(
            subject=subject,
            greeting=greeting,
            progress_summary=progress_summary,
            today_tasks=tasks_today,
            motivational_message=motivational_message,
            streak_info=streak_info,
            overall_status=overall_status
        )
    
    def _get_time_based_greeting(self, user_name: str) -> str:
        """Generate time-based greeting."""
        current_hour = datetime.now().hour
        
        if current_hour < 12:
            return f"Good morning, {user_name}! ☀️"
        elif current_hour < 17:
            return f"Good afternoon, {user_name}! 🌤️"
        else:
            return f"Good evening, {user_name}! 🌅"
    
    def _generate_progress_summary(self, tasks_completed: int, tasks_planned: int, 
                                  completion_rate: float) -> str:
        """Generate progress summary text."""
        if tasks_planned == 0:
            return "No tasks were planned for yesterday."
        
        completion_percentage = int(completion_rate * 100)
        
        if completion_rate >= 0.8:
            return f"✅ Excellent work! You completed {tasks_completed}/{tasks_planned} tasks ({completion_percentage}%)"
        elif completion_rate >= 0.6:
            return f"👍 Good progress! You completed {tasks_completed}/{tasks_planned} tasks ({completion_percentage}%)"
        elif completion_rate >= 0.4:
            return f"📈 You're making progress! Completed {tasks_completed}/{tasks_planned} tasks ({completion_percentage}%)"
        else:
            return f"🎯 Let's improve today! You completed {tasks_completed}/{tasks_planned} tasks ({completion_percentage}%)"
    
    def _generate_motivational_message(self, completion_rate: float, 
                                     days_ahead_behind: int, streak_days: int) -> str:
        """Generate personalized motivational message."""
        
        messages = {
            "ahead_high_completion": [
                "You're absolutely crushing it! Your consistency is paying off, and you're building incredible momentum toward your thesis completion.",
                "Fantastic work! You're not just meeting expectations, you're exceeding them. This dedication will make all the difference in your final thesis quality.",
                "Amazing progress! You're proving to yourself that you can achieve anything you set your mind to. Keep this energy going!"
            ],
            "ahead_medium_completion": [
                "Great job staying ahead of schedule! Even though you didn't complete everything yesterday, you're still in a strong position.",
                "You're doing well overall! Being ahead gives you the flexibility to have occasional lighter days. Keep up the good work!",
                "Solid progress! You're ahead of schedule, which is exactly where you want to be. Every step forward counts."
            ],
            "on_track_high_completion": [
                "Perfect! You're right on track and completing your tasks efficiently. This is exactly the kind of consistency that leads to success.",
                "Excellent work! You're maintaining the perfect balance between progress and pace. Your future self will thank you!",
                "You're doing everything right! Staying on track with high completion rates is the formula for thesis success."
            ],
            "on_track_medium_completion": [
                "You're on the right path! While there's room for improvement, you're maintaining good momentum toward your deadline.",
                "Keep going! You're on track overall, and every completed task brings you closer to your thesis goal.",
                "Good work! You're maintaining steady progress. Consider what might help you complete more tasks tomorrow."
            ],
            "behind_any_completion": [
                "Don't worry - everyone faces challenges! What matters is that you're still working toward your goal. Today is a new opportunity to make progress.",
                "You're stronger than you think! Falling behind doesn't define your journey. Focus on what you can control today and take it one task at a time.",
                "This is temporary! Every thesis journey has ups and downs. Your persistence will pay off, and you'll get back on track."
            ],
            "long_streak": [
                "Incredible streak! You've built an amazing habit that's carrying you toward success. This consistency is your superpower!",
                "Your dedication is inspiring! This streak shows you have what it takes to complete your thesis with excellence.",
                "Amazing commitment! You're proving that small, consistent actions lead to big achievements."
            ]
        }
        
        # Determine message category
        if days_ahead_behind > 0:
            if completion_rate >= 0.7:
                category = "ahead_high_completion"
            else:
                category = "ahead_medium_completion"
        elif days_ahead_behind == 0:
            if completion_rate >= 0.7:
                category = "on_track_high_completion"
            else:
                category = "on_track_medium_completion"
        else:
            category = "behind_any_completion"
        
        # Override with streak message if applicable
        if streak_days >= 7:
            category = "long_streak"
        
        # Select random message from category
        import random
        return random.choice(messages[category])
    
    def _generate_streak_info(self, streak_days: int) -> str:
        """Generate streak information text."""
        if streak_days == 0:
            return "🔥 Start a new streak today! Complete your planned tasks to begin building momentum."
        elif streak_days == 1:
            return "🔥 1 day streak! You're off to a great start - keep it going!"
        elif streak_days < 7:
            return f"🔥 {streak_days} day streak! You're building great momentum!"
        elif streak_days < 14:
            return f"🔥 {streak_days} day streak! You're on fire! This consistency is amazing!"
        else:
            return f"🔥 {streak_days} day streak! You're a thesis productivity machine! Incredible dedication!"
    
    def _generate_overall_status(self, days_ahead_behind: int, completion_rate: float) -> str:
        """Generate overall status message."""
        if days_ahead_behind > 2:
            return "🎉 You're significantly ahead of schedule! This gives you great flexibility for the final stretch."
        elif days_ahead_behind > 0:
            return "✅ You're ahead of schedule! Keep up this excellent pace."
        elif days_ahead_behind == 0:
            return "🎯 You're right on track! Perfect pacing for your thesis completion."
        elif days_ahead_behind > -3:
            return "⚠️ You're slightly behind schedule, but nothing that can't be caught up with focused effort."
        else:
            return "🚨 You're behind schedule. Consider using the emergency replan feature to adjust your timeline."
    
    def _create_html_email(self, content: DailyEmailContent) -> str:
        """Create HTML email from content."""
        
        tasks_html = ""
        for i, task in enumerate(content.today_tasks, 1):
            tasks_html += f"<li style='margin-bottom: 8px;'>{task}</li>"
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Daily Thesis Progress</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
                <h1 style="margin: 0; font-size: 24px;">📚 Thesis Helper Daily Update</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">{datetime.now().strftime('%A, %B %d, %Y')}</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h2 style="color: #2c3e50; margin-top: 0;">{content.greeting}</h2>
                <p style="font-size: 16px; margin-bottom: 0;">{content.progress_summary}</p>
            </div>
            
            <div style="background: #fff; border: 1px solid #e0e0e0; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="color: #2c3e50; margin-top: 0;">🎯 Today's Mission:</h3>
                <ul style="padding-left: 20px;">
                    {tasks_html}
                </ul>
            </div>
            
            <div style="background: #e8f5e8; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="color: #2c3e50; margin-top: 0;">💪 Motivation Boost:</h3>
                <p style="font-size: 16px; font-style: italic; margin-bottom: 10px;">"{content.motivational_message}"</p>
                <p style="font-size: 14px; margin-bottom: 0;">{content.streak_info}</p>
            </div>
            
            <div style="background: #f0f8ff; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="color: #2c3e50; margin-top: 0;">📊 Overall Status:</h3>
                <p style="font-size: 16px; margin-bottom: 0;">{content.overall_status}</p>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
                <p style="font-size: 14px; color: #666;">
                    Keep pushing forward! Every step brings you closer to your thesis completion.
                </p>
                <p style="font-size: 12px; color: #999; margin-top: 10px;">
                    This email was sent by your Thesis Helper AI assistant.
                </p>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _create_email_message(self, to_email: str, subject: str, html_content: str) -> MIMEMultipart:
        """Create email message with HTML content."""
        
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"Thesis Helper <{self.username}>"
        message["To"] = to_email
        
        # Create HTML part
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        return message
    
    def _send_email(self, message: MIMEMultipart) -> bool:
        """Send email using Gmail SMTP."""
        try:
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect to Gmail SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                
                # Send email
                server.send_message(message)
                
            return True
            
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False
    
    def send_emergency_replan_notification(self, user_email: str, user_name: str, 
                                         reason: str, adjustments: List[str]) -> bool:
        """
        Send emergency replan notification email.
        
        Args:
            user_email: User's email address
            user_name: User's name
            reason: Reason for emergency replan
            adjustments: List of adjustments made
            
        Returns:
            bool: True if email was sent successfully
        """
        try:
            subject = "🚨 Emergency Timeline Replan - Action Required"
            
            adjustments_html = ""
            for adjustment in adjustments:
                adjustments_html += f"<li>{adjustment}</li>"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #e74c3c;">🚨 Emergency Timeline Replan</h2>
                <p>Hi {user_name},</p>
                <p>Your timeline has been automatically adjusted due to: <strong>{reason}</strong></p>
                
                <h3>Adjustments Made:</h3>
                <ul>
                    {adjustments_html}
                </ul>
                
                <p><strong>Next Steps:</strong></p>
                <ol>
                    <li>Review your updated timeline in the app</li>
                    <li>Focus on the highest priority tasks</li>
                    <li>Consider if any additional adjustments are needed</li>
                </ol>
                
                <p>Remember: setbacks are normal in thesis writing. What matters is how you respond!</p>
                
                <p>Best regards,<br>Your Thesis Helper AI</p>
            </body>
            </html>
            """
            
            message = self._create_email_message(user_email, subject, html_content)
            return self._send_email(message)
            
        except Exception as e:
            print(f"Failed to send emergency replan email: {str(e)}")
            return False


def test_email_connection() -> bool:
    """
    Test email service connection.
    
    Returns:
        bool: True if connection is successful
    """
    try:
        config = get_email_config()
        context = ssl.create_default_context()
        
        with smtplib.SMTP(config["host"], config["port"]) as server:
            server.starttls(context=context)
            server.login(config["username"], config["password"])
            
        return True
    except Exception:
        return False


# Global email service instance
email_service = EmailService() 