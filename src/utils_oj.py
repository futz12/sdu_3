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

'''
{
    "code": 0,
    "message": "成功",
    "timestamp": "1697952695668",
    "data": {
        "rows": [
            {
                "problemId": "1000",
                "features": null,
                "isPublic": 1,
                "problemCode": "SDUOJ-1000",
                "problemTitle": "A+B Problem",
                "source": "",
                "remoteOj": null,
                "remoteUrl": null,
                "submitNum": 1352,
                "acceptNum": 732,
                "tagDTOList": []
            }
        ],
        "totalNum": "87",
        "totalPage": "87",
        "pageSize": "1",
        "pageIndex": "1"
    }
}
'''


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


# {"username":"202323092017","password":"12345678"}
# {'code': 0, 'message': 'successful', 'timestamp': '1698039586170', 'data': {'userId': '11633', 'username': '202323092017', 'nickname': '吴叶轩', 'email': '1391525377@qq.com', 'studentId': '202323092017', 'roles': ['user'], 'groups': ['53'], 'ipv4': '10.17.200.15', 'userAgent': 'python-requests/2.31.0'}}

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
'''
{
    "code": 0,
    "message": "successful",
    "timestamp": "1698063218684",
    "data": {
        "rows": [
            {
                "groupId": "53",
                "gmtCreate": "1697895166000",
                "openness": 1,
                "title": "2023兴趣开放实验室纳新专用",
                "memberNum": 12,
                "description": "嘻嘻",
                "userId": "268",
                "status": 2,
                "owner": {
                    "userId": "268",
                    "username": "misaka",
                    "nickname": "koi",
                    "email": "koi20000@163.com",
                    "status": null
                }
            }
        ],
        "totalNum": "1",
        "totalPage": "1",
        "pageSize": "2",
        "pageIndex": "1"
    }
}
'''


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


'''
{
    "code": 0,
    "message": "successful",
    "timestamp": "1698393156056",
    "data": {
        "groupId": "53",
        "gmtCreate": "1697895166000",
        "gmtModified": "1697895166000",
        "features": "",
        "openness": 1,
        "title": "2023兴趣开放实验室纳新专用",
        "memberNum": 12,
        "description": "嘻嘻",
        "markdown": "\n",
        "status": 2,
        "owner": {
            "userId": "268",
            "username": "misaka",
            "nickname": "koi",
            "email": "koi20000@163.com",
            "status": null
        },
        "members": [
            {
                "userId": "268",
                "username": "misaka",
                "nickname": "koi",
                "email": "koi20000@163.com",
                "status": null
            },
            {
                "userId": "5150",
                "username": "202000130139",
                "nickname": "任君驰",
                "email": "wiketool@gmail.com",
                "status": null
            },
            {
                "userId": "11529",
                "username": "202200300292",
                "nickname": "杨英龙",
                "email": "3117942880@qq.com",
                "status": null
            },
            {
                "userId": "11633",
                "username": "202323092017",
                "nickname": "吴叶轩",
                "email": "1391525377@qq.com",
                "status": null
            },
            {
                "userId": "11925",
                "username": "202300130002",
                "nickname": "彭麟翔",
                "email": "billpenn2005@outlook.com",
                "status": null
            },
            {
                "userId": "12046",
                "username": "202300130020",
                "nickname": "刘子昕",
                "email": "2538582956@qq.com",
                "status": null
            },
            {
                "userId": "12114",
                "username": "202300130150",
                "nickname": "王成意",
                "email": null,
                "status": null
            },
            {
                "userId": "12287",
                "username": "OL2023u001",
                "nickname": "吴叶轩",
                "email": "OL2023u001@sduoj.online",
                "status": null
            },
            {
                "userId": "12288",
                "username": "OL2023u002",
                "nickname": "彭麟翔",
                "email": "OL2023u002@sduoj.online",
                "status": null
            },
            {
                "userId": "12289",
                "username": "OL2023u003",
                "nickname": "杨英龙",
                "email": "OL2023u003@sduoj.online",
                "status": null
            },
            {
                "userId": "12290",
                "username": "OL2023u004",
                "nickname": "刘子昕",
                "email": "OL2023u004@sduoj.online",
                "status": null
            },
            {
                "userId": "12291",
                "username": "OL2023u005",
                "nickname": "王成意",
                "email": "OL2023u005@sduoj.online",
                "status": null
            }
        ]
    }
}
'''


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


