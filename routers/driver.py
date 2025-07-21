from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from database import get_db
from models import Driver, Batch, Order, Breadcrumb
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ✅ Assign driver to a batch manually
@router.post("/batches/{batch_id}/assign_driver")
def assign_driver(batch_id: str, driver_id: int = Form(...), db: Session = Depends(get_db)):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # ✅ Assign driver to batch
    batch.driver_id = driver_id
    db.add(batch)

    # ✅ Also assign driver_id to all orders in the batch
    orders = db.query(Order).filter(Order.batch_id == batch_id).all()
    for order in orders:
        order.driver_id = driver_id
        db.add(order)

    db.commit()
    return {
        "message": f"✅ Driver {driver_id} assigned to batch {batch_id}",
        "order_ids_updated": [str(order.id) for order in orders]
    }

# ✅ Auto-assign drivers to batches without using pincode (round-robin strategy)
@router.post("/auto-assign-drivers")
def auto_assign_drivers(db: Session = Depends(get_db)):
    # Get all unassigned batches
    unassigned_batches = db.query(Batch).filter(Batch.driver_id == None).all()

    # Get drivers who are not already assigned to any batch
    assigned_driver_ids = db.query(Batch.driver_id).filter(Batch.driver_id != None).distinct().all()
    assigned_driver_ids = {d[0] for d in assigned_driver_ids}

    available_drivers = db.query(Driver).filter(~Driver.id.in_(assigned_driver_ids)).all()

    if not available_drivers:
        raise HTTPException(status_code=400, detail="No unassigned drivers available")

    if len(unassigned_batches) > len(available_drivers):
        raise HTTPException(
            status_code=400,
            detail=f"Not enough unassigned drivers. Need {len(unassigned_batches)}, only {len(available_drivers)} available."
        )

    assignments = []

    for batch, driver in zip(unassigned_batches, available_drivers):
        batch.driver_id = driver.id
        db.add(batch)

        # Update driver_id in all orders belonging to this batch
        orders = db.query(Order).filter(Order.batch_id == batch.id).all()
        for order in orders:
            order.driver_id = driver.id
            db.add(order)

        assignments.append({
            "batch_id": str(batch.id),
            "driver_id": driver.id,
            "order_ids": [str(order.id) for order in orders],
        })

    db.commit()
    return {
        "message": "✅ Drivers auto-assigned (1 batch per driver)",
        "assignments": assignments
    }



# ✅ Get all batches assigned to a driver
@router.get("/drivers/{driver_id}/batches")
def get_driver_batches(driver_id: int, db: Session = Depends(get_db)):
    batches = db.query(Batch).filter(Batch.driver_id == driver_id).all()
    return batches

# ✅ Get driver routes (orders) grouped by batch
@router.get("/drivers/{driver_id}/routes")
def get_routes_for_driver(driver_id: int, db: Session = Depends(get_db)):
    batches = db.query(Batch).filter(Batch.driver_id == driver_id).all()
    result = []
    for batch in batches:
        orders = db.query(Order).filter(Order.batch_id == batch.id).all()
        result.append({
            "batch_id": str(batch.id),
            "orders": [
                {
                    "order_id": str(o.id),
                    "customer_name": o.customer_name,
                    "address": o.address,
                    "pincode": o.pincode,
                    "latitude": o.latitude,
                    "longitude": o.longitude
                } for o in orders
            ]
        })
    return {"routes": result}

# ✅ Track driver's live location (breadcrumb)
@router.post("/drivers/{driver_id}/track")
def submit_location(
    driver_id: int,
    latitude: float = Form(...),
    longitude: float = Form(...),
    db: Session = Depends(get_db)
):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    breadcrumb = Breadcrumb(
        driver_id=driver_id,
        latitude=latitude,
        longitude=longitude
    )
    db.add(breadcrumb)
    db.commit()
    return {"message": "Location tracked"}

# ✅ HTML UI form to assign driver manually (with auto button)
@router.get("/assign-driver-form", response_class=HTMLResponse)
def assign_driver_form(request: Request, db: Session = Depends(get_db)):
    drivers = db.query(Driver).all()
    batches = db.query(Batch).filter(Batch.driver_id == None).all()
    return templates.TemplateResponse("assign_driver.html", {
        "request": request,
        "drivers": drivers,
        "batches": batches
    })

# ✅ Handle form POST for manual assignment
@router.post("/assign-driver-form", response_class=HTMLResponse)
def assign_driver_submit(batch_id: str = Form(...), driver_id: int = Form(...), db: Session = Depends(get_db)):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        return HTMLResponse("<h3>❌ Batch not found</h3>", status_code=404)

    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        return HTMLResponse("<h3>❌ Driver not found</h3>", status_code=404)

    batch.driver_id = driver_id
    db.commit()
    return HTMLResponse(f"<h3>✅ Driver <b>{driver.name}</b> assigned to Batch <b>{batch.id}</b></h3>")

@router.get("/driver-orders")
def driver_orders(request: Request, driver_id: int = None, db: Session = Depends(get_db)):
    if driver_id is None:
        return templates.TemplateResponse("driver_orders.html", {
            "request": request,
            "orders": None  # don't render anything
        })

    # Find orders assigned to batches where driver_id matches
    orders = (
        db.query(Order)
        .join(Batch, Batch.id == Order.batch_id)
        .filter(Batch.driver_id == driver_id)
        .all()
    )

    total_cod = sum(order.amount for order in orders if order.payment_mode == "cod")

    return templates.TemplateResponse("driver_orders.html", {
        "request": request,
        "orders": orders,
        "total_cod": total_cod
    })