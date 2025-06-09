H:\skippy-ai-agent\home-integration>python simple_n8n_debug.py
🧪 N8N WORKFLOW DEBUG HELPER
========================================
📤 Sending test request to: http://192.168.0.229:5678/webhook-test/skippy/chat
📦 Payload: {'message': 'turn on the lights', 'user': 'DebugTest'}

⏳ Sending request...
✅ Request sent! Status: 200
📝 Got response: {"response":"AI response error","route":"ai_chat","personality_mode":"ai_powered","model":"llama3.1:...

🔍 NOW CHECK N8N INTERFACE:
========================================
1. Go to your n8n workflow
2. Look for nodes with green checkmarks (executed)
3. Click each node and check for data:

   📋 Smart Router Node:
      • Click the node
      • Look for 'Output' or 'Data' tab
      • Should show: route, isHomeCommand, commandType

   📋 Route Switch Node:
      • Click the node
      • Check if it has ANY output data
      • If empty = condition failing
      • If has data = condition working

   📋 Next Nodes:
      • Home Automation Handler
      • AI Chat Handler
      • Check which one (if any) received data

📋 DETAILED NODE CHECKING GUIDE
========================================

After sending the test request above:

🔍 STEP 1: Check Smart Router
   • In n8n, click the 'Smart Router' node
   • Look for these tabs: Input | Output | Settings
   • Click 'Output' tab
   • You should see JSON data with these fields:
     - message: 'turn on the lights'
     - route: 'home_automation' (KEY FIELD!)
     - isHomeCommand: true
     - commandType: 'lights'

🔍 STEP 2: Check Route Switch
   • Click the 'Route Switch' node
   • Check 'Output' tab
   • CRITICAL: Is there ANY data here?
     ✅ If YES: Switch is working, data flows
     ❌ If NO: Switch condition is broken

🔍 STEP 3: Check Final Nodes
   • Look at 'Home Automation Handler' node
   • Look at 'AI Chat Handler' node
   • One of these should have data (depending on routing)

🔧 COMMON ISSUES:
   • Smart Router has no 'route' field → Fix Smart Router code
   • Route Switch has no output → Fix Switch condition
   • Both handlers empty → Switch routing is wrong

Press Enter after you've checked the nodes in n8n...