#!/usr/bin/env python3

'''
class to handle outline
'''

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

    # to list
    def iter_flatten(self, level=0):
        '''
            convert to a flatten list
                each entry with format, (title, page, level)

            Paremeter:
                level: int
                    initial level
        '''
        for entry in self.iter_flatten_of_children(level+1):
            yield entry
