import csv
import uuid
import random
from faker import Faker
from datetime import datetime

fake = Faker()

# Constants
NUM_ORDERS = 500
VALID_PHONE = "+916363547255" 
PAYMENT_MODES = ["cod", "upi", "prepaid"]
PAYMENT_STATUSES = ["pending", "paid", "failed"]

# Generate clustered pincodes
clustered_pincodes = [
    "560001", "560002", "560003",  # Cluster 1 (Bangalore Central)
    "110001", "110002", "110003",  # Cluster 2 (Delhi Central)
    "400001", "400002", "400003",  # Cluster 3 (Mumbai Central)
    "700001", "700002", "700003",  # Cluster 4 (Kolkata Central)
    "600001", "600002", "600003"   # Cluster 5 (Chennai Central)
]

orders = []

for i in range(NUM_ORDERS):
    weight = round(random.uniform(0.5, 5.0), 2)
    amount = round(weight * 100, 2)

    # Assign a pincode cluster
    pincode = random.choice(clustered_pincodes)

    order = {
        "id": str(uuid.uuid4()),
        "customer_name": fake.name(),
        "address": fake.address().replace("\n", ", "),
        "pincode": pincode,
        "latitude": round(fake.latitude(), 6),
        "longitude": round(fake.longitude(), 6),
        "weight": weight,
        "payment_mode": random.choice(PAYMENT_MODES),
        "payment_status": random.choice(PAYMENT_STATUSES),
        "driver_id": "",  # Empty initially
        "amount": amount,
        "created_at": datetime.utcnow().isoformat(),
        "batch_id": "",  # Empty initially
        "customer_phone": VALID_PHONE,
        "otp_verified": random.choice([True, False]),
    }

    orders.append(order)

# CSV headers
headers = list(orders[0].keys())

# Write to CSV
with open("orders.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(orders)

print("✅ orders.csv generated with 500 rows and clustered pincodes.")
