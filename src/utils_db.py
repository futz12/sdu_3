submit_max = 2000

import sqlite3

import matplotlib.pyplot as plt
from pylab import mpl

# 解决中文字体问题
mpl.rcParams["font.sans-serif"] = ["SimHei"]

'''
data_base/sdu3_base

{
    CREATE TABLE problem (
    problemId    TEXT    PRIMARY KEY
                         UNIQUE,
    problemTitle TEXT,
    acceptNum    INTEGER,
    submitNum    INTEGER
    );

    CREATE TABLE submit (
    submissionId TEXT UNIQUE
                      NOT NULL,
    problemId    TEXT NOT NULL
                      PRIMARY KEY,
    userId       TEXT NOT NULL,
    judgeResult  BLOB NOT NULL
    );
    CREATE TABLE message (
    url TEXT    PRIMARY KEY
                NOT NULL,
    title TEXT NOT NULL,
    postTime TEXT NOT NULL,
    recvTime TEXT NOT NULL
    );
}
'''

'''
{
    SELECT problemId, COUNT(*) as submissionCount  
    FROM submit  
    GROUP BY problemId  
    ORDER BY submissionCount DESC  
    LIMIT 10;
}
'''


class sdu3_db():
    def __init__(self):

        # 如果数据库文件夹不存在就创建
        import os
        if not os.path.exists('data_base'):
            os.makedirs('data_base')

        # 打开数据库连接
        self._conn = sqlite3.connect('data_base/sdu3_base.db')

        # 创建游标对象
        cursor = self._conn.cursor()

        # 检查表是否存在
        cursor.execute("PRAGMA table_info(problem)")
        if cursor.fetchone() is not None:
            print("Table exists.")
        else:
            print("Table does not exist.")
            cursor = self._conn.cursor()
            cursor.execute('''  
                CREATE TABLE problem (  
                    problemId TEXT PRIMARY KEY UNIQUE,  
                    problemTitle TEXT,  
                    acceptNum INTEGER,  
                    submitNum INTEGER  
                )  
            ''')

        cursor.execute("PRAGMA table_info(submit)")
        if cursor.fetchone() is not None:
            print("Table exists.")
        else:
            print("Table does not exist.")
            cursor = self._conn.cursor()
            cursor.execute('''  
                CREATE TABLE submit (
                    submissionId TEXT UNIQUE
                                NOT NULL,
                    problemId    TEXT NOT NULL,
                    userId       TEXT NOT NULL,
                    judgeResult        BLOB NOT NULL
                )
            ''')

        cursor.execute("PRAGMA table_info(message)")
        if cursor.fetchone() is not None:
            print("Table exists.")
        else:
            print("Table does not exist.")
            cursor = self._conn.cursor()
            cursor.execute('''  
                CREATE TABLE message (
                    url TEXT    PRIMARY KEY
                                NOT NULL,
                    title TEXT NOT NULL,
                    postTime TEXT NOT NULL,
                    recvTime TEXT NOT NULL,
                    data TEXT
                )
            ''')

        # contest_problem
        cursor.execute("PRAGMA table_info(contest_problem)")
        if cursor.fetchone() is not None:
            print("Table exists.")
        else:
            print("Table does not exist.")
            cursor = self._conn.cursor()
            cursor.execute('''  
                CREATE TABLE contest_problem (
                    contestId TEXT NOT NULL,
                    problemId TEXT NOT NULL,
                    problemTitle TEXT NOT NULL,
                    acceptNum INTEGER,
                    submitNum INTEGER,
                    PRIMARY KEY(contestId, problemId)
                )
            ''')

        # contest_submit
        cursor.execute("PRAGMA table_info(contest_submit)")
        if cursor.fetchone() is not None:
            print("Table exists.")
        else:
            print("Table does not exist.")
            cursor = self._conn.cursor()
            cursor.execute('''
                CREATE TABLE contest_submit (
                    submissionId TEXT UNIQUE
                                NOT NULL,
                    contestId    TEXT NOT NULL,
                    problemId    TEXT NOT NULL,
                    userId       TEXT NOT NULL,
                    judgeResult        BLOB NOT NULL
                )
            ''')

        self._conn.commit()

    def __del__(self):
        self._conn.close()

    def insert_message(self, url, title, postTime, recvTime, data):
        cursor = self._conn.cursor()

        cursor.execute('''
                    INSERT INTO message (url, title, postTime, recvTime, data)
                    VALUES (?, ?, ?, ? ,? )
                ''', (url, title, postTime, recvTime, data))

        self._conn.commit()

    def query_message(self, url):
        cursor = self._conn.cursor()

        cursor.execute("SELECT * FROM message WHERE url = '%s'" % (url))

        return cursor.fetchone()

    def clear_message(self):
        cursor = self._conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS message")
        cursor.execute('''  
                        CREATE TABLE message (  
                            url TEXT PRIMARY KEY UNIQUE,  
                            title TEXT NOT NULL ,  
                            postTime TEXT NOT NULL ,  
                            recvTime TEXT NOT NULL ,
                            data TEXT
                        )  
                    ''')

        self._conn.commit()

    def have_message(self, url):
        cursor = self._conn.cursor()

        cursor.execute("SELECT * FROM message WHERE url = '%s'" % (url))

        if cursor.fetchone() is not None:
            return True
        else:
            return False

    def insert_problem(self, problemId, problemTitle, acceptNum, submitNum):
        cursor = self._conn.cursor()

        cursor.execute('''  
                    INSERT INTO problem (problemId, problemTitle, acceptNum, submitNum)  
                    VALUES (?, ?, ?, ?)  
                ''', (problemId, problemTitle, acceptNum, submitNum))

        self._conn.commit()

    def query_problem(self, problemId):
        cursor = self._conn.cursor()

        cursor.execute("SELECT * FROM problem WHERE problemId = '%s'" % (problemId))

        return cursor.fetchone()

    def clear_problem(self):
        cursor = self._conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS problem")
        cursor.execute('''  
                        CREATE TABLE problem (  
                            problemId TEXT PRIMARY KEY UNIQUE,  
                            problemTitle TEXT,  
                            acceptNum INTEGER,  
                            submitNum INTEGER  
                        )  
                    ''')

        self._conn.commit()

    def insert_submit(self, submissionId, problemId, userId, judgeResult):
        cursor = self._conn.cursor()

        cursor.execute('''
                    INSERT INTO submit (submissionId, problemId, userId, judgeResult)
                    VALUES (?, ?, ?, ?)
                ''', (submissionId, problemId, userId, judgeResult))

        self._conn.commit()

    def query_submit(self, problemId):
        cursor = self._conn.cursor()

        cursor.execute("SELECT * FROM submit WHERE problemId = '%s'" % (problemId))

        return cursor.fetchone()

    def clear_submit(self):
        cursor = self._conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS submit")
        cursor.execute('''
                            CREATE TABLE submit (
                                submissionId TEXT UNIQUE
                                            NOT NULL,
                                problemId    TEXT NOT NULL,
                                userId       TEXT NOT NULL,
                                judgeResult        BLOB NOT NULL
                            )
                        ''')

        self._conn.commit()

    def rank_submit_form_submit_top10(self):
        cursor = self._conn.cursor()

        # 先找到problem的编号再说
        cursor.execute('''
                    SELECT problemId, COUNT(*) as submissionCount FROM submit
                    GROUP BY problemId 
                    ORDER BY submissionCount DESC 
                    LIMIT 10
                   ''')
        # 在problem表找到对应的题目信息

        list_problemId_top10 = cursor.fetchall()

        list_problem_top10 = []

        for problem in list_problemId_top10:
            cursor.execute("SELECT * FROM problem WHERE problemId = '%s'" % (problem[0]))
            tmp = cursor.fetchone()

            # 顺便再把提交次数也get出来吧
            cursor.execute("SELECT COUNT(*) FROM submit WHERE problemId = '%s'" % (problem[0]))
            tmp = tmp + cursor.fetchone()

            list_problem_top10.append(tmp)

        return list_problem_top10

    def rank_accept_from_submit_top10(self):
        cursor = self._conn.cursor()

        # 先找到problem的编号再说
        cursor.execute('''
                    SELECT problemId, COUNT(*) as submissionCount FROM submit
                    WHERE judgeResult = 1 
                    GROUP BY problemId 
                    ORDER BY submissionCount DESC 
                    LIMIT 10
                   ''')
        # 在problem表找到对应的题目信息

        list_problemId_top10 = cursor.fetchall()

        list_problem_top10 = []

        for problem in list_problemId_top10:
            cursor.execute("SELECT * FROM problem WHERE problemId = '%s'" % (problem[0]))
            tmp = cursor.fetchone()

            # 顺便再把通过次数也get出来吧
            cursor.execute("SELECT COUNT(*) FROM submit WHERE problemId = '%s' AND judgeResult = 1" % (problem[0]))
            tmp = tmp + cursor.fetchone()

            list_problem_top10.append(tmp)

        return list_problem_top10

    def show_judgeResult(self):
        cursor = self._conn.cursor()

        # 统计AC的数量
        cursor.execute('''
                    SELECT COUNT(judgeResult) AS cnt
                    FROM submit
                    WHERE judgeResult = 1  
                     ''')
        ac_count = cursor.fetchone()

        # 圆饼图显示AC率
        plt.figure()
        plt.title('AC率')
        labels = 'AC', 'Other'
        sizes = [ac_count[0], submit_max - ac_count[0]]
        explode = (0, 0.1)
        plt.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
        plt.axis('equal')  # 保证是圆形
        plt.show()

    def show_top10(self):
        # matplotlib绘制表格
        col = ['problemId', 'problemTitle', 'tot_acceptNum', 'tot_submitNum', 'submit_in_2000']
        row = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        plt.figure(figsize=(18, 6))  # 设置画布大小
        plt.title('提交前十情况表')

        tbl = plt.table(self.rank_submit_form_submit_top10(), colLabels=col, rowLabels=row, loc='center')
        tbl.scale(1, 2)  # 列宽行高
        plt.axis('off')  # 不显示坐标轴
        plt.show()

        col = ['problemId', 'problemTitle', 'tot_acceptNum', 'tot_submitNum', 'accept_in_2000']
        row = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        plt.figure(figsize=(18, 6))  # 设置画布大小
        plt.title('通过前十情况表')

        tbl = plt.table(self.rank_accept_from_submit_top10(), colLabels=col, rowLabels=row, loc='center')
        tbl.scale(1, 2)  # 列宽行高
        plt.axis('off')  # 不显示坐标轴
        plt.show()

        # 绘制柱状图
        plt.figure()
        plt.title('提交前十情况表')
        plt.xlabel('problemId')
        plt.ylabel('submitNum')
        plt.bar([x[0] for x in self.rank_submit_form_submit_top10()],
                [x[4] for x in self.rank_submit_form_submit_top10()], width=0.5)

        plt.show()

    def clear_contest_problem(self):
        cursor = self._conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS contest_problem")
        cursor.execute('''  
                        CREATE TABLE contest_problem (  
                            contestId TEXT NOT NULL,
                            problemId TEXT NOT NULL,
                            problemTitle TEXT NOT NULL,
                            acceptNum INTEGER,
                            submitNum INTEGER,
                            PRIMARY KEY(contestId, problemId)
                        )  
                    ''')

        self._conn.commit()

    def insert_contest_problem(self, contestId, problemId, problemTitle, acceptNum, submitNum):
        cursor = self._conn.cursor()

        cursor.execute('''
                    INSERT INTO contest_problem (contestId, problemId, problemTitle,acceptNum,submitNum)
                    VALUES (?, ?, ?,?, ?)
                ''', (contestId, problemId, problemTitle, acceptNum, submitNum))

        self._conn.commit()

    def clear_contest_submit(self):
        cursor = self._conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS contest_submit")
        cursor.execute('''
                        CREATE TABLE contest_submit (
                            submissionId TEXT UNIQUE
                                        NOT NULL,
                            contestId    TEXT NOT NULL,
                            problemId    TEXT NOT NULL,
                            userId       TEXT NOT NULL,
                            judgeResult        BLOB NOT NULL
                        )
                    ''')

        self._conn.commit()

    def insert_contest_submit(self, submissionId, contestId, problemId, userId, judgeResult):
        cursor = self._conn.cursor()

        cursor.execute('''
                    INSERT INTO contest_submit (submissionId, contestId, problemId, userId, judgeResult)
                    VALUES (?, ?, ?, ?, ?)
                ''', (submissionId, contestId, problemId, userId, judgeResult))

        self._conn.commit()

    def have_contest_submit(self, submissionId):
        cursor = self._conn.cursor()

        cursor.execute("SELECT * FROM contest_submit WHERE submissionId = '%s'" % (submissionId))

        if cursor.fetchone() is not None:
            return True
        else:
            return False

    def get_contest_submit_count(self, contestId, userId):
        cursor = self._conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM contest_submit WHERE contestId = '%s' AND userId = '%s'" % (
            contestId, userId))

        return cursor.fetchone()[0]

    def get_contest_submit_accept(self, contestId, userId):
        cursor = self._conn.cursor()

        # 一道题通过多次也只算一次
        cursor.execute(
            "SELECT COUNT(DISTINCT problemId) FROM contest_submit WHERE contestId = '%s' AND userId = '%s' AND judgeResult = 1" % (
                contestId, userId))

        return cursor.fetchone()[0]

    def get_contest_submit_top5(self, contestId):
        cursor = self._conn.cursor()

        cursor.execute('''
                    SELECT userId, COUNT(*) as submissionCount FROM contest_submit
                    WHERE contestId = '%s'
                    GROUP BY userId 
                    ORDER BY submissionCount DESC 
                    LIMIT 5
                   ''' % (contestId))

        return cursor.fetchall()

    def get_contest_submit_accept_top5(self, contestId):
        cursor = self._conn.cursor()

        cursor.execute('''
                    SELECT userId, COUNT(*) as submissionCount FROM contest_submit
                    WHERE contestId = '%s' AND judgeResult = 1
                    GROUP BY userId 
                    ORDER BY submissionCount DESC 
                    LIMIT 5
                   ''' % (contestId))

        return cursor.fetchall()

    def analysis_group(self, contests, members):
        for member in members:
            print('正在分析用户：', member['email'], member['nickname'])
            for _c in contests:
                print('正在分析比赛：', _c['contestTitle'])
                print('用户提交次数：', self.get_contest_submit_count(_c['contestId'], member['userId']))
                print('用户通过题数：', self.get_contest_submit_accept(_c['contestId'], member['userId']))

        for contest in contests:
            top5_submit = self.get_contest_submit_top5(contest['contestId'])
            top5_submit_accept = self.get_contest_submit_accept_top5(contest['contestId'])
            # 绘制统计图
            plt.figure()
            plt.title(contest['contestTitle'] + ' 前五情况表')
            plt.xlabel('userId')
            plt.ylabel('submitNum & acceptNum')

            plt.bar([x[0] for x in top5_submit],
                    [x[1] for x in top5_submit], width=0.5, label='提交次数')
            plt.bar([x[0] for x in top5_submit_accept],
                    [x[1] for x in top5_submit_accept], width=0.5, label='通过题目数')

            plt.legend()
            plt.show()
