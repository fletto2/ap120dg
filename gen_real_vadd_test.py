#!/usr/bin/env python3
"""Generate SimH test for a hand-crafted VADD microcode loop.

Tests the emulator's microcode engine with real AP features:
  - S-pad loop control (DEC, branch on s-pad condition)
  - Memory addressing (MA set from s-pad, MA increment)
  - Floating-point adder (FADD)
  - Data pad read/write
  - Memory write (MI)
  - DMA Host→AP and AP→Host with IEEE float conversion

Test: A={1.0, 2.0, 3.0} + B={4.0, 5.0, 6.0} = C={5.0, 7.0, 9.0}
S-pad: SP[0]=base_A(0), SP[1]=base_B(3), SP[2]=base_C(6), SP[3]=N(3)
"""

import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lnk100 import parse_apo, Linker

# ── DG Nova instruction encoding ────────────────────────────────────

DEV_FPS = 0o55
PULSE_N = 0; PULSE_S = 1; PULSE_C = 2; PULSE_P = 3
SKPDN = 2

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

# ── 64-bit microcode field packing ──────────────────────────────────

def pack_instr(*, df=0, sop=0, sh=0, sps=0, spd=0, fadd=0, a1=0, a2=0,
               cond=0, disp=0, dpx_src=0, dpy_src=0, dpbs=0,
               xr=4, yr=4, xw=4, yw=4, fm=0, m1=0, m2=0, mi=0,
               ma_op=0, dpa_op=0, tma_op=0):
    w = 0
    def put(start, width, val):
        nonlocal w
        shift = 63 - start - (width - 1)
        w |= (val & ((1 << width) - 1)) << shift
    put(0,1,df); put(1,3,sop); put(4,2,sh); put(6,4,sps); put(10,4,spd)
    put(14,3,fadd); put(17,3,a1); put(20,3,a2); put(23,4,cond); put(27,5,disp)
    put(32,2,dpx_src); put(34,2,dpy_src); put(36,3,dpbs); put(39,3,xr); put(42,3,yr)
    put(45,3,xw); put(48,3,yw); put(51,1,fm); put(52,2,m1); put(54,2,m2)
    put(56,2,mi); put(58,2,ma_op); put(60,2,dpa_op); put(62,2,tma_op)
    return w

# Constants
SOP_NOP=0; SOP_SPEC=1; SOP_ADD=2; SOP_SUB=3; SOP_MOV=4
SPS_HALT=5; SPS_CLR=8; SPS_INC=9; SPS_DEC=10
FADD_FADD=3
A_DPX=2; A_MD=4
COND_NOP=0; COND_BGT=15; COND_BNE=14
DPBS_MD=5; DPBS_DPX=3
MI_DPBS=3
MA_INC=1; MA_SET=3

# ── Hand-crafted VADD loop ─────────────────────────────────────────
#
# S-pad: SP[0]=base_A, SP[1]=base_B, SP[2]=base_C, SP[3]=N
#
# PS[0]: MA ← SP[0] (base_A)
# PS[1]: Read MD[MA] into DPX, MA++
# PS[2]: MA ← SP[1] (base_B)
# PS[3]: FADD DPX + MD[MA], FA→DPX, MA ← SP[2] (base_C)
# PS[4]: DPBS=DPX → MI → MD[MA] (store result)
# PS[5]: SP[0]++, SP[1]++, SP[2]++
# PS[6]: DEC SP[3] (N--), branch if >0 to PS[0]
# PS[7]: HALT

code = [
    # PS[0]: MA ← SP[0] (base_A). NOP everything else.
    pack_instr(sop=SOP_NOP, spd=0, ma_op=MA_SET),

    # PS[1]: DPBS=MD (read MD[MA] → DPX), MA++
    pack_instr(dpbs=DPBS_MD, ma_op=MA_INC),

    # PS[2]: MA ← SP[1] (base_B)
    pack_instr(sop=SOP_NOP, spd=1, ma_op=MA_SET),

    # PS[3]: FADD A1=DPX + A2=MD[MA]. Result enters FAB1.
    # Pipeline: FAB1→FAB2→FA requires 2 FADD-active cycles to propagate.
    pack_instr(fadd=FADD_FADD, a1=A_DPX, a2=A_MD),

    # PS[4]: FADD NOP (FAND with zero inputs) to push pipeline.
    # FAB1→FAB2 (result moves to stage 2). Set MA ← SP[2] (base_C).
    pack_instr(fadd=5, a1=0, a2=0, spd=2, ma_op=MA_SET),  # FAND 0,0 = NOP push

    # PS[5]: FADD NOP to push pipeline again. FAB2→FA, result now in FA.
    pack_instr(fadd=5, a1=0, a2=0),  # FAND 0,0

    # PS[6]: MI=1 writes FA to MD[MA=base_C]
    pack_instr(mi=1),

    # PS[7]: SP[0]++
    pack_instr(sop=SOP_SPEC, sps=SPS_INC, spd=0),

    # PS[8]: INC SP[1]
    pack_instr(sop=SOP_SPEC, sps=SPS_INC, spd=1),

    # PS[9]: INC SP[2]
    pack_instr(sop=SOP_SPEC, sps=SPS_INC, spd=2),

    # PS[10]: DEC SP[3] (N--). Branch if s-pad > 0 back to PS[0].
    # Branch formula: target = PSA + 1 + DISPF - 17
    # Want target=0 from PSA=10: 0 = 10 + 1 + DISPF - 17, DISPF = 6
    pack_instr(sop=SOP_SPEC, sps=SPS_DEC, spd=3, cond=COND_BGT, disp=6),

    # PS[11]: HALT
    pack_instr(sop=SOP_SPEC, sps=SPS_HALT),
]

