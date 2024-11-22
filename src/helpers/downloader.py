import requests
from pathlib import Path

def download_to_local(url:str, out_path:Path, parent_mkdir:bool=True):
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
    