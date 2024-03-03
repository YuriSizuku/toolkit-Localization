for file in `ls build/*_v*.py`; do
   echo "## test $file"
   python $file -h 1>/dev/null
done