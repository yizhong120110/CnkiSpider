# -*- encoding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium_utils import openChrome, exec_func, isElementExist, isCompleteDownload
from logger import log as logger
import time, re, os, datetime
from settings import DevelopmentConfig as devConfig
from pool.resultset import connection

LOGIN_URL = "https://user.cn-ki.net/login"
CHECK_URL = "https://www.cn-ki.net/"



def input_usernum(driver, usernum):
    time.sleep(1)
    elem = driver.find_element_by_id("num")
    for key in usernum:
        elem.send_keys(key)
        time.sleep(0.5)
    return driver


def input_passwd(driver, passwd):
    time.sleep(1)
    elem = driver.find_element_by_id("passwd")
    for key in passwd:
        elem.send_keys(key)
        time.sleep(0.5)
    # 输入密码后登录
    time.sleep(1)
    driver.find_element_by_xpath('//*[@id="app"]/div/div/div[3]/div/div/div[1]/div[3]/button').click()
    return driver


def arrow_back(driver):
    time.sleep(1)
    driver.find_element_by_css_selector("#app > div.application--wrap > div > main > div > div > div:nth-child(1) > div > div > div.card__actions > button:nth-child(1)").click()
    return driver


def high_search(driver, title, author):
    time.sleep(1)
    driver.find_element_by_xpath('//*[@id="advance_link"]/a[1]').click()
    time.sleep(1)
    # 定位第一个下拉列表
    #driver.find_element_by_xpath("/html/body/div[2]/div[2]/div[2]/div/span").click()
    #time.sleep(1)
    # 第一个下拉列表赋值为第一个选项：主题
    #driver.find_element_by_xpath('/html/body/div[2]/div[2]/div[2]/div/div/div[1]').click()
    #time.sleep(1)
    # input区域赋值title
    elem = driver.find_element_by_xpath("/html/body/div[2]/div[2]/div[3]/input")
    for key in title:
        elem.send_keys(key)
        time.sleep(0.5)
    time.sleep(1)
    # 定位第二个下拉列表
    driver.find_element_by_xpath("/html/body/div[2]/div[3]/div/div[2]/div/span").click()
    time.sleep(1)
    # 第二个下拉列表赋值为第六个选项：作者
    driver.find_element_by_xpath('/html/body/div[2]/div[3]/div/div[2]/div/div/div[6]').click()
    time.sleep(1)
    # input区域赋值author
    elem = driver.find_element_by_xpath("/html/body/div[2]/div[3]/div/div[3]/input")
    for key in author:
        elem.send_keys(key)
        time.sleep(0.5)
    time.sleep(1)
    driver.find_element_by_xpath('//*[@id="conditions"]/div[5]/div[3]/button').click()
    # 点击完后会出现一个遮罩层：正在加载，请稍后，加载完后可能搜不到目标
    elem = driver.find_element_by_xpath("/html/body/div[3]/div/span")
    driver.implicitly_wait(10)
    logger.info(elem.text)
    driver.implicitly_wait(60)
    # 校验是否搜索到了文献
    try:
        elem = driver.find_element_by_xpath("/html/body/div[2]/div[7]/div[1]/div/div[2]")
        reobj = re.findall("\d+", elem.text)
        if reobj:
            total = int(reobj[0])
        else:
            total = 0
    except:
        logger.exception("")
        total = 0
    return driver, total


def input_title(driver, title):
    time.sleep(1)
    elem = driver.find_element_by_id("txt_SearchText")
    for key in title:
        elem.send_keys(key)
        time.sleep(0.5)
    time.sleep(1)
    driver.find_element_by_class_name("mainbtn").click()
    driver.implicitly_wait(10)
    # 校验是否搜索到了文献
    try:
        elem = driver.find_element_by_xpath("/html/body/div[2]/div[6]/div/div")
        reobj = re.findall("\d+", elem.text)
        if reobj:
            total = int(reobj[0])
        else:
            total = 0
    except:
        logger.exception("")
        total = 0
    return driver, total


def get_publish_time(driver):
    time.sleep(1)
    elem = driver.find_element_by_xpath("/html/body/div[2]/div[7]/div[2]/div/div/div[1]/span[4]")
    publish = ""
    pa = re.compile("\d{4}-\d{2}-\d{2}")
    reobj = re.findall(pa, elem.text)
    if reobj:
        publish = reobj[0]
    return driver, publish


