# import subprocess

# def record_system_audio(filename="output.wav", duration=10):
#     subprocess.run([
#         "ffmpeg",
#         "-f", "pulse",
#         "-i", "Virtual_Speaker.monitor",
#         "-t", str(duration),
#         "-ac", "2",
#         "-ar", "44100",
#         filename
#     ])
# record_system_audio()


import subprocess

def stream_opus_audio():
    process = subprocess.Popen([
        "ffmpeg",
        "-f", "pulse",
        "-i", "Virtual_Speaker.monitor",
        "-ac", "1",                 # Mono
        "-ar", "48000",             # Opus standard
        "-c:a", "libopus",          # Encode as Opus
        "-f", "opus",               # Output format
        "pipe:1"                    # Send to stdout
    ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    try:
        while True:
            chunk = process.stdout.read(4096)  # You can adjust chunk size
            if not chunk:
                break
            print(chunk)  # Or: send to a WebSocket, file, etc.
    except KeyboardInterrupt:
        process.terminate()
        print("\nStopped streaming.")

stream_opus_audio()
