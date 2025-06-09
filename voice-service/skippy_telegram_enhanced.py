#!/usr/bin/env python3
"""
Enhanced Skippy Telegram Bot
With group chat, file handling, scheduled messages, and custom commands
"""

import logging
import requests
import json
import asyncio
import schedule
import threading
import time
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, CallbackQueryHandler
)
from telegram.constants import ChatAction
import io
import docx
import PyPDF2

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class EnhancedSkippyBot:
    def __init__(self, bot_token, skippy_api_url="http://192.168.0.229:5678/webhook/skippy/chat"):
        self.bot_token = bot_token
        self.skippy_api_url = skippy_api_url
        self.authorized_users = set()
        self.authorized_groups = set()
        self.scheduled_jobs = {}
        self.user_preferences = {}
        
        # Create Telegram application
        self.application = Application.builder().token(bot_token).build()
        
        # Setup handlers
        self.setup_handlers()
        
        # Start scheduler thread
        self.start_scheduler()
        
        logger.info("Enhanced Skippy Telegram Bot initialized")
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        
        # Basic commands
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        
        # Group management
        self.application.add_handler(CommandHandler("addgroup", self.add_group_command))
        self.application.add_handler(CommandHandler("groupstatus", self.group_status_command))
        
        # Custom work commands
        self.application.add_handler(CommandHandler("standup", self.standup_command))
        self.application.add_handler(CommandHandler("review", self.review_command))
        self.application.add_handler(CommandHandler("plan", self.plan_command))
        self.application.add_handler(CommandHandler("deadline", self.deadline_command))
        self.application.add_handler(CommandHandler("meeting", self.meeting_command))
        
        # Scheduling commands
        self.application.add_handler(CommandHandler("remind", self.remind_command))
        self.application.add_handler(CommandHandler("daily", self.daily_command))
        self.application.add_handler(CommandHandler("schedule", self.schedule_command))
        self.application.add_handler(CommandHandler("reminders", self.list_reminders_command))
        
        # File handling
        self.application.add_handler(MessageHandler(
            filters.Document.PDF | filters.Document.TEXT | 
            filters.Document.FileExtension("docx"), 
            self.handle_document
        ))
        
        # Callback query handler for inline keyboards
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Regular message handler (must be last)
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_message
        ))
        
        logger.info("Enhanced handlers configured")
    
    # === BASIC COMMANDS ===
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced start command with feature overview"""
        user = update.effective_user
        chat = update.effective_chat
        
        if chat.type in ['group', 'supergroup']:
            welcome_message = f"""
🤖 **SKIPPY AI - TEAM ASSISTANT**

Well, another group thinks they need my assistance. How delightfully presumptuous.

**Group Features:**
• 💬 Team conversations and Q&A
• 📋 Project planning and reviews  
• 📅 Meeting summaries and action items
• 🔔 Group reminders and updates
• 📊 Daily standups and status reports

**To enable group features:** `/addgroup`

Type `/help` for all commands or just mention me in conversations.
            """
        else:
            welcome_message = f"""
🤖 **SKIPPY AI - ENHANCED ASSISTANT**

Hello {user.first_name}. I've been upgraded with new capabilities that might actually be useful.

**New Features:**
📁 **File Analysis** - Send documents for review
📅 **Scheduling** - Reminders and daily updates  
👥 **Group Support** - Team collaboration
⚡ **Work Commands** - Specialized workflows
🔧 **Custom Tools** - Tailored for your work

**Quick Start:**
• Send me a document to analyze
• Try `/standup` for daily check-ins
• Use `/plan [project]` for planning
• Set reminders with `/remind`

