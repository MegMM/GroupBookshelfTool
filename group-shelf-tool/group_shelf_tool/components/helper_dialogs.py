from group_bookshelf_tool import Config
config = Config()
log = config.set_logger(__package__, __name__)

from pathlib import Path
from PyQt6.QtCore import Qt, QDir, pyqtSignal 
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QDialog, QDialogButtonBox, 
    QWidget, QLabel, QLineEdit, QPushButton, QSlider, QStackedLayout, QTreeView, 
    QAbstractItemView) 

# from group_bookshelf_tool.components.file_utils import ZipUtility

class TextSlider(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.text_label = QLabel()
        self.text_label.setWordWrap(True)
        self.layout.addWidget(self.text_label)

        self.text_edit = QLineEdit()
        self.text_edit.setReadOnly(True)
        self.layout.addWidget(self.text_edit)
        self.text_edit.hide()

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.valueChanged.connect(self.update_text)
        self.layout.addWidget(self.slider)
        self.slider.hide()
        self.text = ''

    def set_text(self, text):
        self.text = text
        if len(text) < 400:
            self.text_label.hide()
            # self.text_label.show()
            self.slider.hide()
            self.text_edit.show()
            self.text_edit.setText(text)
        else:
            self.text_edit.hide()
            self.slider.show()
            self.text_label.show()
            self.text_label.setText(text[:100])
            self.slider.setRange(0, len(text) - 100)
            self.slider.setValue(0)

    def update_text(self):
        start_index = self.slider.value()
        self.text_label.setText(self.text[start_index:start_index + 100])


class BaseDirectoryDialog(QDialog):
    directory_selected = pyqtSignal(str)

    def __init__(self, target_dir:str|Path, button_configs: dict, parent=None):
        super().__init__(parent)
        self.current_dir = target_dir
        self.button_configs = button_configs
        self.parent = parent
        self.selected_directory = None
        log.debug(f"BaseDirectoryDialog: {self.parent = }")

        self.setWindowTitle("Base Directory Dialog")
        self.setGeometry(100, 100, 800, 600)
        self._init_ui()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)

        # Directory Browser using QFileSystemModel
        self.status_label = TextSlider()
        self.status_label.set_text("Select Directory")
        self.status_label.setEnabled(False)
        self.layout.addWidget(self.status_label)

        self.directory_label = QLabel(self.current_dir)
        self.layout.addWidget(self.directory_label)

        self.filesystem_model = QFileSystemModel()
        self.filesystem_model.setRootPath(self.current_dir)
        # Showing both files and directories
        self.filesystem_model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)  
        self.filesystem_model.setNameFilters(["*"])  # Show all directories
        self.filesystem_model.setNameFilterDisables(False)

        self.tree_view = QTreeView()  # Changed to QTreeView
        self.tree_view.setModel(self.filesystem_model)
        self.tree_view.setRootIndex(self.filesystem_model.index(self.current_dir))
        self.tree_view.setHeaderHidden(True)  # Hide the default header
        self.tree_view.hideColumn(1)  # Hide the "Type" column
        self.tree_view.hideColumn(2)  # Hide the "Size" column
        self.tree_view.hideColumn(3)  # Hide the "Date Modified" column
        self.tree_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree_view.selectionModel().selectionChanged.connect(self.on_item_selected)
        self.layout.addWidget(self.tree_view)

        # Button Box
        self.button_box = QDialogButtonBox(Qt.Orientation.Horizontal)

        # Add buttons from the incoming configuration
        for btn_name, config in self.button_configs.items():
            button = QPushButton(config["text"])
            button_role = config.get("role")
            if button_role:
                self.button_box.addButton(button, button_role)
            else:
                self.button_box.addButton(button)  # Add without a specific role if none provided

            if "tooltip" in config:
                button.setToolTip(config["tooltip"])
            if "slot" in config:
                setattr(self, btn_name, button)

        cancel_button = QPushButton("Close")
        cancel_button.clicked.connect(self.reject)
        self.button_box.addButton(cancel_button, QDialogButtonBox.ButtonRole.RejectRole)
        self.layout.addWidget(self.button_box)

    def update_status_label(self, msg):
        self.status_label.set_text(msg)
    
    def on_item_selected(self):
        selected_indexes = self.tree_view.selectionModel().selectedIndexes()
        if selected_indexes:
            selected_index = selected_indexes[0]
            file_path = self.filesystem_model.filePath(selected_index)
            if self.filesystem_model.isDir(selected_index):
                self.selected_directory = file_path
                self.directory_label.setText(self.selected_directory)
        
    def get_selected_directory(self):
        return self.selected_directory

    

