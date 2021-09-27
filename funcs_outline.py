#!/usr/bin/env python3

'''
Functions for PDF outline

two types of representation: nest (nested list), level (explicit level specified)
    nest: a nested list,
        e.g. [(t1, p1), [(t2, p2), (t3, p3)]]
    level: level is specified explicitly,
        e.g. [(t1, p1, 0), (t2, p2, 1), (t3, p3 1)]
'''

import numbers
import re

from PyPDF2.generic import NullObject

from .funcs_rw import open_pdf_as_reader

# from pdf
def get_outlines_from_reader(reader, page_shift=0):
    '''
        return list of entries [title, page number, level]
            where
                `level` starts from 0 (that means top level is 0)
                `page number` also starts from 0
    '''
    outlines=reader.getOutlines()
    return parse_outlines_list(outlines, reader, page_shift=page_shift)

def get_outlines_from_pdf(pdfname, page_shift=0):
    '''
        get outlines from a pdf file
    '''
    reader=open_pdf_as_reader(pdfname)
    return get_outlines_from_reader(reader, page_shift=page_shift)

def parse_outlines_list(outlines, reader, level=0, page_shift=0):
    '''
        parse outline list gotten directly from PyPDF2 reader

        return [title, page number, level]

        Parameters:
            level: int
                current outline level
    '''
    result=parse_outlines_nest(outlines, reader, page_shift=page_shift)

    return outline_nest_to_level(result, level=level)

def parse_outlines_nest(outlines, reader, page_shift=0, remove_unprintable=True):
    '''
        parse outline list gotten directly from PyPDF2 reader

        return nested outlines, [(t1, p1), [(t2, p2), (t3, p3)]]

        Parameters:
            page_shift: int

            remove_unprintable: bool
                wheter remove unprintable char, e.g. '\x00'
    '''
    result=[]
    for entry in outlines:
        if '/Title' in entry:
            title=entry['/Title']
            if remove_unprintable:
                title=str_clean_unprintable(title)

            if isinstance(entry.getDestArray()[0], NullObject):
            # if not hasattr(entry.getDestArray()[0], 'idnum'):
                page=-1
            else:
                page=reader.getDestinationPageNumber(entry)
                page+=page_shift
            result.append([title, page])
            continue

        subout=parse_outlines_nest(entry, reader, page_shift=page_shift)
        result.append(subout)

    return result

def str_clean_unprintable(s):
    '''
        remove unprintable chars, like '\x00'
    '''
    if isinstance(s, bytes):  # element in bytes would be int, i.e. type(s[0]) is int
        s=s.decode()
    return ''.join([i for i in s if i.isprintable()])

# from txt file
def get_outlines_from_txt(fname, offset=0, lstrip=True, func_level=None):
    '''
        parse text file to the list of entries [title, page number, level]
            see `get_outlines_from_reader` for detail

        each line in the text file is wrtten with format
            title page[L(level)]
        where
            level is optional
                which is given by appending to the page number
                    seperated with letter `L`, ignoring case
            page is the page number which starts from 1

        Parameter:
            func_level: None, int, string, or callable
                function for line mssing `level` field
                if None, use 0
                if int, use it as a default level
                if string, use a function named by it
                if callable, it is called with `func_level(title, page)`

            offset: int
                offset for page number
    '''
    # strip
    strip=lambda line: line.rstrip()
    if lstrip:
        strip=lambda line: line.strip()

    # func level
    if func_level is None:
        func_level=lambda title, page: 0
    elif isinstance(func_level, numbers.Integral):
        level=int(func_level)
        func_level=lambda title, page, l=level: l
    elif type(func_level) is str:
        # current named functions
        funcs_named={'sec': level_parser_sec}
        func_level=funcs_named[func_level]
    elif not callable(func_level):
        raise Exception('unexpected func_level:', func_level)

    # main work
    result=[]
    with open(fname) as f:
        for line in f:
            title, pnumstr=strip(line).rsplit(maxsplit=1)

            # page number, outline level
            page, level=pagenum_parse(pnumstr)

            # outline level
            if level is None:
                level=func_level(title, page)

            # minus 1 since page number in text starts from 1
            result.append([title, page+offset-1, level])

    return result

def pagenum_parse(pnumstr):
    '''
        parse string for pagenum in text outline file

        two formats:
            xxx: an interger
                only contain page number
            xxxLxxx or xxxlxxx: aLb
                a: page number
                b: outline level
    '''
    nums=pnumstr.lower().split('l')
    if len(nums)==1:
        return int(nums[0]), None

    num, level=nums
    return int(num), int(level)

## some named functions for level parser
def level_parser_sec(title, page, level_default=0):
    '''
        parse level from the section id
            which is given by like 1.1 for level 1
    '''
    sec, *_=title.split(maxsplit=1)
    m=re.search(r'([\dIVX]+(\.\d+)*)', sec)
    if m:
        return len(m.groups()[0].split('.'))-1

    return level_default

def get_level_parser_map(level_map, level_default=0):
    '''
        get a level parser which is based on a map from title starting to level
    '''
    if str(level_map) is not dict:
        # if not dict, must be [(list of strings, level)]
        level_list=level_map
        level_map={}
        for names, level in level_list:
            if type(names) is not str:
                for n in names:
                    level_map[n]=level
            else:
                level_map[names]=level

    def parser(title, page, level_default=level_default):
        starting=title.split(maxsplit=1)[0]
        if starting in level_map:
            return level_map[starting]
        return level_default

    return parser

