#!/usr/bin/env python3
"""Generate SimH test harness for FPS AP-120B VADD (vector add).

Exercises the full host→AP pipeline:
  1. Load microcode into PS via FN DEP protocol
  2. Load S-pad parameters via FN DEP
  3. DMA Host→AP (load input data)
  4. START AP, poll SKPDN 055
  5. DMA AP→Host (read results)
  6. Verify results via examine

Hand-crafted 4-instruction microcode: C[i] = A[i] + B[i]
"""

import struct, sys

# ── 64-bit microcode field packing ──────────────────────────────────

def pack_instr(*, df=0, sop=0, sh=0, sps=0, spd=0, fadd=0, a1=0, a2=0,
               cond=0, disp=0, dpx_src=0, dpy_src=0, dpbs=0,
               xr=4, yr=4, xw=4, yw=4, fm=0, m1=0, m2=0, mi=0,
               ma_op=0, dpa_op=0, tma_op=0):
    """Pack fields into a 64-bit AP microinstruction word.

    Field positions (bit 0 = MSB):
      0:    DF        1-3:  SOP      4-5:  SH       6-9:  SPS
      10-13: SPD      14-16: FADD    17-19: A1      20-22: A2
      23-26: COND     27-31: DISP    32-33: DPX     34-35: DPY
      36-38: DPBS     39-41: XR      42-44: YR      45-47: XW
      48-50: YW       51: FM         52-53: M1      54-55: M2
      56-57: MI       58-59: MA_OP   60-61: DPA_OP  62-63: TMA_OP
    """
    w = 0
    def put(start, width, val):
        nonlocal w
        shift = 63 - start - (width - 1)
        mask = (1 << width) - 1
        w |= (val & mask) << shift

    put(0, 1, df)
    put(1, 3, sop)
    put(4, 2, sh)
    put(6, 4, sps)
    put(10, 4, spd)
    put(14, 3, fadd)
    put(17, 3, a1)
    put(20, 3, a2)
    put(23, 4, cond)
    put(27, 5, disp)
    put(32, 2, dpx_src)
    put(34, 2, dpy_src)
    put(36, 3, dpbs)
    put(39, 3, xr)
    put(42, 3, yr)
    put(45, 3, xw)
    put(48, 3, yw)
    put(51, 1, fm)
    put(52, 2, m1)
    put(54, 2, m2)
    put(56, 2, mi)
    put(58, 2, ma_op)
    put(60, 2, dpa_op)
    put(62, 2, tma_op)
    return w

def instr_to_octal_words(w):
    """Split 64-bit word into 4 octal 16-bit words (MSB first)."""
    w3 = (w >>  0) & 0xFFFF
    w2 = (w >> 16) & 0xFFFF
    w1 = (w >> 32) & 0xFFFF
    w0 = (w >> 48) & 0xFFFF
    return w0, w1, w2, w3

# ── Constants ───────────────────────────────────────────────────────

SOP_NOP  = 0
SOP_SPEC = 1
SOP_ADD  = 2
SOP_SUB  = 3
SOP_MOV  = 4

SPS_HALT = 5
SPS_CLR  = 8
SPS_INC  = 9
SPS_DEC  = 10

FADD_NOP  = 0
FADD_FSUBR = 1
FADD_FSUB = 2
FADD_FADD = 3

A_NOP = 0; A_FA = 1; A_DPX = 2; A_DPY = 3; A_MD = 4

COND_NOP = 0
COND_BR  = 2
COND_BNE = 14
COND_BGE = 15

DPBS_NOP = 0; DPBS_MD = 5; DPBS_DPX = 3

MI_NOP = 0; MI_FA = 1; MI_FM = 2; MI_DPBS = 3

# DPX/DPY write-source field (SIM100 sections 33010-33220)
DPW_NOP = 0; DPW_DPBS = 1; DPW_FA = 2; DPW_FM = 3

MA_NOP = 0; MA_INC = 1; MA_DEC = 2; MA_SET = 3

# ── DG Nova instruction encoding ───────────────────────────────────

