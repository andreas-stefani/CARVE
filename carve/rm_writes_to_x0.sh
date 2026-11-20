#!/bin/bash
dest_path="$HOME/Thesis/carve/clean"
if [ -d "$dest_path" ]; then
    rm -rf "$dest_path"
fi

results_path="$HOME/Thesis/related-work/aesip/aesip-main/riscv_greenthumb/riscv/results/"
cp -r "$results_path" "$dest_path"

for dir in "$dest_path"/*/; do
    for file in "$dir"*.s; do
        awk '{ sub(/#.*/, "") }                                         # strip comments
            NF == 0 { next }                                            # skip empty lines
            $2 == "x0," && !($1 == "jal" || $1 == "jalr") { next }      # jal x0 and jalr x0 are valid instructions, anything else that writes to x0 is removed

            # replace pseudo instructions with their real instruction equivalents
            $1 == "neg"  { print "sub", $2, "x0,", $3; next }           # neg rd, rs       -> sub rd, x0, rs
            $1 == "not"  { print "xori", $2, $3 ",", "-1"; next }       # not rd, rs       -> xori rd, rs, -1
            $1 == "bgtu" { print "bltu", $3, $2, $4; next }             # bgtu a, b, off   -> bltu b, a, off
            $1 == "bnez" { print "bne", $2, "x0,", $3; next }           # bnez rs, off     -> bne rs, x0, off
            $1 == "beqz" { print "beq", $2, "x0,", $3; next }           # beqz rs, off     -> beq rs, x0, off

            # zero idiom: r ^ r = 0 and r - r = 0, no matter what r holds -> do not read r (it may never have been written)
            ($1 == "xor" || $1 == "sub") && $3 == $4 "," { print "addi", $2, "x0,", "0"; next }   # xor rd, r, r -> addi rd, x0, 0

            { print }                                                   # everything else: keep as is
        ' "$file" > "$file.tmp" && mv "$file.tmp" "$file"
    done
done