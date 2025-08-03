# backend/routers/leads.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import JSONResponse
from models import Token
from utils import clean_and_score, export_to_excel, send_email_with_attachment, send_to_crm
import pandas as pd
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
import logging

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter()
SECRET_KEY = "secret"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

# ---- AUTH ----
@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info(f"Login attempt: username={form_data.username}")
    if form_data.username == "admin" and form_data.password == "admin123":
        token = jwt.encode({"sub": form_data.username}, SECRET_KEY, algorithm="HS256")
        logger.info("Login successful")
        return {"access_token": token, "token_type": "bearer"}
    logger.warning("Login failed: incorrect credentials")
    raise HTTPException(status_code=400, detail="Incorrect username or password")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = payload.get("sub")
        logger.debug(f"Token decoded successfully for user: {user}")
        return user
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise HTTPException(status_code=403, detail="Invalid token")

# ---- ENDPOINTS ----
@router.post("/upload_csv")
def upload_csv(file: UploadFile = File(...), user: str = Depends(get_current_user)):
    logger.info(f"[{user}] Uploading CSV: {file.filename}")
    if not file.filename.endswith('.csv'):
        logger.warning("Upload failed: File is not CSV")
        raise HTTPException(status_code=400, detail="File must be a CSV")
    try:
        df = pd.read_csv(file.file)
        df = clean_and_score(df)
        logger.info(f"Processed {len(df)} records")
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error processing CSV: {e}")
        raise HTTPException(status_code=500, detail="Failed to process CSV")

@router.post("/export_excel")
def export_excel(file: UploadFile = File(...), user: str = Depends(get_current_user)):
    logger.info(f"[{user}] Requesting Excel export for: {file.filename}")
    if not file.filename.endswith('.csv'):
        logger.warning("Export failed: File is not CSV")
        raise HTTPException(status_code=400, detail="File must be a CSV")
    try:
        df = pd.read_csv(file.file)
        df = clean_and_score(df)
        logger.info(f"Exporting {len(df)} records to Excel")
        return export_to_excel(df)
    except Exception as e:
        logger.error(f"Error exporting to Excel: {e}")
        raise HTTPException(status_code=500, detail="Failed to export data")

@router.post("/email_report")
def email_report(
    file: UploadFile = File(...),
    email: str = Form(...),
    user: str = Depends(get_current_user)
):
    logger.info(f"[{user}] Sending report to email: {email}")
    if not file.filename.endswith('.csv'):
        logger.warning("Email report failed: File is not CSV")
        raise HTTPException(status_code=400, detail="File must be a CSV")
    try:
        df = pd.read_csv(file.file)
        df = clean_and_score(df)
        send_email_with_attachment(email, df)
        logger.info("Email sent successfully")
        return {"message": f"Report sent to {email}"}
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email report")

@router.post("/send_to_crm")
def send_to_crm_api(file: UploadFile = File(...), user: str = Depends(get_current_user)):
    logger.info(f"[{user}] Sending leads to CRM from: {file.filename}")
    if not file.filename.endswith('.csv'):
        logger.warning("Send to CRM failed: File is not CSV")
        raise HTTPException(status_code=400, detail="File must be a CSV")
    try:
        df = pd.read_csv(file.file)
        df = clean_and_score(df)
        results = []
        for _, row in df.iterrows():
            success = send_to_crm(row.to_dict())
            results.append({"name": row.get("name", "Unknown"), "success": success})
        logger.info(f"CRM sync completed with {len(results)} leads")
        return results
    except Exception as e:
        logger.error(f"Error sending leads to CRM: {e}")
        raise HTTPException(status_code=500, detail="Failed to send leads to CRM")
