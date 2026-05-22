from tools.excel_logger import save_to_excel

lead = {
    "name": "Demo Dental Clinic",
    "outreach_email": "demo@gmail.com",
    "linkedin_url": "https://linkedin.com/company/demo",
    "website": "https://demo.com"
}

save_to_excel(lead, "Sent", "Email")

print("✅ Excel updated")