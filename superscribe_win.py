import os
import sys
import time
import logging
import threading
import datetime
import wave
import pyaudio
import keyboard
import pyautogui
import pyperclip
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import Menu
from pystray import Icon as TrayIcon, Menu as TrayMenu, MenuItem as TrayMenuItem

# Import our icon creator
from icon import create_icon

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='superscribe.log',
    filemode='a'
)

# Log to console as well
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    logging.error("API key not found in environment variables")
    sys.exit(1)
    
genai.configure(api_key=api_key)
logging.info("Google Generative AI client initialized successfully")

class AudioRecorder:
    def __init__(self, storage_dir="recordings"):
        self.is_recording = False
        self.frames = []
        self.storage_dir = storage_dir
        self.recording_thread = None
        self.ensure_storage_dir()
        
        # Audio parameters
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.chunk = 1024
        
        try:
            self.audio = pyaudio.PyAudio()
            self.device_index = self.get_input_device_index()
            if self.device_index is None:
                logging.error("No suitable input device found")
                raise ValueError("No suitable input device found. Please check your microphone connection.")
        except Exception as e:
            logging.error(f"Failed to initialize PyAudio: {str(e)}")
            self.audio = None
            raise ValueError(f"Audio initialization failed: {str(e)}")
    
    def ensure_storage_dir(self):
        """Ensure the storage directory exists"""
        Path(self.storage_dir).mkdir(parents=True, exist_ok=True)
    
    def get_input_device_index(self):
        """Find a suitable input device"""
        info = self.audio.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        # Log all available devices for debugging
        for i in range(num_devices):
            device_info = self.audio.get_device_info_by_index(i)
            logging.info(f"Device {i}: {device_info.get('name')}, Input channels: {device_info.get('maxInputChannels')}")
        
        # Try to find a suitable input device
        for i in range(num_devices):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info.get('maxInputChannels') > 0:
                logging.info(f"Selected input device: {device_info.get('name')}")
                return i
                
        return None
        
    def start_recording(self):
        """Start recording audio from microphone"""
        if self.audio is None:
            logging.error("Cannot start recording - PyAudio not initialized")
            return False
            
        try:
            self.frames = []
            self.is_recording = True
            
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk
            )
            
            logging.info(f"Recording started with device index {self.device_index}")
            
            # Start recording in a separate thread
            self.recording_thread = threading.Thread(target=self._record)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            return True
        except Exception as e:
            self.is_recording = False
            logging.error(f"Failed to start recording: {str(e)}")
            return False
        
    def _record(self):
        """Record audio from microphone"""
        try:
            while self.is_recording:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.frames.append(data)
        except Exception as e:
            logging.error(f"Error during recording: {str(e)}")
            self.is_recording = False
            
    def stop_recording(self):
        """Stop recording and save the audio file"""
        if not self.is_recording or self.audio is None:
            return None
            
        self.is_recording = False
        
        try:
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=2.0)
                
            if hasattr(self, 'stream') and self.stream:
                self.stream.stop_stream()
                self.stream.close()
            
            logging.info("Recording stopped")
            
            if not self.frames:
                logging.warning("No audio data captured")
                return None
                
            # Generate filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.storage_dir, f"recording_{timestamp}.wav")
            
            # Save recording to WAV file
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.frames))
                
            logging.info(f"Recording saved to {filename}")
            return filename
        except Exception as e:
            logging.error(f"Error stopping recording: {str(e)}")
            return None

    def __del__(self):
        """Clean up audio resources"""
        if hasattr(self, 'audio') and self.audio:
            self.audio.terminate()

class TranscriptionService:
    def __init__(self):
        self.model = "gemini-2.0-flash"
        
    def transcribe_audio_file(self, audio_file):
        """Transcribe a specific audio file using Google Gemini API"""
        try:
            # Check if file exists
            if not os.path.exists(audio_file):
                error_msg = f"Error: Audio file not found: {audio_file}"
                logging.error(error_msg)
                return error_msg
                
            # Check file size
            file_size = os.path.getsize(audio_file)
            if file_size == 0:
                error_msg = "Error: Audio file is empty"
                logging.error(error_msg)
                return error_msg
                
            logging.info(f"Transcribing audio file: {audio_file} ({file_size} bytes)")
            
            # Determine the MIME type based on file extension
            mime_type = "audio/wav"  # Default
            if audio_file.lower().endswith('.mp3'):
                mime_type = "audio/mpeg"
            elif audio_file.lower().endswith('.wav'):
                mime_type = "audio/wav"
            elif audio_file.lower().endswith('.m4a'):
                mime_type = "audio/mp4"
            elif audio_file.lower().endswith('.ogg'):
                mime_type = "audio/ogg"
                
            # Create model
            model = genai.GenerativeModel(model_name=self.model)
            
            # Read audio file data
            with open(audio_file, "rb") as f:
                audio_data = f.read()
            
            # Create prompt and contents
            prompt = 'Generate a transcript of the speech.'
            
            # Send request and get response
            logging.info("Sending request to Gemini API")
            
            response = model.generate_content(
                contents=[
                    prompt,
                    {"mime_type": mime_type, "data": audio_data}
                ]
            )
            
            # Check response
            if not response or not hasattr(response, 'text'):
                error_msg = "Error: Received invalid response from Gemini API"
                logging.error(error_msg)
                return error_msg
            
            transcription = response.text
            
            logging.info(f"Transcription successful: {len(transcription)} characters")
            return transcription
            
        except Exception as e:
            error_msg = f"Error during transcription: {str(e)}"
            logging.error(f"Transcription error: {str(e)}")
            return error_msg

