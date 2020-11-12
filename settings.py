# -*- encoding: utf-8 -*-
'''
@File    :   settings.py    
@Contact :   yizhong120110@gmail.com
@Descrip :

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2020/10/20 17:49   qiuy      1.0         None
'''

import os,logging,time
from urllib.parse import quote
userhome = os.environ.get("HOME","")
class BaseConfig(object):
    # mysql数据库连接串 用户名:密码@host:port
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://paper:paper@127.0.0.1:3306/flask_cata?charset=utf8mb4"
    SQLALCHEMY_POOL_SIZE = 2
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_POOL_RECYCLE = -1
    # mongodb数据库连接串
    MONGO_URL = "mongodb://192.168.10.205:5625/"
    # 数据库名
    DB = "paper"
    # 集合名
    COL = "brief"
    # 追踪对象的修改并且发送信号
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOGDIR = os.path.join(os.path.dirname(__file__), "logs")
    DEBUG = True
    LOGLEVEL = logging.DEBUG

class DevelopmentConfig(BaseConfig):
    USER_AGENTS =[
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
        "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11",
        "Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
    ]
    # 请求时间间隔
    INTERVAL = 3
    SEARCH_HANDLE = {
        "action": "",
        "NaviCode": "*",
        "ua": "1.21",
        "isinEn": "0",
        "PageName": "ASP.brief_result_aspx",
        "DbPrefix": "CDMD",
        "DbCatalog": quote("中国优秀博硕士学位论文全文数据库"),
        "ConfigFile": "CDMD.xml",
        "db_opt": "CDMD",
        "db_value": quote("中国博士学位论文全文数据库,中国优秀硕士学位论文全文数据库"),
        "CKB_extension": "ZYW",
        "his": "0",
        "__": quote(time.asctime(time.localtime()) + " GMT+0800 (中国标准时间)")
    }
    YEAR = ["2020", "2019", "2018", "2017", "2016", "2015", "2014", "2013", "2012", "2011", "2010"]

    SUBJECT = ["企业管理（含：财务管理、市场营销、人力资源管理）",
               "管理科学与工程",
               "马克思主义理论与思想政治教育",
               "计算机软件与理论",
               "课程与教学论",
               "计算机应用技术",
               "外科学(含：普外、骨外、泌尿外、胸心外、神外、整形、烧伤、野战外)",
               "内科学(含：心血管病、血液病、呼吸系病、消化系病、内分泌与代谢病、肾病、风湿病、传染病)",
               "计算机科学与技术",
               "通信与信息系统",
               "金融学（含∶保险学）",
               "信息与通信工程",
               "会计学",
               "外国语言学及应用语言学",
               "英语语言文学",
               "设计艺术学",
               "机械工程",
               "行政管理",
               "材料科学与工程",
               "材料学",
               "工商管理",
               "控制科学与工程",
               "控制理论与控制工程",
               "民商法学(含：劳动法学、社会保障法学)",
               "美术学",
               "生物化学与分子生物学",
               "体育教育训练学",
               "土木工程",
               "结构工程",
               "环境工程",
               "产业经济学",
               "农业经济管理","国际法学(含：国际公法、国际私法、国际经济法)",
               "交通运输规划与管理",
               "中国近现代史",
               "中国现当代文学"]

    # 获取cookie
    BASIC_URL = "http://kns.cnki.net/kns/brief/result.aspx"
    # 利用post请求先行注册一次
    SEARCH_HANDLE_URL = "http://kns.cnki.net/kns/request/SearchHandler.ashx/?"
    # 发送get请求获得文献资源
    GET_PAGE_URL = "http://kns.cnki.net/kns/brief/brief.aspx?pagename="
    # 切换页面基础链接
    CHANGE_PAGE_URL = "http://kns.cnki.net/kns/brief/brief.aspx"
    # 数据本地存放路径
    BRIEF_PATH = r"D:\Work\12_Workspace_Python\CnkiSpider"
    # 芝麻代理API
    PROXY_API = "http://webapi.http.zhimacangku.com/getip?num=1&type=2&pro=&city=0&yys=0&port=1&pack=124137&ts=0&ys=0&cs=0&lb=1&sb=0&pb=4&mr=2&regions="