def combine_level_parser(*parsers, level_default=0):
    '''
        combine a list of parsers
    '''
    def parser(title, page, level_default=level_default):
        for f in parsers:
            level=f(title, page, level_default=None)

            if level is not None:
                return level

        return level_default

    return parser

# two types of representation of outlines: nest (nested list), level (explicit level specified)
def outline_nest_to_level(outlines, level=0):
    '''
        convert nested outlines to explicit level

        two structures to store outlines
            nest: a nested list,
                e.g. [(t1, p1), [(t2, p2), (t3, p3)]]
            level: level is specified explicitly,
                e.g. [(t1, p1, 0), (t2, p2, 1), (t3, p3 1)]

        Parameter:
            level: int
                level of top outline
    '''
    is_atom=is_outline_entry

    result=[]
    for (title, page), level in iter_nested_list(outlines, level, is_atom=is_atom):
        result.append([title, page, level])
    return result

def outline_level_to_nest(outlines):
    '''
        convert explicit level outlines to nest type

        two structures to store outlines
            nest: a nested list,
                e.g. [(t1, p1), [(t2, p2), (t3, p3)]]
            level: level is specified explicitly,
                e.g. [(t1, p1, 0), (t2, p2, 1), (t3, p3 1)]
    '''
    parents=[]
    parent=[]
    level_prev=None

    result=parent
    for title, page, level in outlines:
        if level_prev is None:
            level_prev=level

        if level>level_prev:
            parents.append((parent, level_prev))
            
            parent.append([])
            parent=parent[-1]
        elif level<level_prev:
            assert parents

            while parents:
                parent, l0=parents.pop()
                if l0<=level:
                    break

            assert l0==level # not allowed new level, which not existed before

        parent.append([title, page])
        level_prev=level

    return result

## auxilliary function
def is_outline_entry(e):
    '''
        determine wheter an entry is outline type, that is [title, page]
            in a nested structure of outlines
    '''
    return not hasattr(e[-1], '__iter__')

def iter_nested_list(root, level=0, is_atom=lambda e: not hasattr(e, '__iter__')):
    '''
        iter in the nested list

        return element, level

        Parameter:
            level: int
                top level for the nested list

            is_atom: callable
                determine whether current element is an atom,
                    if so, it would be returned
    '''
    assert hasattr(root, '__iter__')

    for e in root:
        if is_atom(e):
            yield e, level
        else:
            for a in iter_nested_list(e, level+1, is_atom=is_atom):
                yield a

# add outlines
def add_outlines(writer, outlines, parent=None):
    '''
        add outlines given by a list of entries [title, page number, level]

        return number of outlines added

        `exclude_invalid`: exclude invalid outline
            which refer to page out of writer
    '''
    numpages=writer.getNumPages()

    outlines_nest=outline_level_to_nest(outlines)

    return add_outlines_nest(writer, outlines_nest)

def add_outlines_nest(writer, outlines, parent=None):
    '''
        add outlines given by a nested type

        return number of outlines added

    '''
    n=0
    bm=None
    for entry in outlines:
        if is_outline_entry(entry):
            title, page=entry
            bm=writer.addBookmark(title, page, parent)

            n+=1
        else:
            assert bm is not None  # not allow empty parent
            n+=add_outlines_nest(writer, entry, bm)

    return n

# write to text
def write_outline_to_txt(fname, outlines):
    '''
        write a outline list to a text file
    '''
    with open(fname, 'w') as f:
        for title, page, level in outlines:
            f.write('%s %iL%i\n' % (title, page, level))

def write_outline_nest_to_txt(fname, outlines, delimiters=('/*', '*/')):
    '''
        write nested outlines to a text file
    '''
    if type(delimiters) is str:
        d0=d1=delimiters
    else:
        d0, d1=delimiters

    with open(fname, 'w') as f:
        _write_outline_nest(f, outlines, d0, d1, 0)

def _write_outline_nest(f, outlines, d0, d1, i):
    '''
        real work of function `write_outline_nest_to_txt`

        next i would be returned

        Parameter:
            d0, d1: str
                start/end delimiters
                it could be different, like {, },
                    or same for both , like ======

            i: int
                id of a delimiter
    '''
    i0=i
    i+=1

    f.write('%s quote %i\n' % (d0, i0))
    for entry in outlines:
        if is_outline_entry(entry):
            title, page=entry
            f.write('%s %i\n' % (title, page))
        else:
            i=_write_outline_nest(f, entry, d0, d1, i)
    f.write('%s quote %i\n' % (d1, i0))

    return i

# read nested text file
def get_outlines_from_nest_txt(fname, delimiters=('/*', '*/'), lstrip=True):
    '''
        get outline from nested text file
    '''
    # strip
    strip=lambda line: line.rstrip()
    if lstrip:
        strip=lambda line: line.strip()

    # delimiters
    if type(delimiters) is str:
        d0=d1=delimiters
    else:
        d0, d1=delimiters

    parents=[]
    holder=None

    root=[]
    with open(fname) as f:
        for line in f:
            if line.startswith(d0):
                parents.append(holder)

                if holder is None:
                    holder=root
                else:
                    holder.append([])
                    holder=holder[-1]
            elif line.startswith(d1):
                holder=parents.pop()
            else:
                title, page=strip(line).rsplit(maxsplit=1)
                holder.append([title, int(page)])

    assert not parents

    return root
