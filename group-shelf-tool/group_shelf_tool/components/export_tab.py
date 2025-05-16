from group_bookshelf_tool import Config
config = Config()
log = config.set_logger(__package__, __name__)

import sys
from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QFormLayout, QHBoxLayout, QVBoxLayout, QDialog,
    QWidget, QComboBox, QLabel, QPushButton, QMessageBox, QDialogButtonBox, QTreeWidget) 

from group_bookshelf_tool.components.converter import HTML_CSV_Converter
from group_bookshelf_tool.components.db_admin import DownloadHistoryTable
from group_bookshelf_tool.components.downloader import DownloaderUI
from group_bookshelf_tool.components.file_utils import PathBuilder, ZipUtility
from group_bookshelf_tool.components.helper_dialogs import (
    FileManagerDialog, ConvertDirectoryDialog)
# , BrowserDialog)


class ExportTab(QWidget):
    """
    This is the Downloader Widget
    """
    # activity_update = pyqtSignal(str)
    download_update = pyqtSignal()

    def __init__(self, parent, groups_table, driver):
        super().__init__(parent)
        self.setGeometry(100, 100, 900, 700)
        self.setContentsMargins(5, 20, 20, 0)

        self.parent = parent    
        self.groups_table = groups_table
        self.driver = driver    
        self.base_url = f"{config.base_url}/group"
        self.base_download_dir = self.download_dir = config.download_dir
        self.initialize_values()
        # Set up GroupsAdminTab and DownloadTab synchronization
        self.groups_admin_tab = parent.groups_admin_tab # set up synch
        self.groups_admin_tab.database_modified.connect(self.update_group_combobox)
        # self.groups_admin_tab.database_modified.connect(self.sync_database_values)
        self.zip_util = ZipUtility()
        self.setup_page_ui()
        self.update_group_combobox() 

    def initialize_values(self):
        """ Lists: group_names, sort_order_choices
            Variables: group_name, folder_name, sort_order_text, shelf_url, download_dir 
        """
        self.group_name = ''
        self.group_names = ['Group Names > ']
        self.sync_database_values()
        self.sort_order_choices = [
                ('Sort order> ', ''), 
                ('Ascending - better matching between archives', 'a'), 
                ('Descending - most recent bookshelf adds', 'd')]
        self.folder_name = ""
        self.sort_order_text = ""
        self.shelf_url = ""
        self.download_dir = ""
        self.set_group_data()

    def setup_page_ui(self):
        # create small widgets first
        self.page_layout = QVBoxLayout()
        self.setObjectName("download_tab")
        # log.debug(f"setup_page_ui: {self.group_names = }")
            # add the selection options form to page
        self.form_layout = self.add_form_to_page()
        self.page_layout.addLayout(self.form_layout)
            # add a label for activity message to page
        self.activity_message_label = QLabel(self)
        self.page_layout.addWidget(self.activity_message_label)
            # add a summary labe for the selection options to page
        self.summary_label = self.add_summary_label_to_page()
        self.page_layout.addWidget(self.summary_label)
        self.update_summary_label()
            # add buttons to bottom of the page
        self.button_layout = self.add_buttons_to_page()
        self.page_layout.addLayout(self.button_layout)
            # finalize the layout
        self.setLayout(self.page_layout)
        self.update_summary_label() # Updates Display

    def add_form_to_page(self):
        """ Choices will be used everywhere so they're class attributes """
        self.group_combobox = QComboBox(self)
        self.group_combobox.addItems(self.group_names)
        self.group_combobox.currentIndexChanged.connect(self.on_group_selected)
        
        self.url_label = QLabel(self)
        self.url_label.setText("None selected")

        # TODO ?: ComboBox for 30, 50, 100
        self.books_per_page = 100
        self.books_per_page_label = QLabel(self)
        self.books_per_page_label.setText(str(self.books_per_page))

        self.sort_order_combobox = QComboBox(self)
        for text, data in self.sort_order_choices:
            self.sort_order_combobox.addItem(text, data)
        self.sort_order_combobox.currentIndexChanged.connect(self.on_sort_selected)

        form_layout = QFormLayout() 
        form_layout.addRow("Group:", self.group_combobox) 
        form_layout.addRow("URL:", self.url_label) 
        form_layout.addRow("Books per page:", self.books_per_page_label) 
        form_layout.addRow("Sort order:", self.sort_order_combobox)
        return form_layout

    def add_summary_label_to_page(self):
        summary_label = QLabel(self) 
        summary_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft) 
        summary_label.setWordWrap(True)
        summary_label.setText(f""" 
    Summary of download options:
    Group> 
    Folder name>
    URL>  
    Books per page> 
    Sort order> """)
        return summary_label
       
    def add_buttons_to_page(self):
        # execute, quit buttons
        self.download_button = QPushButton(text="Start Download", parent=self)
        self.download_button.setObjectName("download_button")
        self.download_button.setMinimumSize(150, 35)
        self.download_button.clicked.connect(self.start_download)
        self.convert_button = QPushButton(text="Convert HTML to CSV", parent=self)
        self.convert_button.setObjectName("convert_button")
        self.convert_button.setMinimumSize(150, 35)
        self.convert_button.clicked.connect(self.launch_conversion_dialog)
        self.file_management_btn = QPushButton(text="File Management", parent=self)
        self.file_management_btn.setMinimumSize(150, 35)
        self.file_management_btn.clicked.connect(self.launch_file_management)

        button_layout = QHBoxLayout()
        center_alignment = Qt.AlignmentFlag.AlignCenter
        button_layout.addStretch()
        button_layout.addWidget(self.download_button, alignment=center_alignment)
        button_layout.addWidget(self.convert_button, alignment=center_alignment)
        button_layout.addWidget(self.file_management_btn, alignment=center_alignment)
        button_layout.addStretch()
        return button_layout

    def update_activity_label(self, message):
        if message is None and self.user_message is None:
            self.user_message = "Messaging system failure."
        else:
            self.user_message = message
        # log.debug(f"update_activity_label {message = }")
        self.activity_message_label.setText(self.user_message)

    def sync_database_values(self):
        self.group_names.clear()
        # log.debug(f"sync_database_values() cleared? {self.group_names = }")
        self.group_names = ['Group Names > ']
        self.group_names.extend(self.groups_table.list_group_names())

    def update_group_combobox(self):
        log.debug("Updating group combobox...")
        # clears and resets self.groups_names
        self.sync_database_values()
        # Block signal to prevent currentIndexChanged logic during update
        self.group_combobox.blockSignals(True)
        # Clears and resets the self.group_combobox
        self.group_combobox.clear()
        self.group_combobox.addItems(self.group_names)
        # Open signal back up
        self.group_combobox.blockSignals(False)

    def on_group_selected(self, index):
        # set group_name first
        self.group_name = self.group_combobox.itemText(index)
        if index == 0:
            self.set_no_group_selected()
            return 
        else:
            self.update_group_data()

    def set_no_group_selected(self):
            self.update_activity_label("No group selected")
            self.initialize_values()
            self.sort_order_combobox.setCurrentIndex(0)
            self.sort_order_text = ""
            self.update_summary_label()

    def set_group_data(self):
        self.group_data = {
            'group_name': self.group_name,
            'folder_name': self.folder_name,
            'shelf_url': self.shelf_url,
            'download_dir': self.download_dir,
        }

    def update_group_data(self):
        # log.debug(f"{self.group_name = }")
        self.folder_name = self.groups_table.get_folder_name(group_name=self.group_name)
        # log.debug(f"{self.folder_name = }")
        self.shelf_url = self.groups_table.get_shelf_url(group_name=self.group_name)
        self.shelf_url = f"{self.base_url}/{self.shelf_url}"
        self.url_label.setText(self.shelf_url)

        if not self.folder_name or self.folder_name is None:
            self.set_no_group_selected()
            return 
        else:
            self.sort_order_combobox.setCurrentIndex(1)
            self.sort_order = self.sort_order_choices[1][1]
            self.sort_order_text = self.sort_order_choices[1][0]
            self.update_activity_label(f"{self.group_name} selected.")

        self.pbuilder = PathBuilder(base_dir=self.base_download_dir)
        if not self.download_dir or self.download_dir is None:
            self.download_dir = config.download_dir
        # log.debug(f"{self.folder_name = }")
        path_data = self.pbuilder.set_download_folder(folder_name=self.folder_name)
        self.download_dir = path_data['directory_path']
        # log.debug(f"{self.download_dir = }")
        self.set_group_data()
        self.update_summary_label()

    def on_sort_selected(self, index):
        self.sort_order = self.sort_order_combobox.itemData(index)
        # log.debug(f"{self.sort_order = }")
        if index == 0 or not self.group_name:
            self.sort_order_text = ''
        else:
            self.sort_order_text = self.sort_order_combobox.itemText(index)
        # log.debug(f"{self.sort_order_text = }")
        self.update_summary_label()

    def update_summary_label(self): 
        if not self.download_dir or self.download_dir is None:
            self.download_dir = ""

        self.summary_label.setText(f"""
    <b><u>Summary of download options:</u></b><br/>
    <div style="margin-top:0; margin-left:1em;">
      <b>Group:</b> {self.group_name}<br/>
      <b>Folder name:</b> {self.folder_name}<br/>
      <b>URL:</b> {self.shelf_url} <br/>
      <b>Books per page:</b> {self.books_per_page} <br/>
      <b>Sort order:</b> {self.sort_order_text}<br/>
      <b>Download path:</b> {self.download_dir}<br/>
    </div>
    """)
        
    def emit_dialog_message(self, msg_type='information', message='Empty message'):
        self.admin_message = message
        if msg_type == 'information':
            QMessageBox.information(self, 'Information', message)
        elif msg_type == 'warning':
            QMessageBox.warning(self, 'Warning', message)
        elif msg_type == 'critical':
            QMessageBox.critical(self, 'Error', message)
        elif msg_type == 'question':
            response = QMessageBox.question(self, 'Question', message)
            if response == QMessageBox.StandardButton.Yes:
                # Handle yes response
                pass
            elif response == QMessageBox.StandardButton.No:
                # Handle no response
                pass
        else:
            # Handle unknown message type
            pass

    def start_download(self):
        if self.driver is None:
            self.update_activity_label("No web connection available")
            return
        # if not self.download_dir or self.download_dir is None:
        #     self.download_dir = config.download_dir

        data_cols = [self.group_name, self.folder_name, self.shelf_url, 
                     self.sort_order_text, self.download_dir]
        if not all(data_cols):
            self.update_activity_label("Warning: Can not download. No options are selected.")
            return
        
        self.pbuilder.make_new_dir(self.update_activity_label, Path(self.download_dir))
        # self.download = SeleniumDownloader(
        # log.debug(f"{self.driver = }")
        # log.debug(f"{self.shelf_url = }")
        # log.debug(f"{self.books_per_page = }")
        log.debug(f"Starting download...")
        self.download = DownloaderUI(
            driver=self.driver,
            shelf_url=self.shelf_url, 
            download_dir=self.download_dir,
            books_per_page=self.books_per_page, 
            sort_order=self.sort_order
        )
        self.download.message_signal.connect(self.update_activity_label)
        self.download.finished_signal.connect(self.complete_download_session)
        self.download.start()

    def launch_conversion_dialog(self):
        msg = "Dialog to convert files to CSV, GoogleSheet"
        self.update_activity_label(msg)
        log.debug(f"Dialog to convert files to CSV, GoogleSheet")
        self.update_group_data()
        # log.debug(f"{self.group_data = }")
        if not self.download_dir:
            self.download_dir = self.base_download_dir
        conversion_dialog = ConvertDirectoryDialog(target_dir=self.download_dir)
        # self.conversion_dialog.show()
        if conversion_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_dir = conversion_dialog.get_selected_directory()
            if selected_dir:
                log.debug(f"ConvertDirectoryDialog selected directory: {selected_dir}")

    def launch_file_management(self):
        # log.debug(f"{self.folder_name = }")
        # log.debug(f"{self.download_dir = }")
        if not self.download_dir:
            self.download_dir = self.base_download_dir
        file_manager_dialog = FileManagerDialog(target_dir=self.download_dir, 
                                                zip_util=self.zip_util)
        if file_manager_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_dir = file_manager_dialog.get_selected_directory()
            if selected_dir:
                log.debug(f"FileManagerDialog selected directory: {selected_dir}")

    def complete_download_session(self):
        msg = f"Downloads complete. Located at {self.download_dir}"
        log.debug(msg)
        self.update_activity_label(msg)

        self.zip_util.zip_files(self.update_activity_label, directory=self.download_dir)
        
        log.debug(f"Setting up DownloadHistoryTable")
        group_id = self.groups_table.get_group_id_by_name(group_name=self.group_name, folder_name=self.folder_name)      

        history = DownloadHistoryTable()
        history.add_download_session(
            group_id = group_id,
            group_name=self.group_name,
            folder_name=self.folder_name,
            download_dir=self.download_dir,
            sort_order=self.sort_order_text,
            books_per_page=self.books_per_page,
            status_update=self.update_activity_label,
        )
        self.download_update.emit()

    def quit(self):
        self.parent.quit_app()


