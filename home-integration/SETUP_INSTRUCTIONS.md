# 🤖🏠 Skippy Home Assistant Integration - Complete Setup

## 📁 File Structure
```
H:\skippy-ai-agent\home-integration\
├── skippy_home_control_workflow.json      (Home automation workflow)
├── skippy_main_workflow_complete.json     (Main Skippy workflow with routing)
├── test_skippy_complete.py               (Test script)
├── SETUP_INSTRUCTIONS.md                 (This file)
└── README.md                             (Quick reference)
```

## 🎯 What This Integration Does

**BEFORE:** Skippy only does AI chat
```
"Turn on lights" → Skippy: "I don't control your lights, meat-sack"
```

**AFTER:** Skippy controls smart home AND does AI chat
```
"Turn on lights" → Skippy: "Oh, you want light? How revolutionary. ✅ Lights turned ON"
"Tell me a joke" → Skippy: "Why did the human ask an AI for humor? Because..."
```

## 🚀 Quick Setup (5 Minutes)

### Step 1: Import Workflows
1. **Open n8n:** http://192.168.0.229:5678
2. **Import Home Workflow:**
   - New Workflow → Import from file
   - Select `skippy_home_control_workflow.json`
   - Save as "Skippy Home Control"
   - **Activate** the workflow

3. **Import/Update Main Workflow:**
   - Import `skippy_main_workflow_complete.json`
   - Replace your existing main Skippy workflow
   - **Activate** the workflow

### Step 2: Test the Integration
```bash
cd H:\skippy-ai-agent\home-integration
python test_skippy_complete.py
```

Choose option 1 (Full Test Suite)

### Step 3: Try It Out!
**Home Automation Commands:**
```bash
curl -X POST http://192.168.0.229:5678/webhook/skippy/chat -H "Content-Type: application/json" -d "{\"message\": \"turn on the lights\", \"user\": \"TestUser\"}"
```

**Regular AI Commands:**
```bash
curl -X POST http://192.168.0.229:5678/webhook/skippy/chat -H "Content-Type: application/json" -d "{\"message\": \"tell me a joke\", \"user\": \"TestUser\"}"
```

## 🏠 Supported Home Commands

### 💡 Lighting Control
- `"turn on the lights"` → Turns on all lights
- `"turn off the lights"` → Turns off all lights  
- `"set lights to blue"` → Changes light color
- `"dim lights to 50%"` → Sets brightness

### 🎬 Scene Control
- `"activate movie mode"` → Sets up movie scene
- `"activate work mode"` → Bright lights for work
- `"activate relax mode"` → Dimmed ambient lighting
- `"activate bedtime mode"` → Minimal lighting

### 🎵 Media Control
- `"play music"` → Starts music playback
- `"pause music"` → Pauses playback
- `"set volume to 80%"` → Adjusts volume

### 🌡️ Climate Control  
- `"set temperature to 22 degrees"` → Adjusts thermostat

### 📱 Status & Information
- `"show device status"` → Lists all smart home devices
- `"show home status"` → General home overview

## 🤖 AI Chat Commands
Any command that doesn't match home automation keywords goes to AI:
- `"tell me a joke"`
- `"what's the weather?"`
- `"help me plan my day"`
- `"explain quantum physics"`

## 🔧 Advanced Setup (Optional)

### Adding Real Home Assistant
1. **Install Home Assistant:**
   ```bash
   docker run -d --name homeassistant --privileged --restart=unless-stopped \
     -e TZ=Europe/London -v /home/homeassistant:/config --network=host \
     ghcr.io/home-assistant/home-assistant:stable
   ```

2. **Get API Token:**
   - Go to: http://localhost:8123
   - Profile → Long-Lived Access Tokens → Create Token

3. **Update Home Workflow:**
   - Replace simulated responses with real Home Assistant API calls
   - Add your HA token to HTTP Request nodes

### Voice Integration
Connect to your existing voice service:
```python
# In your voice script, change the webhook URL to:
SKIPPY_URL = "http://192.168.0.229:5678/webhook/skippy/chat"
```

### Telegram Integration
Update your Telegram bot to use the new endpoint:
```python
# In your Telegram bot, change to:
SKIPPY_URL = "http://192.168.0.229:5678/webhook/skippy/chat"  
```

## 🧪 Testing & Troubleshooting

### Run Full Test Suite
```bash
python test_skippy_complete.py
# Choose option 1 for full tests
```

### Common Issues

**❌ "Connection refused"**
- Check n8n is running: http://192.168.0.229:5678
- Verify workflows are active (green toggle)

**❌ "Wrong routing"**  
- Check keyword detection in Smart Router node
- Verify Switch node conditions

**❌ "No Skippy personality"**
- Check Ollama is running: http://192.168.0.229:11434
- Verify AI prompt in Prepare AI Prompt node

**❌ "Home commands not working"**
- Test home workflow directly: http://192.168.0.229:5678/webhook/skippy-home-control
- Check Parse Home Command node logic

### Interactive Testing
```bash
python test_skippy_complete.py
# Choose option 2 for interactive mode
```

## 🎉 Success Indicators

**✅ Perfect Setup:**
- All test phases pass
- Home commands get sarcastic responses about home control
- AI commands get regular Skippy personality responses
- Responses include proper routing information

**Example Perfect Responses:**
```json
{
  "response": "Oh, you want light? How revolutionary. ✅ Lights turned ON - there, happy now, meat-sack?",
  "route": "home_automation", 
  "commandType": "lights",
  "success": true
}
```

## 🚀 Next Steps

Once working:
1. **Add real smart devices** to Home Assistant
2. **Create custom scenes** for your home
3. **Add grow room monitoring** (sensors, cameras, automation)
4. **Expand voice commands** with more natural language
5. **Add scheduling** and automation routines

## 📞 Support

If you get stuck:
1. Run the test script first
2. Check n8n execution logs  
3. Verify webhook URLs match your setup
4. Test each workflow individually

**Your Skippy will soon control your entire smart home with maximum sarcasm!** 🤖🏠