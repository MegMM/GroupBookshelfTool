from group_bookshelf_tool import Config
config = Config()
log = config.set_logger(__package__, __name__)

import os

import os
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class InitDBWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Selenium in PyQt6")
        self.setGeometry(100, 100, 275, 200)
        self.database = config.database
        self.database_exists = os.path.exists(self.database)

        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)

        self.database_status_label = QLabel()
        self.database_status_label.setText("No connection started")
        self.database_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.database_status_label.setStyleSheet("""
            font-family: Titillium;
            font-size: 14px;
            width = 200;
            padding-bottom: 10px;
            """)
        self.database_status_label
        self.main_layout.addWidget(self.database_status_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.test_buttton = QPushButton("Test existing database")
        self.test_buttton.clicked.connect(self.test_database)
        self.main_layout.addWidget(self.test_buttton)

        self.initialize_button = QPushButton("Initialize new database\n(removes existing database)")
        self.initialize_button.clicked.connect(self.initialize_database)
        self.main_layout.addWidget(self.initialize_button)

        self.load_button = QPushButton("Load data file")
        self.load_button.clicked.connect(self.load_data)
        self.main_layout.addWidget(self.load_button)

        self.quit_button = QPushButton("Quit Setup")
        self.quit_button.setObjectName("long_btn")
        self.quit_button.clicked.connect(self.quit_app)
        self.main_layout.addWidget(self.quit_button)

        self.setCentralWidget(self.main_widget)

    def update_status_label(self, message):
        self.database_status_label.setText(message)
    
    def test_database(self):
        if self.database_exists:
            try:
                from group_bookshelf_tool.components.db_admin import SessionLocal
                with SessionLocal():
                    pass
                message = "Database connection confirmed."
                log.info(f"{message}")
                self.update_status_label(message)

            except:
                message = "Removing corrupt database. Re-initialize."
                log.info(f"{message}")
                self.update_status_label(message)
                os.remove(self.database)   
        else:
            message = "No database exists."
            log.info(f"{message}")
            self.update_status_label(message)

    def initialize_database(self):
        try:
            message = "Initializing database. Removing existing database."
            log.info(f"{message}")
            self.update_status_label(message)
            os.remove(self.database) 
            try:
                from group_bookshelf_tool.components.db_admin import GroupsTable
                gr = GroupsTable()
                gr.create_groups_table()
            except:
                message = "Failed to create table."
                log.info(f"{message}")
                self.update_status_label(message)

        except:
            message = "Failed to remove existing database."
            log.info(f"{message}")
            self.update_status_label(message)

    def load_data(self):
        try:
            from group_bookshelf_tool.components.db_admin import GroupsTable
            gr = GroupsTable() 
            gr.load_data()
            message = "Data successfully uploaded."
            log.info(f"{message}")
            self.update_status_label(message)
        except:
            message = "Failed to upload data."
            log.info(f"{message}")
            self.update_status_label(message)              

    def quit_app(self):
        self.close()

def run_db_init():
    app = QApplication(sys.argv)
    window = InitDBWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_db_init()




# gr = GroupsTable()
# gr.init_table()