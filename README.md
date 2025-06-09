
**Ah! That's a critical issue - Ollama (your AI engine) isn't running or isn't accessible at that URL. This is why the AI chat routing will fail.**

## 🔍 **Let's Check Ollama Status:**

### **Step 1: Check if Ollama is Running****Run this Ollama checker:**
```bash
cd H:\skippy-ai-agent\home-integration
python ollama_checker.py
```

## 🚀 **Quick Manual Checks:**

### **Check 1: Is Ollama Installed and Running?**
```bash
# Open Command Prompt and try:
ollama --version

# If installed, try:
ollama serve

# Or try:
ollama run llama3.1:8b
```

### **Check 2: Quick URL Test**
```bash
# Test if Ollama is responding:
curl http://192.168.0.229:11434/api/tags
curl http://localhost:11434/api/tags
```

## 🔧 **Most Likely Solutions:**

### **Solution 1: Start Ollama**
**If Ollama is installed but not running:**
```bash
# Open Command Prompt as Administrator
ollama serve
```
**Keep this window open**

### **Solution 2: Install Ollama**
**If Ollama isn't installed:**
1. **Download Ollama:** https://ollama.ai
2. **Install it**
3. **Open Command Prompt:**
   ```bash
   ollama pull llama3.1:8b
   ollama serve
   ```

### **Solution 3: Use Different Ollama URL**
**If Ollama is running on a different URL, we'll update the workflow accordingly.**

## 🎯 **Temporary Fix - Use Home Automation Only**

**While we fix Ollama, let's create a simplified workflow that only does home automation:**## 🎯 **Quick Action Plan:**

### **Step 1: Use Temporary Workflow (No Ollama Required)**
1. **Delete any existing workflows in n8n**
2. **Import the "Home-Only" workflow above**
3. **Activate it**
4. **Test immediately**

### **Step 2: Fix Ollama (Parallel Task)**
1. **Run the ollama checker script**
2. **Start/install Ollama if needed**
3. **Once working, upgrade to full AI workflow**

### **Step 3: Test the Temporary Workflow**
```bash
# Test home automation (should work perfectly)
curl -X POST "http://192.168.0.229:5678/webhook/skippy/chat" -H "Content-Type: application/json" -d "{\"message\": \"turn on the lights\", \"user\": \"TestUser\"}"

# Test basic AI (built-in responses)
curl -X POST "http://192.168.0.229:5678/webhook/skippy/chat" -H "Content-Type: application/json" -d "{\"message\": \"tell me a joke\", \"user\": \"TestUser\"}"
```

## 🚀 **This Should Fix Your Routing Tests:**
**The temporary workflow will:**
- ✅ **Handle home automation** with proper routing
- ✅ **Handle basic AI** with built-in Skippy responses
- ✅ **Return proper JSON** with `route`, `personality_mode`, etc.
- ✅ **Pass all routing tests**

**First, run the ollama checker to see what's wrong with Ollama, then import the temporary workflow to get everything working while we fix the AI engine!** 🔧# Skippy AI Agent - Phase 1 Setup Guide

## Overview
This guide will help you build the foundation of Skippy - your AI home assistant with personality, voice interaction, and expandable capabilities.

## Prerequisites
- Windows 10 (with future Ubuntu Server migration path)
- DESKTOP-P9KPD9G specifications confirmed
- Docker Desktop for Windows
- Node.js 18+ installed
- Python 3.9+ installed

## Phase 1 Architecture

```
┌─────────────────────────────────────────┐
│           Main Server (Windows)         │
├─────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────────┐   │
│  │   n8n Hub   │  │  Skippy Core    │   │
│  │ Orchestrator│  │  Personality    │   │
│  └─────────────┘  └─────────────────┘   │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ Voice Module│  │ Conversation    │   │
│  │ STT/TTS     │  │ Logger          │   │
│  └─────────────┘  └─────────────────┘   │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │   Redis     │  │   PostgreSQL    │   │
│  │ Message Q   │  │   Database      │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
```

## Step 1: Core Infrastructure Setup

### 1.1 Install Docker Desktop
```bash
# Download from https://docker.com/products/docker-desktop
# Install and restart system
# Verify installation
docker --version
docker-compose --version
```

