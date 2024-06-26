import requests
from requests.auth import HTTPDigestAuth
import time
import random
import string
from onvif import ONVIFCamera
from onvif.exceptions import ONVIFError
import pyaudio
import socket
import numpy as np
import struct
import msvcrt

host = '10.253.1.141'
port = 80
username = 'ADMIN'
password = '1234'

def random_string(length=16):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def perform_request(audio_out, enable):
    timestamp = int(time.time() * 1000)
    base_url = f'http://{host}/cgi-bin/set'
    params = {
        'system.information.media_player': 'activex',
        'system.information.audio_out': audio_out,
        'system.audio_out.enable': enable,
        '_': timestamp
    }
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US, en; q=0.5',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'Keep-Alive',
        'Referer': f'http://{host}/www/index.html',
        'Host': host
    }
    session_id = random_string(36)
    cookies = {
        'def_stream': 'stream1',
        'def_rec': 'off',
        'def_zoom': 'off',
        'SESSIONID': session_id,
        'def_va': 'OFF',
        'ipcamera': 'test'
    }
    response = requests.get(base_url, params=params, headers=headers, cookies=cookies, auth=HTTPDigestAuth(username, password))
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    print(f"Response Body: {response.text}")


def is_key_pressed():
    return msvcrt.kbhit() and msvcrt.getch() == b'q'

# Connect to the camera
try:
    camera = ONVIFCamera(host, port, username, password)
    media_service = camera.create_media_service()
    profiles = media_service.GetProfiles()
    profile = profiles[0]
except ONVIFError as e:
    print(f"Error connecting to camera: {e}")
    raise

# Ensure the profile supports audio
if not profile.AudioEncoderConfiguration:
    raise ONVIFError('Profile does not support audio encoder configuration')

perform_request('on', 'on')

# Get the audio encoder configuration
audio_encoder_config = media_service.GetAudioEncoderConfiguration(
    {'ConfigurationToken': profile.AudioEncoderConfiguration.token})

print(f"Audio Encoder Configuration: {audio_encoder_config}")

# Prepare RTP streaming
rtp_port = 59191  # Destination port
source_port =  random.randint(50446,65535) 
client_ip = '10.253.0.95'  

print(f"Client IP: {client_ip}")

try:
    rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    rtp_socket.bind((client_ip, source_port))
    print(f"Socket bound to {client_ip}:{source_port}")
except socket.gaierror as e:
    print(f"Error binding socket: {e}")
    raise


def create_rtp_packet(payload, seq_num, timestamp, ssrc):
    # RTP header fields
    version = 2
    padding = 0
    extension = 0
    csrc_count = 0
    marker = 0
    payload_type = 0  # Typically, G.711 uses payload type 0 (PCMU) or 8 (PCMA)
    
    rtp_header = struct.pack('!BBHII', 
        (version << 6) | (padding << 5) | (extension << 4) | csrc_count,
        (marker << 7) | payload_type,
        seq_num,
        timestamp,
        ssrc
    )
    return rtp_header + payload

# Initialize variables
seq_num = 0
timestamp = 0
ssrc = random.randint(0, 2**32 - 1)

def send_audio_data(audio_data):
    global seq_num, timestamp

    # Ensure exactly 2036 bytes
    if len(audio_data) > 2036:
        audio_data = audio_data[:2036]  # Truncate to 2036 bytes
    elif len(audio_data) < 2036:
        audio_data += b'\x00' * (2036 - len(audio_data))  # Pad to 2036 bytes

    rtp_packet = create_rtp_packet(audio_data, seq_num, timestamp, ssrc)
    rtp_socket.sendto(rtp_packet, (host, rtp_port))
    seq_num += 1
    timestamp += 160  # 160 samples for 20ms at 8kHz
    print(f"Sending RTP packet to {host}:{rtp_port}, Size: {len(rtp_packet)} bytes")


# Set up PyAudio to capture audio from the microphone
p = pyaudio.PyAudio()

# Configuration for the audio stream
stream = p.open(format=pyaudio.paInt16, channels=1, rate=8000, input=True, frames_per_buffer=1024)

def pcm_to_g711(pcm_data):
    pcm_samples = np.frombuffer(pcm_data, dtype=np.int16)
    g711_data = np.zeros(2036, dtype=np.uint8)  # Fixed size for G.711 encoded data

    for i in range(min(len(pcm_samples), 1024)):  # Limit to 1024 samples (2036 bytes)
        pcm_val = pcm_samples[i]
        ulaw_byte = linear2ulaw(pcm_val)
        g711_data[i * 2] = ulaw_byte & 0xFF
        g711_data[i * 2 + 1] = (ulaw_byte >> 8) & 0xFF

    return g711_data.tobytes()


def linear2ulaw(pcm_val):
    pcm_val = max(min(pcm_val, 32767), -32768)
    BIAS = 0x84
    CLIP = 32635
    if pcm_val < 0:
        pcm_val = BIAS - pcm_val
        mask = 0x7F
    else:
        pcm_val += BIAS
        mask = 0xFF
    if pcm_val > CLIP:
        pcm_val = CLIP
    pcm_val += (0x84 >> 2)
    exponent = 7
    segment = 0x4000
    for exp in range(7, -1, -1):
        if pcm_val >= segment:
            exponent = exp
            break
        segment >>= 1
    mantissa = (pcm_val >> (exponent + 3)) & 0x0F
    ulaw_byte = ~(mask & ((exponent << 4) | mantissa))
    return ulaw_byte

try:
    while True:
        audio_data = stream.read(320)  # Read enough audio data to cover the G.711 encoding
        g711_audio_data = pcm_to_g711(audio_data)

        # Ensure exactly 2036 bytes
        if len(g711_audio_data) > 2048:
            g711_audio_data = g711_audio_data[:2048]  # Truncate to 2036 bytes
        elif len(g711_audio_data) < 2048:
            g711_audio_data += b'\x00' * (2048 - len(g711_audio_data))  # Pad to 2036 bytes

        print(f"G.711 Encoded Data: {len(g711_audio_data)} bytes")
        send_audio_data(g711_audio_data)
        time.sleep(0.02)  # Adjust sleep time if necessary
        
        # Check for 'Q' key press to perform request to turn off audio output
        if is_key_pressed():
            perform_request('off', 'off')
            break
        
except KeyboardInterrupt:
    stream.stop_stream()
    stream.close()
    p.terminate()
    rtp_socket.close()
    print("Streaming stopped.")
