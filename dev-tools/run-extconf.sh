#!/bin/bash

script_dir=$(cd $(dirname ${BASH_SOURCE:-$0}); pwd)
if [ ! -e $script_dir/settings.sh ]; then
    echo "Error: Could not find $script_dir/settings.sh" 1>&2
    exit 1
fi
. $script_dir/settings.sh

export PKG_CONFIG_PATH=$opencv_install_dir/lib/pkgconfig
opts="$opts --with-opt-include=$opencv_install_dir/include/opencv4"
opts="$opts --with-opt-lib=$opencv_install_dir/lib"

set -x
ruby extconf.rb $opts
