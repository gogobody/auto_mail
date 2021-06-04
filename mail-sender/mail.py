import requests, os
import math
import yaml
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header

"""
天气来自： http://www.tianqiapi.com/
文字图片来源：http://wufazhuce.com/
风景图：https://qqlykm.cn/api/fengjing
土味情话：https://chp.shadiao.app/api.php
环境变量：
天气
TIANQI_APPID
TIANQI_APPSEC
邮件
FROM_ADDR
FROM_PSWD
TO_ADDR
"""

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'
}

# 获取当前文件路径
current_path = os.path.abspath(__file__)
father_path = os.path.abspath(os.path.dirname(current_path) + os.path.sep + ".")
config_path = os.path.join(father_path, 'config.yml')
template_path = os.path.join(father_path, 'template.html')

print("config_path:", config_path)

# 读取yml配置
def getYmlConfig(yaml_file=config_path):
    file = open(yaml_file, 'r', encoding="utf-8")
    file_data = file.read()
    file.close()
    config = yaml.load(file_data, Loader=yaml.FullLoader)
    return dict(config)


config = getYmlConfig()
application = config['application']
girlfriend = config['girlfriend']


# 获取天气信息，今天的和明天的
def getWeather(city):
    try:
        appid = os.environ["TIANQI_APPID"]
        appsecret = os.environ["TIANQI_APPSEC"]
    except KeyError:
        appid = application['weather']['appid']
        appsecret = application['weather']['appsecret']
    url = 'https://tianqiapi.com/api?version=v1&city={city}&appid={appid}&appsecret={appsecret}'.format(city=city,
                                                                                                        appid=appid,
                                                                                                        appsecret=appsecret)
    res = requests.get(url)
    if res.json().get("errcode", 0) > 0:
        print(res.json().get("errmsg"))
        exit(0)
    data = res.json()['data']
    return {
        'today': data[0],
        'tomorrow': data[1],
        'aftertomorrow': data[2]
    }


# 获取土味情话，有时候很智障
def getSweetWord():
    url = 'https://chp.shadiao.app/api.php'
    res = requests.get(url)
    return res.text


def getImgWords():
    src = 'https://qqlykm.cn/api/fengjing'
    text = getSweetWord()
    return src, text


# 模板消息，有能力的话，可以自己修改这个模板
def getMessage():
    now = datetime.now()
    start = datetime.strptime(girlfriend['start_love_date'], "%Y-%m-%d")
    days = (now - start).days
    city = girlfriend['city']
    boyname = girlfriend['boyname']
    girlname = girlfriend['girlname']
    weather = getWeather(city=city)
    today = weather['today']
    tomorrow = weather['tomorrow']
    aftertomorrow = weather['aftertomorrow']
    today_avg = (int(today['tem1'][:-1]) + int(today['tem2'][:-1])) / 2
    tomorrow_avg = (int(tomorrow['tem1'][:-1]) + int(tomorrow['tem2'][:-1])) / 2
    wdc = '明天'
    if today_avg > tomorrow_avg:
        wdc += '下降'
        wdc += str(abs(tomorrow_avg - today_avg)) + "℃"
    elif math.isclose(tomorrow_avg, today_avg):
        wdc += '保持不变'
    else:
        wdc += '上升'
        wdc += str(abs(tomorrow_avg - today_avg)) + "℃"
    wdc += '。'
    clothes_tip = tomorrow['index'][3]['desc']

    img, desc = getImgWords()
    with open(template_path, encoding='utf-8') as f:
        html = f.read()
        today_w = '今天 {} {}/{} 空气指数:{} 日出日落: {}/{}'.format(today['wea'], today['tem1'], today['tem2'],
                                                           today['air_level'], today['sunrise'], today['sunset'])
        tomorrow_w = '明天 {} {}/{} 空气指数:{} 日出日落: {}/{}'.format(tomorrow['wea'], tomorrow['tem1'], tomorrow['tem2'],
                                                              tomorrow['air_level'], tomorrow['sunrise'],
                                                              tomorrow['sunset'])
        aftertomorrow_w = '后天 {} {}/{} 空气指数:{} 日出日落: {}/{}'.format(aftertomorrow['wea'], aftertomorrow['tem1'],
                                                                   aftertomorrow['tem2'],
                                                                   aftertomorrow['air_level'], aftertomorrow['sunrise'],
                                                                   aftertomorrow['sunset'])
        html = html.replace('{{$day}}', str(days)).replace('{{today}}', today_w). \
            replace('{{tomorrow}}', tomorrow_w).replace('{{aftertomorrow}}', aftertomorrow_w). \
            replace('{{datetime}}', today['date']).replace('{{summary}}', wdc + clothes_tip).replace('{{$img}}', img). \
            replace('{{$desc}}', desc).replace('{{boyname}}', boyname).replace('{{girlname}}', girlname)
        return html


def sendQQMail():
    mail_host = application['mail']['host']
    mail_port = application['mail']['port']
    boyname = girlfriend['boyname']
    girlname = girlfriend['girlname']
    try:
        mail_user = os.environ['FROM_ADDR']
    except KeyError:
        mail_user = application['mail']['username']
    try:
        mail_pass = os.environ['FROM_PSWD']
    except KeyError:
        mail_pass = application['mail']['password']
    try:
        receivers = os.environ['TO_ADDR']
    except KeyError:
        receivers = girlfriend['mails']
    encoding = application['mail']['default-encoding']

    mail_msg = getMessage()
    # print(mail_msg)
    message = MIMEText(mail_msg, 'HTML', encoding)
    message['From'] = Header('{}<{}>'.format(boyname, mail_user), encoding)
    if type(receivers) == str:
        receivers = [receivers]
    receivers.append(mail_user)
    message['To'] = ','.join('receiver_name{} <{}>'.format(index, i) for index, i in enumerate(receivers))

    subject = application['name']
    message['Subject'] = Header(subject, 'utf-8')

    smtpObj = smtplib.SMTP_SSL(mail_host, mail_port)
    smtpObj.login(mail_user, mail_pass)
    smtpObj.sendmail(mail_user, receivers, message.as_string())


def main_handler():
    try:
        sendQQMail()
    except Exception as e:
        print('出现错误')
        raise e
    else:
        return 'success'


if __name__ == '__main__':
    print(main_handler())
