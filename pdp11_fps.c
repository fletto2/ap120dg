/* pdp11_fps.c: FPS AP-120B / FPS-100 array processor, Unibus

   Copyright (c) 2026, Usagi Electric Community

   Permission is hereby granted, free of charge, to any person obtaining a
   copy of this software and associated documentation files (the "Software"),
   to deal in the Software without restriction, including without limitation
   the rights to use, copy, modify, merge, publish, distribute, sublicense,
   and/or sell copies of the Software, and to permit persons to whom the
   Software is furnished to do so, subject to the following conditions:

   The above copyright notice and this permission notice shall be included in
   all copies or substantial portions of the Software.

   fps          FPS AP-120B / FPS-100 array processor

   Phase 1 implementation: host interface + memory + DMA + panel commands.
   No AP microcode execution yet (AP always halted unless START issued,
   then runs until explicit STOP).

   I/O mapping (derived from 280B schematic 512-3280-004 Rev B):

     Writes — flag selects register within DOx channel:
     DOA  ac,FPS (none) → LDSR*    → write SWR
     DOAS ac,FPS (S)    → LDFN*    → write FN (command)
     DOAC ac,FPS (C)    → HCTLCLK* → write CTRL
     DOAP ac,FPS (P)    → INTCLK*  → interrupt AP (APIRT)
     DOB  ac,FPS (none) → HWCCLK*  → write WC
     DOBS ac,FPS (S)    → HMACLK*  → write HMA
     DOBC ac,FPS (C)    → HADRCLK* → write APMA
     DOBP ac,FPS (P)    → HDMACLK* → start DMA
     DOC  ac,FPS (none) → B0CLK*   → write FMTH
     DOCS ac,FPS (S)    → B2CLK*   → write FMTL

     Reads — flag selects register via HOSTRS mux:
     DIA  ac,FPS (none) → FN2HD    → read FN status
     DIAS ac,FPS (S)    → SR2HD    → read SWR
     DIAC ac,FPS (C)    → LT2HD    → read LITES
     DIAP ac,FPS (P)    → HADR2HD* → read APMA
     DIB  ac,FPS        → BH2HD*   → read FMTH
     DIC  ac,FPS        → BL2HD*   → read FMTL

     Three DONE/BUSY pairs (subdevice address):
     Subdevice 0: RUN DONE / RUN BUSY  (AP execution status)
     Subdevice 1: DMA DONE / DMA BUSY  (DMA transfer status)
     Subdevice 2: CTL05 DONE / CTL05 BUSY (programmed interrupt)

   APIN/APOUT register numbering (from DAPEX.MAC TABLE):
     1=SWR, 2=FN, 3=LITES, 4=APMA, 5=HMA, 6=WC, 7=CTL,
     8=FMTH, 9=FMTL, 10=RESET

   Reference: AP-120B Processor Handbook, 860-7259-003, Feb 1979
*/

#include "pdp11_defs.h"
#include <string.h>
#include <math.h>

/* Device code */
#define DEV_FPS         055
#define DEV_FPS_DMA     056                     /* Subdevice 1: DMA */
#define DEV_FPS_CTL5    057                     /* Subdevice 2: CTL05 */

/* Interrupt vectors — one bit per subdevice in dev_busy/dev_done */
#define INT_V_FPS       1                       /* Subdevice 0: RUN */
#define INT_FPS         (1 << INT_V_FPS)
#define INT_V_FPSDMA    2                       /* Subdevice 1: DMA */
#define INT_FPSDMA      (1 << INT_V_FPSDMA)
#define INT_V_FPSCTL5   3                       /* Subdevice 2: CTL05 */
#define INT_FPSCTL5     (1 << INT_V_FPSCTL5)
#define PI_FPS          0000020

/* FN command bits (bit 0 = MSB) */
#define FN_STOP         0x8000
#define FN_START        0x4000
#define FN_CONT         0x2000
#define FN_STEP         0x1000
#define FN_RESET        0x0800
#define FN_EXAM         0x0400
#define FN_DEP          0x0200
#define FN_BREAK        0x0100
#define FN_INC_MASK     0x00C0
#define FN_INC_SHIFT    6
#define FN_WORD_MASK    0x0030
#define FN_WORD_SHIFT   4
#define FN_REGSEL_MASK  0x000F

/* FN status bits (read) */
#define FN_HALTED       0x8000
#define FN_SWR_ACK      0x4000

/* CTL register bits */
#define CTL_WC_ZERO     0x8000
#define CTL_INTR_AP     0x4000
#define CTL_TAPWC       0x2000
#define CTL_IHHALT      0x1000
#define CTL_IHWC        0x0800
#define CTL_IHENB       0x0400
#define CTL_FERR        0x0200
#define CTL_DLATE       0x0100
#define CTL_CC          0x0080
#define CTL_APDMA       0x0040
#define CTL_WRTHOST     0x0020
#define CTL_DECAPMA     0x0010
#define CTL_DECHMA      0x0008
#define CTL_FMT_MASK    0x0006
#define CTL_HDMA        0x0001

/* CTL read-only mask */
#define CTL_RO_MASK     (CTL_WC_ZERO | CTL_FERR | CTL_DLATE)

/* Memory sizes */
#define PS_SIZE         4096            /* Program Store: 4K x 64-bit */
#define MD_SIZE         65536           /* Main Data: 64K x 38-bit (stored in 64-bit) */
#define TM_SIZE         8192            /* Table Memory: 8K for trig + constants */
#define SP_SIZE         16              /* Scratch Pad: 16 x 16-bit (0-15, octal 0-17) */
#define SRS_SIZE        16              /* Subroutine Return Stack */

/* REG SELECT values for FN EXAM/DEP */
#define REGSEL_PSA      0
#define REGSEL_SPD      1
#define REGSEL_MA       2
#define REGSEL_TMA      3
#define REGSEL_DPA      4
#define REGSEL_SPFN     5
#define REGSEL_STATUS   6
#define REGSEL_DA       7
#define REGSEL_PS_TMA   8       /* Program Source addressed by TMA */
#define REGSEL_CB       9       /* Control Buffer (EXAM only) */
#define REGSEL_DPX      10
#define REGSEL_DPY      11
#define REGSEL_DPZ      12
#define REGSEL_MD_MA    13      /* Main Data addressed by MA */
#define REGSEL_SPFN_E   14      /* SPFN (EXAM only) */
#define REGSEL_TM_TMA   15      /* Table Memory by TMA (EXAM only) */

/* 64-bit instruction word field extraction macros
   Bit 0 = MSB of the 64-bit word (stored in t_uint64)
   Field positions from SIM100.FTN SPLIT routine */

#define FPS_FIELD(w, start, width) \
    ((int32)(((w) >> (63 - (start) - (width) + 1)) & ((1 << (width)) - 1)))

#define FPS_DF(w)    FPS_FIELD(w, 0, 1)    /* SPEC selector */
#define FPS_SOP(w)   FPS_FIELD(w, 1, 3)    /* S-pad operation */
#define FPS_SH(w)    FPS_FIELD(w, 4, 2)    /* Shift */
#define FPS_SPS(w)   FPS_FIELD(w, 6, 4)    /* S-pad source reg */
#define FPS_SPD(w)   FPS_FIELD(w, 10, 4)   /* S-pad dest reg */
#define FPS_FADD(w)  FPS_FIELD(w, 14, 3)   /* Float adder op */
#define FPS_A1(w)    FPS_FIELD(w, 17, 3)   /* Adder input 1 */
#define FPS_A2(w)    FPS_FIELD(w, 20, 3)   /* Adder input 2 */
#define FPS_COND(w)  FPS_FIELD(w, 23, 4)   /* Branch condition */
#define FPS_DISP(w)  FPS_FIELD(w, 27, 5)   /* Branch displacement (signed) */
#define FPS_DPX(w)   FPS_FIELD(w, 32, 2)   /* DP X source */
#define FPS_DPY(w)   FPS_FIELD(w, 34, 2)   /* DP Y source */
#define FPS_DPBS(w)  FPS_FIELD(w, 36, 3)   /* DP bus select */
#define FPS_XR(w)    FPS_FIELD(w, 39, 3)   /* DPX read index */
#define FPS_YR(w)    FPS_FIELD(w, 42, 3)   /* DPY read index */
#define FPS_XW(w)    FPS_FIELD(w, 45, 3)   /* DPX write index */
#define FPS_YW(w)    FPS_FIELD(w, 48, 3)   /* DPY write / VALUE hi */
#define FPS_FM(w)    FPS_FIELD(w, 51, 1)   /* Float multiply start */
#define FPS_M1(w)    FPS_FIELD(w, 52, 2)   /* Multiplier input 1 */
#define FPS_M2(w)    FPS_FIELD(w, 54, 2)   /* Multiplier input 2 */
#define FPS_MI(w)    FPS_FIELD(w, 56, 2)   /* Memory input select */
#define FPS_MA_OP(w) FPS_FIELD(w, 58, 2)   /* MA operation */
#define FPS_DPA_OP(w) FPS_FIELD(w, 60, 2)  /* DPA operation */
#define FPS_TMA_OP(w) FPS_FIELD(w, 62, 2)  /* TMA operation */
#define FPS_VALUE(w) ((int32)((w) & 0xFFFF)) /* 16-bit immediate (bits 48-63) */

/* S-pad operations (SOP field, DF=0) */
#define SOP_NOP     0
#define SOP_SPEC    1       /* SPEC mode: redefines SPS/SPD fields */
#define SOP_ADD     2
#define SOP_SUB     3
#define SOP_MOV     4
#define SOP_AND     5
#define SOP_OR      6
#define SOP_EQV     7

/* S-pad operations with SOP=1 (SPEC), SPS field encodes operation */
#define SPS_NOP     0
#define SPS_WRTEXP  1
#define SPS_WRTHMN  2
#define SPS_WRTLMN  3
#define SPS_CLR     8
#define SPS_INC     9
#define SPS_DEC     10
#define SPS_COM     11
#define SPS_LDSPI   14      /* Load S-pad immediate (VALUE -> SPD) */

/* Branch conditions (COND field) */
#define COND_NOP    0
#define COND_BR     2       /* Unconditional branch */
#define COND_RET    7       /* Return from subroutine */
#define COND_BEQ    12      /* Branch if s-pad condition EQ */
#define COND_BNE    13
#define COND_BGE    14
#define COND_BGT    15

/* SPEC field operations (when DF=1, SOP=1) */
#define SPEC_HOSTPNL 1     /* Host panel operation */
#define SPEC_SETPSA  2     /* Set PSA from s-pad */
#define SPEC_HALT    5     /* Halt AP */

/* Data Pad Bus Select (DPBS) */
#define DPBS_NOP    0
#define DPBS_DB     1       /* Data bus */
#define DPBS_VALUE  2       /* 16-bit immediate value */

/* MA/DPA/TMA operations */
#define ADDR_NOP    0
#define ADDR_INC    1
#define ADDR_DEC    2
#define ADDR_SET    3       /* Set from s-pad */

/* Data Pad sizes */
#define DPX_SIZE    32
#define DPY_SIZE    32

/* Host memory is reached through the Unibus map, not directly. */
extern int32 AMASK;                                     /* Nova address mask */

