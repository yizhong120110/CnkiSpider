# -*- encoding: utf-8 -*-
'''
@File    :   paper.py    
@Contact :   yizhong120110@gmail.com
@Descrip :   知网博硕士论文爬虫

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2020/10/26 13:31   qiuy      1.0         init
2020/11/05 10:00   qiuy      2.0         增加代理部分，使用芝麻代理，每一次重构类实体更换一次代理
'''

import requests, time, random, os, pprint, re, math, json, copy
from urllib3.exceptions import ConnectTimeoutError
from requests.exceptions import ConnectionError,ProxyError,ReadTimeout
from bs4 import BeautifulSoup
from settings import DevelopmentConfig as DEVConfig
from logger import log as logger
from getPageDetail import pageDetail
from urllib.parse import quote
import pymongo
# 移除ssl认证警告
requests.packages.urllib3.disable_warnings()


def getCollege():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),"college.txt")
    with open(path,"rb") as fileHandle:
        collegeStr = fileHandle.read()
    collegeLst = collegeStr.decode("utf8").split("\r\n")
    return collegeLst


def delCollege(college, move):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "college.txt")
    #with open(path, "rb") as fileHandle:
    #    collegeStr = fileHandle.read()
    #newCollegeStr = collegeStr.replace((college + "\r\n").encode("utf8"), b"")
    #with open(path, "wb") as fileHandle:
    #    fileHandle.write(newCollegeStr)
    #if move:
    #    delPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "delCollege.txt")
    #    with open(delPath, "a") as fileHandle:
    #        fileHandle.write(college + "\r")


def getProxies():
    proxy = {}
    try:
        time.sleep(1)
        response = requests.get(DEVConfig.PROXY_API).json()
        if response["code"] == 0:
            for item in response["data"]:
                proxy["http"] = "http://{ip}:{port}".format(**item)
                proxy["https"] = "https://{ip}:{port}".format(**item)
            logger.info("%s"%proxy)
            return proxy 
        else:
            logger.info(response["msg"])
            time.sleep(10)
            return getProxies()
    except Exception as e:
        logger.info(f"请求代理异常：{e}")
        time.sleep(20)
        return getProxies()



