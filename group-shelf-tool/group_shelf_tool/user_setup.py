import os
import sys
from pathlib import Path
import configparser
import getpass


def setup_config():
    config = configparser.ConfigParser()

    # Create sections
    config.add_section('PATH')
    config.add_section('SITE')
    config.add_section('OUTPUT')
    config.add_section('ASSETS')

    # Set default values for 'PATH', 'OUTPUT', 'ASSETS' sections
    config.set('PATH', 'default_path', '/default/path')
    config.set('OUTPUT', 'default_output', '/default/output')
    config.set('ASSETS', 'default_assets', '/default/assets')

    # Get user input for 'SITE' section
    url = input("Enter the site URL: ")
    email = input("Enter your email: ")
    password = getpass.getpass("Enter your password: ")

    # Set values for 'SITE' section
    config.set('SITE', 'url', url)
    config.set('SITE', 'email', email)
    config.set('SITE', 'password', password)

    # Write the configuration to a file
    with open('config.ini', 'w') as config_file:
        config.write(config_file)

    print("Config file created successfully.")

if __name__ == "__main__":

    print("""
This script sets up your user config file for the Goodreads Group Bookshelf Tool. 
The application directory will contain a 'config.ini' file, a JSON file, 
and a small SQLite3 database, the application code and a 'BookShelfData'
directory for Downloads and Processed files.
    """)    
    setup_config()


