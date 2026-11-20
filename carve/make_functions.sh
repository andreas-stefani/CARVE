#!/bin/bash

readonly EXIT_SUCCESS=0
readonly EXIT_FAILURE=1
readonly UNSUPPORTED_INSTR=2

rm -rf replacement_functions
dest_path="$HOME/Thesis/carve/clean"

for dir in "$dest_path"/*/; do              # slli, mul, div ...
    instr=$(basename "$dir")
    for file in "$dir"*.s; do               # best-len2.s , best-len5.s ...
        name=$(basename "$file")
        if [ "$name" == "$instr.s" ]; then
            continue;
        fi

        python3 label_registers.py "$instr" "$name" > tmp.txt
        code=$?
        if [ $code -eq $EXIT_SUCCESS ]; then
            file_name="${instr}_${name%.s}.txt"
            mkdir -p replacement_functions/"$instr"
            mv tmp.txt replacement_functions/"$instr"/"$file_name"
        
        elif [ $code -eq $EXIT_FAILURE ]; then
            echo "ERROR: $instr $name"
            rm tmp.txt

        elif [ $code -eq $UNSUPPORTED_INSTR ]; then   
            echo "UNSUPPORTED INSTRUCTION: $instr $name"
            rm tmp.txt

        else
            echo "UKNOWN ERROR ${code}"
            rm tmp.txt
        fi
    done
done