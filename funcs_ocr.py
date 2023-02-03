#!/usr/bin/env python3

'''
functions for image ocr
'''

import os

import re
import numbers

from cnocr import CnOcr

from .funcs_path import list_files_by_range_fmt

_cnocr=None    # a global ocr
def ocr_image(fname, score=None, lang='en'):
    print('OCR %s' % fname)

    global _cnocr
    if _cnocr is None:
        # if lang=='en':
        #     _cnocr=CnOcr(det_model_name='naive_det', rec_model_name='en_PP-OCRv3')
        # else:
        _cnocr=CnOcr(det_model_name='naive_det')
    
    # text='\n'.join([''.join(data['text']) for data in res])
    lines=[]
    for data in _cnocr.ocr(fname):
        if score is not None and data['score']<score:
            # skip text of too low score
            continue

        lines.append(data['text'])

    text='\n'.join(lines)

    return text

def ocr_images_list(images, fname_out=None):
    '''
        ocr a list of images
    '''
    text=''
    for fname in images:
        text+=ocr_image(fname)+'\n'

    if fname_out is None:
        return text

    with open(fname_out, 'w') as f:
        f.write(text)

def ocr_images_in_dir(dir_images, fname_out=None):
    '''
        ocr images in a directory
    '''
    images=list_files_in_dir(dir_images)
    ocr_images_list(images, fname_out=fname_out)

def ocr_images_by_namefmt(fname_format='page-%i.png', dir_images='pages',
                        page_range=None, fname_out=None):
    '''
        ocr images through list of names with similar format
    '''
    fnames=list_files_by_range_fmt(dir_images=dir_images,
                                   fname_format=fname_format,
                                   page_range=page_range)

    ocr_images_list(fnames, fname_out=fname_out)
