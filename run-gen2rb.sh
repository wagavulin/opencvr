#!/bin/bash

script_dir=$(cd $(dirname ${BASH_SOURCE:-$0}); pwd)
if [ ! -e $script_dir/settings.sh ]; then
    echo "Error: Could not find $script_dir/settings.sh" 1>&2
    exit 1
fi
. $script_dir/settings.sh

target_header_list="$opencv_build_dir/modules/python_bindings_generator/headers.txt"
export PYTHONPATH="$opencv_src_dir/modules/python/src2"

if [ $bindtest_only -eq 1 ]; then
    echo "Bind only test functions"
    touch headers.txt # generate empty file
else
    cp $target_header_list headers.txt
fi

./gen2rb.py headers.txt
