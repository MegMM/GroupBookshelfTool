# import sqlalchemy as sq
from group_bookshelf_tool import Config
config = Config()
log = config.set_logger(__package__, __name__)

import os
import json
import pickle
import time
from datetime import datetime
from sqlalchemy import text, inspect, update, select, or_, and_, sql, engine
from sqlalchemy.exc import NoResultFound, IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, validates
from group_bookshelf_tool.components.models import (
    Group, Book, Download, GroupBook, TagURL, 
    Base, engine, SessionLocal, metadata)


class DatabaseHelper:
    """ 
        Instantiated from main Tab Widgets 
        and passed to the db_admin functions when needed 
    """
    def __init__(self):
        pass

    def get_table_map(self):
        self.table_map = {
                'Group': Group,
                'Book': Book,
                'Download': Download,
                'GroupBook': GroupBook,
                'TagURL': TagURL,
            }
        
class BaseDB:
    def __init__(self, db_helper):
        self.db_helper = db_helper  
        self.initial_groups_file = config.initial_groups_file
        self.saved_groups_file = config.saved_groups_file
        self.database_file = config.database

    def get_db(self):
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def close_db(self, engine):
        db = SessionLocal()
        db.close()
        if engine:
            engine.dispose()
            engine = None
            log.debug("Database engine disposed from admin_functions.py")

    def list_all_tables (self):
        with SessionLocal() as db:
            # inspector = inspect()
            try:
                return inspect.get_table_names()
            except:
                return []

    def verify_table(self, table_class=None, table_name=None):
        if table_class:
            return table_class
        elif table_name is not None and not table_name in table_map.keys():
            log.error(f"Invalid table name: {table_name}. Must be {list(table_map.keys())}")
            return None
        else:
            db_helper = DatabaseHelper()
            db_helper.get_table_map()
            return db_helper.table_map[table_name]       

    def fetch_records(self, table_class=None, table_name=None):
        table_class = self.verify_table(table_class, table_name)
        if not table_class:
            return None

        with SessionLocal() as session:
            try:
                records = session.query(table_class).all()
                return records
            except Exception as e:
                log.error(f"Error fetching record: {e}")
                return None

    def fetch_record(self, table_class=None, table_name=None, id=None, group_name=None, folder_name=None):
        table_class = self.verify_table(table_class, table_name)
        if not table_class:
            return None # Get the class from the map

        with SessionLocal() as session:
            try:
                if id:
                    record = session.query(table_class).filter(table_class.id == id).first()
                    return record
                elif group_name and folder_name:
                    record = session.query(table_class).filter_by(
                        group_name=group_name, folder_name=folder_name
                    ).first()
                    return record
                else:
                    return None
            except Exception as e:
                log.error(f"Error fetching record: {e}")
                return None

    @validates('group_id')
    def update_folder_name(self, key, group_id):
        if group_id:
            # Get the group and update folder_name
            group = object_session(self).query(Group).get(group_id)
            if group:
                self.folder_name = group.folder_name
        return group_id

