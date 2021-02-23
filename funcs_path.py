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
        inds=get_orderkey_for_fnames(fnames)

    return sort_fnames(fnames_dir, key=inds)

def list_files_by_range_fmt(dir_images='.', fname_format=None, page_range=None):
    '''
        list files by given name format and range
    '''
    if page_range is None:
        fnames=list_files_in_dir(dir_images, fname_format)
    else:
        if fname_format is None:
            raise Exception('fname format is not given')

        fnames=[]
        for p in ext_elements_by_range(ele_range=page_range):
            fname=os.path.join(dir_images, fname_format % p)
            fnames.append(fname)

    return fnames

# sort functions
def argsort(array):
    '''
        argsort array
    '''
    inds=list(range(len(array)))
    pairs=list(zip(inds, array))
    return [i for i, _ in sorted(pairs, key=lambda s: s[1])]

def sort_fnames(fnames, key=None):
    if key is None:
        key=get_orderkey_for_fnames(fnames)

    return [fnames[i] for i in argsort(key)]

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
def get_orderkey_for_fnames(fnames):
    '''
        get a key for the fnames sorting

        extract thd digit slice in fname
            and different kind order for string and digit
    '''
    ptn=re.compile(r'(\d+)')  # pattern for split

    inds=[]
    for fname in fnames:
        segs=ptn.split(fname)

        digits=[]
        chars=[]
        for s in segs:
            if ptn.match(s):
                digits.append(int(s))
            else:
                chars.append(s)

        inds.append((tuple(chars), tuple(digits)))

    return inds

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

    fnms=[]
    inds=[]
    for name in fnames:
        m=ptn.match(name)
        if not m:
            continue

        ind,=m.groups()
        ind=int(ind)

        fnms.append(name)
        inds.append(ind)

    return fnms, inds

def strformat_to_repattern(strformat):
    '''
        convert string format to re pattern
    '''
    s=strformat.replace('.', r'\.').replace('%i', r'(\d+)')

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

# page range
def ext_elements_by_range(array=None, ele_range=None,
                            keep_end=False, one_started=False):
    '''
        extract continuing elements in array

        Parameters:
            ele_range: None, integral, list of one/two elements
                if None, return total array

                The other 3 types are represented by `p`, `[p]`, `[p0, p1]` respectively

                See readme for detail

            array: None or array-like object
                if None, ele_range must be `[p0, p1]` or `p`,
                    for `p`,  list of only one element is returned
                    for `[p0, p1]`, numbers from p0 to p1 would be returned.
                        if `keep_end`, p1 is included

            one_started: bool
                if True, the positive index starts from 1, not 0
    '''
    if ele_range is None:
        return array

    # translate `p` to `[p0, p1]`
    if isinstance(ele_range, numbers.Integral):
        p0=p1=ele_range
        ele_range=[p0, p1]
        keep_end=True

    # step is supported
    assert len(ele_range)<=3

    # handle `[p0, p1, step]`
    step=1
    incre=1    # used to handle keep end
    if len(ele_range)==3:
        step=ele_range.pop()
        assert step!=0

        incre=step//abs(step)

    assert 1<=len(ele_range)<=2

    # producing mode
    if array is None:
        p0, p1=ele_range
        assert isinstance(p0, numbers.Integral) and \
               isinstance(p1, numbers.Integral)

        if keep_end:
            p1+=incre

        return list(range(p0, p1, step))

    # handle `[p]`
    if len(ele_range)==1:
        p,=ele_range
        return array[slice(p)]

    # handle `[p0, p1]`
    p0, p1=ele_range
    n=len(array)

    if one_started: # normalized to zero-started
        if p0 is not None and p0>0:
            p0-=1
        if p1 is not None and p1>0:
            p1-=1

    '''
    Note:
        if p0 exceed the border, 0 or n-1, (for step>0 or <0)
            slice will retract to 0/n-1 respectively
    
                not min {t=p0+k*step: 0 <= t <= n-1}
    '''
    # make it clear, not dependent on implement of slice
    if p0 is not None:
        if p0<0:
            p0+=n

        if p0<0 and step<0:
            return []

        if p0<0 and step>0:
            p0=0
        elif p0>n-1 and step<0:
            p0=n-1

    # handle keep_end
    if keep_end and p1 is not None:
        if p1<0:
            p1+=n

        if p1<0:
            p1-=n

        p1+=incre

    return array[slice(p0, p1, step)]
