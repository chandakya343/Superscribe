import os
import time
import logging
import sys
from dotenv import load_dotenv
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import google.generativeai as genai
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("Error: GEMINI_API_KEY not found in .env file")
    logging.error("API key not found in environment variables")
    sys.exit(1)
    
genai.configure(api_key=api_key)
logging.info("Google Generative AI client initialized successfully")

class AudioFileTranscriber:
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
                
            print(f"Transcribing audio file: {audio_file} ({file_size} bytes)")
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
            print("Reading audio file...")
            with open(audio_file, "rb") as f:
                audio_data = f.read()
            
            # Create prompt and contents
            prompt = 'Generate a transcript of the speech.'
            
            # Send request and get response
            print("Sending request to Gemini API...")
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
            
            print("\n--- Transcription Result ---")
            print(transcription)
            print("---------------------------\n")
            
            logging.info(f"Transcription successful: {len(transcription)} characters")
            return transcription
            
        except Exception as e:
            error_msg = f"Error during transcription: {str(e)}"
            logging.error(f"Transcription error: {str(e)}")
            print(error_msg)
            return error_msg

class SimpleUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SuperScribe Audio Transcriber")
        self.root.geometry("800x600")
        
        self.transcriber = AudioFileTranscriber()
        self.setup_ui()
        
    def setup_ui(self):
        # Create frames
        top_frame = tk.Frame(self.root, pady=10)
        top_frame.pack(fill=tk.X)
        
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # File selection
        self.file_var = tk.StringVar(value="No file selected")
        
        file_label = tk.Label(top_frame, text="Audio File:")
        file_label.pack(side=tk.LEFT, padx=5)
        
        file_entry = tk.Entry(top_frame, textvariable=self.file_var, width=50)
        file_entry.pack(side=tk.LEFT, padx=5)
        
        browse_button = tk.Button(top_frame, text="Browse", command=self.browse_file)
        browse_button.pack(side=tk.LEFT, padx=5)
        
        transcribe_button = tk.Button(top_frame, text="Transcribe", command=self.transcribe_file)
        transcribe_button.pack(side=tk.LEFT, padx=5)
        
        # Result text area
        self.result_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=20)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def browse_file(self):
        filetypes = [
            ("Audio files", "*.wav *.mp3 *.m4a *.ogg"),
            ("WAV files", "*.wav"),
            ("MP3 files", "*.mp3"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select audio file",
            filetypes=filetypes,
            initialdir=os.path.join(os.getcwd(), "recordings")
        )
        
        if filename:
            self.file_var.set(filename)
            self.status_var.set(f"Selected file: {os.path.basename(filename)}")
        
    def transcribe_file(self):
        file_path = self.file_var.get()
        
        if not file_path or file_path == "No file selected":
            messagebox.showerror("Error", "Please select an audio file first")
            return
            
        # Clear previous results
        self.result_text.delete(1.0, tk.END)
        self.status_var.set("Transcribing...")
        self.root.update()
        
        # Transcribe the file
        try:
            start_time = time.time()
            transcription = self.transcriber.transcribe_audio_file(file_path)
            elapsed_time = time.time() - start_time
            
            # Display the result
            self.result_text.insert(tk.END, transcription)
            self.status_var.set(f"Transcription completed in {elapsed_time:.2f} seconds")
            
        except Exception as e:
            self.result_text.insert(tk.END, f"Error: {str(e)}")
            self.status_var.set("Transcription failed")

def main():
    # Use a specific file if provided as an argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        transcriber = AudioFileTranscriber()
        transcriber.transcribe_audio_file(file_path)
    else:
        # Start the GUI
        root = tk.Tk()
        app = SimpleUI(root)
        root.mainloop()

if __name__ == "__main__":
    main() 