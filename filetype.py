from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def filetype(f):
    # Resolve the file path
    fpath = Path(f).resolve()
    logging.info(f"INPUT FILE PATH: {fpath}")

    # Define a mapping of file extensions to formats
    file_extension_map = {
        '.ggf': 'ggf_',
        '.gff': 'gff_',
        '.byn': 'byn_',
        '.gsf': 'gsf_',
        '.bin': 'jav_bin_'
    }

    # Get file extension and return corresponding format
    return file_extension_map.get(fpath.suffix, 'unknown')
