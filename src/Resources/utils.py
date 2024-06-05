import json


def load_config(file_path: str) -> dict:
    """
    Load a JSON configuration file.
    :param file_path: Path to the JSON file.
    :return: Dictionary with the configuration.
    """
    with open(file_path, 'r') as file:
        return json.load(file)
