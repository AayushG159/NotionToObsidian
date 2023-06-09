import csv
import logging
import re
from pathlib import Path
from util import get_nested_tag

logger = logging.getLogger(__name__)
date_regex = re.compile(r'[\d]{4}/[\d]{1,2}/[\d]{1,2}')


def convert_notion_db_data(file_path, root_path):
    """
    #TODO: Add support for multiple date-formats
    Performs the following steps:
    1. Read csv and extract headers from it
    2. Navigate to corresponding dir using name extracted
    3. Using the extracted header list, convert every file containing the headers into obsidian front-matter
    4. Add nested tag at the end of yaml front-matter
    :param file_path: CSV file path
    :param root_path: Root directory path
    :return: None
    """
    file_path = Path(file_path)
    suffix = file_path.suffix
    file_name = file_path.name[:-len(suffix)]
    dir_path = Path(file_path.parents[0], file_name)
    tag_property = 'tag: "' + get_nested_tag(dir_path, root_path) + '"\n'
    logger.debug(f"Reading header list from {file_path}")
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        extracted_headers = next(csv_reader)
    logger.debug(f"Extracted headers: {extracted_headers}")
    logger.debug(f"Iterating over files in dir {dir_path.name}")
    for child_file in dir_path.iterdir():
        logger.debug(f"Formatting data in {child_file.name}")
        if not child_file.is_file():
            continue
        with open(child_file, 'r', encoding='utf-8') as file:
            file_data = file.readlines()
        index = list()
        for i, line in enumerate(file_data):
            for header in extracted_headers:
                # added colon symbol so that it takes into consideration of being a property
                if line.find(header + ':') > -1:
                    index.append(i)
                    line = line.replace(header, header.lower().replace(' ', '-'))
                line = re.sub(date_regex, lambda m: m.group(0).replace('/', '-'), line)
                file_data[i] = line
        front_matter_str = '---\n'
        file_data[index[-1]] = file_data[index[-1]].rstrip() + '\n' + tag_property + front_matter_str
        file_data[index[0]] = front_matter_str + file_data[index[0]]
        with open(child_file, 'w', encoding='utf-8') as file:
            file.writelines(file_data[index[0]:])
        logger.debug(f"Modified file {child_file.name}")
    logger.debug(f"Completed modification of database in {dir_path.name}")
