#!/usr/bin/env python
"""Module for merging PDFs."""

# Import system libraries
import sys
import os

# Import third party libraries
from PyPDF2 import PdfFileMerger

from tkinter import filedialog as fd


def merge(outFile, inFiles):
    """Function that merges contents of a directory or individually
    specified PDF files into a single file.

    Args:
        outFile (string): Name of the file to output. Should include
        extension.
        inFiles (list of strings): List of paths to files to merge into
        a single pdf or a list containing a single path to a directory
        to merge it's entire contents
        contents
    """
    # TODO Provide exception handling for inputs (calid directory? valid PDFS?)
    if len(inFiles) == 1 and os.path.isdir(inFiles[0]):
        # fileList=os.listdir(inFiles)
        files = [os.path.join(inFiles[0], fileName)
                 for fileName in os.listdir(inFiles[0])]
    else:
        files = inFiles

    merger = PdfFileMerger()

    # TODO Put print statements into a log; write exception for permissions
    # errors
    for pdf in sorted(files):
        print("merging " + pdf + "...")
        merger.append(pdf)

    print("writing output")
    merger.write(outFile)
    print("output written")
    print("closing output")
    merger.close()
    print("output closed")


def main():
    if sys.argv == []:
        merge(sys.argv[1], sys.argv[2:])
    else:
        print("Hello!")
        outputFile = fd.asksaveasfilename()
        inputFile = fd.askopenfilenames()
        merge(outputFile, inputFile)


if __name__ == "__main__":

    main()
