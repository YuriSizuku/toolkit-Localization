for fpath in `ls $(dirname $0)/build/*_v*.py`; do
   echo "## test $fpath"
   python $fpath -h 1>/dev/null
done