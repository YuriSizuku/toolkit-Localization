build_pysrc()
{
    src_dir=$1
    dst_dir=$2
    module_name=$3
    module_ver=$(python -c "import sys, os; sys.path.append(r'$src_dir'); from $module_name import __version__ as v; print(v)")
    echo build ${module_name}_v${module_ver}.py
    cp -f $src_dir/${module_name}.py $dst_dir/${module_name}_v${module_ver}.py
}

if ! [ -d build ]; then mkdir build; fi

build_pysrc ../../src ./build libutil
build_pysrc ../../src ./build libtext
build_pysrc ../../src ./build libfont
build_pysrc ../../src ./build libimage
build_pysrc ../../src ./build libword
build_pysrc ../../src ./build ftextcvt
build_pysrc ../../src ./build ftextpack
