# LocalizationTool

![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/yurisizuku/reversetool?color=green&label=LocalizationTool)![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/YuriSizuku/LocalizationTool/build_pyexe.yml?label=pyexe)  

This project is seperated from my [ReverseTool](https://github.com/YuriSizuku/ReverseTool)  
See also, [GalgameReverse](https://github.com/YuriSizuku/GalgameReverse)

## Cross scripts and libraries

* `libbintext.py`, for text exporting and importing, checking
* `libscenario.py`, some matching and statistic method for text  
* `libfont.py`, for extracting, building tile font, or generating font picture.  
* `libtexture.py`, something about texture and picture convert
* `ftext.py`, convert the `ftext` format made by `bintext.py`  
* `codepage.py`, convert some strings encoding in  file  

## Windows scripts and libraries

* `winconsole.js`,  Allocate a console for game  
* `winfile.js` , view information for both `CreateFile`, `ReadFile`, `WriteFile`, `fopen`,`fread`, `fwrite`  
* `winredirect.js`, redirect font, codepage, and paths in games  