DEV_FPS = 0o55

def dg_io(ac, code, pulse, dev):
    """Encode DG Nova I/O instruction."""
    return (0b011 << 13) | (ac << 11) | (code << 8) | (pulse << 6) | dev

def dg_doa(ac, pulse, dev):  return dg_io(ac, 2, pulse, dev)
def dg_dob(ac, pulse, dev):  return dg_io(ac, 4, pulse, dev)
def dg_dia(ac, pulse, dev):  return dg_io(ac, 1, pulse, dev)
def dg_skp(test, dev):       return dg_io(0, 7, test, dev)  # test in pulse field

def dg_lda(ac, mode, disp):
    """LDA ac, disp  (mode 0=page zero, mode 1=PC-relative)."""
    return (0b001 << 13) | (ac << 11) | (mode << 8) | (disp & 0xFF)

def dg_sta(ac, mode, disp):
    """STA ac, disp."""
    return (0b010 << 13) | (ac << 11) | (mode << 8) | (disp & 0xFF)

def dg_jmp(mode, disp, ind=0):
    """JMP disp (mode 0=page zero, 1=PC-relative)."""
    return (0b000 << 13) | (0 << 11) | (ind << 10) | (mode << 8) | (disp & 0xFF)

def dg_halt():
    """HALT = DOC 0,CPU."""
    return dg_io(0, 6, 0, 0o77)

SKPDN  = 2  # pulse=2 in skip = test DONE
SKPBZ  = 1  # test BUSY zero

PULSE_N = 0; PULSE_S = 1; PULSE_C = 2; PULSE_P = 3

# ── IEEE 32-bit float encoding (for DMA format 0) ──────────────────

def ieee32(f):
    """Return (hi16, lo16) for a 32-bit IEEE float."""
    b = struct.pack('>f', f)
    v = struct.unpack('>I', b)[0]
    return (v >> 16) & 0xFFFF, v & 0xFFFF

# ── Microcode: C[i] = A[i] + B[i] for i=0..N-1 ────────────────────
#
# S-pad setup:  SP[0]=base_A, SP[1]=base_B, SP[2]=base_C, SP[3]=N
#
# Inst 0: MA ← SP[0] (base_A). Read MD[MA] into DPX. MA++.
# Inst 1: FADD DPX + MD[MA]. FA→DPX. MA ← SP[1] (base_B).
#          Wait — MA_SET happens after the read, so we need a different approach.
#
# Let me redesign with explicit address management:
#
# Inst 0: MA ← SP[0] (base_A), NOP. (set address)
# Inst 1: Read MD[MA] into DPX, MA ← SP[1] (base_B). (fetch A[i], set B addr)
# Inst 2: FADD DPX + MD[MA], FA→DPX, MA ← SP[2] (base_C). (compute, set C addr)
# Inst 3: DPBS=DPX→MI→MD[MA], write C[i]. (store result)
# Inst 4: SP[0]++, SP[1]++, SP[2]++, SP[3]--.
#          Actually can only do one s-pad op per cycle.
#
# This is getting complex. Let me use a simpler unrolled approach for N=3:
#
# Actually, let me just do N=1 (single element) for the first test.
# A[0] + B[0] → C[0].  A at MD[0], B at MD[1], C at MD[2].
#
# Inst 0: MA=0 (from SP[0]=0), NOP
# Inst 1: Read MD[0] onto DPBS, DPX←DPBS. MA++.
# Inst 2: FADD A1=DPX, A2=MD[1]. MA++.
# Inst 3: Adder-active filler -- pushes the adder pipeline one stage.
# Inst 4: MI=FA → MD[2]. Store result.
# Inst 5: HALT.
#
# The filler at inst 3 is required: the floating adder has a 2-cycle
# latency (FPADD→FAB1→FAB2→FA), so the sum issued at inst 2 only reaches
# FA at inst 4.  A plain NOP would NOT do -- per SIM100 label 35000 the
# adder pipeline only advances when the adder is active, so the filler
# uses the single-operand form (FADD=0 with A1≠0) rather than all-zeros.
#
# 6 instructions total.

