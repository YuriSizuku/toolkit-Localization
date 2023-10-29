# ReverseTool

![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/yurisizuku/reversetool?color=green&label=ReverseTool)![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/YuriSizuku/ReverseTool/build_wintools.yml?label=build_wintools)  
There are my tools for reversing.  
The building example is in `./project`,  
as well as `Makefile` for `tcc`, `gcc` and `clang`.  

## Cross scripts and libraries

* `libbintext.py`, for text exporting and importing, checking
* `librawtext.py`, some matching and statistic method for text  
* `libfont.py`, for extracting, building tile font, or generating font picture.  
* `libtexture.py`, something about texture and picture convert
* `libshellcode.py`, some method for generating shellcode, such as parsing `coff` object file  
* `ftext.py`, convert the `ftext` format made by `bintext.py`  
* `codepage.py`, convert some strings encoding in  file  

## Windows scripts and libraries

* `winhook.h`,  single file for dynamic hook functions, such as IAT hook, inline hook  
* `winpe.h`, single file for parsing windows PE structure, adjust RELOC, ADDRS, or IAT  
* `windllin.py` , pre inject  `dll` to a `exe`  
* `winconsole.js`,  Allocate a console for game  
* `winfile.js` , view information for both `CreateFile`, `ReadFile`, `WriteFile`, `fopen`,`fread`, `fwrite`  
* `winredirect.js`, redirect font, codepage, and paths in games  

## Windows Useful tools

* `win.c`, a tool to start a exe with a `dll` injected, see [Release](https://github.com/YuriSizuku/ReverseUtil/releases)  