class paperSpider(object):
    """
        知网博硕士论文爬虫
    """
    def __init__(self, currentPage, year, college, maxPage):
        try:
            # 当前页
            self.currentPage = currentPage
            # 年份
            self.year = year
            # 学术机构
            self.college = college
            # 每次最多处理的页数
            self.maxPage = maxPage
            self.headers = {"User-Agent": random.choice(DEVConfig.USER_AGENTS)}
            # 连接mongodb
            self.client = pymongo.MongoClient(DEVConfig.MONGO_URL)
            self.connStatus = "ok"
        except Exception as e:
            raise
            logger.error(f"init error:{e}")
            self.connStatus = "OtherException"


    def searchReference(self):
        """
        按年份和学科进行检索，每次searchReference只扫描10页，使用三重循环(for、for、while)完成这项工作
        :return:    1、False:用于强制结束本次searchReference的执行
                        1）searchHandle请求失败，退出本次执行
                        2）“检索”按钮执行后无响应，退出本次执行
                        3）Scan Over 扫描超出最大页码，退出本次执行
                        4）当前概览页面解析异常，退出本次执行
                        5）其他异常，退出本次执行
                        以上五种情况都会触发while循环体的break操作，退出对本学科的处理，开始扫描下一学科
                        可优化的点：对于第1）、2）、4）种情况，简单粗暴的结束本学科的扫描，开始下一学科的扫描并不合理。如果因为反爬机制而触发这三
                        种情况，即便是扫描下一学科，也是同样的结果，不如记下当前处理的页码，等待10分钟后重新扫描，类似于对出现验证码情况的处理
                        2020-11-07 9:36 已做调整
                    2、self.currentPage:正常的返回，返回当前searchReference处理的页码。
                    3、self.currentPage - 1：出现验证码之后的返回，返回正在处理的前一页，这样在while循环体内结束本次处理，进行currentPage + 1之后，
                        还是继续处理出现验证码的这一页
        """
        # 第一次http请求，相当于注册操作
        searchHandleList = "".join([
            DEVConfig.SEARCH_HANDLE_URL,
            "action={action}&",
            "NaviCode={NaviCode}&",
            "ua={ua}&",
            "isinEn={isinEn}&",
            "PageName={PageName}&",
            "DbPrefix={DbPrefix}&",
            "DbCatalog={DbCatalog}&",
            "ConfigFile={ConfigFile}&",
            "db_opt={db_opt}&",
            "db_value={db_value}&",
            "CKB_extension={CKB_extension}&",
            "his={his}&",
            "__={__}&",
            "year_from={year_from}&",
            "year_to={year_to}&",
            "degreedanwei_value1={degreedanwei_value1}&",
            "degreedanwei_special1={degreedanwei_special1}"
        ])
        searchHandleDic = copy.deepcopy(DEVConfig.SEARCH_HANDLE)
        searchHandleDic.update({"year_from": self.year,
                                "year_to": self.year,
                                "degreedanwei_special1": "=",
                                "degreedanwei_value1": quote(self.college)}
                                )
        try:
            # 20201125 193300 发生it's not an expected result时，response的code是200，是正常的http响应。searchHandle为空，没有searchHandle，下文的搜索自然为空
            cnt = 1
            while cnt <= 3:
                self.session = requests.Session()
                #self.proxy = getProxies()
                searchHandleDic.update({"__": quote(time.asctime(time.localtime()) + " GMT+0800 (中国标准时间)")})
                url = searchHandleList.format(**searchHandleDic)
                logger.info(f"[Search Handle]第{cnt}次请求searchHandle，最多请求三次")
                response = self.session.get(url, headers=self.headers, proxies=self.proxy, timeout=30)
                if not response:
                    logger.error("[Search Handle]get no search handle,sleep 300 seconds")
                    time.sleep(300)
                    return self.currentPage - 1
                searchHandle = response.text
                if searchHandle:
                    logger.info(f"[Search Handle]成功获取searchHandle:{searchHandle}，模拟检索操作")
                    break
                else:
                    if cnt < 3:
                        logger.info("[Search Handle]未获取到searchHandle,可能是因为网络原因，也可能是不存在本学术机构的文献数据，10秒后进入下一次重试")
                        time.sleep(10)
                    cnt += 1
            else:
                # 三次重试后扔未获取到searchHandle，直接return False，开始检索下一学术机构文献
                logger.info("[Search Handle]max retries exceeded with searchHandle,return False,scan next college")
                return False
            # 第二次，“检索”按钮执行后的查询结果
            timestamp = str(int(time.time() * 1000))
            # get请求中需要传入第一个检索条件的值（学科专业）
            #key_value = quote(self.subject)
            key_value = ""
            self.getPageUrl = DEVConfig.GET_PAGE_URL + searchHandle + "&t=" + timestamp + "&keyValue=" + key_value + "&S=1&sorttype="
            response = self.session.get(self.getPageUrl, headers=self.headers,proxies=self.proxy,timeout=30)
            if not response:
                logger.error("[Click Check Button]get no result,sleep 180 seconds")
                # return False
                time.sleep(180)
                return self.currentPage - 1
            try:
                referencNumPattern = re.compile(r".*?找到&nbsp;(.*?)&nbsp;")
                referenceNum = re.search(referencNumPattern, response.text).group(1)
                referenceNum = int(referenceNum.replace(",", ""))
                referenceNumStr = str(referenceNum)
                self.referencePages = math.ceil(referenceNum / 20)
                logger.info("[Click Check Button]检索到" + referenceNumStr + "条结果，共计" + str(self.referencePages) + "页")
                if referenceNum == 0:
                    logger.info("[Click Check Button][%s]的论文文献数量为0，跳过" % self.college)
                    delCollege(self.college, True)
                    return False
                if self.currentPage > self.referencePages or self.currentPage > 300:
                    logger.info("[Search Reference]扫描超出最大页码范围，退出并删除该学术机构，开始下一个学术机构文献的扫描")
                    delCollege(self.college, False)
                    return False
                if self.referencePages > 1:
                    # 页面跳转
                    changePagePattern = re.compile(r'.*?pagerTitleCell.*?<a href="(.*?)".*')
                    self.changePageUrl = re.search(changePagePattern, response.text).group(1)
                # 支持跳页扫描
                if self.currentPage > 1:
                    res = self.getOtherPage(self.maxPage)
                else:
                    res = self.parsePage(response.text, self.maxPage-1)
                    #res = self.parsePage(response.text, self.maxPage)
                if res == "Captcha Code":
                    return self.currentPage - 1
                elif res == "Scan Over":
                    return False
                elif res == "Detail Error":
                    # 扫描过程中代理IP失效，记录当前页码，更换代理IP后重新扫描这一页
                    return self.currentPage - 1
                else:
                    return self.currentPage
            except ConnectionError as ce:
                logger.error(f"[Get Other Page]ConnectionError,current pageno:%d,%s" % (self.currentPage, ce))
                time.sleep(180)
                return self.currentPage - 1
            except ProxyError as pe:
                # 发生此异常，一般是位于getOtherPage中的数据请求，等待3分钟后重新处理本页，而不是直接跳过该学科
                logger.error("[Get Other Page]ProxyError,current pageno:%d,%s" % (self.currentPage, pe))
                time.sleep(180)
                return self.currentPage - 1
            except ReadTimeout as rt:
                logger.error(f"[Get Other Page]ReadTimeout,current pageno:%d,%s" % (self.currentPage, rt))
                time.sleep(180)
                return self.currentPage - 1
            except Exception as e:
                # 虽然request有响应，但响应内容并非预期
                logger.error(f"[Get Other Page]it's not an expected result:{e}")
                return False
        except ConnectionError as ce:
            logger.error(f"[Click Check Button]ConnectionError,current pageno:%d,%s" % (self.currentPage, ce))
            time.sleep(180)
            return self.currentPage - 1
        except ConnectTimeoutError as cte:
            # 扫描过程中代理IP失效，记录当前页码，更换代理IP后重新扫描这一页
            logger.error("[Click Check Button]ConnectTimeoutError,current pageno:%d,%s"%(self.currentPage,cte))
            time.sleep(180)
            return self.currentPage - 1
        except ProxyError as pe:
            logger.error("[Click Check Button]ProxyError,current pageno:%d,%s"%(self.currentPage,pe))
            time.sleep(180)
            return self.currentPage - 1
        except ReadTimeout as rt:
            logger.error(f"[Click Check Button]ReadTimeout,current pageno:%d,%s" % (self.currentPage, rt))
            time.sleep(180)
            return self.currentPage - 1
        except Exception as e:
            logger.error(e)
            return False

    def parsePage(self, pageSource, leftPage):
        logger.info("[Parse Page]正在处理第%d页" % self.currentPage)
        soup = BeautifulSoup(pageSource, "lxml")
        keyList = ["title", "author", "college", "degree", "year", "detail"]
        # 定位到内容表区域
        tr_table = soup.find(name="table", attrs={"class": "GridTableContent"})
        # 处理验证码
        try:
            # 去除第一个tr标签（表头）
            tr_table.tr.extract()
        except Exception as e:
            # sleep10分钟后，强制使searchReference方法return以退出本次循环，进入下一次10页的轮询
            logger.error("[Parse Page]出现验证码，等待十分钟后退出本次循环，刷新session，重新处理本页")
            time.sleep(600)
            return "Captcha Code"
            #return self.parse_page(
            #    crack.get_image(self.get_result_url, self.session,pageSource))
        # 遍历每一行
        trList = []
        for index, tr in enumerate(tr_table.find_all(name="tr")):
            tdList = []
            # 遍历每一列
            for idx, td in enumerate(tr.find_all(name="td")):
                tdText = ""
                # stripped_strings：用来获取目标路径下所有的子孙非标签字符串，会自动去掉空白字符串，返回的是一个生成器
                # 在td标签下还存在在a、span等标签，这个方法的作用是提取出所有的非
                if idx == 1:
                    for string in td.stripped_strings:
                        tdText += string
                    # 解析详情链接
                    aTag = td.find(name="a", attrs={"class": "fz14"})
                    if aTag:
                        detailUrl = aTag.attrs["href"]
                    else:
                        logger.error("do not find detail url")
                        detailUrl = ""
                else:
                    for string in td.stripped_strings:
                        if " " in string:
                            string = string.split(" ")[0]
                        tdText += string
                if 1 <= idx <= 5:
                    tdList.append(tdText)
            # modify by qiuy @ 20201102 174300 mongodb里加入文献详情的完整url
            tdList.append("https://kns.cnki.net" + detailUrl)
            tdDict = dict(zip(keyList, tdList))
            title = tdDict.get("title")
            # 解析文献详情，因网络故障最多重试三次，三次后更换代理重新处理本页
            cnt = 0
            while cnt < 3:
                detailDict = pageDetail.getDetailPage(self.session, self.proxy, self.getPageUrl, detailUrl, self.year, self.college, title)
                if detailDict == "Error":
                    logger.error("[Get Detail Page]failed,sleep 5 seconds,then try again]")
                    cnt += 1
                    time.sleep(5)
                    continue
                else:
                    break
            else:
                logger.info("[Get Detail Page]max retries exceeded with this detail,re-download all papers of page %d"%self.currentPage)
                return "Detail Error"
            tdDict.update(detailDict)
            trList.append(tdDict)
            logger.info(title)
            time.sleep(4)
        self.savePaper(self.currentPage, trList, self.client)
        if leftPage >= 1:
            self.currentPage += 1
            if self.currentPage > self.referencePages or self.currentPage > 300:
                logger.info("[Parse Page]扫描超出最大页码范围，退出，开始下一个学术机构文献的扫描")
                delCollege(self.college, False)
                return "Scan Over"
           # else:
                # 注意此处必须return，用一个例子来说明一下不加return的结果
                # 假定一次检索只有2页内容（25篇论文），当self.currentPage累加到2的时候调用self.getOtherPage方法，注意，此时没有return
                # 在self.getOtherPage方法里又继续调用self.parsePage方法，此时self.currentPage累计到3，触发Scan Over，因为206行调用
                # self.getOtherPage没有return，所以继续执行205行的return True。这样就导致了self.searchReference在第132行return self.currentPage
                # 该值为3。转到while循环里，spider.searchReference的返回值为3，满足else条件，继续加1，变成了4。因此进行下一次while的轮询时，就变成了
                # 从第4页开始，而第4页没有任何内容，触发了click check button异常，退出了while循环。
            return self.getOtherPage(leftPage)
        return True

    def getOtherPage(self,leftPage):
        """
        def getOtherPage(self, startPage, endPage):
        请求其他页面和请求第一个页面形式不同
        重新构造请求
        """
        curpagePattern = re.compile(r".*?curpage=(\d+).*?")
        self.otherPageUrl = DEVConfig.CHANGE_PAGE_URL + re.sub(
            curpagePattern, "?curpage=" + str(self.currentPage),
            self.changePageUrl)
        logger.info(self.otherPageUrl)
        # 试一下，在这里优化，减少出现not an except result的情况,重试三次
        response = self.session.get(self.otherPageUrl, headers=self.headers, proxies=self.proxy,timeout=30)
        leftPage -= 1
        return self.parsePage(response.text, leftPage)

    def savePaper(self, title, paper, client):
        path = os.path.join(DEVConfig.BRIEF_PATH,"data",self.year,self.college)
        if not os.path.isdir(path):
            logger.info(f"目录[{path}]不存在，创建目录")
            os.makedirs(path)
        filePath = os.path.join(path, f"{title}.txt")
        with open(filePath, "wb") as fileHandle:
            fileHandle.write(str(paper).encode("utf8"))
        #db = client[DEVConfig.DB]
        #col = db[DEVConfig.COL]
        #col.insert_many(paper)


