# backend/utils.py
import pandas as pd
import numpy as np
from io import BytesIO
from fastapi import UploadFile
from fastapi.responses import StreamingResponse
from typing import List
import openpyxl
import smtplib
from email.message import EmailMessage
import os
import requests
import logging

# Logger setup
logger = logging.getLogger(__name__)

# Dummy CRM integration
def send_to_crm(lead_data: dict):
    url = "https://saasquatchleads.com/api/leads"
    try:
        response = requests.post(url, json=lead_data)
        logger.info(f"Sent data to CRM, status code: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send to CRM: {e}")
        return False

def clean_and_score(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Cleaning and scoring dataframe.")
    df = df.fillna("")
    if "industry" not in df.columns:
        logger.warning("Column 'industry' not found in dataframe.")
        df["industry"] = ""
    df["score"] = df["industry"].apply(lambda x: 90 if "Finance" in x else 50)
    df["priority"] = pd.cut(df["score"], bins=[0, 60, 80, 100], labels=["Low", "Medium", "High"])
    logger.debug(f"Scored dataframe head: \n{df.head()}")
    return df

def export_to_excel(df: pd.DataFrame) -> StreamingResponse:
    logger.info("Exporting dataframe to Excel.")
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    logger.info("Excel export completed.")
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": "attachment; filename=lead_report.xlsx"}
    )

def send_email_with_attachment(to_email: str, df: pd.DataFrame):
    logger.info(f"Preparing to send email to {to_email}.")
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)

    msg = EmailMessage()
    msg['Subject'] = 'Lead Scoring Report'
    msg['From'] = os.getenv("EMAIL_SENDER")
    msg['To'] = to_email
    msg.set_content("Please find attached the lead scoring report.")
    msg.add_attachment(
        output.read(),
        maintype='application',
        subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename="report.xlsx"
    )

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(os.getenv("EMAIL_SENDER"), os.getenv("EMAIL_PASSWORD"))
            smtp.send_message(msg)
        logger.info("Email sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
