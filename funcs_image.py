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
from .funcs_path import list_files_by_range_fmt

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
def yield_fitz_pages_from_pdf(pdfname, page_range=None, page_mode=False):
    '''
        return page number and page
    '''
    pdf=fitz.open(pdfname)

    pages=range(len(pdf))

    if page_range is not None:
        pages=ext_elements_in_range(pages, page_range, page_mode=page_mode)

    for p in pages:
        i=p
        if page_mode:
            i+=1
        yield i, pdf[p]

# write functions
def write_page_to_file(page, fname):
    page_to_image(page, write_to_file=fname)

def write_pdf_to_dir_image(pdfname, dir_image='pages',
                            fname_format='page-%i.png', page_range=None, page_mode=True):
    '''
        extract pages in a PDF to a directory
    '''
    if not os.path.exists(dir_image):
        os.mkdir(dir_image)

    # format for image file name
    f=lambda p, fmt=fname_format: fmt % p

    for i, page in yield_fitz_pages_from_pdf(pdfname, page_range=page_range, page_mode=page_mode):
        fname=os.path.join(dir_image, f(i))
        print('write to %s' % fname)

        write_page_to_file(page, fname)

# create pdf from images or other pdf
def mkpdf_from_images(pdf_out, images, pagesize='a4', page_scale=1, **kwargs):
    '''
        make pdf from pages

        optional keyword arguments:
            page_range
            page_mode
            fname_format
    '''
    if type(pagesize) is str:
        pagesize=getattr(PageSizes, pagesize.upper())

    if page_scale!=1:
        # rescale the page size
        pagesize=tuple([t*page_scale for t in pagesize])

    c=canvas.Canvas(pdf_out, pagesize=pagesize)

    for i, p in enumerate(yield_images(images, page_range=page_range)):
        if type(p) is str:
            print('add page %i: %s' % (i+1, p))
        else:
            print('add page', i+1)

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
def yield_images(images, **kwargs):
    '''
        yield images from list, directory or PDF
    '''
    if type(images) is str:
        if os.path.isdir(images):
            func=yield_images_from_dir
        else:
            func=yield_images_from_pdf
    else:
        func=yield_images_from_list

    for p in func(images, **kwargs):
        yield p

def yield_images_from_list(images, page_range=None):
    '''
        yield PIL image from list
    '''
    if page_range is not None:
        images=ext_elements_in_range(images, page_range)
        
    for img in images:
        yield img

def yield_images_from_pdf(pdfname, page_mode=True, **kwargs):
    '''
        yield PIL image from PDF file
    '''
    for _, page in yield_fitz_pages_from_pdf(pdfname, page_mode=page_mode, **kwargs):
        yield page_to_image(page)

def yield_images_from_dir(dir_images, **kwargs):
    for fname in list_files_by_range_fmt(dir_images, **kwargs):
        yield fname

# image operations
## crop image
def crop_image(img, *args):
    '''
        `left, upper, width, height` are given as a ratio to the image size
            generally ranging from 0 to 1
    '''
    if len(args)==1:
        left, right, upper, lower=args[0]
    elif len(args)==2:
        (left, right), (upper, lower)=args
    else:
        left, right, upper, lower=args

    w, h=img.size


    left=w*left
    upper=h*upper

    right=w*right
    lower=h*lower

    # width=w*width
    # height=h*height

    # right=left+width
    # lower=upper+height

    return img.crop(box=(left, upper, right, lower))

def split_images_horizontal(dir_images, page_range=None, dir_out=None,
                prefix_fmt='page-%i', prefix_out_fmt='crop-%i', fig_suffix='.png'):
    '''
        split each page in a directory `dir_images` within in range `page_range`
            equally into 2 parts in horizontal direction
    '''
    if dir_out is None:
        dir_out=dir_images

    if not os.path.exists(dir_out):
        os.mkdir(dir_out)

    fnames=list_files_by_range_fmt(dir_images, page_range=page_range,
                    fname_format=(prefix_fmt+fig_suffix))

    ncrop=1
    for fname in fnames:
        print('split', fname)
        img=Image.open(fname)

        outfname=os.path.join(dir_out,  (prefix_out_fmt  % ncrop)+fig_suffix)
        crop=crop_image(img, 0, 0.5, 0, 1)
        crop.save(outfname)
        ncrop+=1

        outfname=os.path.join(dir_out,  (prefix_out_fmt  % ncrop)+fig_suffix)
        crop=crop_image(img, 0.5, 1, 0, 1)
        crop.save(outfname)
        ncrop+=1

