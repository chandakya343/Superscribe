# SuperScribe: Voice-to-Text Transcription Assistant

A powerful voice-to-text transcription tool that transforms your spoken words into written text exactly where your cursor is positioned.
(For windows only my friends tell me mac has something like that built in)

## Features

- **Seamless Integration**: Works with any application that accepts text input
- **Smart Transcription**: Powered by Google's Gemini API for superior accuracy
- **Keyboard Shortcut Activation**: Press Ctrl+Function to start recording, release to transcribe
- **Comprehensive History**: Maintains a searchable log of all previous transcriptions
- **Audio Management**: Saves audio recordings for reference and verification

## Setup

### Prerequisites

- Windows 10 or later
- Microphone (internal or external)
- Internet connection (for API access)
- Python 3.8+ (for development only)

### Installation

#### Option 1: Using the Executable (Recommended)

1. Download the latest release from the releases page
2. Extract the ZIP file to a location of your choice
3. Run `SuperScribe.exe`
4. The application will start and appear in the system tray

#### Option 2: From Source (Development)

1. Make sure you have Python installed on your system.

2. Clone this repository:
   ```
   git clone https://github.com/yourusername/superscribe.git
   cd superscribe
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

5. Run the application:
   ```
   python superscribe_win.py
   ```

### Building the Executable

If you want to build the executable yourself:

1. Install the requirements:
   ```
   pip install -r requirements.txt
   ```

2. Run the build script:
   ```
   python build_exe.py
   ```

3. Find the executable in the `dist` folder

## Usage

1. Start the application (it will appear in the system tray)
2. Place your cursor where you want the transcribed text to appear
3. Press and hold the Ctrl+Function keys
4. Speak clearly into your microphone
5. Release the keys when finished speaking
6. The transcribed text will appear at your cursor position

## System Tray Options

- **Show History**: View and search all previous transcriptions
- **Settings**: Configure application settings
- **Exit**: Close the application

## Privacy

All recordings are stored locally on your computer. You can:
- View your recording history in the application
- Delete recordings and transcriptions via the application interface

## Troubleshooting

- **No Transcription Appears**: Check your microphone connection and make sure you have internet access
- **Application Doesn't Start**: Verify that the `.env` file contains your valid API key
- **Poor Transcription Quality**: Speak clearly and reduce background noise

## License

MIT 
