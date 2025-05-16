from group_bookshelf_tool import Config
config = Config()
log = config.set_logger(__package__, __name__)

import json
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import (
        # layouts
    QHBoxLayout, QVBoxLayout, QScrollArea, QFormLayout, 
        # widgets
    QWidget, QLabel, QPushButton, QComboBox, QLineEdit, QCheckBox, QSizePolicy,
        # table widgets
    QHeaderView, QTableWidget, QTableWidgetItem, QAbstractItemView, 
        # dialogs
    QDialog, QDialogButtonBox, QMessageBox, 
)        


class GroupsAdminTab(QWidget):
    """
    This is the Database Administration Widget
    """
    database_modified = pyqtSignal()

    def __init__(self, parent, groups_table):
        super().__init__(parent)
        self.parent = parent
        self.groups_table = groups_table
        # log.debug(f"GroupsAdminTab using groups_table with ID: {id(self.groups_table)}")
        self.setGeometry(100, 100, 900, 700)
        self.setContentsMargins(0, 0, 0, 0)
        self.db_connection_on = False
        self.page_layout = QVBoxLayout(self)
        self.draw_database_connection_box()
        # self.page_layout.addStretch()
        self.draw_groups_table()
        if self.db_connection_on:
            self.populate_qt_table()
        # self.page_layout.addStretch()
        self.draw_admin_buttons()

    def draw_database_connection_box(self):
        self.database_connection_widget = QWidget()
        self.database_connection_layout = QHBoxLayout(self.database_connection_widget)

        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(False)
        scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        preferred_height = 35
        preferred_width = 650
        self.database_status_label = QLabel()
        self.database_status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.database_status_label.setWordWrap(False)
            # Remove the fixed width
        self.database_status_label.setFixedHeight(preferred_height)
        self.database_status_label.setFixedWidth(preferred_width)
        # self.database_status_label.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.database_status_label.setStyleSheet("""
            font-family: Titillium;
            font-size: 14px;
            font-style: bold;
            padding-bottom: 12px;
            """)
        
        label_container = QWidget()
        label_container_layout = QHBoxLayout(label_container)
        label_container_layout.addWidget(self.database_status_label, )
        label_container_layout.setContentsMargins(0, 0, 0, 0)
        label_container.setFixedHeight(preferred_height)

        scrollArea.setWidget(label_container)
        scrollArea.setFixedHeight(preferred_height + 10)
        self.database_connection_layout.addWidget(scrollArea, alignment=Qt.AlignmentFlag.AlignTop)

        self.connect_db()
        if self.db_connection_on:
            self.update_database_label("Database connection started")
        else:
            self.update_database_label("No database connection started")

        self.combo_box = QComboBox()
        
        self.combo_box.addItems([
            "Database Actions",
            "Check Connection",
            "Initialize Database",
            "Load Saved Groups",
            "Save Groups to JSON"
        ])
        self.combo_box.currentTextChanged.connect(self.combo_box_selected)
        self.database_connection_layout.addWidget(self.combo_box)
        # self.database_connection_layout.addWidget(self.combo_box, alignment=Qt.AlignmentFlag.AlignTop)

        self.refresh_data_button = QPushButton(f"Refresh Data")
        self.refresh_data_button.clicked.connect(self.user_refresh)
        self.database_connection_layout.addWidget(
            self.refresh_data_button, alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.page_layout.addWidget(self.database_connection_widget)

    def combo_box_selected(self, text):
        if text == "Check Connection":
            self.connect_db()
        if text == "Initialize Database":
            self.init_table()
        elif text == "Load Saved Groups":
            self.load_saved_file()
        elif text == "Save Groups to JSON":
            self.save_to_json()

    def update_user_message(self, message):
        if message is None and self.user_message is None:
            self.user_message = "Messaging system failure."
        self.user_message = message

    def update_database_label(self, message=None):
        """ Updates the label widget """
        self.update_user_message(message)
        self.database_status_label.setText(self.user_message)

    def update_admin_message(self, message):
        self.admin_message = message

    def refresh_data(self, message=None):
        self.populate_qt_table()
        self.update_user_message(message)
        self.database_modified.emit()

    def user_refresh(self):
        self.refresh_data("Refreshed table data")

    def connect_db(self):
        """ 
        Checks if database connection is active
        Posts message to widget
        """
        try:
            self.groups_table.get_db()
            self.db_connection_on = True
            message = "Database connected"
        except Exception as e:
            message = "Database connection failed"
            log.debug(f"Connection failed: {e}")
        self.update_database_label(message)

    def init_table(self):
        """ 
        Loads data from an initialization file
        Updates admin_message with self.update_database_label()
        """
        confirm = QMessageBox.question( self, "Confirm Delete",
            f"Initializing the database removes any existing database. Proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.groups_table.init_table(self.update_database_label)
        self.refresh_data()

    def load_saved_file(self):
        """ 
        Loads data from a fixed name file
        Updates admin_message with self.update_database_label()
        """
        self.groups_table.load_data(self.update_database_label)
        self.refresh_data()

    def save_to_json(self):
        """
        Saves the fetched group data to a JSON file.
        Args: status_update() callback function
        """
        filename = self.saved_groups_file
        try:
            results = []
            for row in self.groups_table.fetch_groups():
                # Convert SQLAlchemy object to a dictionary
                result = {
                    "id": row.id,
                    "group_name": row.group_name,
                    "membership": 1 if self.make_membership_bool(row.membership) else 0,
                    "folder_name": row.folder_name,
                    "url_str": row.url_str,
                    "create_date": row.create_date.isoformat() if row.create_date else None, 
                    "mod_date": row.mod_date.isoformat() if row.mod_date else None,
                }
                results.append(result)
            with open(filename, 'w') as f:
                json.dump(results, f, indent=4)
            msg = f"Successfully saved data to {filename}"
            log.info(msg)
            self.update_admin_message(f"{msg}")
        except Exception as e:
            msg = f"Failed to saved data to {filename}"
            log.info(msg)
            self.update_admin_message(f"Error: {msg}")

    def draw_groups_table(self):
            # Create the table widget
        header_names = ['ID', 'Group Name', 'Membership', 'Folder Name', 
                        'URL', 'Created Date', 'Modified Date']
        self.table_widget = QTableWidget(self)
            # Allows row selection
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.ContiguousSelection)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setColumnCount(7)
            # Display the header_names 
        self.table_widget.setHorizontalHeaderLabels(header_names)
        self.table_widget.verticalHeader().setVisible(False)
            # Set the stretch mode to stretch all sections to fit the view
        header = self.table_widget.horizontalHeader()
            # Allow manual resizing for all columns
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_widget.setColumnWidth(0, 30)
        self.table_widget.setColumnWidth(1, 180)
        self.table_widget.setColumnWidth(2, 80)
        self.table_widget.setColumnWidth(3, 180)
        self.table_widget.setColumnWidth(4, 225)
        self.table_widget.setColumnWidth(5, 80)
            # Fill the table widget with existing columns
        header.setStretchLastSection(True)
        self.membership_index = 2
            # Add data to table
        self.populate_qt_table()
            # Set up signal for double-click editing
        self.table_widget.itemDoubleClicked.connect(self.edit_group_double_clicked)
        # Prevent the table widget from entering edit mode
        self.page_layout.addWidget(self.table_widget, stretch=1)

    def populate_qt_table(self):
        try:
            records = self.groups_table.get_group_records()
            self.table_widget.setRowCount(len(records))
                # Populate the table with records
            for row_idx, record in enumerate(records):

                membership_text = "Yes" if record.membership else "No"
                id_str = str(record.id) if record.id is not None else ""

                self.table_widget.setItem(row_idx, 0, QTableWidgetItem(id_str))
                self.table_widget.setItem(row_idx, 1, QTableWidgetItem(record.group_name))
                self.table_widget.setItem(row_idx, 2, QTableWidgetItem(membership_text))                
                self.table_widget.setItem(row_idx, 3, QTableWidgetItem(record.folder_name))
                self.table_widget.setItem(row_idx, 4, QTableWidgetItem(record.url_str))
                self.table_widget.setItem(row_idx, 5, QTableWidgetItem(record.create_date.strftime('%Y-%m-%d %H:%M:%S')))
                self.table_widget.setItem(row_idx, 6, QTableWidgetItem(record.mod_date.strftime('%Y-%m-%d %H:%M:%S')))
            # self.layout.addWidget(self.table)
            return records 
        except Exception as e:
            self.update_database_label(f"Data fetch failed.")
            log.error(f"Group table fetch failed: {e}")

    def draw_admin_buttons(self):
        button_layout = QHBoxLayout()
        self.admin_message = ""
        self.add_btn = QPushButton(f"Add Group")
        self.add_btn.setMinimumHeight(30)
        self.edit_btn = QPushButton(f"Edit Group")
        self.edit_btn.setMinimumHeight(30)
        self.delete_btn = QPushButton(f"Delete Group")
        self.delete_btn.setMinimumHeight(30)
            # Connect default signals
        self.add_btn.clicked.connect(self.add_group)
        self.edit_btn.clicked.connect(self.on_edit_button_clicked)
        self.delete_btn.clicked.connect(self.delete_group)
            # Add to layout
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        self.page_layout.addLayout(button_layout)

    def add_group(self):
        try:
            dialog = AddGroupDialog(self)
            if dialog.exec() == QDialog.accepted:
                # data = dialog.get_data()
                # log.debug(f"{data = }")
                self.refresh_data()
                self.database_modified.emit()
        except Exception as e:
            message = "Add group failed to add data"
            log.debug(f"{message}: {e}")
            QMessageBox.critical(self, "Error", message)
            return
    
    def delete_group(self):
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select a row to delete.")
            return
        if len(selected_rows) > 1:
            QMessageBox.warning(self, "Warning", "Please select only one row to delete.")
            return
        selected_row = selected_rows[0].row()
        id_to_delete = self.table_widget.item(selected_row, 0).text()
        confirm = QMessageBox.question( self, "Confirm Delete",
            f"Are you sure you want to delete group with id '{id_to_delete}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        # log.debug(f"{confirm == QMessageBox.StandardButton.Yes = }")
        if confirm == QMessageBox.StandardButton.Yes:
            self.groups_table.delete_group_record(self.update_admin_message, id_to_delete)
            self.table_widget.removeRow(int(id_to_delete))
            QMessageBox.information(self, "Update", f"{self.admin_message}")
            self.database_modified.emit()
    
        self.refresh_data()

    def get_row_data(self, row_index=None):
        """Gets data for the specified row from the table."""
        # row_index = selected_items[0].row()
        if row_index is None:
            selected_items = self.table_widget.selectedItems()
            if not selected_items:
                return None

        row_data = {}
        for col in range(self.table_widget.columnCount()):
            header_text = self.table_widget.horizontalHeaderItem(col).text()
            column_key = header_text.lower().replace(" ", "_")
            item = self.table_widget.item(row_index, col)
            if item:
                if self.is_boolean_column(column_key):
                    row_data[column_key] = item.text().lower() == 'yes'
                else:
                    row_data[column_key] = item.text()
        return row_data

    def is_boolean_column(self, column_key:str) -> bool:
        """Helper function to check if a column is boolean."""
        boolean_columns:list = ["membership"] 
        return column_key in boolean_columns
    
    def edit_group_double_clicked(self, item):
        row = item.row()
        row_data = self.get_row_data(row)  # Get data for the current row
        log.debug(f"{row_data = }")
        self.edit_group_dialog(row_data)

        for column in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, column)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)        

    def on_edit_button_clicked(self):
        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a row to edit.")
            return

        row_index = selected_items[0].row()
        row_data = self.get_row_data(row_index)
        if row_data:
            self.edit_group_dialog(row_data)
            return
        else:
            QMessageBox.critical(self, "Error", "Could not retrieve data for the selected row.")

    def edit_group_dialog(self, initial_data):
        # log.debug(f"{initial_data = }")
        try:
            dialog = EditDialog(self, initial_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_data = dialog.get_data() 
                log.debug(f"{updated_data = }")
                # self.groups_table.update_group_record(updated_data)
                self.groups_table.update_group_record(updated_data, self.update_admin_message)
                QMessageBox.information(self, "Updated", f"{self.admin_message}")
                self.refresh_data()
                self.database_modified.emit()
        except Exception as e:
            self.db_connection_on = False
            message = "Edit Dialog failed to process data"
            log.debug(f"{message}: {e}")
            QMessageBox.critical(self, "Error", message)


class GroupRecordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.groups_table = self.parent.groups_table if parent else None
        self.record_dialog_layout = QVBoxLayout(self)    
        self.form_layout = QFormLayout()
        self.group_label = QLabel("Enter Goodreads Group name: ")
        self.group_name_input = QLineEdit()
        self.membership_box = QWidget()
        self.membership_layout = QHBoxLayout(self.membership_box)
        self.membership_input = QCheckBox("Required Group membership?")
        self.membership_input.setStyleSheet("font-weight: bold;")
        self.membership_layout.addWidget(self.membership_input)
        self.folder_label = QLabel("Enter folder name: ")
        self.folder_name_input = QLineEdit()
        self.url_label = QLabel("Enter bookshelf URL: ")
        self.url_input = QLineEdit()

        self.form_layout.addWidget(self.group_label)
        self.form_layout.addWidget(self.group_name_input)
        self.form_layout.addWidget(self.membership_box)
        self.form_layout.addWidget(self.folder_label)
        self.form_layout.addWidget(self.folder_name_input)
        self.form_layout.addWidget(self.url_label)
        self.form_layout.addWidget(self.url_input)

        self.record_dialog_layout.addLayout(self.form_layout)

        self.qbtns = (
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        # Add dialog buttons
        self.button_box = QDialogButtonBox(self.qbtns)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Add button_box to the base class layout
        self.record_dialog_layout.addWidget(self.button_box)

        # Set the base class layout as the dialog's layout
        self.setLayout(self.record_dialog_layout)

    def get_data(self):
        # log.debug(f"{self.membership_input.isChecked() = }")
        return {
            'group_name': self.group_name_input.text(),
            'membership': self.membership_input.isChecked(),
            'folder_name': self.folder_name_input.text(),
            'url_str': self.url_input.text()
        }


class AddGroupDialog(GroupRecordDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setGeometry(100, 100, 300, 300)
        self.setWindowTitle("Add Group")
        self.admin_message = "New action: Adding Group to table"
        # Default text
        self.group_name_input.setPlaceholderText("Group Name Here")
        self.folder_name_input.setPlaceholderText("group_name_here")
        self.url_input.setPlaceholderText("bookshelf/12345-group-name-here")
    
    def get_data(self):
        return super().get_data()
    
    def update_admin_message(self, message):
        self.admin_message = message
        
    def is_empty_list(self, val_list):
        val_list = [x if x is not None else '' for x in val_list]
        return all(x == '' for x in val_list)

    def accept(self):
        values = self.get_data() 
        log.debug(f"{values = }")      
        if self.is_empty_list(values.values()):
            self.update_admin_message("No data to add")
            QMessageBox.information(self, "Notification", f"{self.admin_message}")
        else:
            self.add_data(values)
        super().accept()

    def add_data(self, values):
        if self.groups_table.add_group_record(status_update=self.update_admin_message, data=values):
            QMessageBox.information(self, "Added", f"{self.admin_message}")
            self.parent.refresh_data(self.admin_message)
        else:
            QMessageBox.warning(self, "Add failed", f"{self.admin_message}")


class EditDialog(GroupRecordDialog):
    def __init__(self, parent, row_data):
        super().__init__(parent)
        # log.debug(f"{row_data = }")
        self.group_id = row_data['id']
        self.group_name = row_data['group_name']
        self.membership = row_data['membership']
        self.group_folder = row_data['folder_name']
        self.group_url = row_data['url']

        self.setWindowTitle(f"Edit {row_data['group_name']}")
        self.admin_message = "New action: Editing record"
        # Apply styles here
        style_string = "color: white"
        self.group_name_input.setStyleSheet(style_string)
        self.folder_name_input.setStyleSheet(style_string)
        self.url_input.setStyleSheet(style_string)
        # Set existing editable text
        self.group_name_input.setText(self.group_name)
        # log.debug(f"{self.membership = }")
        self.membership_input.setChecked(self.membership)
        self.folder_name_input.setText(self.group_folder)
        self.url_input.setText(self.group_url)
        
    def get_data(self):
        data = {'id': self.group_id}
        updated_data = super().get_data()
        # log.debug(f"EditDialog get_data(): {updated_data = }")
        data.update(updated_data)
        # FIXME: temporary fix: 
        # url_str is being misnamed in the data gathering
        # data['url_str'] = data.pop('url')
        # log.debug(f"{data = }")
        return data
    
    def update_admin_message(self, message):
        self.admin_message = message
   
    def accept(self):
        # self.update_record()
        super().accept()
        
    # def update_record(self):
    #     values = self.get_data()
    #     self.groups_table.update_group_record(status_update=self.update_admin_message, data=values)
    #     QMessageBox.information(self, "Updated", f"{self.admin_message}")
    #     self.parent.refresh_data(self.admin_message)
        