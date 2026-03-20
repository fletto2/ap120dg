#!/usr/bin/env python3
"""Generate SimH test for REAL HSR VADD from BAAHSR.MAC.

Uses the actual 20-instruction production microcode from the FPS
math library. Tests the full microcode execution engine including:
  - SPUFLT (s-pad unsigned float conversion)
  - Pipeline loop control (FSUBR TM,FA for decrement, BFGT for branch)
  - Memory addressing with s-pad indexing (ADD I,A; SETMA)
  - Floating adder pipeline (FADD DPX,DPY)
  - Data pad read/write (DPX<MD, DPY<MD, MI<FA)
  - Table Memory ROM access (LDTMA; DB=!ONE)
  - Subroutine call/return (JSR SPUFLT, RETURN)

Test: A={1.0, 2.0, 3.0} + B={4.0, 5.0, 6.0} = C={5.0, 7.0, 9.0}
"""

import struct, sys

DEV_FPS = 0o55
PULSE_N = 0; PULSE_S = 1; PULSE_C = 2; PULSE_P = 3
SKPDN = 2
FN_DEP = 0o001000
FN_START = 0o040000

def dg_io(ac, code, pulse, dev):
    return (0b011 << 13) | (ac << 11) | (code << 8) | (pulse << 6) | dev
def dg_doa(ac, pulse, dev): return dg_io(ac, 2, pulse, dev)
def dg_dob(ac, pulse, dev): return dg_io(ac, 4, pulse, dev)
def dg_skp(test, dev):      return dg_io(0, 7, test, dev)
def dg_lda(ac, mode, disp): return (0b001 << 13) | (ac << 11) | (mode << 8) | (disp & 0xFF)
def dg_jmp(mode, disp):     return (0b000 << 13) | (mode << 8) | (disp & 0xFF)
def dg_halt():              return dg_io(0, 6, 0, 0o77)
def ieee32(f):
    b = struct.pack('>f', f)
    v = struct.unpack('>I', b)[0]
    return (v >> 16) & 0xFFFF, v & 0xFFFF
def fn_dep_ps(word, inc_tma=False):
    inc = 3 if inc_tma else 0
    return FN_DEP | (inc << 6) | (word << 4) | 0o10

# ── HSR VADD microcode (20 instructions from BAAHSR.MAC) ───────────

hsr_words = [
    "040674,000000,000000,000000",  # PS[0]: MOV N,NM
    "011014,000000,000000,000013",  # PS[1]: JSR SPUFLT (PC-rel +11 → PS[13])
    "040000,000431,000000,000060",  # PS[2]: BFEQ DONE; MOV A,A; SETMA
    "040210,000000,000000,000060",  # PS[3]: MOV B,B; SETMA
    "030520,000000,000000,000000",  # PS[4]: SUB K,C
    "020100,000000,045004,000060",  # PS[5]: ADD I,A; SETMA; DPX<MD
    "020310,142000,015500,100060",  # PS[6]: ADD J,B; SETMA; DPY<MD; FSUBR TM,DPX(NN)
    "000001,123000,000440,000000",  # PS[7]: FADD DPX,DPY
    "020100,000000,045004,000060",  # PS[8]: ADD I,A; SETMA; DPX<MD
    "020310,141000,015000,100060",  # PS[9]: ADD J,B; SETMA; DPY<MD; FSUBR TM,FA
    "020521,123556,000440,000160",  # PS[10]: FADD DPX,DPY; ADD K,C; SETMA; MI<FA; BFGT LOOP
    "000000,000340,000000,000000",  # PS[11]: DONE: RETURN
    "041774,000000,046005,000000",  # PS[12]: SPUFLT: MOV NM,NM; DPX(1)<SPFN
    "001674,000723,002000,000033",  # PS[13]: LDSPI C27; DB=27.; BGE POS
    "011314,000000,010004,000005",  # PS[14]: RPSF F64K; DPY<DB
    "041775,136122,000540,000000",  # PS[15]: FADD DPY,MDPX(1); MOV C27,C27; BR COMM
    "041775,156000,000500,000000",  # PS[16]: POS: FADD ZERO,MDPX(1); MOV C27,C27
    "000001,100000,000000,000000",  # PS[17]: COMM: FADD (push)
    "000003,103340,102005,010001",  # PS[18]: DPX(1)<FA; LDTMA; DB=!ONE; RETURN
    "000000,000041,012000,000000",  # PS[19]: F64K constant (65536.0)
]

