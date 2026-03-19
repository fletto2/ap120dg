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

   This is a STUB implementation that emulates the host interface registers
   (SWR, FN, LITES, CTL, WC, HMA, APMA) and the FN command protocol
   (DEP, EXAM, START, STOP, RESET) but does NOT emulate the AP pipeline
   or execute AP microcode. The AP is always "halted" unless a START
   command is written to FN.

   I/O mapping (Hypothesis A -- to be verified on real hardware):
     DOA ac,055       Write SWR (switch register -- data)
     DOB ac,055       Write FN  (function register -- commands)
     DOC ac,055       Write CTL (control register -- DMA/interrupt)
     DIA ac,055       Read FN status (bit 0/MSB = halted)
     DIB ac,055       Read LITES (panel display)
     DIC ac,055       Read CTL status

   Flag effects:
     S (Start)        Set BUSY, clear DONE
     C (Clear)        Clear BUSY and DONE
     P (Pulse)        AP interrupt (APIRT equivalent)

   Reference: AP-120B Processor Handbook, 860-7259-003, Feb 1979
*/

#include "nova_defs.h"

/* Device code */
#define DEV_FPS         055

/* Interrupt vector -- using bit 1 (unused in standard config) */
#define INT_V_FPS       1
#define INT_FPS         (1 << INT_V_FPS)
#define PI_FPS          0000020

/* FN register command bits (bit 0 = MSB convention, stored as uint16) */
#define FN_STOP         0x8000  /* Bit 0: Stop AP */
#define FN_START        0x4000  /* Bit 1: Start at SWR address */
#define FN_CONT         0x2000  /* Bit 2: Continue from PSA */
#define FN_STEP         0x1000  /* Bit 3: Single step */
#define FN_RESET        0x0800  /* Bit 4: Hard reset */
#define FN_EXAM         0x0400  /* Bit 5: Examine register */
#define FN_DEP          0x0200  /* Bit 6: Deposit SWR into register */
#define FN_BREAK        0x0100  /* Bit 7: Set breakpoint */
#define FN_INC_MASK     0x00C0  /* Bits 8-9: INC field */
#define FN_INC_SHIFT    6
#define FN_WORD_MASK    0x0030  /* Bits 10-11: WORD field */
#define FN_WORD_SHIFT   4
#define FN_REGSEL_MASK  0x000F  /* Bits 12-15: REG SELECT */

/* FN status bits (read) */
#define FN_HALTED       0x8000  /* Bit 0: AP is halted */
#define FN_SWR_ACK      0x4000  /* Bit 1: SWR read acknowledge */

/* CTL register bits */
#define CTL_WC_ZERO     0x8000  /* Bit 0: WC=0 (read only) */
#define CTL_INTR_AP     0x4000  /* Bit 1: Interrupt AP */
#define CTL_IHHALT      0x1000  /* Bit 3: Enable host interrupt on halt */
#define CTL_IHWC        0x0800  /* Bit 4: Enable host interrupt on DMA done */
#define CTL_IHENB       0x0400  /* Bit 5: Interrupt host enable */
#define CTL_HDMA        0x0001  /* Bit 15: Start DMA / DMA active */

/* REG SELECT values */
#define REGSEL_PSA      0
#define REGSEL_SPD      1
#define REGSEL_MA       2
#define REGSEL_TMA      3
#define REGSEL_DPA      4
#define REGSEL_SPFN     5
#define REGSEL_STATUS   6
#define REGSEL_DA       7
#define REGSEL_PS_TMA   8   /* 010 octal */
#define REGSEL_MD_MA    13  /* 015 octal */

extern int32 int_req, dev_busy, dev_done, dev_disable;

/* FPS state */
static int32 fps_swr;                  /* Switch Register (data) */
static int32 fps_fn_status;            /* FN status (read) */
static int32 fps_lites;                /* Lights register */
static int32 fps_ctl;                  /* Control register */
static int32 fps_wc;                   /* Word Count */
static int32 fps_hma;                  /* Host Memory Address */
static int32 fps_apma;                 /* AP Memory Address */
static int32 fps_running;              /* AP running flag */

/* AP internal registers (accessible via FN EXAM/DEP) */
static int32 fps_regs[16];             /* Register file indexed by REGSEL */

/* Function prototypes */
int32  fps (int32 pulse, int32 code, int32 AC);
t_stat fps_reset (DEVICE *dptr);

static void fps_process_fn_command (int32 cmd);

/* FPS data structures */

DIB fps_dib = { DEV_FPS, INT_FPS, PI_FPS, &fps };

UNIT fps_unit = { UDATA (NULL, 0, 0) };

