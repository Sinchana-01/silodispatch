from sqlalchemy.orm import Session
from database import SessionLocal
from models import Order, Batch
from tqdm import tqdm  # Optional: for progress bar

def update_driver_ids_in_orders():
    db: Session = SessionLocal()
    try:
        batches_with_drivers = db.query(Batch).filter(Batch.driver_id != None).all()

        for batch in tqdm(batches_with_drivers, desc="Updating orders"):
            orders = db.query(Order).filter(Order.batch_id == batch.id).all()
            for order in orders:
                order.driver_id = batch.driver_id
                db.add(order)

        db.commit()
        print("✅ Order driver_ids updated successfully based on batch assignments.")

    except Exception as e:
        db.rollback()
        print("❌ Error:", e)
    finally:
        db.close()

if __name__ == "__main__":
    update_driver_ids_in_orders()
