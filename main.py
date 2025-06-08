
import json, os
from pathlib import Path
from datetime import date

from job_search import search_jobs, canonical_url
from bot_notify import send_message, await_reply, send_document
from cv_tailor import tailor_cv
from apply_via_email import send_application

HISTORY_FILE = Path("history.json")

def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return {"seen_links": [], "applied_links": []}

def save_history(hist):
    HISTORY_FILE.write_text(json.dumps(hist, indent=2))

def run():
    hist = load_history()
    new_jobs = [j for j in search_jobs() if canonical_url(j["link"]) not in hist["seen_links"]]
    if not new_jobs:
        send_message("🏖 No new jobs today — have fun at the beach!")
        print("INFO: sent beach message")
        return        
    msg_lines = [f"🌍 New roles for {date.today().isoformat()}"]
    for idx, job in enumerate(new_jobs, 1):
        msg_lines.append(f"{idx}. {job['title']} — {job['company']} — {job['location']}")
        msg_lines.append(job["link"])
    send_message("\n".join(msg_lines))
    choice_text = await_reply()
    chosen_idxs = {int(x) for x in choice_text.replace(',', ' ').split() if x.isdigit()}
    for idx in chosen_idxs:
        if 1 <= idx <= len(new_jobs):
            job = new_jobs[idx-1]
            cv_path = tailor_cv(job)
            send_document(cv_path, caption=f"CV for {job['company']}")
            if os.getenv("GMAIL_USER") and os.getenv("GMAIL_APP_PASSWORD"):
                send_application(job, cv_path)
            hist["applied_links"].append(canonical_url(job["link"]))
    hist["seen_links"].extend(canonical_url(j["link"]) for j in new_jobs)
    save_history(hist)

if __name__ == "__main__":
    run()