# class ConversionDialog(BrowserDialog):
#     def __init__(self, parent):
#         button_configs = {
#             # "Browse": {"text": "Browse", 
#             #            "role": QDialogButtonBox.ButtonRole.ActionRole, 
#             #            "slot": "", 
#             #            "tooltip": "Browse for a file"
#             #            },
#             "Convert": {"text": "Convert HTML", 
#                         "role": QDialogButtonBox.ButtonRole.ActionRole, 
#                         "slot": "self.start_conversion_tool", 
#                         "tooltip": "Convert HTML to another format",
#                         },
#             # "Cancel": {"text": "Cancel", 
#             #            "role": QDialogButtonBox.StandardButton.Cancel, 
#             #            "slot": "", 
#             #            "tooltip": "Cancel the operation",
#             #            },
#         }
#         super().__init__(parent)
#         self.setWindowTitle("Conversion Browser")
#         self.setGeometry(100, 100, 800, 600)
#         self.parent = parent
#         self.base_dir = Path(self.parent.base_download_dir)
#         # self.layout = QVBoxLayout()
#         # self.setLayout(self.layout)

#         self.tree_widget = QTreeWidget()
#         self.tree_widget.setHeaderLabels(["Name", "Path"])
#         # self.tree_widget.itemSelectionChanged.connect(self.update_buttons)
#         self.layout.addWidget(self.tree_widget)
#         self.status_label = QLabel()
#         # self.status_label.setWordWrap(True)
#         self.layout.addWidget(self.status_label)
#         self.update_status("Testing status label")

