from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
import logging
import asyncio
import numpy as np
import io
import time
from collections import deque
import soundfile as sf # For reading uploaded audio files

# Import models
from models.analysis_models import AnalysisResult, IncidentReport

# Import controllers
from controllers.audio_controller import AudioController
from controllers.alert_controller import AlertController
from controllers.verification_controller import VerificationController
from controllers.report_controller import ReportController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Allow CORS for local development (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Global instances of controllers and services
SAMPLE_RATE = 44100  # Assuming client sends 44.1kHz audio (common for browser)
CHUNK_SIZE_SECONDS = 2 # Process audio in 2-second chunks

audio_controller = AudioController(sample_rate=SAMPLE_RATE)
alert_controller = AlertController()
verification_controller = VerificationController()
report_controller = ReportController()

# Global state for active connections and their data
# In a production multi-user system, this would be managed per-user/per-call session
class ConnectionState:
    def __init__(self):
        self.audio_buffer = bytearray()
        self.processing_queue = asyncio.Queue() # For sending analysis results to client
        self.alert_queue = asyncio.Queue()      # For sending TTS alerts to client
        self.all_analysis_results: deque[AnalysisResult] = deque(maxlen=200) # Store recent results for reporting (increased maxlen)
        self.call_start_time: float = 0.0
        self.current_time_offset: float = 0.0 # Time offset for current chunk relative to call start

# Using a dictionary to manage states for potentially multiple connections (though global processor for now)
active_connections: dict[str, ConnectionState] = {}
# For simplicity, we'll use a single fixed connection ID for now
SINGLE_CONNECTION_ID = "default_call_session"

@app.on_event("startup")
async def startup_event():
    """
    Initializes global state and starts background processing task.
    """
    active_connections[SINGLE_CONNECTION_ID] = ConnectionState()
    app.state.audio_processor_task = asyncio.create_task(audio_processor_loop())
    logger.info("Backend startup: Audio processing task initiated.")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Cancels background processing task on shutdown.
    """
    if hasattr(app.state, 'audio_processor_task'):
        app.state.audio_processor_task.cancel()
        try:
            await app.state.audio_processor_task
        except asyncio.CancelledError:
            logger.info("Audio processing task cancelled during shutdown.")
    logger.info("Backend shutdown complete.")

@app.get("/")
async def read_root():
    """
    Simple health check endpoint.
    """
    return {"message": "Voice Scam Shield Backend is running!"}

@app.post("/enroll-voice/{name}")
async def enroll_voice_endpoint(name: str, audio_file: UploadFile = File(...)):
    """
    Endpoint to enroll a voice for caller verification.
    Expects audio file (e.g., WAV) in the request body.
    """
    try:
        audio_bytes = await audio_file.read()
        # Assuming audio_file is WAV bytes, decode it
        audio_data_np, sr = sf.read(io.BytesIO(audio_bytes), dtype='float32')
        
        # Ensure sample rate matches expected
        if sr != SAMPLE_RATE:
            # Resample if necessary for consistency with other services
            num_samples_target = int(len(audio_data_np) * SAMPLE_RATE / sr)
            audio_data_np = np.interp(
                np.linspace(0, len(audio_data_np) - 1, num_samples_target),
                np.arange(len(audio_data_np)),
                audio_data_np
            ).astype(np.float32)
            logger.info(f"Resampled enrolled audio from {sr}Hz to {SAMPLE_RATE}Hz.")
            sr = SAMPLE_RATE # Update sample rate after resampling

        verification_controller.enroll_voice(name, audio_data_np, sr)
        return JSONResponse(content={"message": f"Voice for {name} enrolled successfully."})
    except Exception as e:
        logger.error(f"Error enrolling voice: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to enroll voice: {e}")

@app.get("/generate-report")
async def generate_report_endpoint():
    """
    Endpoint to generate an incident report for the current session.
    """
    conn_state = active_connections.get(SINGLE_CONNECTION_ID)
    if not conn_state or not conn_state.all_analysis_results:
        raise HTTPException(status_code=404, detail="No analysis data available for report.")
    
    report = await report_controller.generate_incident_report(
        list(conn_state.all_analysis_results), conn_state.call_start_time
    )
    return report

async def audio_processor_loop():
    """
    Background task to continuously process audio chunks from the buffer.
    """
    conn_state = active_connections[SINGLE_CONNECTION_ID]
    
    while True:
        await asyncio.sleep(0.1) # Check buffer every 100ms

        # Minimum buffer size for processing (16-bit PCM, 2 bytes per sample)
        min_buffer_size_bytes = int(SAMPLE_RATE * CHUNK_SIZE_SECONDS * 2)

        if len(conn_state.audio_buffer) >= min_buffer_size_bytes:
            # Take a chunk from the buffer
            chunk_bytes = conn_state.audio_buffer[:min_buffer_size_bytes]
            del conn_state.audio_buffer[:min_buffer_size_bytes] # Remove processed chunk

            # Convert bytes to numpy array (assuming 16-bit PCM)
            audio_data_np = np.frombuffer(chunk_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            
            logger.debug(f"Processing {len(audio_data_np)/SAMPLE_RATE:.2f} seconds of audio from buffer.")

            # Process audio chunk using AudioController
            analysis_results = await audio_controller.process_audio_chunk(
                audio_data_np, conn_state.current_time_offset
            )
            
            # Update current time offset for next chunk
            conn_state.current_time_offset += CHUNK_SIZE_SECONDS

            # Store results and generate alerts
            for result in analysis_results:
                # Perform caller verification for 'caller' segments
                if result.speaker != "speaker_1" and result.audio_segment_bytes: # Assuming speaker_1 is the user
                    try:
                        # Convert audio_segment_bytes back to numpy array for verification
                        segment_audio_np, _ = sf.read(io.BytesIO(result.audio_segment_bytes), dtype='float32')
                        caller_matches = verification_controller.verify_caller_voice(segment_audio_np, SAMPLE_RATE)
                        result.caller_verification_matches = caller_matches
                        if caller_matches:
                            logger.info(f"Caller identified: {caller_matches}")
                    except Exception as e:
                        logger.error(f"Error during real-time caller verification: {e}")

                conn_state.all_analysis_results.append(result) # Store for reporting
                
                # Generate and queue TTS alert if needed
                alert_audio = await alert_controller.generate_and_send_alert(result)
                if alert_audio:
                    result.alert_triggered = True # Mark that an alert was sent
                    await conn_state.alert_queue.put(alert_audio)
                
                # Put analysis result into queue for client display
                await conn_state.processing_queue.put(result.model_dump()) # Send Pydantic model as dict

        # Prevent busy-waiting if buffer is empty
        if not conn_state.audio_buffer:
            await asyncio.sleep(0.5) # Longer sleep if no data

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio streaming and result sending.
    """
    await websocket.accept()
    logger.info("WebSocket connection established.")

    conn_state = active_connections[SINGLE_CONNECTION_ID]
    conn_state.audio_buffer = bytearray() # Clear buffer for new session
    conn_state.all_analysis_results.clear() # Clear previous results
    conn_state.call_start_time = time.time()
    conn_state.current_time_offset = 0.0
    
    # Start tasks to send analysis results and alerts to client
    send_analysis_task = asyncio.create_task(send_analysis_results_to_client(websocket, conn_state))
    send_alert_task = asyncio.create_task(send_alerts_to_client(websocket, conn_state))

    try:
        while True:
            data = await websocket.receive_bytes()
            conn_state.audio_buffer.extend(data)
            # logger.debug(f"Received {len(data)} bytes, buffer size: {len(conn_state.audio_buffer)} bytes.")

    except WebSocketDisconnect:
        logger.info("WebSocket connection disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        send_analysis_task.cancel()
        send_alert_task.cancel()
        try:
            await send_analysis_task
            await send_alert_task
        except asyncio.CancelledError:
            logger.debug("WebSocket sending tasks cancelled.")

async def send_analysis_results_to_client(websocket: WebSocket, conn_state: ConnectionState):
    """
    Sends processed analysis results from the queue back to the client via WebSocket.
    """
    while True:
        result = await conn_state.processing_queue.get()
        if result:
            try:
                await websocket.send_json({"type": "analysis_result", "data": result})
                logger.debug(f"Sent analysis result to client: {result['scam_detection']['label']}")
            except Exception as e:
                logger.error(f"Error sending analysis results via WebSocket: {e}")
                break

async def send_alerts_to_client(websocket: WebSocket, conn_state: ConnectionState):
    """
    Sends TTS audio alerts from the queue back to the client via WebSocket.
    """
    while True:
        alert_audio_bytes = await conn_state.alert_queue.get()
        if alert_audio_bytes:
            try:
                # Send as binary data with a specific type for client to distinguish
                await websocket.send_bytes(b"ALERT_AUDIO_START" + alert_audio_bytes + b"ALERT_AUDIO_END")
                logger.info("Sent TTS alert audio to client.")
            except Exception as e:
                logger.error(f"Error sending alert audio via WebSocket: {e}")
                break

if __name__ == "__main__":
    # To run this server, save the file as server/main.py and then run:
    # uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    # (Make sure you are in the 'server' directory when running this command)
    uvicorn.run(app, host="0.0.0.0", port=8000)