/* Host interface registers */
static int32 fps_swr;                   /* Switch Register */
static int32 fps_fn_status;             /* FN status (read) */
static int32 fps_lites;                 /* Lights register */
static int32 fps_ctl;                   /* Control register */
static int32 fps_wc;                    /* Word Count */
static int32 fps_hma;                   /* Host Memory Address */
static int32 fps_apma;                  /* AP Memory Address */
static int32 fps_fmth;                  /* Format High */
static int32 fps_fmtl;                  /* Format Low */

/* AP internal state */
static int32 fps_running;               /* AP running flag */
static int32 fps_psa;                   /* Program Source Address */
static int32 fps_sra;                   /* Subroutine Return Address (stack ptr) */
static int32 fps_ma;                    /* Main Data Address */
static int32 fps_tma;                   /* Table Memory Address */
static int32 fps_dpa;                   /* Data Pad Address */
/* Main data read pipeline.  SIM100 line 1316 says it outright: "FETCH MD
   FROM MA SET THREE CYCLES AGO IF A READ WAS DONE THEN".  A read started
   by SETMA at cycle N lands in MDR at N+3, and the production math
   library depends on it -- VADD issues SETMA two instructions before the
   DPX<MD that consumes the value.  Reading memory instantly puts the
   wrong vector element in the data pads. */
static t_uint64 fps_mdb[3];             /* MDB1..MDB3 */
static int32 fps_mdb_v[3];              /* valid flags, SIM100's MDBn(7) */
static t_uint64 fps_mdr;                /* memory data register */
static int32 fps_da;                    /* Device Address */
static int32 fps_ap_status;             /* AP internal status register */
static int32 fps_spfn;                  /* S-Pad Function output */
static int32 fps_spd_ptr;              /* S-Pad Destination pointer (host DEP) */

static int32 fps_spad[SP_SIZE];         /* Scratch Pad registers */
static int32 fps_srs[SRS_SIZE];         /* Subroutine Return Stack */

/* Data Pads (38-bit values stored in 64-bit) */
static t_uint64 fps_dpx[DPX_SIZE];        /* Data Pad X */
static t_uint64 fps_dpy[DPY_SIZE];        /* Data Pad Y */

/* Pipeline registers (38-bit in 64-bit)
   Real AP-120B has 2-stage pipeline: FPADD→FAB1→FAB2→FA.
   FADD result enters FAB1, shifts to FAB2 next cycle, then to FA.
   So FA reflects the FADD from 2 cycles ago. */
static t_uint64 fps_fa;                   /* Floating Adder output (delayed) */
static t_uint64 fps_fab1;                 /* Adder pipeline stage 1 */
static t_uint64 fps_fab2;                 /* Adder pipeline stage 2 */
static t_uint64 fps_fm;                   /* Floating Multiplier output */
static t_uint64 fps_fmb1, fps_fmb2, fps_fmb3; /* Multiplier pipeline */
static t_uint64 fps_a1, fps_a2;           /* Adder inputs */
static t_uint64 fps_m1, fps_m2;           /* Multiplier inputs */
static t_uint64 fps_inbs;                /* I/O input bus */
static t_uint64 fps_dpbs;                /* Data Pad bus */
static t_uint64 fps_cb;                   /* Control Buffer (current instruction) */
static int32 fps_trace = 0;               /* per-cycle trace to stdout */
static int32 fps_trace_n = 0;             /* cycles remaining to trace */
static t_uint64 tr_dpx, tr_dpy;           /* pad operands, for the trace only */
static int32 tr_xr, tr_yr, tr_xw;

/* AP memory (allocated dynamically, fps_ps is extern for loader) */
t_uint64 *fps_ps;                         /* Program Store (64-bit words) */
static t_uint64 *fps_md;                  /* Main Data (38-bit in 64-bit) */

/* Table Memory ROM */
static t_uint64 *fps_tm;               /* Table Memory ROM (allocated in reset) */

/* DMA state */
static int32 fps_dma_active;            /* DMA transfer in progress */
static int32 fps_dma_phase;             /* 0=first word, 1=second word */
static uint16 fps_dma_buf;              /* Buffer for 2-word transfers */

/* Three-subdevice DONE/BUSY model (SimH only provides one pair via dev_busy/dev_done,
   which we map to subdevice 0 = RUN. Subdevices 1 and 2 are tracked internally.) */
static int32 fps_dma_busy;              /* Subdevice 1: DMA BUSY */
static int32 fps_dma_done;              /* Subdevice 1: DMA DONE */
static int32 fps_ctl05_busy;            /* Subdevice 2: CTL05 BUSY */
static int32 fps_ctl05_done;            /* Subdevice 2: CTL05 DONE */

/* Execution state */
static int32 fps_spcond;                 /* S-pad condition code */
static int32 fps_facond;                 /* Float adder condition (current) */
static int32 fps_facond_br;              /* ...as the branch field sees it */

/* Function prototypes */
/* ---- PDP-11 Unibus host interface -------------------------------------

   The register block and its offsets are DAPEX.MAC's, and the base
   address and vector are the ones FPS's own DRV100.CMD offers as the
   defaults when it generates FPSMC.MAC:

        CSR 176000, vector 170, CSRSIZ 120(8)

        000  FMTH   format high            010x unused
        002  FMTL   format low
        100  WC     word count for DMA
        102  HMA    host memory address
        104  CTRL   control (interrupts, DMA go, AP interrupt)
        106  APMA   AP memory address
        110  SWR    switch register  (host -> AP)
        112  FN     function/status  (read status, write command)
        114  LITES  lights                 (read only -- no write strobe
                                            exists on the real board)
        116  ABRT   reset

   The Nova build reached host memory as M[] directly.  On the Unibus the
   transfer has to go through the map, so DMA uses Map_ReadW/Map_WriteW.  */

#define FPS_BASE        0176000
#define FPS_VEC         0170
#define FPS_IPL         5

/* Register offsets, in words from the base */
#define FPSR_FMTH       000
#define FPSR_FMTL       001
#define FPSR_WC         040
#define FPSR_HMA        041
#define FPSR_CTRL       042
#define FPSR_APMA       043
#define FPSR_SWR        044
#define FPSR_FN         045
#define FPSR_LITES      046
#define FPSR_ABRT       047

static void fps_process_fn_command (int32 cmd);

/* The Nova build kept host status in dev_busy/dev_done.  On the Unibus the
   host reads FN instead, so these become no-ops; interrupts are not raised
   yet and DAPEX polls FN, which is the documented handshake. */
#define DEV_SET_BUSY(x)
#define DEV_CLR_BUSY(x)
#define DEV_SET_DONE(x)
#define DEV_CLR_DONE(x)
#define DEV_UPDATE_INTR

static void fps_signal_halt (void);
static void fps_signal_dma_done (void);
static void fps_dma_cycle (void);
static void fps_execute_cycle (void);
static void fps_write_reg (int32 regsel, int32 val);
static int32 fps_read_reg (int32 regsel);
static void fps_init_table_memory (void);
static t_uint64 fps_double_to_38bit (double d);
static double fps_38bit_to_double (t_uint64 v);
extern t_stat fps_load_apo (FILE *f);
t_stat fps_rd (int32 *data, int32 PA, int32 access);
t_stat fps_wr (int32 data, int32 PA, int32 access);
t_stat fps_reset (DEVICE *dptr);
t_stat fps_svc (UNIT *uptr);
t_stat fps_attach (UNIT *uptr, CONST char *cptr);
t_stat fps_detach (UNIT *uptr);

#define IOLN_FPS        0120

DIB fps_dib = {
    FPS_BASE, IOLN_FPS, &fps_rd, &fps_wr,
    0, 0, 0, { NULL }, IOLN_FPS
    };

UNIT fps_unit = { UDATA (&fps_svc, UNIT_ATTABLE, 0) };

REG fps_reg[] = {
    { ORDATA (SWR,      fps_swr,        16) },
    { ORDATA (FN,       fps_fn_status,  16) },
    { ORDATA (LITES,    fps_lites,      16) },
    { ORDATA (CTRL,     fps_ctl,        16) },
    { ORDATA (WC,       fps_wc,         16) },
    { ORDATA (HMA,      fps_hma,        16) },
    { ORDATA (APMA,     fps_apma,       16) },
    { ORDATA (FMTH,     fps_fmth,       16) },
    { ORDATA (FMTL,     fps_fmtl,       16) },
    { ORDATA (PSA,      fps_psa,        16) },
    { ORDATA (MA,       fps_ma,         16) },
    { ORDATA (TMA,      fps_tma,        16) },
    { ORDATA (DPA,      fps_dpa,        16) },
    { FLDATA (RUNNING,  fps_running,     0) },
    { ORDATA (TRACE,    fps_trace,       1) },
    { DRDATA (TRACEN,   fps_trace_n,    32) },
    { NULL }
    };

MTAB fps_mod[] = {
    { MTAB_XTD|MTAB_VDV|MTAB_VALR, 010, "ADDRESS", "ADDRESS",
      &set_addr, &show_addr, NULL, "Bus address" },
    { MTAB_XTD|MTAB_VDV|MTAB_VALR, 0, "VECTOR", "VECTOR",
      &set_vec, &show_vec, NULL, "Interrupt vector" },
    { 0 }
    };

DEVICE fps_dev = {
    "FPS", &fps_unit, fps_reg, fps_mod,
    1, 8, 16, 1, 8, 16,
    NULL, NULL, &fps_reset,
    NULL, &fps_attach, &fps_detach,
    &fps_dib, DEV_DISABLE | DEV_DIS | DEV_UBUS | DEV_DEBUG
    };


/* Read an AP internal register by REGSEL value */

static int32 fps_read_reg (int32 regsel)
{
switch (regsel) {
    case REGSEL_PSA:     return fps_psa;
    case REGSEL_SPD:     return fps_spd_ptr;             /* SPD pointer */
    case REGSEL_MA:      return fps_ma;
    case REGSEL_TMA:     return fps_tma;
    case REGSEL_DPA:     return fps_dpa;
    case REGSEL_SPFN:    return fps_spfn;
    case REGSEL_STATUS:  return fps_ap_status;
    case REGSEL_DA:      return fps_da;
    case REGSEL_PS_TMA:                                 /* PS word addressed by TMA */
        if (fps_ps && fps_tma < PS_SIZE)
            return (int32)(fps_ps[fps_tma] & 0xFFFF);  /* Low 16 bits */
        return 0;
    case REGSEL_MD_MA:                                  /* MD word addressed by MA */
        if (fps_md && fps_ma < MD_SIZE)
            return (int32)(fps_md[fps_ma] & 0xFFFF);
        return 0;
    case REGSEL_TM_TMA:                                 /* Table Memory by TMA */
        if (fps_tm && fps_tma < TM_SIZE)
            return (int32)(fps_tm[fps_tma] & 0xFFFF);
        return 0;
    default:
        return 0;
    }
}


/* Write an AP internal register by REGSEL value */

