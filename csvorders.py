import csv
from models import Driver
from database import SessionLocal

db = SessionLocal()
with open("drivers.csv", newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        driver = Driver(name=row["name"], phone_number=row["phone_number"])
        db.add(driver)
    db.commit()
db.close()
