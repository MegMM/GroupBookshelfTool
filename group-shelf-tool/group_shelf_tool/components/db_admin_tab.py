from group_bookshelf_tool import Config
config = Config()
log = config.set_logger(__package__, __name__)
#log.debug(f"config {__package__}.{__name__}")

# import sys
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
# import subprocess
from PyQt6.QtCore import (
    Qt, 
    # QDir,
    QProcess, 
    QSize, 
    pyqtSignal
)
# from PyQt6.QtGui import (
#     QAction, 
#     QPalette, 
#     QColor
# )
from PyQt6.QtWidgets import (
    # QApplication, 
    # QMainWindow,    # window components
    # QGridLayout,    # layouts
    QFormLayout, 
    QHBoxLayout,  
    QVBoxLayout,                       
    QWidget, 
    # QCheckBox, 
    QComboBox, 
    QDialog, 
    QDialogButtonBox,
    # QFileDialog, 
    QInputDialog,
    QLabel, 
    QLayout,
    QLineEdit, 
    QListWidget, 
    QMessageBox, 
    QPushButton, 
    # QRadioButton, 
    QStackedWidget,
    QStackedLayout, 
    # QTabWidget, 
    # QTabBar, 
    QTableWidget, 
    QTableWidgetItem, 
    # QTextEdit,
    # QSizePolicy             # sizing and looks
)        
import group_bookshelf_tool.components.db_admin as db
from group_bookshelf_tool.components.db_init import InitDBWindow
# main_stylesheet = Path(config.PROJSRC) / 'main.qss'
# groups_table = db.GroupsTable()

