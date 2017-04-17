#!/usr/bin/env bash

set -e

work_path=$HOME/.f
cur_path=`pwd`
func="
function f() {
    if [ -z \"\$*\" ]; then
        path=\`python $work_path/f.py\`
    else
        path=\`python $work_path/f.py \"\$@\"\`
    fi
    if [ \"0\" == \"\$?\" ]; then
        cd \$path
    fi
}
"

mkdir -p "$work_path"
ln -s "$cur_path/f.py" "$work_path/f.py"
echo "$func" >> "$HOME/.bashrc"
source "$HOME/.bashrc"

echo "f successfully installed!"