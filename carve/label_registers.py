"""
RUN:
    python3 label_registers.py <instruction> <GreenThumbSolution.s>
RETURNS:
    prints the MIR function in 4 parts:
    (A) function header
    (B) variable declarations ( MF, DL, TTI, MRI) & destination register getter
    (C) original instruction operand getters, for immidiate/registers
    (D) GreenThumbs solution in MIR format, declaring temporal registers when needed
    (E) function footer
EXIT CODES:
    (0) = supported instruction, no ERROR
    (1) = supported instruction, ERROR
    (2) = unsupported instruction
"""
import sys
import os

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
UNSUPPORTED_INSTR = 2


def buildMI (opcode,dest,regs):
    if dest == "dest":
        MI = "BuildMI(*MBBOrig, MI, DL, TII->get(RISCV::" + opcode.upper() + "), RDest)"                # BuildMI(*MBBOrig, MI, DL, TII->get(RISCV::SLLI), RDest
    else:
        REG = "Register " + dest.upper() + " = MRI.createVirtualRegister(&RISCV::GPRRegClass);"
        print(REG)
        MI = "BuildMI(*MBBOrig, MI, DL, TII->get(RISCV::" + opcode.upper() + "), " + dest.upper() + ")" # BuildMI(*MBBOrig, MI, DL, TII->get(RISCV::SLLI), T1
    
    for op in regs:
        if op == "zero":
            MI+=".addReg(RISCV::X0)"
        elif op == "imm":
            MI+=".addImm(Imm)"   # the spec's immediate, read from MI.getOperand(2) in the "before" part
        elif op.lstrip("-").isdigit(): # strip '-' for isdigit test, in case of negative number
            MI+=".addImm("+ op +")"
        else:
            MI+=".addReg("+op.upper()+")"
    MI+=";"
    print(MI)

def parseFile (path):
    instrs = []
    for line in open(path):
        line = line.replace(","," ") # create new string & replace ',' -> ' ' 
        line = line.split()          # create new string & split on spaces, save in list
        if line:                     # not null
            instrs.append(line)
    return instrs

if len(sys.argv) != 3:
    print("> python3 label_registers.py <instr> <solution.s>")
    sys.exit(EXIT_FAILURE)

script_dir = os.path.dirname(os.path.abspath(__file__))
results = os.path.join(script_dir, "clean") # instruction/best-lenN.s
path = os.path.join(results,sys.argv[1], sys.argv[2])
spec_path = os.path.join(results, sys.argv[1], sys.argv[1] + ".s")

spec = parseFile(spec_path)[0]
instrs = parseFile(path)

# locate last write to dest, cut the instructions there => everything else is junk, as it does not change the dest reg's value
last = -1                        #                                                                      Λ
for i,part in enumerate(instrs): #                                                                      |
    if part[1] == spec[1]:       # if dest reg( opcode dest_reg ...) same as spec's dest reg            |
        last = i                 # store last time seen -------------------------------------------------
if last == -1:
    print("ERROR: no instruction writes", spec[1], "in", path, file=sys.stderr) # nobody writes to dest reg 
    sys.exit(EXIT_FAILURE)
instrs = instrs[:last + 1] # cut out irrelevant instructions

# print(spec)
# print(instrs)

# PRINT PART A of HEADER - function definition
instr_printA = sys.argv[1]
len_printA = sys.argv[2][:-2]
len_printA = len_printA.replace("-","_")
print("\nstatic MachineBasicBlock* emit_"+instr_printA+"_"+len_printA+"(MachineInstr& MI, MachineBasicBlock* MBBOrig) {")

# PRINT PART B of HEADER - variable delcarations & destiination register
print("""
MachineFunction* MF  = MBBOrig->getParent();
DebugLoc DL  = MI.getDebugLoc();
const TargetInstrInfo* TII = MF->getSubtarget().getInstrInfo();
MachineRegisterInfo& MRI = MF->getRegInfo();
Register RDest = MI.getOperand(0).getReg();""")

names = {"x0":"zero"}

# read <instr>.s from results/<instr>.s
# lists the registers used in the original instruction
# named in1,in2 -> writen: MI.getOperand(1) & MI.getOperand(2)
# ALL other instructions will use temporary registers
for k,s in enumerate(spec[2:]):
    if s.startswith("x"): # save relevant registers
        names[s] = "in" + str(k+1)
        print("Register "+ names[s].upper() +" = MI.getOperand(" + str(k+1) + ").getReg();")
    else:                 # save relevant immidiate number
        names[s] = "imm"
        print("int64_t Imm = MI.getOperand(" + str(k+1) + ").getImm();")
print("\n")
# print(names)

branches = ["beq", "bne", "blt", "bge", "bltu", "bgeu", "jal", "jalr"]
num_t = 0
# [opcode, RDest, Reg, Reg/Temp]
for i,part in enumerate(instrs):
    regs = []
    op = part[0]       # opcode of instruction
    if op in branches: # unsupported instructions
        print("ERROR: unsupported instruction",op, file=sys.stderr)
        sys.exit(UNSUPPORTED_INSTR) 
    
    rd = part[1]       # RDest
    srcs = part[2:]    # [0]=Reg, [1]=Reg/Temp

    # handle src ( Reg, Reg/Imm )
    for s in srcs:
        if s in names: # already in, store its name 
            regs.append(names[s])
        elif s.lstrip("-").isdigit(): # number, keep as is
            regs.append(s)
        else:          # register that was never written and is not an input -> can't build it, stop
            print("ERROR: line", i + 1, "reads", s, "before anything writes it, in", path, file=sys.stderr)
            sys.exit(EXIT_FAILURE)
    
    # handle rd
    if i == (len(instrs)-1):    
        d = "dest"
    else:
        num_t+=1
        names[rd] = "t" + str(num_t)
        d = names[rd]

    buildMI(op, d, regs)

# PRINT FOOTER - delete original instruction & return last BB
print("""
MI.eraseFromParent();
return MBBOrig;
}""")

sys.exit(EXIT_SUCCESS)
