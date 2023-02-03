Tools to edit ebooks

# Introduction
Motivation of this toolkit is that some ebooks, e.g. downloaded from [Library Genesis](http://libgen.rs/), have some flaws for reading, for example no bookmarks. Tools here are designed to fix these flaws. Currently implemented tasks include adding bookmarks, editing page labels, removing annotations, changing page size and so on

# Required Library
PyPDF2
PyMuPDF
reportlab
cnocr

# Error solution

## fitz
`pip3 install pymupdf`

# ele_range
`ele_range` is a frequently used argument to specify multiply elements in a array-like object, like pages in pdf, files in directory and indices for regular array.

Argument `ele_range` here could be given with integral, list/tuple of one/two elements, represented by `p`, `[p]`, `[p0, p1]` respectively.

Each value in `p` and `[p0, p1]` is used to specify an element. For example, `ele_range=1` means a element corresponding to `1`. But there are two kinds of couting system, that are starting from 0 or 1. This only refers to the positive value. This would be specified by a optional keyword argument `one_started`. For `0` and negative, the meaning is of no doubt and argument `one_started` doesn't work for it.

And for `[p0, p1]`, there are also two choices about wheter the end element is kept or not. Key word argument `keep_end` is to specify it. Meanwhile, `p0` and `p1` could be `None`. If so, they means head or tail element respectively.

But `[p]` has different sense. Non-negative value means how many elements at head would be extracted (if `0`, nothing returned) , and negative value means how many elements at tail would be deleted (the left is to be extracted). So argument `one_started` also doesn't work for it.

For different case, there are different conventional meaning of `ele_range`. In the case closer to user, like specify the pages in pdf, `one_started=True` and `keep_end=True` are frequently set. And in case closer to routine, like extracting elements in array constructed by routines, `one_started=False` and `keep_end=False` are always used.

The basic function implementing this protocol is `funcs_path.ext_elements_by_range`

# Task
