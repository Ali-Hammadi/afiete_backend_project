from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def send_professional_email(receiver_email, process, otp=None, user_name="User"):
    # 1. تحديد بيانات الإيميل بناءً على العملية (Process)
    email_data = {
        "verification": {
            "subject": "Verify Your Account - Afiete",
            "body": "Welcome to Afiete! To complete your verification, please use the following code:",
            "action_url": None, 
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
        }
    }

    # الحصول على البيانات، أو إرجاع قيم افتراضية
    default_info = {"subject": "Update from Afiete", "body": "Thank you for using Afiete.", "action_url": "https://alihammadi.pythonanywhere.com/"}
    info = email_data.get(process, default_info)

    # 2. تجهيز السياق للقالب (Context)
    # هنا التعديل السحري: تم فصل الـ otp وتمريره باسم otp_code ليتعرف عليه الـ HTML
    context = {
        "title": info["subject"],
        "user_name": user_name,
        "message_body": info["body"],
        "otp_code": otp,  # 👈 هذا ما سيُظهر المربع الأزرق الأنيق
        "action_url": info.get("action_url"), # 👈 هذا سيخفي الزر إذا كانت القيمة None
        "button_text": info.get("button_text", "Visit Afiete")
    }

    # 3. تحويل القالب لـ HTML
    html_content = render_to_string('emails/base_email.html', context)
    text_content = "Please view this email in an HTML-compatible client to see the verification code properly."

    # 4. إعداد وإرسال الإيميل
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