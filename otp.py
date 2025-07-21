from fastapi import APIRouter
import random

router = APIRouter()

otp_store = {}

@router.post("/send-otp/{phone}")
def send_otp(phone: str):
    otp = random.randint(100000, 999999)
    otp_store[phone] = otp
    print(f"OTP for {phone} is {otp}")
    return {"message": "OTP sent"}

@router.post("/verify-otp/{phone}/{otp_input}")
def verify_otp(phone: str, otp_input: int):
    if otp_store.get(phone) == otp_input:
        return {"status": "verified"}
    return {"status": "invalid"}