# Main data reads are THREE cycles deep.  SIM100 line 1316 says it
# outright -- "FETCH MD FROM MA SET THREE CYCLES AGO IF A READ WAS DONE
# THEN" -- and the pipeline MDB1->MDB2->MDB3->MDR is pushed once per
# cycle, so a SETMA at cycle N delivers to MDR at N+3.  An instruction
# consuming MD must sit that far behind the SETMA that fetched it.  The
# adder is separately 2 deep and only advances when active, hence the
# filler before the store.

microcode = [
    # 0: MA <- SPAD[0] (=0).  Starts the read of MD[0]; reaches MDR at 3.
    pack_instr(sop=SOP_NOP, spd=0, ma_op=MA_SET),

    # 1: MA++ (=1).  Starts the read of MD[1]; reaches MDR at 4.
    pack_instr(sop=SOP_NOP, ma_op=MA_INC),

    # 2: waiting for the first read.
    pack_instr(sop=SOP_NOP),

    # 3: MDR holds MD[0].  DPBS=MD, DPX <- DPBS.
    pack_instr(dpbs=DPBS_MD, dpx_src=DPW_DPBS),

    # 4: MDR holds MD[1].  FADD A1=DPX (MD[0]) + A2=MD (MD[1]).
    pack_instr(fadd=FADD_FADD, a1=A_DPX, a2=A_MD),

    # 5: adder-active filler advances FAB1->FAB2; MA++ (=2) for the store.
    pack_instr(fadd=0, a1=A_DPX, ma_op=MA_INC),

    # 6: FA ready.  MI=FA -> MD[2].
    pack_instr(mi=MI_FA),

    # 7: HALT
    pack_instr(sop=SOP_SPEC, sps=SPS_HALT),
]

# Verify microcode
for i, w in enumerate(microcode):
    ws = instr_to_octal_words(w)
    print(f"# PS[{i}]: {ws[0]:06o},{ws[1]:06o},{ws[2]:06o},{ws[3]:06o}  (0x{w:016X})", file=sys.stderr)

# ── FN command values ───────────────────────────────────────────────

FN_DEP  = 0x0200
FN_START = 0x4000
FN_RESET = 0x0800

# REGSEL values
REGSEL_PSA    = 0
REGSEL_SPD    = 1
REGSEL_MA     = 2
REGSEL_TMA    = 3
REGSEL_PS_TMA = 8    # PS word at TMA
REGSEL_MD_MA  = 13   # MD word at MA

# DEP into TMA (set TMA register): FN = DEP | REGSEL_TMA
FN_DEP_TMA = FN_DEP | REGSEL_TMA   # 0x0203

# DEP into PS[TMA], WORD=w, INC=TMA(3):
# INC field is bits 10-11 of FN command, WORD is bits 8-9
# FN = DEP | (INC << 6) | (WORD << 4) | REGSEL_PS_TMA
def fn_dep_ps(word, inc_tma=False):
    inc = 3 if inc_tma else 0
    return FN_DEP | (inc << 6) | (word << 4) | REGSEL_PS_TMA

# DEP into SPD: FN = DEP | REGSEL_SPD = 0x0201
FN_DEP_SPD = FN_DEP | REGSEL_SPD

# DEP into PSA: FN = DEP | REGSEL_PSA = 0x0200
FN_DEP_PSA = FN_DEP | REGSEL_PSA

# ── Test data ───────────────────────────────────────────────────────

# Input: A[0]=1.5, B[0]=2.5 → C[0] should be 4.0
test_a = 1.5
test_b = 2.5
test_c_expected = test_a + test_b  # 4.0

a_hi, a_lo = ieee32(test_a)
b_hi, b_lo = ieee32(test_b)
c_hi, c_lo = ieee32(test_c_expected)

print(f"# A={test_a} → hi={a_hi:04X} lo={a_lo:04X}", file=sys.stderr)
print(f"# B={test_b} → hi={b_hi:04X} lo={b_lo:04X}", file=sys.stderr)
print(f"# Expected C={test_c_expected} → hi={c_hi:04X} lo={c_lo:04X}", file=sys.stderr)

