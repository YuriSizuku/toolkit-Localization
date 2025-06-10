build_pysrc()
{
    src_dir=$1
    dst_dir=$2
    module_name=$3
    module_ver=$(python -c "import sys, os; sys.path.append(r'$src_dir'); from $module_name import __version__ as v; print(v)")
    module_ver=$(echo $module_ver | sed -E 's/\./_/g')
    echo build ${module_name}_v${module_ver}.py
    cp -f $src_dir/${module_name}.py $dst_dir/${module_name}_v${module_ver}.py
}

mkdir -p $(dirname $0)/build
build_pysrc src $(dirname $0)/build libutil
build_pysrc src $(dirname $0)/build libtext
build_pysrc src $(dirname $0)/build libfont
build_pysrc src $(dirname $0)/build libimage
build_pysrc src $(dirname $0)/build libword
build_pysrc src $(dirname $0)/build ftextcvt
build_pysrc src $(dirname $0)/build ftextpack
