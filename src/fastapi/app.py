import os
from fastapi import FastAPI, File, UploadFile, Body
from fastapi.responses import JSONResponse

from llm_handler.llm_handler_gateway import LLMHandler
from retriever.retriever_gateway import Retriever
from speech_to_text.speech_to_text_gateway import STTHandler

app = FastAPI(title="BFKiosk", version="0.1.0")

@app.post("/api/kiosk")
async def kiosk_gateway(audio_file: UploadFile = File(...)):
    text_converted = STTHandler(audio_file)

    action = LLMHandler(text_converted)

    return JSONResponse({"STT_result": text_converted, "action": action})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8800, reload=True)