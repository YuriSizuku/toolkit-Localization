# -*- coding: utf-8 -*-
g_description = f"""
A tool to change or adjust ftext
    v0.3, developed by devseed
"""

import os
import codecs
import argparse
import json
from io import StringIO
from csv import DictWriter, DictReader
from docx import Document # pip install python-docx
from docx.shared import Pt
from typing import Union, List, Dict

try:
    from libutil import writelines, savebytes, loadfiles, ftext_t, load_ftext, save_ftext
except ImportError:
    exec("from libutil_v600 import writelines, savebytes, loadfiles, ftext_t, load_ftext, save_ftext")

__version__ = 300

@loadfiles((0, 'utf-8'))
def ftext2pretty(linesobj: Union[str, List[str]], outpath=None) -> List[str]:
    """
    make ftext2 format pretty, and try to fix some problem
    """

    lines = linesobj
    if len(lines) > 0: lines[0] = lines[0].lstrip("\ufeff") # remove bom
    for i, line in enumerate(lines): # try fix break
        indicator = line[0]
        line = line.rstrip('\n').rstrip('\r')
        if indicator=="○" or indicator=="●":
            text_offset = line.find(indicator, 1) + 1
            if text_offset < 0: raise ValueError(f"indicator {indicator} not closed, [lineno={i+1} line='{line}']")
            elif line[text_offset]!=" ": 
                print(f"detect no ' ' [lineno={i} line='{line}']")
                line = line[0: text_offset] + ' ' + line[text_offset:]
        lines[i] =  line + '\n'
    return save_ftext(*load_ftext(lines), outpath)

def ftext2csv(linesobj: Union[str, List[str]], outpath=None) -> List[str]:
    """
    convert ftext2 files to csv format
    tag(org ○, now ●),addr,size,text

    """
    
    ftexts1, ftexts2 = load_ftext(linesobj)
    assert(len(ftexts1) == len(ftexts2))
    sbufio = StringIO()
    wr = DictWriter(sbufio, ["tag", "addr", "size", "text"])
    wr.writeheader() # will automaticaly detect comma, use excel to write csv can not encode as utf8
    for i, (t1, t2) in enumerate(zip(ftexts1, ftexts2)): 
        wr.writerow({"tag": "org", "addr": hex(t1.addr), "size": hex(t1.size), "text": t1.text})
        wr.writerow({"tag": "now", "addr": hex(t2.addr), "size": hex(t2.size), "text": t2.text})
    lines = sbufio.getvalue().splitlines(True)
    sbufio.close()
    if outpath: savebytes(outpath, codecs.BOM_UTF8 + writelines(lines, "utf-8"))
    return lines

def ftext2json(ftextobj: Union[str, List[str]], outpath=None) -> List[str]:
    """
    convert ftext2 to json format
    { 
        "org": {"addr": 0, "size": 0, "text": ""}
        "now" : {"addr": 0, "size": 0, "text": ""}
    }
    """
    
    ftexts1, ftexts2 = load_ftext(ftextobj)
    assert(len(ftexts1) == len(ftexts2))
    jarr: List[Dict[str: str]] = []
    for i, (t1, t2) in enumerate(zip(ftexts1, ftexts2)):
        jarr.append({
            "org": {"addr": hex(t1.addr), "size": hex(t1.size), "text": t1.text}, 
            "now" : {"addr": hex(t2.addr), "size": hex(t2.size), "text": t2.text}
        })
    
    jstr = json.dumps(jarr, ensure_ascii=False, indent=2)
    if outpath: savebytes(outpath, jstr.encode("utf-8"))
    return jstr.splitlines(True)

@loadfiles([(0, "utf-8")])
def ftext2docx(linesobj: Union[str, List[str]], outpath=None) -> Document:
    """
    if this function compiled by nuitka, 
    it needs default.docx file in ./docx/templates
    """

    lines = linesobj
    document = Document()
    for i, line in enumerate(lines):
        line = line.rstrip('\n').rstrip('\r')
        p = document.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(line)
        run.font.name = "SimSun"
        run.font.size = Pt(10.5)
    if outpath: document.save(outpath)
    return document

