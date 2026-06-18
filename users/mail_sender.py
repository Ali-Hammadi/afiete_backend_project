from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def send_professional_email(receiver_email, process, otp=None, user_name="User"):
    # 1. تحديد بيانات الإيميل بناءً على العملية (Process)
    email_data = {
        "verification": {
            "subject": "Verify Your Account - Afiete",
            "body": f"Welcome to Afiete! To complete your verification, please use the following code: <strong>{otp}</strong>"
        },
        "Doctor Accepted": {
            "subject": "Afiete - Doctor Application Accepted",
            "body": "Congratulations! We are pleased to inform you that your application to join the Afiete team has been accepted."
        },
        "Doctor Rejected": {
            "subject": "Afiete - Application Update",
            "body": "Thank you for your interest in Afiete. After careful review, we regret to inform you that we cannot proceed with your application at this time."
        },
        "Email Reset": {
            "subject": "Afiete - Password Reset",
            "body": f"You requested a password reset. Your OTP is: <strong>{otp}</strong>"
        }
    }

    # الحصول على البيانات، أو إرجاع قيم افتراضية إذا لم يوجد الـ process
    info = email_data.get(process, {"subject": "Update from Afiete", "body": "Thank you for using Afiete."})

    # 2. تجهيز السياق للقالب (Context)
    context = {
        "title": info["subject"],
        "user_name": user_name,
        "message_body": info["body"],
        "action_url": "https://alihammadi.pythonanywhere.com/login" # رابط الموقع
    }

    # 3. تحويل القالب لـ HTML
    html_content = render_to_string('emails/base_email.html', context)
    text_content = "Please view this email in an HTML-compatible client."

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