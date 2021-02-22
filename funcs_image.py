#!/usr/bin/env python3

'''
Functions for PDF related to image

page here is from fitz, unlike others, which are of PyPDF2
    and fitz is contained in module `PyMuPDF`

two libraries used: fitz and reportlab
'''

import os

from io import BytesIO
import re

from PIL import Image

import fitz

from reportlab.lib import pagesizes as PageSizes
# from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from .funcs_page import ext_elements_in_range


# convert page to PIL Image
def page_to_image(page, write_to_file=None, **kwargs):
    '''
        convert page to PIL image or write to a file

        Parameters:
            write_to_file: None or string
                if None, return a PIL image object
                otherwise, specify a file name to write image to
    '''
    pix=page_to_pixmap(page, **kwargs)

    png=pix.getPNGData()

    if write_to_file:
        with open(write_to_file, 'wb') as f:
            f.write(png)
        return
    
    return Image.open(BytesIO(png))

def page_to_pixmap(page, zoomxy=2, alpha=False):
    '''
        convert page to pixel map

        zoom coefficient
        image size by default: 792X612, dpi=96
        zoom_x=1.33333333 # (1.33333333-->1056x816), 1056/792=1.333333
        zoom_y=1.33333333
    '''
    zoom_x=zoom_y=zoomxy
    mat=fitz.Matrix(zoom_x, zoom_y)

    return page.getPixmap(matrix=mat, alpha=alpha)

# fitz page
def yield_fitz_pages_from_pdf(pdfname, page_range=None):
    '''
        return page number and page
    '''
    pdf=fitz.open(pdfname)

    pages=range(len(pdf))

    if page_range is not None:
        pages=ext_elements_in_range(pages, page_range)

    for p in pages:
        yield p, pdf[p]

# write functions
def write_page_to_file(page, fname):
    page_to_image(page, write_to_file=fname)

def write_pdf_to_dir_image(pdfname, dir_image='pages',
                            image_prefix=None, page_range=None):
    '''
        extract pages in a PDF to a directory
    '''
    if not os.path.exists(dir_image):
        os.mkdir(dir_image)

    # format for image file name
    if image_prefix is None:
        # prefix=fname.rsplit('.', maxsplit=1)[0]+'_p'
        image_prefix='page-'
    f=lambda p, pref=image_prefix: pref+('%i.png' % p)

    for i, page in yield_fitz_pages_from_pdf(pdfname, page_range=page_range):
        print('write page:', i+1)

        fname=os.path.join(dir_image, f(i+1))
        write_page_to_file(page, fname)

# create pdf from images or other pdf
def mkpdf_from_images(pdf_out, images, pagesize='a4', page_range=None, page_scale=1):
    '''
        make pdf from pages
    '''
    if type(pagesize) is str:
        pagesize=getattr(PageSizes, pagesize.upper())

    if page_scale!=1:
        # rescale the page size
        pagesize=tuple([t*page_scale for t in pagesize])

    c=canvas.Canvas(pdf_out, pagesize=pagesize)

    for i, p in enumerate(yield_images(images, page_range=page_range)):
        print('add page:', i+1)

        add_image_page(c, p)

        c.showPage()

    c.save()

## auxilliary functions for canvas drawing
def add_image_page(c, img, pagesize='a4'):
    '''
        add image to a pdf canvas

        Parameters:
            c: `canvas.Canvas`
            img: str or PIL Image
    '''
    if type(img) is str:
        img=Image.open(img)

    if type(pagesize) is str:
        pagesize=getattr(PageSizes, pagesize.upper())

    rect=page_draw_region(pagesize, img.size)
    c.drawImage(ImageReader(img), *rect)

def page_draw_region(pagesize, imgsize):
    '''
        determine draw region for an image in the page

        return (left, top, right, bottom)
    '''
    w0, h0=pagesize
    w1, h1=imgsize

    # scale image to page
    scale=min(w0/w1, h0/h1)
    w1*=scale
    h1*=scale

    # determine region
    dw, dh=w0-w1, h0-h1

    left=dw/2
    right=left+w1

    top=dh/2
    bottom=top+h1

    return left, top, right, bottom

## yield images from image name list, image directory or PDF file
def yield_images(images, page_range=None):
    '''
        yield images from list, directory or PDF
    '''
    if type(images) is str:
        if os.path.isdir(images):
            images=read_images_from_dir(images)
            func=yield_images_from_list
        else:
            func=yield_images_from_pdf
    else:
        func=yield_images_from_list

    for p in func(images, page_range):
        yield p

def yield_images_from_list(images, page_range=None):
    '''
        yield PIL image from list
    '''
    if page_range is not None:
        images=ext_elements_in_range(images, page_range)
        
    for img in images:
        if type(img) is str:
            yield Image.open(img)
        else:
            yield img

def yield_images_from_pdf(pdfname, page_range):
    '''
        yield PIL image from PDF file
    '''
    for _, page in yield_fitz_pages_from_pdf(pdfname, page_range):
        yield page_to_image(page)

## load images from directory
def read_images_from_dir(dir_image):
    '''
        read image files from directory
    '''
    pages=os.listdir(dir_image)
    fnames=[os.path.join(dir_image, p) for p in pages]
    if len(fnames)<2:
        return fnames

    # sort list
    ## extract format: ${PREFIX}${NUM}${SUFFIX}
    fmt=re.compile(r'(\D*)(\d*)(.*)')

    p=pages[0]
    PREFIX, num, SUFFIX=fmt.match(p).groups()
    if not num:
        return fnames

    nums=[int(num)]
    samefmt=True
    for p in pages[1:]:
        pref, num, suff=fmt.match(p).groups()
        if (not num) or (pref != PREFIX) or (suff != SUFFIX):
            samefmt=False
            break
        nums.append(int(num))

    if not samefmt:
        return sorted(fnames)

    return [fnames[i] for i in argsort(nums)]

def argsort(array):
    '''
        argsort array
    '''
    inds=list(range(len(array)))
    pairs=list(zip(inds, array))
    return [i for i, _ in sorted(pairs, key=lambda s: s[1])]
