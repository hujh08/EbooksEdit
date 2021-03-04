#!/usr/bin/env python3

'''
Functions for PDF page

there are two types of page
    one in annotations is from PyPDF2
    one in image converting is from fitz
'''

import numbers

from reportlab.lib import pagesizes as PageSizes
# from reportlab.lib.pagesizes import A4

# remove annotations
def page_clean_annots(page):
    '''
        clean annots in page

        return number of annotations deleted
    '''
    if '/Annots' not in page:
        return 0

    n=len(page['/Annots'])
    del page['/Annots']
    
    return n

# page size
def get_pagesize_by_name(pagesize, scale=None):
    '''
        return (w, h) for page size

        support string type, like A4
    '''
    if type(pagesize) is str:
        pagesize=getattr(PageSizes, pagesize.upper())

    if scale is not None:
        # rescale the page size
        w, h=pagesize
        if isinstance(scale, numbers.Number):
            sx=sy=scale
        else:
            sx, sy=scale
        pagesize=(w*sx, h*sy)

    return pagesize

def page_resize(page, pagesize=None, scale=None, keep_ratio=True):
    '''
        scale page

        `keep_ratio`: bool
            if True, keep the ratio of width and height of page while scaling
    '''
    if pagesize is None:
        if scale is None:
            return

        if isinstance(scale, numbers.Number):
            page.scaleBy(float(scale))
        else:
            # scale=(sx, sy), scale in both axes
            page.scale(*scale)

        return

    pagesize=get_pagesize_by_name(pagesize, scale)
    if keep_ratio:
        w0, h0=get_pagesize_of(page)
        w, h=pagesize
        page.scaleBy(min(w/w0, h/h0))
    else:
        page.scaleTo(*pagesize)

def get_pagesize_of(page):
    '''
        get pagesize of an page object
    '''
    x0, y0, x1, y1=page.mediaBox

    return float(x1-x0), float(y1-y0)

# add blank pages
def add_blank_page_after(writer, page):
    '''
        add blank page after `page`

        `page` is an index started from 1
    '''
    writer.insertBlankPage(index=page)

def add_blank_pages_after(writer, pages):
    '''
        add blank page after `page`

        page in `pages` is an index started from 1
    '''
    if isinstance(pages, numbers.Integral):
        # only adding one page
        add_blank_page_after(writer, pages)
        return 1

    for page in sorted(pages, reverse=True):
        add_blank_page_after(writer, page)

    return len(pages)



