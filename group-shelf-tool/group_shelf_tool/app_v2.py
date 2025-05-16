from group_bookshelf_tool import Config
config = Config()
log = config.set_logger(__package__, __name__)

import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication,  QSplashScreen, QMainWindow,
    QLabel, QPushButton, QTabWidget, QVBoxLayout, QWidget)

import qdarkstyle
import group_bookshelf_tool.components.db_admin as db
from group_bookshelf_tool.components.site_connector import QSiteConnector
from group_bookshelf_tool.components.history_tab import DownloadHistoriesTab
from group_bookshelf_tool.components.export_tab import ExportTab
from group_bookshelf_tool.components.groups_admin_tab import GroupsAdminTab

class SplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(400, 400, 350, 200)
        self.layout = QVBoxLayout()
        self.layout.addStretch()
        self.label = QLabel("Logging in...", self, alignment=Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 12pt")
        self.layout.addWidget(self.label)
        self.layout.addStretch()
        self.setLayout(self.layout)

    def show_message(self, message):
        self.label.setText(message)


class MainWindow(QMainWindow):
    def __init__(self, connector):
        super().__init__()
        # log.debug(f"MainWindow start?")
        self.connector = connector
        self.groups_table = db.GroupsTable()
        self.setWindowTitle("Goodreads Group Bookshelf Archiver")
        self.setGeometry(100, 100, 900, 600)

        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.quit_button = QPushButton("Quit Application")
        self.quit_button.setMinimumSize(850, 30)
        self.quit_button.clicked.connect(self.quit_app)
        self.main_layout.addWidget(self.quit_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.start_up_label = QLabel()
        self.main_layout.addWidget(self.start_up_label)

        self.groups_admin_tab = GroupsAdminTab(self, self.groups_table)
        self.history_tab = DownloadHistoriesTab(self, self.groups_table)
        self.export_tab= ExportTab(self, self.groups_table, self.connector)

        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        self.tab_widget.addTab(self.groups_admin_tab, "Groups Admin")
        self.tab_widget.addTab(self.export_tab, "Download Shelf")
        self.tab_widget.addTab(self.history_tab, "Downloaded Histories")
        self.main_layout.addWidget(self.tab_widget)

        self.setCentralWidget(self.main_widget)

    def post_start_up_message(self, msg):
        self.start_up_label.setText(msg)

    def quit_app(self):
        self.close()

    def closeEvent(self, event):
        self.quit_app()
        event.accept()


def set_app_style(app):
    style_sheet = qdarkstyle.load_stylesheet_pyqt6()
    app.setStyleSheet(style_sheet)
    return app

def create_app():
    # global splash
    app = QApplication(sys.argv)
    app = set_app_style(app)
    splash = SplashScreen()
    splash = set_app_style(splash)
    splash.show()
    connector = QSiteConnector()
    # Connect signals to slots
    connector.logged_in.connect(lambda success: handle_login_success(splash, connector, success))
    connector.connection_error.connect(lambda error_msg: handle_login_failure(splash, error_msg))
    # Start the connection process (which should ideally happen in a separate thread)
    # DO NOT call sys.exit(app.exec()) here. Let the event loop start after setup.
    return app, splash, connector
    
def handle_login_success(splash, connector, success):
    if success:
        connector.logged_in = True
        window = MainWindow(connector=connector)
        window.show()
        splash.close() # Close the splash screen after showing the main window
    else:
        # Handle unsuccessful login after the splash screen
        error_window = QLabel("Login was not successful.") # Replace with a more informative UI
        error_window.show()
        splash.close() # Still close the splash screen on failure

def handle_login_failure(splash, error_msg):
    splash.show_message(f"Connection failed: {error_msg}")
    # Optionally, you could add a button to retry or exit
    QApplication.quit() # Or handle the failure in a different way

if __name__ == "__main__":
    app, splash, connector = create_app()
    sys.exit(app.exec())