class SuperScribeApp:
    def __init__(self):
        self.recorder = AudioRecorder()
        self.transcriber = TranscriptionService()
        self.recording = False
        self.history = []
        self.settings = {
            'hotkey': 'ctrl+function',  # Default hotkey
            'auto_start': False,
            'save_recordings': True
        }
        
        # Setup the application
        self.setup_keyboard_hooks()
        self.create_tray_icon()
        
    def setup_keyboard_hooks(self):
        # Configure the keyboard hook for recording
        keyboard.add_hotkey('ctrl+function', self.on_hotkey_pressed, trigger_on_release=False)
        keyboard.add_hotkey('ctrl+function', self.on_hotkey_released, trigger_on_release=True)
        
    def on_hotkey_pressed(self):
        """Start recording when hotkey is pressed"""
        if not self.recording:
            self.recording = True
            logging.info("Hotkey pressed - starting recording")
            self.recorder.start_recording()
            
    def on_hotkey_released(self):
        """Stop recording and process when hotkey is released"""
        if self.recording:
            self.recording = False
            logging.info("Hotkey released - stopping recording")
            
            # Stop recording and get the saved file
            audio_file = self.recorder.stop_recording()
            
            if audio_file:
                # Transcribe the audio
                transcription = self.transcriber.transcribe_audio_file(audio_file)
                
                if transcription and not transcription.startswith("Error:"):
                    # Copy transcription to clipboard and paste at cursor position
                    self.paste_text_at_cursor(transcription)
                    
                    # Add to history
                    self.history.append({
                        'timestamp': datetime.datetime.now(),
                        'audio_file': audio_file,
                        'transcription': transcription
                    })
                    
                    # Show notification
                    self.tray_icon.notify(
                        "SuperScribe", 
                        "Transcription completed and pasted at cursor position"
                    )
                else:
                    logging.error(f"Transcription failed: {transcription}")
                    self.tray_icon.notify(
                        "SuperScribe", 
                        "Transcription failed. Check log for details."
                    )
            else:
                logging.error("No audio file created")
                self.tray_icon.notify(
                    "SuperScribe", 
                    "Recording failed. Check microphone connection."
                )
                
    def paste_text_at_cursor(self, text):
        """Paste the transcribed text at current cursor position"""
        try:
            # Copy text to clipboard
            pyperclip.copy(text)
            
            # Simulate Ctrl+V to paste
            pyautogui.hotkey('ctrl', 'v')
            
            logging.info("Text pasted at cursor position")
        except Exception as e:
            logging.error(f"Error pasting text: {str(e)}")
    
    def create_tray_icon(self):
        """Create system tray icon and menu"""
        # Create a custom icon
        icon_path = create_icon()
        icon_image = Image.open(icon_path)
        
        # Create system tray icon
        self.tray_icon = TrayIcon(
            'superscribe',
            icon_image,
            'SuperScribe',
            menu=TrayMenu(
                TrayMenuItem('Show History', self.show_history),
                TrayMenuItem('Settings', self.show_settings),
                TrayMenuItem('Exit', self.exit_app)
            )
        )
    
    def start(self):
        """Start the application"""
        logging.info("Starting SuperScribe")
        self.tray_icon.run()
    
    def show_history(self, _=None):
        """Show transcription history"""
        history_window = tk.Toplevel()
        history_window.title("SuperScribe - Transcription History")
        history_window.geometry("800x600")
        
        # Create a frame for the history list
        list_frame = tk.Frame(history_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add a scrollable text widget to display history
        history_text = tk.Text(list_frame, wrap=tk.WORD)
        history_scroll = tk.Scrollbar(list_frame, command=history_text.yview)
        history_text.configure(yscrollcommand=history_scroll.set)
        
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Populate the history
        if self.history:
            for entry in reversed(self.history):
                timestamp = entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                history_text.insert(tk.END, f"--- {timestamp} ---\n")
                history_text.insert(tk.END, entry['transcription'] + "\n\n")
        else:
            history_text.insert(tk.END, "No transcription history yet.")
        
        # Make the text read-only
        history_text.configure(state=tk.DISABLED)
    
    def show_settings(self, _=None):
        """Show settings dialog"""
        settings_window = tk.Toplevel()
        settings_window.title("SuperScribe - Settings")
        settings_window.geometry("400x300")
        settings_window.resizable(False, False)
        
        # Add settings controls
        tk.Label(settings_window, text="Settings", font=("Helvetica", 16)).pack(pady=10)
        
        # Hotkey setting (placeholder - not functional in this basic version)
        tk.Label(settings_window, text="Hotkey: ctrl+function").pack(anchor="w", padx=20, pady=5)
        
        # Auto-start with Windows
        auto_start_var = tk.BooleanVar(value=self.settings['auto_start'])
        auto_start_cb = tk.Checkbutton(settings_window, text="Start with Windows", variable=auto_start_var)
        auto_start_cb.pack(anchor="w", padx=20, pady=5)
        
        # Save recordings
        save_rec_var = tk.BooleanVar(value=self.settings['save_recordings'])
        save_rec_cb = tk.Checkbutton(settings_window, text="Save audio recordings", variable=save_rec_var)
        save_rec_cb.pack(anchor="w", padx=20, pady=5)
        
        # Save button
        def save_settings():
            self.settings['auto_start'] = auto_start_var.get()
            self.settings['save_recordings'] = save_rec_var.get()
            settings_window.destroy()
            
        tk.Button(settings_window, text="Save", command=save_settings).pack(pady=20)
    
    def exit_app(self, _=None):
        """Exit the application"""
        logging.info("Exiting SuperScribe")
        try:
            self.tray_icon.stop()
        except Exception:
            pass
        sys.exit(0)

def main():
    try:
        app = SuperScribeApp()
        app.start()
    except Exception as e:
        logging.error(f"Error starting SuperScribe: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 