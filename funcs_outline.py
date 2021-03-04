#!/usr/bin/env python3

'''
Functions for PDF outline
'''

import numbers
import re

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
    result=[]
    for entry in outlines:
        if '/Title' not in entry:
            suboutlines=parse_outlines_list(entry, reader, level+1, page_shift)
            result.extend(suboutlines)

            continue

        title=entry['/Title']
        page=reader.getDestinationPageNumber(entry)
        result.append([title, page+page_shift, level])

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
    m=re.match(r'([\dIVX]+(\.\d+)*)\s', title)
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

# add outlines
def add_outlines(writer, outlines):
    '''
        add outlines given by a list of entries [title, page number, level]

        return number of outlines added

        `exclude_invalid`: exclude invalid outline
            which refer to page out of writer
    '''
    numpages=writer.getNumPages()

    parents=[]
    parent=None
    level_now=-1
    n=0
    for title, page, level in outlines:
        if page>numpages-1:
            continue

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

# write to text
def write_outline_to_txt(fname, outlines):
    '''
        write a outline list to a text file
    '''
    with open(fname, 'w') as f:
        for title, page, level in outlines:
            f.write('%s %iL%i\n' % (title, page, level))