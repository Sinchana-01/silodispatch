from database import SessionLocal
from models import Order
import uuid

# Start DB session
db = SessionLocal()

# Create test order
order = Order(
    id=str(uuid.uuid4()),
    customer_name="Sinchana",
    amount=199.99,
    payment_mode="UPI",
    payment_status="PENDING",
    driver_id="driver_123"
)

# Add and commit
db.add(order)
db.commit()

print("✅ Test order created with ID:", order.id)
