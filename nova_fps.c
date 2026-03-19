/* nova_fps.c: FPS AP-120B / FPS-100 array processor simulator

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

   I/O mapping (Hypothesis A):
     DOA ac,055       Write SWR (switch register -- data)
     DOB ac,055       Write FN  (function register -- commands)
     DOC ac,055       Write CTL (control register -- DMA/interrupt)
     DIA ac,055       Read FN status
     DIB ac,055       Read LITES (panel display / EXAM output)
     DIC ac,055       Read CTL status

   APIN/APOUT register numbering (from DAPEX.MAC TABLE):
     1=SWR, 2=FN, 3=LITES, 4=APMA, 5=HMA, 6=WC, 7=CTL,
     8=FMTH, 9=FMTL, 10=RESET

   Reference: AP-120B Processor Handbook, 860-7259-003, Feb 1979
*/

#include "nova_defs.h"
#include <string.h>
#include <math.h>

/* Device code */
#define DEV_FPS         055

/* Interrupt vector */
#define INT_V_FPS       1
#define INT_FPS         (1 << INT_V_FPS)
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
#define TM_SIZE         2560            /* Table Memory ROM: 2.5K x 38-bit */
#define SP_SIZE         16              /* Scratch Pad: 16 x 16-bit */
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

extern int32 int_req, dev_busy, dev_done, dev_disable;
extern uint16 M[];                                      /* Nova main memory */
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
static int32 fps_da;                    /* Device Address */
static int32 fps_ap_status;             /* AP internal status register */
static int32 fps_spfn;                  /* S-Pad Function output */

static int32 fps_spad[SP_SIZE];         /* Scratch Pad registers */
static int32 fps_srs[SRS_SIZE];         /* Subroutine Return Stack */

/* Data Pads (38-bit values stored in 64-bit) */
static t_uint64 fps_dpx[DPX_SIZE];        /* Data Pad X */
static t_uint64 fps_dpy[DPY_SIZE];        /* Data Pad Y */

/* Pipeline registers (38-bit in 64-bit) */
static t_uint64 fps_fa;                   /* Floating Adder output */
static t_uint64 fps_fm;                   /* Floating Multiplier output */
static t_uint64 fps_a1, fps_a2;           /* Adder inputs */
static t_uint64 fps_m1, fps_m2;           /* Multiplier inputs */
static t_uint64 fps_inbs;                /* I/O input bus */
static t_uint64 fps_dpbs;                /* Data Pad bus */
static t_uint64 fps_cb;                   /* Control Buffer (current instruction) */

/* AP memory (allocated dynamically) */
static t_uint64 *fps_ps;                  /* Program Store (64-bit words) */
static t_uint64 *fps_md;                  /* Main Data (38-bit in 64-bit) */

/* Table Memory ROM */
static t_uint64 *fps_tm;               /* Table Memory ROM (allocated in reset) */

/* DMA state */
static int32 fps_dma_active;            /* DMA transfer in progress */

/* Execution state */
static int32 fps_spcond;                 /* S-pad condition code */
static int32 fps_facond;                 /* Float adder condition */

/* Function prototypes */
int32  fps_io (int32 pulse, int32 code, int32 AC);
t_stat fps_reset (DEVICE *dptr);
t_stat fps_svc (UNIT *uptr);

static void fps_process_fn_command (int32 cmd);
static void fps_dma_cycle (void);
static int32 fps_read_reg (int32 regsel);
static void fps_write_reg (int32 regsel, int32 val);
static void fps_execute_cycle (void);
static void fps_init_table_memory (void);

/* FPS data structures */

DIB fps_dib = { DEV_FPS, INT_FPS, PI_FPS, &fps_io };

UNIT fps_unit = { UDATA (&fps_svc, 0, 0) };

