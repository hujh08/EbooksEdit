#!/usr/bin/env python3

'''
Functions for PDF file
'''

from .funcs_rw import open_pdf_as_reader, new_writer, write_pdf_to
from .funcs_page import page_clean_annots
from .funcs_outline import get_outlines_from_reader, add_outlines
from .funcs_pagelabel import get_pagelabels_from_reader, add_pagelabels
from .funcs_path import ext_elements_by_range

# pdf copy
def copy_pdf(pdf_old, pdf_new=None, page_range=None,
                keep_annots=False, keep_outlines=True, keep_pagelabels=True):
    '''
        copy a pdf

        page_range must be given with one_started=True and keep_end=True
    '''
    reader=open_pdf_as_reader(pdf_old)
    nump=reader.getNumPages()

    pages=range(nump)
    if page_range is not None:
        pages=ext_elements_by_range(pages, ele_range=page_range, one_started=True, keep_end=True)
    print('number of pages in pdf: %i' % len(pages))

    # copy pages from reader
    writer=new_writer()
    n_annots=0
    print('copy pages:')
    for i in range(nump):
        page=reader.getPage(i)

        if not keep_annots:
            n=page_clean_annots(page)
            n_annots+=n

            print('    del %i annots in page %i' % (n, i))

        writer.addPage(page)

    if not keep_annots:
        print('del %i annots in total' % n_annots)

    # outline
    if keep_outlines:
        outlines=get_outlines_from_reader(reader)
        n=add_outlines(writer, outlines)
        print('add %i outlines' % n)

    # page labels
    if keep_pagelabels:
        pagelabels=get_pagelabels_from_reader(reader)
        n=add_pagelabels(writer, pagelabels)
        print('add %i pagelabels' % n)

    # write
    if pdf_new is None:
        return writer

    write_pdf_to(pdf_new, writer)
