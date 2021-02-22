#!/usr/bin/env python3

'''
Functions for PDF outline
'''

import numbers
import re

from .funcs_rw import open_pdf_as_reader

# from pdf
def get_outlines_from_reader(reader):
    '''
        return list of entries [title, page number, level]
            where
                `level` starts from 0 (that means top level is 0)
                `page number` also starts from 0
    '''
    outlines=reader.getOutlines()
    return parse_outlines_list(outlines, reader)

def get_outlines_from_pdf(pdfname):
    '''
        get outlines from a pdf file
    '''
    reader=open_pdf_as_reader(pdfname)
    return get_outlines_from_reader(reader)

def parse_outlines_list(outlines, reader, level=0):
    '''
        parse outline list gotten directly from PyPDF2 reader

        return [title, page number, level]

        Parameters:
            level: int
                current outline level
    '''
    result=[]
    for entry in outlines:
        if '/Title' not in entry:
            suboutlines=parse_outlines_list(entry, reader, level+1)
            result.extend(suboutlines)

            continue

        title=entry['/Title']
        page=reader.getDestinationPageNumber(entry)
        result.append([title, page, level])

    return result

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

            result.append([title, page+offset, level])

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
def level_parser_sec(title, page):
    '''
        parse level from the section id
            which is given by like 1.1 for level 1
    '''
    sec, *_=title.split(maxsplit=1)
    m=re.match(r'([\dIVX]+(\.\d+)*)\s', title)
    if m:
        return len(m.groups()[0].split('.'))-1

    return 0

# add outlines
def add_outlines(writer, outlines):
    '''
        add outlines given by a list of entries [title, page number, level]

        return number of outlines added
    '''
    parents=[]
    parent=None
    level_now=-1
    n=0
    for title, page, level in outlines:
        if level>level_now:
            assert level==level_now+1
            level_now=level
            parents.append(parent)
        elif level<level_now:
            for _ in range(level_now-level):
                parents.pop()
            level_now=level

        parent=writer.addBookmark(title, page, parents[-1])
        n+=1

    return n
