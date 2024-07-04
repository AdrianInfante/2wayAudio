# Audio Streaming to ONVIF Camera

This project allows you to stream audio from your microphone to an ONVIF-compatible IP camera using RTP (Real-time Transport Protocol). It sets up the camera to enable audio output and handles audio capture, encoding, and transmission in real-time. 

## Features
- Connects to an ONVIF camera and configures it for audio streaming.
- Captures audio from the microphone.
- Sends audio data over RTP to the camera.
- Allows toggling audio output on the camera via HTTP requests.

## Prerequisites
Before running this script, ensure you have the following prerequisites installed:
- Python 3.x
- `requests`
- `onvif-zeep`
- `pyaudio`
- `numpy`
- `msvcrt` (Windows only, used for keyboard input detection)

You can install the necessary packages using `pip`:
```sh
pip install requests onvif-zeep pyaudio numpy
```

## Configuration
Update the following configuration variables in the script as per your setup:
- `host`: IP address of the ONVIF camera.
- `port`: Port number for the ONVIF camera (usually 80).
- `username`: Username for the camera.
- `password`: Password for the camera.
- `client_ip`: IP address of the client machine from which you are running the script.

## Usage
1. Ensure the ONVIF camera is connected and accessible over the network.
2. Run the script:
   ```sh
   python audio_streaming_to_onvif_camera.py
   ```
3. The script will:
   - Connect to the camera and configure it for audio streaming.
   - Capture audio from the microphone.
   - Send the encoded audio data to the camera via RTP.


## Notes
- The script uses the `msvcrt` module for detecting keyboard input, which is specific to Windows. Modify this part if running on a different operating system.
- Adjust the sleep time in the main loop (`time.sleep(0.02)`) if necessary to match the audio capture rate and transmission timing.

