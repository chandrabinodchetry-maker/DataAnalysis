from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import sqlite3
import pandas as pd
from typing import Optional
# Import your Irish jobs functions if needed
from irish_job import fetch_jobs, preprocess, addfeatur, classify_job_type, standardize_county, save_to_db, url, headers, cookies

# THIS MUST COME FIRST
app = FastAPI()
DB_PATH = "jobs1.db"

@app.get("/")
def root():
    return {"message": "Irish Jobs API is running!"}

@app.get("/jobs", response_class=HTMLResponse)
def get_jobs(
    title: Optional[str] = None,
    companyName: Optional[str] = None,
    location: Optional[str] = None,
    salary: Optional[str] = None,
    job_type: Optional[str] = None,
    isActive: Optional[bool] = None,
    is_recent: Optional[bool] = None
):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM irish_jobs", conn)
    conn.close()

    # Apply filters (same as before)
    if title:
        df = df[df["title"].str.contains(title, case=False, na=False)]
    if companyName:
        df = df[df["companyName"].str.contains(companyName, case=False, na=False)]
    if location:
        df = df[df["location"].str.contains(location, case=False, na=False)]
    if salary:
        df = df[df["salary"].str.contains(salary, case=False, na=False)]
    if job_type:
        df = df[df["job_type"].str.contains(job_type, case=False, na=False)]
    if isActive is not None:
        df = df[df["isActive"] == isActive]
    if is_recent is not None:
        df = df[df["is_recent"] == is_recent]

    # --- Add Apply button ---
    # Make a copy so we don't touch original columns # AI LLM Chat GPT
    df_display = df.copy()
    if "url" in df_display.columns:
        df_display["Apply"] = df_display["url"].apply(
            lambda x: f'<a href="{x}" target="_blank">Apply</a>'
        )
    else:
        df_display["Apply"] = ""

    # Add job description column if it exists
    if "description" not in df_display.columns:
        df_display["description"] = "No description available"

    # Reorder columns to show description and Apply last
    columns_order = [col for col in df_display.columns if col not in ["description", "Apply"]] + ["description", "Apply"]
    df_display = df_display[columns_order]

    # Convert to HTML table   #AI ChatGpT.
    html = df_display.to_html(escape=False, classes="table table-striped", index=False)

    return HTMLResponse(content=f"""  
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 8px; border: 1px solid #ccc; }}
            th {{ background-color: #f2f2f2; }}
            a {{ text-decoration: none; color: white; background-color: #007BFF; padding: 5px 10px; border-radius: 4px; }}
            a:hover {{ background-color: #0056b3; }}
        </style>
    </head>
    <body>
        <h2>Irish Jobs – Table View</h2>
        {html}
    </body>
    </html>
    """)
