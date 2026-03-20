/* iapex.h -- FPS AP-120B / FPS-100 Host-Independent API
 *
 * C translation of IAPEX.FTN — the host-independent layer that sits
 * above FDAPEX/DAPEX. Provides program management (APEX), data
 * transfer (APPUT/APGET), synchronization (APWAIT), and error handling.
 *
 * Original: FPS100>PDP11>OPSYS>APX100.01>IAPEX.FTN, Nov 1979
 */

#ifndef IAPEX_H
#define IAPEX_H

#include <stdint.h>
#include "fdapex.h"

/* ---- Initialization ---- */

int      apinit(int apnum, int action);   /* Returns status: >0=OK, <0=error */
void     apxset(void);                    /* Initialize APEX + reset AP */
void     apxclr(void);                    /* Clear APEX program tables */

/* ---- Program Execution (APEX) ---- */

void     apex(const uint16_t *code, int code_size,
              const uint16_t *slist, int nspads,
              uint16_t start_addr);        /* Load + run AP program */

/* ---- Synchronization ---- */

void     apwait(void);                    /* Wait for both DMA + AP done */

/* ---- Data Transfer ---- */

void     apput(const uint16_t *host, uint16_t ap, int n, int fmt);
void     apget(uint16_t *host, uint16_t ap, int n, int fmt);

/* ---- Error Checking ---- */

int      apchk(void);                     /* Check AP software error (S-PAD 15) */
void     apstat(int *iany, int *istat);   /* Check hardware error status */

/* ---- Breakpoints ---- */

void     setbrk(uint16_t brkloc);
void     clrbrk(void);

/* ---- S-PAD Access ---- */

uint16_t apgsp(int regnum);              /* Read S-PAD register (0-15) */

/* ---- Memory Sizing ---- */

int      sizemd(void);                    /* Returns MD size in words */
int      sizeps(void);                    /* Returns PS size (1024 or 4096) */

/* ---- APEX State (exposed for test harness) ---- */

#define APEX_TABLE_SIZE  50

typedef struct {
    int      tblptr;                      /* Next free table slot (1-based) */
    int      ressiz;                      /* Resident code size (bootstrap) */
    int      psptr;                       /* Next free PS location */
    int      brk;                         /* Breakpoint displacement (-1=none) */
    uint16_t hostbl[APEX_TABLE_SIZE];     /* Host addresses of loaded code */
    uint16_t aptbl[APEX_TABLE_SIZE];      /* Corresponding PS addresses */
    int      pssiz;                       /* Total PS size */
    int      tblsiz;                      /* Table size (always 50) */
} apex_state_t;

extern apex_state_t apex_state;

#endif /* IAPEX_H */
