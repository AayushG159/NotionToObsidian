import logging
import re
from shutil import move
from pathlib import Path
from notion_db import convert_notion_db_data

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class Migrate:
    MAX_DEPTH = 100
    MARKDOWN_SUFFIX = '.md'
    CSV_SUFFIX = '.csv'
    MARKDOWN_CSV_SUFFIX = [MARKDOWN_SUFFIX, CSV_SUFFIX]

    def __init__(self, root_loc):
        self.uuid = set()
        self.files = set()
        self.attachments = set()
        self.root_loc = root_loc

    def start_migration(self):
        """
        Main function to be called for starting the migration
        :return: None
        """
        self.traverse_rename(current_dir=self.root_loc)
        self.format_files()

    def move_attachments_format_links(self, folder_name):
        pass

    def format_files(self):
        """
        Fetches file list stored traverse_rename() and performs the following operations based on the type of file:
        1. Markdown (.md) - removes all uuids from a list generated during traverse_rename()
        2. CSV (.csv) - run a mini-function which converts all notion db properties to obsidian front-matter
        :return: None
        """
        for file_path in self.files:
            file = Path(file_path)
            if file.suffix == Migrate.MARKDOWN_SUFFIX:
                self.remove_uuid_refs(file)
            elif file.suffix == Migrate.CSV_SUFFIX:
                convert_notion_db_data(file, self.root_loc)
            else:
                continue

    def remove_uuid_refs(self, path):
        with open(path, 'r+', encoding='utf-8') as file:
            file_data = file.read()
            for hex_number in self.uuid:
                file_data = re.sub("%20" + hex_number, "", file_data)
            file.seek(0)
            file.write(file_data)
            file.truncate()

    def traverse_rename(self, current_dir, current_depth=0):
        """
        Performs the following steps:
        1. Traverses until no directories are found
        2. During each depth traversal, store UUID's found on all dir/file names
        3. Rename all
        :param current_dir: path of current directory
        :param current_depth: int, signifying the current depth
        :return: None
        """
        current_dir = Path(current_dir)
        logging.info(f"Current depth: {current_depth} and root dir/file: {current_dir}")
        if current_depth > Migrate.MAX_DEPTH:
            return
        for child_dir in current_dir.iterdir():
            logging.info(f"Dir/File: {child_dir.name}")
            is_dir = True
            extension = ''
            child_dir_split = child_dir.name.split()
            extracted_hex = child_dir_split[-1]
            if child_dir.is_file():
                is_dir = False
                extension = child_dir.suffix
                if extension not in Migrate.MARKDOWN_CSV_SUFFIX:
                    self.attachments.add(child_dir.parents[0])
                    continue
                extracted_hex = extracted_hex.split(extension)[0]
            self.uuid.add(extracted_hex)
            new_name_dir = " ".join(child_dir_split[:-1]) + extension
            logging.info(f"Dir/File renamed to : {new_name_dir}")
            new_path = move(Path(current_dir, child_dir), Path(current_dir, new_name_dir))
            if is_dir:
                logging.info(f"Dir to traverse : {new_path}")
                self.traverse_rename(new_path, current_depth + 1)
            else:
                self.files.add(new_path)