class DBAdminTab(QWidget):
    """
    This is the Master Tab Widget
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.groups_table = parent.groups_table
        self.setContentsMargins(5, 20, 20, 0)
        # Create the page_layout
        page_layout = QVBoxLayout(self)
        self.initialize_groups_btn = QPushButton(f"Initialize Groups")
        self.initialize_groups_btn.setObjectName("long_btn")
        self.initialize_groups_btn.clicked.connect(self.init_db)
        page_layout.addWidget(self.initialize_groups_btn)

        self.initialize_books_btn = QPushButton(f"Add Group")
        self.initialize_books_btn.setObjectName("long_btn")
        # self.initialize_books_btn.clicked.connect(self.add_groups)

        self.initialize_books_btn = QPushButton(f"Update Group data")
        self.initialize_books_btn.setObjectName("long_btn")
        # self.initialize_books_btn.clicked.connect(self.update_group)

        self.initialize_books_btn = QPushButton(f"View Data")
        self.initialize_books_btn.setObjectName("long_btn")
        # self.initialize_books_btn.clicked.connect(self.view_books_data)

        # Create the combobox
        self.combo_box = QComboBox(self)
        self.combo_box.addItems(["Groups", "Books", "Tags"])
        self.combo_box.currentIndexChanged.connect(self.switch_view)
        page_layout.addWidget(self.combo_box)

        # Create the stacked widget
        self.stacked_widget = QStackedWidget(self)
        page_layout.addWidget(self.stacked_widget)
        # Add views to the stacked widget
        self.group_crud = GroupCRUDWidget(self)
        self.book_crud = BookCRUDWidget(self)
        self.initialize_tables_widget = InitializeTablesWidget(self)
        self.stacked_widget.addWidget(self.initialize_tables_widget)
        self.stacked_widget.addWidget(self.group_crud)
        self.stacked_widget.addWidget(self.book_crud)
        self.stacked_widget.addWidget(QLabel("This will display CRUD ops for Groups"))
        self.quit_btn = QPushButton("Quit Application")
        self.quit_btn.clicked.connect(self.parent.quit_app)
        page_layout.addWidget(self.quit_btn)

    def switch_view(self, index):
        self.stacked_widget.setCurrentIndex(index)

    def init_db(self):
        init_window = InitDBWindow()
        init_window.show()


class InitializeTablesWidget(QWidget):
    def __init__(self, parent):
        # self.parent=parent
        super().__init__(parent)
        self.groups_table = parent.groups_table
        layout = QVBoxLayout(self)
        self.initialize_groups_btn = QPushButton(f"View Groups")
        self.initialize_groups_btn.setObjectName("long_btn")
        self.initialize_groups_btn.clicked.connect(self.load_groups_data)

        self.initialize_books_btn = QPushButton(f"View Books data")
        self.initialize_books_btn.setObjectName("long_btn")
        self.initialize_books_btn.clicked.connect(self.load_books_data)

        self.initialize_tags_btn = QPushButton(f"View Tags data")
        self.initialize_tags_btn.setObjectName("long_btn")
        self.initialize_tags_btn.clicked.connect(self.load_tags_data)

        layout.addWidget(self.initialize_groups_btn)
        layout.addWidget(self.initialize_books_btn)
        layout.addWidget(self.initialize_tags_btn)
        layout.addStretch()
        
    def load_groups_data(self):
        log.debug(f"Calling admin load_data")
        self.groups_table.load_data()

    def load_books_data(self):
        pass

    def load_tags_data(self):
        pass


class BaseCRUDWidget(QWidget):
    def __init__(self, item_type, parent=None):
        self.parent=parent
        super().__init__(parent)
        self.item_type = item_type  # "Group", "Book", "Tag", etc.
        layout = QVBoxLayout(self)
        # Create the table widget
        header_names = ['ID', 'Group Name', 'Folder Name', 'URL', 'Created Date', 'Mod Date']
        self.table_widget = QTableWidget(self)
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels(header_names)        
        self.table_widget.verticalHeader().setVisible(False)
        layout.addWidget(self.table_widget)
        
        # Button layout
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton(f"Add {self.item_type} item")
        self.edit_btn = QPushButton(f"Edit {self.item_type} item")
        self.delete_btn = QPushButton(f"Delete {self.item_type} item")
        self.quit_btn = QPushButton(f"Quit {self.item_type}")
        
        # Connect default signals
        self.add_btn.clicked.connect(self.add_item)
        self.edit_btn.clicked.connect(self.edit_item)
        self.delete_btn.clicked.connect(self.delete_item)
        self.quit_btn.clicked.connect(self.close)
        
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.quit_btn)
        layout.addLayout(button_layout)
        # self.populate_qt_table()

    # Methods to override in child classes
    def add_item(self):
        raise NotImplementedError("Subclass must implement add_item()")
        
    def edit_item(self):
        raise NotImplementedError("Subclass must implement edit_item()")
        
    def delete_item(self):
        raise NotImplementedError("Subclass must implement delete_item()")    

    def setup_qt_table(self):
        self.populate_qt_table()

    def populate_qt_table(self):
        raise NotImplementedError("Subclass must implement populate_qt_table()")


class AddGroupDialog(QDialog):
    def __init__(self, parent=None):
        self.parent = parent
        super().__init__(parent)
        self.groups_table = self.parent.groups_table if parent else None
        self.setWindowTitle("Add Group")
    #     self.setup_ui()

    # def setup_ui(self):
        layout = QVBoxLayout(self)    
        # Create form layout for fields
        form_layout = QFormLayout()

        self.group_label = QLabel("Enter Goodreads Group name: ")
        self.group_name_input = QLineEdit()
        self.group_name_input.setPlaceholderText("Group Name Here")
        form_layout.addWidget(self.group_label)
        form_layout.addWidget(self.group_name_input)
        
        self.folder_label = QLabel("Enter folder name label: ")
        self.folder_name_input = QLineEdit()
        self.folder_name_input.setPlaceholderText("group_name_here")
        form_layout.addWidget(self.folder_label)
        form_layout.addWidget(self.folder_name_input)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL")
        form_layout.addWidget(self.url_input)
        
        layout.addLayout(form_layout)
        
        qbtns = (
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        # Add dialog buttons
        button_box = QDialogButtonBox(qbtns)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_data(self):
        return {
            'group_name': self.group_name_input.text(),
            'folder_name': self.folder_name_input.text(),
            'url_str': self.url_input.text()
        }
    
    def accept(self):
        self.add_data()
        super().accept()

    def add_data(self):
        values = self.get_data()
        # log.debug(f"{values = }")
        self.groups_table.add_group_record(values)


class EditGroupWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        button_layout = QHBoxLayout()
        self.initialize_btn = QPushButton(f"Load/Reload Groups table")
        self.edit_btn = QPushButton(f"Edit Groups table")
        self.initialize_btn.clicked.connect(self.initialize_table)
        self.edit_btn.clicked.connect(self.edit_item)
        button_layout.addWidget(self.initialize_btn)
        button_layout.addWidget(self.edit_btn)

    def initialize_table(self):
        """ !!! Don't build table here"""
        pass

    def edit_item():
        pass


