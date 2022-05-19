# ReverseUtil  

![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/yurisizuku/reverseutil?color=green&label=ReverseUtil)![GitHub Workflow Status](https://img.shields.io/github/workflow/status/yurisizuku/reverseutil/build_tools)  
There are my tools for reversing.  
The building example is in `./sln`,  
as well as `Makefile` for `tcc`, `gcc` and `clang`.  

## UTIL scripts and libraries

* `bintext.py`, for text exporting and importing, checking  
* `libfont.py`, for extracting, building tile font, or generating font picture.  
* `libtext.py`, some  matching and statistic method for text  
* `texture.py`, something about texture and picture convert  
* `ftextcvt.py`, convert the `ftext` format made by `bintext.py`  
* `cpcvt.py`, convert some strings encoding in  file  
* `listmagic.py`, list the files magic to analyze  
* `shellcode.py`, some method for generating shellcode, such as parsing `coff` object file  
* `bintext.h`, parser for `ftext` by `bintext.py`  

## Windows scripts and libraries

* `win_injectdll.py` , pre inject  `dll` to a `exe`  
* `win_console.js`,  Allocate a console for game  
* `win_file.js` , view information for both `CreateFile`, `ReadFile`, `WriteFile`, `fopen`,`fread`, `fwrite`  
* `win_redirect.js`, redirect font, codepage, and paths in games   
* `winhook.h`,  single file for dynamic hook functions, such as IAT hook, inline hook  
* `winpe.h`, single file for parsing windows PE structure, adjust RELOC, ADDRS, or IAT  

## Useful tools

* `dllloader.c`, a tool to start a exe with a `dll` injected, see [Release](https://github.com/YuriSizuku/ReverseUtil/releases)  
