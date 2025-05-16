from group_bookshelf_tool import Config
config=Config()
log = config.set_logger(__package__, __name__)

from pathlib import Path
from pynput import keyboard
from random import randint
from PyQt6.QtCore import pyqtSignal, QThread
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import math
import re
import time


class Downloader:
    def __init__(self, driver, shelf_url: str, download_dir: str|Path, books_per_page: str|int, 
                 sort_order: str):
        self.driver = driver
        self.shelf_url:str = shelf_url
        self.download_dir:str = download_dir
        # log.debug(f"{books_per_page = }")
        self.books_per_page = int(books_per_page)
        self.sort_order:str = sort_order if sort_order else 'a'
        self.max_pages = 100
        self.start_page:int = 1
        self.filename_prefix = "page_" 
        self.book_count:int = self.find_book_count()
        log.debug(f"\n{self.book_count = }\n")

    def run(self):
        """ 
        Launches self.run_downloader and closes driver when finished. 
        Not all operations require it, hence they're split apart.
        """
        self.cancel_requested = False
        self.download_complete = False
        success = None
        self.reverse_file_numbering = False
        if self.driver is None:
            return "No web connection available"
        
        self.total_pages = math.ceil(self.book_count/self.books_per_page)
        if self.total_pages > self.max_pages:
            try:
                log.debug(f"Starting download first half of large bookshelf... \n")
                success, result_msg = self.run_downloader(
                                        first_page=self.start_page, 
                                        last_page=self.max_pages)
            except Exception as e:
                log.error(f"Failed to process first half of large bookshelf (more than 10,000 books): {e}")

            if success:
                self.download_complete = False
                self.reverse_file_numbering = True
                self.set_reverse_sort_order()
                try:
                    log.debug(f"Starting download second half of large bookshelf... \n")
                    log.debug(f"{self.max_pages+1 = }")
                    log.debug(f"{min(self.total_pages, self.max_pages*2) = }")
                    success, result_msg = self.run_downloader(
                                        first_page=self.max_pages+1, 
                                        last_page=min(self.total_pages, self.max_pages*2))
                    # log.debug(f"{result_msg = }")
                
                except Exception as e:
                    log.error(f"Failed to process second half of large bookshelf (more than 10,000 books): {e}")
                self.download_complete = True
        else:
            try:
                success, result_msg = self.run_downloader(
                                        first_page=self.start_page, 
                                        last_page=self.total_pages)
                log.debug(f"{result_msg = }")
                self.download_complete = True
            except:
                log.error(f"Failed to process standard-sized shelf")

        return result_msg

    def run_downloader(self, first_page, last_page):
        """
        Downloads content from a paginated Goodreads bookshelf (or similar) to individual files.
        Enhanced downloader function that supports both ascending and descending page numbering
        """
        # using self.max_pages ends the file_num count  at 101 in reverse order
        page_range = range(self.start_page, last_page + 1)
        TESTING = False
        #! WARNING: not sure the listener works in conjunction with PyQt6
        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()

        try:
            log.debug(f"\n{page_range = }\n")
            for page_num in page_range:
                if self.cancel_requested:
                    listener.stop()
                    result_msg = "Warning: Download cancelled by user."
                    break # exit loop.
                log.debug(f"{page_num = }")
                # log.debug(f"{absolute_url_path = }")
                if self.reverse_file_numbering:
                    file_num = last_page - (page_num - self.start_page)
                    # log.debug(f"{last_page}-{page_num}+{self.start_page} = {file_num = }\n")
                else:
                    file_num = page_num
                    # log.debug(f"{file_num = }\n")
                if not TESTING:
                    result_msg = self.read_and_save_webpage(page_num, file_num)
                    log.debug(result_msg)
            if not self.cancel_requested:
                listener.stop()
            result_msg = f"Download loop complete"
            success = True
        except Exception as e:
            result_msg = f"Error during download: {e}"
            log.error(result_msg)   
            success = False

        return success, result_msg
        
    def read_and_save_webpage(self, page_num, file_num):
        # Navigate to url
        try:
            self.absolute_url = self.set_absolute_url(page_num)
            self.driver.get(self.absolute_url)  
            # Get the page source
            page_source = self.driver.page_source
            self.filepath = self.set_full_path(f"{self.filename_prefix}{file_num}.html")
            with open(self.filepath, "w", encoding="utf-8") as file:
                file.write(page_source)
            result_msg = f"Saving {self.absolute_url = } to {self.filepath = }"
            # log.debug(result_msg)
        except:
            result_msg = f"Failed to download or save web page: {self.absolute_url}, {self.filepath}"
            # log.error(result_msg)
        finally: 
            delay_min, delay_max = (3, 5)
            sleep_time = randint(delay_min, delay_max)
            time.sleep(sleep_time)
            return result_msg

    def find_book_count(self):
        try:
            # Ensure we are on the first page
            self.driver.get(self.shelf_url)
            # Wait for the element containing the total book count to be present
            # Use a precise XPath locator, parent::div
            parent_link_locator = (By.XPATH, "//div/a[@class='actionLinkLite greyText']/parent::div")
            parent_div = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(parent_link_locator))
            # log.debug(f"{parent_div = }")
            # Extract the text from the parent div
            text = parent_div.text
            log.debug(f"Total book count text: {text}")
            # Parse the text to extract the total book count
            # (Adapt this regex based on the format of the text)
            match = re.search(r"\((\d+)\)", text)  # Regex to extract the number within parentheses
            if match:
                return int(match.group(1))
            else:
                log.error(f"Could not extract total book count from text: {text}")
                return self.start_page  # Or handle this case appropriately
        except Exception as e:
            log.error(f"Error finding last page: {e}")
            return self.start_page  # Or handle this case appropriately

    def set_reverse_sort_order(self):
        self.sort_order = 'd' if self.sort_order == 'a' else 'a'

    def set_absolute_url(self, page_num):
        ''' Construct the full url '''
        return f"{self.shelf_url}?page={page_num}&order={self.sort_order}&per_page={self.books_per_page}&utf8=%E2%9C%93"

    def set_full_path(self, filename):
        path = Path(self.download_dir)
        return path/filename

    def on_press(self, key):
        try:
            if key.char == 'q':
                self.cancel_requested = True
                # Stop listener
                return False
        except AttributeError:
            pass


class DownloaderUI(QThread):
    message_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    cancel_signal = pyqtSignal()

    def __init__(self, driver, shelf_url: str, download_dir: str|Path, books_per_page: str|int, 
                 sort_order: str):
        super().__init__()
        # log.debug(f"DownloaderUI: {driver = }, {shelf_url = }")
        # log.debug(f"DownloaderUI: {books_per_page = }")
        self.downloader = Downloader(driver=driver, shelf_url=shelf_url, 
                                    download_dir=download_dir, books_per_page=books_per_page, sort_order=sort_order)
        
    def run(self):
        msg = "Starting downloads..."
        log.info(msg)
        self.message_signal.emit(msg)
        result_msg = self.downloader.run()
        if self.downloader.cancel_requested:
            self.cancel_signal.emit()
        self.message_signal.emit(result_msg)
        if self.downloader.download_complete:
            self.finished_signal.emit() # always emit finished signal.

