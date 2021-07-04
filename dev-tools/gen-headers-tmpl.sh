#!/bin/bash

script_dir=$(cd $(dirname ${BASH_SOURCE:-$0}); pwd)
if [ ! -e $script_dir/settings.sh ]; then
    echo "Error: Could not find $script_dir/settings.sh" 1>&2
    exit 1
fi
. $script_dir/settings.sh

headers_txt="$opencv_build_dir/modules/python_bindings_generator/headers.txt"
cat $headers_txt | grep "include" | sed "s/^.*\/include\///" > headers-tmpl.txt