if __name__ == "__main__":
    collegeLst = getCollege()
    #currentPage = 1
    year = DEVConfig.YEAR
    logger.info(f"正在处理[{year}]年的数据")
    for college in collegeLst:
        path = os.path.join(DEVConfig.BRIEF_PATH, "data", year, college)
        if os.path.isdir(path):
            fileNum = len(os.listdir(path))
        else:
            fileNum = 0
        logger.info(f"正在处理学术机构为[{college}]的数据，当前共有[{fileNum}]页")
        currentPage = fileNum + 1
        if fileNum == 300:
            logger.info(f"[Main]该学术机构的论文下载数量已超过最大值，中止本次扫面，并删除该学术机构")
            delCollege(college, False)
            time.sleep(2)
            continue
        while True:
            logger.info("[Main]启动新的一轮数据读取，建立爬虫类")
            spider = paperSpider(currentPage, year, college, 10)
            #if spider.connStatus in ("ConnectTimeoutError","ProxyError"):
            # 这里需要测试一下，比如，处理到第五页，主动抛出connection异常，测试下一次的currentpage是不是5
            #    continue
            if spider.connStatus == "OtherException":
                logger.info("突发其他异常，程序退出")
                exit()
            logger.info("[Main]请求代理，构建session，查询该学术机构的论文文献")
            currentPage = spider.searchReference()
            # 0 == False  True
            if type(currentPage) == bool and currentPage == False:
                # 知网最多支持爬取300页，爬完300页后退出，并重置起始页码
                #logger.info("can not find more information,break,and scan next subject")
                #currentPage = 1
                time.sleep(2)
                break
            else:
                currentPage += 1
            time.sleep(2)