def download_and_check(driver, con, downloadPath, user):
    time.sleep(1)
    elem = driver.find_element_by_xpath("/html/body/div[2]/div[7]/div[2]/div/div/div[3]/a[1]")
    elem.click()
    driver.implicitly_wait(10)
    time.sleep(1)
    driver.switch_to.window(driver.window_handles[2])
    driver.implicitly_wait(10)
    try:
        # 这里判断账号是否被禁用了
        #elem = isElementExist(driver, "xpath", "/html/body/div[1]/div/div/div[2]/div/div/h3")
        elem = isElementExist(driver, "tag_name", "h3", "校验是否具有下载权限")
        if elem:
            if elem.text in ("您的全文配额已用完", "由于iData的服务能力有限，无法继续提供下载。如需使用权限码请点击这里使用权限码"):
                disable = "20991231"
            if elem.text == "你的下载情况异常,被系统判断为恶意批量下载，已暂停当前账号的下载权限，晚上12点后会自动解封，请明天再过来下载即可。":
                disable = datetime.datetime.now().strftime("%Y%m%d")
            sql = f"update idata_account set disable = '{disable}' where account = '{user}'"
            logger.info(sql)
            con.update(sql)
            return driver, False, elem.text
        else:
            # 出现新的跳转页面：“文献已准备就绪，点击这里下载”
            elem = isElementExist(driver, "xpath", "/html/body/div[1]/div/div/div[2]/div/div/h4", "校验下载时是否出现新的跳转界面")
            if elem:
                logger.info(elem.text)
                driver.find_element_by_xpath("/html/body/div[1]/div/div/div[2]/div/div/h4/a").click()
            #time.sleep(3)
            if isCompleteDownload(downloadPath):
                logger.info("文件下载完成")
            else:
                pass
            return driver, True, "已下载"
    except:
        logger.exception("点击下载链接异常：")
        return driver, False, "下载过程中出现异常"




def download_from_idata(con, url, user, pswd, title, author):
    logger.info(f"{title}，{author}")
    downloadPath = os.path.join(devConfig.DOWNLOAD_ROOT, str(time.time()).replace(".", ""))
    driver = openChrome(downloadPath)
    publish = ""
    try:
        # 登录
        driver.get(url)
        driver.implicitly_wait(10)
        # 输入账号
        driver = exec_func(input_usernum, driver, user)
        driver.implicitly_wait(10)
        # 输入密码并点击登录按钮
        driver = exec_func(input_passwd, driver, pswd)
        driver.implicitly_wait(10)
        # 校验密码
        elem = isElementExist(driver, "xpath", "/html/body/div/div/div/div[4]/div/div", "校验密码是否正确")
        if elem and elem.text == "密码错误":
            logger.info("密码错误")
            return False
        # 返回检索页面
        driver = exec_func(arrow_back, driver)
        driver.implicitly_wait(10)
        # 页面跳转后，定位到当前页面
        time.sleep(1)
        driver.switch_to.window(driver.window_handles[1])
        driver.implicitly_wait(10)
        # 根据标题和作者进行高级检索
        driver, total = exec_func(high_search, driver, title, author)
        if total != 1:
            # 检索到0条或者多条文件，未能精确匹配，跳过
            logger.info(f"检索到{total}条文献，退出")
            return False
        driver.implicitly_wait(10)
        # 提取发表时间
        driver, publish = exec_func(get_publish_time, driver)
        logger.info(publish)
        # 下载文献
        driver, result, message = exec_func(download_and_check, driver, con, downloadPath, user)
        driver.implicitly_wait(10)

    except:
        logger.exception("")
    finally:
        logger.info("回收driver")
        driver.quit()
        return publish, message




