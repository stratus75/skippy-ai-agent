#!/usr/bin/env python3
"""
Skippy Home Automation Hub
Controls smart home devices with Skippy's personality
"""

import json
import requests
import asyncio
import logging
from datetime import datetime, time
import socket
import subprocess
import platform
import threading
import time as time_module

# Smart home integrations
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("⚠️  MQTT not available - install with: pip install paho-mqtt")

try:
    from phue import Bridge
    PHILIPS_HUE_AVAILABLE = True
except ImportError:
    PHILIPS_HUE_AVAILABLE = False
    print("⚠️  Philips Hue not available - install with: pip install phue")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SkippyHomeAutomation:
    def __init__(self):
        self.devices = {}
        self.scenes = {}
        self.automations = {}
        
        # Initialize integrations
        self.hue_bridge = None
        self.mqtt_client = None
        
        # Device discovery
        self.discover_devices()
        
        logger.info("Skippy Home Automation initialized")
    
    def discover_devices(self):
        """Discover smart home devices on network"""
        print("🔍 Discovering smart home devices...")
        
        # Quick option to skip Hue discovery
        print("🤔 Skip Hue discovery for faster startup? (y/n)")
        skip_hue = input("Skip Hue? [y/n]: ").strip().lower()
        
        if skip_hue != 'y':
            # Discover Philips Hue
            if PHILIPS_HUE_AVAILABLE:
                self.discover_hue_bridge()
        else:
            print("⏭️  Skipping Hue discovery")
        
        # Add virtual/mock devices for testing if no real devices found
        if len(self.devices) == 0:
            print("🔧 No physical devices found - adding virtual devices for testing")
            self.add_virtual_devices()
        
        # Discover other devices
        self.discover_network_devices()
        
        print(f"✅ Found {len(self.devices)} devices")
    
    def add_virtual_devices(self):
        """Add virtual devices for testing when no physical devices available"""
        virtual_devices = {
            'virtual_living_room_light': {
                'type': 'light',
                'name': 'Living Room Light',
                'platform': 'virtual',
                'state': 'off',
                'brightness': 100,
                'color': 'white',
                'capabilities': ['on_off', 'brightness', 'color']
            },
            'virtual_bedroom_light': {
                'type': 'light', 
                'name': 'Bedroom Light',
                'platform': 'virtual',
                'state': 'off',
                'brightness': 80,
                'color': 'white',
                'capabilities': ['on_off', 'brightness', 'color']
            },
            'virtual_music_player': {
                'type': 'media',
                'name': 'Virtual Music Player',
                'platform': 'virtual',
                'state': 'stopped',
                'volume': 50,
                'capabilities': ['play', 'pause', 'volume']
            }
        }
        
        self.devices.update(virtual_devices)
        print(f"🔧 Added {len(virtual_devices)} virtual devices for testing")
    
    def discover_hue_bridge(self):
        """Discover and connect to Philips Hue bridge with timeout"""
        try:
            print("🔍 Looking for Philips Hue bridge...")
            
            # Quick network scan with timeout
            import socket
            import threading
            
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            network_base = '.'.join(local_ip.split('.')[:-1])
            
            print(f"🔍 Scanning network {network_base}.1-20 (quick scan)...")
            
            found_bridges = []
            scan_timeout = 5  # 5 second timeout
            
            def check_ip(ip):
                try:
                    # Quick HTTP check for Hue bridge
                    import urllib.request
                    url = f"http://{ip}/api/config"
                    req = urllib.request.Request(url, headers={'User-Agent': 'SkippyHome'})
                    response = urllib.request.urlopen(req, timeout=2)
                    data = json.loads(response.read().decode())
                    
                    # Check if it's a Hue bridge
                    if 'bridgeid' in data and 'name' in data:
                        found_bridges.append(ip)
                        print(f"🌈 Found Hue bridge at {ip}")
                        
                except:
                    pass  # Not a Hue bridge or unreachable
            
            # Scan first 20 IPs only with threading for speed
            threads = []
            for i in range(1, 21):  # Only scan .1 to .20
                ip = f"{network_base}.{i}"
                if ip != local_ip:
                    thread = threading.Thread(target=check_ip, args=(ip,))
                    thread.daemon = True
                    thread.start()
                    threads.append(thread)
            
            # Wait for scan to complete or timeout
            start_time = time.time()
            for thread in threads:
                remaining_time = scan_timeout - (time.time() - start_time)
                if remaining_time > 0:
                    thread.join(timeout=remaining_time)
                else:
                    break
            
            print(f"🔍 Network scan completed in {time.time() - start_time:.1f} seconds")
            
            if found_bridges:
                bridge_ip = found_bridges[0]
                print(f"🌈 Connecting to Hue bridge at {bridge_ip}")
                
                self.hue_bridge = Bridge(bridge_ip)
                
                # Try to connect (may need button press on first run)
                try:
                    self.hue_bridge.connect()
                    lights = self.hue_bridge.lights
                    
                    for light in lights:
                        self.devices[f"hue_{light.name.lower().replace(' ', '_')}"] = {
                            'type': 'light',
                            'name': light.name,
                            'platform': 'hue',
                            'device': light,
                            'capabilities': ['on_off', 'brightness', 'color']
                        }
                    
                    print(f"✅ Connected to Hue bridge - {len(lights)} lights found")
                    
                except Exception as e:
                    print(f"⚠️  Hue bridge found but connection failed: {e}")
                    print("💡 Press the button on your Hue bridge and run again")
            else:
                print("❌ No Hue bridge found on local network")
                    
        except Exception as e:
            print(f"❌ Hue discovery error: {e}")
        
        print("✅ Hue discovery completed")
    
    def discover_network_devices(self):
        """Discover other smart devices on network"""
        print("🔍 Scanning network for smart devices...")
        
        # Common smart device ports and signatures
        device_signatures = {
            80: ['smart', 'iot', 'device'],
            8080: ['web', 'interface'],
            1883: ['mqtt', 'broker'],
            502: ['modbus'],
            6053: ['homekit']
        }
        
        # Get local network range
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        network_base = '.'.join(local_ip.split('.')[:-1])
        
        found_devices = []
        
        # Quick scan of common IPs (in a real implementation, use threading)
        for i in range(1, 5):  # Just scan a few IPs as example
            ip = f"{network_base}.{i}"
            if ip != local_ip:
                for port in [80, 8080]:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        result = sock.connect_ex((ip, port))
                        if result == 0:
                            found_devices.append({'ip': ip, 'port': port})
                        sock.close()
                    except:
                        pass
        
        # Add discovered devices (simplified)
        for device in found_devices:
            device_id = f"network_device_{device['ip'].replace('.', '_')}"
            self.devices[device_id] = {
                'type': 'unknown',
                'name': f"Device at {device['ip']}",
                'platform': 'network',
                'ip': device['ip'],
                'port': device['port'],
                'capabilities': ['unknown']
            }
    
    def setup_mqtt(self, broker_host="localhost", broker_port=1883):
        """Setup MQTT for Home Assistant / other platforms"""
        if not MQTT_AVAILABLE:
            print("❌ MQTT not available")
            return False
        
        try:
            self.mqtt_client = mqtt.Client("skippy_home_automation")
            
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    print("✅ Connected to MQTT broker")
                    # Subscribe to device topics
                    client.subscribe("homeassistant/+/+/state")
                    client.subscribe("skippy/command/+")
                else:
                    print(f"❌ MQTT connection failed: {rc}")
            
            def on_message(client, userdata, msg):
                try:
                    topic = msg.topic
                    payload = msg.payload.decode()
                    print(f"📨 MQTT: {topic} = {payload}")
                    
                    # Handle Skippy commands
                    if topic.startswith("skippy/command/"):
                        self.handle_mqtt_command(topic, payload)
                        
                except Exception as e:
                    logger.error(f"MQTT message error: {e}")
            
            self.mqtt_client.on_connect = on_connect
            self.mqtt_client.on_message = on_message
            
            self.mqtt_client.connect(broker_host, broker_port, 60)
            self.mqtt_client.loop_start()
            
            return True
            
        except Exception as e:
            print(f"❌ MQTT setup failed: {e}")
            return False
    
    def handle_mqtt_command(self, topic, payload):
        """Handle MQTT commands for Skippy"""
        try:
            command_parts = topic.split('/')
            if len(command_parts) >= 3:
                device_name = command_parts[2]
                command_data = json.loads(payload)
                
                print(f"🎛️  MQTT Command: {device_name} = {command_data}")
                # Process command...
                
        except Exception as e:
            logger.error(f"MQTT command error: {e}")
    
    # === DEVICE CONTROL METHODS ===
    
    def control_lights(self, command, target="all", **kwargs):
        """Control smart lights"""
        try:
            # Find light devices (both real and virtual)
            light_devices = {k: v for k, v in self.devices.items() if v['type'] == 'light'}
            
            if not light_devices:
                return "❌ No lights found. Connect smart lights or use virtual mode."
            
            # Determine target lights
            target_lights = []
            
            if target.lower() == "all":
                target_lights = list(light_devices.keys())
            else:
                # Find specific lights
                for device_id, device in light_devices.items():
                    if target.lower() in device['name'].lower():
                        target_lights.append(device_id)
            
            if not target_lights:
                return f"❌ No lights found matching '{target}'"
            
            results = []
            
            for light_id in target_lights:
                device = self.devices[light_id]
                
                if device['platform'] == 'hue' and self.hue_bridge:
                    # Real Hue light control
                    light = device['device']
                    
                    if command == "on":
                        light.on = True
                        device['state'] = 'on'
                        results.append(f"✅ {device['name']} turned on")
                        
                    elif command == "off":
                        light.on = False
                        device['state'] = 'off'
                        results.append(f"✅ {device['name']} turned off")
                        
                    elif command == "brightness":
                        brightness = kwargs.get('level', 50)
                        light.brightness = min(254, max(1, int(brightness * 2.54)))
                        device['brightness'] = brightness
                        results.append(f"✅ {device['name']} brightness set to {brightness}%")
                        
                    elif command == "color":
                        color_name = kwargs.get('color', 'white')
                        color_map = {
                            'red': [0.7, 0.3], 'blue': [0.1, 0.1], 'green': [0.3, 0.6],
                            'yellow': [0.5, 0.5], 'purple': [0.3, 0.1], 'white': [0.3, 0.3]
                        }
                        
                        if color_name in color_map:
                            light.xy = color_map[color_name]
                            device['color'] = color_name
                            results.append(f"✅ {device['name']} color set to {color_name}")
                        else:
                            results.append(f"❌ Unknown color: {color_name}")
                
                else:
                    # Virtual device control
                    if command == "on":
                        device['state'] = 'on'
                        results.append(f"✅ {device['name']} (virtual) turned on")
                        
                    elif command == "off":
                        device['state'] = 'off'
                        results.append(f"✅ {device['name']} (virtual) turned off")
                        
                    elif command == "brightness":
                        brightness = kwargs.get('level', 50)
                        device['brightness'] = brightness
                        results.append(f"✅ {device['name']} (virtual) brightness set to {brightness}%")
                        
                    elif command == "color":
                        color_name = kwargs.get('color', 'white')
                        device['color'] = color_name
                        results.append(f"✅ {device['name']} (virtual) color set to {color_name}")
            
            return "\n".join(results)
            
        except Exception as e:
            return f"❌ Light control error: {e}"
    
    def control_music(self, command, **kwargs):
        """Control music/media"""
        try:
            if platform.system() == "Windows":
                if command == "play":
                    # Use Windows media controls
                    subprocess.run(['powershell', '-Command', 
                                  'Add-Type -AssemblyName System.Windows.Forms; '
                                  '[System.Windows.Forms.SendKeys]::SendWait("{MEDIA_PLAY_PAUSE}")'])
                    return "🎵 Music playback toggled"
                    
                elif command == "volume":
                    level = kwargs.get('level', 50)
                    # Use a simpler volume control method for Windows
                    try:
                        # Try the COM method first
                        subprocess.run(['powershell', '-Command', 
                                      f'(New-Object -comObject WScript.Shell).SendKeys([char]174)'])  # Volume down key
                        return f"🔊 Volume adjusted (Windows media keys)"
                    except:
                        # Fallback to nircmd if available
                        try:
                            subprocess.run(['nircmd.exe', 'setsysvolume', str(int(level * 655.35))], 
                                         check=True, capture_output=True)
                            return f"🔊 Volume set to {level}%"
                        except:
                            return f"🔊 Volume control attempted - may need additional software"
                    
            elif platform.system() == "Linux":
                if command == "play":
                    subprocess.run(['playerctl', 'play-pause'])
                    return "🎵 Music playback toggled"
                elif command == "volume":
                    level = kwargs.get('level', 50)
                    subprocess.run(['amixer', 'set', 'Master', f'{level}%'])
                    return f"🔊 Volume set to {level}%"
            
            return "❌ Media control limited on this platform"
            
        except Exception as e:
            return f"⚠️ Media control attempted: {e}"
    
    def get_device_status(self, device_name=None):
        """Get status of devices"""
        if device_name:
            if device_name in self.devices:
                device = self.devices[device_name]
                return f"📱 {device['name']}: {device['type']} ({device['platform']})"
            else:
                return f"❌ Device '{device_name}' not found"
        else:
            if not self.devices:
                return "❌ No devices discovered yet"
            
            status = "📱 **SMART HOME STATUS**\n\n"
            
            by_type = {}
            for device_id, device in self.devices.items():
                device_type = device['type']
                if device_type not in by_type:
                    by_type[device_type] = []
                by_type[device_type].append(device)
            
            for device_type, devices in by_type.items():
                status += f"**{device_type.title()}s ({len(devices)}):**\n"
                for device in devices:
                    status += f"  • {device['name']} ({device['platform']})\n"
                status += "\n"
            
            return status
    
    def create_scene(self, scene_name, actions):
        """Create automation scenes"""
        self.scenes[scene_name] = {
            'name': scene_name,
            'actions': actions,
            'created': datetime.now().isoformat()
        }
        
        return f"✅ Scene '{scene_name}' created with {len(actions)} actions"
    
    def activate_scene(self, scene_name):
        """Activate a scene"""
        if scene_name not in self.scenes:
            return f"❌ Scene '{scene_name}' not found"
        
        scene = self.scenes[scene_name]
        results = []
        
        for action in scene['actions']:
            try:
                if action['type'] == 'light':
                    result = self.control_lights(
                        action['command'], 
                        action.get('target', 'all'),
                        **action.get('params', {})
                    )
                    results.append(result)
                    
                elif action['type'] == 'music':
                    result = self.control_music(
                        action['command'],
                        **action.get('params', {})
                    )
                    results.append(result)
                    
            except Exception as e:
                results.append(f"❌ Action failed: {e}")
        
        return f"🎬 Scene '{scene_name}' activated:\n" + "\n".join(results)
    
    # === SKIPPY INTEGRATION ===
    
    def process_home_command(self, message):
        """Process home automation commands from Skippy"""
        message_lower = message.lower()
        
        # Light commands
        if any(word in message_lower for word in ['light', 'lights', 'lamp', 'bulb']):
            if 'on' in message_lower or 'turn on' in message_lower:
                return self.control_lights('on')
            elif 'off' in message_lower or 'turn off' in message_lower:
                return self.control_lights('off')
            elif 'dim' in message_lower or 'brightness' in message_lower:
                # Extract brightness level if mentioned
                import re
                brightness_match = re.search(r'(\d+)%?', message)
                level = int(brightness_match.group(1)) if brightness_match else 50
                return self.control_lights('brightness', level=level)
            elif any(color in message_lower for color in ['red', 'blue', 'green', 'yellow', 'purple', 'white']):
                for color in ['red', 'blue', 'green', 'yellow', 'purple', 'white']:
                    if color in message_lower:
                        return self.control_lights('color', color=color)
        
        # Music commands
        elif any(word in message_lower for word in ['music', 'play', 'song', 'audio', 'sound']):
            if 'play' in message_lower or 'start' in message_lower:
                return self.control_music('play')
            elif 'volume' in message_lower:
                import re
                volume_match = re.search(r'(\d+)%?', message)
                level = int(volume_match.group(1)) if volume_match else 50
                return self.control_music('volume', level=level)
        
        # Scene commands
        elif any(word in message_lower for word in ['scene', 'mood', 'setting']):
            if 'movie' in message_lower or 'cinema' in message_lower:
                return self.activate_scene('movie_mode')
            elif 'relax' in message_lower or 'chill' in message_lower:
                return self.activate_scene('relax_mode')
            elif 'work' in message_lower or 'focus' in message_lower:
                return self.activate_scene('work_mode')
        
        # Status commands
        elif any(word in message_lower for word in ['status', 'devices', 'home']):
            return self.get_device_status()
        
        return None  # No home automation command detected
    
    def setup_default_scenes(self):
        """Setup some default automation scenes"""
        
        # Movie mode
        movie_actions = [
            {'type': 'light', 'command': 'brightness', 'params': {'level': 20}},
            {'type': 'light', 'command': 'color', 'params': {'color': 'blue'}},
            {'type': 'music', 'command': 'volume', 'params': {'level': 70}}
        ]
        self.create_scene('movie_mode', movie_actions)
        
        # Relax mode
        relax_actions = [
            {'type': 'light', 'command': 'brightness', 'params': {'level': 60}},
            {'type': 'light', 'command': 'color', 'params': {'color': 'yellow'}},
            {'type': 'music', 'command': 'volume', 'params': {'level': 40}}
        ]
        self.create_scene('relax_mode', relax_actions)
        
        # Work mode
        work_actions = [
            {'type': 'light', 'command': 'on'},
            {'type': 'light', 'command': 'color', 'params': {'color': 'white'}},
            {'type': 'light', 'command': 'brightness', 'params': {'level': 90}}
        ]
        self.create_scene('work_mode', work_actions)
        
        print("✅ Default scenes created: movie_mode, relax_mode, work_mode")

