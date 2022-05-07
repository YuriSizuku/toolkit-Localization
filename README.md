# ReverseUtil
There are my tools for reversing.  

The building example is in `./vsproject`.  As the visual studio doesn't support x64 `inline asm`, if you want to build for x64, please use clang.

## UTIL scripts

* `bintext.py`, for text exporting and importing, checking  
* `libfont.py`, for extracting, building tile font, or generating font picture.  
* `libtext.py`, some  matching and statistic method for text  
* `texture.py`, something about texture and picture convert  
* `listmagic.py`, list the files magic to analyze  
* `textconvert.py`, convert the encoding of text file  
* `shellcode.py`, some method for generating shellcode, such as parsing `coff` object file

## windows tools

* `win_injectdll.py` , staticly inject  `dll` to a `exe`  
* `win_console.js`,  Allocate a console for game  
* `win_file.js` , view information for both `CreateFile`, `ReadFile`, `WriteFile`, `fopen`,`fread`, `fwrite`  
* `win_redirect.js`, redirect font, codepage, and paths in games  
* `winhook.h`,  single file for dynamic hook functions, such as IAT hook, inline hook  
* `winpe.h`, single file for parsing windows PE structure, adjust RELOC, ADDRS, or IAT  
* `bintext.h`, parser for `ftext` by `bintext.py`  