''''
{
    "code": 0,
    "message": "successful",
    "timestamp": "1698064210326",
    "data": {
        "rows": [
            {
                "contestId": "286",
                "gmtCreate": "1697895538000",
                "gmtModified": "1698042286000",
                "features": {
                    "mode": "ioi",
                    "openness": "private",
                    "frozenTime": 0,
                    "contestRunning": {
                        "displayPeerSubmission": 1,
                        "displayRank": 1,
                        "displayJudgeScore": 1,
                        "displayCheckpointResult": 1,
                        "allowToSubmit": 1
                    },
                    "contestEnd": {
                        "displayPeerSubmission": 1,
                        "displayRank": 1,
                        "displayJudgeScore": 1,
                        "displayCheckpointResult": 1,
                        "allowToSubmit": 1
                    }
                },
                "isPublic": 1,
                "contestTitle": "2023兴趣开放实验室纳新-测试一",
                "userId": "268",
                "groupId": null,
                "gmtStart": "1697895600000",
                "gmtEnd": "1700573700000",
                "source": "",
                "participantNum": 5,
                "username": "misaka",
                "managerGroupDTO": null
            }
        ],
        "totalNum": "1",
        "totalPage": "1",
        "pageSize": "15",
        "pageIndex": "1"
    }
}
'''


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

'''
{
    "code": 0,
    "message": "successful",
    "timestamp": "1698064766869",
    "data": {
        "contestId": "286",
        "gmtCreate": "1697895538000",
        "gmtModified": "1698042286000",
        "features": {
            "mode": "ioi",
            "openness": "private",
            "frozenTime": 0,
            "contestRunning": {
                "displayPeerSubmission": 1,
                "displayRank": 1,
                "displayJudgeScore": 1,
                "displayCheckpointResult": 1,
                "allowToSubmit": 1
            },
            "contestEnd": {
                "displayPeerSubmission": 1,
                "displayRank": 1,
                "displayJudgeScore": 1,
                "displayCheckpointResult": 1,
                "allowToSubmit": 1
            }
        },
        "isPublic": 1,
        "contestTitle": "2023兴趣开放实验室纳新-测试一",
        "gmtStart": "1697895600000",
        "gmtEnd": "1700573700000",
        "source": "",
        "participantNum": 5,
        "markdownDescription": "\n",
        "problems": [
            {
                "problemCode": "1",
                "problemTitle": "A+B for Input-Output Practice 1",
                "problemWeight": 1,
                "problemColor": "",
                "acceptNum": 1,
                "submitNum": 1,
                "judgeResult": null,
                "judgeScore": null
            },
            {
                "problemCode": "2",
                "problemTitle": "A+B for Input-Output Practice 2",
                "problemWeight": 1,
                "problemColor": "",
                "acceptNum": 0,
                "submitNum": 0,
                "judgeResult": null,
                "judgeScore": null
            },
            {
                "problemCode": "3",
                "problemTitle": "A+B for Input-Output Practice 3",
                "problemWeight": 1,
                "problemColor": "",
                "acceptNum": 0,
                "submitNum": 0,
                "judgeResult": null,
                "judgeScore": null
            },
            {
                "problemCode": "4",
                "problemTitle": "A+B for Input-Output Practice 4",
                "problemWeight": 1,
                "problemColor": "",
                "acceptNum": 0,
                "submitNum": 0,
                "judgeResult": null,
                "judgeScore": null
            },
            {
                "problemCode": "5",
                "problemTitle": "A+B for Input-Output Practice 5",
                "problemWeight": 1,
                "problemColor": "",
                "acceptNum": 0,
                "submitNum": 0,
                "judgeResult": null,
                "judgeScore": null
            },
            {
                "problemCode": "6",
                "problemTitle": "A+B for Input-Output Practice 6",
                "problemWeight": 1,
                "problemColor": "",
                "acceptNum": 0,
                "submitNum": 0,
                "judgeResult": null,
                "judgeScore": null
            }
        ],
        "participants": [
            "misaka",
            "OL2023u001",
            "202300130150",
            "202323092017",
            "202300130002"
        ],
        "username": "misaka"
    }
}
'''


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