# ── Generate SimH script ───────────────────────────────────────────

out = []
def emit(s):
    out.append(s)

emit("; Test harness: FPS AP-120B full pipeline test")
emit("; Hand-crafted microcode: C[0] = A[0] + B[0] (38-bit float add)")
emit("; Generated by gen_vadd_test.py")
emit("")
emit("set cpu 32K")
emit("set fps enabled")
emit("set fpsdma enabled")
emit("set fpsctl5 enabled")
emit("")

# ── Page-zero data area (040-077) ──────────────────────────────────
# Store constants that the Nova program will load via LDA

pz_base = 0o040  # Page-zero data area start
pz = {}           # label → address
pz_next = pz_base

def pz_const(name, val):
    global pz_next
    pz[name] = pz_next
    emit(f"deposit {pz_next:03o} {val:06o}")
    pz_next += 1

emit("; Page-zero constants")
pz_const("zero", 0)

# FN values for DEP protocol
pz_const("fn_dep_tma", FN_DEP_TMA)
# PS DEP: word 0 (MSB), no TMA inc
pz_const("fn_dep_ps_w0", fn_dep_ps(0))
# PS DEP: word 1
pz_const("fn_dep_ps_w1", fn_dep_ps(1))
# PS DEP: word 2
pz_const("fn_dep_ps_w2", fn_dep_ps(2))
# PS DEP: word 3 (LSB), with TMA increment
pz_const("fn_dep_ps_w3_inc", fn_dep_ps(3, inc_tma=True))
# DEP into SPD
pz_const("fn_dep_spd", FN_DEP_SPD)
# DEP into PSA
pz_const("fn_dep_psa", FN_DEP_PSA)
# FN START
pz_const("fn_start", FN_START)

# DMA setup values
# Host→AP DMA: CTRL = CC(0x80) + APDMA(0x40) = 0xC0 = 0300 octal
pz_const("dma_ctl_h2a", 0o300)
# AP→Host DMA: CTRL = CC + APDMA + WRTHOST(0x20) = 0xE0 = 0340 octal
pz_const("dma_ctl_a2h", 0o340)

# Word counts: 2 host words per 38-bit float × count
# For 2 floats (A+B): WC=4
pz_const("wc_in", 4)
# For 1 float result: WC=2
pz_const("wc_out", 2)

# AP memory addresses
pz_const("apma_zero", 0)
pz_const("apma_two", 2)  # Result location

# S-pad value (base address of A = 0)
pz_const("sp_val_0", 0)

# Microcode words (4 per instruction, 5 instructions = 20 values)
mc_labels = []
for i, w in enumerate(microcode):
    ws = instr_to_octal_words(w)
    for j in range(4):
        name = f"mc_{i}_w{j}"
        pz_const(name, ws[j])
        mc_labels.append(name)

emit("")

# ── Input data in host memory (at 0o600) ──────────────────────────

host_data_addr = 0o600
emit(f"; Input data at host address {host_data_addr:03o}")
emit(f"; A={test_a}: hi={a_hi:04X} lo={a_lo:04X}, B={test_b}: hi={b_hi:04X} lo={b_lo:04X}")
emit(f"deposit {host_data_addr:03o} {a_hi:06o}")
emit(f"deposit {host_data_addr+1:03o} {a_lo:06o}")
emit(f"deposit {host_data_addr+2:03o} {b_hi:06o}")
emit(f"deposit {host_data_addr+3:03o} {b_lo:06o}")
pz_const("host_in_addr", host_data_addr)

# Result area in host memory (at 0o610)
host_result_addr = 0o610
emit(f"; Result area at host address {host_result_addr:03o}")
emit(f"deposit {host_result_addr:03o} 0")
emit(f"deposit {host_result_addr+1:03o} 0")
emit(f"; Expected C={test_c_expected}: hi={c_hi:04X} lo={c_lo:04X}")
pz_const("host_out_addr", host_result_addr)