REG fps_reg[] = {
    { ORDATA (SWR,      fps_swr,        16) },
    { ORDATA (FN,       fps_fn_status,  16) },
    { ORDATA (LITES,    fps_lites,      16) },
    { ORDATA (CTL,      fps_ctl,        16) },
    { ORDATA (WC,       fps_wc,         16) },
    { ORDATA (HMA,      fps_hma,        16) },
    { ORDATA (APMA,     fps_apma,       16) },
    { ORDATA (FMTH,     fps_fmth,       16) },
    { ORDATA (FMTL,     fps_fmtl,       16) },
    { ORDATA (PSA,      fps_psa,        12) },
    { ORDATA (SRA,      fps_sra,         4) },
    { ORDATA (MA,       fps_ma,         16) },
    { ORDATA (TMA,      fps_tma,        12) },
    { ORDATA (DPA,      fps_dpa,         8) },
    { ORDATA (DA,       fps_da,          8) },
    { ORDATA (STATUS,   fps_ap_status,  16) },
    { FLDATA (RUN,      fps_running,     0) },
    { FLDATA (BUSY,     dev_busy,   INT_V_FPS) },
    { FLDATA (DONE,     dev_done,   INT_V_FPS) },
    { FLDATA (DISABLE,  dev_disable,INT_V_FPS) },
    { FLDATA (INT,      int_req,    INT_V_FPS) },
    { BRDATA (SPAD,     fps_spad, 8, 16, SP_SIZE) },
    { BRDATA (SRS,      fps_srs, 8, 16, SRS_SIZE) },
    { NULL }
    };

DEVICE fps_dev = {
    "FPS", &fps_unit, fps_reg, NULL,
    1, 8, 16, 1, 8, 16,
    NULL, NULL, &fps_reset,
    NULL, NULL, NULL,
    &fps_dib, DEV_DISABLE | DEV_DEBUG
    };


/* I/O dispatch routine */

int32 fps_io (int32 pulse, int32 code, int32 AC)
{
int32 rval = 0;

/* Handle data transfers */
switch (code) {

    case ioDOA:                                         /* DOA: write SWR */
        fps_swr = AC & 0xFFFF;
        break;

    case ioDOB:                                         /* DOB: write FN (command) */
        fps_process_fn_command (AC & 0xFFFF);
        break;

    case ioDOC:                                         /* DOC: write CTL */
        fps_ctl = (AC & ~CTL_RO_MASK) | (fps_ctl & CTL_RO_MASK);
        if (AC & CTL_INTR_AP) {
            fps_fn_status |= FN_SWR_ACK;                /* Simulate AP reading SWR */
            }
        if (AC & CTL_HDMA) {                            /* Start DMA */
            fps_dma_active = 1;
            fps_ctl |= CTL_HDMA;
            sim_activate (&fps_unit, 10);               /* Schedule DMA cycles */
            }
        break;

    case ioDIA:                                         /* DIA: read FN status */
        rval = fps_fn_status;
        fps_fn_status &= ~FN_SWR_ACK;                  /* Clear ack after read */
        break;

    case ioDIB:                                         /* DIB: read LITES */
        rval = fps_lites;
        break;

    case ioDIC:                                         /* DIC: read CTL */
        rval = fps_ctl;
        if (fps_wc == 0)
            rval |= CTL_WC_ZERO;
        if (fps_dma_active)
            rval |= CTL_HDMA;
        else
            rval &= ~CTL_HDMA;
        break;

    default:
        break;
    }

/* Handle flag pulses */
switch (pulse) {

    case iopS:                                          /* Start */
        DEV_SET_BUSY( INT_FPS );
        DEV_CLR_DONE( INT_FPS );
        DEV_UPDATE_INTR;
        break;

    case iopC:                                          /* Clear */
        DEV_CLR_BUSY( INT_FPS );
        DEV_CLR_DONE( INT_FPS );
        DEV_UPDATE_INTR;
        break;

    case iopP:                                          /* Pulse = APIRT */
        fps_fn_status |= FN_SWR_ACK;
        break;
    }

return rval;
}


/* Read an AP internal register by REGSEL value */

