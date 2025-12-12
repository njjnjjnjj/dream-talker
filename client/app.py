from contextlib import asynccontextmanager
import logging
import uvicorn
from fastapi import FastAPI

from recorder import Recorder
from log import init_log

init_log()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_event()
    yield


app = FastAPI(lifespan=lifespan)

recorder: Recorder = None


async def startup_event():
    global recorder
    recorder = Recorder()


@app.post("/start_record")
def start_record():
    """Starts the audio recording."""
    if recorder:
        recorder.start()
        return {"status": "recording_started"}
    return {"status": "error", "message": "recorder_not_initialized"}


@app.post("/stop_record")
def stop_record():
    """Stops the audio recording."""
    if recorder:
        recorder.stop()
        return {"status": "recording_stopped"}
    return {"status": "error", "message": "recorder_not_initialized"}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8569, reload=True)