emit("")
emit(f"; Page-zero used: {pz_base:03o}-{pz_next-1:03o} ({pz_next - pz_base} words)")
emit("")

# ── DG Nova program (at 0o200) ─────────────────────────────────────

pc = 0o200
prog = []

def inst(opcode, comment=""):
    global pc
    prog.append((pc, opcode, comment))
    pc += 1

emit("; DG Nova program at 0o200")
emit("; Phase 1: Load microcode into PS[0..4] via FN DEP")

# Set TMA=0: SWR ← 0, DOAS FN=DEP_TMA
inst(dg_lda(0, 0, pz["zero"]), "LDA 0,zero")
inst(dg_doa(0, PULSE_N, DEV_FPS), "DOA 0,FPS  ; SWR ← 0")
inst(dg_lda(0, 0, pz["fn_dep_tma"]), "LDA 0,fn_dep_tma")
inst(dg_doa(0, PULSE_S, DEV_FPS), "DOAS 0,FPS ; FN ← DEP TMA (set TMA=0)")

# Load 5 microcode instructions, each = 4 words
for i in range(len(microcode)):
    ws = instr_to_octal_words(microcode[i])
    for w_idx in range(4):
        label = f"mc_{i}_w{w_idx}"
        # SWR ← word value
        inst(dg_lda(0, 0, pz[label]), f"LDA 0,{label}")
        inst(dg_doa(0, PULSE_N, DEV_FPS), f"DOA 0,FPS  ; SWR ← PS[{i}] word {w_idx}")
        # FN ← DEP PS word (last word of each instruction increments TMA)
        if w_idx < 3:
            fn_label = f"fn_dep_ps_w{w_idx}"
        else:
            fn_label = "fn_dep_ps_w3_inc"
        inst(dg_lda(0, 0, pz[fn_label]), f"LDA 0,{fn_label}")
        inst(dg_doa(0, PULSE_S, DEV_FPS), f"DOAS 0,FPS ; FN ← DEP PS w{w_idx}{' +TMA' if w_idx==3 else ''}")

emit("")
emit("; Phase 2: Load S-pad (SP[0]=0, base address of A)")
# Only need SP[0] = 0 for our minimal program
inst(dg_lda(0, 0, pz["sp_val_0"]), "LDA 0,sp_val_0")
inst(dg_doa(0, PULSE_N, DEV_FPS), "DOA 0,FPS  ; SWR ← 0 (SP[0])")
inst(dg_lda(0, 0, pz["fn_dep_spd"]), "LDA 0,fn_dep_spd")
inst(dg_doa(0, PULSE_S, DEV_FPS), "DOAS 0,FPS ; FN ← DEP SPD")

emit("")
emit("; Phase 3: DMA Host→AP (load 2 floats into MD[0] and MD[1])")
# Set APMA=0
inst(dg_lda(0, 0, pz["apma_zero"]), "LDA 0,apma_zero")
inst(dg_dob(0, PULSE_C, DEV_FPS), "DOBC 0,FPS ; APMA ← 0")
# Set HMA=host_in_addr
inst(dg_lda(0, 0, pz["host_in_addr"]), "LDA 0,host_in_addr")
inst(dg_dob(0, PULSE_S, DEV_FPS), "DOBS 0,FPS ; HMA ← host_in_addr")
# Set WC=4 (2 floats × 2 words each)
inst(dg_lda(0, 0, pz["wc_in"]), "LDA 0,wc_in")
inst(dg_dob(0, PULSE_N, DEV_FPS), "DOB 0,FPS  ; WC ← 4")
# Set CTRL (Host→AP, float format, auto-inc APMA)
inst(dg_lda(0, 0, pz["dma_ctl_h2a"]), "LDA 0,dma_ctl_h2a")
inst(dg_doa(0, PULSE_C, DEV_FPS), "DOAC 0,FPS ; CTRL ← Host→AP")
# Start DMA (DOBP)
inst(dg_dob(0, PULSE_P, DEV_FPS), "DOBP 0,FPS ; start DMA")

