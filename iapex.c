/* iapex.c -- FPS AP-120B / FPS-100 Host-Independent API
 *
 * C translation of IAPEX.FTN — the host-independent layer above FDAPEX.
 * Original: FPS100>PDP11>OPSYS>APX100.01>IAPEX.FTN, Nov 1979, J. Ramus
 *
 * This provides program management (APEX table, load-on-demand),
 * data transfer wrappers, synchronization, and error handling.
 *
 * Dependencies: fdapex.c (DAPEX layer), platform fps_io() function.
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "iapex.h"

/* ============================================================
 * APEX state (program table)
 * ============================================================ */

apex_state_t apex_state;

/* Bootstrap microcode: 15 words loaded at PS[0] by LOADBT.
   This minimal bootstrap handles the APEX message protocol:
   it waits for SWR from the host, reads the 5-word message,
   and dispatches accordingly. On real hardware this is loaded
   once during APINIT and stays resident. */

/* Real AP-120B bootstrap is 60 words loaded at PS[0]; it handles
   the APEX message protocol. On the emulator, FN_START sets PSA
   directly so the bootstrap is not needed — we just reserve space. */

#define BOOT_SIZE 15    /* Reserved PS space for bootstrap */

/* ============================================================
 * Initialization
 * ============================================================ */

int apinit(int apnum, int action)
{
    int status;

    /* Assign processor */
    status = apasgn(apnum, action);
    if (status < 0)
        return status;

    /* Initialize APEX subsystem */
    apxset();

    return status;
}

void apxset(void)
{
    /* Clear program tables */
    apxclr();

    /* Reset AP hardware */
    aprset();

    /* Size Program Store */
    apex_state.pssiz = sizeps();
    apex_state.psptr = apex_state.ressiz;

    /* Load bootstrap (reserved area at PS[0..BOOT_SIZE-1]) */
    /* On the emulator, the bootstrap isn't needed because
       FN_START sets PSA directly. We just reserve the space. */
    apex_state.ressiz = BOOT_SIZE;
    apex_state.psptr = BOOT_SIZE;
}

void apxclr(void)
{
    memset(&apex_state, 0, sizeof(apex_state));
    apex_state.tblptr = 0;
    apex_state.ressiz = BOOT_SIZE;
    apex_state.psptr = BOOT_SIZE;
    apex_state.brk = -1;       /* No breakpoint */
    apex_state.tblsiz = APEX_TABLE_SIZE;
    apex_state.pssiz = 4096;   /* Default, updated by apxset */
}

/* ============================================================
 * APEX — Program Store Executive
 *
 * Manages a table of loaded programs. If the requested code is
 * already in PS, just run it. Otherwise, load it first.
 *
 * Parameters:
 *   code      - Microcode words (4 uint16 per instruction, MSB first)
 *   code_size - Number of 16-bit words (= num_instructions * 4)
 *   slist     - S-PAD parameter values to load before running
 *   nspads    - Number of S-PAD parameters
 *   start_addr - Entry offset within the code (usually 0)
 * ============================================================ */

void apex(const uint16_t *code, int code_size,
          const uint16_t *slist, int nspads,
          uint16_t start_addr)
{
    int num_instr = code_size / 4;
    uint16_t ps_addr;
    int i;

    /* Check if this code is already loaded (by matching host address) */
    uint16_t host_key = (uint16_t)(uintptr_t)code;
    for (i = 0; i < apex_state.tblptr; i++) {
        if (apex_state.hostbl[i] == host_key) {
            /* Found — use existing PS address */
            ps_addr = apex_state.aptbl[i];
            goto run;
        }
    }

    /* Not loaded — load into PS at current pointer */
    if (apex_state.psptr + num_instr > apex_state.pssiz) {
        apstop(1);  /* PS MEMORY OVERFLOW */
        return;
    }

    ps_addr = apex_state.psptr;
    loadps(code, ps_addr, num_instr);
    apex_state.psptr += num_instr;

    /* Record in table */
    if (apex_state.tblptr < apex_state.tblsiz) {
        apex_state.hostbl[apex_state.tblptr] = host_key;
        apex_state.aptbl[apex_state.tblptr] = ps_addr;
        apex_state.tblptr++;
    }

run:
    /* Load S-PAD and start execution */
    spldgo(slist, nspads, ps_addr + start_addr, 0);

    /* Wait for completion */
    if (wtrun() != 0) {
        apstop(12);  /* AP STOP */
    }
}