code = []
for line in hsr_words:
    ws = [int(w, 8) for w in line.split(",")]
    word64 = ((ws[0] & 0xFFFF) << 48) | ((ws[1] & 0xFFFF) << 32) | \
             ((ws[2] & 0xFFFF) << 16) | (ws[3] & 0xFFFF)
    code.append(word64)

# Append HALT at PS[20] — the RETURN at PS[11] will pop SRS to here
halt_word = (1 << 60) | (5 << 54)  # SOP=SPEC, SPS=HALT
code.append(halt_word)

# ── S-pad values ────────────────────────────────────────────────────
# VADD expects: SP[0]=A, SP[1]=I, SP[2]=B, SP[3]=J, SP[4]=C, SP[5]=K, SP[6]=N
spad_vals = [0, 1, 3, 1, 6, 1, 3]

test_a = [1.0, 2.0, 3.0]
test_b = [4.0, 5.0, 6.0]
test_c = [a + b for a, b in zip(test_a, test_b)]

HOST_DATA = 0o600
HOST_RESULT = 0o620

# ── Generate SimH script ───────────────────────────────────────────

out = []
def emit(s): out.append(s)

emit(f"; HSR VADD test — 20 production instructions from BAAHSR.MAC")
emit(f"; A={{1,2,3}} + B={{4,5,6}} = C={{5,7,9}}")
emit("set cpu 32K")
emit("set fps enabled")
emit("set fpsdma enabled")
emit("set fpsctl5 enabled")
emit("")

pz = {}
pz_next = 0o040

def pz_const(name, val):
    global pz_next
    pz[name] = pz_next
    emit(f"deposit {pz_next:03o} {val:06o}")
    pz_next += 1

pz_const("zero", 0)
pz_const("fn_dep_tma", FN_DEP | 3)     # REGSEL_TMA
pz_const("fn_dep_ps_w0", fn_dep_ps(0))
pz_const("fn_dep_ps_w1", fn_dep_ps(1))
pz_const("fn_dep_ps_w2", fn_dep_ps(2))
pz_const("fn_dep_ps_w3_inc", fn_dep_ps(3, inc_tma=True))
pz_const("fn_dep_psa", FN_DEP | 0)     # REGSEL_PSA
pz_const("fn_start", FN_START)
pz_const("fn_dep_spd", FN_DEP | 1)     # REGSEL_SPD
pz_const("fn_dep_spfn", FN_DEP | 5)    # REGSEL_SPFN
pz_const("dma_ctl_h2a", 0o300)
pz_const("dma_ctl_a2h", 0o340)
pz_const("wc_in", 12)
pz_const("wc_out", 6)
pz_const("apma_zero", 0)
pz_const("apma_six", 6)
pz_const("host_in", HOST_DATA)
pz_const("host_out", HOST_RESULT)
pz_const("entry", 0)

# Microcode words
for i, word in enumerate(code):
    for w in range(4):
        val = (word >> (48 - w*16)) & 0xFFFF
        pz_const(f"mc{i}_w{w}", val)

# S-pad values and addresses
for i, val in enumerate(spad_vals):
    pz_const(f"sp{i}", val)
for i in range(len(spad_vals)):
    pz_const(f"spa{i}", i)

emit("")

# Input/output data
emit(f"; Float data at {HOST_DATA:03o}")
addr = HOST_DATA
for v in test_a + test_b:
    hi, lo = ieee32(v)
    emit(f"deposit {addr:03o} {hi:06o}")
    addr += 1
    emit(f"deposit {addr:03o} {lo:06o}")
    addr += 1
emit(f"; Result area at {HOST_RESULT:03o}")
for i in range(6):
    emit(f"deposit {HOST_RESULT+i:03o} 0")

# Pre-load SRS with return address → HALT at PS[20]
emit("")
emit("; SRS[0] = 20 (HALT), SRA = 1 (one return address)")
emit("deposit fps SRS[0] 000024")  # 20 decimal = 24 octal
emit("deposit fps SRA 1")

# ── Nova program ────────────────────────────────────────────────────

pc = 0o1000
prog = []
def inst(opcode):
    global pc
    prog.append((pc, opcode))
    pc += 1

