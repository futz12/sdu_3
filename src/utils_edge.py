import re
import time
import chardet
import codecs

import threading

import bs4

import requests
from selenium import webdriver

import src.utils_pdf as pdf
from src.varlist import sdu3_db
from src.varlist import debug
from src.varlist import loop_message_time

import src.utils_download as dl

url_msg_list = 'https://www.bkjx.sdu.edu.cn/sanji_list.jsp?totalpage=%d&PAGENUM=%d&urltype=tree.TreeTempUrl&wbtreeid=1010'
url_msg_hand = 'https://www.bkjx.sdu.edu.cn/'

# 智能识别通知的正文部分
'''
{
    url:
    title:
    post_date:
    recv_date:
}
'''


class message_server:  # 自动爬取通知
    _clock = loop_message_time  # 10min爬取一次
    _count = 0

    def __init__(self, clock=loop_message_time):
        self._clock = clock
        # 启动一个线程
        _thread = threading.Thread(target=self._loop)
        _thread.setDaemon(True)
        _thread.start()

    def _loop(self):
        self.db = sdu3_db()
        while True:
            print('成功启动自动爬取通知服务')
            print('爬取周期为 %d 秒' % self._clock)
            self._count += 1
            print('这是第 %d 次爬取' % self._count)
            self._view_and_get_list()
            time.sleep(self._clock)

    def _get_maintext_and_time(self, url):
        # 判断是不是 UTF8-DOM
        data = requests.get(url).content
        if chardet.detect(data)['encoding'] == 'utf-8':
            if data[:3] == codecs.BOM_UTF8:
                data = data[3:]

        data = data.decode(chardet.detect(data)['encoding'], 'ignore')

        soup = bs4.BeautifulSoup(data, 'html.parser')
        # 提取正文
        # <div class="v_news_content">
        text = soup.find('div', class_='v_news_content').getText()

        # 提取时间
        # 2023-10-25 08:51:09
        post_time = re.findall(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', data)
        if len(post_time) == 0:
            return [text, '']
        else:
            return [text, post_time[0]]

    def _view_and_get_list(self):
        data = requests.get('https://www.bkjx.sdu.edu.cn/sanji_list.jsp?urltype=tree.TreeTempUrl&wbtreeid=1010').text
        # <td nowrap="" align="left" width="1%" id="fanye128813">共2499条&nbsp;&nbsp;1/167&nbsp;</td>

        # 获取页数 167
        page_num = re.findall(r'共\d+条&nbsp;&nbsp;\d+/(\d+)&nbsp;', data)[0]
        print('page_num = ' + page_num)
        if debug:
            page_num = 1

        opt = webdriver.EdgeOptions()
        opt.add_argument('--headless')

        driver = webdriver.Edge(opt)

        images = []

        '''
        <a href="***" target="_blank" title="关于做好济南校本部2023级本科新生图像信息采集工作的通知" style="">关于做好济南校本部2023级本科新生图像信息采集工作的通知</a>
        <div style="float:right;">[2023-09-14]</div>

        a. url: content.jsp?urltype=news.NewsContentUrl&amp;wbtreeid=1019&amp;wbnewsid=36758

        norn url: https://www.bkjx.sdu.edu.cn/content.jsp?urltype=news.NewsContentUrl&wbtreeid=1019&wbnewsid=36758

        other url: https://www.ipo.sdu.edu.cn/wdhcontent.jsp?urltype=news.NewsContentUrl&amp;wbtreeid=1006&amp;wbnewsid=3671
        '''

        flag = False  # 只增量更新，有老的就不要了

        for i in range(1, page_num + 1):
            driver.get(url_msg_list % (page_num, i))
            # 判断是否加载完毕，完毕就截图
            driver.implicitly_wait(5)

            # 作用是调整大小 截取整个网页
            width = driver.execute_script("return document.documentElement.scrollWidth")
            height = driver.execute_script("return document.documentElement.scrollHeight")
            driver.set_window_size(width, height)

            # 给<div class="right-subpage">截图
            images.append(driver.find_element('class name', 'right-subpage').screenshot_as_png)

            if flag:
                continue  # 但是图片还是要截的

            data = driver.page_source
            title = re.findall(r'<a href=".*?" target="_blank" title="(.*?)" style="">', data)
            url = re.findall(r'<a href="(.*?)" target="_blank" title=".*?" style="">', data)
            date = re.findall(r'<div style="float:right;">\[(.*?)\]</div>', data)

            for j in range(0, len(url)):
                # &amp; -> &
                url[j] = url[j].replace('&amp;', '&')

                if url[j].find('http') == -1:  # 相对路径转换
                    url[j] = url_msg_hand + url[j]
                else:
                    print('find other url: ' + url[j])

                if self.db.have_message(url[j]):
                    flag = True
                    break  # 网页上的链接顺序一般是时间顺序，出现一个重复的就可以停止了
                    # year-mo-day

                info = self._get_maintext_and_time(url[j])  # [text, post_time]
                if info[1] == '':
                    self.db.insert_message(url[j], title[j], date[j], time.strftime("%Y-%m-%d", time.localtime()),
                                           info[0])
                else:
                    self.db.insert_message(url[j], title[j], info[1], time.strftime("%Y-%m-%d", time.localtime()),
                                           info[0])
                # 单独给每个网页截图
                images_sub = []

                # !!! 这里还有些bug

                driver.get(url[j])
                driver.implicitly_wait(5)

                # 中间先插一段下载附件的吧

                # <a href="/system/_content/download.jsp?urltype=news.DownloadAttachUrl&amp;owner=1348324972&amp;wbfileid=13117233" target="_blank">山东大学2023年高质量教材出版资助清单.pdf</a>

                # 先判断有没有
                data = driver.page_source
                file_link = re.findall(r'<a href="(.*?)" target="_blank">(.*?)</a>', data)
                for k in range(0, len(file_link)):
                    if file_link[k][0].find('/system') == -1:
                        print('find other file: ' + file_link[k][1])
                        continue  # 不是附件
                    print('find file: ' + file_link[k][0])
                    # 下载到 /file/title/xxx
                    dl.download_file(file_link[k][0], 'file/' + title[j] + '/' + file_link[k][1])
                # 结束插入

                # 作用是调整大小 截取整个网页
                width_sub = driver.execute_script("return document.documentElement.scrollWidth")
                height_sub = driver.execute_script("return document.documentElement.scrollHeight")
                # print(width_sub, height_sub)
                driver.set_window_size(width_sub, height_sub)

                # 给 <form name="_newscontent_fromname"> 截图
                images_sub.append(driver.find_element('name', '_newscontent_fromname').screenshot_as_png)

                pdf.imgs2pdf(images_sub, 'pdf/' + date[j] + ' ' + title[j] + '.pdf')

        pdf.imgs2pdf(images, 'pdf/main.pdf')
        print("done edge")
