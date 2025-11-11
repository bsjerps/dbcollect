#!/usr/bin/env python
"""
awrstrip.py - Strip SQL text from html formatted Oracle AWR reports
Copyright (c) 2025 - Bart Sjerps <bart@dirty-cache.com>
License: GPLv3+

The SQL sections are replaced with a 'removed' message.
The files must be valid html files and have .html as extension,
other files will be ignored.
Sections to be removed:
* Top SQL tables (SQL Ordered by ...)
* Complete list of SQL text
* ADDM report
"""

import os, sys, re, logging
from lib.errors import Errors

try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree as etree

_deleted = 'Section removed by awrstrip'

def awrstrip(path, out=None, inplace=False):
    """Strip a html formatted AWR report from sections containing SQL text.
    The ADDM report is also removed as it also often contains SQL code.

    Parameters:
    path: file to be processed (must be valid html)
    out: path to save file as (not saved if none)
    inplace: save to same file if True

    Returns:
    None
    """
    if 'lxml' not in sys.modules:
        logging.debug('python-lxml package not found, fallback to slower xml package')
    try:
        tree = etree.parse(path)
    except etree.ParseError:
        logging.error(Errors.E006, path)
        return
    blacklist = []
    try:
        tree_iter = tree.iter
    except Exception:
        # Need this on Python 2.6
        tree_iter = tree.getiterator
    for element in tree_iter():
        if element.tag == 'table':
            # Look for tables with 'SQL' in the 'summary' attribute
            summary = element.get('summary')
            if summary:
                if re.search(r"top sql|sql statements", summary, re.I):
                    #logging.debug('removing table "%s"', summary.replace('\n',''))
                    blacklist.append(element)
        elif element.tag == 'pre':
            # Look for a separate <pre> section starting with ADDM
            if element.text and element.text.strip().startswith('ADDM'):
                #logging.debug('removing section "ADDM Report"')
                blacklist.append(element)
    changed = False
    for elem in blacklist:
        changed = True
        elem.clear()
        elem.tag = 'h3'
        elem.text = _deleted
    if inplace is True:
        out = path
    if out and changed:
        try:
            tree.write(out, encoding="utf-8")
        except IOError as err:
            logging.error(Errors.E007, out, os.strerror(err.errno))
