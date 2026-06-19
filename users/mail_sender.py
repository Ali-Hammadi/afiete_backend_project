from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def send_professional_email(receiver_email, process, otp=None, user_name="User"):
    # 1. تحديد بيانات الإيميل بناءً على القيمة التي تصل (process)
    # بما أنك ترسل كود الـ OTP مكان الـ process، سنتحقق إذا كان المدخل عبارة عن أرقام (OTP)
    if str(process).isdigit() and len(str(process)) <= 4:
        subject = "Verify Your Account - Afiete"
        body = "Welcome to Afiete! To complete your verification, please use the following code:"
        action_url = None
        button_text = "Visit Afiete"
    else:
        # إذا تم إرسال نص لعملية معينة (مثل حالات الطبيب لاحقاً)
        email_data = {
            "Doctor Accepted": {
                "subject": "Afiete - Doctor Application Accepted",
                "body": "Congratulations! We are pleased to inform you that your application to join the Afiete team has been accepted.",
                "action_url": None, 
                "button_text": None
            },
            "Doctor Rejected": {
                "subject": "Afiete - Application Update",
                "body": "Thank you for your interest in Afiete. After careful review, we regret to inform you that we cannot proceed with your application at this time.",
                "action_url": None, 
                "button_text": None
            },
            "Email Reset": {
                "subject": "Afiete - Password Reset",
                "body": "You requested a password reset. Your OTP is:",
                "action_url": None, 
            }
        }
        # استخدام القيم الافتراضية بدون رابط pythonanywhere
        default_info = {"subject": "Update from Afiete", "body": "Thank you for using Afiete.", "action_url": None}
        info = email_data.get(process, default_info)
        
        subject = info["subject"]
        body = info["body"]
        action_url = info.get("action_url")
        button_text = info.get("button_text", "Visit Afiete")

    # 2. تجهيز السياق للقالب (Context)
    context = {
        "title": subject,
        "user_name": user_name,
        "message_body": body,
        "otp_code": otp, 
        "action_url": action_url, 
        "button_text": button_text
    }

    # 3. تحويل القالب لـ HTML
    html_content = render_to_string('emails/base_email.html', context)
    text_content = "Please view this email in an HTML-compatible client to see the verification code properly."

    # 4. إعداد وإرسال الإيميل
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[receiver_email]
    )
    
    msg.attach_alternative(html_content, "text/html")
    
    try:
        msg.send()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False