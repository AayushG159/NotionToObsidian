import logging
import re
import os
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
        self.move_attachments_format_links('Attachments')

    def move_attachments_format_links(self, folder_name):
        """
        Fetches attachment directories list stored and performs the following:
        1. Renames files to it's directory with incremental suffix
        2. Moves the attachments to a designated folder at root location
        3. Format attachment links present in notes
        :param folder_name: desired attachments folder name
        :return: None
        """
        folder_name_path = Path(self.root_loc, folder_name)
        if not os.path.exists(folder_name_path):
            os.mkdir(folder_name_path)
        notion_file_pattern = re.compile(r'(Untitled|untitled)[\s0-9]*')
        markdown_embed_pattern = re.compile(r'!\[.*?\]\((.*?)\)')
        for att_dir in self.attachments:
            att_dir = Path(att_dir)
            if not att_dir.is_dir():
                continue
            index = 0
            new_path_list = dict()
            for att_file in att_dir.iterdir():
                att_file = Path(att_file)
                match = re.search(notion_file_pattern, str(att_file))
                new_file_name = att_file.name
                if match:
                    suffix = att_file.suffix
                    new_file_name = att_file.parents[0].name + ' - ' + str(index) + suffix
                    index += 1
                old_path = str(att_file.relative_to(att_dir.parents[0])).replace('\\', '/').replace(' ', '%20')
                new_path = str(move(Path(att_file), Path(folder_name_path, new_file_name)))
                new_path_list[old_path] = str(Path(new_path).relative_to(Path(self.root_loc))).replace('\\', '/')
            # opening corresponding markdown file
            md_file = str(att_dir) + Migrate.MARKDOWN_SUFFIX
            with open(md_file, 'r', encoding='utf-8') as file:
                md_file_data = file.readlines()
            for i, line in enumerate(md_file_data):
                if re.search(markdown_embed_pattern, line):
                    embed_path = line.rstrip()[line.index('(')+1: -1]
                    line = '![[' + new_path_list[embed_path] + ']]'
                    md_file_data[i] = line
            with open(md_file, 'w', encoding='utf-8') as file:
                file.writelines(md_file_data)

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
        """
        Replaces uuid (extracted during traverse_rename()) in file content
        :param path: file_path
        :return: None
        """
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
