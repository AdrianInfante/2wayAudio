import tkinter as tk
from threading import Thread
from tkinter import PhotoImage
import requests
from requests.auth import HTTPDigestAuth
import time
import random
import string
from onvif import ONVIFCamera
from onvif.exceptions import ONVIFError
import pyaudio
import socket
import struct
import queue

# Constants
host = '77.164.63.63'
port = 80
username = 'ADMIN'
password = 'Vicon135!'
client_ip = '10.253.0.95'  # Replace with your PC's IP address


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
        'Host': host,
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


def create_rtp_packet(payload, seq_num, timestamp, ssrc):
    version = 2
    padding = 0
    extension = 0
    csrc_count = 0
    marker = 0
    payload_type = 10  # 10 is for L16, which is linear PCM
    
    rtp_header = struct.pack('!BBHII', 
        (version << 6) | (padding << 5) | (extension << 4) | csrc_count,
        (marker << 7) | payload_type,
        seq_num,
        timestamp,
        ssrc
    )
    return rtp_header + payload

import threading

def audio_streaming():
    global streaming
    stream = None  # Initialize stream to None
    rtp_socket = None  # Initialize RTP socket to None
    p = None  # Initialize PyAudio instance to None
    try:
        # Connect to the camera
        camera = ONVIFCamera(host, port, username, password)
        media_service = camera.create_media_service()
        profiles = media_service.GetProfiles()
        profile = profiles[0]
        
        # Ensure the profile supports audio
        if not profile.AudioEncoderConfiguration:
            raise ONVIFError('Profile does not support audio encoder configuration')
        
        # Get the audio encoder configuration
        audio_encoder_config = media_service.GetAudioEncoderConfiguration(
            {'ConfigurationToken': profile.AudioEncoderConfiguration.token})
        
        print(f"Audio Encoder Configuration: {audio_encoder_config}")
        
        rtp_port = 59191  # Destination port
        source_port = random.randint(50446, 65535)  # Source port
        
        print(f"Client IP: {client_ip}")
        
        try:
            rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            rtp_socket.bind((client_ip, source_port))
            print(f"Socket bound to {client_ip}:{source_port}")
        except socket.gaierror as e:
            print(f"Error binding socket: {e}")
            raise
        
        p = pyaudio.PyAudio()
        
        buffer_size = 1024
        format_audio = pyaudio.paInt16
        channel = 1
        f_rate = 8000
        
        stream = p.open(format=format_audio, channels=channel, rate=f_rate, input=True, frames_per_buffer=buffer_size)
        
        seq_num = 0
        timestamp = 0
        ssrc = random.randint(0, 0xFFFFFFFF)
        
        jitter_buffer = queue.Queue(maxsize=300)
        
        print("Streaming audio...")
        
        while streaming:
            try:
                data = stream.read(buffer_size, exception_on_overflow=False)
                rtp_packet = create_rtp_packet(data, seq_num, timestamp, ssrc)
                try:
                    jitter_buffer.put_nowait(rtp_packet)
                except queue.Full:
                    jitter_buffer.get()
                    jitter_buffer.put_nowait(rtp_packet)
                seq_num += 1
                timestamp += buffer_size
                time.sleep(buffer_size / 8000)
            except IOError as e:
                print(f"IOError during audio read: {e}")
            
            if not jitter_buffer.empty():
                rtp_socket.sendto(jitter_buffer.get(), (host, rtp_port))
        
    except Exception as e:
        print(f"Error during streaming: {e}")
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        if rtp_socket:
            rtp_socket.close()
        if p:
            p.terminate()
        print("Audio streaming stopped.")

def start_stop_streaming():
    global streaming
    if not streaming:
        streaming = True
        start_stop_button.config(image=pressed_image)
        threading.Thread(target=audio_streaming).start()
    else:
        streaming = False
        start_stop_button.config(image=normal_image)


streaming = False

# Create the GUI application
app = tk.Tk()
app.title("Audio Streaming Controller")


normal_image = PhotoImage(file="normal.png") 
pressed_image = PhotoImage(file="pressed.png")  


start_stop_button = tk.Button(app, image=normal_image, compound=tk.LEFT, command=start_stop_streaming)
start_stop_button.pack(pady=20)

def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f'{width}x{height}+{x}+{y}')


center_window(app)


app.mainloop()
