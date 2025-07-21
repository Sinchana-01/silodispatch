# docs.py
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/docs/home", response_class=HTMLResponse)
def show_docs_home(request: Request):
    return templates.TemplateResponse("docs_home.html", {"request": request})

@router.get("/docs/architecture", response_class=HTMLResponse)
def architecture(request: Request):
    return templates.TemplateResponse("architecture.html", {"request": request})

@router.get("/docs/erd", response_class=HTMLResponse)
def erd(request: Request):
    return templates.TemplateResponse("erd.html", {"request": request})

@router.get("/docs/sequence", response_class=HTMLResponse)
def sequence(request: Request):
    return templates.TemplateResponse("sequence.html", {"request": request})

@router.get("/docs/clustering", response_class=HTMLResponse)
def clustering(request: Request):
    return templates.TemplateResponse("clustering.html", {"request": request})

@router.get("/docs/readme")
def download_readme():
    return FileResponse("static/README.md", filename="README.md", media_type="text/markdown")