static void fps_write_reg (int32 regsel, int32 val)
{
switch (regsel) {
    case REGSEL_PSA:     fps_psa = val & 0xFFF; break;
    case REGSEL_SPD:     fps_spd_ptr = val & 0xF; break;    /* Set SPD pointer */
    case REGSEL_MA:      fps_ma = val & 0xFFFF; break;
    case REGSEL_TMA:     fps_tma = val & 0xFFFF; break;
    case REGSEL_DPA:     fps_dpa = val & 0xFF; break;
    case REGSEL_SPFN:                                      /* DEP into SPFN → write to spad[SPD] */
        fps_spfn = val & 0xFFFF;
        if (fps_spd_ptr < SP_SIZE)
            fps_spad[fps_spd_ptr] = val & 0xFFFF;
        break;
    case REGSEL_STATUS:  fps_ap_status = val & 0xFFFF; break;
    case REGSEL_DA:      fps_da = val & 0xFF; break;
    case REGSEL_PS_TMA:                                 /* Write to PS by TMA */
        if (fps_ps && fps_tma < PS_SIZE) {
            /* WORD field selects which 16-bit portion of 64-bit word */
            /* Handled by caller via fps_process_fn_command */
            fps_ps[fps_tma] = (fps_ps[fps_tma] & ~0xFFFFULL) | (val & 0xFFFF);
            }
        break;
    case REGSEL_MD_MA:                                  /* Write to MD by MA */
        if (fps_md && fps_ma < MD_SIZE)
            fps_md[fps_ma] = (fps_md[fps_ma] & ~0xFFFFULL) | (val & 0xFFFF);
        break;
    default:
        break;
    }
}

/* Read a host interface register. */

t_stat fps_rd (int32 *data, int32 PA, int32 access)
{
int32 rg = (PA >> 1) & 077;

switch (rg) {

    case FPSR_FMTH:  *data = fps_fmth & 0177777;  break;
    case FPSR_FMTL:  *data = fps_fmtl & 0177777;  break;
    case FPSR_WC:    *data = fps_wc   & 0177777;  break;
    case FPSR_HMA:   *data = fps_hma  & 0177777;  break;
    case FPSR_CTRL:  *data = fps_ctl  & 0177777;  break;
    case FPSR_APMA:  *data = fps_apma & 0177777;  break;
    case FPSR_SWR:   *data = fps_swr  & 0177777;  break;

    case FPSR_FN:                                       /* status */
        *data = fps_fn_status & 0177777;
        break;

    case FPSR_LITES:                                    /* read only */
        *data = fps_lites & 0177777;
        break;

    default:
        *data = 0;
        break;
        }
return SCPE_OK;
}

/* Write a host interface register. */

t_stat fps_wr (int32 data, int32 PA, int32 access)
{
int32 rg = (PA >> 1) & 077;

switch (rg) {

    case FPSR_FMTH:  fps_fmth = data & 0177777;  break;
    case FPSR_FMTL:  fps_fmtl = data & 0177777;  break;
    case FPSR_WC:    fps_wc   = data & 0177777;  break;
    case FPSR_HMA:   fps_hma  = data & 0177777;  break;
    case FPSR_APMA:  fps_apma = data & 0177777;  break;
    case FPSR_SWR:   fps_swr  = data & 0177777;  break;

    case FPSR_CTRL:                                     /* control */
        fps_ctl = (data & ~CTL_RO_MASK) | (fps_ctl & CTL_RO_MASK);
        if (fps_ctl & CTL_INTR_AP)                        /* interrupt the AP */
            fps_fn_status |= FN_SWR_ACK;
        if (fps_ctl & CTL_HDMA) {                     /* start DMA */
            fps_dma_active = 1;
            fps_dma_phase = 0;
            sim_activate (&fps_unit, 1);
            }
        break;

    case FPSR_FN:                                       /* command */
        fps_process_fn_command (data & 0177777);
        break;

    case FPSR_LITES:                                    /* no write strobe */
        break;

    case FPSR_ABRT:                                     /* reset */
        fps_reset (&fps_dev);
        break;

    default:
        break;
        }
return SCPE_OK;
}



/* Signal AP halt to host — sets RUN DONE (subdevice 0) and optionally
   interrupts the host if CTL_IHHALT is enabled. Called from every code
   path that sets fps_running=0 / fps_fn_status|=FN_HALTED. */

static void fps_signal_halt (void)
{
fps_running = 0;
fps_fn_status |= FN_HALTED;
DEV_CLR_BUSY( INT_FPS );                               /* Clear RUN BUSY */
DEV_SET_DONE( INT_FPS );                               /* Set RUN DONE */
if (fps_ctl & CTL_IHHALT)                              /* If halt interrupt enabled */
    DEV_UPDATE_INTR;
}

/* Signal DMA completion — sets DMA DONE (subdevice 1) and optionally
   interrupts the host if CTL_IHWC is enabled. */

static void fps_signal_dma_done (void)
{
fps_dma_active = 0;
fps_dma_phase = 0;
fps_dma_busy = 0;
fps_dma_done = 1;
fps_ctl &= ~CTL_HDMA;
fps_ctl |= CTL_WC_ZERO;                                /* Set WC=0 status bit */
/* Set DMA DONE on subdevice 1 (device code 056) */
DEV_CLR_BUSY( INT_FPSDMA );
DEV_SET_DONE( INT_FPSDMA );
if (fps_ctl & CTL_IHWC)                                /* If DMA-done interrupt enabled */
    DEV_UPDATE_INTR;
}


/* Process FN command word */

static void fps_process_fn_command (int32 cmd)
{
int32 regsel = cmd & FN_REGSEL_MASK;
int32 word = (cmd & FN_WORD_MASK) >> FN_WORD_SHIFT;
int32 inc = (cmd & FN_INC_MASK) >> FN_INC_SHIFT;

if (cmd & FN_RESET) {
    fps_swr = 0;
    fps_lites = 0;
    fps_ctl = 0;
    fps_wc = 0;
    fps_hma = 0;
    fps_apma = 0;
    fps_fmth = 0;
    fps_fmtl = 0;
    fps_running = 0;
    fps_psa = 0;
    fps_sra = 0;
    fps_ma = 0;
    fps_tma = 0;
    fps_dpa = 0;
fps_mdb[0] = fps_mdb[1] = fps_mdb[2] = 0;
fps_mdb_v[0] = fps_mdb_v[1] = fps_mdb_v[2] = 0;
fps_mdr = 0;
    fps_da = 0;
    fps_ap_status = 0;
    fps_spfn = 0;
    fps_dma_active = 0;
    fps_dma_busy = 0;
    fps_dma_done = 0;
    fps_ctl05_busy = 0;
    fps_ctl05_done = 0;
    memset (fps_spad, 0, sizeof (fps_spad));
    memset (fps_srs, 0, sizeof (fps_srs));
    fps_fn_status = FN_HALTED;
    return;
    }

if (cmd & FN_STOP) {
    fps_signal_halt ();
    }

if (cmd & FN_START) {
    int32 max_cycles;
    fps_psa = fps_swr & 0xFFF;
    fps_running = 1;
    fps_fn_status &= ~FN_HALTED;
    /* Execute AP synchronously until halt or max cycles */
    for (max_cycles = 0; max_cycles < 100000 && fps_running; max_cycles++)
        fps_execute_cycle ();
    if (fps_running)                                    /* Still running? Schedule async */
        sim_activate (&fps_unit, 10);
    }

if (cmd & FN_CONT) {
    int32 max_cycles;
    fps_running = 1;
    fps_fn_status &= ~FN_HALTED;
    for (max_cycles = 0; max_cycles < 100000 && fps_running; max_cycles++)
        fps_execute_cycle ();
    if (fps_running)
        sim_activate (&fps_unit, 10);
    }

if (cmd & FN_STEP) {
    /* Execute one instruction then halt */
    fps_running = 1;
    fps_fn_status &= ~FN_HALTED;
    fps_execute_cycle ();
    fps_signal_halt ();
    }

if (cmd & FN_DEP) {
    /* Deposit SWR into selected register/memory */
    if (regsel == REGSEL_PS_TMA && fps_ps && fps_tma < PS_SIZE) {
        /* Write to specific 16-bit portion of 64-bit PS word */
        int shift = (3 - word) * 16;                    /* word 0=bits 0-15=top */
        t_uint64 mask = 0xFFFFULL << shift;
        fps_ps[fps_tma] = (fps_ps[fps_tma] & ~mask) |
                          ((t_uint64)(fps_swr & 0xFFFF) << shift);
        }
    else if (regsel == REGSEL_MD_MA && fps_md && fps_ma < MD_SIZE) {
        /* Write to 16-bit portion of 38-bit MD word */
        /* word 0 = bits 0-15 (mantissa high), word 1 = bits 16-31 (mantissa low + exp) */
        int shift = (1 - word) * 16;
        if (shift >= 0) {
            t_uint64 mask = 0xFFFFULL << shift;
            fps_md[fps_ma] = (fps_md[fps_ma] & ~mask) |
                             ((t_uint64)(fps_swr & 0xFFFF) << shift);
            }
        }
    else {
        fps_write_reg (regsel, fps_swr);
        }
    fps_fn_status |= FN_SWR_ACK;

    /* Handle INC field */
    switch (inc) {
        case 1: fps_ma++;  fps_ma &= 0xFFFF; break;
        case 2: fps_dpa++; fps_dpa &= 0xFF;  break;
        case 3: fps_tma++; fps_tma &= 0xFFFF; break;
        }
    }

if (cmd & FN_EXAM) {
    /* Examine: copy register to LITES for host to read via DIB */
    if (regsel == REGSEL_PS_TMA && fps_ps && fps_tma < PS_SIZE) {
        int shift = (3 - word) * 16;
        fps_lites = (int32)((fps_ps[fps_tma] >> shift) & 0xFFFF);
        }
    else if (regsel == REGSEL_MD_MA && fps_md && fps_ma < MD_SIZE) {
        int shift = (1 - word) * 16;
        if (shift >= 0)
            fps_lites = (int32)((fps_md[fps_ma] >> shift) & 0xFFFF);
        else
            fps_lites = 0;
        }
    else {
        fps_lites = fps_read_reg (regsel);
        }

    /* Handle INC for EXAM too */
    switch (inc) {
        case 1: fps_ma++;  fps_ma &= 0xFFFF; break;
        case 2: fps_dpa++; fps_dpa &= 0xFF;  break;
        case 3: fps_tma++; fps_tma &= 0xFFFF; break;
        }
    }

if (cmd & FN_BREAK) {
    /* Set breakpoint at address in SWR -- not implemented yet */
    }
}


/* Unit service -- DMA cycle processing */

t_stat fps_svc (UNIT *uptr)
{
int32 cycles;

/* Execute AP instructions if running */
if (fps_running && fps_ps) {
    for (cycles = 0; cycles < 100 && fps_running; cycles++)
        fps_execute_cycle ();
    }

/* Process DMA if active */
if (fps_dma_active)
    fps_dma_cycle ();

/* Reschedule if AP is running or DMA active */
if (fps_running || fps_dma_active)
    sim_activate (uptr, 10);

return SCPE_OK;
}


/* Forward declarations for FP helpers (defined below DMA section) */
static int32 fp_get_exp (t_uint64 val);
static int32 fp_get_mant (t_uint64 val);
static t_uint64 fp_pack (int32 exp, int32 mant);

/* Format conversion: AP 38-bit float <-> host 32-bit float
   AP format:  bits 37-28 = 10-bit exponent (biased 512)
               bits 27-0  = 28-bit mantissa (2's complement)
   Host format (PDP-11/DG 32-bit):
               bit 31 = sign
               bits 30-23 = 8-bit exponent (biased 128)
               bits 22-0  = 23-bit mantissa (unsigned, hidden 1)

   Note: DG Nova 32-bit float may differ from PDP-11. For now we
   use a generic 32-bit IEEE-like format. */

