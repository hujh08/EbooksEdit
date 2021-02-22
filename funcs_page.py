#!/usr/bin/env python3

'''
Functions for PDF page

there are two types of page
    one in annotations is from PyPDF2
    one in image converting is from fitz
'''

import numbers

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

# page range
def ext_elements_in_range(array, page_range=None,
                            page_mode=False):
    '''
        slice for page range

        if `page_mode` and head-tail both given in `page_range`,
            page range starts from 1 and include the stop index
    '''
    if page_range is None:
        return array

    if isinstance(page_range, numbers.Integral):
        # only a integral
        page_range=[page_range]

    if page_mode and len(page_range)>1:
        p0, p1, *step=page_range[:2]
        if p0>0:  # if negative, keep unchanging
            page_range=(p0-1, p1, *step)

    return array[slice(*page_range)]
