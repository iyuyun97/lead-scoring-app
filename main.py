# backend/main.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import leads

# ---------- Logging Setup ----------
logging.basicConfig(
    level=logging.INFO,  # Ubah ke DEBUG jika ingin lebih rinci
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Tampilkan di console
        # logging.FileHandler("app.log"),  # (Opsional) Simpan ke file log
    ]
)
logger = logging.getLogger(__name__)
logger.info("🚀 Starting Lead Scoring & CRM API...")

# ---------- FastAPI App Setup ----------
app = FastAPI(
    title="Lead Scoring & CRM API",
    description="API backend untuk upload, scoring, dan integrasi lead ke SaaSquatchLeads CRM",
    version="1.0.0",
)

# ---------- CORS Configuration ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ganti jadi whitelist domain saat production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Root Healthcheck ----------
@app.get("/")
def read_root():
    logger.info("📡 Health check endpoint dipanggil.")
    return {"message": "API is running."}

# ---------- Register Routers ----------
app.include_router(leads.router, prefix="/api", tags=["Lead Operations"])
