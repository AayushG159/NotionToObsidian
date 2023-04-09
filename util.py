from pathlib import Path


def get_nested_tag(file_path, root):
    """
    Generate nested tag from relative file path
    :param file_path: current directory path
    :param root: root path
    :return: nested tag
    """
    relative_file_path = Path(file_path).relative_to(Path(root))
    tag_name = str(relative_file_path).replace(' ', '').replace('\\', '/')
    return tag_name
