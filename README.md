# LocalizationTool

![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/yurisizuku/reversetool?color=green&label=LocalizationTool) ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/YuriSizuku/LocalizationTool/build_pyexe.yml?label=pyexe)  

🍀 General localization tools for galgame, seperated from my [ReverseTool](https://github.com/YuriSizuku/ReverseTool)  
See also, [GalgameReverse](https://github.com/YuriSizuku/GalgameReverse) for specific galgames.  

## Components

### cross platfrom libraries

* `libutil.py`, basic serilization functions for ftext and tbl  
* `libtext.py`, for text exporting and importing, checking
* `libfont.py`, for extracting, building tile font, or generating font picture.
* `libimage.py`, something about texture and picture convert  
* `libalg.py`, some matching and statistic method for text  
* `ftextcvt.py`, convert the `ftext` format made by `bintext.py`  
* `ftextpack.py`, method for packing `ftext` in a bin file with lower memory  

### windows platform libraries

* `winconsole.js`,  allocate a console for game  
* `winfile.js` , view information for both `CreateFile`, `ReadFile`, `WriteFile`, `fopen`,`fread`, `fwrite`  
* `winredirect.js`, redirect font, codepage, and paths in games  

## CLI Example

Using ">" to load or save files in zip, such as `path1/file1.zip>path2/file2`
For these examples, you need `mkdir -p project/pyexe_bintext/build` before.  

### bintext

You can also replace `python src/libtext.py` with `cbintext.exe` in command line.  

```shell

# insert ftext (save direct or in gz file)
python src/libtext.py insert test/sample/COM001 test/sample/COM001.txt --refer test/sample/COM001 -t test/sample/COM001.tbl -o project/pyexe_bintext/build/COM001_rebuild.bin --log_level info --bytes_padding "2020" --bytes_fallback "815A" --insert_shorter --insert_longer  --text_replace "季" "季季季" --text_replace "煌びやかな光" "你你你你你" 
python src/libtext.py insert test/sample/COM001 test/sample/COM001.txt --refer test/sample/COM001 -t test/sample/COM001.tbl -o project/pyexe_bintext/build/COM001_rebuild.bin.gz --log_level info

# extract ftext from bin file (save direct or in zip file)
python src/libtext.py extract project/pyexe_bintext/build/COM001_rebuild.bin -o project/pyexe_bintext/build/COM001_rebuild.txt --log_level info -e sjis --has_cjk --min_len 4 --skip 0x16 --size 1024
python src/libtext.py extract project/pyexe_bintext/build/COM001_rebuild.bin -o "project/pyexe_bintext/build/COM001.zip>COM001/COM001_rebuild.txt" --log_level info -e sjis --has_cjk --min_len 4 --skip 0x16 --size 1024

# check ftext (direct or in zip file)
python src/libtext.py check project/pyexe_bintext/build/COM001_rebuild.txt --refer project/pyexe_bintext/build/COM001_rebuild.bin -o "project/pyexe_bintext/build/COM001_rebuild_check.txt" --log_level info -e sjis
python src/libtext.py check "project/pyexe_bintext/build/COM001.zip>COM001/COM001_rebuild.txt" --refer project/pyexe_bintext/build/COM001_rebuild.bin -o "project/pyexe_bintext/build/COM001.zip>COM001/COM001_rebuild_check.txt" --log_level info -e sjis
```

### ftextpack

```shell
# pack both of origin and new text in fp01 file
python src/ftextpack.py test/sample/COM001 test/sample/COM001.txt -o project/pyexe_bintext/build/COM001.fp01 -t test/sample/COM001.tbl --pack_org

# pack compact mode in zip file
python src/ftextpack.py test/sample/COM001 test/sample/COM001.txt -o "project/pyexe_bintext/build/COM001.zip>COM001/COM001.fp01" -t test/sample/COM001.tbl --pack_compact
```

### ftextcvt

``` shell
# json convert
python src/ftextcvt.py test/sample/COM001.txt -o project/pyexe_bintext/build/COM001.json
python src/ftextcvt.py project/pyexe_bintext/build/COM001.json -o project/pyexe_bintext/build/COM001.json.txt

# csv convert
python src/ftextcvt.py test/sample/COM001.txt -o project/pyexe_bintext/build/COM001.csv
python src/ftextcvt.py project/pyexe_bintext/build/COM001.csv -o project/pyexe_bintext/build/COM001.csv.txt

# docx convert
python src/ftextcvt.py test/sample/COM001.txt -o project/pyexe_bintext/build/COM001.docx
python src/ftextcvt.py project/pyexe_bintext/build/COM001.docx -o project/pyexe_bintext/build/COM001.docx.txt

# pretty ftext format
python src/ftextcvt.py project/pyexe_bintext/build/COM001.json.txt -o project/pyexe_bintext/build/COM001.json.txt

```

## File Formats

### ftext (translation format text)  

The ftext files are using `utf-8 unix lf` format to store. In the ftexts,  we use `●num|addr|size● org_text` for origin text reference and `○num|addr|size○ trans_text` for translation text edit.  Do not modify the index information within `●` or `○`, and must leave a space after `●` or `○`.  

Inside the ftext, `\r` and `\n` are replaced to `[\r]` and `[\n]`. We also use `{{}}` for input some custom formats or informations to process.  

``` shell
# ftext example  
○00002|00018D|04C○ 湧き出る温泉と豊かな自然に包まれた風光明媚な地で、知る人ぞ知る観光地である。
●00002|00018D|04C● 此地温泉涌流，自然繁茂，风光明媚。可谓是内行人都知晓的胜地。

○00003|0001FD|00A○ 季節は夏。
●00003|0001FD|00A● 时值夏日。{{b'\xff'}}

○00004|000253|068○ 残月島にある唯一の街\n『@r紅霞市（こうかし）@0』では、ここ最近の不況が嘘のように盛り上がりを見せていた。
●00004|000253|068● 在残月岛{{'唯一'.encoding('sjis')}}的市区“@r红霞市@0”里，近来经济之萧条每况愈下，已是人心惶惶。

○00005|000307|056○ 『@r花柳街（かりゅうがい）@0』の一郭に存在する置屋に、上流階級のお客様が現れたからだ。
●00005|000307|056● 因为有上流社会的客人来到了@r花柳街@0某郭的置屋。

○00006|000381|032○ ――今、煌びやかな光の中を一人の美しい女性が往く。
●00006|000381|032● ――此刻，正有一位美丽的女性，身披华光，款款行来。
```

### fpack (translation format text pack, ftextpack)  

Packing ftext files into a bin file, for optimizing the memory usage.  Usually use `ftextpack.py` to pack ftext files and `ftextpack.h` to search ftext in the game dynamic translation.  

### tbl (translation word encoding table)  

In the format of `tcode=tchar`, usally used for custom codepage and glphy mapping.  

```shell
8140=　
8141=、
8142=。
8143=，
8144=．
8145=・
8146=：
8147=；
8148=？
8149=！
814A=゛
814B=゜
814C=´
814D=｀
212F=¨
```

## History

* `binary_text.py` -> `bintext.py` -> `libbintext.py` -> `libtext.py`  

``` python
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

* `futil.py` -> `libfont.py`
* `texture.py` -> `libtexture.py` -> `libimage.py`
* `text.py` -> `librawtext.py` -> `libscenario.py` -> `libalg.py`  

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