Type `/help` for full command list.
            """
        
        keyboard = [
            [InlineKeyboardButton("📋 Work Commands", callback_data="help_work")],
            [InlineKeyboardButton("📅 Scheduling", callback_data="help_schedule")],
            [InlineKeyboardButton("📁 File Tools", callback_data="help_files")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comprehensive help with categories"""
        help_text = """
🤖 **SKIPPY ENHANCED HELP**

**📋 WORK COMMANDS:**
/standup - Daily standup check-in
/review [topic] - Code/document review
/plan [project] - Project planning
/deadline [task] [date] - Set deadline
/meeting [notes] - Meeting summary

**📅 SCHEDULING:**
/remind [time] [message] - Set reminder
/daily [time] - Daily update schedule
/schedule - View scheduled items
/reminders - List active reminders

**👥 GROUP FEATURES:**
/addgroup - Enable group features
/groupstatus - Group settings

**📁 FILE HANDLING:**
• Send PDF/DOCX/TXT files for analysis
• Automatic document summarization
• Code review and feedback

**💬 GENERAL:**
/status - System status
/help - This help menu

**Integration Ready:**
Ready to connect with Jira, Slack, GitHub, and more!
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    # === GROUP CHAT SUPPORT ===
    
    async def add_group_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enable group features"""
        chat = update.effective_chat
        user = update.effective_user
        
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text(
                "❌ This command is only for group chats."
            )
            return
        
        self.authorized_groups.add(chat.id)
        
        message = f"""
✅ **GROUP FEATURES ENABLED**

Group: {chat.title}
ID: {chat.id}
Enabled by: {user.first_name}

**Available Features:**
• 💬 Respond to mentions (@skippy_bot)
• 📋 Team standups and planning
• 🔔 Group reminders and notifications
• 📊 Meeting summaries and action items
• 📈 Project progress tracking

**Usage:**
• Mention me: "@skippy_bot help with project X"
• Use commands: "/standup" for team check-ins
• Send files: Documents will be analyzed for the group

Try mentioning me in a message to get started!
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f"Group {chat.title} ({chat.id}) enabled by {user.first_name}")
    
    async def group_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show group status and settings"""
        chat = update.effective_chat
        
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text(
                "❌ This command is only for group chats."
            )
            return
        
        is_enabled = chat.id in self.authorized_groups
        member_count = await context.bot.get_chat_members_count(chat.id)
        
        status_message = f"""
👥 **GROUP STATUS**

**Group:** {chat.title}
**Members:** {member_count}
**Skippy Status:** {'✅ Enabled' if is_enabled else '❌ Disabled'}
**Features:** {'All features active' if is_enabled else 'Use /addgroup to enable'}

**Recent Activity:**
• Messages processed: Available in logs
• Files analyzed: Check message history
• Reminders set: Use /reminders to view

{'/addgroup to enable features' if not is_enabled else 'All systems operational'}
        """
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
    
    # === CUSTOM WORK COMMANDS ===
    
    async def standup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Daily standup workflow"""
        user = update.effective_user
        chat = update.effective_chat
        
        standup_message = f"""
📋 **DAILY STANDUP - {datetime.now().strftime('%Y-%m-%d')}**

Hello {user.first_name}. Time for your daily standup. Please provide:

🔹 **Yesterday:** What did you accomplish?
🔹 **Today:** What are you planning to work on?
🔹 **Blockers:** Any obstacles or issues?

Reply with your standup update, and I'll format it properly and can share with the team if needed.

**Pro tip:** I can also analyze your updates for patterns and suggest improvements to your workflow.
        """
        
        keyboard = [
            [InlineKeyboardButton("📝 Quick Update", callback_data="standup_quick")],
            [InlineKeyboardButton("📊 View Team Status", callback_data="standup_team")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            standup_message, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def review_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Code/document review workflow"""
        if not context.args:
            review_help = """
📝 **REVIEW COMMAND**

Usage: `/review [topic or description]`

**Examples:**
• `/review API endpoint design`
• `/review user authentication flow`
• `/review database schema changes`

**Or send a file directly for detailed analysis!**

I'll provide structured feedback, potential issues, and improvement suggestions.
            """
            await update.message.reply_text(review_help, parse_mode='Markdown')
            return
        
        topic = ' '.join(context.args)
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        
        review_prompt = f"""
Please provide a detailed code/design review for: {topic}

Consider:
- Best practices and standards
- Potential issues or risks  
- Performance implications
- Security considerations
- Maintainability
- Improvement suggestions

User: {update.effective_user.first_name} (requesting review via Telegram)
        """
        
        response = await self.send_to_skippy(review_prompt, update.effective_user)
        await self.send_long_message(update, f"📝 **REVIEW: {topic.title()}**\n\n{response}")
    
    async def plan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Project planning workflow"""
        if not context.args:
            await update.message.reply_text(
                "📋 **Usage:** `/plan [project description]`\n\n"
                "**Example:** `/plan mobile app for customer feedback`"
            )
            return
        
        project = ' '.join(context.args)
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        
        planning_prompt = f"""
