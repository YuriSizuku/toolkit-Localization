# History

* `libtext.py`  

``` python
# `binary_text.py` -> `bintext.py` -> `libbintext.py` ->
v0.1, initial version with utf-8 support
v0.2, added tbl and decodetbl, encodetbl, check with tbl
v0.3, added extractsjis, extract by tbl or arbitary extract implement, patch using tbl
v0.3.1, added punctuation cjk, added try in decode
v0.3.2, fixed patched error when short than origin 
v0.3.3, change the merge function with matching "●(.*)●[ ](.*)"
v0.4, add read_format_text, write_format_text, optimize the code structure
v0.4.1, fixed merge_text in this optimized the code structure
v0.4.2, remove useless callbacks, adjust default len, add arbitary encoding, add jump_table rebuild, 
v0.4.3, change the structure, write_format_text, read_format_text added line_texts mode
v0.4.4, adding padding char if text shorter than origin (in order with \x0d, \x0a, zeros will stop str), 
v0.4.5, fix the padding problem, --padding bytes 32 00
v0.5, add verify text, shift addr function
v0.5.1, fix the problem of other encoding tbl; read_format_text regex in lazy mode.
v0.5.2, add replace_map in patch_text
v0.5.3, add serach replace text mode by --search_file
v0.5.4, add extraxt --start, --end parameter
v0.5.5, add extract_unicode for 0x2 aligned unicode
v0.5.6, add typing hint and prepare read lines for pyscript in web
v0.5.7, add repalced map in check method, fix -e in check 
v0.5.8, add f_extension for {{}}, f_adjust in patch_text, and align for patch
v0.6, remake to increase speed and simplify functions
```

* `libfont.py`

```shell
# `futil.py` ->
```

* `libimage.py`

``` shell
# `texture.py` -> `libtexture.py` -> 
v0.1, initial version with RGBA8888， RGB332 convert
v0.1.1, added BGR mode
v0.2, add swizzle method
v0.2.1, change cv2 to PIL.image
v0.3, remake with libutil v0.6, accelerate by numba parallel
```

* `libword.py`

```shell
# `text.py` -> `librawtext.py` -> `libscenario.py` -> 

```

* `ftextpack.py`

```shell
v0.1, initial version with data.fp01
v0.1.1, add allow_compat for smaller memory use
v0.2, remake according to libtext v0.6
```

* `ftextcvt.py`

```shell
v0.1, initial version with formatftext, docx2ftext, ftext2docx
v0.2, add support for csv and json, compatiable with paratranz.cn
v0.3, remake according to libtext v0.6
```
