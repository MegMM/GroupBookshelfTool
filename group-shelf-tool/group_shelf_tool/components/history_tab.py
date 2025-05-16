from group_bookshelf_tool import Config
config = Config()
log = config.set_logger(__package__, __name__)

# from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QFormLayout, QWidget, QLabel, QDialog, QDialogButtonBox,
    QHeaderView, QTableWidget, QTableWidgetItem, QAbstractItemView, 
)        
import group_bookshelf_tool.components.db_admin as db


class DownloadHistoriesTab(QWidget):
    """
    This is the Downloads History Widget
    """
    def __init__(self, parent, table):
        super().__init__(parent)
        self.parent = parent      
        self.export_tab= parent.export_tab# set up synch with the DownloadTab
        self.export_tab.download_update.connect(self.populate_qt_table)

        self.history_table = db.DownloadHistoryTable()
        self.setGeometry(100, 100, 900, 700)
        self.setContentsMargins(5, 20, 20, 0)
        self.setObjectName("download_tab")
        self.page_layout = QVBoxLayout(self)
        self.directions_label = QLabel(self)
        self.directions_label.setText("Double-click on rows for full information")
        self.page_layout.addWidget(self.directions_label)

        self.header_map = {
            'id': 'id',
            'group_id': 'Group Id',
            'group_name': 'Group Name',
            'download_date': 'Download Date',        
            }
        # self.header_names = ['id', 'Group Id', 'Group Name', 'Download Date']
        self.draw_history_table()

    def draw_history_table(self):
        self.table_widget = QTableWidget(self)
            # Allows row selection
        self.table_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.ContiguousSelection)
        self.table_widget.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setColumnCount(4)
            # Display the self.header_names 
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setHorizontalHeaderLabels(self.header_map.values())
        self.table_widget.verticalHeader().setVisible(False)
        header = self.table_widget.horizontalHeader()
            # Allow manual resizing for all columns
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_widget.setColumnWidth(0, 25)
        self.table_widget.setColumnWidth(1, 85)
        self.table_widget.setColumnWidth(2, 220)
        self.table_widget.setColumnWidth(3, 220)
        header.setStretchLastSection(True)
        self.populate_qt_table()
            # Set up signal for double-click editing
        self.table_widget.itemDoubleClicked.connect(self.view_record_double_clicked)
        self.page_layout.addWidget(self.table_widget, stretch=1)

    def populate_qt_table(self):
        try:
            self.current_records = self.history_table.get_downloads_records()
            
                # Check if records were fetched
            if not self.current_records:
                log.warning("No download records found to populate the table.")
                self.table_widget.setRowCount(0)
                return # Exit if no records
            
            self.table_widget.setRowCount(len(self.current_records))
                # Populate the table with records
            for ix, record in enumerate(self.current_records):
                id_str = str(record.id) if record.id is not None else ""
                group_id_str = str(record.group_id) if record.group_id is not None else ""
                group_name_str = str(record.group_name) if record.group_name is not None else ""
                date_str = record.download_date.strftime('%Y-%m-%d %H:%M:%S') \
                    if hasattr(record, 'download_date') and record.download_date else "" # Check attribute exists

                self.table_widget.setItem(ix, 0, QTableWidgetItem(id_str))
                self.table_widget.setItem(ix, 1, QTableWidgetItem(group_id_str))
                self.table_widget.setItem(ix, 2, QTableWidgetItem(group_name_str))
                self.table_widget.setItem(ix, 3, QTableWidgetItem(date_str))
        except Exception as e:
            log.error(f"Download table fetch failed: {e}")

    def view_record_double_clicked(self, item):
        if item is None:
            return
        row = item.row()
        log.debug(f"Row {row} double-clicked.")

        if hasattr(self, 'current_records') and 0 <= row < len(self.current_records):
            record = self.current_records[row]
            # Now, convert this record into the dictionary format
            # that your DownloadRecord dialog expects (matching self.display_data keys).
            # This assumes your record has attributes like record.id, etc.
            data_for_dialog = {
                'id': getattr(record, 'id', None),
                'group_id': getattr(record, 'group_id', None),
                'group_name': getattr(record, 'group_name', None),
                'folder_name': getattr(record, 'folder_name', None),
                'download_dir': getattr(record, 'download_dir', None),
                'sort_order': getattr(record, 'sort_order', None),
                'books_per_page': getattr(record, 'books_per_page', None),
                'download_date': getattr(record, 'download_date', None) # map create_date to 'download_date' key
            }
            log.debug(f"Data for dialog: {data_for_dialog}")
        # --- Fallback to your get_row_data if you prefer (but less ideal) ---
        # else:
        #     log.warning(f"current_records not available or row {row} out of bounds. Falling back to get_row_data.")
        #     data_for_dialog = self.get_row_data(row) # Get data for the current row

            if not data_for_dialog:
                log.error(f"Could not retrieve data for row {row}.")
                return

            try:
                # Pass data_for_dialog first, then self as parent
                dialog = DownloadRecord(data_for_dialog, self)
                if dialog.exec() == QDialog.DialogCode.Accepted: # Or QDialog.Accepted
                    log.debug("Download record dialog was accepted.")
                    # You might want to refresh the table or do other actions here
                else:
                    log.debug("Download record dialog was cancelled/closed.")
            except Exception as e: # Catch specific exceptions if possible
                log.exception("Error launching or executing DownloadRecord dialog.") # log.exception is great
        else:
            log.warning(f"Could not get data for row {row} from self.current_records.")

    def get_row_data(self, row_index): # Kept for reference, but using original data is better
        """Gets data for the specified row by reading from the QTableWidget cells."""
        if row_index < 0 or row_index >= self.table_widget.rowCount():
            log.warning(f"get_row_data: row_index {row_index} is out of bounds.")
            return None

        row_data = {}
        # Ensure column headers match what DownloadRecord expects as keys
        # This must align with DownloadRecord.display_data keys
        # header_to_key_map = {
        #     'id': 'id',
        #     'Group Id': 'group_id',
        #     'Group Name': 'group_name',
        #     'Download Date': 'download_date'
        # }
        header_to_key_map = {v: k for k, v in self.header_map.items()}
        for col_idx in range(self.table_widget.columnCount()):
            header_item = self.table_widget.horizontalHeaderItem(col_idx)
            if not header_item:
                continue
            header_text = header_item.text()
            column_key = header_to_key_map.get(header_text) # Use defined mapping

            if not column_key: # If header not in map, try to generate a key (less robust)
                column_key = header_text.lower().replace(" ", "_")

            item = self.table_widget.item(row_index, col_idx)
            if item and item.text() is not None:
                row_data[column_key] = item.text()
            else:
                row_data[column_key] = None # Or ""
        log.debug(f"Data from get_row_data for row {row_index}: {row_data}")
        return row_data
    

