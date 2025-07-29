#!/bin/sh

input_list=$1

for url in $(cat ${input_list}); do
  python /home/hawkeye/mourrusty/projects/work/api_discovery.py ${url}
done