static int32 fps_read_reg (int32 regsel)
{
switch (regsel) {
    case REGSEL_PSA:     return fps_psa;
    case REGSEL_SPD:     return fps_spad[0];            /* SPD = s-pad destination */
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
    case REGSEL_SPD:     fps_spad[0] = val & 0xFFFF; break;
    case REGSEL_MA:      fps_ma = val & 0xFFFF; break;
    case REGSEL_TMA:     fps_tma = val & 0xFFF; break;
    case REGSEL_DPA:     fps_dpa = val & 0xFF; break;
    case REGSEL_SPFN:    fps_spfn = val & 0xFFFF; break;
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
    fps_da = 0;
    fps_ap_status = 0;
    fps_spfn = 0;
    fps_dma_active = 0;
    memset (fps_spad, 0, sizeof (fps_spad));
    memset (fps_srs, 0, sizeof (fps_srs));
    fps_fn_status = FN_HALTED;
    return;
    }

if (cmd & FN_STOP) {
    fps_running = 0;
    fps_fn_status |= FN_HALTED;
    /* Interrupt host if IHHALT enabled */
    if (fps_ctl & CTL_IHHALT) {
        DEV_CLR_BUSY( INT_FPS );
        DEV_SET_DONE( INT_FPS );
        DEV_UPDATE_INTR;
        }
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
    /* TODO: implement when AP execution engine exists */
    fps_psa++;
    fps_fn_status |= FN_HALTED;
    fps_running = 0;
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
        case 3: fps_tma++; fps_tma &= 0xFFF; break;
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
        case 3: fps_tma++; fps_tma &= 0xFFF; break;
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

/* Convert exponent: AP bias 512, host bias 128 */
aexp = hexp + (512 - 128);

/* Shift 24-bit mantissa to 28-bit position */
amant = hmant << 4;

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

/* Convert exponent */
hexp = aexp - (512 - 128);
if (hexp <= 0 || hexp >= 255) { *hi = 0; *lo = 0; return; }

/* Shift 28-bit mantissa to 24-bit, remove hidden bit */
hmant = (amant >> 4) & 0x7FFFFF;

host32 = (sign << 31) | (hexp << 23) | hmant;
*hi = (uint16)(host32 >> 16);
*lo = (uint16)(host32 & 0xFFFF);
}


/* DMA state machine -- handles multi-word transfers per AP word */
static int32 fps_dma_phase;                             /* 0=first word, 1=second word */
static uint16 fps_dma_buf;                              /* Buffer for 2-word transfers */

/* Execute one DMA cycle (transfer one host word) */

static void fps_dma_cycle (void)
{
int32 fmt;
uint16 host_word, hi_word, lo_word;

if (fps_wc == 0 || !fps_dma_active) {
    fps_dma_active = 0;
    fps_dma_phase = 0;
    fps_ctl &= ~CTL_HDMA;
    if (fps_ctl & CTL_IHWC) {
        DEV_CLR_BUSY( INT_FPS );
        DEV_SET_DONE( INT_FPS );
        DEV_UPDATE_INTR;
        }
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
    if ((fps_hma & AMASK) <= (uint32)AMASK)
        M[fps_hma & AMASK] = host_word;
    }
else {
    /* Host -> AP */
    host_word = ((fps_hma & AMASK) <= (uint32)AMASK) ?
        M[fps_hma & AMASK] : 0;

    switch (fmt) {
        case 0:                                         /* 38-bit float conversion */
            if (fps_dma_phase == 0) {
                fps_dma_buf = host_word;                /* Save high word */
                fps_dma_phase = 1;
                }
            else {
                if (fps_md && fps_apma < MD_SIZE)
                    fps_md[fps_apma] = fps_host_to_ap_float (fps_dma_buf, host_word);
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

if (fps_wc == 0) {
    fps_dma_active = 0;
    fps_dma_phase = 0;
    fps_ctl &= ~CTL_HDMA;
    if (fps_ctl & CTL_IHWC) {
        DEV_CLR_BUSY( INT_FPS );
        DEV_SET_DONE( INT_FPS );
        DEV_UPDATE_INTR;
        }
    }
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
int32 ma_op, dpa_op, tma_op, dpbs, use_value;
int32 spsr_val, result, branch;
int32 signed_disp;

if (!fps_running || !fps_ps)
    return;
if (fps_psa >= PS_SIZE) {
    fps_running = 0;
    fps_fn_status |= FN_HALTED;
    return;
    }

/* Fetch instruction from Program Store */
instr = fps_ps[fps_psa];
fps_cb = instr;

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
            fps_running = 0;
            fps_fn_status |= FN_HALTED;
            if (fps_ctl & CTL_IHHALT) {
                DEV_CLR_BUSY( INT_FPS );
                DEV_SET_DONE( INT_FPS );
                DEV_UPDATE_INTR;
                }
            return;
        case 8:                                         /* JMP/JSR */
            {
            int32 ps_mode = (spd >> 1) & 3;
            int32 target = 0;
            switch (ps_mode) {
                case 0: target = FPS_VALUE(instr) & 0xFFF; break;
                case 1: target = (fps_psa + 1 + (int16_t)FPS_VALUE(instr)) & 0xFFF; break;
                case 2: target = fps_tma & 0xFFF; break;
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
    fps_running = 0;
    fps_fn_status |= FN_HALTED;
    if (fps_ctl & CTL_IHHALT) {
        DEV_CLR_BUSY( INT_FPS );
        DEV_SET_DONE( INT_FPS );
        DEV_UPDATE_INTR;
        }
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
            }
        return;                                         /* Don't increment PSA */
    case 3:  branch = 1; break;                          /* BINTRQ - interrupt request */
    case 4:  branch = 1; break;                          /* BION - I/O ready (stub: always) */
    case 5:  branch = 0; break;                          /* BIOZ - I/O not ready */
    case 6:  branch = (fps_facond != 0); break;          /* BFPE - float error */
    case 8:  branch = (fps_facond == 0); break;          /* BFEQ - float equal */
    case 9:  branch = (fps_facond != 0); break;          /* BFNE - float not equal */
    case 10: branch = (fps_facond >= 0); break;          /* BFGE - float >= 0 */
    case 11: branch = (fps_facond > 0);  break;          /* BFGT - float > 0 */
    case COND_BEQ:  branch = (fps_spcond == 0); break;   /* s-pad EQ */
    case COND_BNE:  branch = (fps_spcond != 0); break;   /* s-pad NE */
    case COND_BGE:  branch = (fps_spcond >= 0); break;   /* s-pad GE */
    case COND_BGT:  branch = (fps_spcond > 0);  break;   /* s-pad GT */
    default:        break;
    }

/* S-pad operation (when DF=0) */
if (df == 0) {
    result = spsr_val;

    switch (sop) {
        case SOP_NOP:   break;
        case SOP_SPEC:                                  /* SPEC mode */
            /* SPS values 0-7 are SPEC ops (handled in separate block below),
               not s-pad single-operand operations. Skip write for those. */
            if (sps < 8)
                goto skip_spad_write;
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

    /* Write result to SPD (unless NOP) */
    if (sop != SOP_NOP && spd < SP_SIZE)
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
                case 1: target = (fps_psa + 1 + (int16_t)FPS_VALUE(instr)) & 0xFFF; break; /* PC-relative */
                case 2: target = fps_tma & 0xFFF; break;            /* TMA */
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
            fps_running = 0;
            fps_fn_status |= FN_HALTED;
            if (fps_ctl & CTL_IHHALT) {
                DEV_CLR_BUSY( INT_FPS );
                DEV_SET_DONE( INT_FPS );
                DEV_UPDATE_INTR;
                }
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
            fps_running = 0;
            fps_fn_status |= FN_HALTED;
            if (fps_ctl & CTL_IHHALT) {
                DEV_CLR_BUSY( INT_FPS );
                DEV_SET_DONE( INT_FPS );
                DEV_UPDATE_INTR;
                }
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
t_uint64 md_val = (fps_md && fps_ma < MD_SIZE) ? fps_md[fps_ma] : 0;
t_uint64 a1_val = 0, a2_val = 0;
t_uint64 fa_new = fps_fa, fm_new = fps_fm;
t_uint64 dpbs_val = 0;
int32 mi_field = use_value ? 0 : FPS_MI(instr);
int32 fm_start = use_value ? 0 : FPS_FM(instr);
int32 m1_field = use_value ? 0 : FPS_M1(instr);
int32 m2_field = use_value ? 0 : FPS_M2(instr);

/* Adder input selection */
if (fadd_op != 0 && fadd_op != 7) {                    /* Not NOP or I/O group */
    switch (FPS_A1(instr)) {
        case 0: break;                                  /* NOP */
        case 1: a1_val = fps_fa; break;                 /* FA (previous result) */
        case 2: a1_val = dpx_val; break;                /* DPX */
        case 3: a1_val = dpy_val; break;                /* DPY */
        case 4: a1_val = md_val; break;                 /* MD */
        default: a1_val = 0; break;                     /* ZERO */
        }
    switch (FPS_A2(instr)) {
        case 0: break;
        case 1: a2_val = fps_fa; break;
        case 2: a2_val = dpx_val; break;
        case 3: a2_val = dpy_val; break;
        case 4: a2_val = md_val; break;
        default: a2_val = 0; break;
        }

    /* Floating adder operation */
    switch (fadd_op) {
        case 1: fa_new = fps_38bit_sub (a2_val, a1_val); break; /* FSUBR */
        case 2: fa_new = fps_38bit_sub (a1_val, a2_val); break; /* FSUB */
        case 3: fa_new = fps_38bit_add (a1_val, a2_val); break; /* FADD */
        case 4: fa_new = ~(a1_val ^ a2_val) & FP_38_MASK; break; /* FEQV */
        case 5: fa_new = a1_val & a2_val; break;        /* FAND */
        case 6: fa_new = a1_val | a2_val; break;        /* FOR */
        }
    fps_fa = fa_new;

    /* Update float adder condition code */
    if (fps_fa == 0)
        fps_facond = 0;
    else if (fp_get_mant(fps_fa) < 0)
        fps_facond = -1;
    else
        fps_facond = 1;
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
    case 6: dpbs_val = (t_uint64)fps_spfn; break;       /* SPFN */
    case 7: dpbs_val = (fps_tm && fps_tma < TM_SIZE) ? fps_tm[fps_tma] : 0; break;
    }

/* Write to Data Pads (when DPBS active and not NOP) */
if (dpbs != 0) {
    fps_dpx[dpx_widx] = dpbs_val;
    fps_dpy[dpy_widx] = dpbs_val;
    }

/* Adder result can also write to DPX */
if (fadd_op != 0 && fadd_op != 7) {
    int32 dpx_src = FPS_DPX(instr);
    int32 dpy_src = FPS_DPY(instr);
    if (dpx_src == 1)                                   /* DPX source = FA */
        fps_dpx[dpx_widx] = fps_fa;
    if (dpy_src == 1)                                   /* DPY source = FA */
        fps_dpy[dpy_widx] = fps_fa;
    if (dpx_src == 2)                                   /* DPX source = FM */
        fps_dpx[dpx_widx] = fps_fm;
    if (dpy_src == 2)                                   /* DPY source = FM */
        fps_dpy[dpy_widx] = fps_fm;
    }

/* Memory input (MI field) - write to main data */
if (mi_field != 0 && fps_md && fps_ma < MD_SIZE) {
    switch (mi_field) {
        case 1: fps_md[fps_ma] = fps_inbs; break;      /* INBS */
        case 2: fps_md[fps_ma] = (t_uint64)FPS_VALUE(instr); break; /* VALUE */
        case 3: fps_md[fps_ma] = dpbs_val; break;      /* From DPBS */
        }
    }
}

/* Memory address updates (when not using VALUE field) */
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
        case ADDR_SET:  fps_tma = fps_spad[spd] & 0xFFF; break;
        }
    }

/* Advance PSA */
if (branch) {
    /* Signed 5-bit displacement: range -16 to +15 */
    signed_disp = disp;
    if (signed_disp >= 16)
        signed_disp -= 32;
    fps_psa = (fps_psa + signed_disp) & 0xFFF;
    }
else {
    fps_psa = (fps_psa + 1) & 0xFFF;
    }
}


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

/* Remaining 512 entries: reciprocals, sqrt, etc. - leave as zero for now */
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
fps_sra = 0;
fps_ma = 0;
fps_tma = 0;
fps_dpa = 0;
fps_da = 0;
fps_ap_status = 0;
fps_spfn = 0;
fps_dma_active = 0;
fps_dma_phase = 0;
fps_dma_buf = 0;
memset (fps_spad, 0, sizeof (fps_spad));
memset (fps_srs, 0, sizeof (fps_srs));
memset (fps_dpx, 0, sizeof (fps_dpx));
memset (fps_dpy, 0, sizeof (fps_dpy));
fps_fa = fps_fm = 0;
fps_a1 = fps_a2 = fps_m1 = fps_m2 = 0;
fps_inbs = fps_dpbs = fps_cb = 0;
fps_spcond = fps_facond = 0;
/* Don't zero PS and MD on reset -- preserve loaded programs */
/* Initialize table memory ROM on first reset */
fps_init_table_memory ();

DEV_CLR_BUSY( INT_FPS );
DEV_CLR_DONE( INT_FPS );
DEV_UPDATE_INTR;
sim_cancel (&fps_unit);

return SCPE_OK;
}