@loadfiles([(0, "utf-8")])
def csv2ftext(linesobj: Union[str, List[str]], outpath=None) -> List[str]:
    lines = linesobj
    if len(lines) > 0: lines[0] = lines[0].lstrip("\ufeff")
    ftexts1, ftexts2 = [], []
    for i, t in enumerate(DictReader(lines)):
        ftext = None
        try:
            ftext = ftext_t(int(t['addr'], 0), int(t['size'], 0), t['text'])
        except ValueError and TypeError as e: print(f"{repr(e)} [i={i} '{t}']")
        if ftext is None: continue
        if t["tag"]=="org": ftexts1.append(ftext)
        elif t["tag"]=="now": ftexts2.append(ftext)
        else: raise ValueError(f"unknow tag {t['tag']} [i={i} '{t}']")
    assert(len(ftexts1) == len(ftexts2))
    return save_ftext(ftexts1, ftexts2, outpath)

@loadfiles(0)
def json2ftext(binobj: Union[str, List[str]], outpath=None) -> List[str]:
    ftexts1, ftexts2 = [], []
    for i, t in enumerate(json.loads(binobj)):
        if "org" in t:
            t2 = t["org"]
            ftext = ftext_t(int(t2['addr'], 0), int(t2['size'], 0), t2['text'])
            ftexts1.append(ftext)
        if "now" in t:
            t2 = t["now"]
            ftext = ftext_t(int(t2['addr'], 0), int(t2['size'], 0), t2['text'])
            ftexts2.append(ftext)
    assert(len(ftexts1) == len(ftexts2))
    return save_ftext(ftexts1, ftexts2, outpath)

def docx2ftext(docxobj, outpath=None) -> List[str]:
    lines = []
    document = Document(docxobj)
    # text is the whole text, p.run are every str in styles
    for p in document.paragraphs:
        line = p.text.rstrip('\n').rstrip('\r') 
        lines.append(line + '\n')
    if outpath: savebytes(outpath, writelines(lines))
    return lines

def cli(cmdstr=None):
    def cmd_convert():
        flag = False
        if inpath_ext== '.txt': #  ftext to others
            if outpath_ext == '.txt': ftext2pretty(inpath, outpath)
            elif outpath_ext == '.docx': ftext2docx(inpath, outpath)
            elif outpath_ext == '.csv': ftext2csv(inpath, outpath)
            elif outpath_ext == ".json": ftext2json(inpath, outpath)
            else: flag = True
        elif outpath_ext == '.txt': # others to ftext
            if inpath_ext == '.docx': docx2ftext(inpath, outpath)
            elif inpath_ext == '.csv': csv2ftext(inpath, outpath)
            elif inpath_ext == '.json': json2ftext(inpath, outpath)
            else: flag = True
            return
        else: flag = True
        if not flag: return
        raise NotImplementedError(f"convert not support {inpath_ext}->{outpath_ext}")

    parser = argparse.ArgumentParser(description=g_description)
    parser.add_argument("inpath")
    parser.add_argument("-o", "--outpath", default="out.txt")

    args = parser.parse_args(cmdstr.split(' ') if cmdstr else None)
    inpath, outpath = args.inpath, args.outpath
    outpath = outpath if len(outpath) > 0 else None
    inpath_ext = os.path.splitext(inpath)[1].lower()
    outpath_ext = os.path.splitext(outpath)[1].lower()
    cmd_convert()

if __name__ == '__main__':
    cli()

"""
history:
v0.1, initial version with formatftext, docx2ftext, ftext2docx
v0.2, add support for csv and json, compatiable with paratranz.cn
v0.3, remake according to libtext v0.6
"""