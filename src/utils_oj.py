import json
import os
import threading

import requests

import time

from src.utils_db import submit_max

from src.varlist import db
from src.varlist import sdu3_db

from src.varlist import loop_flush_submit_time

from src.varlist import push_message as pm

url_oj_problem = 'https://oj.qd.sdu.edu.cn/api/problem/list?pageNow=1&pageSize='
url_oj_submit = 'https://oj.qd.sdu.edu.cn/api/submit/list?pageNow=1&pageSize='
url_oj_login = 'https://oj.qd.sdu.edu.cn/api/user/login'
url_oj_group = 'https://oj.qd.sdu.edu.cn/api/group/query?groupId='
url_oj_submit_contest = 'https://oj.qd.sdu.edu.cn/api/contest/listSubmission?pageNow=1&pageSize=%d&contestId=%s'

'''
 0 Not Submit
 1 Accept
 2 TLE
 4 RE
 6 WA
 8 CE
'''

user_info = None


def get_list_problem():
    ret = requests.get(url_oj_problem + str(1)).text

    data = json.loads(ret)

    code = data['code']
    if code != 0:
        print('error')
        return []
    totalNum = int(data['data']['totalNum'])

    ret = requests.get(url_oj_problem + str(totalNum)).text
    data = json.loads(ret)
    if code != 0:
        print('error')
        return []
    return data['data']['rows']


def get_list_submit():
    ret = requests.get(url_oj_submit + str(submit_max)).text

    data = json.loads(ret)

    code = data['code']
    if code != 0:
        print('error')
        return []
    return data['data']['rows']


def login_and_get_cookies(username, password):
    """ Hander

        accept: application/json, text/plain, */*
        accept-language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6
        cache-control: no-cache, no-store, must-revalidate
        content-type: application/json;charset=UTF-8
        origin: https://oj.qd.sdu.edu.cn
        referer: https://oj.qd.sdu.edu.cn/v2/login?to=/v2/home
        sec-ch-ua: "Chromium";v="118", "Microsoft Edge";v="118", "Not=A?Brand";v="99"
        sec-ch-ua-mobile: ?0
        sec-ch-ua-platform: "Windows"
    """

    data = {
        'username': username,
        'password': password
    }
    # 注入Hander
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache, no-store, must-revalidate',
        'content-type': 'application/json;charset=UTF-8',
        'origin': 'https://oj.qd.sdu.edu.cn',
        'referer': 'https://oj.qd.sdu.edu.cn/v2/login?to=/v2/home',
        'sec-ch-ua': '"Chromium";v="118", "Microsoft Edge";v="118", "Not=A?Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }
    ret = requests.post(url_oj_login, data=json.dumps(data), headers=headers)
    data = ret.text
    data = json.loads(data)
    code = data['code']
    if code != 0:
        print(data['message'])
        return None

    print('login success', {data['data']['userId'], data['data']['username'], data['data']['nickname']})
    # 提取cookies
    print(ret.cookies.get_dict())

    global user_info
    user_info = ret.cookies
    return ret.cookies.get_dict()


# https://oj.qd.sdu.edu.cn/api/group/page?pageNow=1&pageSize=%d&isParticipating=1

def get_group_list():
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache, no-store, must-revalidate',
        'content-type': 'application/json;charset=UTF-8',
        'origin': 'https://oj.qd.sdu.edu.cn',
        'referer': 'https://oj.qd.sdu.edu.cn/v2/group',
        'sec-ch-ua': '"Chromium";v="118", "Microsoft Edge";v="118", "Not=A?Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    # 需要登入
    data = requests.get('https://oj.qd.sdu.edu.cn/api/group/page?pageNow=1&pageSize=1&isParticipating=1',
                        headers=headers, cookies=user_info).text
    data = json.loads(data)
    code = data['code']
    if code != 0:
        print(data['message'])
        return []

    totalNum = int(data['data']['totalNum'])
    print('find totalNum group = %d' % (totalNum))

    data = requests.get('https://oj.qd.sdu.edu.cn/api/group/page?pageNow=1&pageSize=%s&isParticipating=1' % totalNum,
                        headers=headers, cookies=user_info).text
    data = json.loads(data)
    code = data['code']
    if code != 0:
        print(data['message'])
        return []
    return data['data']['rows']


# https://oj.qd.sdu.edu.cn/api/group/query?groupId=53
# From https://oj.qd.sdu.edu.cn/v2/group/53

def get_group_member_list(groupId):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache, no-store, must-revalidate',
        'content-type': 'application/json;charset=UTF-8',
        'origin': 'https://oj.qd.sdu.edu.cn',
        'referer': 'https://oj.qd.sdu.edu.cn/v2/group/' + str(groupId),
        'sec-ch-ua': '"Chromium";v="118", "Microsoft Edge";v="118", "Not=A?Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    # 需要登入
    data = requests.get('https://oj.qd.sdu.edu.cn/api/group/query?groupId=' + groupId,
                        headers=headers, cookies=user_info).text
    data = json.loads(data)
    code = data['code']
    if code != 0:
        print(data['message'])
        return []

    return data['data']['members']

# https://oj.qd.sdu.edu.cn/api/contest/list?pageNow=1&pageSize=15&groupId=53


