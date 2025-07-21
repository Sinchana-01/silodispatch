# notifications/whatsapp.py
import httpx, os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_FROM")  # ✅ same name as your OTP env var

async def send_whatsapp_payment_link(customer_phone: str, customer_name: str, order_id: str, amount: float, payment_link: str):
    formatted_number = f"whatsapp:{customer_phone}"
    message = f"Hi {customer_name}, your payment link for order {order_id} is ready. Please pay ₹{amount} using this link: {payment_link}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json",
            auth=(TWILIO_SID, TWILIO_AUTH),
            data={
                "From": f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
                "To": formatted_number,
                "Body": message
            }
        )
    if response.status_code != 201:
        print("❌ WhatsApp send failed:", response.text)
    else:
        print("✅ WhatsApp sent:", response.json())
