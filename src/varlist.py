# 全局变量表
from src.utils_db import sdu3_db
from src.utils_mail import push_message

debug = True
db = sdu3_db()

loop_message_time = 10 * 60  # 默认 10分钟 为一个 message 爬取周期
loop_flush_submit_time = 30 # 默认 30秒 为一个 submit 刷新周期
