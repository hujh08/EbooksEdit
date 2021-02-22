#!/usr/bin/env python3

'''
functions for path operations
'''

import os
import re
import numbers

# list files in dir
def list_files_in_dir(dir_images='.', fname_format=None):
    '''
        list files in a directory

        result returned is sorted in some order

        if `fname_format` is given, filter out files with that format
    '''
    fnames=list(list_regular_files(dir_images))

    if fname_format is not None:
        fnames, inds=filter_fnames_by_format(fnames, fname_format)

    fnames_dir=list(join_path_to_fnames(fnames, dir_images))

    if len(fnames)<2:
        return fnames_dir

    if fname_format is None:
        inds=parse_format_fnames(fnames)

    return [fnames_dir[i] for i in argsort_fnames(fnames, inds)]

def list_files_by_range_fmt(dir_images='.', fname_format=None, page_range=None):
    '''
        list files by given name format and range
    '''
    if page_range is None:
        fnames=list_files_in_dir(dir_images, fname_format)
    else:
        if fname_format is None:
            raise Exception('fname format is not given')

        if isinstance(page_range, numbers.Integral):
            p0=page_range
            p1=p0
        elif len(page_range)==1:
            p0=page_range[0]
            p1=p0
        else:
            p0, p1=page_range

        fnames=[]
        for p in range(p0, p1+1):
            fname=os.path.join(dir_images, fname_format % p)
            fnames.append(fname)

    return fnames

# sort functions
def argsort_fnames(fnames, key=None):
    if key is None:
        return argsort(fnames)

    return argsort(key)

def argsort(array):
    '''
        argsort array
    '''
    inds=list(range(len(array)))
    pairs=list(zip(inds, array))
    return [i for i, _ in sorted(pairs, key=lambda s: s[1])]

# operations to a list of fnames
def join_path_to_fnames(fnames, parent):
    '''
        join a parent directory to a list of fnames
    '''
    for fname in fnames:
        yield os.path.join(parent, fname)

def list_regular_files(directory='.'):
    '''
        list regular files in a directory
    '''
    for name in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, name)):
            yield name

# file name format
def parse_format_fnames(fnames):
    '''
        extract a global format for a list of file names
            which is of the form: ${PREFIX}${INDEX}${SUFFIX}

        if format not exists, return None

        if exists, return indices for files
    '''
    ptn=re.compile(r'(\D*)(\d*)(.*)')

    p=fnames[0]
    PREFIX, num, SUFFIX=ptn.match(p).groups()
    if not num:
        return None

    indices=[int(num)]
    samefmt=True
    for p in fnames[1:]:
        pref, num, suff=ptn.match(p).groups()
        if (not num) or (pref != PREFIX) or (suff != SUFFIX):
            samefmt=False
            break
        indices.append(int(num))

    if not samefmt:
        return None

    return indices

## filter by format
def filter_fnames_by_format(fnames, strformat):
    '''
        filter out file names for the given format

        valid string format here only could accept one integral as argument
    
        return filtered fnames and indices
    '''
    if not is_valid_strformat_fname(strformat):
        raise Exception('invalid string format:', strformat)

    ptn=strformat_to_repattern(strformat)

    fnames_result=[]
    inds=[]
    for name in fnames:
        fname=os.path.join(dir_images, name)
        
        m=ptn.match(name)
        if not m:
            continue

        ind,=m.groups()
        ind=int(ind)

        fnames_result.append(name)
        inds.append(ind)

    return fnames_result, inds

def strformat_to_repattern(strformat):
    '''
        convert string format to re pattern
    '''
    s=strformat.replace('.', r'\.').replace('%i', r'(\d)')

    return re.compile('^'+s+'$')

def is_valid_strformat_fname(strformat):
    '''
        valid string format here only could accept one integral as argument
    '''
    if '%i' not in strformat:
        return False

    try:
        strformat % 0
    except:
        return False

    return True