'''
{
    "code": 0,
    "message": "successful",
    "timestamp": "1698071432733",
    "data": {
        "problemCode": "1",
        "problemWeight": 1,
        "problemTitle": "A+B for Input-Output Practice 1",
        "memoryLimit": 262144,
        "timeLimit": 1000,
        "functionTemplates": [
            {
                "judgeTemplateId": "6",
                "isShowFunctionTemplate": 1,
                "functionTemplate": "#include <iostream>\nusing namespace std;\nvoid input(int &x, int &y);\nvoid output(int x, int y);\nint main() {\n    int n, x, y;\n    cin >> n;\n    while(n--) {\n        input(x, y);\n        output(x, y);\n    }\n}\n// 你的 solution 会被放置在这",
                "initialTemplate": "void input(int &x, int &y) {\n    // TODO: 请填写代码\n}\nvoid output(int x, int y) {\n    // TODO: 请填写代码\n}"
            },
            {
                "judgeTemplateId": "13",
                "isShowFunctionTemplate": 1,
                "functionTemplate": null,
                "initialTemplate": null
            },
            {
                "judgeTemplateId": "14",
                "isShowFunctionTemplate": 1,
                "functionTemplate": "import java.util.Scanner;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner scan = new Scanner(System.in);\n        int n = scan.nextInt();\n        while(n-- > 0) {\n            Solver.inputAndOutput(scan);\n        }\n    }\n}\n// 你的 solution 会被放置在这",
                "initialTemplate": "class Solver {\n    public static void inputAndOutput(Scanner scan) {\n        // TODO: 请填写代码\n    }\n}"
            },
            {
                "judgeTemplateId": "19",
                "isShowFunctionTemplate": 1,
                "functionTemplate": "#include <stdio.h>\nvoid input(int *x, int *y);\nvoid output(int x, int y);\nint main() {\n    int n, x, y;\n    scanf(\"%d\", &n);\n    while(n--) {\n        input(&x, &y);\n        output(x, y);\n    }\n}\n// 你的 solution 会被放置在这",
                "initialTemplate": "void input(int *x, int *y) {\n    // TODO: 请填写代码\n}\nvoid output(int x, int y) {\n    // TODO: 请填写代码\n}"
            }
        ],
        "judgeTemplates": [
            {
                "id": "6",
                "type": 0,
                "title": "C++14",
                "comment": "",
                "acceptFileExtensions": [
                    "cc",
                    "cpp"
                ]
            },
            {
                "id": "13",
                "type": 0,
                "title": "Python3.6",
                "comment": "",
                "acceptFileExtensions": [
                    "py"
                ]
            },
            {
                "id": "14",
                "type": 0,
                "title": "Java8",
                "comment": "",
                "acceptFileExtensions": [
                    "java"
                ]
            },
            {
                "id": "19",
                "type": 0,
                "title": "C11",
                "comment": "",
                "acceptFileExtensions": [
                    "c"
                ]
            }
        ],
        "problemDescriptionDTO": {
            "markdownDescription": "## Description\n计算a+b\n\n## Input\n\n输入第一行是一个整数 N，代表接下来 N 行会有 N 组样例输入。\n\n## Output\n每组输出占一行。\n\n## Sample Input\n```\n2\n1 5\n10 20\n```\n## Sample Output\n```\n6\n30\n```",
            "htmlDescription": null,
            "htmlInput": null,
            "htmlOutput": null,
            "htmlSampleInput": null,
            "htmlSampleOutout": null,
            "htmlHint": null
        },
        "problemCaseDTOList": []
    }
}
'''


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

