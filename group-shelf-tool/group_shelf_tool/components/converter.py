from group_bookshelf_tool import Config
config=Config()
log = config.set_logger(__package__, __name__)

from PyQt6.QtCore import pyqtSignal, QThread
from bs4 import BeautifulSoup, SoupStrainer
import pandas as pd
from pathlib import Path

class HTML_CSV_Converter(QThread):
    message_signal = pyqtSignal(str)
    conversion_finished = pyqtSignal

    def __init__(self, download_data):
        super().__init__()
        if any(v is None for v in download_data.values()):
            self.message_signal.emit("No download to process")
            return
        for k, v in download_data.items():
            setattr(self, k, v)
            # log.debug(f"{k}: {v}")
        del self.shelf_url
        self.output_file = self.get_output_file()
        log.debug(f"{self.output_file = }")
        self.files = [file for file in Path(self.download_dir).iterdir() \
                 if file.name.endswith(".html")]
        # log.debug(f"{files}")
        self.soup_book_rows = []
        
    def get_output_file(self):
        out_path =  Path(config.output_dir)/config.processed_dir
        filename = self.download_dir.split('Downloads\\')
        log.debug(f"{filename = }")
        filename = filename[-1].replace('\\', '_')
        return out_path/f"{filename}.csv"

    def collect_book_rows(self):
        for file in self.files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    html = f.read()
                soup = BeautifulSoup(html, 'html.parser')
                self.html_header = [th.text.strip() for th in soup.find_all('th')]
                filtered_rows = [tr for tr in soup.find_all('tr') if not tr.find('th')]
                self.soup_book_rows.extend(filtered_rows)
            except Exception as e:
                print(f"Error reading file {file}: {e}")

    def cleanup_header_text(self):       
        self.html_header[0] = "img"
        self.html_header[-1] = "view_activity"

    def set_up_columns(self):
        self.col_headers = []
        for col in self.html_header[1:]:
            if ' ' in col:
                col = col.replace(' ', '_')
            if 'rating' in col:
                continue
            if 'date' in col:
                self.col_headers.append(col)
                continue
            else:
                self.col_headers.append(col)
                self.col_headers.append(f"{col}_url")
        log.debug(f"{self.col_headers}")
        log.debug(f"{len(self.col_headers) = }")

    def build_tag_map(self, td):
        # log.debug(f"tag_map: {td.find_all('a') = }")
        tag_list = []
        tag_url_list = []
        for tag in td.find_all('a'):
            text = tag.text.strip()
            # log.debug(f"{text = }")
            # if text not in self.tag_map.keys():
            #     self.tag_map[text] = tag['href']
            tag_list.append(text)
            tag_url_list.append(tag['href'])
        # log.debug(f"{tag_list = }")
        return tag_list, tag_url_list
            
    def parse_row(self, row):
        parsed_row = []
        for ix, td in enumerate(row.find_all('td')):
            # log.debug(f"{td = }")
            
            # Skip img and rating fields
            if ix in [0, 3]: 
                continue
            
            # title, author, add by user fields
            if ix in [1, 2, 7]: 
                parsed_row.append(td.text.replace('\n', ''))
                # no user link for 'deleted' user
                if 'deleted user' not in td.text: 
                    parsed_row.append(td.a['href'])
            
            # shelves field !! complicated
            #! IN FLUX: Settled on two fields for tags and tag_urls 
            elif ix == 4: 
                tags, tag_urls = self.build_tag_map(td)
                parsed_row.append(tags)
                parsed_row.append(tag_urls)

            #  log.debug(f"{td = }")
            # view activity field
            elif ix == 9:
                parsed_row.append("view activity")
                parsed_row.append(td.a['href'])
            
            # handle the 3 dates fields
            else:
                parsed_row.append(td.text.strip()) 
        # log.debug(f"{len(parsed_row) = }")
        return parsed_row
    
    def duplicate_book_titles_by_url(self, df):
        groups = [g for _, g in df.groupby("title_url") if len(g) > 1]
        if groups:
            dups = pd.concat(groups)
        else:
            dups = None
        log.debug(f"{dups = }")
        return dups
    
    # def parse_rows(self):
    #     self.parsed_rows = [self.parse_row(row) for row in self.soup_book_rows]

    def run(self):
        self.tag_map = {}
        self.collect_book_rows()
        self.cleanup_header_text()
        self.set_up_columns()
        # for ix, col in enumerate(self.html_header):
        #     log.debug(f"{ix} - {col}")
        # for ix, col in enumerate(self.col_headers):
        #     log.debug(f"{ix} - {col}")
        
        # self.parse_rows()
        self.parsed_rows = [self.parse_row(row) for row in self.soup_book_rows]

        df = pd.DataFrame(self.parsed_rows, columns=self.col_headers)
        dups = self.duplicate_book_titles_by_url(df)
        if dups is None:
            df.to_csv(self.output_file, index=False)
        else:
            log.warning(f"Warning! Duplicate book titles based on url id exist")
        # log.debug(f"{df.columns}")
        # log.debug(f"\n{[df['shelves'].iloc[813]]}")
        # log.debug(f"\n{[df['shelves'].iloc[1017]]}")


    
if __name__ == "__main__":
    group_data = {  
        'group_name': "MM Romance",
        'folder_name': "MM_Romance",
        'shelf_url': '',
        'download_dir': r"C:\GoodreadsGroupBookshelfTool\BookShelfData\Downloads\MM_Romance\2025\May02_1230",
        # 'download_dir': r"C:\GoodreadsGroupBookshelfTool\BookShelfData\Downloads\YA_LGBT_Books\2025\May05_1313"
    }
    conv = HTML_CSV_Converter(group_data)
    conv.run()