from group_bookshelf_tool import Config
config=Config()
log = config.set_logger(__package__, __name__)

from PyQt6.QtCore import pyqtSignal, QObject, QThread
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from fake_useragent import UserAgent
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class SiteConnector:
    def __init__(self):
        self.email_text:str = config.email
        self.password_text:str = config.password
        self.signInURL = "https://www.goodreads.com/user/sign_in"
        self.driver = None # Initialize driver as None
        if not hasattr(self, 'login_successful'):
            self.login_successful = False
        
    def start_connection(self, msg, no_browser):
        # log.info(msg)
        ua = UserAgent()
        user_agent = ua.random
        options = webdriver.ChromeOptions()
        if no_browser:
            options.add_argument("--headless=new")
        options.add_argument(f"--user-agent={user_agent}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-page-load-metrics")
        options.add_argument("--log-level=3")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        try:
            self.driver.get(self.signInURL)
            # log.debug(f"{self.driver}")
            return_msg = "Success! Connected to sign-in page."
        except Exception as e:
            return_msg = f"ERROR: Failed to connect with initial sign-in page: {self.signInURL}"
            log.error(msg)
            return False, return_msg
        return True, return_msg

    def get_dynamic_sign_in_link(self, msg):
        # log.info(msg)
        # link_xpath = f"//a[contains(@href, '/ap/signin')]"
        # button_xpath_part = f"//button[contains(text(), 'Sign in with email')]"
        # ancestor_xpath_part = "/ancestor::a[1]"
        # full_xpath = f"{link_xpath}{button_xpath_part}{ancestor_xpath_part}"
        wait = WebDriverWait(self.driver, 10)
        links = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
        self.link_href = next((link.get_attribute("href") for link in links if link.get_attribute("href") and "Sign in with email" in link.text), None)
        if not self.link_href:
            return False, "Sign in link not found"
        else:
            # msg = f"Dynamic sign-in link found: {self.link_href}"
            msg = f"Dynamic sign-in link found"
            return True, msg

    def fill_log_in_fields(self, msg):
        # log.info(msg)
        # log.debug(self.driver.capabilities["chrome"]["chromedriverVersion"])
        try:
            self.driver.get(self.link_href)
            wait = WebDriverWait(self.driver, 15)
            self.email_field = wait.until(EC.presence_of_element_located(
                (By.ID, "ap_email")))
            # log.debug("Email field found.")
            self.password_field = wait.until(EC.presence_of_element_located(
                (By.ID, "ap_password")))
            # log.debug("Password field found.")
            if self.email_field and self.password_field:
                result_msg = "Email and Password fields found."
            # log.info(result_msg)
        except Exception as e:
            log.error(result_msg)
            return False, result_msg
        return True, result_msg

    def exectute_log_in(self, msg):
        # log in fails here when Goodreads throws up an "Are you human?" test
        # main app call restarts the log in process with a browser
        try:
            # log.debug(f"Looking for signInSubmit button")
            exectute_log_in_button = self.driver.find_element(By.ID, "signInSubmit")
            self.email_field.send_keys(self.email_text)
            self.password_field.send_keys(self.password_text)
            # log.debug(f"Found {exectute_log_in_button = }")
            exectute_log_in_button.click()
            result_msg = "Submit button clicked"
            return True, result_msg
        except:
            log.error(f"No button found {bool(exectute_log_in_button) = }")
            return False, f"No Submit button found"

    def check_login_success(self, msg):
        timeout=20
        poll_frequency=0.5
        confirm_login_url = (By.XPATH, "//a[contains(@href, '/user/show/')]")
        try:
            wait = WebDriverWait(self.driver, timeout, poll_frequency=poll_frequency)
            self.confirm_login = wait.until(EC.presence_of_element_located(confirm_login_url))
            self.login_successful = True
            result_msg = "Login successful!"
            # log.info(result_msg)
            return True, result_msg
        except Exception as e:
            error_msg = f"ERROR: Final submit failed after {timeout} seconds: {e}"
            # log.error(error_msg)
            return False, error_msg

    def cleanup(self):
        # log.debug(f"\n\ndriver cleanup exists {self.driver = }")
        if self.driver:
            self.driver.quit()


class ConnectorEngine(QObject):
    """ 
    As pass through between the SiteConnector logic and the PyQt interface,
    separated for threading purposes.
    """
    logged_in = pyqtSignal(bool)
    connection_error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.site_connector = None

    def set_browser(self, no_browser):
        self.no_browser = no_browser

    def log_in_failure(self, msg):
        log.error(msg)
        self.connection_error.emit(msg)
        self.logged_in.emit(False)

    def do_connect(self):
        success, msg = self.site_connector.start_connection("Starting connection...", self.no_browser)
        try:
            if not success:
                self.log_in_failure(msg)
                return
            success, msg = self.site_connector.get_dynamic_sign_in_link("Getting dynamic sign-in link...")
            if not success:
                self.log_in_failure(msg)
                return
            success, msg = self.site_connector.fill_log_in_fields("Filling login fields...")
            if not success:
                self.log_in_failure(msg)
                return
            success, msg = self.site_connector.exectute_log_in("Submitting login credentials...")
            if not success:
                self.log_in_failure(msg)
                return
            # log.debug(f"Check login success")
            success, msg = self.site_connector.check_login_success("Checking login success..")
            if success:
                log.info(msg)
                self.logged_in.emit(True)
                self.driver = self.site_connector.driver
                return
            else:     
                self.log_in_failure(msg)
                return
            
        except Exception as e:
            error_msg = f"An unexpected error occurred during login: {e}"
            log.error(error_msg)
            self.connection_error.emit(error_msg)
            self.logged_in.emit(False)


class QSiteConnector(QObject, SiteConnector):
    logged_in = pyqtSignal(bool)
    connection_error = pyqtSignal(str)

    def __init__(self, no_browser=None):
        super().__init__()
        SiteConnector.__init__(self)
        self.log_in_success = False
        self.worker_thread = QThread()
        self.worker = ConnectorEngine()
        self.worker.set_browser(no_browser)
        self.worker.site_connector = self
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.do_connect)
        self.worker.logged_in.connect(self.logged_in)
        self.worker.connection_error.connect(self.connection_error)
        self.worker_thread.start()

    def start(self):
        # The connection process starts when the thread is started in __init__
        pass

    def cleanup(self):
        # Cleanup will be handled in the worker thread's finally block
        pass