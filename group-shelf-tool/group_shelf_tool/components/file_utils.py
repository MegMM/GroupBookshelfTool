from group_bookshelf_tool import Config
config = Config()
log = config.set_logger(__package__, __name__)

from datetime import datetime
from pathlib import Path
import os
import zipfile

class DirectoryUtils:
    def __init__(self):
        pass

    def make_new_dir(self, path):
        """
        Desc: Make a new directory, add parents if needed.
        """
        # log.debug(f"Making directory for {path}")
        try:
            path.mkdir(parents=True)
        except FileExistsError as exception:
            log.error(f"make_new_dir(): {path} directory already exists.")

    def move_directory(self, current, destination):
        """
        Desc: Move files to new archive destination
        """
        if not current.is_dir():
            self.dir_exists(destination)
        else:
            current.rename(destination)

    def is_empty(self, path:str|Path):
        """
        Desc: Validation check that path is empty
        """
        return not any(Path(path).iterdir())
    
    def remove_empty_dir(self, path:str|Path):
        if self.is_empty(path):
            os.rmdir(str(path))
            msg = f"Directory {path} is empty and has been removed."
            log.debug(msg)
            return msg
        else:
            return False

    def delete_empty_subdirectories(self, directory):
        for child in directory.iterdir():
            if child.is_dir():
                if not list(child.iterdir()):
                    child.rmdir()
                else:
                    self.delete_empty_subdirectories(child)


class DateFormatter:
    def __init__(self, date_obj=None):
        self.date_obj = date_obj or datetime.now()

    def get_year(self):
        return str(self.date_obj.year)

    def get_month_day(self):
        return self.date_obj.strftime("%b%d")

    def get_timestamp(self):
        return self.date_obj.strftime("%H%M")

    def get_date_time_string(self):
        return f"{self.get_month_day()}_{self.get_timestamp()}"


class PathBuilder(DirectoryUtils, DateFormatter):
    def __init__(self, base_dir):
        DirectoryUtils.__init__(self) # no () after class
        DateFormatter.__init__(self)
        self.base_dir = Path(base_dir)

    def validate_full_path(self, basepath, subpath):
        if subpath is None:
            return basepath
        else:
            basepath_str = str(Path(basepath).resolve())
            subpath_str = str(Path(subpath).resolve())
            if subpath_str.startswith(basepath_str):
                return subpath_str
            elif basepath_str.startswith(subpath_str):
                raise ValueError(f"Folder name '{subpath}' is a basepath directory of the base directory '{basepath}'")
            else:
                combined_path = Path(basepath) / Path(subpath).name
                return str(combined_path)

    def set_download_folder(self, status_update=None, folder_name=None):
        # log.debug(f"Invoking set_download_folder()")
        if folder_name is None:
            return {'directory_path': ""}
        
        # log.debug(f"{self.base_dir = }, {folder_name = }")
        working_path = self.validate_full_path(self.base_dir, folder_name)
        # log.debug(f"{working_path = }")
        year = self.get_year()
        date_time = self.get_date_time_string()
        directory_path = Path(working_path) / year / date_time

        try:
            # If the path exists, is a directory, and is not empty, create a new timestamped folder
            if directory_path.exists() and directory_path.is_dir() \
                    and len(os.listdir(str(directory_path))) > 0:
                new_timestamp = datetime.now().strftime("%H%M%S") #add seconds.
                working_path = self.validate_full_path(self.base_dir, folder_name)
                directory_path = working_path / year / f"{self.get_month_day()}_{new_timestamp}"
                date_time = f"{self.get_month_day()}_{new_timestamp}" #update date_time string.
            # os.makedirs(directory_path, exist_ok=True)
        except OSError as e:
            log.error(f"Failed to create directory {directory_path}: {e}")
            status_update(f"Failed to create directory {directory_path}: {e}")
            return None

        # log.debug(f"{directory_path = }")
        return {
            'directory_path': str(directory_path),
            'year': year,
            'date_time': date_time,
        }
    
    def make_new_dir(self, status_update, path):
        return super().make_new_dir(path)

    
class ZipUtility(DirectoryUtils, DateFormatter):
    def __init__(self):
        # log.debug(f"Initializing ZipUtility...")
        super().__init__()
        DateFormatter.__init__(self) # !! STOP putting '()' after parent class

    def has_html_files(self, directory):
        return any(filename.endswith(".html") for filename in Path(directory).iterdir())
    
    def zip_files(self, status_update, directory:str|Path):
        # Example usage:
        # zip_html_files("/path/to/your/directory")
        directory = Path(directory).resolve()  # Ensure directory is an absolute path
        log.debug(f"ZipUtility {directory = }")
        
        try:
            # Removes most current directory if it's completely empty
            msg = self.remove_empty_dir(directory)
            if msg:
                status_update(msg)
                return
        except:
            # has_html_files = any(filename.endswith(".html") for filename in directory.iterdir())
            if not self.has_html_files(directory):
                msg = f"No HTML files found in {directory}."
                log.debug(msg)
                status_update(msg)
                return
        # log.debug(f"{self.get_year() = }")
        # log.debug(f"ZIP Util: {config.output_dir = }")
        trunc_path = str(directory).split('Downloads\\')[1]
        zip_filename = trunc_path.replace('\\', '_')
        zip_filename = f"{zip_filename}.zip"
        # log.debug(f"{zip_filename = }")
        # zip_filename = f"{folder_name}_{self.get_year()}_{directory.name}.zip"

        zip_filepath = directory.parent / zip_filename
        if zip_filepath.exists():
            msg = f"Zip file exists in {directory}."
            log.debug(msg)
            status_update(msg)
            return
        
        html_files = [file for file in directory.iterdir() if file.name.endswith(".html")]
        with zipfile.ZipFile(zip_filepath, 'w') as zip_file:
            # Iterate over all HTMl files in the directory
            for file in html_files:
                zip_file.write(os.path.join(directory, file), file)

        msg = f"Success! HTML files in directory {directory} have been zipped to {zip_filepath}."
        log.info(msg)
        status_update(msg)



# Example Usage:
# if __name__ == "__main__":
#     class DummyParent:
#         pass
#     base_dir = "/tmp/downloads"  # Replace with your desired base directory
#     folder_name = "my_folder"

#     pbuilder = PathBuilder(DummyParent(), base_dir)
#     download_folder = pbuilder.set_download_folder(folder_name)

#     if download_folder:
#         log.debug(download_folder)

#     # Simulate an existing folder to test the new logic
#     try:
#         os.makedirs(download_folder['directory_path'], exist_ok=True)
#     except Exception:
#         pass #ignore if the folder already exists.

#     download_folder = pbuilder.set_download_folder(folder_name) #call again, it will create a new folder.

#     if download_folder:
#         log.debug(download_folder)

#     base_dir = "C:\\downloads" #example windows path.
#     pbuilder = PathBuilder(DummyParent(), base_dir)
#     download_folder = pbuilder.set_download_folder(folder_name)

#     if download_folder:
#         log.debug(download_folder)

#     # Simulate an existing folder to test the new logic
#     try:
#         os.makedirs(download_folder['directory_path'], exist_ok=True)
#     except Exception:
#         pass #ignore if the folder already exists.

#     download_folder = pbuilder.set_download_folder(folder_name) #call again, it will create a new folder.

#     if download_folder:
#         log.debug(download_folder)


# if __name__ == "__main__":
#     dn = PathBuilder()
#     shelf_name = 'LGBTQ_Fantasy_SciFi'
#     data = dn.set_download_folder({'shelf_folder': shelf_name})
#     log.debug(f"{data = }")