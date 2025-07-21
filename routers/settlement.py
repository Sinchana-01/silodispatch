# settlement.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from io import StringIO
import uuid
import csv

from database import get_db, Base
from models import Driver, Order
from sqlalchemy import Column, Float, DateTime, Integer, ForeignKey,String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ✅ Settlement Model
class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    order_id = Column(String, ForeignKey("orders.id"))
    amount = Column(Float, nullable=False)
    settled_at = Column(DateTime, default=datetime.utcnow)

    driver = relationship("Driver")
    order = relationship("Order")

# ✅ Dashboard UI
@router.get("/settlements/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("settlement.html", {"request": request})

# ✅ Live COD totals per driver
@router.get("/settlements/live")
def get_live_driver_cod(db: Session = Depends(get_db)):
    subquery = db.query(Settlement.order_id).subquery()

    results = db.query(
        Driver.id,
        Driver.name,
        func.sum(Order.amount).label("cod_total")
    ).join(Order, Order.driver_id == Driver.id)\
     .filter(
        Order.payment_mode == "cod",
        Order.driver_id != None,
        Order.payment_status == "cash_received",
        ~Order.id.in_(subquery)
     )\
     .group_by(Driver.id, Driver.name).all()

    return {
        "drivers": [
            {
                "driver_id": r.id,
                "driver_name": r.name,
                "outstanding_cod": float(r.cod_total or 0)
            } for r in results
        ]
    }

# ✅ One-click settle per driver
@router.post("/settlements/settle/{driver_id}")
def settle_driver(driver_id: int, db: Session = Depends(get_db)):
    subquery = db.query(Settlement.order_id).subquery()

    orders = db.query(Order).filter(
        Order.driver_id == driver_id,
        Order.payment_mode == "cod",
        Order.payment_status == "cash_received",
        ~Order.id.in_(subquery)
    ).all()

    if not orders:
        raise HTTPException(status_code=400, detail="No unsettled COD orders for driver")

    for order in orders:
        settlement = Settlement(
            driver_id=driver_id,
            order_id=order.id,
            amount=order.amount,
        )
        db.add(settlement)

    db.commit()
    return {"message": f"₹{sum(o.amount for o in orders):.2f} settled for driver {driver_id}"}

# ✅ CSV export
@router.get("/settlements/export/csv")
def export_csv(db: Session = Depends(get_db)):
    settlements = db.query(Settlement).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Driver ID", "Order ID", "Driver Name", "Amount"])

    for s in settlements:
        writer.writerow([
            str(s.id),
            s.driver_id,
            str(s.order_id),
            s.driver.name,
            s.amount
        ])

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=settlements.csv"}
    )
