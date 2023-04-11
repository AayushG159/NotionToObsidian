import configparser
import sys
from pathlib import Path


class Config:

    def __init__(self):
        self.config = configparser.ConfigParser()

    def get_config(self):
        abs_path = Path(sys.path[0])
        config_file_path = Path(abs_path.parents[0], 'resources', 'config.ini')
        self.config.read(config_file_path)
        all_config = self.config['all_config']
        root_loc = all_config['root_location']
        att_folder_name = all_config['attachments_folder_name']
        return root_loc, att_folder_name
