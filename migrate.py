import re
import os
import logging
from shutil import move
from pathlib import Path
from notion_db import convert_notion_db_data
from util import get_nested_tag

logger = logging.getLogger(__name__)


class Migrate:
    MAX_DEPTH = 100
    MARKDOWN_SUFFIX = '.md'
    CSV_SUFFIX = '.csv'
    MARKDOWN_CSV_SUFFIX = [MARKDOWN_SUFFIX, CSV_SUFFIX]
    NOTION_FILE_PATTERN = re.compile(r'(Untitled|untitled)[\s0-9]*')
    MARKDOWN_EMBED_PATTERN = re.compile(r'!\[.*?\]\((.*?)\)')
    MARKDOWN_LINK_PATTERN = re.compile(r'\[.*?\]\((.*?)\)')

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
        logger.info(f"Initiating notion to obsidian notes migration")
        logger.info(f"Traversing, storing UUIDs from file names, renaming files")
        self.traverse_rename(current_dir=self.root_loc)
        logger.info(f"Complete")
        logger.info(f"Removing UUIDs from files and formatting notion DB data")
        self.format_files()
        logger.info(f"Complete")
        logger.info(f"Renaming and moving attachments to designated folder. Also, resolving corresponding embeds in notes")
        self.move_attachments_format_links('Attachments')
        logger.info(f"Complete")
        logger.info(f"Adding nested tags as front-matter to notes, moving them to root location and resolving internal links")
        self.notes_tags_move_resolve('Attachments')
        logger.info(f"Complete")

    def notes_tags_move_resolve(self, folder_name):
        """
        Performs the following:
        1. Add nested tag based on file path
        2. Checks for internal links and resolves them in advance for notes movement in the following step
        3. Moves notes to root location
        :param folder_name: desired attachments folder name
        :return: None
        """
        front_matter_str = '---'
        for file in self.files:
            file = Path(file)
            if file.suffix == Migrate.MARKDOWN_SUFFIX:
                logger.debug(f"Adding nested tags in note: {file.name}")
                is_file_changed = False
                with open(file, 'r', encoding='utf-8') as f:
                    file_data = f.readlines()
                for i, line in enumerate(file_data):
                    if i == 0 and file_data[0].rstrip() != front_matter_str:
                        is_file_changed = True
                        tag_property = 'tag: "' + get_nested_tag(file, self.root_loc) + '"\n'
                        file_data[i] = front_matter_str + '\n' + tag_property + front_matter_str + '\n'
                    if re.search(Migrate.MARKDOWN_LINK_PATTERN, line):
                        is_file_changed = True
                        embed_path = line.rstrip()[line.index('(') + 1: -1]
                        if embed_path.rfind(Migrate.MARKDOWN_SUFFIX) > -1:
                            line = '[[' + embed_path[embed_path.rfind('/') + 1:] + ']]'
                            file_data[i] = line
                if is_file_changed:
                    with open(file, 'w', encoding='utf-8') as f:
                        f.writelines(file_data)
                move(file, Path(self.root_loc, file.name))
            if file.suffix == Migrate.CSV_SUFFIX:
                move(file, Path(self.root_loc, folder_name, file.name))
            logger.debug(f"Moved note: {file.name}")

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
        logger.debug(f"Created designated folder for attachments: {folder_name}")
        for att_dir in self.attachments:
            att_dir = Path(att_dir)
            if not att_dir.is_dir():
                continue
            logger.debug(f"Moving attachments from folder: {att_dir.name}")
            index = 0
            new_path_list = dict()
            for att_file in att_dir.iterdir():
                att_file = Path(att_file)
                match = re.search(Migrate.NOTION_FILE_PATTERN, str(att_file))
                new_file_name = att_file.name
                if match:
                    suffix = att_file.suffix
                    new_file_name = att_file.parents[0].name + ' - ' + str(index) + suffix
                    index += 1
                old_path = str(att_file.relative_to(att_dir.parents[0])).replace('\\', '/').replace(' ', '%20')
                new_path = str(move(Path(att_file), Path(folder_name_path, new_file_name)))
                new_path_list[old_path] = str(Path(new_path).relative_to(Path(self.root_loc))).replace('\\', '/')
                logger.debug(f"Moved file attachments from folder: {att_file.name}")
            # opening corresponding markdown file
            md_file = Path(str(att_dir) + Migrate.MARKDOWN_SUFFIX)
            with open(md_file, 'r', encoding='utf-8') as file:
                md_file_data = file.readlines()
            for i, line in enumerate(md_file_data):
                if re.search(Migrate.MARKDOWN_EMBED_PATTERN, line):
                    embed_path = line.rstrip()[line.index('(')+1: -1]
                    line = '![[' + new_path_list[embed_path] + ']]'
                    md_file_data[i] = line
            with open(md_file, 'w', encoding='utf-8') as file:
                file.writelines(md_file_data)
            logger.debug(f"Resolved attachments embeds in note: {md_file.name}")

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
        logger.debug(f"Current depth: {current_depth} and root dir/file: {current_dir}")
        if current_depth > Migrate.MAX_DEPTH:
            return
        for child_dir in current_dir.iterdir():
            logger.debug(f"Dir/File: {child_dir.name}")
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
            logger.debug(f"Dir/File renamed to : {new_name_dir}")
            new_path = move(Path(current_dir, child_dir), Path(current_dir, new_name_dir))
            if is_dir:
                logger.debug(f"Dir to traverse : {new_path}")
                self.traverse_rename(new_path, current_depth + 1)
            else:
                self.files.add(new_path)