'''
[{'submissionId': '7001f4231c056ce', 'gmtCreate': '1698075278539', 'gmtModified': '1698075278837', 'version': 1, 'isPublic': 0, 'valid': 1, 'userId': '11633', 'judgeTemplateId': '6', 'judgeResult': 4, 'judgeScore': 0, 'usedTime': 1, 'usedMemory': 3408, 'codeLength': 50, 'checkpointNum': 10, 'publicCheckpointNum': 0, 'problemCode': '5', 'problemTitle': 'A+B for Input-Output Practice 5', 'judgeTemplateTitle': 'C++14', 'username': '202323092017'}
, {'submissionId': '7001f1efa0056c9', 'gmtCreate': '1698075242476', 'gmtModified': '1698075242680', 'version': 1, 'isPublic': 0, 'valid': 1, 'userId': '11633', 'judgeTemplateId': '6', 'judgeResult': 8, 'judgeScore': 0, 'usedTime': 0, 'usedMemory': 0, 'codeLength': 111, 'checkpointNum': 10, 'publicCheckpointNum': 0, 'problemCode': '1', 'problemTitle': 'A+B for Input-Output Practice 1', 'judgeTemplateTitle': 'C++14', 'username': '202323092017'}, {'submissionId': '7001c84018056b2', 'gmtCreate': '1698074559496', 'gmtModified': '1698074559539', 'version': 1, 'isPublic': 0, 'valid': 1, 'userId': '11633', 'judgeTemplateId': '6', 'judgeResult': 8, 'judgeScore': 0, 'usedTime': 0, 'usedMemory': 0, 'codeLength': 8, 'checkpointNum': 10, 'publicCheckpointNum': 0, 'problemCode': '5', 'problemTitle': 'A+B for Input-Output Practice 5', 'judgeTemplateTitle': 'C++14', 'username': '202323092017'}, {'submissionId': '7001c5f4c0056af', 'gmtCreate': '1698074521905', 'gmtModified': '1698074522284', 'version': 1, 'isPublic': 0, 'valid': 1, 'userId': '11633', 'judgeTemplateId': '6', 'judgeResult': 1, 'judgeScore': 100, 'usedTime': 2, 'usedMemory': 3468, 'codeLength': 354, 'checkpointNum': 10, 'publicCheckpointNum': 0, 'problemCode': '6', 'problemTitle': 'A+B for Input-Output Practice 6', 'judgeTemplateTitle': 'C++14', 'username': '202323092017'}, {'submissionId': '7001c4696c056ad', 'gmtCreate': '1698074496607', 'gmtModified': '1698074516900', 'version': 1, 'isPublic': 0, 'valid': 1, 'userId': '11633', 'judgeTemplateId': '6', 'judgeResult': 2, 'judgeScore': 0, 'usedTime': 1999, 'usedMemory': 3308, 'codeLength': 378, 'checkpointNum': 10, 'publicCheckpointNum': 0, 'problemCode': '6', 'problemTitle': 'A+B for Input-Output Practice 6', 'judgeTemplateTitle': 'C++14', 'username': '202323092017'}, {'submissionId': '7001c260b4056ab', 'gmtCreate': '1698074463279', 'gmtModified': '1698074463646', 'version': 1, 'isPublic': 0, 'valid': 1, 'userId': '11633', 'judgeTemplateId': '6', 'judgeResult': 1, 'judgeScore': 100, 'usedTime': 1, 'usedMemory': 3468, 'codeLength': 378, 'checkpointNum': 10, 'publicCheckpointNum': 0, 'problemCode': '4', 'problemTitle': 'A+B for Input-Output Practice 4', 'judgeTemplateTitle': 'C++14', 'username': '202323092017'}, {'submissionId': '7001c17180056aa', 'gmtCreate': '1698074447969', 'gmtModified': '1698074468264', 'version': 1, 'isPublic': 0, 'valid': 1, 'userId': '11633', 'judgeTemplateId': '6', 'judgeResult': 2, 'judgeScore': 0, 'usedTime': 1999, 'usedMemory': 3312, 'codeLength': 331, 'checkpointNum': 10, 'publicCheckpointNum': 0, 'problemCode': '4', 'problemTitle': 'A+B for Input-Output Practice 4', 'judgeTemplateTitle': 'C++14', 'username': '202323092017'}, {'submissionId': '7001c01854056a8', 'gmtCreate': '1698074425881', 'gmtModified': '1698074446171', 'version': 1, 'isPublic': 0, 'valid': 1, 'userId': '11633', 'judgeTemplateId': '6', 'judgeResult': 2, 'judgeScore': 0, 'usedTime': 1999, 'usedMemory': 3296, 'codeLength': 351, 'checkpointNum': 10, 'publicCheckpointNum': 0, 'problemCode': '4', 'problemTitle': 'A+B for Input-Output Practice 4', 'judgeTemplateTitle': 'C++14', 'username': '202323092017'}, {'submissionId': '7001bedaa8056a6', 'gmtCreate': '1698074405547', 'gmtModified': '1698074405921', 'version': 1, 'isPublic': 0, 'valid': 1, 'userId': '11633', 'judgeTemplateId': '6', 'judgeResult': 6, 'judgeScore': 70, 'usedTime': 1, 'usedMemory': 3424, 'codeLength': 372, 'checkpointNum': 10, 'publicCheckpointNum': 0, 'problemCode': '4', 'problemTitle': 'A+B for Input-Output Practice 4', 'judgeTemplateTitle': 'C++14', 'username': '202323092017'}, {'submissionId': '7001bc5eac056a3', 'gmtCreate': '1698074364847', 'gmtModified': '1698074385143', 'version': 1, 'isPublic': 0, 'valid': 1, 'userId': '11633', 'judgeTemplateId': '6', 'judgeResult': 2, 'judgeScore': 0, 'usedTime': 1999, 'usedMemory': 3312, 'codeLength': 325, 'checkpointNum': 10, 'publicCheckpointNum': 0, 'problemCode': '4', 'problemTitle': 'A+B for Input-Output Practice 4', 'judgeTemplateTitle': 'C++14', 'username': '202323092017'}, {'submissionId': '7001b734ac056a0', 'gmtCreate': '1698074280239', 'gmtModified': '1698074280660', 'version': 1, 'isPublic': 0, 'valid': 1, 'userId': '11633', 'judgeTemplateId': '6', 'judgeResult': 1, 'judgeScore': 100, 'usedTime': 3, 'usedMemory': 3468, 'codeLength': 211, 'checkpointNum': 10, 'publicCheckpointNum': 0, 'problemCode': '3', 'problemTitle': 'A+B for Input-Output Practice 3', 'judgeTemplateTitle': 'C++14', 'username': '202323092017'}, {'submissionId': '7001b54dc80569e', 'gmtCreate': '1698074249079', 'gmtModified': '1698074249470', 'version': 1, 'isPublic': 0, 'valid': 1, 'userId': '11633', 'judgeTemplateId': '6', 'judgeResult': 1, 'judgeScore': 100, 'usedTime': 3, 'usedMemory': 3488, 'codeLength': 224, 'checkpointNum': 10, 'publicCheckpointNum': 0, 'problemCode': '2', 'problemTitle': 'A+B for Input-Output Practice 2', 'judgeTemplateTitle': 'C++14', 'username': '202323092017'}, {'submissionId': '7001abef740569a', 'gmtCreate': '1698074095582', 'gmtModified': '1698074095965', 'version': 1, 'isPublic': 0, 'valid': 1, 'userId': '11633', 'judgeTemplateId': '6', 'judgeResult': 1, 'judgeScore': 100, 'usedTime': 2, 'usedMemory': 3484, 'codeLength': 96, 'checkpointNum': 10, 'publicCheckpointNum': 0, 'problemCode': '1', 'problemTitle': 'A+B for Input-Output Practice 1', 'judgeTemplateTitle': 'C++14', 'username': '202323092017'}, {'submissionId': '7001aa47f005698', 'gmtCreate': '1698074068479', 'gmtModified': '1698074068672', 'version': 1, 'isPublic': 0, 'valid': 1, 'userId': '11633', 'judgeTemplateId': '6', 'judgeResult': 8, 'judgeScore': 0, 'usedTime': 0, 'usedMemory': 0, 'codeLength': 95, 'checkpointNum': 10, 'publicCheckpointNum': 0, 'problemCode': '1', 'problemTitle': 'A+B for Input-Output Practice 1', 'judgeTemplateTitle': 'C++14', 'username': '202323092017'}, {'submissionId': '6fe809a6c0065a0', 'gmtCreate': '1697966579124', 'gmtModified': '1697966579338', 'version': 1, 'isPublic': 0, 'valid': 1, 'userId': '268', 'judgeTemplateId': '19', 'judgeResult': 1, 'judgeScore': 100, 'usedTime': 0, 'usedMemory': 1716, 'codeLength': 160, 'checkpointNum': 10, 'publicCheckpointNum': 0, 'problemCode': '1', 'problemTitle': 'A+B for Input-Output Practice 1', 'judgeTemplateTitle': 'C11', 'username': 'misaka'}]
'''


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