class FileManagerDialog(BaseDirectoryDialog):
    # directory_selected = pyqtSignal(str)

    def __init__(self, parent=None, target_dir=None, zip_util=None):
        target_dir = target_dir if target_dir is not None else config.output_dir
        button_configs = {
            "zip_btn": {
                "text": "ZIP Directory",
                "role": QDialogButtonBox.ButtonRole.ActionRole,
                "slot": "self.run_zip_directory",
                "tooltip": "Zip HTML Download directories",
            },
            "remove_btn": {
                "text": "Remove Empty Folders",
                "role": QDialogButtonBox.ButtonRole.ActionRole,
                "slot": "self.remove_empty_folders",
                "tooltip": "Remove empty directories",
            },
        }
        super().__init__(target_dir, button_configs, parent)
        log.debug(f"FileManagerDialog: {self.parent = }")
        self.zip_util = zip_util
        self.setWindowTitle("File Manager")
        # self.directory_selected.connect(self.on_directory_selected)
        self._connect_slots()

    def _connect_slots(self):
        if hasattr(self, "zip_btn"):
            self.zip_btn.clicked.connect(self.run_zip_directory)
        if hasattr(self, "remove_btn"):
            self.remove_btn.clicked.connect(self.on_click_remove_empty_folders)

    def run_zip_directory(self):
        selected_dir = Path(self.get_selected_directory())
        if selected_dir:
            self.update_status_label("ZIPPING HTML files in")
            self.zip_util.zip_files(self.update_status_label, 
                                    directory=selected_dir)
        else:
            self.update_status_label("No directory selected for zipping.")

    def on_click_remove_empty_folders(self):
        index = self.filesystem_model.index(self.get_selected_directory())
        # Useful info for future use. Not used here.
        # parent_index = self.filesystem_model.parent(index)
        # parent_index_info = self.filesystem_model.fileInfo(parent_index)
        # parent_dir_path = parent_index_info.absoluteFilePath()
        # log.debug(f"{parent_dir_path = }")
        # dir_index = self.filesystem_model.fileInfo(index)
        # dir_path = dir_index.absoluteFilePath()
        # log.debug(f"{dir_index = }")
        self.remove_empty_folders(index)

    def remove_empty_folders(self, index):
        dir_index = self.filesystem_model.fileInfo(index)
        if dir_index.isDir():
            dir_path = dir_index.absoluteFilePath()
            log.debug(f"Removing empty directories from {dir_path = }")
            dir = QDir(dir_path)
            if dir.isEmpty():
                dir.rmdir(dir_path)
            else:
                for entry in dir.entryList():
                    if entry != '.' and entry != '..':
                        child_index = self.filesystem_model.index(dir_path + '/' + entry)
                          # recursive call
                        self.remove_empty_folders(child_index)

        else:
            log.info("No directory selected for removing empty subdirectories.")
            return


class ConvertDirectoryDialog(BaseDirectoryDialog):
    def __init__(self, parent=None, target_dir=None):
        target_dir = target_dir if target_dir is not None else config.output_dir
        button_configs = {
            "convert_btn": {
                "text": "Convert HTML",
                "role": QDialogButtonBox.ButtonRole.ActionRole,
                "slot": "self.start_conversion_tool",
                "tooltip": "Convert HTML to another format",
            },
        }
        super().__init__(target_dir, button_configs, parent)
        self.setWindowTitle("Convert Directory")
        self._connect_slots()

    def _connect_slots(self):
        if hasattr(self, "convert_btn"):
            self.convert_btn.clicked.connect(self.start_conversion_tool)

    def start_conversion_tool(self):
        selected_dir = Path(self.get_selected_directory())
        if selected_dir:
            self.update_status_label(f"Starting conversion of HTML files in ")
            # Implement your HTML conversion logic here
        else:
            self.update_status_label("No directory selected for conversion.")

