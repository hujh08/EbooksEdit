#!/usr/bin/env python3

'''
Functions for PDF file
'''

from .funcs_rw import open_pdf_as_reader, new_writer, write_pdf_to
from .funcs_page import page_clean_annots, page_resize, add_blank_pages_after
from .funcs_outline import get_outlines_from_reader, add_outlines, get_outlines_from_txt
from .funcs_pagelabel import (get_pagelabels_from_reader, add_pagelabels,
                              add_pagelabel_head, add_pagelabel_extras)
from .funcs_path import ext_elements_by_range

# pdf copy
def copy_pdf(pdf_old, pdf_new=None, writer=None, page_range=None, 
                keep_annots=False, keep_outlines=True, keep_pagelabels=True,
                pagesize=None, pagescale=None, keep_ratio=True,
                strict=False, **kwargs):
    '''
        copy a pdf

        page_range must be given with one_started=True and keep_end=True
    '''
    reader=open_pdf_as_reader(pdf_old, strict=strict, **kwargs)
    nump=reader.getNumPages()

    pages=range(nump)
    if page_range is not None:
        pages=ext_elements_by_range(pages, ele_range=page_range, one_started=True, keep_end=True)
    # print('number of pages in pdf: %i' % len(pages))

    # copy pages from reader
    if writer is None:
        writer=new_writer()
    page_shift=writer.getNumPages()  # in case for not empty writer

    n_annots=0
    print('to copy %i pages' % len(pages))
    for i in pages:
        print('add page', i+1)
        page=reader.getPage(i)

        if not keep_annots:
            n=page_clean_annots(page)
            n_annots+=n

            if n:
                print('    del %i annots in page %i' % (n, i+1))

        if pagesize is not None or pagescale is not None:
            page_resize(page, pagesize, pagescale, keep_ratio)

        writer.addPage(page)

    if not keep_annots:
        print('del %i annots in total' % n_annots)

    # outline
    if keep_outlines:
        outlines=get_outlines_from_reader(reader, page_shift=page_shift)
        n=add_outlines(writer, outlines)
        print('add %i outlines' % n)

    # page labels
    if keep_pagelabels:
        pagelabels=get_pagelabels_from_reader(reader, page_shift=page_shift)
        n=add_pagelabels(writer, pagelabels)
        print('add %i pagelabels' % n)

    # write
    if pdf_new is None:
        return writer

    write_pdf_to(pdf_new, writer)

# merge PDF files
def merge_pdfs(pdfs, pdf_new=None, writer=None,
                keep_outlines=False, keep_pagelabels=False, **kwargs):
    '''
        merge multiply of PDF files

        element in `pdfs` could a file name or array [file name, page_range]
    '''
    if writer is None:
        writer=new_writer()

    for fname in pdfs:
        kw=kwargs.copy()

        if type(fname) is not str:
            fname, page_range=fname
            kw['page_range']=page_range  # cover the global set in kwargs

        print('==== merge pdf %s ====' % fname)
        copy_pdf(fname, writer=writer, keep_outlines=keep_outlines,
                                       keep_pagelabels=keep_pagelabels, **kw)
        print()

    # write
    if pdf_new is None:
        return writer

    write_pdf_to(pdf_new, writer)

# frequently used functions
def pdf_edit_headlabel_outline(pdf_old, pdf_new=None, num_headpage=0, foutline=None,
                                blank_pages=None, keep_annots=False,
                                extra_pages=None,
                                **kwargs):
    '''
        edit a pdf file, adding page label to head pages and adding outlines
    '''
    writer=copy_pdf(pdf_old, keep_annots=keep_annots,
                             keep_outlines=False,
                             keep_pagelabels=False)

    if blank_pages is not None:
        n=add_blank_pages_after(writer, blank_pages)
        print('add %i blank pages' % n)

    # page label
    if num_headpage>0:
        n=add_pagelabel_head(writer, num_headpage)
        print('add head page labels', n)

    if extra_pages is not None:
        print('add extra page labels:', extra_pages)
        add_pagelabel_extras(writer, extra_pages, num_head=num_headpage)

    # outline
    if foutline is not None:
        outlines=get_outlines_from_txt(foutline, offset=num_headpage,
                                            extra_pages=extra_pages, **kwargs)

        n=add_outlines(writer, outlines)
        print('add %i outlines' % n)

    # write
    if pdf_new is None:
        return writer

    write_pdf_to(pdf_new, writer)