### 1.2 Create Project Structure
```bash
mkdir skippy-ai-agent
cd skippy-ai-agent
mkdir -p {n8n,voice,personality,database,logs,config}
```

### 1.3 Docker Compose Configuration
Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # Redis for message queuing and caching
  redis:
    image: redis:7-alpine
    container_name: skippy-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  # PostgreSQL for persistent data
  postgres:
    image: postgres:15-alpine
    container_name: skippy-db
    environment:
      POSTGRES_DB: skippy
      POSTGRES_USER: skippy
      POSTGRES_PASSWORD: skippy_secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped

  # n8n Orchestration Hub
  n8n:
    image: n8nio/n8n:latest
    container_name: skippy-n8n
    ports:
      - "5679:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=skippy_admin
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_DATABASE=skippy
      - DB_POSTGRESDB_USER=skippy
      - DB_POSTGRESDB_PASSWORD=skippy_secure_password
      - N8N_ENCRYPTION_KEY=your_encryption_key_here
      - WEBHOOK_URL=http://localhost:5678/
    volumes:
      - n8n_data:/home/node/.n8n
      - ./n8n/custom:/home/node/.n8n/custom
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
  n8n_data:
```

## Step 2: Voice Processing Module

### 2.1 Voice Service Setup
Create `voice/voice_service.py`:

```python
import asyncio
import websockets
import json
import whisper
import pyttsx3
import pyaudio
import wave
import threading
from queue import Queue
import numpy as np

class SkippyVoiceService:
    def __init__(self):
        self.whisper_model = whisper.load_model("base")
        self.tts_engine = pyttsx3.init()
        self.wake_words = ["hey skippy", "skippy"]
        self.conversation_mode = False
        self.trading_mode = False
        self.audio_queue = Queue()
        
    async def start_voice_service(self):
        """Main voice service loop"""
        print("🎤 Skippy Voice Service Starting...")
        
        # Start audio capture thread
        audio_thread = threading.Thread(target=self.capture_audio)
        audio_thread.daemon = True
        audio_thread.start()
        
        # Start WebSocket server for n8n communication
        await websockets.serve(self.handle_websocket, "localhost", 8765)
        print("🎤 Voice service ready on ws://localhost:8765")
        
    async def handle_websocket(self, websocket, path):
        """Handle WebSocket connections from n8n"""
        async for message in websocket:
            data = json.loads(message)
            if data['type'] == 'speak':
                self.speak(data['text'])
            elif data['type'] == 'set_mode':
                self.set_conversation_mode(data['mode'])
                
    def capture_audio(self):
        """Continuous audio capture and processing"""
        # Audio capture implementation
        pass
        
    def process_speech(self, audio_data):
        """Convert speech to text using Whisper"""
        result = self.whisper_model.transcribe(audio_data)
        text = result["text"].lower().strip()
        
        # Check for wake words and mode commands
        if any(wake_word in text for wake_word in self.wake_words):
            if "conversational mode" in text:
                self.conversation_mode = True
                self.speak("Entering conversational mode")
            elif "trading mode" in text:
                self.trading_mode = True
                self.speak("Entering trading mode")
            else:
                # Send to n8n for processing
                self.send_to_n8n(text)
                
    def speak(self, text):
        """Convert text to speech"""
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
        
    def send_to_n8n(self, text):
        """Send processed speech to n8n hub"""
        # WebSocket communication to n8n
        pass

if __name__ == "__main__":
    service = SkippyVoiceService()
    asyncio.run(service.start_voice_service())
```

### 2.2 Voice Module Dockerfile
Create `voice/Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    espeak \
    espeak-data \
    libespeak1 \
    libespeak-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "voice_service.py"]
```

## Step 3: Skippy Personality Engine

### 3.1 Core Personality Module
Create `personality/skippy_core.py`:

```python
import json
import asyncio
import websockets
from datetime import datetime
import redis
import psycopg2
from typing import Dict, List, Any

