addi  x1, x0, 0          
andi  x4, x3, 1          
beq x4, x0, x0,
add   x1, x1, x2         
slli  x2, x2, 1          
srli  x3, x3, 1          
bne x3, x0, -20
