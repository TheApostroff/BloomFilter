from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import language_tool_python
import os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# LanguageTool setup
tool = language_tool_python.LanguageToolPublicAPI('auto')

@app.get("/api/hello")
def hello():
    return {"msg": "Backend operational"}

@app.post("/api/spellcheck")
async def spellcheck(payload: dict):
    text = payload.get('text', '')
    matches = tool.check(text)
    issues = [{
        "offset": m.offset,
        "length": m.errorLength,
        "message": m.message,
        "replacements": m.replacements
    } for m in matches]
    return {"issues": issues}
