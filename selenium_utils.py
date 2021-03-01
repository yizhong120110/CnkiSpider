# -*- coding: utf-8 -*-
"""
@desc: 爬虫 selenium 框架
@version: python3.7
@author: shhx
@time: 2019/12/20 21:53

阿里云ECS上部署，通过 VNC 查看不能正常登录，应该是阿里云DNS的问题
    Google验证码服务reCaptcha不正常
chromedriver 下载地址
    http://npm.taobao.org/mirrors/chromedriver/79.0.3945.36/chromedriver_linux64.zip

def login_email(driver, email):
    elem = driver.find_element_by_css_selector("input[type=email]")
    # 输入用户名和密码的时候不能够一下将用户名全部输入，否则网站会判定你是爬虫，就会让你输入短信验证码
    # 此处我按照字符输入，并且每个字符输入时，间隔400毫秒
    for i in email:
        elem.send_keys(i)
        time.sleep(0.4)
    # 输入完用户名和密码以后间隔1秒再点击登录按钮
    time.sleep(1)
    driver.find_element_by_css_selector("button[type=submit]").click()
    return "ok"
"""
import time
import os
from selenium import webdriver
from logger import log as logger
from operator import methodcaller

max_time = 5


def openChrome(download_dir=None, headless=True, ext_arguments=None):
    """
    前台开启浏览器模式
    :param download_dir:
    :param headless: True 提供可视化页面，False 无头模式
    :param ext_arguments: None or list，用于扩展 options 启动项
    :return:
    """
    options = webdriver.ChromeOptions()
    arguments = []
    if headless:
        # # 去掉“chrome正受到自动测试软件的控制”
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        pass
    else:
        # 解决DevToolsActivePort文件不存在的报错
        arguments.append("--no-sandbox")
        # 指定浏览器分辨率
        arguments.append("window-size=1920x1080")
        # 浏览器不提供可视化页面. linux下如果系统不支持可视化不加这条会启动失败
        arguments.append("--headless")
        # 谷歌文档提到需要加上这个属性来规避bug
        arguments.append("--disable-gpu")
        # 不加载图片, 提升速度
        arguments.append("blink-settings=imagesEnabled=false")
        # 隐藏滚动条, 应对一些特殊页面
        arguments.append("--hide-scrollbars")
        arguments.append("--disable-dev-shm-usage")
    logger.info(f"arguments:{arguments}")
    for arg in arguments:
        options.add_argument(arg)
    if ext_arguments and isinstance(ext_arguments, list):
        logger.info(f"ext_arguments:{ext_arguments}")
        for ext_arg in ext_arguments:
            options.add_argument(ext_arg)
    if download_dir:
        prefs = {
            "profile.default_content_settings.popups": 0,
            "download.default_directory": download_dir,
        }
        options.add_experimental_option("prefs", prefs)
    # 打开chrome浏览器
    logger.info("启动chrome")
    driver = webdriver.Chrome(chrome_options=options)

    # 当你打开无头浏览器时，你需要操作一下浏览器，可以移动浏览器位置，放大或缩小浏览器，否则网站会判定你是爬虫
    # 在此，我先等待了1秒，然后放大浏览器，然后缩小浏览器，然后等待2秒
    time.sleep(1)
    driver.set_window_size(1200, 800)
    time.sleep(1)
    driver.set_window_size(1000, 800)
    time.sleep(2)
    return driver


def robot_check(driver):
    robot_str = "Please click the checkbox above to prove that you’re not a robot."
    if robot_str in driver.page_source:
        logger.info("found the robot message in driver.page_source")
        return True
    return False


def robot_click(driver):
    driver.find_element_by_css_selector("span[role=checkbox]").click()
    return "ok"


# 这个可以改成闭包的方式
def exec_func(func, driver, *args, **kwargs):
    """
    while True方式执行 func
    :param func:
    :param driver:
    :param args:
    :param kwargs:
    :return:
    """
    result = None
    test_max_time = max_time
    while True:
        try:
            #if robot_check(driver):
            #    robot_click(driver)
            result = func(driver, *args, **kwargs)
            time.sleep(0.5)
            break
        except Exception:
            test_max_time -= 1
            if test_max_time < 0:
                logger.info(f"请求超时：[{driver.current_url}]")
                logger.exception("")
                logger.info("======================== 源码 ========================")
                #logger.info(f"{driver.page_source}")
                picture_name = time.strftime(
                    "screenshot_%Y-%m-%d-%H_%M_%S", time.localtime(time.time())
                )
                driver.save_screenshot(f"{picture_name}.png")
                logger.info("======================== 源码end ========================")
                break
            logger.debug(f"{func.__name__}, sleep one second[{max_time-test_max_time}]")
            time.sleep(1)
    if not result:
        raise RuntimeError("result is None")
    return result


def check_download_end(driver, dirpath):
    """
    判断文件是否下载完成
    :param driver:
    :param dirpath:
    :return:
    """
    while True:
        all_files = [os.path.join(dirpath, x) for x in os.listdir(dirpath)]
        filepath = sorted(all_files, key=os.path.getctime, reverse=False)[0]
        if check_modified_time(filepath, 5):
            return filepath
        time.sleep(2)


def isElementExist(driver, ext, param, abstract):
    # 根据xpath判断元素是否存在
    cnt = 0
    while cnt <= 4:
        try:
            #func = f"driver.find_element_by_{ext}('{param}')"
            func = f"find_element_by_{ext}"
            logger.info(f"{abstract}，正在执行函数：{func}")
            elem = methodcaller(func, param)(driver)
            driver.implicitly_wait(10)
            return elem
        except:
            logger.warning("页面元素不存在")
            flag = False
        cnt += 1
        return flag


def isCompleteDownload(dirpath):
    # 根据后缀名判断文件是否已下载完成，2秒监听一次，3分钟未完成，退出
    cnt = 0
    while cnt < 90:
        try:
            files = [os.path.join(dirpath, x) for x in os.listdir(dirpath)]
            filename = sorted(files, key=os.path.getctime, reverse=False)[0]
            # 根据下载的文件类型继续扩展后缀
            if os.path.splitext(filename)[1] in (".pdf",):
                return True
            logger.info("正在下载中，继续监听...")
            time.sleep(2)
        except:
            logger.exception("检查下载进度异常")
            time.sleep(2)
        cnt += 1
    else:
        logger.warning("文件下载超时，程序自动退出")
        return False

