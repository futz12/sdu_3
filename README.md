# sdu_3 代码说明

### 环境要求

- python3.9
- Pillow 9.X
- requirements.txt 内容

### 注意事项

- OJ账号请在 login 函数中修改替换否则 error
- 推送需要配置邮箱信息，请在 utils_mail.py 中修改
- 没有写网络异常检测，请确保网络通畅
- 消息通知默认爬取一页，把debug改为False可以爬取所有消息
- 请保证电脑存在edge（chromium）

### 代码说明

- 网页的附件将自动下载到 /file
- 网页截图将保存在 /pdf
- 软件配置文件为 varlist.py
- 下载的题目在 /problem
- AC 分析情况在终端显示
- 其他数据将使用mathplotlib绘制图表展示，请注意确认
- 代码没有经过严格测试，可能存在bug，如果有问题请联系我
- 不严格的说本程序实现了全部要求，部分可能由于作者比较懒，没有认真实现QAQ
- 邮箱的提醒周期是 30s，可以在 varlist.py 中修改
- 消息爬取的周期是 10min，可以在 varlist.py 中修改