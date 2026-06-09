import smtplib
import ssl
from email.message import EmailMessage
import socket

def send_email(receiver_email, otp_code=None , process="verification"):

    smtp_server = "smtp.gmail.com"
    port = 587
    sender_email = "afiete2026@gmail.com"
    sender_password = "nmmsuchwtfunhwhy" # eco password not real for security
    subject = "Welcome to Afiete"
    is_html=False
    body = ' '
    if process == "verification":
        body = f"""Hello,

I hope you are doing well.

I would like to request a One-Time Password {otp_code} to complete my account verification process.
Please send the OTP to this email address or provide guidance on how I can receive it.

Thank you for your assistance.

Best regards,
Afiete Team"""
    elif process == "Doctor Accepted":
        subject = "Afiete - Doctor Accepted"
        body = f"""
        Hello Doctor, 
        We are pleased to inform you that your application to join Afiete has been accepted. 
        We look forward to having you as part of our community and working together to provide excellent healthcare"""
    
    
    elif process == "Doctor Rejected":
        subject = "Afiete - Doctor Rejected"
        body = f""" Hello Doctor,
        We regret to inform you that your application to join Afiete has been rejected. 
        We appreciate your interest in our platform and encourage you to apply again in the future.
        """
    elif process == "Email Reset":
        subject = "Afiete - Email Reset"
        body = f""" Hello,
        You have been reset email,
        wa want to check,
        your one time password otp:{otp_code}
        Afiete Team
        """
    try:
        # إنشاء الرسالة
        msg = EmailMessage()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject
        print(len(sender_password))

        if is_html:
            msg.add_alternative(body, subtype='html')
        else:
            msg.set_content(body)

        # إنشاء اتصال آمن
        context = ssl.create_default_context()

        try:
            with smtplib.SMTP(smtp_server, port, timeout=10) as server:
                server.starttls(context=context)

                try:
                    server.login(sender_email, sender_password)
                except smtplib.SMTPAuthenticationError as e:
                    # print("❌ خطأ في تسجيل الدخول: تحقق من الإيميل أو كلمة المرور")
                    # print(e)
                    return False

                try:
                    server.send_message(msg)
                    # print("✅ تم إرسال الإيميل بنجاح")
                    return True

                except smtplib.SMTPRecipientsRefused:
                    # print("❌ الإيميل المستلم مرفوض")
                    return False
                except smtplib.SMTPException as e:
                    # print(f"❌ خطأ أثناء الإرسال: {e}")
                    return False
                return False

        except smtplib.SMTPConnectError:
            # print("❌ فشل الاتصال بالسيرفر")
            return False
        except smtplib.SMTPServerDisconnected:
            # print("❌ السيرفر قطع الاتصال")
            return False    
        except socket.gaierror:
            #   print("❌ خطأ في DNS أو اسم السيرفر غير صحيح")
            return False
        except TimeoutError:
            # print("❌ انته ت مهلة الاتصال (Timeout)")
                return False
        return False

    except Exception as e:
        # print(f"❌ خطأ غير متوقع: {e}")
        return False
    