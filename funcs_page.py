#!/usr/bin/env python3

'''
Functions for PDF page

there are two types of page
    one in annotations is from PyPDF2
    one in image converting is from fitz
'''

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
def ext_elements_in_range(array, page_range=None):
    '''
        slice for page range
    '''
    if page_range is None:
        return array

    if isinstance(page_range, numbers.Integral):
        # only a integral
        return array[slice(page_range)]

    return array[slice(*page_range)]