static t_uint64 fps_host_to_ap_float (uint16 hi, uint16 lo)
{
int32 sign, hexp, hmant, aexp, amant;
uint32 host32 = ((uint32)hi << 16) | lo;

if (host32 == 0) return 0;

sign = (host32 >> 31) & 1;
hexp = (host32 >> 23) & 0xFF;
hmant = host32 & 0x7FFFFF;

/* Restore hidden bit */
hmant |= 0x800000;

/* Convert exponent: AP bias 512, host bias 127.
   IEEE: value = hmant × 2^(hexp-150)  [hmant is 24-bit with hidden 1]
   AP:   value = amant × 2^(aexp-540)  [amant is 28-bit 2's complement]
   With amant = hmant << 3: aexp = hexp + 387.
   The <<3 shift puts 24-bit hmant into [2^26, 2^27), keeping bit 27
   clear so the 28-bit 2's complement sign is correct for positive values. */
aexp = hexp + (512 - 125);

/* Shift 24-bit mantissa to 28-bit: <<3 keeps bit 27 (sign) clear */
amant = hmant << 3;

/* Apply sign (2's complement for AP) */
if (sign)
    amant = -amant;

return fp_pack (aexp, amant);
}

static void fps_ap_to_host_float (t_uint64 ap_val, uint16 *hi, uint16 *lo)
{
int32 aexp, amant, sign, hexp, hmant;
uint32 host32;

if (ap_val == 0) { *hi = 0; *lo = 0; return; }

aexp = fp_get_exp (ap_val);
amant = fp_get_mant (ap_val);

sign = (amant < 0) ? 1 : 0;
if (sign) amant = -amant;

/* Convert exponent (inverse of host-to-AP: aexp = hexp + 387) */
hexp = aexp - (512 - 125);
if (hexp <= 0 || hexp >= 255) { *hi = 0; *lo = 0; return; }

/* Shift 28-bit mantissa to 24-bit (>>3, inverse of <<3), strip hidden bit */
hmant = (amant >> 3) & 0x7FFFFF;

host32 = (sign << 31) | (hexp << 23) | hmant;
*hi = (uint16)(host32 >> 16);
*lo = (uint16)(host32 & 0xFFFF);
}


/* Execute one DMA cycle (transfer one host word) */

static void fps_dma_cycle (void)
{
int32 fmt;
uint16 host_word, hi_word, lo_word;

if (fps_wc == 0 || !fps_dma_active) {
    fps_signal_dma_done ();
    return;
    }

fmt = (fps_ctl & CTL_FMT_MASK) >> 1;

if (fps_ctl & CTL_WRTHOST) {
    /* AP -> Host */
    switch (fmt) {
        case 0:                                         /* 38-bit float conversion */
            if (fps_dma_phase == 0) {
                if (fps_md && fps_apma < MD_SIZE)
                    fps_ap_to_host_float (fps_md[fps_apma], &hi_word, &lo_word);
                else { hi_word = 0; lo_word = 0; }
                host_word = hi_word;
                fps_dma_buf = lo_word;
                fps_dma_phase = 1;
                }
            else {
                host_word = fps_dma_buf;
                fps_dma_phase = 0;
                /* Advance AP address after second word */
                if (fps_ctl & CTL_APDMA) {
                    fps_apma += (fps_ctl & CTL_DECAPMA) ? -1 : 1;
                    fps_apma &= 0xFFFF;
                    }
                }
            break;

        case 1:                                         /* 32-bit integer (2 words, no conversion) */
            if (fps_dma_phase == 0) {
                t_uint64 ap_val = (fps_md && fps_apma < MD_SIZE) ? fps_md[fps_apma] : 0;
                host_word = (uint16)((ap_val >> 16) & 0xFFFF);
                fps_dma_buf = (uint16)(ap_val & 0xFFFF);
                fps_dma_phase = 1;
                }
            else {
                host_word = fps_dma_buf;
                fps_dma_phase = 0;
                if (fps_ctl & CTL_APDMA) {
                    fps_apma += (fps_ctl & CTL_DECAPMA) ? -1 : 1;
                    fps_apma &= 0xFFFF;
                    }
                }
            break;

        case 2:                                         /* 16-bit integer (1 word) */
        default:
            host_word = (fps_md && fps_apma < MD_SIZE) ?
                (uint16)(fps_md[fps_apma] & 0xFFFF) : 0;
            if (fps_ctl & CTL_APDMA) {
                fps_apma += (fps_ctl & CTL_DECAPMA) ? -1 : 1;
                fps_apma &= 0xFFFF;
                }
            break;
        }
    {                                                   /* AP -> host */
    uint16 w = (uint16) host_word;
    Map_WriteW (fps_hma & 0777777, 2, &w);
    }
    }
else {
    /* Host -> AP */
    {                                                   /* host -> AP */
    uint16 w = 0;
    Map_ReadW (fps_hma & 0777777, 2, &w);
    host_word = w;
    }

    switch (fmt) {
        case 0:                                         /* 38-bit float conversion */
            if (fps_dma_phase == 0) {
                fps_dma_buf = host_word;                /* Save high word */
                fps_dma_phase = 1;
                }
            else {
                if (fps_md && fps_apma < MD_SIZE) {
                    fps_md[fps_apma] = fps_host_to_ap_float (fps_dma_buf, host_word);
                    }
                fps_dma_phase = 0;
                if (fps_ctl & CTL_APDMA) {
                    fps_apma += (fps_ctl & CTL_DECAPMA) ? -1 : 1;
                    fps_apma &= 0xFFFF;
                    }
                }
            break;

        case 1:                                         /* 32-bit integer (2 words) */
            if (fps_dma_phase == 0) {
                fps_dma_buf = host_word;
                fps_dma_phase = 1;
                }
            else {
                if (fps_md && fps_apma < MD_SIZE)
                    fps_md[fps_apma] = ((t_uint64)fps_dma_buf << 16) | host_word;
                fps_dma_phase = 0;
                if (fps_ctl & CTL_APDMA) {
                    fps_apma += (fps_ctl & CTL_DECAPMA) ? -1 : 1;
                    fps_apma &= 0xFFFF;
                    }
                }
            break;

        case 2:                                         /* 16-bit integer (1 word) */
        default:
            if (fps_md && fps_apma < MD_SIZE)
                fps_md[fps_apma] = (t_uint64)host_word;
            if (fps_ctl & CTL_APDMA) {
                fps_apma += (fps_ctl & CTL_DECAPMA) ? -1 : 1;
                fps_apma &= 0xFFFF;
                }
            break;
        }
    }

/* Update host address */
fps_hma += (fps_ctl & CTL_DECHMA) ? -1 : 1;
fps_hma &= 0xFFFF;

/* Decrement word count */
fps_wc = (fps_wc - 1) & 0xFFFF;

if (fps_wc == 0)
    fps_signal_dma_done ();
}


/* 38-bit FPS floating point format:
   Bits 37-28: 10-bit exponent (biased by 512)
   Bits 27-0:  28-bit mantissa (2's complement)
   Stored in low 38 bits of a t_uint64 */

#define FP_EXP_SHIFT    28
#define FP_EXP_MASK     0x3FF
#define FP_MANT_MASK    0x0FFFFFFFULL
#define FP_EXP_BIAS     512
#define FP_38_MASK      0x3FFFFFFFFFULL

static int32 fp_get_exp (t_uint64 val)
{
return (int32)((val >> FP_EXP_SHIFT) & FP_EXP_MASK);
}

static int32 fp_get_mant (t_uint64 val)
{
int32 mant = (int32)(val & FP_MANT_MASK);
if (mant & 0x08000000)                                 /* Sign extend 28-bit */
    mant |= (int32)0xF0000000;
return mant;
}

/* 38-bit AP float -> double, for tracing only. */
static double fps_38bit_to_double (t_uint64 val)
{
int32 exp = fp_get_exp (val);
int32 mant = fp_get_mant (val);
if (mant == 0) return 0.0;
return (double)mant / 268435456.0 * pow (2.0, (double)(exp - FP_EXP_BIAS));
}

static t_uint64 fp_pack (int32 exp, int32 mant)
{
return ((t_uint64)(exp & FP_EXP_MASK) << FP_EXP_SHIFT) |
       ((t_uint64)mant & FP_MANT_MASK);
}

static t_uint64 fps_38bit_add (t_uint64 a, t_uint64 b)
{
int32 exp_a = fp_get_exp (a), exp_b = fp_get_exp (b);
int32 mant_a = fp_get_mant (a), mant_b = fp_get_mant (b);
int32 result_exp, result_mant, diff;

if (mant_a == 0) return b;
if (mant_b == 0) return a;

diff = exp_a - exp_b;
result_exp = (diff >= 0) ? exp_a : exp_b;
if (diff > 0) mant_b >>= diff;
else if (diff < 0) mant_a >>= -diff;

result_mant = mant_a + mant_b;

/* Normalize */
if (result_mant == 0) return 0;
while (result_mant > 0x07FFFFFF || result_mant < -0x08000000) {
    result_mant >>= 1;
    result_exp++;
    }
while (result_mant != 0 &&
       result_mant < 0x04000000 && result_mant > -0x04000000) {
    result_mant <<= 1;
    result_exp--;
    }
if (result_exp >= (int32)FP_EXP_MASK || result_exp <= 0) return 0;
return fp_pack (result_exp, result_mant);
}

static t_uint64 fps_38bit_sub (t_uint64 a, t_uint64 b)
{
int32 exp_b = fp_get_exp (b);
int32 mant_b = fp_get_mant (b);
if (mant_b == 0) return a;
return fps_38bit_add (a, fp_pack (exp_b, -mant_b));
}

static t_uint64 fps_38bit_mul (t_uint64 a, t_uint64 b)
{
int32 exp_a = fp_get_exp (a), exp_b = fp_get_exp (b);
int32 mant_a = fp_get_mant (a), mant_b = fp_get_mant (b);
t_int64 prod;
int32 result_exp, result_mant;

if (mant_a == 0 || mant_b == 0) return 0;

prod = (t_int64)mant_a * (t_int64)mant_b;
result_mant = (int32)(prod >> 27);                     /* Scale 56-bit product to 28-bit */
result_exp = exp_a + exp_b - FP_EXP_BIAS;

/* Normalize */
if (result_mant == 0) return 0;
while (result_mant > 0x07FFFFFF || result_mant < -0x08000000) {
    result_mant >>= 1;
    result_exp++;
    }
while (result_mant < 0x04000000 && result_mant > -0x04000000) {
    result_mant <<= 1;
    result_exp--;
    }
if (result_exp >= (int32)FP_EXP_MASK || result_exp <= 0) return 0;
return fp_pack (result_exp, result_mant);
}


/* Execute one AP instruction cycle */

