from tools.email_sender import send_email

success = send_email(
    to_email="mdabdulbarimr10@gmail.com",
    subject="SMTP Test",
    body="✅ Your AI Sales Automation email system is working.",
    sender_email="abdulbarimr10@gmail.com",
    app_password="wlwwouuynvttvlld"
)

print("RESULT:", success)