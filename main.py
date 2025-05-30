import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.mediastreams import AudioFrame, MediaStreamError, MediaStreamTrack
import subprocess
import fractions
import numpy as np
from pydantic import BaseModel
import ssl

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Redirect root to static/index.html
@app.get("/")
async def index():
    return HTMLResponse(open("static/index.html").read())

# Redirect /manifest.json to /static/manifest.json
@app.get("/manifest.json")
async def manifest():
    return FileResponse("static/manifest.json")

pcs = set()
last_recorder = None

class Offer(BaseModel):
    sdp: str
    type: str

class SpeakerStreamTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, source="virtual_sink.monitor", sample_rate=48000, channels=2):
        super().__init__()
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration = 0.02
        self.chunk_size = int(sample_rate * self.chunk_duration * channels * 2)
        self.timestamp = 0

        self.process = subprocess.Popen(
            [
                "parec",
                "--device", source,
                "--format=s16le",
                "--rate", str(sample_rate),
                "--channels", str(channels),
                "--latency-msec=1",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=self.chunk_size * 4,
        )

    async def recv(self):
        if self.process is None or self.process.poll() is not None:
            raise MediaStreamError("parec process not running")

        pcm_data = await asyncio.get_event_loop().run_in_executor(
            None, lambda: self.process.stdout.read(self.chunk_size)
        )

        if not pcm_data:
            raise MediaStreamError("No audio received")

        pcm_array = np.frombuffer(pcm_data, dtype=np.int16)

        if pcm_array.size % self.channels != 0:
            pcm_array = pcm_array[:-(pcm_array.size % self.channels)]

        pcm_array = pcm_array.reshape(-1, self.channels)

        layout = {1: "mono", 2: "stereo"}.get(self.channels)
        if not layout:
            raise MediaStreamError(f"Unsupported channels: {self.channels}")

        frame = AudioFrame(format="s16", layout=layout, samples=pcm_array.shape[0])
        frame.sample_rate = self.sample_rate
        frame.planes[0].update(pcm_array.tobytes())
        frame.pts = self.timestamp
        frame.time_base = fractions.Fraction(1, self.sample_rate)
        self.timestamp += pcm_array.shape[0]
        return frame

    def stop(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

class AudioRecorder:
    def __init__(self):
        self.process = None

    def add_track(self, track):
        async def read_data():
            self.process = await asyncio.create_subprocess_exec(
                "pacat", "--playback", "--device=mic_sink",
                "--rate=48000", "--channels=2", "--format=s16le", "--latency-msec=1",
                stdin=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )

            while True:
                try:
                    frame = await track.recv()
                    pcm_array = frame.to_ndarray(format="s16")
                    if pcm_array.ndim == 1:
                        pcm_array = np.repeat(pcm_array, 2).reshape(-1, 2)
                    pcm_bytes = pcm_array.astype(np.int16).tobytes()
                    if self.process and self.process.stdin:
                        self.process.stdin.write(pcm_bytes)
                        await self.process.stdin.drain()
                except MediaStreamError:
                    break
                except:
                    break

            await self.finalize()

        asyncio.create_task(read_data())

    async def finalize(self):
        if self.process:
            try:
                if self.process.stdin:
                    self.process.stdin.close()
                await self.process.wait()
            except:
                try:
                    self.process.kill()
                except:
                    pass
                
def parse_candidate(candidate_str: str) -> RTCIceCandidate:
    parts = candidate_str.split()
    # Expected minimal parts count is 8 (foundation, component, protocol, priority, ip, port, 'typ', type)
    if len(parts) < 8:
        raise ValueError("Invalid candidate string format")

    foundation = parts[0].replace("candidate:", "")
    component = int(parts[1])
    protocol = parts[2].lower()
    priority = int(parts[3])
    ip = parts[4]
    port = int(parts[5])
    # 'typ' should be parts[6], type is parts[7]
    if parts[6] != "typ":
        raise ValueError("Invalid candidate string format: missing 'typ'")

    cand_type = parts[7]

    # Optional fields follow after index 7
    related_address = None
    related_port = None
    tcp_type = None

    # Parse optional fields key-value pairs
    opt_idx = 8
    while opt_idx + 1 < len(parts):
        key = parts[opt_idx]
        value = parts[opt_idx + 1]
        if key == "raddr":
            related_address = value
        elif key == "rport":
            related_port = int(value)
        elif key == "tcptype":
            tcp_type = value
        opt_idx += 2

    return RTCIceCandidate(
        component=component,
        foundation=foundation,
        ip=ip,
        port=port,
        priority=priority,
        protocol=protocol,
        type=cand_type,
        relatedAddress=related_address,
        relatedPort=related_port,
        tcpType=tcp_type,
    )
    
    
@app.post("/offer")
async def offer(offer: Offer):
    global last_recorder

    # Clean up all existing peer connections before accepting a new one
    if pcs:
        for old_pc in list(pcs):
            try:
                for transceiver in old_pc.getTransceivers():
                    sender = transceiver.sender
                    if sender and sender.track:
                        sender.track.stop()
                await old_pc.close()
            except Exception as e:
                print(f"Error closing old pc: {e}")
            pcs.discard(old_pc)
        if last_recorder:
            await last_recorder.finalize()
            last_recorder = None

    pc = RTCPeerConnection()
    pcs.add(pc)

    speaker_track = SpeakerStreamTrack()
    pc.addTrack(speaker_track)

    recorder = AudioRecorder()
    last_recorder = recorder

    @pc.on("track")
    async def on_track(track):
        if track.kind == "audio":
            recorder.add_track(track)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        if pc.connectionState in ["failed", "closed"]:
            speaker_track.stop()
            await pc.close()
            pcs.discard(pc)

    try:
        await pc.setRemoteDescription(RTCSessionDescription(sdp=offer.sdp, type=offer.type))
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    except:
        if pc in pcs:
            pcs.discard(pc)
        speaker_track.stop()
        await pc.close()
        raise

@app.post("/stop")
async def stop():
    global last_recorder

    if last_recorder:
        await last_recorder.finalize()

    for pc in list(pcs):  # <--- iterate over a copy
        try:
            for transceiver in pc.getTransceivers():
                sender = transceiver.sender
                if sender and sender.track:
                    sender.track.stop()
            # if pc:
            #     print(pc)
            #     await pc.close()
        except Exception as e:
            print(f"Error during pc cleanup: {e}")

    pcs.clear()
    return {"message": "Stopped"}

from fastapi import Request

@app.post("/ice")
async def ice(request: Request):
    data = await request.json()
    candidate_dict = data.get("candidate")
    if candidate_dict:
        if pcs:
            pc = list(pcs)[-1]
            # Parse candidate string to RTCIceCandidate object
            candidate_obj = parse_candidate(candidate_dict["candidate"])
            candidate_obj.sdpMid = candidate_dict.get("sdpMid")
            candidate_obj.sdpMLineIndex = candidate_dict.get("sdpMLineIndex")
            await pc.addIceCandidate(candidate_obj)
    return {"result": "ok"}

if __name__ == "__main__":
    import uvicorn
    # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # ssl_context.load_cert_chain('cert.pem', 'key.pem')
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9001,
        # ssl_keyfile="key.pem",
        # ssl_certfile="cert.pem",
        log_level="debug"
    )
