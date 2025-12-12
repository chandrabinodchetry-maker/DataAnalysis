import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import subprocess
import smtplib
from email.mime.text import MIMEText
import os

# --- Configuration ---
PROJECT_DIR = os.getenv("JOBS_PROJECT_DIR", "/home/azureuser/IrishJobsAPI")
DB_PATH = os.path.join(PROJECT_DIR, "jobs1.db")

# Environment variables for email
EMAIL_FROM = os.getenv("JOBS_EMAIL")  
EMAIL_PASS = os.getenv("JOBS_APP_PASSWORD") 
EMAIL_TO = "chandra.binod.chetry@gmail.com"  # recipient

def send_email(new_jobs_df):
    """Sends an email with the new jobs found in HTML table format."""
    if not EMAIL_FROM or not EMAIL_PASS:
        print("Email credentials (JOBS_EMAIL or JOBS_APP_PASSWORD) not set.")
        return

    # Only keep relevant columns
    columns_for_email = ["title", "companyName", "location", "salary", "datePosted", "url", "job_type"]
    df_email = new_jobs_df[columns_for_email]

    # Convert to HTML table (URLs remain clickable)
    html_body = f"""
    <html>
        <body>
            <h2>New Jobs added in the last 24 hours</h2>
            {df_email.to_html(index=False, escape=False)}
        </body>
    </html>
    """

    # Create HTML email
    msg = MIMEText(html_body, 'html')
    msg['Subject'] = "New Job Postings (Last 24 Hours)"
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASS)
            server.send_message(msg)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

def main():
    print(f"Starting job execution from directory: {PROJECT_DIR}")
    
    # 1️⃣ Run the scraping pipeline
    try:
        print("1. Running job scraping pipeline (updates DB)...")
        subprocess.run(
            ["python3", os.path.join(PROJECT_DIR, "irish_job.py")],
            check=True,
            cwd=PROJECT_DIR 
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running the scraping job (irish_job.py): {e}")
        return 

    # 2️⃣ Load updated DB
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM irish_jobs", conn) 
        conn.close()
    except Exception as e:
        print(f"Error reading from database at {DB_PATH}: {e}")
        return

    if df.empty:
        print("2. Database is empty, no jobs to check.")
        return

    # 3️⃣ Filter jobs posted in the last 24 hours
    print("3. Filtering for new jobs in the last 24 hours...")
    df["datePosted"] = pd.to_datetime(df["datePosted"], errors='coerce')
    cutoff_time = datetime.now() - timedelta(hours=24)
    new_jobs_df = df[df["datePosted"] >= cutoff_time].dropna(subset=["datePosted"])

    if not new_jobs_df.empty:
        print(f"Found {len(new_jobs_df)} new jobs.")
        send_email(new_jobs_df)
    else:
        print("4. No new jobs found in the last 24 hours.")

if __name__ == "__main__":
    main()
