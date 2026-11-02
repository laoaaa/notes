#!/bin/zsh
cd -- "${0:A:h}" || exit 1
python3 tools/sync-local.py --publish
result=$?
printf '\n按回车关闭窗口。'
read -r
exit "$result"
