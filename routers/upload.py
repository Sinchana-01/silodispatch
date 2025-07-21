from fastapi import APIRouter, UploadFile, File, HTTPException
import csv
from io import StringIO
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Order
import uuid
from fastapi.responses import HTMLResponse
from models import Driver 
from datetime import datetime

from routers import upload  # assuming this is in routers/upload.py


# ✅ MOVE THIS TO TOP
router = APIRouter()

@router.get("/orders/upload", response_class=HTMLResponse)
async def upload_form():
    return """
    <html>
        <head><title>Upload Orders CSV</title></head>
        <body>
            <h2>Upload Orders CSV</h2>
            <form action="/upload-orders" enctype="multipart/form-data" method="post">
                <input name="file" type="file" accept=".csv">
                <input type="submit" value="Upload">
            </form>
        </body>
    </html>
    """

@router.post("/upload-orders")
async def upload_orders(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file format")

    contents = await file.read()
    decoded = contents.decode("utf-8")
    reader = csv.DictReader(StringIO(decoded))

    db: Session = SessionLocal()
    try:
        for row in reader:
            print("CSV Row:", row)  # 🐛 DEBUG HERE
            order = Order(
                id=str(uuid.uuid4()),
                customer_name=row["customer_name"],
                address=row["address"],
                pincode=row["pincode"],
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                weight=float(row["weight"]),
                payment_mode=row["payment_mode"],  # ✅ This must be set
                
                driver_id = int(row["driver_id"]) if row["driver_id"].strip() else None,
                

                amount=float(row["amount"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                batch_id=row["batch_id"] or None,
                customer_phone=row["customer_phone"],
                
            )
            db.add(order)
        db.commit()
    except Exception as e:
        db.rollback()
        print("UPLOAD ERROR:", e)  # 🐛 DEBUG HERE
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

    return {"message": "Orders uploaded successfully"}
@router.get("/drivers/upload", response_class=HTMLResponse)
async def upload_driver_form():
    return """
    <html>
        <head><title>Upload Drivers CSV</title></head>
        <body>
            <h2>Upload Drivers CSV</h2>
            <form action="/upload-drivers" enctype="multipart/form-data" method="post">
                <input name="file" type="file" accept=".csv">
                <input type="submit" value="Upload">
            </form>
        </body>
    </html>
    """

@router.post("/upload-drivers")
async def upload_drivers(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file format")

    contents = await file.read()
    decoded = contents.decode("utf-8")
    reader = csv.DictReader(StringIO(decoded))

    db: Session = SessionLocal()
    try:
        for row in reader:
            print("Driver Row:", row)  # 🐛 DEBUG
            driver = Driver(
                name=row["name"],
                phone_number=row["phone_number"]
            )
            db.add(driver)
        db.commit()
    except Exception as e:
        db.rollback()
        print("DRIVER UPLOAD ERROR:", e)  # 🐛 DEBUG
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

    return {"message": "Drivers uploaded successfully"}
