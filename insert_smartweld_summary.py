from pymongo import MongoClient
from datetime import datetime

# MongoDB connection settings
MONGODB_URI = "mongodb+srv://Aniruddha:7711@cluster0.8c5tyma.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "smart_weld_blogs"
COLLECTION_NAME = "product_knowledge"

# SmartWeld summary (truncated into a dictionary for structured storage)
smartweld_summary = {
    "title": "SmartWeld – Welding Management Software",
    "overview": "SmartWeld is an IIoT-based Welding Management Software for companies of all sizes...",
    "features": [
        "Real-time monitoring of weld parameters",
        "Full traceability of each weld, operator, and machine",
        "Root Cause Analysis with alerts",
        "Centralized data repository with dashboards",
        "Predictive analytics and forecasting models",
        "Reduced lead time and machine downtime",
        "Smart card-enabled welder tracking",
        "Cloud-based and on-premise deployment"
    ],
    "benefits": [
        "20–35% increase in productivity",
        "30–35% quality improvement",
        "20–30% cost reduction",
        "24x7 weld data logging and accessibility",
        "Supports multiple arc welding processes",
        "Compatible with any brand/make of machine"
    ],
    "technology": {
        "data_transfer": ["GSM SIM", "Wi-Fi"],
        "offline_storage": "Up to 10 hours (4000 records)",
        "security": "Encrypted cloud storage",
        "accessibility": "Any device: PC, tablet, smartphone"
    },
    "modules": [
        "Realtime Monitoring", "Traceability", "Cost Optimization",
        "Welder Performance Oversight", "Alerts & Notifications",
        "Predictive Maintenance", "Weld Data Documentation"
    ],
    "business_model": {
        "subscription": "Customized after site assessment",
        "clients": ["BHEL Trichy", "Medium fabricators"],
        "contact": {
            "phone": ["+91 94346 41479", "+91 8882331144"],
            "email": "support@smart-weld.com"
        }
    },
    "vision": "To lead globally in Welding + IIoT + AI/ML with real-time, smart, and reliable solutions.",
    "timestamp": datetime.utcnow()
}

# Connect and insert into MongoDB
client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Insert the document
result = collection.insert_one(smartweld_summary)

print(f"SmartWeld summary inserted with ID: {result.inserted_id}")