# Phase 1: Load microcode (set TMA=0, then DEP all words)
inst(dg_lda(0, 0, pz["zero"]))
inst(dg_doa(0, PULSE_N, DEV_FPS))
inst(dg_lda(0, 0, pz["fn_dep_tma"]))
inst(dg_doa(0, PULSE_S, DEV_FPS))

for i in range(len(code)):
    for w in range(4):
        inst(dg_lda(0, 0, pz[f"mc{i}_w{w}"]))
        inst(dg_doa(0, PULSE_N, DEV_FPS))
        fn = "fn_dep_ps_w3_inc" if w == 3 else f"fn_dep_ps_w{w}"
        inst(dg_lda(0, 0, pz[fn]))
        inst(dg_doa(0, PULSE_S, DEV_FPS))

# Phase 2: Load s-pad via two-step DEP
for i in range(len(spad_vals)):
    inst(dg_lda(0, 0, pz[f"spa{i}"]))
    inst(dg_doa(0, PULSE_N, DEV_FPS))
    inst(dg_lda(0, 0, pz["fn_dep_spd"]))
    inst(dg_doa(0, PULSE_S, DEV_FPS))
    inst(dg_lda(0, 0, pz[f"sp{i}"]))
    inst(dg_doa(0, PULSE_N, DEV_FPS))
    inst(dg_lda(0, 0, pz["fn_dep_spfn"]))
    inst(dg_doa(0, PULSE_S, DEV_FPS))

# Phase 3: DMA Host→AP
inst(dg_lda(0, 0, pz["apma_zero"]))
inst(dg_dob(0, PULSE_C, DEV_FPS))
inst(dg_lda(0, 0, pz["host_in"]))
inst(dg_dob(0, PULSE_S, DEV_FPS))
inst(dg_lda(0, 0, pz["wc_in"]))
inst(dg_dob(0, PULSE_N, DEV_FPS))
inst(dg_lda(0, 0, pz["dma_ctl_h2a"]))
inst(dg_doa(0, PULSE_C, DEV_FPS))
inst(dg_dob(0, PULSE_P, DEV_FPS))
inst(dg_skp(SKPDN, DEV_FPS + 1))
inst(dg_jmp(1, 0xFF))

# Phase 4: START
inst(dg_lda(0, 0, pz["entry"]))
inst(dg_doa(0, PULSE_N, DEV_FPS))
inst(dg_lda(0, 0, pz["fn_dep_psa"]))
inst(dg_doa(0, PULSE_S, DEV_FPS))
inst(dg_lda(0, 0, pz["fn_start"]))
inst(dg_doa(0, PULSE_S, DEV_FPS))
inst(dg_skp(SKPDN, DEV_FPS))
inst(dg_jmp(1, 0xFF))

# Phase 5: DMA AP→Host
inst(dg_lda(0, 0, pz["apma_six"]))
inst(dg_dob(0, PULSE_C, DEV_FPS))
inst(dg_lda(0, 0, pz["host_out"]))
inst(dg_dob(0, PULSE_S, DEV_FPS))
inst(dg_lda(0, 0, pz["wc_out"]))
inst(dg_dob(0, PULSE_N, DEV_FPS))
inst(dg_lda(0, 0, pz["dma_ctl_a2h"]))
inst(dg_doa(0, PULSE_C, DEV_FPS))
inst(dg_dob(0, PULSE_P, DEV_FPS))
inst(dg_skp(SKPDN, DEV_FPS + 1))
inst(dg_jmp(1, 0xFF))
inst(dg_halt())

emit("")
for addr, opcode in prog:
    emit(f"deposit {addr:03o} {opcode:06o}")

emit("")
emit(f"go {0o1000:03o}")
for i, val in enumerate(test_c):
    hi, lo = ieee32(val)
    emit(f'echo "C[{i}] expected: {hi:06o},{lo:06o} (IEEE {val})"')
emit(f'echo "Actual:"')
emit(f"examine {HOST_RESULT:03o}-{HOST_RESULT+5:03o}")
emit("examine fps PSA")
emit("quit")

script = "\n".join(out) + "\n"
outfile = sys.argv[1] if len(sys.argv) > 1 else "/tmp/test_hsr_vadd.simh"
with open(outfile, 'w') as f:
    f.write(script)
print(f"Generated {outfile} ({len(prog)} Nova, {len(code)} AP instructions)", file=sys.stderr)
