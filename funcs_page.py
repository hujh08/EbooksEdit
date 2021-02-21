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