class DownloadRecord(QDialog):
    def __init__(self, record_data, parent=None): # <-- Modified: Accept record_data
        super().__init__(parent)
        self.parent = parent
        self.record_data = record_data  # <-- Store the passed data

        self.setWindowTitle("Download Record Details") # Good to have a title
        self.record_dialog_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        # Define the fields to display: (key, display_text)
        self.display_data = [
            ('id', 'Record ID'), # Assuming 'id' might be a key from get_row_data
            ('group_id', 'Group ID'),
            ('group_name', 'Group Name'),
            ('folder_name', 'Folder Name'),
            ('download_dir', 'Download Directory'),
            ('sort_order', 'Sort Order'),
            ('books_per_page', 'Books Per Page'),
            ('download_date', 'Download Date') # Key from get_row_data using header
        ]

        self._create_form_fields() # Helper to create labels

        self.record_dialog_layout.addLayout(self.form_layout) # <-- Add form_layout to main layout

        self._populate_form_fields() # Helper to fill data into labels

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.accept)
        self.process_button = self.button_box.addButton(
            "Custom Action", QDialogButtonBox.ButtonRole.ActionRole
        )
        self.process_button.clicked.connect(self.perform_custom_action)
        self.record_dialog_layout.addWidget(self.button_box)

        self.setLayout(self.record_dialog_layout)
        self.setMinimumWidth(400) # Optional: set a decent minimum size

    def perform_custom_action(self):
        log.debug(f"Custom action")

    def _create_form_fields(self):
        """Creates the static labels and data placeholder labels."""

        for key, display_text in self.display_data:
            static_label = QLabel(f"{display_text}: ")
            data_label = QLabel("")  # Placeholder, will be filled
            # Store the data_label using a consistent naming convention (e.g., self.group_name_data_label)
            setattr(self, f"{key}_data_label", data_label)
            self.form_layout.addRow(static_label, data_label)

    def _populate_form_fields(self):
        """Populates the data labels with values from self.record_data."""
        for key, _ in self.display_data:
            try:
                data_label_widget = getattr(self, f"{key}_data_label")
                value = self.record_data.get(key, "N/A") # Get value from the passed record_data
                data_label_widget.setText(str(value))
            except AttributeError:
                log.warning(f"Dialog attribute '{key}_data_label' not found for populating.")
            except Exception as e:
                log.error(f"Error populating dialog field for '{key}': {e}")

    def accept(self):
        log.debug("DownloadRecord dialog accepted.")
        super().accept()



