import requests
import ddddocr
import os

url_file = 'https://www.bkjx.sdu.edu.cn'
url_captcha = 'https://www.bkjx.sdu.edu.cn/system/resource/js/filedownload/createimage.jsp'


# https://www.bkjx.sdu.edu.cn/system/_content/download.jsp?urltype=news.DownloadAttachUrl&owner=1348324972&wbfileid=13115496&codeValue=%s

# 获取并识别验证码
def get_codeValue():
    ret = requests.get(url_captcha)
    img_data = ret.content
    # ocr
    ocr = ddddocr.DdddOcr(show_ad=False)
    code = ocr.classification(img_data)
    print(code)
    # 输出图片
    # with open('captcha.jpg', 'wb') as f:
    #    f.write(img_data)
    return [code, ret.cookies]  # 验证码是什么不重要 重要的是cookies


# <RequestsCookieJar[<Cookie JSESSIONID=F4D88F8CAD77D1DEF20C3A04547A8195 for www.bkjx.sdu.edu.cn/>]>


def download_file(file_url, save_file):
    # 如果文件不在就再创建
    if not os.path.exists(os.path.dirname(save_file)):
        os.makedirs(os.path.dirname(save_file))
    # &amp; -> &
    file_url = file_url.replace('&amp;', '&')
    access_token = get_codeValue()
    print(url_file + file_url + '&codeValue=' + access_token[0])
    data = requests.get(url_file + file_url + '&codeValue=' + access_token[0], cookies=access_token[1]).content
    with open(save_file, 'wb') as f:
        f.write(data)
