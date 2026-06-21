import smtplib
from email.message import EmailMessage
def send_mail(to,subject,body):
    server=smtplib.SMTP_SSL('smtp.gmail.com',465)
    server.login('svppcai@gmail.com','etnb eqod xvgh relk')
    msg=EmailMessage()
    msg['FROM']='svppcai@gmail.com'
    msg['TO']=to
    msg['SUBJECT']=subject
    msg.set_content(body)
    server.send_message(msg)
    print('Mail sent successfully')
    server.close()