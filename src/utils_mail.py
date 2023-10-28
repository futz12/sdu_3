import smtplib
from email.mime.text import MIMEText

push_mail = 'xxx@163.com'
push_mail_password = 'password'

get_mail = 'xxx@qq.com'


def push_message(title, message):
    msg = MIMEText(message)
    msg['Subject'] = title
    msg['From'] = push_mail
    msg['To'] = get_mail
    s = smtplib.SMTP_SSL('smtp.163.com', 465)
    s.login(push_mail, push_mail_password)
    s.sendmail(push_mail, get_mail, msg.as_string())
    s.quit()
