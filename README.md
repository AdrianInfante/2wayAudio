# Audio Streaming to ONVIF Camera

This project allows you to stream audio from your microphone to an ONVIF-compatible IP camera using RTP (Real-time Transport Protocol). It sets up the camera to enable audio output and handles audio capture, encoding, and transmission in real-time. 

## Features
- Connects to an ONVIF camera and configures it for audio streaming.
- Captures audio from the microphone.
- Encodes audio data to G.711 format.(Disabled)
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
   - Encode the audio to G.711 format. (Disabled)
   - Send the encoded audio data to the camera via RTP.

## Functions Overview
### `random_string(length=16)`
Generates a random string of specified length.

### `perform_request(audio_out, enable)`
Performs an HTTP request to the camera to enable or disable audio output.

### `is_key_pressed()`
Checks if the 'Q' key is pressed. (Disabled)

### `create_rtp_packet(payload, seq_num, timestamp, ssrc)`
Creates an RTP packet with the given payload, sequence number, timestamp, and SSRC.

### `send_audio_data(audio_data)`
Sends the audio data to the camera using RTP.

### `pcm_to_g711(pcm_data)`
Converts PCM audio data to G.711 format. (Disabled)

### `linear2ulaw(pcm_val)`
Converts a linear PCM value to u-law.

## Error Handling
The script handles common errors such as connection issues with the camera and socket binding errors. Ensure the camera's credentials and IP address are correct, and that the specified ports are open and available.

## Notes
- The script uses the `msvcrt` module for detecting keyboard input, which is specific to Windows. Modify this part if running on a different operating system.
- Adjust the sleep time in the main loop (`time.sleep(0.02)`) if necessary to match the audio capture rate and transmission timing.