#         self.init_button_box(button_configs)
#         # self.conversion_button = QPushButton("Convert to CSV")
#         # self.conversion_button.clicked.connect(self.start_conversion_tool)
#         # self.conversion_button.setEnabled(False)
#         # self.button_layout.addWidget(self.conversion_button)
#         # self.browse_button = QPushButton("Browse")
#         # self.browse_button.clicked.connect(self.browse_directory)
#         # self.button_layout.addWidget(self.browse_button)
#         # self.quit_button = QPushButton("Quit")
#         # self.quit_button.clicked.connect(self.quit)
#         # self.button_layout.addWidget(self.quit_button)
        
#         self.layout.addWidget(self.button_box)
#         self.display_directory(self.base_dir)

#     def update_status_message(self, message):
#         if message is None and self.user_message is None:
#             self.user_message = "Messaging system failure."
#         self.user_message = message

#     def update_status(self, message):
#         self.update_status_message(message)
#         self.status_label.setText(self.user_message)

#     # def browse_directory(self):
#     #     directory = QFileDialog.getExistingDirectory(self, "Select Directory", str(self.base_dir))
#     #     directory = Path(directory).resolve() 
#     #     if directory:
#     #         self.display_directory(directory)

#     def launch_file_management(self):
#         # log.debug(f"{self.folder_name = }")
#         # log.debug(f"{self.shelf_folder = }")
#         self.file_manager = FileManagerDialog(self)
#         self.file_manager.show()

#     def start_conversion_tool(self):
#         self.converter = HTML_CSV_Converter(self.group_data)
#         self.converter.message_signal.connect(self.update_status)
    
#     def quit(self):
#         self.close()