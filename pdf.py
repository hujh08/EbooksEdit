#!/usr/bin/env python3

'''
class to handle pdf operations
'''

from PyPDF2 import PdfFileReader, PdfFileWriter

class PDFEditor:
    '''
        class to handle pdf operations
    '''
    def __init__(self, pdfname=None):
        '''
            open a pdf file and initiate a writer
        '''
        self.writer=PdfFileWriter()

        if pdfname is not None:
            self.load_pdf(pdfname)

    # copy pdf pages
    def load_pdf(self, pdfname):
        '''
            load pdf file
        '''
        reader=PdfFileReader(open(pdfname, 'rb'))
        nump=reader.getNumPages()

        for i in range(nump):
            page=reader.getPage(i)
            self.writer.addPage(page)

    # annotation
    def clean_annots(self):
        '''
            clean annots in all pages
        '''
        nump=self.writer.getNumPages()

        for i in range(nump):
            page=self.writer.getPage(i) 

            if '/Annots' in page:
                del page['/Annots']

    # save
    def save_to(self, fname):
        with open(fname, 'wb') as f:
            self.writer.write(f)