static void fps_execute_cycle (void)
{
t_uint64 instr;
int32 df, sop, sh, sps, spd, fadd_op, cond, disp;
int32 ma_op, dpa_op, tma_op, dpbs, use_value, mem_cycle;
int32 spsr_val, result, branch, psa_set = 0;

if (!fps_running || !fps_ps)
    return;
if (fps_psa >= PS_SIZE) {
    fps_signal_halt ();
    return;
    }

/* Fetch instruction from Program Store */
instr = fps_ps[fps_psa];
fps_cb = instr;

if (fps_trace && fps_trace_n != 0) {
    printf ("[%4d] %06o,%06o,%06o,%06o",
            fps_psa,
            (int32)((instr >> 48) & 0xFFFF), (int32)((instr >> 32) & 0xFFFF),
            (int32)((instr >> 16) & 0xFFFF), (int32)(instr & 0xFFFF));
    }


/* Memory data register: SIM100 label 12600, before the operands are used.
   MDB3 -> MDR only when MDB3 holds a completed read. */
if (fps_mdb_v[2] == 1)
    fps_mdr = fps_mdb[2];

/* Pipeline shift: FAB2→FA every cycle (unconditional, per SIM100 line 1338).
   This must happen before any early returns (HALT, JMP, RETURN, etc.)
   so that the pipeline advances even on control flow instructions. */
fps_fa = fps_fab2;
/* FACOND is a TWO-BIT code, not a sign: SIM100 line 1347 takes
   FACOND = MOD(FAB2(7),4) from the adder's condition element, and the
   branch tests read it as bit0 = zero, bit1 = negative.  That is why
   BFGT is "FACOND .EQ. 0" (positive and non-zero) rather than a
   greater-than comparison. */
/* The branch field runs BEFORE this update and reads the condition out
   of STATUS(1) (SIM100 line 1233), which was written at label 30000 at
   the end of the PREVIOUS cycle -- so a branch tests the adder condition
   as of one cycle earlier, not the result landing in FA right now. */
fps_facond_br = fps_facond;
fps_facond = 0;
if (fps_fab2 == 0)
    fps_facond |= 1;                                    /* zero */
else if (fp_get_mant (fps_fab2) < 0)
    fps_facond |= 2;                                    /* negative */



/* Decode fields */
df      = FPS_DF(instr);
sop     = FPS_SOP(instr);
sh      = FPS_SH(instr);
sps     = FPS_SPS(instr);
spd     = FPS_SPD(instr);
fadd_op = FPS_FADD(instr);
cond    = FPS_COND(instr);
disp    = FPS_DISP(instr);
dpbs    = FPS_DPBS(instr);
ma_op   = FPS_MA_OP(instr);
dpa_op  = FPS_DPA_OP(instr);
tma_op  = FPS_TMA_OP(instr);

/* Check if VALUE field is active (disables YW, FM, M1, M2, MI, MA, TMA, DPA) */
use_value = (dpbs == DPBS_VALUE) ||
            (df == 0 && sop == SOP_SPEC && sps >= 8 && sps <= 12 && (spd & 7) <= 3);

/* S-pad source read */
spsr_val = (sps < SP_SIZE) ? fps_spad[sps] : 0;

/* Check for SPEC operations FIRST (SOP=1, SPS<8) — these take priority
   and return immediately without further processing */
if (df == 0 && sop == SOP_SPEC && sps < 8) {
    switch (sps) {
        case 1:                                         /* HOSTPNL: SWDB */
            fps_fn_status ^= FN_SWR_ACK;
            break;
        case 5:                                         /* HALT */
            fps_signal_halt ();
            return;
        case 8:                                         /* JMP/JSR */
            {
            int32 ps_mode = (spd >> 1) & 3;
            int32 target = 0;
            switch (ps_mode) {
                case 0: target = FPS_VALUE(instr) & 0xFFF; break;
                case 1: target = (fps_psa + (int16_t)FPS_VALUE(instr)) & 0xFFF; break;
                case 2: target = fps_tma & 0xFFFF; break;
                case 3: target = fps_swr & 0xFFF; break;
                }
            if (spd & 1) {                              /* JSR */
                fps_srs[fps_sra & 0xF] = (fps_psa + 1) & 0xFFF;
                fps_sra = (fps_sra + 1) & 0xF;
                }
            fps_psa = target;
            return;
            }
        case 12:                                        /* SETEXIT */
            fps_srs[fps_sra & 0xF] = (fps_psa + 1) & 0xFFF;
            break;
        default:
            break;
        }
    /* Advance PSA and return (SPEC ops don't do s-pad or data pad) */
    fps_psa = (fps_psa + 1) & 0xFFF;
    return;
    }

/* DF=1 HALT check (early return) */
if (df == 1 && sop == SOP_SPEC && sps == 5) {
    fps_signal_halt ();
    return;
    }

/* Branch evaluation */
branch = 0;
switch (cond) {
    case COND_NOP:  break;                              /* No branch */
    case COND_BR:   branch = 1; break;                  /* Unconditional */
    case COND_RET:                                      /* Return from subroutine */
        if (fps_sra > 0) {
            fps_sra--;
            fps_psa = fps_srs[fps_sra & 0xF];
            psa_set = 1;                                /* Skip normal PSA advance */
            }
        break;                                          /* Let rest of cycle complete */
    case 3:  branch = 1; break;                          /* BINTRQ - interrupt request */
    case 4:  branch = 1; break;                          /* BION - I/O ready (stub: always) */
    case 5:  branch = 0; break;                          /* BIOZ - I/O not ready */
    case 6:  branch = 0; break;                          /* BFPE  - FP error not modelled */
    /* SIM100 dispatches I=CONDF+1 to labels 11110..11113, so:
         8  FACOND .EQ. 2          negative            BFLT
         9  FACOND .NE. 2          not negative        BFGE
        10  MOD(FACOND,2) .EQ. 0   not zero            BFNE
        11  FACOND .EQ. 0          positive non-zero   BFGT
       BFEQ is NOT here -- it lives in the STEST field below. */
    case 8:  branch = (fps_facond_br == 2); break;          /* BFLT */
    case 9:  branch = (fps_facond_br != 2); break;          /* BFGE */
    case 10: branch = ((fps_facond_br & 1) == 0); break;    /* BFNE */
    case 11: branch = (fps_facond_br == 0); break;          /* BFGT */
    case COND_BEQ:  branch = (fps_spcond == 0); break;   /* s-pad EQ */
    case COND_BNE:  branch = (fps_spcond != 0); break;   /* s-pad NE */
    case COND_BGE:  branch = (fps_spcond >= 0); break;   /* s-pad GE */
    case COND_BGT:  branch = (fps_spcond > 0);  break;   /* s-pad GT */
    default:        break;
    }

/* STEST field (SIM100 label 11500): when SOP=1 and SPS=0 the SPD field
   selects a further test, and this is where BFEQ lives -- MOD(FACOND,2)
   .EQ. 1, i.e. the adder result was zero.  Without it a loop that exits
   on "count reached zero" never exits. */
if (sop == 1 && sps == 0) {
    switch (spd) {
        case 0: branch = ((fps_facond_br & 1) == 1); break;   /* BFEQ  */
        case 1: branch = (((fps_spcond >> 1) & 1) == 1); break;/* s-pad negative */
        case 2: branch = ((fps_spcond & 1) == 1); break;      /* s-pad zero */
        case 3: branch = ((fps_spcond & 1) == 0); break;      /* s-pad non-zero */
        /* 12-15 test a bit of the FLAG register, which is not modelled */
        default: break;                              /* 4-7 DPBS/status, 12-15 FLAG */
        }
    }

/* S-pad operation (when DF=0) */
if (df == 0) {
    int32 spad_single_op = 0;                           /* SOP=0, SPS>=8 group */
    result = spsr_val;

    switch (sop) {
        case SOP_NOP:
            /* SOP=0 is only a true no-op when SPS<8.  SOP=0 with SPS>=8 is
               the single-operand group, which operates on SPD and writes
               back (SIM100 label 13100; the NOP test is at label 13000:
               IXNOP = SOPF==1 .OR. (SOPF==0 .AND. SPSF<8)). */
            if (sps < 8)
                goto skip_spad_write;
            spad_single_op = 1;
            switch (sps) {
                case 8:  result = 0; break;                       /* CLR */
                case 9:  result = (fps_spad[spd] + 1) & 0xFFFF; break;  /* INC */
                case 10: result = (fps_spad[spd] - 1) & 0xFFFF; break;  /* DEC */
                case 11: result = (~fps_spad[spd]) & 0xFFFF; break;     /* COM */
                default: result = fps_spad[spd]; break;           /* 12-15: MOV SPD */
                }
            break;
        case SOP_SPEC:                                  /* SPEC mode */
            /* SPS 0-7 are SPEC ops (HALT, SWDB, JMP/JSR) handled later.
               SPS 8 is dual: CLR when SPD>3, JMP/JSR when SPD<=3 (use_value).
               SPS 9-12 are always s-pad ops. */
            if (sps < 8)
                goto skip_spad_write;  /* Pure SPEC ops, no s-pad */
            switch (sps) {
                case SPS_CLR:                           /* CLR SPD */
                    result = 0;
                    break;
                case SPS_INC:                           /* INC SPD */
                    result = (fps_spad[spd] + 1) & 0xFFFF;
                    break;
                case SPS_DEC:                           /* DEC SPD */
                    result = (fps_spad[spd] - 1) & 0xFFFF;
                    break;
                case SPS_COM:                           /* COM (complement) SPD */
                    result = (~fps_spad[spd]) & 0xFFFF;
                    break;
                case SPS_LDSPI:                         /* Load immediate VALUE -> SPD */
                    result = FPS_VALUE(instr);
                    break;
                default:
                    result = spsr_val;
                    break;
                }
            break;
        case SOP_ADD:
            result = (fps_spad[spd] + spsr_val) & 0xFFFF;
            break;
        case SOP_SUB:
            result = (fps_spad[spd] - spsr_val) & 0xFFFF;
            break;
        case SOP_MOV:
            result = spsr_val;
            break;
        case SOP_AND:
            result = fps_spad[spd] & spsr_val;
            break;
        case SOP_OR:
            result = fps_spad[spd] | spsr_val;
            break;
        case SOP_EQV:
            result = ~(fps_spad[spd] ^ spsr_val) & 0xFFFF;
            break;
        }

    /* Shift */
    switch (sh) {
        case 0: break;                                  /* No shift */
        case 1: result = ((result << 1) | (result >> 15)) & 0xFFFF; break; /* L */
        case 2: result = ((result >> 1) | (result << 15)) & 0xFFFF; break; /* R */
        case 3: result = ((result >> 1) & 0x7FFF);     /* RR (logical right) */
                break;
        }

    /* Set s-pad condition code */
    if (result == 0)
        fps_spcond = 0;
    else if (result & 0x8000)
        fps_spcond = -1;                                /* Negative */
    else
        fps_spcond = 1;                                 /* Positive */

    /* Write result to SPD (unless NOP or JMP/JSR).  SIM100 label 13880 also
       suppresses the write when COND=1 (STEST), which uses the s-pad ALU
       purely to set condition bits. */
    if ((sop != SOP_NOP || spad_single_op) && spd < SP_SIZE && cond != 1 &&
        !(sop == SOP_SPEC && sps == 8 && use_value))
        fps_spad[spd] = result & 0xFFFF;

    /* SPFN output = result (available for deposit into DP, etc.) */
    fps_spfn = result;
    }

/* SPEC field operations (when DF=0, SOP=1) */
if (df == 0 && sop == SOP_SPEC) {
    int32 spec = sps;                                   /* SPS field = SPEC code */

    switch (spec) {
        case 8:                                         /* JMP/JSR */
            {
            /* Compute target address from SPD subfield */
            int32 ps_mode = (spd >> 1) & 3;
            int32 target = 0;
            switch (ps_mode) {
                case 0: target = FPS_VALUE(instr) & 0xFFF; break;   /* Absolute from VALUE */
                case 1: target = (fps_psa + (int16_t)FPS_VALUE(instr)) & 0xFFF; break; /* PC-relative */
                case 2: target = fps_tma & 0xFFFF; break;            /* TMA */
                case 3: target = fps_swr & 0xFFF; break;            /* SWR (host panel) */
                }
            if (spd & 1) {                              /* JSR (odd SPD) */
                fps_srs[fps_sra & 0xF] = (fps_psa + 1) & 0xFFF;
                fps_sra = (fps_sra + 1) & 0xF;
                }
            fps_psa = target;
            return;                                     /* Don't advance PSA */
            }

        case 1:                                         /* HOSTPNL: SWDB */
            fps_fn_status ^= FN_SWR_ACK;
            return;                                     /* Don't write to SPD */

        case 5:                                         /* HALT */
            fps_signal_halt ();
            return;

        case 12:                                        /* SETEXIT */
            fps_srs[fps_sra & 0xF] = (fps_psa + 1) & 0xFFF;
            break;

        default:
            break;
        }
    }

/* DF=1 operations: bit reversal and extended ops */
if (df == 1) {
    if (sop == SOP_SPEC) {
        int32 spec = sps;
        if (spec == 5) {                                /* HALT */
            fps_signal_halt ();
            return;
            }
        }
    else if (sop != SOP_NOP) {
        /* Bit reversal: reverse bits of SPS register, right-shifted by
           amount in STATUS register low 3 bits. Used by FFT. */
        int32 shift = fps_ap_status & 7;
        int32 nbits = 15 - shift;
        int32 val = spsr_val & 0x7FFF;
        int32 rev = 0;
        int32 i;
        for (i = 0; i < nbits; i++) {
            rev = (rev << 1) | (val & 1);
            val >>= 1;
            }
        rev <<= 1;                                     /* Left-justify in 16-bit */
        fps_spfn = rev & 0xFFFF;
        if (spd < SP_SIZE)
            fps_spad[spd] = fps_spfn;
        /* Set condition code */
        if (fps_spfn == 0)
            fps_spcond = 0;
        else if (fps_spfn & 0x8000)
            fps_spcond = -1;
        else
            fps_spcond = 1;
        }
    }

/* I/O operations (when DF=1, SOP != SPEC) */
if (df == 1 && sop != SOP_SPEC) {
    /* OUT instruction: write s-pad to I/O device addressed by DA */
    /* IN instruction: read I/O device into data pad bus */
    /* LDDA: load device address from VALUE or s-pad */
    /* Simplified: just handle LDDA and basic I/O */
    switch (sop) {
        case 2: /* LDDA */
            fps_da = use_value ? (FPS_VALUE(instr) & 0xFF) : (spsr_val & 0xFF);
            break;
        case 3: /* OUT */
            /* Write to device addressed by DA */
            switch (fps_da) {
                case 0:  fps_wc = spsr_val; break;      /* WC */
                case 1:  fps_hma = spsr_val; break;     /* HMA */
                case 2:  fps_ctl = (spsr_val & ~CTL_RO_MASK) | (fps_ctl & CTL_RO_MASK); break;
                case 3:  fps_apma = spsr_val; break;    /* APMA */
                default: break;
                }
            break;
        case 4: /* LDOMA (load output memory address) */
            fps_ma = use_value ? (FPS_VALUE(instr) & 0xFFFF) : (spsr_val & 0xFFFF);
            break;
        case 5: /* LDDPA (load data pad address) */
            fps_dpa = use_value ? (FPS_VALUE(instr) & 0xFF) : (spsr_val & 0xFF);
            break;
        case 6: /* SWDB (switch data bus -- toggle SWR ack) */
            fps_fn_status ^= FN_SWR_ACK;
            break;
        case 7: /* IN (read from I/O device addressed by DA) */
            switch (fps_da) {
                case 0:  fps_inbs = fps_wc; break;
                case 1:  fps_inbs = fps_hma; break;
                case 2:  fps_inbs = fps_ctl; break;
                case 3:  fps_inbs = fps_apma; break;
                default: fps_inbs = 0; break;
                }
            break;
        default:
            break;
        }
    }

skip_spad_write: ;                                     /* Jump here to skip s-pad write */

/* --- Data Pad read with index --- */
{
int32 xr = FPS_XR(instr);
int32 yr = FPS_YR(instr);
int32 xw = FPS_XW(instr);
int32 yw = use_value ? xw : FPS_YW(instr);         /* YW disabled when VALUE active */
int32 dpx_ridx = (fps_dpa + xr - 4) & 0x1F;
int32 dpy_ridx = (fps_dpa + yr - 4) & 0x1F;
int32 dpx_widx = (fps_dpa + xw - 4) & 0x1F;
int32 dpy_widx = (fps_dpa + yw - 4) & 0x1F;
t_uint64 dpx_val = fps_dpx[dpx_ridx];
t_uint64 dpy_val = fps_dpy[dpy_ridx];
tr_dpx = dpx_val; tr_dpy = dpy_val;
tr_xr = dpx_ridx; tr_yr = dpy_ridx; tr_xw = dpx_widx;
t_uint64 md_val = fps_mdr;      /* three cycles behind SETMA */
t_uint64 fa_new = fps_fa, fm_new = fps_fm;
t_uint64 dpbs_val = 0;
int32 mi_field = use_value ? 0 : FPS_MI(instr);
int32 fm_start = use_value ? 0 : FPS_FM(instr);
int32 m1_field = use_value ? 0 : FPS_M1(instr);
int32 m2_field = use_value ? 0 : FPS_M2(instr);

/* Adder input selection.  The adder is "active" -- and therefore pushes its
   pipeline -- for every instruction except the I/O group (FADD=7) and a true
   no-op (FADD=0 with A1=0).  FADD=0 with A1!=0 is the single-operand group
   (FIX/FLOAT/SCALE, dispatched on A1); those still advance the pipeline.
   Condition transcribed from SIM100 label 35000. */
if (fadd_op != 7 && !(fadd_op == 0 && FPS_A1(instr) == 0)) {
    /* A1/A2 are architectural input latches, not per-cycle temporaries:
       SIM100 keeps them in COMMON beside FAB1/FAB2 (line 1059/1092), and
       a select field of 0 falls through to label 35200 without loading,
       so the latch retains its previous contents.  That is what makes the
       bare "FADD" push idiom work -- it re-runs the adder on the operands
       latched by the preceding instruction.
       When FADD=0 the A1 field is the single-operand sub-opcode rather
       than a source select, so A1 is not loaded at all (label 35000). */
    if (fadd_op != 0)
        /* A1 sources: 0=hold, 1=FM, 2=DPX, 3=DPY, 4=TMR, 5-7=ZERO */
        switch (FPS_A1(instr)) {
            case 0: break;                              /* hold latch */
            case 1: fps_a1 = fps_fm; break;             /* FM (multiplier) */
            case 2: fps_a1 = dpx_val; break;            /* DPX */
            case 3: fps_a1 = dpy_val; break;            /* DPY */
            case 4: fps_a1 = (fps_tm && fps_tma < TM_SIZE) ? /* TMR */
                             fps_tm[fps_tma] : 0; break;
            default: fps_a1 = 0; break;                 /* ZERO */
            }
    /* A2 sources (SIM100 line 2102):
       0=NOP, 1=FA, 2=DPX, 3=DPY, 4=MD, 5=ZERO, 6=MDPX, 7=MDPY */
    switch (FPS_A2(instr)) {
        case 0: break;                                  /* hold latch */
        case 1: fps_a2 = fps_fa; break;                 /* FA */
        case 2: fps_a2 = dpx_val; break;                /* DPX */
        case 3: fps_a2 = dpy_val; break;                /* DPY */
        case 4: fps_a2 = md_val; break;                 /* MD */
        case 5: fps_a2 = 0; break;                      /* ZERO */
        case 6:                                         /* MDPX: modify DPX */
            /* On real hardware: copies DPX mantissa and applies exponent
               from SPFN+512, then FPADD normalizes. Since DPBS=6 already
               produces a normalized float in DPX, MDPX passes it through. */
            fps_a2 = dpx_val;
            break;
        case 7:                                         /* MDPY */
            fps_a2 = dpx_val;
            break;
        }

    /* Floating adder pipeline: FPADD→FAB1, shift FAB1→FAB2.
       FAB2→FA shift already done above (unconditional). */
    fps_fab2 = fps_fab1;

    /* Compute new result into FAB1 */
    switch (fadd_op) {
        case 0:
            /* Single-operand group (SIM100 FPADD label 10000): MC<-A2,
               then A1 dispatches FIX/SCALE/FLOAT.  Those conversions are
               not implemented; pass A2 through so the pipeline still
               advances with the right timing. */
            fa_new = fps_a2;
            break;
        case 1: fa_new = fps_38bit_sub (fps_a2, fps_a1); break; /* FSUBR */
        case 2: fa_new = fps_38bit_sub (fps_a1, fps_a2); break; /* FSUB */
        case 3: fa_new = fps_38bit_add (fps_a1, fps_a2); break; /* FADD */
        case 4: fa_new = ~(fps_a1 ^ fps_a2) & FP_38_MASK; break; /* FEQV */
        case 5: fa_new = fps_a1 & fps_a2; break;        /* FAND */
        case 6: fa_new = fps_a1 | fps_a2; break;        /* FOR */
        }
    fps_fab1 = fa_new;
    }

/* Multiplier */
if (fm_start) {
    t_uint64 m1_val = 0, m2_val = 0;
    switch (m1_field) {
        case 1: m1_val = fps_fm; break;                 /* FM (previous) */
        case 2: m1_val = dpx_val; break;
        case 3: m1_val = dpy_val; break;
        }
    switch (m2_field) {
        case 1: m2_val = fps_fm; break;
        case 2: m2_val = dpx_val; break;
        case 3: m2_val = (fps_tm && fps_tma < TM_SIZE) ? fps_tm[fps_tma] : 0; break;
        }
    fps_fm = fps_38bit_mul (m1_val, m2_val);
    }

/* Data Pad Bus select */
switch (dpbs) {
    case 0: break;                                      /* NOP */
    case 1: dpbs_val = fps_inbs; break;                 /* DB (input bus) */
    case 2: dpbs_val = (t_uint64)FPS_VALUE(instr); break; /* VALUE */
    case 3: dpbs_val = dpx_val; break;                  /* DPX */
    case 4: dpbs_val = dpy_val; break;                  /* DPY */
    case 5: dpbs_val = md_val; break;                   /* MD */
    case 6:                                             /* SPFN bus (SIM100 line 23306) */
        /* Produces a normalized float from the SPFN integer value.
           On real hardware this goes through DPBS→DPX→MDPX→FPADD normalize.
           We produce the normalized result directly. */
        dpbs_val = fps_double_to_38bit((double)(int16_t)(fps_spfn & 0xFFFF));
        break;
    case 7: dpbs_val = (fps_tm && fps_tma < TM_SIZE) ? fps_tm[fps_tma] : 0; break;
    }

/* FADD=7 I/O group: register loads from DPBS value (SIM100 line 32000).
   A1=0 selects "store into regs", A2 selects which register. */
if (fadd_op == 7 && FPS_A1(instr) == 0) {
    switch (FPS_A2(instr)) {
        case 2: fps_ma = (int32)(dpbs_val & 0xFFFF); break;    /* LDMA */
        case 3: fps_tma = (int32)(dpbs_val & 0xFFFF); break;   /* LDTMA */
        case 4: fps_dpa = (int32)(dpbs_val & 0x3F); break;     /* LDDPA */
        }
    }

/* Write to Data Pads.  The DPX/DPY fields alone select the source and
   enable the write (SIM100 sections 33010-33220):
       0 = no write, 1 = DPBS, 2 = FA, 3 = FM
   The write does not depend on the DPBS bus or the adder being active
   this cycle -- DPX=2 latches whatever the adder pipeline presented in
   FA at the top of the cycle, which is how pipeline-scheduled library
   code retrieves results. */
switch (FPS_DPX(instr)) {
    case 1: fps_dpx[dpx_widx] = dpbs_val; break;
    case 2: fps_dpx[dpx_widx] = fps_fa; break;
    case 3: fps_dpx[dpx_widx] = fps_fm; break;
    }
switch (FPS_DPY(instr)) {
    case 1: fps_dpy[dpy_widx] = dpbs_val; break;
    case 2: fps_dpy[dpy_widx] = fps_fa; break;
    case 3: fps_dpy[dpy_widx] = fps_fm; break;
    }

/* Memory address updates (when not using VALUE field).

   These run BEFORE the MI write, because an MA field and an MI field in
   the SAME instruction address the same word: the write goes to the
   address this instruction establishes, not the previous one.  BAASRC's
   VADD is explicit about it --

        SUB K,C                       "BACK UP POINTER
   LOOP: ...
        ADD K,C;SETMA;MI<FA;          "STORE A(M+2)+B(M+2)

   -- C is backed up by one stride before the loop and stepped forward
   again in the very instruction that stores, so the store must see the
   stepped value.  CVADD settles it beyond doubt with

        ADD K,C; SETMA; MI<FA;        "STORE REAL
        INCMA; MI<FA;                 "STORE IMAGS

   where a pre-increment address would write the real part's word twice
   and never store the imaginary part at all.

   The read latch below already used the post-update MA, which is why
   reads paired correctly and only stores came out one element low.  */
if (!use_value) {
    switch (ma_op) {
        case ADDR_INC:  fps_ma = (fps_ma + 1) & 0xFFFF; break;
        case ADDR_DEC:  fps_ma = (fps_ma - 1) & 0xFFFF; break;
        case ADDR_SET:  fps_ma = fps_spad[spd] & 0xFFFF; break;
        }
    switch (dpa_op) {
        case ADDR_INC:  fps_dpa = (fps_dpa + 1) & 0xFF; break;
        case ADDR_DEC:  fps_dpa = (fps_dpa - 1) & 0xFF; break;
        case ADDR_SET:  fps_dpa = fps_spad[spd] & 0xFF; break;
        }
    switch (tma_op) {
        case ADDR_INC:  fps_tma = (fps_tma + 1) & 0xFFF; break;
        case ADDR_DEC:  fps_tma = (fps_tma - 1) & 0xFFF; break;
        case ADDR_SET:  fps_tma = fps_spad[spd] & 0xFFFF; break;
        }
    }

/* Memory input (MI field) - write to main data
   From SIM100.FTN line 2236: MI=1→FA, MI=2→FM, MI=3→DPBS */
if (mi_field != 0 && fps_md && fps_ma < MD_SIZE) {
    switch (mi_field) {
        case 1: fps_md[fps_ma] = fps_fa;                 /* FA (float adder) */
                break;
        case 2: fps_md[fps_ma] = fps_fm; break;        /* FM (float multiplier) */
        case 3: fps_md[fps_ma] = dpbs_val; break;      /* From DPBS */
        }
    }
}

/* Push the memory pipeline every cycle -- SIM100 label 41000, user mode
   "time-pushing" -- then start a new cycle if this instruction touched
   MA.  Order matters: the push happens after the operands were taken
   from MDR above. */
fps_mdb[2] = fps_mdb[1];  fps_mdb_v[2] = fps_mdb_v[1];
fps_mdb[1] = fps_mdb[0];  fps_mdb_v[1] = fps_mdb_v[0];
fps_mdb[0] = 0;           fps_mdb_v[0] = 0;
/* SIM100 label 41010: a memory cycle starts on a live MA field, or on
   the FADD=7 register-load forms that touch MA. */
mem_cycle = ((ma_op >= 1 && !use_value) ||
             (fadd_op == 7 && FPS_A1(instr) == 0 && FPS_A2(instr) == 2) ||
             (fadd_op == 7 && FPS_A1(instr) == 3 && FPS_A2(instr) == 1));
if (mem_cycle) {
    if ((use_value ? 0 : FPS_MI(instr)) != 0)
        fps_mdb_v[0] = -1;                     /* a write, nothing returns */
    else {
        fps_mdb_v[0] = 1;
        fps_mdb[0] = (fps_md && fps_ma < MD_SIZE) ? fps_md[fps_ma] : 0;
        }
    }


if (fps_trace && fps_trace_n != 0) {
    printf ("  FA=%.6g MD=%.6g DPXr=%.6g DPYr=%.6g MA=%o TMA=%o"
            " xr=%d yr=%d xw=%d SP=[%d %d %d %d %d %d %d] fc=%d\n",
            fps_38bit_to_double (fps_fa),
            fps_38bit_to_double ((fps_md && fps_ma < MD_SIZE) ? fps_md[fps_ma] : 0),
            fps_38bit_to_double (tr_dpx), fps_38bit_to_double (tr_dpy),
            fps_ma, fps_tma, tr_xr, tr_yr, tr_xw,
            fps_spad[0], fps_spad[1], fps_spad[2], fps_spad[3],
            fps_spad[4], fps_spad[5], fps_spad[6], fps_facond);
    if (fps_trace_n > 0)
        fps_trace_n--;
    }

/* Advance PSA (unless already set by RETURN) */
if (!psa_set) {
fps_psa = (fps_psa + 1) & 0xFFF;
if (branch) {
    /* Branch displacement: PSA = PSA + 1 + DISPF - 17
       (from SIM100.FTN: TCADD(ONE2,PSA), TCADD(DISPF,PSA), TCADD(M21,PSA)
       where M21 = -17). DISPF is unsigned 5-bit (0-31). */
    fps_psa = (fps_psa + disp - 17) & 0xFFF;
    }
}  /* end if (!psa_set) */
}  /* end fps_execute_cycle */


