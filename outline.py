#!/usr/bin/env python3

'''
class to handle outline
'''

import re

class OutlineEntry:
    '''
        class for one outline entry
    '''
    def __init__(self, title, page, parent, children=[]):
        '''
            parent: None, or `OutlineEntry`
                parent of this entry

            children: list of `OutlineEntry`
                children
        '''
        self.title=title
        self.page=page

        self.parent=parent

        self.children=[]
        if children:
            self.add_children(children)

    # some properties
    @property
    def last_child(self):
        return self.children[-1]

    # children
    def add_child(self, *child):
        if len(child)<=1:
            if isinstance(child, OutlineEntry):
                self.children.append(child[0])
            else:
                self.add_child_from_page(*child[0])
        else:
            self.add_child_from_page(*child)

    def add_child_from_page(self, title, page):
        '''
            add child for given (title, page)
        '''
        entry=OutlineEntry(title, page, self)
        self.children.append(entry)

    def add_children(self, children):
        for child in children:
            self.add_child(child)

    ## from PDF reader outlines
    def add_children_from_pdfreader_outlines(self, outlines):
        '''
            load outline from pdf reader outline struture
                which is nested layout
        '''
        for entry in outlines:
            if '/Title' in entry:
                title=entry['/Title']
                page=entry.page.pdf.getDestinationPageNumber(entry)
                self.add_child_from_page(title, page)
                continue

            self.last_child.add_children_from_pdfreader_outlines(entry)

    # to list
    ## list flattenly
    def iter_flatten(self, level=0):
        '''
            convert to a flatten list
                each entry with format, (title, page, level)

            Paremeter:
                level: int
                    initial level
        '''
        yield self.title, self.page, level
        for entry in self.iter_flatten_of_children(level+1):
            yield entry

    def iter_flatten_of_children(self, level=0):
        '''
            list children
        '''
        for child in self.children:
            for entry in child.iter_flatten(level):
                yield entry

    ## to nested list
    def to_nested_list(self):
        '''
            convert to nested list, e.g. [(t1, p1), [(t2, p2), (t3, p3)]]
        '''
        result=[(self.title, self.page)]
        if self.children:
            result.append(self.children_to_nested_list())
        return result

    def children_to_nested_list(self):
        '''
            convert children to nested list
        '''
        result=[]
        for child in self.children:
            result.extend(child.to_nested_list())
        return result

    # write to text
    def _write_to_txt_nest(self, f, d0, d1, i):
        '''
            real work of function `write_to_txt_nest`
                in class `Outline`

            next i would be returned

            Parameter:
                d0, d1: str
                    start/end delimiters
                    it could be different, like {, },
                        or same for both , like ======

                i: int
                    id of a delimiter
        '''

        OutlineEntry._write_title_page(f, self.title, self.page)

        i=self._write_children_to_txt_nest(f, d0, d1, i)

        return i

    def _write_children_to_txt_nest(self, f, d0, d1, i):
        '''
            real work of function `write_to_txt_nest`
                in class `Outline`

            write children
        '''
        if self.children:
            i0=i
            i+=1

            f.write('%s quote %i\n' % (d0, i0))

            for c in self.children:
                i=c._write_to_txt_nest(f, d0, d1, i)

            f.write('%s quote %i\n' % (d1, i0))

        return i

    ## auxilliary functions
    @staticmethod
    def str_clean_unprintable(s):
        '''
            remove unprintable chars, like '\x00'
        '''
        return ''.join([i for i in s if i.isprintable()])

    @staticmethod
    def _write_title_page(f, title, page, level=None, indent=False):
        '''
            write (title, page) to f
        '''
        title=OutlineEntry.str_clean_unprintable(title)

        line='%s %i' % (title, page)
        if level is not None:
            line+='L%i' % level

            if indent:
                line=('    '*level)+line

        f.write(line+'\n')

