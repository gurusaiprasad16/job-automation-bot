import os, requests, schedule, time, smtplib
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
from datetime import datetime

# =====================
# CONFIG (from Render Environment Variables)
# =====================
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

QUERIES = [
    "2024 fresher software developer",
    "entry level java developer",
    "backend java developer fresher",
    "sql developer fresher",
    "java full stack developer fresher"
]

# =====================
# SCRAPERS (Indeed, LinkedIn, Naukri)
# =====================
def fetch_indeed():
    job_list = []
    for query in QUERIES:
        url = f"https://in.indeed.com/jobs?q={query.replace(' ', '+')}&fromage=1"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        postings = soup.find_all("div", class_="job_seen_beacon")

        for post in postings:
            title = post.find("h2").text.strip() if post.find("h2") else "N/A"
            company = post.find("span", class_="companyName")
            company = company.text.strip() if company else "N/A"
            link = "https://in.indeed.com" + post.find("a")["href"]
            job_list.append({"Job Title": title, "Company": company, "Link": link, "Source": "Indeed"})
    return job_list

def fetch_linkedin():
    job_list = []
    for query in QUERIES:
        url = f"https://www.linkedin.com/jobs/search/?keywords={query.replace(' ', '%20')}&f_TPR=r86400"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        postings = soup.find_all("div", class_="base-card")

        for post in postings:
            title = post.find("h3", class_="base-search-card__title")
            company = post.find("h4", class_="base-search-card__subtitle")
            link_tag = post.find("a", class_="base-card__full-link")
            job_list.append({
                "Job Title": title.text.strip() if title else "N/A",
                "Company": company.text.strip() if company else "N/A",
                "Link": link_tag["href"] if link_tag else "N/A",
                "Source": "LinkedIn"
            })
    return job_list

def fetch_naukri():
    job_list = []
    for query in QUERIES:
        url = f"https://www.naukri.com/{query.replace(' ', '-')}-jobs"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        postings = soup.find_all("article", class_="jobTuple")

        for post in postings:
            title = post.find("a", class_="title")
            company = post.find("a", class_="subTitle")
            job_list.append({
                "Job Title": title.text.strip() if title else "N/A",
                "Company": company.text.strip() if company else "N/A",
                "Link": title["href"] if title else "N/A",
                "Source": "Naukri"
            })
    return job_list

# =====================
# EMAIL FUNCTION
# =====================
def send_email(jobs):
    if not jobs: return
    df = pd.DataFrame(jobs).drop_duplicates()
    html_table = df.to_html(index=False, escape=False)

    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = f"Job Updates - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    msg.attach(MIMEText(html_table, "html"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL, PASSWORD)
    server.sendmail(EMAIL, TO_EMAIL, msg.as_string())
    server.quit()
    print("✅ Email sent successfully!")

# =====================
# TASK
# =====================
def job_task():
    print(f"🔍 Running job search at {datetime.now().strftime('%H:%M')}")
    jobs = fetch_indeed() + fetch_linkedin() + fetch_naukri()
    send_email(jobs)

# Run once at startup (Render keeps process alive)
job_task()

# Schedule every 2 hours between 7 AM - 10 PM
for hour in range(7, 23, 2):
    schedule.every().day.at(f"{hour:02d}:00").do(job_task)

print("🚀 Job automation started... Running every 2 hours.")
while True:
    schedule.run_pending()
    time.sleep(60)