def get_contest_list(groupId):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache, no-store, must-revalidate',
        'content-type': 'application/json;charset=UTF-8',
        'origin': 'https://oj.qd.sdu.edu.cn',
        'referer': 'https://oj.qd.sdu.edu.cn/v2/group/' + str(groupId),
        'sec-ch-ua': '"Chromium";v="118", "Microsoft Edge";v="118", "Not=A?Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    # 需要登入
    data = requests.get('https://oj.qd.sdu.edu.cn/api/contest/list?pageNow=1&pageSize=1&groupId=' + groupId,
                        headers=headers, cookies=user_info).text
    data = json.loads(data)
    code = data['code']
    if code != 0:
        print(data['message'])
        return []

    totalNum = int(data['data']['totalNum'])
    print('find totalNum contest = %d' % (totalNum))

    data = requests.get(
        'https://oj.qd.sdu.edu.cn/api/contest/list?pageNow=1&pageSize=%s&groupId=%s' % (totalNum, groupId),
        headers=headers, cookies=user_info).text
    data = json.loads(data)
    code = data['code']
    if code != 0:
        print(data['message'])
        return []
    return data['data']['rows']


# https://oj.qd.sdu.edu.cn/api/contest/query?contestId=286

# https://oj.qd.sdu.edu.cn/api/contest/query?contestId=286
def get_cproblem_list_and_save(contestId):
    hander = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache, no-store, must-revalidate',
        'content-type': 'application/json;charset=UTF-8',
        'origin': 'https://oj.qd.sdu.edu.cn',
        'referer': 'https://oj.qd.sdu.edu.cn/v2/contest/' + str(contestId) + '/overview',
        'sec-ch-ua': '"Chromium";v="118", "Microsoft Edge";v="118", "Not=A?Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    # 需要登入
    data = requests.get('https://oj.qd.sdu.edu.cn/api/contest/query?contestId=' + str(contestId),
                        headers=hander, cookies=user_info).text
    data = json.loads(data)
    code = data['code']
    if code != 0:
        print(data['message'])
        return []

    for x in data['data']['problems']:
        print(x['problemCode'], x['problemTitle'], x['acceptNum'], x['submitNum'])
        db.insert_contest_problem(contestId, x['problemCode'], x['problemTitle'], x['acceptNum'], x['submitNum'])

    return data['data']['problems']


# https://oj.qd.sdu.edu.cn/api/contest/queryProblem?contestId=286&problemCode=1
# https://oj.qd.sdu.edu.cn/v2/contest/286/problem/1
def get_contest_problem_markdown(contestId, problemId):
    hander = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache, no-store, must-revalidate',
        'content-type': 'application/json;charset=UTF-8',
        'origin': 'https://oj.qd.sdu.edu.cn',
        'referer': 'https://oj.qd.sdu.edu.cn/v2/contest/' + str(contestId) + '/problem/' + str(problemId),
        'sec-ch-ua': '"Chromium";v="118", "Microsoft Edge";v="118", "Not=A?Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    # 需要登入
    data = requests.get(
        'https://oj.qd.sdu.edu.cn/api/contest/queryProblem?contestId=' + str(contestId) + '&problemCode=' + str(
            problemId),
        headers=hander, cookies=user_info).text
    data = json.loads(data)
    code = data['code']
    if code != 0:
        print(data['message'])
        return ''

    markdown = data['data']['problemDescriptionDTO']['markdownDescription']
    '''
    把 /n 等符号转义，并且写到/problem/xxx.markdown
    '''
    markdown = markdown.replace('\\n', '\n')
    markdown = markdown.replace('\\t', '\t')
    markdown = markdown.replace('\\r', '\r')

    # 写出文件
    path = os.path.join(os.getcwd(), 'problem')
    if not os.path.exists(path):
        os.mkdir(path)
    path = os.path.join(path, contestId)
    if not os.path.exists(path):
        os.mkdir(path)

    open(os.path.join(path, '[' + problemId + ']' + data['data']['problemTitle'] + '.md'), 'w', encoding='utf-8').write(
        markdown)

    return markdown


# https://oj.qd.sdu.edu.cn/api/contest/listSubmission?pageNow=1&pageSize=20&contestId=286


def get_contest_submit_list(contestId):
    header = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache, no-store, must-revalidate',
        'content-type': 'application/json;charset=UTF-8',
        'origin': 'https://oj.qd.sdu.edu.cn',
        'referer': 'https://oj.qd.sdu.edu.cn/v2/contest/' + str(contestId) + '/overview',
        'sec-ch-ua': '"Chromium";v="118", "Microsoft Edge";v="118", "Not=A?Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    # 需要登入
    data = requests.get(url_oj_submit_contest % (submit_max, contestId), headers=header, cookies=user_info).text
    data = json.loads(data)
    code = data['code']
    if code != 0:
        print(data['message'])
        return ''

    return data['data']['rows']


class push_accept_server:
    def __init__(self, contestId, loop_check_time=loop_flush_submit_time):
        self._contestId = contestId
        self._loop_check_time = loop_check_time
        # 启动 Loop 线程
        self._thread = threading.Thread(target=self._loop)
        self._thread.setDaemon(True)
        self._thread.start()

    def _loop(self):
        self._db = sdu3_db()
        while True:
            submits = get_contest_submit_list(self._contestId)
            for submit in submits:
                if self._db.have_contest_submit(submit['submissionId']):
                    break  # submit按照时间排序 一旦发现有重复的就退出
                self._db.insert_contest_submit(submit['submissionId'], self._contestId, submit['problemCode'],
                                               submit['userId'], submit['judgeResult'])
                '''
                你还搁着乐呢？
                    大佬：%s (id: %s)
                    已经把 题目 %s (id: %s) AC了
                '''

                if submit['judgeResult'] == 1:
                    pm('[SduOJ] ' + '题目ID:' + submit['problemTitle'] + '有人完成了AC',
                       '你还搁着乐呢？\n大佬：%s (id: %s)\n已经把 题目 %s (id: %s) AC了' % (
                           submit['username'], submit['userId'], submit['problemTitle'], submit['problemCode']))

            time.sleep(self._loop_check_time)
