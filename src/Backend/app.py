# filepath: src/Backend/app.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pdf_extractor import convert_pdf_bytes_to_html

app = FastAPI()

# allow your Vite frontend to talk to this backend
origins = ["http://localhost:5173"]  

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["POST"],
    allow_headers=["*"],
)

@app.post("/convert", response_class=HTMLResponse)
async def convert(pdfFile: UploadFile = File(...)):
    if pdfFile.content_type != "application/pdf":
        raise HTTPException(400, "Please upload a PDF")
    data = await pdfFile.read()
    html = convert_pdf_bytes_to_html(data, pdfFile.filename)
    return HTMLResponse(content=html, media_type="text/html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)