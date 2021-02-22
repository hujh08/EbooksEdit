#!/usr/bin/env python3

'''
Functions for PDF page label
'''

import numbers
import re

import PyPDF2.pdf as PDF

from .funcs_rw import get_root_of_rw

# objects for page label
## named style
_map_style={'roman lowercase': '/r',
            'roman uppercase': '/R',
            'arabic': '/D'}
_alias_style={'roman lowercase': ['roman'],
              'roman uppercase': ['Roman', 'Roman']}
for name, aliases in _alias_style.items():
    s=_map_style[name]
    for a in aliases:
        _map_style[a]=s

def obj_pagelabels(style=None, start=None):
    '''
        object for page label

        Paramters:
            style: string
                specify style of page labels, like Roman or Arabic

            start: optional, None, int
                start page
                if None, use 1
    '''
    # start page
    if start is None:
        start=1

    # style
    global _map_style
    if style in _map_style:
        style=_map_style[style]
    elif style is None:
        style=_map_style['arabic']

    obj=PDF.DictionaryObject()
    obj.update({PDF.NameObject("/S"):PDF.NameObject(style)})
    obj.update({PDF.NameObject("/St"): PDF.NumberObject(start)})
    return obj

def obj_nums_array(page, **kwargs):
    '''
        object for Nums in page labels
    '''
    nums=PDF.ArrayObject()

    nums.append(PDF.NumberObject(page))
    nums.append(obj_pagelabels(**kwargs))

    return nums

# add page label
def add_pagelabel(writer, page, style=None, start=None):
    '''
        add a page label to writer
    '''
    nums_array=locate_pagelabels_in_writer(writer, add_ifnot=True)['/Nums']
    nums_array.extend(obj_nums_array(page, style=style, start=start))

def add_pagelabels(writer, pagelabels):
    '''
        add a list of page labels
    '''
    for page, *ss in pagelabels:
        add_pagelabel(writer, page, *ss)
    return len(pagelabels)

# get page labels
def locate_pagelabels_in_writer(writer, add_ifnot=False):
    '''
        locate the object storing page label in writer

        Parameters:
            add_ifnot: bool
                if True, add an empty page labels structure when not exists
    '''
    root_obj=get_root_of_rw(writer)
    if '/PageLabels' not in root_obj:
        if not add_ifnot:
            return None

        nums_array=PDF.ArrayObject()

        nums_dict=PDF.DictionaryObject()
        nums_dict.update({PDF.NameObject('/Nums'): nums_array})

        labels_dict=PDF.DictionaryObject()
        labels_dict.update({PDF.NameObject('/PageLabels'): nums_dict})

        root_obj.update(labels_dict)

    return root_obj['/PageLabels']

def get_pagelabels_from_reader(reader):
    '''
        get the page label object in PyPDF2 reader

        return a list of page labels, [page, style, start]
    '''
    nums_array=get_root_of_rw(reader)['/PageLabels']['/Nums']

    n=len(nums_array)
    assert n % 2 == 0

    result=[]
    for i in range(0, n, 2):
        page=int(nums_array[i])

        ss=reader.getObject(nums_array[i+1])
        style=str(ss['/S'])

        pagelabel=[page, style]
        result.append(pagelabel)

        if '/St' in ss:
            pagelabel.append(int(ss['/St']))

    return result
