import logging
import re
import csv
from shutil import move
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
date_regex = re.compile(r'[\d]{4}/[\d]{1,2}/[\d]{1,2}')


def convert_notion_db_data(file_path):
    """
    Performs the following steps:
    1. Read csv and extract headers from it
    2. Navigate to corresponding dir using name extracted
    3. Using the extracted header list, convert every file containing the headers into obsidian front-matter
    :param file_path: CSV file path
    :return: None
    """
    file_path = Path(file_path)
    suffix = file_path.suffix
    file_name = file_path.name[:-len(suffix)]
    dir_path = Path(file_path.parents[0], file_name)
    logging.info(f"Reading header list from {file_path}")
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        extracted_headers = next(csv_reader)
    logging.info(f"Extracted headers: {extracted_headers}")
    logging.info(f"Iterating over files in dir {dir_path.name}")
    for child_file in dir_path.iterdir():
        logging.info(f"Formatting data in {child_file.name}")
        if not child_file.is_file():
            continue
        with open(child_file, 'r', encoding='utf-8') as file:
            file_data = file.readlines()
        index = list()
        for i, line in enumerate(file_data):
            for header in extracted_headers:
                # TODO: Check if extra colon addition to the finding substr is needed
                if line.find(header + ':') > -1:
                    index.append(i)
                    line = line.replace(header, header.lower().replace(' ', '-'))
                line = re.sub(date_regex, lambda m: m.group(0).replace('/', '-'), line)
                file_data[i] = line

        front_matter_str = '---\n'
        file_data[index[-1]] = file_data[index[-1]].rstrip() + '\n' + front_matter_str
        file_data[index[0]] = front_matter_str + file_data[index[0]]
        with open(child_file, 'w', encoding='utf-8') as file:
            file.writelines(file_data[index[0]:])
        logging.info(f"Modified file {child_file.name}")
    logging.info(f"Completed modification of database in {dir_path.name}")


class Migrate:
    MAX_DEPTH = 100
    MARKDOWN_CSV_SUFFIX = ['.md', '.csv']

    def __init__(self, root_loc):
        self.hex_list = set()
        self.files = dict()
        self.root_loc = root_loc

    def __repr__(self):
        return self.files.__repr__()

    def start_migration(self):
        self.traverse_rename(current_dir=self.root_loc)

    def remove_uuid_refs(self, path):
        with open(path, 'r+', encoding='utf-8') as file:
            file_data = file.read()
            for hex_number in self.hex_list:
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
                    self.files[child_dir.name] = {'path': child_dir}
                    continue
                extracted_hex = extracted_hex.split(extension)[0]
            self.hex_list.add(extracted_hex)
            new_name_dir = " ".join(child_dir_split[:-1]) + extension
            logging.info(f"Dir/File renamed to : {new_name_dir}")
            new_path = move(Path(current_dir, child_dir), Path(current_dir, new_name_dir))
            if is_dir:
                logging.info(f"Dir to traverse : {new_path}")
                self.traverse_rename(new_path, current_depth + 1)
            else:
                self.files[new_name_dir] = {'path': new_path}
