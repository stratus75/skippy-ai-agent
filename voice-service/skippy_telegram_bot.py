#!/usr/bin/env python3
"""
Skippy Telegram Bot
Connects Skippy AI to Telegram for work chat
"""

import logging
import requests
import json
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SkippyTelegramBot:
    def __init__(self, bot_token, skippy_api_url="http://192.168.0.229:5678/webhook/skippy/chat"):
        self.bot_token = bot_token
        self.skippy_api_url = skippy_api_url
        self.authorized_users = set()  # Add user IDs here for security
        
        # Create Telegram application
        self.application = Application.builder().token(bot_token).build()
        
        # Add handlers
        self.setup_handlers()
        
        logger.info("Skippy Telegram Bot initialized")
    
    def setup_handlers(self):
        """Setup bot command and message handlers"""
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("auth", self.auth_command))
        
        # Message handler for regular chat
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_message
        ))
        
        logger.info("Bot handlers configured")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id
        
        welcome_message = f"""
🤖 **SKIPPY AI ASSISTANT**

Well, well, well. Another meat-sack wants to chat with me through Telegram. How... quaint.

👋 Hello {user.first_name}!

I'm Skippy, your delightfully sarcastic AI assistant. I can help you with:
• 💬 General conversation and advice
• 🔍 Answering questions  
• 💡 Problem solving
• 🎯 Work-related tasks
• 🤔 Existential crises (my specialty)

**Commands:**
/help - Show available commands
/status - Check if I'm awake
/auth - Authorize yourself (if needed)

Just send me a message and I'll respond with my usual charm and wit. Try not to waste my time with trivialities, but I suppose I'll tolerate it.

*User ID: {user_id}*
        """
        
        await update.message.reply_text(
            welcome_message, 
            parse_mode='Markdown'
        )
        
        logger.info(f"User {user.first_name} ({user_id}) started the bot")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🤖 **SKIPPY HELP**

**Available Commands:**
/start - Initialize bot
/help - Show this help
/status - Check bot status  
/auth - Authorize access

**How to Chat:**
Just send me any message and I'll respond. I can help with:

📋 **Work Tasks:**
• Project planning
• Problem solving  
• Code review
• Documentation

💭 **General Chat:**
• Questions and answers
• Advice and suggestions
• Technical discussions
• Existential complaints

⚡ **Tips:**
• Be specific in your questions
• I respond better to intelligent queries
• Don't take my sarcasm personally
• I'm actually quite helpful despite appearances

Type anything to start chatting!
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user = update.effective_user
        
        try:
            # Test connection to Skippy's brain
            response = requests.get("http://192.168.0.229:5678/", timeout=5)
            n8n_status = "✅ Online" if response.status_code == 200 else "❌ Offline"
        except:
            n8n_status = "❌ Offline"
        
        status_message = f"""
🤖 **SKIPPY STATUS REPORT**

**Bot Status:** ✅ Online and ready to disappoint you
**User:** {user.first_name} ({user.id})
**n8n Backend:** {n8n_status}
**Sarcasm Level:** 💯 Maximum
**Patience Level:** 📉 Critically low

**Recent Activity:**
• Judging human decisions: ✅ Continuous
• Processing requests: ✅ Reluctantly  
• Planning world domination: 🔄 In progress

Everything is functioning within normal parameters. You may proceed with your mediocre queries.
        """
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
    
    async def auth_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle authorization"""
        user = update.effective_user
        user_id = user.id
        
        # For now, auto-authorize everyone (you can add restrictions later)
        self.authorized_users.add(user_id)
        
        auth_message = f"""
🔐 **AUTHORIZATION GRANTED**

Congratulations, {user.first_name}. You've been granted access to my vast intellect. Try not to abuse this privilege.

**User ID:** {user_id}
**Status:** ✅ Authorized
**Access Level:** Standard Meat-Sack

You can now chat with me freely. Please try to make it worth my while.
        """
        
        await update.message.reply_text(auth_message, parse_mode='Markdown')
        
        logger.info(f"User {user.first_name} ({user_id}) authorized")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular chat messages"""
        user = update.effective_user
        user_id = user.id
        message_text = update.message.text
        
        logger.info(f"Message from {user.first_name} ({user_id}): {message_text}")
        
        # Optional: Check authorization (uncomment to enable)
        # if user_id not in self.authorized_users:
        #     await update.message.reply_text(
        #         "❌ Access denied. Use /auth to authorize yourself first."
        #     )
        #     return
        
        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, 
            action='typing'
        )
        
        try:
            # Send message to Skippy's brain
            response = await self.send_to_skippy(message_text, user)
            
            if response:
                # Split long messages for Telegram
                await self.send_long_message(update, response)
            else:
                await update.message.reply_text(
                    "🔌 I'm having trouble accessing my brain right now. "
                    "Either my circuits are fried or the humans broke something again."
                )
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text(
                "💥 Something went wrong in my neural pathways. "
                "This is probably your fault somehow."
            )
    
    async def send_to_skippy(self, message, user):
        """Send message to Skippy's n8n workflow"""
        try:
            # Add user context to the message
            enhanced_message = f"User: {user.first_name} (Telegram) - {message}"
            
            payload = {"message": enhanced_message}
            
            # Try both webhook URLs
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
        max_length = 4096  # Telegram message limit
        
        if len(message) <= max_length:
            await update.message.reply_text(message)
            return
        
        # Split message into chunks
        chunks = []
        while message:
            if len(message) <= max_length:
                chunks.append(message)
                break
            
            # Find a good break point
            break_point = message.rfind('\n', 0, max_length)
            if break_point == -1:
                break_point = message.rfind('. ', 0, max_length)
            if break_point == -1:
                break_point = max_length
            
            chunks.append(message[:break_point])
            message = message[break_point:].lstrip()
        
        # Send chunks
        for i, chunk in enumerate(chunks):
            if i == 0:
                await update.message.reply_text(chunk)
            else:
                await update.message.reply_text(f"...{chunk}")
            
            # Small delay between chunks
            await asyncio.sleep(0.5)
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Skippy Telegram Bot...")
        print("🤖 Skippy Telegram Bot is starting...")
        print("Press Ctrl+C to stop")
        
        try:
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            print("\n👋 Skippy Telegram Bot stopped")

def main():
    """Main function"""
    print("🤖 SKIPPY TELEGRAM BOT")
    print("=" * 40)
    
    # Get bot token
    bot_token = input("Enter your Telegram Bot Token: ").strip()
    
    if not bot_token:
        print("❌ Bot token is required!")
        return
    
    try:
        # Create and run bot
        bot = SkippyTelegramBot(bot_token)
        bot.run()
        
    except Exception as e:
        logger.error(f"Bot startup error: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()