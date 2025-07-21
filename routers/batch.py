from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Order, Batch
import uuid
from collections import defaultdict

templates = Jinja2Templates(directory="templates")
router = APIRouter()

# Show batch generation UI (optional)
@router.get("/batches/generate", response_class=HTMLResponse)
def show_generate_page(request: Request):
    return templates.TemplateResponse("generate_batches.html", {"request": request})


# === BATCH CREATION USING PINCODE CLUSTERING ===
@router.post("/batches/today")
def create_batches():
    db: Session = SessionLocal()
    try:
        # STEP 1: Unassign drivers from fully paid batches
        assigned_batches = db.query(Batch).filter(Batch.driver_id != None).all()
        for batch in assigned_batches:
            orders = db.query(Order).filter(Order.batch_id == batch.id).all()
            if orders and all(order.payment_status != 'unpaid' for order in orders):
                driver_id = batch.driver_id
                batch.driver_id = None  # unassign

                # Reassign driver to another batch if available
                unassigned_batches = db.query(Batch).filter(Batch.driver_id == None, Batch.id != batch.id).all()
                for ub in unassigned_batches:
                    ub.driver_id = driver_id
                    break

        # STEP 2: Get all orders that are not batched
        pending_orders = db.query(Order).filter(Order.batch_id == None).all()
        if not pending_orders:
            return {"message": "No unbatched orders found."}

        # STEP 3: Cluster orders by pincode
        cluster_map = defaultdict(list)
        for order in pending_orders:
            cluster_map[order.pincode].append(order)
        order_clusters = list(cluster_map.values())

        # STEP 4: Create batches from clusters
        for cluster in order_clusters:
            batch_orders = []
            current_weight = 0.0

            for order in cluster:
                weight = order.weight or 0.0
                if current_weight + weight > 25 or len(batch_orders) >= 30:
                    # Create batch
                    avg_lat = sum(o.latitude for o in batch_orders) / len(batch_orders)
                    avg_lon = sum(o.longitude for o in batch_orders) / len(batch_orders)
                    batch = Batch(
                        id=str(uuid.uuid4()),
                        latitude=avg_lat,
                        longitude=avg_lon,
                        total_weight=current_weight,
                        order_count=len(batch_orders),
                        pincode=batch_orders[0].pincode  # optional
                    )
                    db.add(batch)
                    db.flush()
                    for o in batch_orders:
                        o.batch_id = batch.id
                    batch_orders = []
                    current_weight = 0.0

                batch_orders.append(order)
                current_weight += weight

            # Add remaining orders in final batch
            if batch_orders:
                avg_lat = sum(o.latitude for o in batch_orders) / len(batch_orders)
                avg_lon = sum(o.longitude for o in batch_orders) / len(batch_orders)
                batch = Batch(
                    id=str(uuid.uuid4()),
                    latitude=avg_lat,
                    longitude=avg_lon,
                    total_weight=current_weight,
                    order_count=len(batch_orders),
                    pincode=batch_orders[0].pincode  # optional
                )
                db.add(batch)
                db.flush()
                for o in batch_orders:
                    o.batch_id = batch.id

        db.commit()
        return {"message": "Batches created and drivers reassigned successfully."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()
