import collections
from configparser import ConfigParser
import os, sys
import logging

# from pathlib import Path, PurePath

class UserValidationError(Exception):
    pass

class PrettyDict(collections.UserDict):
    def __str__(self):
        data = "\n".join(f"{k}: {v}" for k, v in self.data.items())
        return f"\n{data}"
    
class Config(UserValidationError):
    def __init__(self):
        UserValidationError().__init__(self)
        self.rootdir = os.path.dirname(os.path.abspath(__file__))
        #! Switch to config.ini when done with development
        # config_file = os.path.join(self.rootdir, "config.ini")
        config_file = os.path.join(self.rootdir, "dev.ini")
        if not os.path.exists(config_file):
            print("No configuration file found.")
            sys.exit()
        self.config = ConfigParser()
        self.config.read(config_file)

        self.app_dir = self.config['PATHS']['app_dir']
        self.output_dir = self.config['PATHS']['output_dir']
        self.logfile = os.path.join(self.app_dir, self.config['PATHS']['logfile'])

        for section in self.config.sections():
            if section in 'ASSETS':
                for key in self.config[section]:
                    setattr(self, key, self.join_path(self.app_dir, section, key))
            elif section in 'OUTPUT':
                for key in self.config[section]:
                    setattr(self, key, self.join_path(self.output_dir, section, key))
            else:
                for key in self.config[section]:
                    setattr(self, key, self.config[section][key])

    def join_path(self, parent, section, key):
        if 'assets' in section.lower():
            return os.path.join(parent, section.lower(), self.config[section][key])
        else:
            return os.path.join(parent, self.config[section][key])
    
    def set_logger(self, package, name): 
        """ Basic logger with file logging and console logging """

        open(self.logfile, 'a').close()    
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(module)s.%(funcName)s, line %(lineno)d: %(message)s")
        logger = logging.getLogger(f"{package}.{name}") 
        # print(f"{self.logfile = }\n\n")
        logger.setLevel(logging.DEBUG) 
            # Check if handlers already exist to avoid adding them multiple times 
        if not logger.handlers: 
                # File handler 
            fh = logging.FileHandler(filename=self.logfile) 
            fh.setFormatter(formatter) 
            logger.addHandler(fh) 
            # Stream handler (console) 
            sh = logging.StreamHandler(sys.stdout) 
            sh.setFormatter(formatter) 
            logger.addHandler(sh) 
            # Disable propagation to avoid duplicate logs 
        logger.propagate = False 
        return logger
    
    def pretty_dict(self, data_dict):
        return PrettyDict(data_dict)
    
    def get_output_dirs(self):
        # print(f"{self.rootdir = }")
        return {
            "root": self.rootdir,
            "download": self.download_dirs,
            "processed": self.processed_dirs,
        }
    
if __name__ == "__main__":
    config = Config()
    print(config.pretty_dict(config.__dict__))