print(f"VADD loop: {len(code)} instructions", file=sys.stderr)

# ── FN command values ───────────────────────────────────────────────

FN_DEP       = 0o001000
FN_DEP_TMA   = 0o001003
FN_DEP_PSA   = 0o001000
FN_START     = 0o040000  # 0x4000

def fn_dep_ps(word, inc_tma=False):
    inc = 3 if inc_tma else 0
    return FN_DEP | (inc << 6) | (word << 4) | 0o10

# ── Test data ───────────────────────────────────────────────────────

test_a = [1.0, 2.0, 3.0]
test_b = [4.0, 5.0, 6.0]
test_c = [a + b for a, b in zip(test_a, test_b)]
spad_vals = [0, 3, 6, 3]  # base_A, base_B, base_C, N

HOST_DATA = 0o600
HOST_RESULT = 0o620

# ── Generate SimH script ───────────────────────────────────────────

out = []
def emit(s): out.append(s)

emit(f"; VADD loop test — {len(code)} hand-crafted instructions")
emit(f"; A={{1,2,3}} + B={{4,5,6}} = C={{5,7,9}}")
emit("set cpu 32K")
emit("set fps enabled")
emit("set fpsdma enabled")
emit("set fpsctl5 enabled")
emit("")

# Page-zero constants
pz = {}
pz_next = 0o040

def pz_const(name, val):
    global pz_next
    pz[name] = pz_next
    emit(f"deposit {pz_next:03o} {val:06o}")
    pz_next += 1

pz_const("zero", 0)
pz_const("fn_dep_tma", FN_DEP_TMA)
pz_const("fn_dep_ps_w0", fn_dep_ps(0))
pz_const("fn_dep_ps_w1", fn_dep_ps(1))
pz_const("fn_dep_ps_w2", fn_dep_ps(2))
pz_const("fn_dep_ps_w3_inc", fn_dep_ps(3, inc_tma=True))
pz_const("fn_dep_psa", FN_DEP_PSA)
pz_const("fn_start", FN_START)
pz_const("dma_ctl_h2a", 0o300)
pz_const("dma_ctl_a2h", 0o340)
pz_const("wc_in", 12)    # 6 floats × 2 words
pz_const("wc_out", 6)    # 3 floats × 2 words
pz_const("apma_zero", 0)
pz_const("apma_six", 6)
pz_const("host_in", HOST_DATA)
pz_const("host_out", HOST_RESULT)
pz_const("entry", 0)
pz_const("fn_dep_spd", FN_DEP | 1)   # DEP into SPD pointer (REGSEL 1)
pz_const("fn_dep_spfn", FN_DEP | 5)  # DEP into SPFN → spad[SPD] (REGSEL 5)

# S-pad values as page-zero constants
for i, val in enumerate(spad_vals):
    pz_const(f"sp{i}", val)
# S-pad addresses
for i in range(len(spad_vals)):
    pz_const(f"spa{i}", i)

# Microcode words
for i, word in enumerate(code):
    for w in range(4):
        val = (word >> (48 - w*16)) & 0xFFFF
        pz_const(f"mc{i}_w{w}", val)

emit("")
emit("; S-pad loaded via two-step DEP protocol in Nova program")

emit("")
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

# ── Nova program ────────────────────────────────────────────────────

pc = 0o1000
prog = []
def inst(opcode):
    global pc
    prog.append((pc, opcode))
    pc += 1

# Load microcode
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

# Load s-pad via two-step DEP protocol (matches real DAPEX.MAC)
for i in range(len(spad_vals)):
    inst(dg_lda(0, 0, pz[f"spa{i}"]))    # SWR = s-pad address
    inst(dg_doa(0, PULSE_N, DEV_FPS))     # DOA SWR
    inst(dg_lda(0, 0, pz["fn_dep_spd"])) # FN = DEP SPD
    inst(dg_doa(0, PULSE_S, DEV_FPS))     # DOAS FN
    inst(dg_lda(0, 0, pz[f"sp{i}"]))     # SWR = s-pad value
    inst(dg_doa(0, PULSE_N, DEV_FPS))     # DOA SWR
    inst(dg_lda(0, 0, pz["fn_dep_spfn"]))# FN = DEP SPFN → spad[SPD]
    inst(dg_doa(0, PULSE_S, DEV_FPS))     # DOAS FN

# DMA Host→AP
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

# START
inst(dg_lda(0, 0, pz["entry"]))
inst(dg_doa(0, PULSE_N, DEV_FPS))
inst(dg_lda(0, 0, pz["fn_dep_psa"]))
inst(dg_doa(0, PULSE_S, DEV_FPS))
inst(dg_lda(0, 0, pz["fn_start"]))
inst(dg_doa(0, PULSE_S, DEV_FPS))
inst(dg_skp(SKPDN, DEV_FPS))
inst(dg_jmp(1, 0xFF))

# DMA AP→Host
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
outfile = sys.argv[1] if len(sys.argv) > 1 else "/tmp/test_real_vadd.simh"
with open(outfile, 'w') as f:
    f.write(script)
print(f"Generated {outfile} ({len(prog)} Nova, {len(code)} AP instructions)", file=sys.stderr)
