from group_bookshelf_tool import Config
config = Config()
log = config.set_logger(__package__, __name__)
#log.debug(f"config {__package__}.{__name__}")

from datetime import datetime
from pathlib import Path
# import sqlite3
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, relationship, backref, declarative_base, validates
import sqlalchemy.engine.url as url
from sqlalchemy.types import Integer
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, ForeignKey, Table, TypeDecorator
# MODELS: Group, Book, Download, GroupBook, TagURL
db_path = config.database

url = f'sqlite:///{db_path}'
engine = create_engine(url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
metadata = MetaData()
metadata.reflect(bind=engine)

record_group_book_association = Table(
    'record_group_book_association', 
    Base.metadata, 
    Column('group_id', Integer, ForeignKey('groups.id')), 
    Column('book_id', Integer, ForeignKey('books.id'))
)

record_tag_url_association = Table(
    'record_tag_url_association', 
    Base.metadata, 
    Column('id', Integer, ForeignKey('books.id')), 
    Column('tag_url_id', Integer, ForeignKey('tag_urls.id'))
    )

class BooleanInteger(TypeDecorator):
    """ Custom data type for 'membership' column """
    impl = String

    def process_bind_param(self, value, dialect):
        if value is None:
            return 'False'
        if isinstance(value, bool):
            return 'True' if value else 'False'
        if isinstance(value, int):
            if value not in [0, 1]:
                raise ValueError("Invalid integer value. Must be 0 or 1.")
            return 'True' if value == 1 else 'False'
        if isinstance(value, str):
            if value not in ['0', '1', 'True', 'False']:
                raise ValueError("Invalid string value. Must be '0', '1', 'True', or 'False'.")
            return 'True' if value in ['1', 'True'] else 'False'
        raise ValueError("Invalid value type. Must be bool, int, or str.")

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.lower() == 'true'


class Group(Base):
    __tablename__ = "groups"   
    id = Column(Integer, primary_key=True)
    group_name = Column(Text)    
    # membership = Column(Boolean, default=False)
    membership = Column(BooleanInteger)
    folder_name = Column(String)
    url_str = Column(Text)
    downloads = relationship('Download')
    book_list = relationship( 
        'Book', 
        secondary=record_group_book_association, 
        primaryjoin="Group.id == record_group_book_association.c.group_id", 
        secondaryjoin="Book.id == record_group_book_association.c.book_id", 
        backref=backref('groups', lazy='dynamic'), 
        viewonly=True
        )
    create_date = Column(DateTime, default=datetime.utcnow) 
    mod_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"Group(id={self.id}, group_name='{self.group_name}', membership={self.membership}, folder_name='{self.folder_name}', url_str='{self.url_str}', create_date={self.create_date}, mod_date={self.mod_date})"


class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    title = Column(Text)
    title_url = Column(Text)
    author = Column(Text)    
    author_url = Column(Text)
    tag_urls_list = relationship(
        'TagURL', 
        secondary=record_tag_url_association, 
        backref=backref('tag_urls', lazy='dynamic'),
        # overlaps="books_list"
        )    
    date_started = Column(Date)
    date_finished = Column(Date)
    added_by_name = Column(String) 
    added_by_url = Column(Text) 
    date_added = Column(Date)
    activity_link = Column(String)
    create_date = Column(DateTime, default=datetime.utcnow) 
    mod_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    group_shelves = relationship( 
        'Group', 
        secondary=record_group_book_association, 
        primaryjoin="Book.id == record_group_book_association.c.book_id", 
        secondaryjoin="Group.id == record_group_book_association.c.group_id", 
        backref=backref(
            'books', lazy='dynamic'),
            viewonly=True        
        )
    
    def __repr__(self):
        return f"Book(id={self.id}, title='{self.title}', title_url={self.title_url}, author='{self.author}', author_url='{self.author_url}', create_date={self.create_date}, mod_date={self.mod_date})"


class Download(Base):
    __tablename__ = "downloads" 
    id = Column(Integer, primary_key=True) 
    group_id = Column(Integer, ForeignKey('groups.id'))
    group_name = Column(Text)
    folder_name = Column(String) 
    download_dir = Column(Text) 
    sort_order = Column(String) 
    books_per_page = Column(Integer) 
    download_date = Column(DateTime, default=datetime.utcnow) 
    group = relationship('Group', back_populates='downloads')
    # group_shelf = relationship('Group', back_populates='downloads')

    # @validates('group_id')
    # def update_folder_name(self, key, group_id):
    #     if group_id:
    #         # Get the group and update folder_name
    #         group = object_session(self).query(Group).get(group_id)
    #         if group:
    #             self.folder_name = group.folder_name
    #     return group_id


class GroupBook(Base): 
    # Define the Group-to-Book model
    __tablename__ = 'group_books' 
    id = Column(Integer, primary_key=True, autoincrement=True) 
    group = Column(String, nullable=False) 
    # books = relationship('Book', secondary=record_group_book_association, backref='groups')
    # Change the backref name in the GroupBook model
    group_book_list = relationship( 
        'Book', 
        secondary=record_group_book_association, 
        primaryjoin="GroupBook.id == record_group_book_association.c.group_id", 
        secondaryjoin="Book.id == record_group_book_association.c.book_id", 
        backref=backref('group_books', lazy='dynamic')
    )


class TagURL(Base): 
    # Define the Tag-tag_url-Book model 
    __tablename__ = 'tag_urls' 
    id = Column(Integer, primary_key=True, autoincrement=True) 
    tag = Column(String, nullable=False) 
    tag_url = Column(Text, nullable=False) 
    tagged_books = relationship(
        'Book', 
        secondary=record_tag_url_association, 
        backref=backref(
            'tag_urls', lazy='dynamic'),
            viewonly=True
        )


Base.metadata.create_all(bind=engine)


