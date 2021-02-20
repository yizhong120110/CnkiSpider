from bs4 import BeautifulSoup
import re
import time
import os
import math, random
from settings import DevelopmentConfig as DEVConfig
from logger import log as logger
from urllib3.exceptions import ConnectTimeoutError
from requests.exceptions import ConnectionError,ProxyError,ReadTimeout


HEADER = {"User-Agent": random.choice(DEVConfig.USER_AGENTS)}


class PageDetail(object):
    def __init__(self):
        # 生成userKey,服务器不做验证
        self.cnkiUserKey = self.setGuid()

    def getDetailPage(self, session, proxy, refererUrl, deailUrl, year, college, title):
        """
        发送三次请求
        前两次服务器注册 最后一次正式跳转
        """
        # 这个header必须设置
        HEADER["Referer"] = refererUrl
        self.session = session
        self.session.cookies.set("cnkiUserKey", self.cnkiUserKey)
        curUrlPattern = re.compile(r'.*?dbcode=(.*?)&.*?filename=(.*?).nh')
        curUrlSet = re.search(curUrlPattern, deailUrl)
        # 前两次请求需要的验证参数
        params = {
            "curUrl": "detail.aspx?dbCode=" + curUrlSet.group(1) + "&fileName=" + curUrlSet.group(2) + ".nh",
            "referUrl": refererUrl + "#J_ORDER&",
            "cnkiUserKey": self.session.cookies["cnkiUserKey"],
            "action": "file",
            "userName": "",
            "td": str(int(time.time() * 1000))
        }
        try:
            # 首先向服务器发送两次预请求
            self.session.get(
                "https://i.shufang.cnki.net/KRS/KRSWriteHandler.ashx",
                headers=HEADER,
                params=params,
                proxies=proxy,
                verify=False,
                timeout=30)
            self.session.get(
                "https://kns.cnki.net/KRS/KRSWriteHandler.ashx",
                headers=HEADER,
                params=params,
                proxies=proxy,
                verify=False,
                timeout=30)
            pageUrl = "https://kns.cnki.net" + deailUrl
            detailRes = self.session.get(pageUrl, headers=HEADER, proxies=proxy, timeout=30)
            return self.parsePage(detailRes.text, year, college, title)
        except ConnectionError as ce:
            logger.error(f"[Get Detail Page]ConnectionError,{ce}")
            return "Error"
        except ConnectTimeoutError as cte:
            logger.error(f"[Get Detail Page]ConnectTimeoutError,{cte}")
            return "Error"
        except ProxyError as pe:
            logger.error(f"[Get Detail Page]ProxyError,{pe}")
            return "Error"
        except ReadTimeout as rt:
            logger.error(f"[Get Detail Page]ReadTimeout,{rt}")
            return "Error"
        except Exception as e:
            # 这里触发异常后会导致换学科，需要测试一下
            logger.error(f"[Get Detail Page]OtherError:{e}")
            return {}

    def parsePage(self, detailPage,year, college, title):
        """
        解析页面信息
        """
        soup = BeautifulSoup(detailPage, "lxml")
        try:
            title = title.replace("/","、  ")
            path = os.path.join(DEVConfig.BRIEF_PATH, "source", year, college)
            if not os.path.isdir(path):
                logger.info(f"目录[{path}]不存在，创建目录")
                os.makedirs(path)
            filePath = os.path.join(path, f"{title}.html")

            with open(filePath,"wb") as fileHandle:
                fileHandle.write(detailPage.encode("utf8"))
        except Exception as e:
            logger.error(f"[Parse Detail Page]download html source file error,give up:{e}")
        detailDict = {}
        # 获取摘要
        if soup.find(name="span", id="ChDivSummary"):
            abstractList = soup.find(name="span", id="ChDivSummary").strings
        else:
            logger.error("[Parse Detail Page]find no abstract")
            abstractList = ""
        self.abstract = ""
        for a in abstractList:
            self.abstract += a
        detailDict.update({"abstract": self.abstract})

        # 获取关键词和导师,关键词和导师的标签都为<p>标签
        self.keywords = []
        self.tutor = []
        try:
            keywordsLabel = soup.find_all(name="p", class_="keywords")
            keywordsText, tutorText = keywordsLabel
            for k_l in keywordsText:
                # 去除关键词中的空格，换行
                for k in k_l.stripped_strings:
                    self.keywords.append(k.strip(";"))
        except Exception as e:
            logger.error(f"[Parse Detail Page]find no keywords:{e}")
        try:
            self.tutor = tutorText.text.replace("\r", "").replace("\n", "").replace(" ", "").strip(";").split(";")
            #for t_l in tutorList:
            # 'NavigableString' object has no attribute 'stripped_strings'
            #    # 去除关键词中的空格，换行
            #    for k in t_l.stripped_strings:
            #        self.tutor.append(k.strip(";"))
        except Exception as e:
            logger.error(f"[Parse Detail Page]find no tutors:{e}")
        #logger.debug(self.keywords)
        #logger.debug(self.tutor)

        detailDict.update({"keyword": self.keywords})
        detailDict.update({"tutor": self.tutor})

        # 获取专辑subject、专题major、DOI、分类号code
        liLabel = soup.find_all(name="li", class_="top-space")
        liList = []
        liKeyword = ["subject", "major", "doi", "code"]
        if liLabel:
            for li in liLabel:
                for p in li.p.stripped_strings:
                    liList.append(p)
            liDict = dict(zip(liKeyword, liList))
        else:
            liDict = {}
        detailDict.update(liDict)
        #logger.info(title)
        return detailDict

    def setGuid(self):
        """
        生成用户秘钥
        """
        guid = ""
        for i in range(1, 32):
            n = str(format(math.floor(random.random() * 16.0), "x"))
            guid += n
            if (i == 8) or (i == 12) or (i == 16) or (i == 20):
                guid += "-"
        return guid

# 实例化
pageDetail = PageDetail()
