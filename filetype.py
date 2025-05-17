from pathlib import Path
import os

def filetype(f):
    fpath = Path(f)
    path = fpath.resolve()
    print 'INPUT FILE PATH: ', path
    file_ = open(str(path),'rb').read()
    if Path(f).suffix == '.ggf':
        fileformat = 'ggf_'
        return fileformat
    if Path(f).suffix == '.gff':
        fileformat = 'gff_'
        return fileformat
    if Path(f).suffix == '.byn':
        fileformat = 'byn_'
        return fileformat
    if Path(f).suffix == '.gsf':
        fileformat = 'gsf_'
        return fileformat
    if Path(f).suffix == '.bin':
        fileformat = 'jav_bin_'
        return fileformat
    else:
        return 'unknown'
