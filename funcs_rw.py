#!/usr/bin/env python3

'''
Functions for PDF reader/writer
'''

from PyPDF2 import PdfFileReader, PdfFileWriter

# pdf reader
def open_pdf_as_reader(pdfname):
    '''
        open a pdf file

        return a PyPDF2 reader
    '''
    return PdfFileReader(open(pdfname, 'rb'))

def get_root_of_reader(reader):
    '''
        get the Root object in reader
    '''
    return reader.trailer['/Root']

# writer
def new_writer():
    return PdfFileWriter()

def write_pdf_to(pdfname, writer):
    '''
        save writer to a PDF file
    '''
    with open(pdfname, 'wb') as f:
        writer.write(f)

def get_root_of_writer(writer):
    '''
        get the Root object in writer
    '''
    return writer._root_object

# reader/writer
def get_root_of_rw(rw):
    if isinstance(rw, PdfFileReader):
        return get_root_of_reader(rw)

    if isinstance(rw, PdfFileWriter):
        return get_root_of_writer(rw)

    raise Exception('unexpected type:', type(rw))