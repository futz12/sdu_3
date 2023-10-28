import src.utils_oj as oj
from src.varlist import db
from src.varlist import debug
import src.utils_edge as e

import time

# 程序入口
if __name__ == '__main__':

    db.clear_submit()  # 清空提交记录
    db.clear_problem()  # 清空题目记录
    db.clear_message()  # 清空通知记录,也可以不清除，可以接到上次爬取

    print('start 开始爬取 OJ ')

    list_problem = oj.get_list_problem()
    list_submit = oj.get_list_submit()

    for problem in list_problem:
        db.insert_problem(problem['problemId'], problem['problemTitle'], problem['acceptNum'], problem['submitNum'])

    for submit in list_submit:
        db.insert_submit(submit['submissionId'], submit['problemId'], submit['userId'], submit['judgeResult'])

    db.show_top10()  # 显示前十名
    db.show_judgeResult()  # 显示提交结果分析

    #    mail.push_message('test', 'Hello World')

    e.message_server()  # 启动自动爬取通知服务

    db.clear_contest_problem()  # 清空比赛题目记录，也可以不清除，可以接到上次爬取
    # db.clear_contest_submit()

    oj.login_and_get_cookies('xxxx', 'password')  # 登录并获取cookies，注意这个要自己改改
    group = oj.get_group_list()

    for i in range(0, len(group)):
        print(group[i]['title'])
        contests = oj.get_contest_list(group[i]['groupId'])

        for j in range(0, len(contests)):
            problems = oj.get_cproblem_list_and_save(contests[j]['contestId'])
            for k in range(0, len(problems)):
                oj.get_contest_problem_markdown(contests[j]['contestId'], problems[k]['problemCode'])
                print(problems[k]['problemTitle'] + ' state: ',
                      'Accept' if problems[k]['judgeResult'] == 1 else 'Not Accept')

            submits_list = oj.get_contest_submit_list(contests[j]['contestId'])
            for x in submits_list:
                # print(x)
                if db.have_contest_submit(x['submissionId']):
                    break  # submit是按世界排序的，所以一旦出现重复就可以停止了
                db.insert_contest_submit(x['submissionId'], contests[j]['contestId'], x['problemCode'], x['userId'],
                                         x['judgeResult'])

            oj.push_accept_server(contests[j]['contestId'])  # 启动推送服务

        members = oj.get_group_member_list(group[i]['groupId'])
        db.analysis_group(contests, members)  # 按比赛制作提交前五和ac前五的统计图

    # 按比赛制作提交前五和ac前五的统计图

    print('done')
    # 避免程序结束
    while True:
        time.sleep(10000)
