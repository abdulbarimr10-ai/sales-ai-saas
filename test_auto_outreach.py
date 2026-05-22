from tools.auto_outreach import process_lead_outreach

lead = {
    "name": "Test Clinic",
    "outreach_email": "mdabdulbarir10@gmail.com",
    "linkedin_url": "",
    "website": "https://example.com",
    "email_draft": "Hello! We help clinics automate patient follow-ups."
}

process_lead_outreach(lead)

print("✅ Outreach complete")