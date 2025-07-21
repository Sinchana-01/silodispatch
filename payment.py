import os
import uuid
import httpx
from uuid import UUID
from datetime import datetime
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request, Depends, Query, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from models import Order, Payment

# 🔐 Load Razorpay credentials
load_dotenv()
RAZORPAY_API_KEY = os.getenv("RAZORPAY_API_KEY")
RAZORPAY_API_SECRET = os.getenv("RAZORPAY_API_SECRET")

router = APIRouter(prefix="/payment")

# ✅ Create Razorpay Payment
@router.post("/create-upi-payment/{order_id}")
async def create_razorpay_payment(order_id: UUID, db: Session = Depends(get_db)):
    if not RAZORPAY_API_KEY or not RAZORPAY_API_SECRET:
        raise HTTPException(status_code=500, detail="Razorpay credentials not loaded.")

    existing_payment = db.query(Payment).filter(Payment.order_id == str(order_id)).first()
    if existing_payment:
        return {
            "payment_link": f"https://rzp.io/i/{existing_payment.payment_link_id}",
            "razorpay_link_id": existing_payment.payment_link_id,
            "reference_id": str(order_id),
            "status": "existing"
        }

    order = db.query(Order).filter(Order.id == str(order_id)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    payload = {
        "amount": int(order.amount * 100),
        "currency": "INR",
        "accept_partial": False,
        "description": "SiloDispatch UPI Payment",
        "reference_id": str(order_id),
        "customer": {
            "name": "Silo Customer",
            "email": "test@example.com",
            "contact": order.customer_phone
        },
        "notify": {
            "sms": True,
            "email": False
        },
        "reminder_enable": True,
        "callback_url": f"http://localhost:8000/payment/callback/{order_id}",
        "callback_method": "get"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.razorpay.com/v1/payment_links",
            auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET),
            json=payload
        )

    if response.status_code != 200:
        print("❌ Razorpay error:", response.text)
        raise HTTPException(status_code=500, detail="Failed to create Razorpay payment link")

    data = response.json()
    print("✅ Razorpay response:", data)

    payment = Payment(
        id=str(uuid.uuid4()),
        order_id=str(order_id),
        status="created",
        razorpay_payment_id=None,
        payment_link_id=data["id"],
        signature=None,
        created_at=datetime.utcnow()
    )
    db.add(payment)
    db.commit()

    return {
        "payment_link": data["short_url"],
        "razorpay_link_id": data.get("id"),
        "reference_id": data.get("reference_id"),
        "status": "new"
    }

# ✅ Razorpay Callback
@router.get("/callback/{order_id}", response_class=HTMLResponse)
async def razorpay_callback(order_id: UUID, request: Request):
    params = dict(request.query_params)
    print("🔔 Razorpay callback received:", params)

    payment_status = params.get("razorpay_payment_link_status")
    razorpay_payment_id = params.get("razorpay_payment_id")
    razorpay_payment_link_id = params.get("razorpay_payment_link_id")
    razorpay_signature = params.get("razorpay_signature")

    db: Session = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == str(order_id)).first()
        if not order:
            return f"<h1>❌ Order not found</h1><p>Order ID: {order_id}</p>"

        # ✅ Check if this Razorpay payment was already processed
        existing_payment = db.query(Payment).filter(
            Payment.razorpay_payment_id == razorpay_payment_id,
            Payment.order_id == str(order_id)
        ).first()

        if payment_status == "paid":
            # Update order if not already marked as paid
            if order.payment_status != "paid":
                order.payment_status = "paid"
                db.add(order)

            # Update or insert payment record
            if existing_payment:
            
                existing_payment.status = "paid"
                existing_payment.signature = razorpay_signature
                existing_payment.payment_link_id = razorpay_payment_link_id
                existing_payment.amount = order.amount
                db.add(existing_payment)
            else:
                new_payment = Payment(
                    id=str(uuid.uuid4()),
                    order_id=str(order_id),
                    status="paid",
                    amount=order.amount,
                    razorpay_payment_id=razorpay_payment_id,
                    payment_link_id=razorpay_payment_link_id,
                    signature=razorpay_signature,
                    created_at=datetime.utcnow()
                )
                db.add(new_payment)

            db.commit()

            return f"<h1>✅ Payment Successful</h1><p>Order ID: {order_id}</p>"

        else:
            # Mark order as failed only if not paid already
            if order.payment_status != "paid":
                order.payment_status = "failed"
                db.add(order)
                db.commit()

            return f"<h1>❌ Payment Failed</h1><p>Order ID: {order_id}</p><p>Status: {payment_status}</p>"

    except Exception as e:
        db.rollback()
        print("❌ Error in DB update:", e)
        return f"<h1>❌ Internal Error</h1><p>{str(e)}</p>"
    finally:
        db.close()


# ✅ Fetch Order Info
@router.get("/orders/{order_id}/info")
def get_order_info(order_id: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "customer_phone": order.customer_phone,
        "amount": order.amount
    }

# ✅ Show Cash Collection Page
@router.get("/cash_collect", response_class=HTMLResponse)
def show_cash_collection_page(request: Request, order_id: str = Query(...), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return HTMLResponse("<h3>❌ Order not found</h3>", status_code=404)

    if order.payment_status == "cash_received":
        return HTMLResponse("<h3>✅ Cash already received</h3>")

    return HTMLResponse(f"""
        <html>
            <head><title>Collect Cash</title></head>
            <body>
                <h2>💰 Collect ₹{order.amount} Cash</h2>
                <form action="/payment/cash_collect" method="post">
                    <input type="hidden" name="order_id" value="{order_id}" />
                    <button type="submit" style="font-size:18px;">✅ Confirm Cash Received</button>
                </form>
            </body>
        </html>
    """)

# ✅ Confirm Cash Collection
@router.post("/cash_collect", response_class=HTMLResponse)
def confirm_cash_collection(order_id: str = Form(...), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return HTMLResponse("<h3>❌ Order not found</h3>", status_code=404)

    order.payment_status = "cash_received"
    
    db.commit()

    return HTMLResponse(f"""
        <html>
            <body>
                <h2>✅ Cash of ₹{order.amount} Collected</h2>
                <p>Order {order_id} marked as <b>Delivered</b></p>
            </body>
        </html>
    """)

# ✅ Confirm Prepaid Delivery
@router.get("/delivered", response_class=HTMLResponse)
def confirm_prepaid_delivery(order_id: str = Query(...), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return HTMLResponse("<h3>❌ Order not found</h3>", status_code=404)

    if order.payment_status in ["delivered", "paid and delivered"]:
        return HTMLResponse(f"<h3>✅ Order {order_id} already delivered</h3>")

    order.payment_status = "delivered"
    db.commit()

    return HTMLResponse(f"""
        <html>
            <body>
                <h2>📦 Order Delivered</h2>
                <p>Order ID: {order_id}</p>
                <p>Status: <b>Delivered</b></p>
            </body>
        </html>
    """)

