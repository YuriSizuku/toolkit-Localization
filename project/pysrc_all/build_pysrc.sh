build_version()
{
    src_dir=$1
    dst_dir=$2
    module_name=$3
    module_ver=$(python -c "import sys, os; sys.path.append(r'$src_dir'); import $module_name as l; print(l.__version__)")
    echo build ${module_name}_v${module_ver}.py
    cp -f $src_dir/${module_name}.py $dst_dir/${module_name}_v${module_ver}.py
}

if ! [ -d build ]; then mkdir build; fi

build_version ../../src ./build libutil
build_version ../../src ./build libtext
# build_version ../../src ./build libimage
# build_version ../../src ./build libalg
# build_version ../../src ./build ftextcvt
# build_version ../../src ./build ftextpack
# build_version ../../src ./build cpcvt