# Wait for DMA done (SKPDN dev 056)
dma_poll_addr = pc
inst(dg_skp(SKPDN, DEV_FPS + 1), "SKPDN 056  ; DMA done?")
inst(dg_jmp(1, 0xFF), "JMP .-1    ; loop")

emit("")
emit("; Phase 4: START AP at PSA=0, poll SKPDN 055")
# Set PSA=0
inst(dg_lda(0, 0, pz["zero"]), "LDA 0,zero")
inst(dg_doa(0, PULSE_N, DEV_FPS), "DOA 0,FPS  ; SWR ← 0 (PSA)")
inst(dg_lda(0, 0, pz["fn_dep_psa"]), "LDA 0,fn_dep_psa")
inst(dg_doa(0, PULSE_S, DEV_FPS), "DOAS 0,FPS ; FN ← DEP PSA")

# START
inst(dg_lda(0, 0, pz["fn_start"]), "LDA 0,fn_start")
inst(dg_doa(0, PULSE_S, DEV_FPS), "DOAS 0,FPS ; FN ← START")

# Wait for DONE (SKPDN 055)
run_poll_addr = pc
inst(dg_skp(SKPDN, DEV_FPS), "SKPDN 055  ; RUN done?")
inst(dg_jmp(1, 0xFF), "JMP .-1    ; loop")

emit("")
emit("; Phase 5: DMA AP→Host (read result from MD[2])")
# Set APMA=2
inst(dg_lda(0, 0, pz["apma_two"]), "LDA 0,apma_two")
inst(dg_dob(0, PULSE_C, DEV_FPS), "DOBC 0,FPS ; APMA ← 2")
# Set HMA=host_out_addr
inst(dg_lda(0, 0, pz["host_out_addr"]), "LDA 0,host_out_addr")
inst(dg_dob(0, PULSE_S, DEV_FPS), "DOBS 0,FPS ; HMA ← host_out_addr")
# Set WC=2 (1 float × 2 words)
inst(dg_lda(0, 0, pz["wc_out"]), "LDA 0,wc_out")
inst(dg_dob(0, PULSE_N, DEV_FPS), "DOB 0,FPS  ; WC ← 2")
# Set CTRL (AP→Host)
inst(dg_lda(0, 0, pz["dma_ctl_a2h"]), "LDA 0,dma_ctl_a2h")
inst(dg_doa(0, PULSE_C, DEV_FPS), "DOAC 0,FPS ; CTRL ← AP→Host")
# Start DMA
inst(dg_dob(0, PULSE_P, DEV_FPS), "DOBP 0,FPS ; start DMA")

# Wait for DMA done
inst(dg_skp(SKPDN, DEV_FPS + 1), "SKPDN 056  ; DMA done?")
inst(dg_jmp(1, 0xFF), "JMP .-1    ; loop")

# HALT
inst(dg_halt(), "HALT")

emit("")

# Write all program deposits
for addr, opcode, comment in prog:
    emit(f"deposit {addr:03o} {opcode:06o}")

emit("")
emit(f"; Program: {0o200:03o}-{pc-1:03o} ({pc - 0o200} words)")
emit("")

# ── Run and verify ──────────────────────────────────────────────────

emit("go 200")
emit(f'echo "=== Full Pipeline Test: {test_a} + {test_b} = {test_c_expected} ==="')
emit(f'echo "Expected: {host_result_addr:03o}={c_hi:06o}, {host_result_addr+1:03o}={c_lo:06o} (IEEE32 {test_c_expected})"')
emit(f'echo "Actual:"')
emit(f"examine {host_result_addr:03o}-{host_result_addr+1:03o}")
emit("")
emit("quit")

# ── Output ──────────────────────────────────────────────────────────

script = "\n".join(out) + "\n"
outfile = sys.argv[1] if len(sys.argv) > 1 else "/dev/stdout"
if outfile == "/dev/stdout":
    print(script, end="")
else:
    with open(outfile, 'w') as f:
        f.write(script)
    print(f"Generated {outfile} ({len(prog)} Nova instructions, {len(microcode)} AP instructions)", file=sys.stderr)