class GroupsTable(BaseDB):
    def __init__(self):
        db_helper = DatabaseHelper()
        super().__init__(db_helper)

    def init_table(self, status_update):
        log.debug(f"{self.database_file = }")
        if os.path.exists(self.database_file):
            try:
                self.close_db(engine)
                os.remove(self.database_file)
                status_update(f"Database file deleted: {self.database_file}")
            except Exception as e:
                message = f"Failed to remove existing database, {os.path.relpath(self.database_file)}: \n{e}"
                log.error(message)
                status_update(message)
                return
        time.sleep(5) 
        try:
            self.create_groups_table()
            log.debug(f"{self.initial_groups_file = }")
            with open(self.initial_groups_file, 'r') as f:
                table_data = json.load(f)
                status_update(f"Loaded data from {self.initial_groups_file}")
                
        except Exception as e:
            status_update(f"No data file found: {self.initial_groups_file}")
            log.error(f"No data file found: {e}")
            return
        try:    
            with SessionLocal() as db:
                for shelf in table_data:
                    log.debug(f"{shelf = }")
                    if 'membership' in shelf.keys():
                        self.add_group_record(
                            group_name=shelf['group_name'],
                            membership=shelf['membership'],
                            folder_name=shelf['folder_name'],
                            url_str=shelf['url_str'],
                            status_update=None
                            )
                    else:
                        self.add_group_record(
                            group_name=shelf['group_name'],
                            folder_name=shelf['folder_name'],
                            url_str=shelf['url_str'],
                            status_update=None
                            )
            status_update(f"Data loaded")
        except Exception as e:
            status_update(f"No data files loaded")
            log.error(f"No data files loaded: {e}")

    def load_data(self, status_update=None):
        """ status_update is a callback function that sends a str """
        log.debug(f"{os.path.exists(self.initial_groups_file) = }")
        log.debug(f"{os.path.exists(self.saved_groups_file) = }")
        try:
            if os.path.exists(self.saved_groups_file):
                with open(self.saved_groups_file, 'r') as f:
                    table_data = json.load(f)
                    status_update(f"Loaded data from {self.saved_groups_file}")
            elif os.path.exists(self.initial_groups_file):
                with open(self.initial_groups_file, 'r') as f:
                    table_data = json.load(f)
                    status_update(f"Loaded data from {self.initial_groups_file}")
                    
        except json.JSONDecodeError as e:
            log.error(f"Error parsing JSON: {e}")
        except FileNotFoundError:
            log.error(f"File not found")
        except Exception as e:
            log.error(f"An error occurred: {e}")

        try:
            # log.debug(f"{table_data = }")
            with SessionLocal() as db:
                for shelf in table_data:
                    log.debug(f"{shelf = }")
                    self.add_group_record(
                        group_name=shelf['group_name'],
                        membership=shelf['membership'],
                        folder_name=shelf['folder_name'],
                        url_str=shelf['url_str'],
                        status_update=status_update
                        )
            status_update(f"Data loaded")
        except Exception as e:
            status_update(f"No data loaded")
            log.error(f"No data files loaded: {e}")

        except (SQLAlchemyError, IOError, TypeError) as e:
            log.error(f"Error saving data to JSON: {e}")
            status_update(f"Error saving data to JSON: {e}")

    def drop_groups_table(self):
        # !WARNING: DON'T use this Relational Database chaos!
        with SessionLocal() as db:
            # This will properly handle foreign key relationships
            Base.metadata.drop_all(bind=engine, tables=[Group.__table__])

    def get_group_records(self):
        return self.fetch_records(table_class=Group)

    def list_group_names(self):
        with SessionLocal() as db:
            # log.debug(f"{[shelf.group_name for shelf in db.query(Group).all()] = }")
            return [shelf.group_name for shelf in db.query(Group).all()]

    def list_group_ids_and_names(self):
        with SessionLocal() as db:
            return [(shelf.id, shelf.group_name) for shelf in db.query(Group).all()]

    def list_folder_names(self):
        with SessionLocal() as db:
            return [shelf.folder_name for shelf in db.query(Group).all()]

    def get_group_record(self, group_id=None, group_name=None, folder_name=None):
        """ 
            Function can use the id to retrieve the record. 
            Or it can use group_name and/or folder_name to retrieve the record.
        """
        if all(x is None for x in [group_id, group_name, folder_name]):
            log.error(f"No values provided for get_group_record")
            return None
        with SessionLocal() as db:
            try:
                if group_id:
                    group = db.query(Group).filter(Group.id == group_id).first()
                    if group:
                        return [group]
                if group_name and folder_name:
                    groups = db.query(Group).filter(
                        and_(Group.group_name == group_name, 
                            Group.folder_name == folder_name)).all()
                else:
                    groups = db.query(Group).filter(
                        or_(Group.group_name == group_name, 
                            Group.folder_name == folder_name)).all()
                return groups
            except SQLAlchemyError as e:
                log.error(f"Error fetching groups: {e}")
                return None
            
    def multiple_groups_error(self, groups, group_id=None, group_name=None, folder_name=None):
        log.error(f"""Options returned multipls groups: 
    {group_id = }, {group_name = }, {folder_name = }
    {groups}""")
        return None

    def get_group_id_by_name(self, group_name=None, folder_name=None):
        """ 
            Function can use one or both of the options to retrieve the id: 
            group_name, folder_name 
        """
        if group_name is None and folder_name is None:
            log.error(f"No values provided for get_group_id_by_name")
            return None
        try:
            groups = self.get_group_record(group_name=group_name, folder_name=folder_name)
            if groups:
                if len(groups) > 1:
                    return self.multiple_groups_error(groups, 
                                                      group_name=group_name, 
                                                      folder_name=folder_name)
                return groups[0].id 
        except SQLAlchemyError as e:
            log.error(f"Error fetching group id with 'group_name' or 'folder_name': {e}")
            return None

    def get_folder_name(self, group_id=None, group_name=None):
        """ 
            Function can use one or both of the options to retrieve the folder_name: 
            group_id, group_name 
        """
        if group_id is None and group_name is None:
            log.error(f"No values provided for get_folder_name")
            return None
        try:
            groups = self.get_group_record(group_id=group_id, group_name=group_name)
            if groups:
                if len(groups) > 1:
                    return self.multiple_groups_error(groups, 
                                                      group_id=group_id, 
                                                      group_name=group_name)
                return groups[0].folder_name       
        except SQLAlchemyError as e:
            log.error(f"Error fetching group folder name with 'group_id' or 'group_name': {e}")
            return None
                
    def get_shelf_url(self, group_id=None, group_name=None, folder_name=None):
        """ 
            Function can use one or more of the options to retrieve the URL: 
            group_id, group_name, folder_name 
        """
        if all(x is None for x in [group_id, group_name, folder_name]):
            log.error(f"No values provided for get_shelf_url")
            return None
        try:
            groups = self.get_group_record(group_id=group_id, group_name=group_name, folder_name=folder_name)
            if groups:
                if len(groups) > 1:
                    return self.multiple_groups_error(groups, 
                                                      group_id=group_id, 
                                                      group_name=group_name, 
                                                      folder_name=folder_name)
                return groups[0].url_str       

        except SQLAlchemyError as e:
            log.error(f"Error fetching group URL with 'group_id', 'group_name', 'folder_name': {e}")
            return None

    def check_url_value(self, url_str):
        return not config.base_url in url_str and 'bookshelf' in url_str \
            and 'group' not in url_str

    def list_shelf_urls(self):
        folders = self.list_folder_names()
        for f in folders:
            log.info(f"URL for {f} is {self.get_group_url(f)}")
    
    def add_group_record(self, data=None, status_update=None, **kwargs):
    # def add_group_record(self, data=None, status_update=None, **kwargs):
        """ Model attributes: group_name, folder_name, url_str """
        values = data if data is not None else kwargs
        log.debug(f"{type(values)}, {values}")
        # log.debug(f"{data = }")
        group_name = values.get('group_name')
        folder_name = values.get('folder_name')
        url_str = values.get('url_str')
        membership = values.get('membership')

        if data is None and not values:
            status_update(f"Database Error: No values provided to add_group_record()")
            return False
        if not group_name:
            msg = "Data missing: requires a minimum of 'group_name' to add_group_record()"
            status_update(f"Database Error: {msg}")
            log.error(msg)
            return False
        
        # membership = self.make_membership_bool(membership)
        log.debug(f"add_group_record: {membership = }")
        
        if not self.check_url_value(url_str):
            status_update(f"""URL not in the correct format:
'bookshelf/99999-group-name""")
            return False
        
        try:
            # log.debug(f"{group_name = }, {folder_name = }, {url_str = }")
            with SessionLocal() as db:
                # log.debug(f"{folder_name = }")
                existing_group = db.query(Group).filter_by(folder_name=folder_name).first()
                if not existing_group:
                    new_group = Group(
                        group_name=group_name, 
                        membership = membership,
                        folder_name=folder_name, 
                        url_str=url_str 
                        )
                    db.add(new_group)
                    # log.debug(f"{group_name} added")
                    db.commit()
                    # log.info(f"Added group '{group_name}' with folder_name '{folder_name}'")
                    status_update(f"Success! {group_name} added")
                    return True
                else:
                    msg = f"Group '{group_name}' with folder_name '{folder_name}' already exists"
                    log.warning(msg)
                    status_update(f"Database Warning: {msg}")
                    db.rollback()
                    return False
                
        except IntegrityError as e:
            log.error(f"Integrity error while adding group: {str(e)}")
            # db.rollback()
            return False
        
        except Exception as e:
            log.error(f"Error adding group: {str(e)}")
            # db.rollback()
            return False

    def update_group_record(self, data=None, status_update=None, **kwargs):
        log.debug(f"\n\nupdate_group_record()...")
        values = data if data is not None else kwargs
        if data is None and not values:
            status_update(f"Database Error: No values provided")
            return
        
        group_id = values.get('id')
        group_name = values.get('group_name')
        membership = values.get('membership')
        folder_name = values.get('folder_name')
        url_str = values.get('url_str')
        log.debug(f"{group_id = }, {group_name = }")

        with SessionLocal() as db:
            existing_group = db.query(Group).filter_by(id=group_id).first()
            log.debug(f"update_group_record: {existing_group.group_name = }")
            if not existing_group:
                message = f"No record found with id: {group_id}"
                log.error(message)
                status_update(f"Database Error: {message}")
                db.rollback()
            else:
                update_fields = {}
                if group_name is not None and group_name != existing_group.group_name:
                    update_fields['group_name'] = group_name
                if membership is not None and membership != existing_group.membership:
                    update_fields['membership'] = membership
                if folder_name is not None and folder_name != existing_group.folder_name:
                    update_fields['folder_name'] = folder_name
                if url_str is not None and url_str != existing_group.url_str:
                    update_fields['url_str'] = url_str

                if update_fields:
                    try:
                        stmt = update(Group).where(Group.id == group_id).values(update_fields)
                        db.execute(stmt)
                        db.commit()
                        status_update(f"Record for group '{existing_group.group_name}' updated successfully.")
                    except Exception as e:
                        db.rollback()
                        status_update(f"Error updating record: {e}")
                        log.error(f"Error updating record: {e}")
                else:
                    status_update("No changes to apply.")

    def delete_group_record(self, status_update=None, id_to_delete=None):
        if id_to_delete is None:
            log.error(f"Error: Failed to delete. No id provided ")
            status_update(f"Failed to delete. No id provided.")   
        try:
            group_to_delete = self.fetch_record(table_class=Group, id=id_to_delete)
            with SessionLocal() as db:
                db.delete(group_to_delete)
                db.commit()
                msg = f"Group with id {id_to_delete} deleted successfully"
                log.info(msg)
                status_update(msg)
        except Exception as e:
            msg = f"Error: Failed to delete {id_to_delete}"
            log.error(msg)
            status_update(msg)

    def create_groups_table(self):
        with SessionLocal() as db:
            Base.metadata.create_all(bind=engine)


