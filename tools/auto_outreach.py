from dotenv import load_dotenv
import os
import time

import database.queries as db
from tools.email_sender import send_email
from tools.excel_logger import save_to_excel

def generate_and_send_email(lead, user_id, settings=None):
    if lead.get("email_sent") == 1:
        print(f"⚠️ Already sent to {lead.get('name')}")
        return True

    email = (lead.get("outreach_email") or "").strip()
    linkedin = (lead.get("linkedin_url") or "").strip()
    name = lead.get("name", "Business")

    message = (lead.get("email_draft") or "").strip()
    subject = f"Quick idea for {name}"

    # Delay to avoid Gmail blocking
    time.sleep(2)

    valid_email = email and "@" in email and "." in email and len(email) > 5
    valid_draft = message and len(message.strip()) >= 15

    if not valid_draft:
        print(f"❌ Empty draft for {name}")
        db.update_lead_field(lead["id"], "send_status", "Empty Draft")
        save_to_excel(lead, status="Empty Draft", action="Skipped")
        return False

    if valid_email:
        print(f"📩 Sending email to {email}...")

        success = send_email(email, subject, message, settings, user_id)

        if success:
            print(f"✅ Sent to {name}")
            db.mark_email_sent(lead["id"], "Sent")
            save_to_excel(lead, status="Sent", action="Email")
            return True
        else:
            print(f"❌ Failed sending to {name}")
            db.update_lead_field(lead["id"], "send_status", "Failed")
            save_to_excel(lead, status="Failed", action="Email")
            return False

    elif linkedin:
        print(f"⚠️ No valid email for {name}")
        db.update_lead_field(lead["id"], "send_status", "No Email")
        save_to_excel(lead, status="No Email", action="LinkedIn Follow-up")
        return False

    else:
        print(f"❌ No contact found for {name}")
        db.update_lead_field(lead["id"], "send_status", "No Contact")
        save_to_excel(lead, status="No Contact", action="Manual")
        return False