"""
This module provides a function for downloading files from a URL.
"""
import requests
from pathlib import Path

def download_to_local(url:str, out_path:Path, parent_mkdir:bool=True):
    """
    Downloads a file from a URL and saves it to a local path.

    Args:
        url (str): The URL of the file to download.
        out_path (Path): The local path to save the file to.
        parent_mkdir (bool): If True, creates the parent directory of `out_path`
            if it does not exist.

    Returns:
        True if the download was successful, False otherwise.
    """
    if not isinstance(out_path, Path):
        raise ValueError(f"{out_path} is not a valide Pathlib Path object")
    
    if parent_mkdir:
        out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url)
        response.raise_for_status()

        #Write in binary mode to avoid new line conversion
        out_path.write_bytes(response.content)
        return True
    except requests.RequestException as e:
        print (f"Failed to download {url} : {e}")
        return False