REG fps_reg[] = {
    { ORDATA (SWR,    fps_swr,       16) },
    { ORDATA (FN,     fps_fn_status, 16) },
    { ORDATA (LITES,  fps_lites,     16) },
    { ORDATA (CTL,    fps_ctl,       16) },
    { ORDATA (WC,     fps_wc,        16) },
    { ORDATA (HMA,    fps_hma,       16) },
    { ORDATA (APMA,   fps_apma,      16) },
    { FLDATA (RUN,    fps_running,    0) },
    { FLDATA (BUSY,   dev_busy,  INT_V_FPS) },
    { FLDATA (DONE,   dev_done,  INT_V_FPS) },
    { FLDATA (DISABLE, dev_disable, INT_V_FPS) },
    { FLDATA (INT,    int_req,   INT_V_FPS) },
    { BRDATA (REGS,   fps_regs, 8, 16, 16) },
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

int32 fps (int32 pulse, int32 code, int32 AC)
{
/* Handle data transfers */
switch (code) {

    case ioDOA:                                         /* DOA: write SWR */
        fps_swr = AC & 0xFFFF;
        break;

    case ioDOB:                                         /* DOB: write FN (command) */
        fps_process_fn_command (AC & 0xFFFF);
        break;

    case ioDOC:                                         /* DOC: write CTL */
        /* Preserve read-only bits (WC=0, FERR, DLATE) */
        fps_ctl = (AC & 0x7F3F) | (fps_ctl & 0x80C0);
        if (AC & CTL_INTR_AP) {                         /* INTR AP bit: pulse */
            /* In a real AP this would interrupt the running program */
            fps_fn_status |= FN_SWR_ACK;                /* Simulate SWR ack */
            }
        break;

    case ioDIA:                                         /* DIA: read FN status */
        fps_fn_status &= ~FN_SWR_ACK;                  /* Clear ack on read */
        return fps_fn_status;

    case ioDIB:                                         /* DIB: read LITES */
        return fps_lites;

    case ioDIC:                                         /* DIC: read CTL */
        return fps_ctl | (fps_wc == 0 ? CTL_WC_ZERO : 0);

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
        /* Interrupt the AP -- simulate SWR read acknowledge */
        fps_fn_status |= FN_SWR_ACK;
        break;
    }

return 0;
}


/* Process FN command word */

static void fps_process_fn_command (int32 cmd)
{
int32 regsel = cmd & FN_REGSEL_MASK;
int32 word = (cmd & FN_WORD_MASK) >> FN_WORD_SHIFT;

if (cmd & FN_RESET) {                                  /* RESET */
    fps_swr = 0;
    fps_lites = 0;
    fps_ctl = 0;
    fps_wc = 0;
    fps_hma = 0;
    fps_apma = 0;
    fps_running = 0;
    memset (fps_regs, 0, sizeof (fps_regs));
    fps_fn_status = FN_HALTED;                          /* AP now halted */
    return;
    }

if (cmd & FN_STOP) {                                   /* STOP */
    fps_running = 0;
    fps_fn_status |= FN_HALTED;
    }

if (cmd & FN_START) {                                  /* START */
    fps_regs[REGSEL_PSA] = fps_swr;                    /* PSA = SWR */
    fps_running = 1;
    fps_fn_status &= ~FN_HALTED;
    }

if (cmd & FN_CONT) {                                   /* CONTINUE */
    fps_running = 1;
    fps_fn_status &= ~FN_HALTED;
    }

if (cmd & FN_DEP) {                                    /* DEPOSIT */
    /* Store SWR into selected register (16-bit portion) */
    fps_regs[regsel] = fps_swr;
    fps_fn_status |= FN_SWR_ACK;                       /* Acknowledge */

    /* Handle INC field */
    switch ((cmd & FN_INC_MASK) >> FN_INC_SHIFT) {
        case 1: fps_regs[REGSEL_MA]++;  break;         /* INC MA */
        case 2: fps_regs[REGSEL_DPA]++; break;         /* INC DPA */
        case 3: fps_regs[REGSEL_TMA]++; break;         /* INC TMA */
        }
    }

if (cmd & FN_EXAM) {                                   /* EXAMINE */
    /* Copy selected register to LITES for host to read */
    fps_lites = fps_regs[regsel];
    }
}


/* Reset routine */

t_stat fps_reset (DEVICE *dptr)
{
fps_swr = 0;
fps_fn_status = FN_HALTED;                             /* AP starts halted */
fps_lites = 0;
fps_ctl = 0;
fps_wc = 0;
fps_hma = 0;
fps_apma = 0;
fps_running = 0;
memset (fps_regs, 0, sizeof (fps_regs));
DEV_CLR_BUSY( INT_FPS );
DEV_CLR_DONE( INT_FPS );
DEV_UPDATE_INTR;
return SCPE_OK;
}