# class DownloadRecord(QDialog):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.parent = parent
#         self.record_dialog_layout = QVBoxLayout(self)    
#         self.form_layout = QFormLayout()
#         fields_to_populate = {
#             'group_name': 'Group Name', # attribute_key : display_text (not strictly needed here if set_line_item defines them)
#             'group_id': 'Group ID',
#             'folder_name': 'Folder Name',
#             'download_dir': 'Download Directory',
#             'sort_order': 'Sort Order',
#             'books_per_page': 'Books Per Page',
#             'download_date': 'Download Date' # Key from get_row_data
#         }
        
#         for key in fields_to_populate:
#             try:
#                 data_label_widget = getattr(self, f"{key}_data_label")
#                 value = self.record_data.get(key, "N/A") # Get value from the passed record_data
#                 data_label_widget.setText(str(value))
#             except AttributeError:
#                 log.warning(f"Dialog does not have a data label for key: {key}_data_label")
#             except Exception as e:
#                 log.error(f"Error populating dialog field for {key}: {e}")

#         # self.set_line_item('group_name', 'Group name')
#         # self.set_line_item('group_id', 'Groupd id')
#         # self.set_line_item('folder_name', 'Folder name')
#         # self.set_line_item('download_dir', 'Download directory')
#         # self.set_line_item('sort_order', 'Sort order')
#         # self.set_line_item('books_per_page', 'Books per page')
#         # self.set_line_item('download_date', 'Download date')

#         self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
#         self.button_box.accepted.connect(self.accept)
#         # Add button_box to the base class layout
#         self.record_dialog_layout.addWidget(self.button_box)
#         self.setLayout(self.record_dialog_layout)

#     def set_line_item(self, obj_name, item_text):
#         line_widget = QWidget()
#         line_layout = QHBoxLayout()
#         obj_name_label = f"{obj_name}_label"
#         setattr(self, obj_name_label, QLabel(f"{item_text}: "))
#         obj_name_text = f"{obj_name}_text"
#         setattr(self, obj_name_text, QLabel(""))
#         line_layout.addWidget(obj_name_label)
#         line_layout.addWidget(obj_name_text)
#         self.form_layout.addWidget(line_widget)

#     def accept(self):
#         super().accept()
#     #     self.group_name_label = QLabel("Group name:")
#     #     self.group_name_text = QLabel("")
#     #     self.folder_name_label = QLabel("Folder name:  ")
#     #     self.folder_name_text = QLabel("")
#     #     self.url_label = QLabel("Enter bookshelf URL: ")
#     #     self.url_input = QLineEdit()

#     #     self.form_layout.addWidget(self.group_label)
#     #     self.form_layout.addWidget(self.group_name_input)
#     #     self.form_layout.addWidget(self.membership_box)
#     #     self.form_layout.addWidget(self.folder_label)
#     #     self.form_layout.addWidget(self.folder_name_input)
#     #     self.form_layout.addWidget(self.url_label)
#     #     self.form_layout.addWidget(self.url_input)

#     #     self.record_dialog_layout.addLayout(self.form_layout)

#     #     self.qbtns = (
#     #         QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
#     #     )
#     #     # Add dialog buttons
#     #     self.button_box = QDialogButtonBox(self.qbtns)
#     #     self.button_box.accepted.connect(self.accept)
#     #     self.button_box.rejected.connect(self.reject)

#     #     # Add button_box to the base class layout
#     #     self.record_dialog_layout.addWidget(self.button_box)

#     #     # Set the base class layout as the dialog's layout
#     #     self.setLayout(self.record_dialog_layout)