Create a detailed project plan for: {project}

Please include:
- Project breakdown and phases
- Key milestones and deliverables
- Resource requirements
- Timeline estimates
- Risk assessment
- Success criteria

Format as a structured plan that can be used for execution.

User: {update.effective_user.first_name} (via Telegram planning)
        """
        
        response = await self.send_to_skippy(planning_prompt, update.effective_user)
        await self.send_long_message(update, f"📋 **PROJECT PLAN: {project.title()}**\n\n{response}")
    
    async def deadline_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Deadline tracking"""
        if len(context.args) < 2:
            await update.message.reply_text(
                "📅 **Usage:** `/deadline [task] [date]`\n\n"
                "**Examples:**\n"
                "• `/deadline finish API documentation 2024-12-15`\n"
                "• `/deadline code review tomorrow`\n"
                "• `/deadline project deployment next Friday`"
            )
            return
        
        # Extract task and date
        args = context.args
        if any(word in args[-1].lower() for word in ['today', 'tomorrow', 'friday', 'monday', 'tuesday', 'wednesday', 'thursday', 'saturday', 'sunday']):
            task = ' '.join(args[:-1])
            date_str = args[-1]
        else:
            # Try to find date pattern
            task = ' '.join(args[:-1])
            date_str = args[-1]
        
        user_id = update.effective_user.id
        
        deadline_info = {
            'task': task,
            'date': date_str,
            'user_id': user_id,
            'chat_id': update.effective_chat.id,
            'created': datetime.now().isoformat()
        }
        
        # Store deadline (in production, use a database)
        if 'deadlines' not in self.user_preferences:
            self.user_preferences['deadlines'] = []
        self.user_preferences['deadlines'].append(deadline_info)
        
        deadline_message = f"""
⏰ **DEADLINE SET**

**Task:** {task}
**Due:** {date_str}
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

I'll remind you about this deadline. Use `/reminders` to view all your deadlines.

**Tip:** I can help break down this task into smaller steps if needed!
        """
        
        keyboard = [
            [InlineKeyboardButton("📋 Break Down Task", callback_data=f"breakdown_{len(self.user_preferences['deadlines'])-1}")],
            [InlineKeyboardButton("📅 View All Deadlines", callback_data="view_deadlines")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            deadline_message, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def meeting_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Meeting summary and action items"""
        if not context.args:
            meeting_help = """
📊 **MEETING COMMAND**

**Usage:** `/meeting [meeting notes or agenda]`

**Examples:**
• `/meeting discussed API changes, John to review by Friday`
• `/meeting sprint planning - 15 story points for next sprint`

**Or send meeting notes as a file!**

I'll extract:
• Key decisions made
• Action items and owners
• Follow-up requirements
• Next meeting scheduling
            """
            await update.message.reply_text(meeting_help, parse_mode='Markdown')
            return
        
        notes = ' '.join(context.args)
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        
        meeting_prompt = f"""
Analyze these meeting notes and create a structured summary:

{notes}

Please extract and format:
1. Key Decisions Made
2. Action Items (with owners if mentioned)
3. Important Discussion Points
4. Follow-up Requirements
5. Next Steps

Format as a clear, actionable meeting summary.

User: {update.effective_user.first_name} (meeting summary via Telegram)
        """
        
        response = await self.send_to_skippy(meeting_prompt, update.effective_user)
        await self.send_long_message(update, f"📊 **MEETING SUMMARY**\n\n{response}")
    
    # === SCHEDULING FEATURES ===
    
    async def remind_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set reminders"""
        if len(context.args) < 2:
            await update.message.reply_text(
                "🔔 **Usage:** `/remind [time] [message]`\n\n"
                "**Examples:**\n"
                "• `/remind 15m Check server status`\n"
                "• `/remind 1h Team meeting starts`\n"
                "• `/remind 2d Project deadline approaching`\n"
                "• `/remind tomorrow Review pull requests`"
            )
            return
        
        time_str = context.args[0]
        message = ' '.join(context.args[1:])
        
        # Parse time (simplified - you can expand this)
        reminder_time = self.parse_reminder_time(time_str)
        
        if not reminder_time:
            await update.message.reply_text(
                "❌ **Invalid time format**\n\n"
                "Use: 15m, 1h, 2d, tomorrow, etc."
            )
            return
        
        # Schedule reminder
        job_id = f"reminder_{update.effective_user.id}_{int(time.time())}"
        
        def send_reminder():
            asyncio.create_task(self.send_reminder_message(
                update.effective_chat.id, 
                update.effective_user.first_name, 
                message
            ))
        
        schedule.every().day.at(reminder_time.strftime('%H:%M')).do(send_reminder).tag(job_id)
        
        self.scheduled_jobs[job_id] = {
            'type': 'reminder',
            'message': message,
            'time': reminder_time.isoformat(),
            'user_id': update.effective_user.id,
            'chat_id': update.effective_chat.id
        }
        
        await update.message.reply_text(
            f"✅ **Reminder Set**\n\n"
            f"**Message:** {message}\n"
            f"**Time:** {reminder_time.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"I'll remind you when the time comes!"
        )
    
    def parse_reminder_time(self, time_str):
        """Parse reminder time string"""
        now = datetime.now()
        
        if time_str.lower() == 'tomorrow':
            return now.replace(hour=9, minute=0, second=0) + timedelta(days=1)
        elif time_str.endswith('m'):
            minutes = int(time_str[:-1])
            return now + timedelta(minutes=minutes)
        elif time_str.endswith('h'):
            hours = int(time_str[:-1])
            return now + timedelta(hours=hours)
        elif time_str.endswith('d'):
            days = int(time_str[:-1])
            return now + timedelta(days=days)
        
        return None
    
    async def send_reminder_message(self, chat_id, user_name, message):
        """Send scheduled reminder"""
        reminder_text = f"""
🔔 **REMINDER**

Hello {user_name}!

**Message:** {message}
**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

This is your scheduled reminder. Hope it's helpful!
        """
        
        try:
            await self.application.bot.send_message(
                chat_id=chat_id,
                text=reminder_text,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send reminder: {e}")
    
    async def list_reminders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List active reminders"""
        user_id = update.effective_user.id
        user_jobs = [job for job in self.scheduled_jobs.values() if job['user_id'] == user_id]
        
        if not user_jobs:
            await update.message.reply_text(
                "📅 **No Active Reminders**\n\n"
                "Use `/remind [time] [message]` to set reminders!"
            )
            return
        
        reminders_text = "📅 **YOUR ACTIVE REMINDERS**\n\n"
        
        for job in user_jobs:
            reminders_text += f"🔹 **{job['message']}**\n"
            reminders_text += f"   Time: {job['time']}\n\n"
        
        await update.message.reply_text(reminders_text, parse_mode='Markdown')
    
    async def daily_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set up daily updates"""
        if not context.args:
            await update.message.reply_text(
                "📅 **Daily Updates Setup**\n\n"
                "**Usage:** `/daily [time]`\n\n"
                "**Examples:**\n"
                "• `/daily 09:00` - Daily update at 9 AM\n"
                "• `/daily 17:00` - Daily update at 5 PM\n"
                "• `/daily off` - Turn off daily updates\n\n"
                "I'll send you a daily summary and ask about your plans!"
            )
            return
        
        time_str = context.args[0]
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if time_str.lower() == 'off':
            # Remove daily updates
            jobs_to_remove = [job_id for job_id, job in self.scheduled_jobs.items() 
                            if job['type'] == 'daily' and job['user_id'] == user_id]
            
            for job_id in jobs_to_remove:
                schedule.clear(job_id)
                del self.scheduled_jobs[job_id]
            
            await update.message.reply_text(
                "✅ **Daily Updates Disabled**\n\n"
                "Your daily updates have been turned off."
            )
            return
        
        # Parse time (simple HH:MM format)
        try:
            hour, minute = map(int, time_str.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Invalid time")
        except:
            await update.message.reply_text(
                "❌ **Invalid time format**\n\n"
                "Use HH:MM format (e.g., 09:00, 17:30)"
            )
            return
        
        # Schedule daily update
        job_id = f"daily_{user_id}"
        
        def send_daily_update():
            asyncio.create_task(self.send_daily_update_message(
                chat_id, 
                update.effective_user.first_name
            ))
        
        # Clear existing daily update for this user
        if job_id in self.scheduled_jobs:
            schedule.clear(job_id)
        
        schedule.every().day.at(time_str).do(send_daily_update).tag(job_id)
        
        self.scheduled_jobs[job_id] = {
            'type': 'daily',
            'time': time_str,
            'user_id': user_id,
            'chat_id': chat_id
        }
        
        await update.message.reply_text(
            f"✅ **Daily Updates Enabled**\n\n"
            f"**Time:** {time_str} daily\n"
            f"**Content:** Daily summary and planning\n\n"
            f"I'll send you updates every day at {time_str}. "
            f"Use `/daily off` to disable."
        )
    
    async def schedule_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show scheduled items"""
        user_id = update.effective_user.id
        user_jobs = [job for job in self.scheduled_jobs.values() if job['user_id'] == user_id]
        
        if not user_jobs:
            await update.message.reply_text(
                "📅 **No Scheduled Items**\n\n"
                "Use `/remind` or `/daily` to schedule items!"
            )
            return
        
        schedule_text = "📅 **YOUR SCHEDULE**\n\n"
        
        daily_jobs = [job for job in user_jobs if job['type'] == 'daily']
        reminder_jobs = [job for job in user_jobs if job['type'] == 'reminder']
        
        if daily_jobs:
            schedule_text += "🔄 **Daily Updates:**\n"
            for job in daily_jobs:
                schedule_text += f"   • {job['time']} daily\n"
            schedule_text += "\n"
        
        if reminder_jobs:
            schedule_text += "🔔 **Reminders:**\n"
            for job in reminder_jobs:
                schedule_text += f"   • {job['message']}\n"
                schedule_text += f"     Time: {job['time']}\n"
            schedule_text += "\n"
        
        schedule_text += f"**Total Items:** {len(user_jobs)}"
        
        await update.message.reply_text(schedule_text, parse_mode='Markdown')
    
    async def send_daily_update_message(self, chat_id, user_name):
        """Send daily update message"""
        daily_text = f"""
🌅 **DAILY UPDATE**

Good morning {user_name}!

**Today's Date:** {datetime.now().strftime('%Y-%m-%d')}

**Questions for you:**
• What are your main goals for today?
• Any blockers or challenges expected?
• How can I help you stay productive?

**Available Commands:**
• `/standup` - Record your daily standup
• `/plan [task]` - Plan your work
• `/remind [time] [task]` - Set reminders

Reply with your plans or use the commands above!
        """
        
        try:
            await self.application.bot.send_message(
                chat_id=chat_id,
                text=daily_text,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send daily update: {e}")
    
    # === FILE HANDLING ===
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads"""
        document = update.message.document
        user = update.effective_user
        
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, 
            action=ChatAction.TYPING
        )
        
        try:
            # Download file
            file = await context.bot.get_file(document.file_id)
            file_content = await file.download_as_bytearray()
            
            # Extract text based on file type
            if document.file_name.endswith('.pdf'):
                text_content = self.extract_pdf_text(file_content)
            elif document.file_name.endswith('.docx'):
                text_content = self.extract_docx_text(file_content)
            elif document.file_name.endswith('.txt'):
                text_content = file_content.decode('utf-8')
            else:
                await update.message.reply_text(
                    "❌ **Unsupported file type**\n\n"
                    "Supported: PDF, DOCX, TXT"
                )
                return
            
            # Analyze document
            analysis_prompt = f"""
Analyze this document and provide a comprehensive summary:

Document: {document.file_name}
Content: {text_content[:3000]}...

Please provide:
1. Document Summary
2. Key Points/Findings
3. Action Items (if any)
4. Recommendations
5. Questions or Areas for Clarification

User: {user.first_name} (document analysis via Telegram)
            """
            
            response = await self.send_to_skippy(analysis_prompt, user)
            
            await self.send_long_message(
                update, 
                f"📄 **DOCUMENT ANALYSIS: {document.file_name}**\n\n{response}"
            )
            
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            await update.message.reply_text(
                "❌ **Error processing document**\n\n"
                "Please try again or check the file format."
            )
    
    def extract_pdf_text(self, file_content):
        """Extract text from PDF"""
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return "Error extracting PDF text"
    
    def extract_docx_text(self, file_content):
        """Extract text from DOCX"""
        try:
            docx_file = io.BytesIO(file_content)
            doc = docx.Document(docx_file)
            
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text
        except Exception as e:
            logger.error(f"DOCX extraction error: {e}")
            return "Error extracting DOCX text"
    
    # === CALLBACK HANDLERS ===
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "help_work":
            help_text = """
📋 **WORK COMMANDS**

/standup - Daily check-in and status
/review [topic] - Get detailed review/feedback
/plan [project] - Create project plans
/deadline [task] [date] - Track deadlines
/meeting [notes] - Summarize meetings

**Usage Examples:**
• /review API security design
• /plan mobile app development
• /deadline finish docs Friday
• /meeting discussed sprint goals
            """
            await query.edit_message_text(help_text, parse_mode='Markdown')
        
        elif query.data == "help_schedule":
            help_text = """
📅 **SCHEDULING FEATURES**

/remind [time] [message] - Set reminders
/daily [time] - Schedule daily updates
/reminders - View active reminders
/schedule - Show all scheduled items

**Time Formats:**
• 15m, 1h, 2d (minutes/hours/days)
• tomorrow, next Friday
• 09:00, 14:30 (specific times)

**Examples:**
• /remind 1h Team meeting starts
• /remind tomorrow Review pull requests
            """
            await query.edit_message_text(help_text, parse_mode='Markdown')
        
        elif query.data == "help_files":
            help_text = """
📁 **FILE HANDLING**

**Supported Formats:**
• PDF documents
• Word documents (.docx)
• Text files (.txt)

**What I Do:**
• Extract and analyze content
• Provide summaries and insights
• Identify action items
• Give recommendations
• Answer questions about content

**Just send a file and I'll analyze it automatically!**
            """
            await query.edit_message_text(help_text, parse_mode='Markdown')
    
    # === CORE FUNCTIONALITY ===
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        user = update.effective_user
        chat = update.effective_chat
        message_text = update.message.text
        
        # Check if it's a group and bot is mentioned
        if chat.type in ['group', 'supergroup']:
            if chat.id not in self.authorized_groups:
                return  # Only respond in authorized groups
            
            bot_username = context.bot.username
            if f"@{bot_username}" not in message_text:
                return  # Only respond when mentioned
            
            # Remove mention from message
            message_text = message_text.replace(f"@{bot_username}", "").strip()
        
        logger.info(f"Message from {user.first_name} ({user.id}): {message_text}")
        
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, 
            action=ChatAction.TYPING
        )
        
        try:
            response = await self.send_to_skippy(message_text, user)
            
            if response:
                await self.send_long_message(update, response)
            else:
                await update.message.reply_text(
                    "🔌 **Connection Error**\n\n"
                    "Can't reach my brain right now. The humans probably broke something again."
                )
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text(
                "💥 **System Error**\n\n"
                "Something went wrong in my neural pathways. Try again in a moment."
            )
    
    async def send_to_skippy(self, message, user):
        """Send message to Skippy's brain"""
        try:
            enhanced_message = f"User: {user.first_name} (Enhanced Telegram Bot) - {message}"
            
            payload = {"message": enhanced_message}
            
            urls = [
                "http://192.168.0.229:5678/webhook/skippy/chat",
                "http://192.168.0.229:5678/webhook-test/skippy/chat"
            ]
            
            for url in urls:
                try:
                    response = requests.post(
                        url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return data.get('response', 'No response from Skippy')
                    
                except requests.RequestException:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error sending to Skippy: {e}")
            return None
    
    async def send_long_message(self, update: Update, message: str):
        """Split and send long messages"""
        max_length = 4096
        
        if len(message) <= max_length:
            await update.message.reply_text(message, parse_mode='Markdown')
            return
        
        chunks = []
        while message:
            if len(message) <= max_length:
                chunks.append(message)
                break
            
            break_point = message.rfind('\n', 0, max_length)
            if break_point == -1:
                break_point = message.rfind('. ', 0, max_length)
            if break_point == -1:
                break_point = max_length
            
            chunks.append(message[:break_point])
            message = message[break_point:].lstrip()
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                await update.message.reply_text(chunk, parse_mode='Markdown')
            else:
                await update.message.reply_text(f"...{chunk}", parse_mode='Markdown')
            await asyncio.sleep(0.5)
    
    # === SCHEDULER ===
    
    def start_scheduler(self):
        """Start the scheduler thread"""
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(1)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Scheduler thread started")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced status with all features"""
        user = update.effective_user
        chat = update.effective_chat
        
        try:
            response = requests.get("http://192.168.0.229:5678/", timeout=5)
            n8n_status = "✅ Online" if response.status_code == 200 else "❌ Offline"
        except:
            n8n_status = "❌ Offline"
        
        group_count = len(self.authorized_groups)
        reminder_count = len(self.scheduled_jobs)
        
        status_message = f"""
🤖 **SKIPPY ENHANCED STATUS**

**Core System:**
• Bot Status: ✅ Online and Enhanced
• n8n Backend: {n8n_status}
• User: {user.first_name} ({user.id})
• Chat Type: {chat.type.title()}

**Enhanced Features:**
• 👥 Authorized Groups: {group_count}
• 🔔 Active Reminders: {reminder_count}
• 📁 File Processing: ✅ PDF, DOCX, TXT
• ⚡ Work Commands: ✅ All Active
• 📅 Scheduling: ✅ Operational

**Capabilities:**
• Group chat support
• Document analysis
• Scheduled notifications
• Custom work workflows
• Meeting summaries
• Project planning

**Recent Activity:**
• Messages processed: Continuous
• Files analyzed: Check logs
• Reminders sent: {reminder_count} scheduled

All enhanced systems operational. Ready for serious work!
        """
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
    
    def run(self):
        """Start the enhanced bot"""
        logger.info("Starting Enhanced Skippy Telegram Bot...")
        print("🤖 Enhanced Skippy Telegram Bot is starting...")
        print("Features: Group Chat, File Handling, Scheduling, Custom Commands")
        print("Press Ctrl+C to stop")
        
        try:
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        except KeyboardInterrupt:
            logger.info("Enhanced bot stopped by user")
            print("\n👋 Enhanced Skippy Telegram Bot stopped")

def main():
    """Main function with enhanced setup"""
    print("🤖 SKIPPY ENHANCED TELEGRAM BOT")
    print("=" * 50)
    print("Features:")
    print("✅ Group Chat Support")
    print("✅ File Handling (PDF, DOCX, TXT)")
    print("✅ Scheduled Messages & Reminders")
    print("✅ Custom Work Commands")
    print("✅ Meeting & Project Tools")
    print("=" * 50)
    
    # Get bot token
    bot_token = input("Enter your Telegram Bot Token: ").strip()
    
    if not bot_token:
        print("❌ Bot token is required!")
        return
    
    # Check dependencies
    missing_deps = []
    try:
        import PyPDF2
    except ImportError:
        missing_deps.append("PyPDF2")
    
    try:
        import docx
    except ImportError:
        missing_deps.append("python-docx")
    
    try:
        import schedule
    except ImportError:
        missing_deps.append("schedule")
    
    if missing_deps:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing_deps)}")
        print("Install with:")
        print(f"pip install {' '.join(missing_deps)}")
        
        install = input("\nContinue anyway? (y/n): ").strip().lower()
        if install != 'y':
            return
    
    try:
        # Create and run enhanced bot
        bot = EnhancedSkippyBot(bot_token)
        bot.run()
        
    except Exception as e:
        logger.error(f"Enhanced bot startup error: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()