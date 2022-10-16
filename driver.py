import os
import platform
import time
import queue
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from sunday.core import Logger
from functools import partial

logger = Logger('DRIVER').getLogger()
class Driver():
    def __init__(self, *args, **kwargs):
        # targetUrl = http://ip:port/wd/hub
        self.taskq = queue.Queue()
        self.init(*args, **kwargs)

    def init(self, driverWait=20, implicitlyWait=15, arguments=[], targetUrl=None):
        logger.info('初始化驱动')
        pwd = os.path.dirname(os.path.abspath(__file__))
        if targetUrl:
            firefox_options = webdriver.FirefoxOptions()
            self.driver = webdriver.Remote(
                command_executor=targetUrl,
                desired_capabilities=DesiredCapabilities.FIREFOX,
                options=firefox_options
            )
        else:
            options = webdriver.ChromeOptions()
            for argument in arguments: options.add_argument(argument)
            # options.add_argument("--proxy-server=127.0.0.1:7758")
            # options.add_argument('headless')
            # options.add_argument('--no-sandbox')
            # options.add_argument('--disable-dev-shm-usage')
            # options.add_argument("--auto-open-devtools-for-tabs")
            # options.set_capability("browserVersion", "67")
            # options.set_capability("platformName", "Windows XP")
            self.driver = webdriver.Chrome(
                    options=options,
                    executable_path=os.path.join(pwd, 'driver', 'chromedriver-%s' % platform.system().lower()))
        self.driver.implicitly_wait(implicitlyWait)
        self.wait = WebDriverWait(self.driver, driverWait)
        # self.currentOpenWindows = self.initTabs(10)
        threading.Thread(target=self.taskRun, daemon=True).start()
        logger.info('驱动载入成功, 配置成功, 任务线程启动成功, 生成driver、wait')

    def empty(self):
        return self.taskq.empty()

    def taskRun(self):
        logger.debug('队列运行ing')
        while True:
            if not self.empty():
                logger.debug('队列执行, 当前等待任务数：%s' % self.taskq.qsize())
                task = self.taskq.get()
                if callable(task): task()
            else:
                time.sleep(0.5)

    def addTask(self, task, *params):
        self.taskq.put(partial(task, self.driver, *params))

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