# class GroupCRUDWidget(BaseCRUDWidget):
#     def __init__(self, parent=None):
#         super().__init__("Group", parent)
        
#     def add_item(self):
#         # Implement group-specific add logic
#         name, ok = QInputDialog.getText(self, "Add Group", "Group name:")
#         if ok and name:
#             self.list_widget.addItem(name)
            
#     def edit_item(self):
#         current = self.list_widget.currentItem()
#         if current:
#             name, ok = QInputDialog.getText(self, "Edit Group", 
#                                           "Group name:", 
#                                           text=current.text())
#             if ok and name:
#                 current.setText(name)
                
#     def delete_item(self):
#         current = self.list_widget.currentItem()
#         if current:
#             reply = QMessageBox.question(self, "Delete Group",
#                                        f"Delete group {current.text()}?",
#                                        QMessageBox.Yes | QMessageBox.No)
#             if reply == QMessageBox.Yes:
#                 self.list_widget.takeItem(self.list_widget.row(current))

#     def refresh_data(self):
#         pass


class GroupCRUDWidget(BaseCRUDWidget):
    def __init__(self, parent=None):
        # self.parent = parent
        super().__init__("Group", parent)
        self.groups_table = parent.groups_table
        # for key, val in self.__dict__.items():
        #     log.debug(f"{key}: {val}")
        self.setup_qt_table()

    def add_item(self):
        dialog = AddGroupDialog(self)
        if dialog.exec() == QDialog.accepted:
            data = dialog.get_data()
            log.debug(f"{data = }")
            self.populate_qt_table()

    def edit_item(self):
        pass

    def show_item_details(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        QMessageBox.information(self, "Group Details",
            f"Group Name: {data['name']}\n"
            f"Folder Name: {data['folder']}\n"
            f"URL: {data['url']}")

    def populate_qt_table(self):
        records = self.groups_table.get_group_records()
        self.table_widget.setRowCount(len(records))
        # Populate the table with records
        for row_idx, record in enumerate(records):
            self.table_widget.setItem(row_idx, 0, QTableWidgetItem(str(record.id)))
            self.table_widget.setItem(row_idx, 1, QTableWidgetItem(record.group_name))
            self.table_widget.setItem(row_idx, 2, QTableWidgetItem(record.folder_name))
            self.table_widget.setItem(row_idx, 3, QTableWidgetItem(record.url_str))
            self.table_widget.setItem(row_idx, 4, QTableWidgetItem(record.create_date.strftime('%Y-%m-%d %H:%M:%S')))
            self.table_widget.setItem(row_idx, 5, QTableWidgetItem(record.mod_date.strftime('%Y-%m-%d %H:%M:%S')))
        # self.layout.addWidget(self.table)
        return records


class BookCRUDWidget(BaseCRUDWidget):
    def __init__(self, parent=None):
        super().__init__("Book", parent)
        self.populate_qt_table()

        # Add book-specific setup if needed
        
    def add_item(self):
        # Implement book-specific add logic
        pass  # Your implementation here

    def populate_qt_table(self):
        pass