/* Initialize Table Memory ROM with trig tables
   The AP-120B ROM contains:
   - Sine table (1024 entries): sin(2*pi*i/1024) for i=0..1023
   - Cosine table (same, offset by 256)
   - FFT twiddle factors
   - Reciprocal/sqrt tables
   All values stored in 38-bit FPS floating point format. */

static t_uint64 *fps_tm;                               /* Table Memory ROM */

static t_uint64 fps_double_to_38bit (double val)
{
int32 exp, mant;
double abs_val;
int sign;

if (val == 0.0) return 0;

sign = (val < 0.0) ? 1 : 0;
abs_val = sign ? -val : val;

/* Compute exponent: val = mant * 2^(exp-512), mant in [0.25, 0.5) */
exp = FP_EXP_BIAS;
while (abs_val >= 0.5 && exp < (int32)FP_EXP_MASK) { abs_val *= 0.5; exp++; }
while (abs_val < 0.25 && exp > 0) { abs_val *= 2.0; exp--; }

/* Convert to 28-bit integer mantissa */
mant = (int32)(abs_val * (double)(1 << 28) + 0.5);
if (mant > 0x07FFFFFF) mant = 0x07FFFFFF;

if (sign) mant = -mant;
return fp_pack (exp, mant);
}

/* Table Memory ROM contents, taken from SIM100.FTN's TMROM block.
   FPS shipped a partial ROM image inside its own simulator: 64 FFT
   coefficients and the 301 function-coefficient words.  Its own
   comment gives the hardware layout:

       FFT-TABLE                  0 - 4095
       FUNCTION COEFFICIENTS   4096 - 4396
       HOLE                    4397 - 8191
       TMRAM                   8192 +

   4096-4396 is exactly the range SYMSRC.APS assigns its symbols, so
   these 301 words hold the scalar constants AND the coefficient
   tables that !DIV, !SQRT, !SNCS, !LOG, !EXP and !ATAN point at.
   These are the real values; they were previously computed for the
   53 scalars and zero for every coefficient.

   Each TM word is stored there as (exponent, mantissa high, mantissa
   low) and decodes as mantissa/2^27 * 2^(exp-512) -- the mantissa is
   normalised to [0.5,1).  Checked against thirteen constants whose
   values are known independently (!ONE, !PI, !E, !LN2, !GAMMA,
   !PHI, !THIRD ...): all thirteen agree.

   NOTE this differs by one power of two from fps_double_to_38bit,
   which normalises to [0.25,0.5).  The emulator is self-consistent,
   so arithmetic is unaffected, but any real ROM image or load module
   must be converted rather than copied in.  Hence the doubles here. */