def main():
    """Test the home automation system"""
    print("🏠 SKIPPY HOME AUTOMATION")
    print("=" * 40)
    
    # Initialize system
    home = SkippyHomeAutomation()
    
    # Setup default scenes
    home.setup_default_scenes()
    
    # Test commands
    print("\n🧪 Testing Commands:")
    
    # Test device status
    print("\n📱 Device Status:")
    print(home.get_device_status())
    
    # Test light control
    print("\n💡 Testing Light Control:")
    print(home.control_lights('on'))
    
    # Test scene activation
    print("\n🎬 Testing Scene:")
    print(home.activate_scene('relax_mode'))
    
    # Interactive mode
    print("\n" + "=" * 40)
    print("Interactive Mode - Type commands or 'quit':")
    print("Examples:")
    print("  - turn on the lights")
    print("  - set lights to red")
    print("  - activate movie mode")
    print("  - show device status")
    
    while True:
        try:
            command = input("\n🏠 Command: ").strip()
            
            if command.lower() in ['quit', 'exit', 'q']:
                break
            
            result = home.process_home_command(command)
            if result:
                print(f"✅ {result}")
            else:
                print("❓ Command not recognized. Try:")
                print("   - light/music/scene commands")
                print("   - 'status' for device info")
                
        except KeyboardInterrupt:
            break
    
    print("\n👋 Skippy Home Automation stopped")

if __name__ == "__main__":
    main()