if __name__ == "__main__":
    titleDic = {"基于水体溶解氧变化的平原河网水力调控方案实时优化研究": "谭培影",
                "基于二维材料的热电子器件研究": "刘威",
                "高性能低成本CMOS温度传感器研究": "唐中",
                "毫米波通信若干场景中的关键算法研究与性能分析": "赵存茁",
                "基于无线能量传输技术的无线通信系统性能分析与优化": "赵斐然",
                "极化码在5G应用场景下的编译码算法研究": "秦康剑",
                "甘薯茎腐病原菌在土壤中的消长规律及轮作对菌量的影响": "赵姝",
                "面向智能电网无线终端的安全通信和抗干扰关键技术研究": "张泰民",
                "智能电磁隐身和超散射的实验研究": "钱超",
                "剪切型多自由度体系地震性能系数谱与P-Δ效应分析": "李潇",
                "外贴复材抗弯加固梁锚固效应和机理研究": "施海锋",
                "复材约束含废砖再生物混凝土应力-应变关系研究": "王晓萌",
                "计及多重不确定性和多元协调运行的光热电站调度策略研究": "赵昱宣",
                "软黏土中吸力式桶形基础上拔离心模型试验与数值分析": "代加林",
                "毛细阻滞型覆盖层微观-宏观水气传导特性及服役性能": "李光耀",
                "供水管网中土霉味卤代苯甲醚的生物甲基化生成机制研究": "周昕彦",
                "缩宫素对肠道巨噬细胞极化的调节及其治疗实验性结肠炎的机制研究": "唐燕",
                "优化加工贸易海关后续监管研究——以济南海关为例": "张磊",
                "政府委托代理招商研究——以济南X园区为例": "张萍萍",
                "山东省体育类社团协同发展模式研究": "薛晓雯",
                "运动休闲特色小镇“三生融合”优化路径研究": "展茂浩",
                "乡村振兴战略背景下河南省体育特色小镇发展路径研究": "张嘉益",
                "高强度间歇训练对12-14岁青少年脑执行功能的影响": "张庆举",
                "社会体育指导与管理专业“一体六翼”人才培养模式构建研究": "赵德",
                "山东体育节庆活动生态化发展路径研究": "赵天宇",
                "乡村振兴中的基层政府环境治理研究——以Y区W镇环境治理为例": "王苏亚",
                "外汇风险管理与高管薪酬": "张嘉文",
                "大数据背景下的车险索赔概率研究——基于随机森林模型": "张潇",
                "“无直接利益冲突”现象及其治理研究": "袁蕊",
                "新时代党员领导干部政德观培育研究": "于瑶",
                "全媒体时代马克思主义传播机制优化研究": "牛凤燕",
                "中国共产党依规治党的历史经验研究": "王国龙",
                "鼠李糖乳杆菌及其上清液对间歇性低氧所致肥胖小鼠心脏损伤的作用": "许慧",
                "纤维素纳米纤维修饰的海藻酸钠-明胶生物墨水用于韧带-骨界面细胞成分的生物3D打印": "雒文彬",
                "嵌合抗原受体T细胞治疗血液肿瘤患者细胞因子释放综合征护理方案的构建及应用": "李宇翔",
                "lncRNA THOR敲除小鼠和家兔模型的构建及其对细胞增殖影响的研究": "刘红梅",
                "新型头孢类化合物NAC-19抗耐甲氧西林金黄色葡萄球菌的作用": "田莉莉",
                "基于泛Kriging-MPSO的挠性航天器姿态机动控制方法研究": "吕雪莹",
                "DHA摄入与ELOVL2/5基因变异对母婴脂肪酸水平的影响及机制研究": "吴义霞",
                "辅助生殖技术中同卵多胎影响因素及解决方法的研究": "刘成军",
                "现代汉语不及范畴研究": "钟健",
                "东亚地区中美关系的结构性析论（2010-2020）": "范为",
                "MDSC通过多胺促进Th17分化及系统性红斑狼疮进展的机制研究": "扈聪",
    }
    publish = []
    cnt = 0
    #while cnt <= 2000:
    #    for title, author in titleDic.items():
    #        title = title.split("——")[0]
    #        ti = download_from_idata(LOGIN_URL, USERNUM, PASSWD, title, author)
    #        publish.append(ti)
    #        time.sleep(20)
    #    time.sleep(2)
    #    cnt += 1
    #logger.info(publish)
    #download_from_idata(LOGIN_URL, "粉丝对抗中的群体认同建构研究——以周杰伦超话打榜事件为例", "常振")
    while cnt <= 2000:
        for title, author in titleDic.items():
            # 连205数据库
            with connection() as con:
                today = datetime.datetime.now().strftime("%Y%m%d")
                sql = f"select account,passwd from idata_account where disable<{today} order by register asc"
                rs = con.fetchone(sql)
                if not rs:
                    logger.info("账户池中的有效账户已用尽")
                    break
                user, pswd = rs
                logger.info(f"idata用户信息:{user}")
                rs = download_from_idata(con, LOGIN_URL, user, pswd, title, author)
                logger.info(rs[1])
