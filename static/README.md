# SiloDispatch

A backend system for efficient logistics, optimized batching, and payment management for field delivery agents.

## Features

- 🧩 Batch Creation (Clustering)
  - Group orders by pincode or Haversine distance
  - Limits: max 25kg or 30 orders per batch

- 🚚 Driver Assignment & Tracking
  - Manual & auto-assignment
  - Breadcrumb GPS support

- ✅ OTP Delivery Verification
  - OTP sent via AWS SNS
  - Secure delivery confirmation

- 💰 Payment Support
  - COD, UPI, Prepaid
  - Razorpay integration
  - Webhook-based update handling

- 📊 Settlement & Reporting
  - Live driver COD balance
  - One-click settlement with timestamp
  - CSV export for finance

## Tech Stack

- FastAPI + Jinja2
- PostgreSQL (via SQLAlchemy)
- Razorpay API
- AWS SNS for OTP
- HTML frontend

## Developer Setup

```bash
git clone <repo-url>
cd silodispatch
pip install -r requirements.txt
uvicorn main:app --reload
