#!/bin/bash

script_dir=$(cd $(dirname ${BASH_SOURCE:-$0}); pwd)

supported_headers="$supported_headers opencv2/core.hpp"
supported_headers="$supported_headers opencv2/imgproc.hpp"
supported_headers="$supported_headers opencv2/imgcodecs.hpp"
supported_headers="$supported_headers opencv2/highgui.hpp"

iflag=`pkg-config --cflags-only-I opencv4`
inc_dir=${iflag:2}

out_path="${script_dir}/headers.txt"
echo "./dummycv/dummycv.hpp" > headers.txt
for hdr in $supported_headers; do
    echo "${inc_dir}/${hdr}" >> headers.txt
done
