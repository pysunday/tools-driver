import os
import platform
import time
import queue
import threading
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from sunday.core import Logger
from functools import partial
from pydash import once

logger = Logger('DRIVER').getLogger()
class Driver():
    def __init__(self, *args, **kwargs):
        # targetUrl = http://ip:port/wd/hub
        self.taskq = queue.Queue()
        self.init(*args, **kwargs)
        self.info = {
                'debugger': False,
                'isRun': False,
                }

    def add_common_argument(self, options):
        options.add_argument('disable-infobars')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-sandbox')
        options.add_argument('--ignore-certificate-errors')

    def init(self, driverWait=20, implicitlyWait=15, arguments=[], targetUrl=None, proxy_host=None, proxy_port=None, wire_host=None):
        pwd = os.path.dirname(os.path.abspath(__file__))
        options = None
        if proxy_host and proxy_port:
            options = {
                    'proxy': {
                        'http': f'http://{proxy_host}:{proxy_port}',
                        'https': f'https://{proxy_host}:{proxy_port}',
                        },
                    }
            if wire_host:
                options['addr'] = wire_host
        logger.info('初始化驱动, wire配置：%s' % options)
        if targetUrl:
            firefox_options = webdriver.FirefoxOptions()
            self.add_common_argument(firefox_options)
            self.initConfig = {
                    'command_executor': targetUrl,
                    'desired_capabilities': DesiredCapabilities.FIREFOX,
                    'options': firefox_options,
                    'seleniumwire_options': options,
                    }
            self.driver = webdriver.Remote(**self.initConfig)
        else:
            chrome_options = webdriver.ChromeOptions()
            self.add_common_argument(chrome_options)
            for argument in arguments:
                options.add_argument(argument)
            self.driver = webdriver.Chrome(
                    options=chrome_options,
                    seleniumwire_options=options,
                    executable_path=os.path.join(pwd, 'driver', 'chromedriver-%s' % platform.system().lower()))
        self.driver.implicitly_wait(implicitlyWait)
        self.wait = WebDriverWait(self.driver, driverWait)
        # self.currentOpenWindows = self.initTabs(10)
        threading.Thread(target=self.taskRun, daemon=True).start()
        logger.info('驱动载入成功, 配置成功, 任务线程启动成功, 生成driver、wait')

    def empty(self):
        return self.taskq.empty()

    def getIsRun(self):
        if hasattr(self, 'info'):
            return self.info['isRun']
        else:
            logger.error('info未找到')
            return False

    def setIsRun(self, isRun):
        self.info['isRun'] = isRun

    def checkAlive(self):
        try:
            self.driver.title
        except Exception as e:
            logger.warning('远程驱动链接超时，重新链接')
            self.driver = webdriver.Remote(**self.initConfig)

    def taskRun(self):
        logger.debug('队列运行ing')
        def close():
            self.driver.execute_script('window.localStorage.clear()')
            self.driver.execute_script('window.sessionStorage.clear()')
            self.setIsRun(False)
            logger.debug('任务结束')
        while True:
            if self.getIsRun() == False and not self.empty():
                self.checkAlive()
                task = self.taskq.get()
                if callable(task):
                    logger.debug('任务开始, 当前等待任务数：%s' % self.taskq.qsize())
                    self.setIsRun(True)
                    task(driver=self.driver, close=once(close))
            else:
                time.sleep(0.5)

    def addTask(self, task, *params):
        self.taskq.put(partial(task, *params))

    def initTabs(self, num):
        while len(self.driver.window_handles) < num:
            self.driver.switch_to.new_window()
        return self.driver.window_handles.copy()


def run(driver, idx):
    print(f'exec task {idx}')
    driver.get('https://baidu.com')
    print(f'exec task end {idx}')


if __name__ == "__main__":
    driver = Driver(arguments=['--proxy-server=127.0.0.1:7758'])
    for i in range(5):
        driver.addTask(run, i)
    print('end')
    time.sleep(10)