class DownloadHistoryTable(BaseDB):
    def __init__(self):
        """
            group_id = Column(Integer, ForeignKey('groups.id'))
            group_name = Column(String)
            folder_name = Column(String) 
            download_dir = Column(String) 
            sort_order = Column(String) 
            books_per_page = Column(Integer) 
            group = relationship('Group', back_populates='downloads')
            download_date = Column(DateTime, default=datetime.utcnow) 
        """
        db_helper = DatabaseHelper()
        super().__init__(db_helper)

    def create_downloads_table(self):
        with SessionLocal() as db:
            Base.metadata.create_all(bind=engine)

    def get_downloads_records(self):
        return self.fetch_records(table_class=Download) 

    def add_download_session(self, group_id, group_name, folder_name, download_dir, 
                             sort_order, books_per_page, status_update=None):
        with SessionLocal() as session:
            log.debug(f"{group_id = }")
            log.debug(f"{group_name = }")
            log.debug(f"{folder_name = }")
            log.debug(f"{download_dir = }")
            log.debug(f"{sort_order = }")
            log.debug(f"{books_per_page = }")
            try:
                new_download = Download(
                    group_id=group_id,
                    group_name=group_name,
                    folder_name=folder_name,
                    download_dir=download_dir,
                    sort_order=sort_order,
                    books_per_page=books_per_page
                )
                session.add(new_download)
                session.commit()
                msg=f"Download information saved for group '{group_name}'."
                status_update(f"Database update: {msg}")
                log.info(msg)
        
            except Exception as e:
                session.rollback()
                msg = f"Failed to save download information: {e}"
                log.error(f"Error saving download information: {msg}")
                status_update(f"Database Error: {msg}")

  

class BooksTable(BaseDB):
    def __init__(self):
        db_helper = DatabaseHelper()
        super().__init__(db_helper)

    def fetch_books(self):
        with SessionLocal() as db:
            records = db.query(Book).all()
        # return fetch_table_data('groups')
        return records