static const double fps_tm_fft[64] = {
    1, 0.99969881772994995, 0.99879545718431473, 0.99729045480489731,
    0.99518472701311111, 0.99247953295707703, 0.98917651176452637, 0.98527764528989792,
    0.98078528046607971, 0.97570212930440903, 0.9700312539935112, 0.96377606689929962,
    0.95694033801555634, 0.94952818006277084, 0.9415440633893013, 0.93299280107021332,
    0.92387953400611877, 0.9142097532749176, 0.90398929268121719, 0.89322429895401001,
    0.88192126154899597, 0.87008699029684067, 0.85772860795259476, 0.84485356509685516,
    0.83146961033344269, 0.8175848126411438, 0.80320753157138824, 0.78834642469882965,
    0.77301045507192612, 0.75720884650945663, 0.74095112830400467, 0.72424708306789398,
    0.70710678398609161, 0.68954054266214371, 0.67155895382165909, 0.65317284315824509,
    0.63439328223466873, 0.61523158848285675, 0.59569930285215378, 0.57580818980932236,
    0.55557022988796234, 0.53499761968851089, 0.5141027420759201, 0.49289819225668907,
    0.47139673680067062, 0.44961132854223251, 0.42755509167909622, 0.40524131432175636,
    0.38268343359231949, 0.35989503562450409, 0.3368898518383503, 0.31368174031376839,
    0.29028467833995819, 0.26671275869011879, 0.24298018030822277, 0.21910124085843563,
    0.19509032182395458, 0.17096188850700855, 0.14673047512769699, 0.12241067551076412,
    0.098017140291631222, 0.073564563877880573, 0.049067674204707146, 0.024541228543967009,
    };

