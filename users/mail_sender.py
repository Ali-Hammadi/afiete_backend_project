from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def send_professional_email(receiver_email, process, otp=None, user_name="User"):
    # 1. تحديد بيانات الإيميل بناءً على القيمة التي تصل
    # إذا كان الـ process عبارة عن أرقام (OTP)، نعتبره هو الكود ونضبط العملية تلقائياً
    if str(process).isdigit() and len(str(process)) <= 4:
        otp = process  # <--- هذا هو التعديل الجوهري: نقل قيمة الكود إلى متغير otp
        process = "verification"  # نحدد نوع العملية يدوياً لأنك ترسل الكود مكانها
    
    # 2. قاموس البيانات
    email_data = {
        "verification": {
            "subject": "Verify Your Account - Afiete",
            "body": "Welcome to Afiete! To complete your verification, please use the following code:",
            "action_url": None, 
            "button_text": "Visit Afiete"
        },
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
            "button_text": "Reset Password"
        }
    }

    # الحصول على البيانات (مع توفير قيم افتراضية إذا لم يتطابق الـ process)
    default_info = {"subject": "Update from Afiete", "body": "Thank you for using Afiete.", "action_url": None, "button_text": "Visit Afiete"}
    info = email_data.get(process, default_info)
    
    # 3. تجهيز السياق للقالب (Context)
    context = {
        "title": info["subject"],
        "user_name": user_name,
        "message_body": info["body"],
        "otp_code": otp,  # الآن أصبح الـ otp يحتوي على القيمة الصحيحة
        "action_url": info.get("action_url"), 
        "button_text": info.get("button_text")
    }

    # 4. إعداد وإرسال الإيميل
    html_content = render_to_string('emails/base_email.html', context)
    text_content = "Please view this email in an HTML-compatible client to see the verification code properly."

    msg = EmailMultiAlternatives(
        subject=info["subject"],
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