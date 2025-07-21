from sqlalchemy import Column, String, Float, DateTime, Boolean, Integer, ForeignKey
from database import Base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from sqlalchemy.orm import relationship

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, autoincrement=True)  # ✅ INTEGER primary key
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    breadcrumbs = relationship("Breadcrumb", back_populates="driver", cascade="all, delete")
    batches = relationship("Batch", back_populates="driver")


class Breadcrumb(Base):
    __tablename__ = "breadcrumbs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # ✅ Add reverse relationship
    driver = relationship("Driver", back_populates="breadcrumbs")
class Batch(Base):
    __tablename__ = "batches"

    id = Column(String, primary_key=True, index=True)
    pincode = Column(String, index=True)
    total_weight = Column(Float)
    order_count = Column(Integer)

    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True) # 👈 Add this
    driver = relationship("Driver", back_populates="batches")
        # ✅ Add these two lines
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
from sqlalchemy.dialects.postgresql import UUID
import uuid

class OTPCode(Base):
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)  # ✅ MATCHING STRING
    phone_number = Column(String)
    otp = Column(String)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime)




class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    address = Column(String)  # ✅ ADD THIS LINE
    pincode = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    weight = Column(Float)       # ✅ Add this line
    payment_status = Column(String, default="unpaid") 
  # ✅ Add this line
    payment_mode = Column(String, nullable=True)
   
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)

    amount = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    batch_id = Column(String, ForeignKey("batches.id"), nullable=True)

    customer_phone = Column(String, nullable=True)
    otp_verified = Column(Boolean, default=False) 

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey("orders.id"))
    status = Column(String)
    amount = Column(Float, nullable=True)  # ✅ Add this line
    razorpay_payment_id = Column(String, nullable=True)
    payment_link_id = Column(String, nullable=True)
    signature = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    




# models.py