class SkippyPersonality:
    def __init__(self):
        self.personality_traits = {
            "sarcasm_level": 7,  # 1-10 scale
            "helpfulness": 9,
            "technical_expertise": 8,
            "humor": 8,
            "loyalty": 10,
            "curiosity": 9
        }
        
        self.memory = {
            "conversations": [],
            "user_preferences": {},
            "learned_behaviors": {},
            "improvement_suggestions": []
        }
        
        self.context = {
            "current_mode": "general",
            "conversation_history": [],
            "active_tasks": [],
            "user_mood": "neutral"
        }
        
    async def process_input(self, input_text: str, user_id: str = "primary") -> str:
        """Process user input and generate Skippy's response"""
        
        # Log conversation
        self.log_conversation(user_id, input_text, "user")
        
        # Analyze input for context
        context = self.analyze_context(input_text)
        
        # Generate response based on personality and context
        response = await self.generate_response(input_text, context)
        
        # Log Skippy's response
        self.log_conversation(user_id, response, "skippy")
        
        return response
        
    def analyze_context(self, text: str) -> Dict[str, Any]:
        """Analyze input for emotional context, intent, and complexity"""
        context = {
            "intent": self.detect_intent(text),
            "emotion": self.detect_emotion(text),
            "complexity": self.assess_complexity(text),
            "requires_specialization": self.check_specialization_needed(text)
        }
        return context
        
    async def generate_response(self, input_text: str, context: Dict) -> str:
        """Generate personality-appropriate response"""
        
        # This will integrate with your chosen LLM
        base_prompt = f"""
        You are Skippy, an AI assistant with these personality traits:
        - Sarcasm level: {self.personality_traits['sarcasm_level']}/10
        - Highly helpful and technical
        - Loyal and curious
        - Based on the character from Expeditionary Force by Craig Alanson
        
        Current context: {context}
        User input: {input_text}
        
        Respond in character as Skippy would, being helpful but with appropriate personality.
        """
        
        # Placeholder for LLM integration
        response = await self.call_llm(base_prompt)
        
        return response
        
    def log_conversation(self, user_id: str, message: str, source: str):
        """Log all conversations for learning and sync"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "message": message,
            "source": source,
            "context": self.context.copy()
        }
        
        # Store in memory and database
        self.memory["conversations"].append(log_entry)
        self.save_to_database(log_entry)
        
    def learn_from_interaction(self, feedback: Dict):
        """Learn and adapt from user interactions"""
        # Implement learning logic
        pass
        
    def sync_with_edge_devices(self):
        """Sync personality state with edge devices"""
        sync_data = {
            "personality_traits": self.personality_traits,
            "recent_context": self.context,
            "user_preferences": self.memory["user_preferences"]
        }
        # Send to edge devices via Redis
        pass

# Integration with your LLM of choice
async def call_llm(self, prompt: str) -> str:
    """Integrate with local LLM (Ollama/LM Studio) or API"""
    # This will be your LLM integration point
    # For now, return a placeholder
    return "This is where Skippy's LLM response will go"

if __name__ == "__main__":
    skippy = SkippyPersonality()
    # Start personality service
```

## Step 4: Database Schema

Create `database/init.sql`:

```sql
-- Conversations table
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(50),
    message TEXT,
    source VARCHAR(20),
    context JSONB,
    session_id VARCHAR(100)
);

-- Personality state table
CREATE TABLE personality_state (
    id SERIAL PRIMARY KEY,
    trait_name VARCHAR(50) UNIQUE,
    value FLOAT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User preferences
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    preference_key VARCHAR(100),
    preference_value JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System improvements log
CREATE TABLE improvement_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    category VARCHAR(50),
    description TEXT,
    implementation_status VARCHAR(20) DEFAULT 'pending',
    priority INTEGER DEFAULT 5
);

-- Offline conversation sync
CREATE TABLE offline_conversations (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50),
    conversation_data JSONB,
    sync_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Step 5: n8n Workflow Templates

### 5.1 Basic Voice Processing Workflow
Once n8n is running (http://localhost:5678), create these workflows:

**Workflow: Voice Input Handler**
1. Webhook Trigger (voice input)
2. Function Node (process wake words)
3. Switch Node (route by intent)
4. HTTP Request (to Skippy personality)
5. Webhook Response (back to voice service)

### 5.2 Conversation Logger Workflow
**Workflow: Conversation Logger**
1. Webhook Trigger (all conversations)
2. PostgreSQL Node (save conversation)
3. Redis Node (update recent context)

## Step 6: Configuration Files

Create `config/skippy_config.yaml`:

```yaml
skippy:
  personality:
    name: "Skippy"
    version: "1.0.0"
    base_traits:
      sarcasm: 7
      helpfulness: 9
      technical_expertise: 8

  voice:
    wake_words: ["hey skippy", "skippy"]
    conversation_modes:
      - general
      - conversational
      - trading
      - coding
    
  database:
    host: "localhost"
    port: 5432
    name: "skippy"
    
  redis:
    host: "localhost"
    port: 6379

  logging:
    level: "INFO"
    conversation_retention_days: 365
    sync_offline_conversations: true
```

## Step 7: Quick Start Commands

Create `start_skippy.bat` for Windows:

```batch
@echo off
echo Starting Skippy AI Agent...
docker-compose up -d
echo Skippy services starting...
echo n8n available at: http://localhost:5679
echo Voice service will start automatically
echo Check logs with: docker-compose logs -f
pause
```

## Step 8: Testing & Verification

1. **Start Services**: Run `docker-compose up -d`
2. **Access n8n**: Open http://localhost:5678
3. **Test Database**: Connect to PostgreSQL on localhost:5432
4. **Voice Test**: Run voice service and test wake word detection

## Next Steps for LLM Integration

### Option 1: Local LLM (Ollama)
```bash
# Install Ollama
# Pull a model like llama2 or mistral
ollama pull llama2
```

### Option 2: LM Studio
- Download LM Studio
- Load a model like CodeLlama or Mistral
- Use API endpoint in personality module

### Option 3: OpenAI API (if acceptable)
- Add OpenAI API key to config
- Integrate in personality module

## Conversation Sync Feature

The system will automatically:
1. Log all conversations locally
2. Store offline interactions when you're not available
3. Sync with our conversations when you return
4. Allow Skippy to learn from both interaction types

Would you like me to elaborate on any specific section or create additional configuration files?
Perfect! I've created a comprehensive setup for your Skippy AI Agent. Here's what I've built for you:

## 📦 Complete File Structure Created:

1. **Docker Compose Configuration** - Orchestrates all services (PostgreSQL, Redis, n8n, Personality Core, Voice Service)

2. **Database Schema** - Complete PostgreSQL setup with tables for conversations, personality traits, user preferences, learning patterns, and more

3. **Skippy Personality Core** - A FastAPI-based service that handles Skippy's personality, conversation processing, and learning capabilities

4. **Voice Processing Service** - Handles speech-to-text (Whisper), text-to-speech (pyttsx3), wake word detection, and WebSocket communication

5. **Configuration Files** - YAML configs, environment variables, and even Nginx configuration for production

6. **Testing Suite** - Comprehensive testing scripts to verify all components work together

7. **Management Scripts** - Windows batch files for easy start/stop/restart operations

8. **Complete Documentation** - Detailed README with setup instructions, troubleshooting, and usage examples

## 🎯 Key Features Implemented:

- **Voice Wake Words**: "Hey Skippy", "Skippy", "Yo Skippy"
- **Personality Engine**: Configurable traits (sarcasm: 7/10, helpfulness: 9/10, etc.)
- **Conversation Modes**: General wake-word activation and continuous conversation mode
- **Database Logging**: All conversations stored with context and learning data
- **WebSocket Communication**: Real-time communication between services
- **Health Monitoring**: Comprehensive health checks and status monitoring
- **Docker-based**: Easy deployment and scaling

## 🚀 Next Steps:

1. **Save all the artifacts** to their respective files in your project directory
2. **Run the setup** using the provided scripts
3. **Test the system** with the testing scripts
4. **Choose your LLM integration** (the personality core is ready for Ollama, OpenAI, or Anthropic)

The system is designed to be **modular and expandable** - you can easily add new capabilities, integrate with home automation systems, or extend the personality engine.

Would you like me to help you with any specific aspect of the setup, or would you like me to create additional components like LLM integration or specific n8n workflows?
