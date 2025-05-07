# Raspberry Pi Pose Estimation System

This project implements a real-time pose estimation system using a Raspberry Pi. The system captures video, detects human poses using MediaPipe, communicates with a backend server, and provides feedback through a speaker.

## Features

- **Real-time pose detection** using MediaPipe
- **WebRTC video streaming** to mobile clients
- **Bluetooth Low Energy (BLE)** communication for device discovery
- **WebSocket communication** with backend server for AI processing
- **Audio feedback** using text-to-speech

## System Components

1. **Camera Management** - Captures video frames and extracts pose keypoints
2. **Backend Server Communication** - Sends pose data to backend AI service
3. **Mobile Connection** - Streams video to mobile clients using WebRTC
4. **Bluetooth Discovery** - Allows mobile clients to discover the device's IP address
5. **Audio Feedback** - Text-to-speech announcements based on AI responses

## Directory Structure

```
├── backend/                # Backend server communication
│   ├── app.py              # Main FastAPI application
│   ├── websocket_backend.py # WebSocket client for AI backend
│   └── connect_backend.py  # Connection utilities
├── iot/                    # IoT device components
│   ├── camera_manager.py   # Camera and video processing
│   ├── get_keypoints.py    # Pose estimation using MediaPipe
│   ├── draw.py             # Visualization utilities
│   └── speaker.py          # Audio feedback system
├── mobile/                 # Mobile client communication
│   └── webrtc_handler.py   # WebRTC implementation for video streaming
├── my_bluetooth/           # Bluetooth communication
│   └── ble_connection.py   # BLE peripheral implementation
├── data/                   # Video samples and output
├── cache/                  # Temporary cache files
└── requirements.txt        # Python dependencies
```

## Getting Started

### Prerequisites

- Raspberry Pi (3 or newer recommended)
- Python 3.9+
- Camera (USB or Raspberry Pi Camera)
- Speaker or headphones
- Bluetooth capability

### Installation

1. Clone the repository:
   ```
   git clone [repository-url]
   cd Raspberry
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Linux/Mac
   # or
   .venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure the backend server connection in `backend/websocket_backend.py`

### Running the Application

Start the main application:
```
python backend/app.py
```

## Configuration

- Update the `domain` and `path` variables in `backend/websocket_backend.py` to point to your backend server
- Adjust camera settings in `iot/camera_manager.py` for your specific camera setup
- Modify BLE settings in `my_bluetooth/ble_connection.py` if needed
