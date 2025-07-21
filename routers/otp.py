from fastapi import Request, Form, APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import Order, OTPCode
import random, os, asyncio
from datetime import datetime
from twilio.rest import Client
from payment import create_razorpay_payment  # Must return dict with "payment_link"
from notifications.whatsapp import send_whatsapp_payment_link  # Your custom async WhatsApp sender

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Load Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")  # e.g., +14155238886

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ✅ Send WhatsApp OTP using Twilio
def send_whatsapp_otp(to_number: str, otp: str):
    message = client.messages.create(
        body=f"🔐 Your SiloDispatch OTP is: {otp}",
        from_=f"whatsapp:{TWILIO_WHATSAPP_FROM}",
        to=f"whatsapp:{to_number}"
    )
    print(f"✅ WhatsApp OTP sent to {to_number}. SID: {message.sid}")


# ✅ Render OTP UI
@router.get("/otp", response_class=HTMLResponse)
def otp_ui_page(request: Request, status: str = "", message: str = ""):
    return templates.TemplateResponse("otp.html", {
        "request": request,
        "status": status,
        "message": message
    })


# ✅ Trigger OTP
@router.post("/orders/trigger_otp_form")
def trigger_otp_form(order_id: str = Form(...), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return RedirectResponse(
            url="/otp?status=error&message=Order not found",
            status_code=303
        )
    if not order.customer_phone:
        return RedirectResponse(
            url="/otp?status=error&message=Customer phone number missing",
            status_code=303
        )

    otp = str(random.randint(100000, 999999))
    otp_entry = OTPCode(
        order_id=order_id,
        phone_number=order.customer_phone,
        otp=otp,
        created_at=datetime.utcnow()
    )
    db.add(otp_entry)
    db.commit()

    send_whatsapp_otp(order.customer_phone, otp)

    return RedirectResponse(
        url=f"/otp?status=success&message=OTP sent to {order.customer_phone}",
        status_code=303
    )


# ✅ Verify OTP and handle payment logic
@router.post("/orders/verify_otp_form")
def verify_otp_form(order_id: str = Form(...), submitted_otp: str = Form(...), db: Session = Depends(get_db)):

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return RedirectResponse(url="/otp?status=error&message=Order not found", status_code=303)

    otp_record = db.query(OTPCode).filter(OTPCode.order_id == order_id).order_by(OTPCode.created_at.desc()).first()
    if not otp_record or otp_record.otp != submitted_otp:
        return RedirectResponse(url="/otp?status=error&message=Invalid OTP", status_code=303)

    order.otp_verified = True
    db.commit()

    # ✅ Handle based on payment mode
    if order.payment_mode == "upi":
        # Generate Razorpay payment link
        payment_data = asyncio.run(create_razorpay_payment(order.id, db))

        # Send WhatsApp payment link
        asyncio.run(send_whatsapp_payment_link(
            customer_phone=order.customer_phone,
            customer_name=order.customer_name,
            order_id=order.id,
            amount=order.amount,
            payment_link=payment_data["payment_link"]
        ))

        return RedirectResponse(url=f"/pay?order_id={order_id}", status_code=302)

    elif order.payment_mode == "cod":
        return RedirectResponse(url=f"/payment/cash_collect?order_id={order_id}", status_code=302)

    elif order.payment_mode == "prepaid":
        order.payment_status = "delivered"
        db.commit()
        return RedirectResponse(url=f"/payment/delivered?order_id={order_id}", status_code=302)

    return RedirectResponse(url="/otp?status=error&message=Unknown payment mode", status_code=303)
