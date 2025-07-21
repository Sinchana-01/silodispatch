from fastapi import FastAPI
from dotenv import load_dotenv
from database import Base, engine
from models import Base
from database import engine



from payment import router as payment_router
from otp import router as otp_router
from routers.upload import router as upload_router

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

from routers import batch

from routers import driver  # or batch if you put it there

from routers import otp
# main.py
from routers import settlement


from database import Base, engine
from models import Order, Batch  # ✅ Import all models
from routers import docs  # 👈 Add this

  # 👈 Mount the documentation router


  # ✅ import the otp router
templates = Jinja2Templates(directory="templates")


from routers import upload
load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SiloDispatch API",
    description="Backend API for handling OTP and Razorpay UPI Payments",
    version="1.0.0"
)


app.include_router(payment_router)
app.include_router(otp_router, prefix="/otp", tags=["OTP"])
app.include_router(upload_router, tags=["Upload"])
app.include_router(batch.router)
app.include_router(driver.router)
app.include_router(upload.router)
app.include_router(docs.router)
app.include_router(otp.router) 
app.include_router(settlement.router)
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/otp_test", response_class=HTMLResponse)
def otp_test_page(request: Request):
    return templates.TemplateResponse("otp_test.html", {"request": request})

@app.get("/pay", response_class=HTMLResponse)
async def pay_form(request: Request):
    return templates.TemplateResponse("payment_form.html", {"request": request})