class Outline(OutlineEntry):
    '''
        class to handle outline
    '''
    def __init__(self):
        '''
            root of outline entries
                no title/page/parent
        '''
        self.children=[]

    # add method for children is inherited from `OutlineEntry`

    # read outlines from files: text or pdf

    ## from pdf
    def load_pdf(self, pdfname):
        '''
            read outline from pdf file
        '''
        from PyPDF2 import PdfFileReader
        reader=PdfFileReader(open(pdfname, 'rb'))

        self.load_pdfreader(reader)

    def load_pdfreader(self, reader):
        '''
            read outlines from from PyPDF2 reader
        '''
        outlines=reader.getOutlines()
        self.add_children_from_pdfreader_outlines(outlines)

    ## from text
    def load_level_txt(self, fname, lstrip=True,
                            map_levels={}, parse_sec=False, func_level=None,
                            level_default=0):
        '''
            load text file
                each line has format: title page[L(level)]
                    where
                        level is optional
                            which is given by appending to the page number
                                seperated with letter `L`, ignoring case
                        page is the page number which starts from 1

            Parameter:
                map_levels: dict, list of tuples
                    if dict, e.g. {s: l}
                        for title starting with `s`, level is `l`

                    see method `get_level_parser_from_map` for detail

                parse_sec: bool or int
                    wheter to parse section using `level_parser_sec`

                    if int, parse section
                        and use the integral as `level_shift` in `level_parser_sec`

                    or list of tuples: [(s, l)], [((s1, s2), l)]
                        title starting with `s(1/2)`, level is `l`

                func_level: callable
                    called with `func_level(title, page)`
                        if not sure, return None

                level_default: int, or None
                    default level, if None, use previous level

                    the four parameters,
                        `map_levels`, `parse_sec`, `func_level`, `level_default`,
                    are used in order

                lstrip: bool
                    whether to do left strip to line of outline file
                    left strip will remove spaces at the starting of title

        '''
        # strip
        strip=lambda line: line.rstrip()
        if lstrip:
            strip=lambda line: line.strip()

        # level parsers
        parsers=[]

        ## map of levels
        if map_levels:
            parsers.append(Outline.get_level_parser_from_map(map_levels))

        ## parse_sec
        if isinstance(parse_sec, numbers.Integral):
            func_sec=lambda t, p, l=parse_sec: Outline.level_parser_sec(t, p, l)
            parsers.append(funcs_sec)
        elif parse_sec:
            parsers.append(Outline.level_parser_sec)

        ## func level
        if func_level is not None:
            parsers.append(funcs_sec)

        func_parser=Outline.combine_level_parsers(*parsers)

        ## level default
        if level_default is None:
            # use previous level
            use_default=False
            level_now=None
        else:
            assert isinstance(level_default, numbers.Integral)
            use_default=True
            level_now=level_default

        # load text
        holder=self
        levels=[]
        with open(fname) as f:
            for line in f:
                title, pnumstr=strip(line).rsplit(maxsplit=1)

                # page number, outline level
                page, level=Outline.pagenum_parse(pnumstr)

                # outline level
                if level is None:
                    level=func_parser(title, page)

                    if level is None:
                        level=level_now

                if not use_default:
                    level_now=level

                if level is not None:
                    if not levels:
                        levels.append(level)
                    elif level>levels[-1]:
                        holder=holder.last_child
                        levels.append(level)
                    elif level<levels[-1]:
                        while levels[-1]>level:
                            holder=holder.parent
                            levels.pop()

                        assert levels[-1]==level

                holder.add_child_from_page(title, page)

    def load_nest_txt(self, fname, delimiters=('/*', '*/'), lstrip=True):
        '''
            load nest file
                a group of lines marked with delimiters at head/tail
                    are treated as children of previous entry

            Parameter:
                lstrip: bool
                    whether to do left strip to line of outline file
                    left strip will remove spaces at the starting of title
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

        # load text
        holder=None
        at_head=True

        with open(fname) as f:
            for line in f:
                lsline=line.lstrip()
                if lsline.startswith(d0):
                    if holder is None and at_head:
                        holder=self
                        at_head=False
                    else:
                        holder=holder.last_child
                elif lsline.startswith(d1):
                    if isinstance(holder, Outline):
                        holder=None
                    else:
                        holder=holder.parent
                else:
                    # delimiter at head could be missed
                    if holder is None and at_head:
                        holder=self
                        at_head=False

                    title, page=strip(line).rsplit(maxsplit=1)
                    page=int(page)

                    holder.add_child_from_page(title, page)

    def load_indent_txt(self, fname):
        '''
            load indented text
                structure of outlines is marked from indentation, just as Python
        '''
        raise Exception('to implement later')

    ### auxilliary functions
    @staticmethod
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

    @staticmethod
    def level_parser_sec(title, page, level_shfit=0):
        '''
            parse level from the section id
                which is given by like 1.1 for level 1

            Parameter:
                level_shift: int
                    level shift,
                        that means level of e.g. 1.1 is 1+`level_shift`
        '''
        sec, *_=title.split(maxsplit=1)
        m=re.search(r'([\dIVX]+(\.\d+)*)', sec)
        if m:
            return len(m.groups()[0].split('.'))-1+level_shfit

        return None

    @staticmethod
    def get_level_parser_from_map(map_levels):
        '''
            get a level parser which is based on a map from title starting to level
        '''
        if str(map_levels) is not dict:
            # if not dict, must be [(list of strings, level)]
            level_list=map_levels
            map_levels={}
            for names, level in level_list:
                if type(names) is not str:
                    for n in names:
                        map_levels[n]=level
                else:
                    map_levels[names]=level

        def parser(title, page):
            starting=title.split(maxsplit=1)[0]
            if starting in map_levels:
                return map_levels[starting]
            return None

        return parser

    @staticmethod
    def combine_level_parsers(*parsers):
        '''
            combine a list of parsers
        '''
        def parser(title, page):
            for f in parsers:
                level=f(title, page)

                if level is not None:
                    return level

            return None

        return parser

    # to list
    ## list flattenly
    def iter_flatten(self, level=0):
        '''
            convert to a flatten list
                each entry with format, (title, page, level)

            Paremeter:
                level: int
                    initial level
        '''
        for entry in self.iter_flatten_of_children(level):
            yield entry

    def to_flatten_list(self):
        '''
            convert to flatten list
        '''
        return list(self.iter_flatten())

    ## to nested list
    def to_nested_list(self):
        '''
            convert to nested list, e.g. [(t1, p1), [(t2, p2), (t3, p3)]]
        '''
        return self.children_to_nested_list()

    # write to text
    def write_to_txt_flatten(self, fname, indent=False):
        '''
            write to text file in a flatten way
        '''
        with open(fname, 'w') as f:
            for t, p, l in self.iter_flatten():
                OutlineEntry._write_title_page(f, t, p, l, indent=indent)

    def write_to_txt_nest(self, fname, delimiters=('/*', '*/')):
        '''
            write to text file in a nest way

            real work is `_write_to_txt_nest`,
                implemented in class `OutlineEntry`
        '''
        if type(delimiters) is str:
            d0=d1=delimiters
        else:
            d0, d1=delimiters

        with open(fname, 'w') as f:
            self._write_children_to_txt_nest(f, d0, d1, 0)