static const double fps_tm_func[301] = {
    0.0039062425494194031, 1, 2, 1.9844961166381836,
    1.9692307710647583, 1.9541984796524048, 1.939393937587738, 1.9248120337724686,
    1.9104477614164352, 1.8962962925434113, 1.8823529481887817, 1.868613138794899,
    1.8550724685192108, 1.841726616024971, 1.8285714238882065, 1.8156028389930725,
    1.8028168976306915, 1.7902097851037979, 1.7777777761220932, 1.7655172348022461,
    1.753424659371376, 1.7414965927600861, 1.7297297269105911, 1.7181207984685898,
    1.7066666632890701, 1.695364236831665, 1.6842105239629745, 1.6732026189565659,
    1.6623376607894897, 1.6516129076480865, 1.641025647521019, 1.6305732429027557,
    1.6202531605958939, 1.6100628972053528, 1.5999999940395355, 1.5900621116161346,
    1.5802469104528427, 1.5705521404743195, 1.5609756112098694, 1.5515151470899582,
    1.5421686768531799, 1.5329341292381287, 1.5238095223903656, 1.5147929042577744,
    1.5058823525905609, 1.4970760196447372, 1.4883720874786377, 1.4797687828540802,
    1.4712643623352051, 1.4628571420907974, 1.4545454531908035, 1.4463276863098145,
    1.4382022470235825, 1.4301676005125046, 1.422222226858139, 1.4143646359443665,
    1.4065934121608734, 1.3989071100950241, 1.3913043439388275, 1.3837837874889374,
    1.3763440847396851, 1.3689839541912079, 1.3617021292448044, 1.3544973582029343,
    1.3473684191703796, 1.3403141349554062, 1.3333333283662796, 1.3264248669147491,
    1.3195876330137253, 1.3128205090761185, 1.3061224520206451, 1.2994923889636993,
    1.2929292917251587, 1.2864321619272232, 1.2800000011920929, 1.2736318409442902,
    1.2673267275094986, 1.2610837370157242, 1.2549019604921341, 1.2487804889678955,
    1.242718443274498, 1.2367149740457535, 1.2307692319154739, 1.2248803824186325,
    1.2190476208925247, 1.2132701426744461, 1.2075471729040146, 1.2018779367208481,
    1.1962616890668869, 1.1906976699829102, 1.1851851791143417, 1.1797235012054443,
    1.1743119210004807, 1.168949767947197, 1.1636363565921783, 1.1583710461854935,
    1.1531531512737274, 1.1479820609092712, 1.1428571492433548, 1.1377777755260468,
    1.1327433586120605, 1.1277533024549484, 1.1228070110082626, 1.117903932929039,
    1.1130434721708298, 1.1082251071929932, 1.1034482717514038, 1.0987124443054199,
    1.0940170884132385, 1.089361697435379, 1.0847457647323608, 1.0801687836647034,
    1.075630247592926, 1.071129709482193, 1.0666666626930237, 1.0622406601905823,
    1.0578512400388718, 1.0534979403018951, 1.0491803288459778, 1.0448979586362839,
    1.0406504124403, 1.0364372432231903, 1.0322580635547638, 1.028112456202507,
    1.0240000039339066, 1.0199203193187714, 1.0158730149269104, 1.0118577033281326,
    1.0078740119934082, 1.0039215683937073, 0.0039062462747097015, 1.4142135679721832,
    1, 2, 0.70710677653551102, 0.71260964125394821,
    0.71807032823562622, 0.72348980605602264, 0.72886898368597031, 0.73420875519514084,
    0.73950996994972229, 0.74477345496416092, 0.75, 0.75519037246704102,
    0.76034531742334366, 0.76546554267406464, 0.77055174857378006, 0.77560460567474365,
    0.78062474727630615, 0.78561282157897949, 0.79056941717863083, 0.79549513012170792,
    0.80039052665233612, 0.80525617301464081, 0.81009259074926376, 0.81490030139684677,
    0.81967981904745102, 0.82443141937255859, 0.82915619760751724, 0.83385400474071503,
    0.83852548897266388, 0.84317109733819962, 0.84779124706983566, 0.85238635540008545,
    0.85695682466030121, 0.86150304973125458, 0.8660254031419754, 0.87052426487207413,
    0.875, 0.87945295125246048, 0.88388347625732422, 0.88829190284013748,
    0.89267855137586594, 0.89704375714063644, 0.90138781815767288, 0.90571104735136032,
    0.91001373529434204, 0.91429618000984192, 0.91855865716934204, 0.92280144244432449,
    0.92702481150627136, 0.93122902512550354, 0.93541434407234192, 0.93958102166652679,
    0.94372930377721786, 0.94785942882299423, 0.951971635222435, 0.95606616139411926,
    0.96014321595430374, 0.96420303732156754, 0.96824583411216736, 0.97227182239294052,
    0.97628121078014374, 0.98027419298887253, 0.9842509850859642, 0.98821176588535309,
    0.9921567440032959, 0.99608609080314636, 0.63661976903676987, 0.079689678736031055,
    0.9999999925494194, 1, 1.570796325802803, 0.00015148512829910032,
    -0.64596371352672577, -0.0046737666125409305, 2, 1.4426950365304947,
    354.18999862670898, 0.9999999925494194, -1, -355.58000183105469,
    0.0012439687852747738, 0.05548334214836359, 0.0096788409864529967, 0.00021702255435229745,
    0.24022983573377132, 0.69314698129892349, 1, 1,
    0.79370052367448807, 0.62996052205562592, 0.69314718246459961, 0.43429448083043098,
    -0.14825421571731567, -0.99999973177909851, -0.33274957537651062, -5.7905561595683608e-10,
    -0.32673035934567451, -0.25777003169059753, -0.50002061575651169, 1.1470254212617874,
    -0.99591780453920364, -0.10032295901328325, -0.00016725615205359645, -1.3069214373826981,
    -0.99836518615484238, -0.54190438240766525, 10.112391591072083, -0.79241736233234406,
    4.3431410789489746, -0.013525635935366154, -5.2276857495307922, -9.6093147993087769,
    -1.8402119129896164, 1, 0.41421356052160263, 2.4142135679721832,
    2, 0, -1.570796325802803, 0.78539816290140152,
    0.10573440231382847, -0.14240077696740627, 0.1999821662902832, -0.060346882790327072,
    -0.33333307504653931, 1, 3.1415926516056061, 2.7182818353176117,
    0.36787944287061691, 7.3890560865402222, 1.144729882478714, 1.0986122936010361,
    2.30258509516716, 0.3010299950838089, 0.31830988451838493, 0.017453292617574334,
    9.8696043491363525, 6.2831853032112122, 1.7724538445472717, 1.2599210441112518,
    1.4422495663166046, 1.1892071217298508, 1.7320508062839508, 2.2360679805278778,
    3.1622776687145233, 0.57721566408872604, 1.6180339902639389, 0.5,
    0.3333333320915699, 0.25, 0.19999999925494194, 0.16666666604578495,
    0.14285714365541935, 0.125, 0.11111111100763083, 0.09999999962747097,
    0.0625, 3, 4, 5,
    6, 7, 8, 9,
    10, 16, 0.57735026627779007, 0.44721359759569168,
    0.31622776761651039,
    };

static void fps_init_table_memory (void)
{
int32 i;
double pi2 = 6.283185307179586;

if (fps_tm == NULL) {
    fps_tm = (t_uint64 *) calloc (TM_SIZE, sizeof (t_uint64));
    if (fps_tm == NULL) return;
    }

/* Sine table: TM[0..1023] = sin(2*pi*i/1024) */
for (i = 0; i < 1024; i++)
    fps_tm[i] = fps_double_to_38bit (sin (pi2 * (double)i / 1024.0));

/* Cosine table: TM[1024..2047] = cos(2*pi*i/1024) */
for (i = 0; i < 1024; i++)
    fps_tm[1024 + i] = fps_double_to_38bit (cos (pi2 * (double)i / 1024.0));

/* Math constants (from SYMSRC.APS, octal addresses converted to decimal) */
    /* real ROM image, see the tables above */
    for (i = 0; i < (int32)(sizeof(fps_tm_fft)/sizeof(double)); i++)
        fps_tm[i] = fps_double_to_38bit (fps_tm_fft[i]);
    for (i = 0; i < (int32)(sizeof(fps_tm_func)/sizeof(double)); i++)
        fps_tm[4096 + i] = fps_double_to_38bit (fps_tm_func[i]);
}


/* Reset routine */

t_stat fps_reset (DEVICE *dptr)
{
/* Allocate AP memory if not already done */
if (fps_ps == NULL) {
    fps_ps = (t_uint64 *) calloc (PS_SIZE, sizeof (t_uint64));
    if (fps_ps == NULL)
        return SCPE_MEM;
    }
if (fps_md == NULL) {
    fps_md = (t_uint64 *) calloc (MD_SIZE, sizeof (t_uint64));
    if (fps_md == NULL)
        return SCPE_MEM;
    }

fps_swr = 0;
fps_fn_status = FN_HALTED;
fps_lites = 0;
fps_ctl = 0;
fps_wc = 0;
fps_hma = 0;
fps_apma = 0;
fps_fmth = 0;
fps_fmtl = 0;
fps_running = 0;
fps_psa = 0;
/* fps_sra preserved across reset (host deposits before go) */
fps_ma = 0;
fps_tma = 0;
fps_dpa = 0;
fps_da = 0;
fps_ap_status = 0;
fps_spfn = 0;
fps_dma_active = 0;
fps_dma_phase = 0;
fps_dma_buf = 0;
/* Preserve s-pad and SRS across reset (host deposits before go) */
memset (fps_dpx, 0, sizeof (fps_dpx));
memset (fps_dpy, 0, sizeof (fps_dpy));
fps_fa = fps_fab1 = fps_fab2 = fps_fm = fps_fmb1 = fps_fmb2 = fps_fmb3 = 0;
fps_a1 = fps_a2 = fps_m1 = fps_m2 = 0;
fps_inbs = fps_dpbs = fps_cb = 0;
fps_spcond = fps_facond = fps_facond_br = 0;
/* Don't zero PS, MD, or SPAD on reset -- preserve loaded programs and state */
/* Initialize table memory ROM on first reset */
fps_init_table_memory ();

fps_dma_busy = 0;
fps_dma_done = 0;
fps_ctl05_busy = 0;
fps_ctl05_done = 0;

DEV_CLR_BUSY( INT_FPS );
DEV_SET_DONE( INT_FPS );                               /* AP halted on reset = RUN DONE */
DEV_CLR_BUSY( INT_FPSDMA );
DEV_CLR_DONE( INT_FPSDMA );
DEV_CLR_BUSY( INT_FPSCTL5 );
DEV_CLR_DONE( INT_FPSCTL5 );
DEV_UPDATE_INTR;
sim_cancel (&fps_unit);

return SCPE_OK;
}


/* Attach handler -- loads .APO file into Program Store */

t_stat fps_attach (UNIT *uptr, CONST char *cptr)
{
t_stat r;
FILE *f;

r = attach_unit (uptr, cptr);
if (r != SCPE_OK) return r;

f = uptr->fileref;
if (f == NULL) return SCPE_OPENERR;

/* Ensure PS memory is allocated */
if (fps_ps == NULL) {
    fps_ps = (t_uint64 *) calloc (PS_SIZE, sizeof (t_uint64));
    if (fps_ps == NULL) return SCPE_MEM;
    }

r = fps_load_apo (f);
return r;
}


/* Detach handler */

t_stat fps_detach (UNIT *uptr)
{
return detach_unit (uptr);
}