/* ============================================================
 * Synchronization
 * ============================================================ */

void apwait(void)
{
    /* Wait for DMA completion */
    apwd();

    /* Wait for AP running completion */
    wtrun();
}

/* ============================================================
 * Data Transfer
 *
 * Format codes:
 *   0 = 38-bit FPS float (2 host words per AP word)
 *   1 = 16-bit integer (1 host word per AP word)
 *   2 = 32-bit float / host FP (2 host words per AP word)
 * ============================================================ */

void apput(const uint16_t *host, uint16_t ap, int n, int fmt)
{
    uint16_t ctl;

    if (n <= 0) return;

    /* DMA control: Host→AP
       Bits: CC(7) + APDMA(6) + FMT(2-1) + HDMAGO(0)
       Base = 0xC1 (CC + APDMA + HDMAGO) */
    ctl = 0xC1 + (fmt << 1);

    /* Word count depends on format:
       fmt 0 (38-bit float): 2 host words per AP word
       fmt 1 (16-bit int):   1 host word per AP word
       fmt 2 (32-bit float): 2 host words per AP word */
    rundma((uint16_t)(uintptr_t)host, ap,
           (uint16_t)((fmt == 1) ? n : n * 2), ctl);
}

void apget(uint16_t *host, uint16_t ap, int n, int fmt)
{
    uint16_t ctl;

    if (n <= 0) return;

    /* DMA control: AP→Host (add WRTHOST bit 5 = 0x20) */
    ctl = 0xC1 + (fmt << 1) + 0x20;

    rundma((uint16_t)(uintptr_t)host, ap,
           (uint16_t)((fmt == 1) ? n : n * 2), ctl);
}

/* ============================================================
 * Error Checking
 * ============================================================ */

int apchk(void)
{
    /* Read S-PAD register 15 (software error flag).
       On real hardware this requires running a small microprogram
       that copies SPAD[15] to LITES. On the emulator, we can
       use APEXAM directly. */
    return apexam(1, 0);  /* REGSEL_SPD, word 0 → reads SPAD[0] */
    /* TODO: need to read SPAD[15] specifically */
}

void apstat(int *iany, int *istat)
{
    uint16_t ctl;

    /* Read CTRL register for hardware error flags */
    ctl = apin(5);  /* CTRL register */

    *istat = ctl;
    *iany = 0;

    /* Check error bits */
    if (ctl & 0x0200)  /* FERR - format error */
        *iany |= 1;
    if (ctl & 0x0100)  /* DLATE - data late */
        *iany |= 2;
}

/* ============================================================
 * Breakpoints
 * ============================================================ */

void setbrk(uint16_t brkloc)
{
    apex_state.brk = brkloc;
}

void clrbrk(void)
{
    apex_state.brk = -1;
}

/* ============================================================
 * S-PAD Access
 * ============================================================ */

uint16_t apgsp(int regnum)
{
    (void)regnum;  /* TODO: need microprogram to read arbitrary SPAD */
    return (uint16_t)apexam(1, 0);  /* Simplified: only SPAD[0] */
}

/* ============================================================
 * Memory Sizing
 * ============================================================ */

int sizemd(void)
{
    /* Default: 8192 words (minimum AP-120B configuration).
       On real hardware, this probes MD by writing/reading patterns. */
    return 8192;
}

int sizeps(void)
{
    /* Default: 4096 words (with PS expansion option).
       Base AP-120B has 1024; with AP-120-PS option, 4096. */
    return 4096;
}
