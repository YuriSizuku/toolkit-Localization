test_libtext()
{
    echo "## test libtext insert"
    python src/libtext.py insert test/sample/COM001 test/sample/COM001.txt --refer test/sample/COM001 -t test/sample/COM001.tbl -o project/pysrc_all//build/COM001_rebuild.bin --log_level info --bytes_padding "2020" --bytes_fallback "815A" --insert_shorter --insert_longer  --text_replace "季" "季季季" --text_replace "煌びやかな光" "你你你你你" 
    python src/libtext.py insert test/sample/COM001 test/sample/COM001.txt --refer test/sample/COM001 -t test/sample/COM001.tbl -o project/pysrc_all//build/COM001_rebuild.bin.gz --log_level info

    echo "## test libtext extract"
    python src/libtext.py extract project/pysrc_all//build/COM001_rebuild.bin -o project/pysrc_all//build/COM001_rebuild.txt --log_level info -e sjis --has_cjk --min_len 4 --skip 0x16 --size 1024
    python src/libtext.py extract project/pysrc_all//build/COM001_rebuild.bin -o "project/pysrc_all//build/COM001.zip>COM001/COM001_rebuild.txt" --log_level info -e sjis --has_cjk --min_len 4 --skip 0x16 --size 1024

    echo "## test libtext check"
    python src/libtext.py check project/pysrc_all//build/COM001_rebuild.txt --refer project/pysrc_all//build/COM001_rebuild.bin -o "project/pysrc_all//build/COM001_rebuild_check.txt" --log_level info -e sjis
    python src/libtext.py check "project/pysrc_all//build/COM001.zip>COM001/COM001_rebuild.txt" --refer project/pysrc_all//build/COM001_rebuild.bin -o "project/pysrc_all//build/COM001.zip>COM001/COM001_rebuild_check.txt" --log_level info -e sjis
}

test_libimage()
{
    echo
}

test_libfont()
{
    echo
}

test_libword()
{
    echo
}

test_ftextpack()
{
    echo "## test ftextpack"
    python src/ftextpack.py test/sample/COM001 test/sample/COM001.txt -o project/pysrc_all//build/COM001.fp01 -t test/sample/COM001.tbl --pack_org
    python src/ftextpack.py test/sample/COM001 test/sample/COM001.txt -o "project/pysrc_all//build/COM001.zip>COM001/COM001.fp01" -t test/sample/COM001.tbl --pack_compact
}

test_ftextcvt()
{
    echo "## test ftextcvt"
    python src/ftextcvt.py test/sample/COM001.txt -o project/pysrc_all//build/COM001.json
    python src/ftextcvt.py project/pysrc_all//build/COM001.json -o project/pysrc_all//build/COM001.json.txt
    python src/ftextcvt.py test/sample/COM001.txt -o project/pysrc_all//build/COM001.csv
    python src/ftextcvt.py project/pysrc_all//build/COM001.csv -o project/pysrc_all//build/COM001.csv.txt
    python src/ftextcvt.py test/sample/COM001.txt -o project/pysrc_all//build/COM001.docx
    python src/ftextcvt.py project/pysrc_all//build/COM001.docx -o project/pysrc_all//build/COM001.docx.txt
    python src/ftextcvt.py project/pysrc_all//build/COM001.json.txt -o project/pysrc_all//build/COM001.json.txt
}

test_all()
{
    mkdir -p project/pysrc_all//build
    rm -f project/pysrc_all//build/COM001.zip
    test_libtext
    test_libimage
    test_libfont
    test_libword
    test_ftextpack
    test_ftextcvt
}