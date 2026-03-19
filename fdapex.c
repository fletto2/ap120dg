/* fdapex.c -- FPS AP-120B / FPS-100 Host Driver (C translation)
 *
 * Clean ANSI C translation of FDAPEX.FTN + DAPEX.MAC for DG Nova.
 * Combines the FORTRAN driver layer (FDAPEX) and the host-dependent
 * assembly layer (DAPEX) into a single C file.
 *
 * Original: FPS100>PDP11>OPSYS>APX100.01>FDAPEX.RT11, Nov 1979, J. Ramus
 * DG Nova I/O mapping from 280B schematic 512-3280-004 Rev B.
 *
 * Register mapping:
 *   DOA  none=SWR    S=FN     C=CTRL    P=INT(APIRT)
 *   DOB  none=WC     S=HMA    C=APMA    P=DMA start
 *   DOC  none=FMTH   S=FMTL
 *   DIA  none=FN     S=SWR    C=LITES   P=APMA
 *   DIB=FMTH  DIC=FMTL
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>

/* ============================================================
 * Hardware abstraction layer
 *
 * On real hardware, these would be inline DG Nova I/O instructions.
 * On the SimH emulator, these call the fps_io() handler.
 * On a modern test harness, these can be stubbed/mocked.
 * ============================================================ */

/* Forward declarations */
void     apwd(void);
void     apstop(int ernum);
uint16_t htst(void);
int      apwr(void);

/* Forward declarations -- platform provides these */
extern void    hw_doa(uint16_t val);           /* DOA: write SWR */
extern void    hw_doas(uint16_t val);          /* DOAS: write FN */
extern void    hw_doac(uint16_t val);          /* DOAC: write CTRL */
extern void    hw_doap(uint16_t val);          /* DOAP: pulse INT */
extern void    hw_dob(uint16_t val);           /* DOB: write WC */
extern void    hw_dobs(uint16_t val);          /* DOBS: write HMA */
extern void    hw_dobc(uint16_t val);          /* DOBC: write APMA */
extern void    hw_dobp(uint16_t val);          /* DOBP: start DMA */
extern void    hw_doc(uint16_t val);           /* DOC: write FMTH */
extern void    hw_docs(uint16_t val);          /* DOCS: write FMTL */
extern uint16_t hw_dia(void);                  /* DIA: read FN status */
extern uint16_t hw_dias(void);                 /* DIAS: read SWR */
extern uint16_t hw_diac(void);                 /* DIAC: read LITES */
extern uint16_t hw_diap(void);                 /* DIAP: read APMA */
extern uint16_t hw_dib(void);                  /* DIB: read FMTH */
extern uint16_t hw_dic(void);                  /* DIC: read FMTL */
extern void    hw_nioc(int subdev);            /* NIOC: clear flags */
extern int     hw_skpdn(int subdev);           /* SKPDN: test DONE */

/* ============================================================
 * FN register bit definitions (bit 0 = MSB, DG convention)
 * ============================================================ */

#define FN_HALTED    0x8000   /* bit 0: AP is halted */
#define FN_ACK       0x4000   /* bit 1: SWR read acknowledge */
#define FN_START     0x4000   /* bit 1: START command (same bit) */
#define FN_CONT      0x2000   /* bit 2: CONTINUE */
#define FN_STEP      0x1000   /* bit 3: STEP */
#define FN_RESET     0x0800   /* bit 4: RESET */
#define FN_EXAM      0x0400   /* bit 5: EXAMINE */
#define FN_DEP       0x0200   /* bit 6: DEPOSIT */
#define FN_BREAK     0x0100   /* bit 7: BREAKPOINT */

/* REG SELECT values for FN EXAM/DEP (bits 12-15) */
#define REG_PSA      0
#define REG_SPD      1
#define REG_MA       2
#define REG_TMA      3
#define REG_DPA      4
#define REG_STATUS   6
#define REG_PS_TMA   8
#define REG_CB       9
#define REG_DPX      10
#define REG_DPY      11
#define REG_MD_MA    13

/* CTRL register bits */
#define CTL_WC_ZERO  0x8000
#define CTL_APIRT    0x4000
#define CTL_IHHALT   0x1000
#define CTL_IHWC     0x0800
#define CTL_IHCB5    0x0400
#define CTL_DLATE    0x0100
#define CTL_HDMA     0x0001

/* LITES error bits */
#define LITES_PARITY 0x0100   /* bit 7: parity error */
#define LITES_STKOVF 0x0080   /* bit 8: stack overflow */

/* DMA control values (for 16-bit host) */
#define DMA_CTL_16BIT  195    /* octal 303: standard 16-bit DMA */

/* ============================================================
 * Driver state
 * ============================================================ */

static struct {
    int      assigned;         /* processor assigned flag */
    int      running;          /* AP running flag (0=stopped) */
    int      supervisor;       /* supervisor mode flag */
    int      dma_active;       /* DMA in progress */
    uint16_t savctl;           /* saved CTRL register */
    uint16_t swr;              /* last SWR written */
    uint16_t fnr;              /* last FN written */
    uint16_t lites;            /* last LITES read */
    uint16_t savhma;           /* saved HMA (write-only) */
    uint16_t savwc;            /* saved WC */
    int      error;            /* last error code */
    uint16_t fpdat[8];         /* supervisor datum storage */
} fps;

/* APEX message block */
static struct {
    uint16_t opt;              /* option code */
    uint16_t sct;              /* s-pad count */
    uint16_t swr;              /* SWR value */
    uint16_t fnr;              /* FN value */
} apex_msg;

/* ============================================================
 * DAPEX core routines (was assembly, now C)
 * ============================================================ */

/* RDWAIT -- wait for AP to acknowledge SWR read.
 * Returns 0 on success, -1 on error (halted or timeout). */
int rdwait(void)
{
    int timeout = 100000;
    while (timeout-- > 0) {
        uint16_t fn = hw_dia();
        if (fn & FN_ACK)
            return 0;                      /* ACK set */
        if (!(fn & FN_HALTED))
            continue;                      /* running, retry */
        /* halted without ACK */
        fps.lites = hw_diac();
        fps.running = 0;
        return -1;
    }
    /* timeout */
    fps.lites = hw_diac();
    fps.running = 0;
    return -1;
}

/* SENDER -- send APEX message or single datum.
 * datum != 0: send single SWR value (HPUT mode).
 * datum == 0: send 5-word APEX message from apex_msg block. */
int sender(uint16_t datum)
{
    if (datum != 0) {
        /* Single datum */
        if (rdwait() < 0) return -1;
        hw_doa(datum);
        hw_doap(datum);                    /* pulse INT */
        return 0;
    }
    /* APEX 5-word message */
    uint16_t *msg = &apex_msg.opt;
    if (rdwait() < 0) return -1;
    hw_doa(0);                             /* SWR = 0 (datum) */
    hw_doap(0);                            /* pulse INT */
    for (int i = 0; i < 4; i++) {
        if (rdwait() < 0) return -1;
        hw_doa(msg[i]);
        hw_doap(msg[i]);
    }
    fps.running = 1;
    return 0;
}

/* APIN -- read interface register.
 * num: 1=SWR, 2=FN, 3=LITES, 4=APMA, 5=HMA, 6=WC, 7=CTL,
 *      8=FMTH, 9=FMTL */
uint16_t apin(int num)
{
    switch (num) {
    case 1:  return hw_dias();              /* read SWR */
    case 2:  return hw_dia();               /* read FN */
    case 3:  return hw_diac();              /* read LITES */
    case 4:  return hw_diap();              /* read APMA */
    case 5:  return fps.savhma;             /* HMA: write-only */
    case 6:  return fps.savwc;              /* WC: write-only */
    case 7:  return fps.savctl;             /* CTRL: write-only */
    case 8:  return hw_dib();               /* read FMTH */
    case 9:  return hw_dic();               /* read FMTL */
    default: return 0;
    }
}

/* APOUT -- write interface register.
 * num: 1=SWR, 2=FN, 3=LITES(nop), 4=APMA, 5=HMA, 6=WC,
 *      7=CTL, 8=FMTH, 9=FMTL, 10=RESET */
void apout(int num, uint16_t val)
{
    switch (num) {
    case 1:  hw_doa(val);  fps.swr = val;    break;
    case 2:  hw_doas(val); fps.fnr = val;    break;
    case 3:  /* LITES is read-only */        break;
    case 4:  hw_dobc(val);                   break;
    case 5:  hw_dobs(val); fps.savhma = val; break;
    case 6:  hw_dob(val);  fps.savwc = val;  break;
    case 7:  hw_doac(val); fps.savctl = val; break;
    case 8:  hw_doc(val);                    break;
    case 9:  hw_docs(val);                   break;
    case 10: /* RESET */
        hw_nioc(0);
        memset(&fps, 0, sizeof(fps));
        break;
    }
}

/* RUNDMA -- initiate DMA transfer.
 * host_addr: host memory address, apma: AP memory address,
 * wc: word count, ctl: control bits (format, direction). */
void rundma(uint16_t host_addr, uint16_t apma, uint16_t wc, uint16_t ctl)
{
    apwd();                                /* wait for previous DMA */
    hw_dobc(apma);                         /* write APMA */
    hw_dob(wc);                            /* write WC */
    fps.savwc = wc;
    hw_dobs(host_addr);                    /* write HMA */
    fps.savhma = host_addr;
    fps.savctl = ctl | CTL_IHWC;           /* enable DMA-done interrupt */
    hw_doac(fps.savctl);                   /* write CTRL */
    fps.dma_active = 1;
    hw_dobp(0);                            /* start DMA */
}

/* APWD -- wait for DMA to complete. */
void apwd(void)
{
    if (!fps.dma_active) return;
    while (!hw_skpdn(1))                   /* poll DMA DONE (subdevice 1) */
        ;
    hw_nioc(1);                            /* clear DMA flags */
    fps.dma_active = 0;
}

/* TSTDMA -- test if DMA complete.
 * Returns 1 if complete, 0 if active. */
int tstdma(void)
{
    return !fps.dma_active;
}

/* WTDMA -- wait for DMA, return error status.
 * Returns 0 if ok, nonzero if data late error. */
int wtdma(void)
{
    apwd();
    return (fps.savctl & CTL_DLATE) ? 1 : 0;
}

/* TSTRUN -- test if AP halted.
 * Returns 1 if halted, 0 if running. */
int tstrun(void)
{
    uint16_t fn = hw_dia();
    return (fn & FN_HALTED) ? 1 : 0;
}

/* WTRUN -- wait for AP to halt.
 * Returns error code: 0=ok, 1=parity, 2=stack overflow. */
int wtrun(void)
{
    while (!hw_skpdn(0))                   /* poll RUN DONE (subdevice 0) */
        ;
    hw_nioc(0);                            /* clear RUN flags */
    fps.running = 0;
    fps.lites = hw_diac();
    if (fps.lites & LITES_PARITY)  return 1;
    if (fps.lites & LITES_STKOVF) return 2;
    return 0;
}

/* APWR -- wait for AP run with full error handling.
 * Calls wtrun and reports error via apstop if needed. */
int apwr(void)
{
    int err = wtrun();
    if (err == 1) apstop(5);               /* parity error */
    if (err == 2) apstop(4);               /* stack overflow */
    return err;
}

/* APRSET -- hardware reset. */
void aprset(void)
{
    hw_nioc(0);
    memset(&fps, 0, sizeof(fps));
}

/* RUNAP -- start AP program execution.
 * psa: program start address, fn_cmd: FN command word. */
void runap(uint16_t psa, int noload, uint16_t swr_val, uint16_t fn_cmd)
{
    if (!noload) {
        hw_doa(psa);                       /* SWR = PSA */
        hw_doas(FN_DEP | REG_PSA);         /* DEP into PSA */
    }
    hw_doa(swr_val);                       /* SWR = switch value */
    hw_doas(fn_cmd);                       /* issue command (START) */
    fps.savctl |= CTL_IHHALT;
    hw_doac(fps.savctl);                   /* enable halt interrupt */
    fps.running = 1;
}

/* APEXAM -- examine AP internal register.
 * regsel: register number (0-15), word: which 16-bit portion (0-3).
 * Returns the examined value. */
uint16_t apexam(int regsel, int word)
{
    uint16_t cmd = FN_EXAM | (word << 4) | regsel;
    hw_doas(cmd);
    return hw_dias();                      /* result appears in SWR */
}

/* SPLDGO -- load scratch pad registers and start execution.
 * slist: array of s-pad values, nspads: count,
 * start: PSA, brkloc: breakpoint address. */
void spldgo(const uint16_t *slist, int nspads, uint16_t start, uint16_t brkloc)
{
    (void)brkloc;  /* breakpoint not yet implemented */
    /* Load s-pad values via DEP into SPD (register 1) */
    for (int i = 0; i < nspads; i++) {
        hw_doa(slist[i]);                  /* SWR = s-pad value */
        hw_doas(FN_DEP | REG_SPD);         /* DEP into SPD */
    }
    /* Load PSA and start */
    runap(start, 0, 0, FN_START);
}

/* APIENA -- enable CTL5 (CB5) programmed interrupt. */
void apiena(void)
{
    fps.savctl |= CTL_IHCB5;
    hw_doac(fps.savctl);
}

/* APIDIS -- disable CTL5 interrupt. */
void apidis(void)
{
    fps.savctl &= ~CTL_IHCB5;
    hw_doac(fps.savctl);
}

/* APWI -- wait for CTL5 interrupt. */
void apwi(void)
{
    while (!hw_skpdn(2))                   /* CTL05 DONE (subdevice 2) */
        ;
    hw_nioc(2);
}

/* TSTINT -- test if CTL5 interrupt occurred.
 * Returns 1 if CTL05 DONE set, 0 otherwise. */
int tstint(void)
{
    return hw_skpdn(2);
}

/* APSUPV -- set supervisor mode.
 * mode: 0=off, nonzero=on. */
void apsupv(int mode)
{
    fps.supervisor = mode;
}

/* APASGN -- assign FPS processor.
 * On DG Nova, always device 055. Returns processor number (1). */
int apasgn(int apno, int action)
{
    (void)apno; (void)action;  /* single device, always 055 */
    aprset();
    fps.assigned = 1;
    return 1;
}

/* APRLSE -- release FPS processor. */
void aprlse(void)
{
    apwd();
    hw_nioc(0);
    fps.running = 0;
    fps.dma_active = 0;
    fps.assigned = 0;
}

/* HPUT -- send single datum to FPS-100 supervisor.
 * datum: value to send. */
int hput(uint16_t datum)
{
    return sender(datum);
}

/* HGET -- wait for datum from FPS-100 supervisor.
 * Returns the datum value. */
uint16_t hget(void)
{
    uint16_t val;
    while ((val = htst()) == 0)
        ;
    return val;
}

/* HTST -- test if datum available from supervisor.
 * Returns datum if found, 0 if not available. */
uint16_t htst(void)
{
    for (int i = 0; i < 8; i++) {
        if (fps.fpdat[i] != 0) {
            uint16_t val = fps.fpdat[i];
            fps.fpdat[i] = 0;
            return val;
        }
    }
    return 0;
}

/* LOOKY -- debug: return register values.
 * Returns current SWR, RUNFG, FN status, CTRL. */
void looky(uint16_t *swr, int *runfg, uint16_t *fn, uint16_t *ctl)
{
    *swr = fps.swr;
    *runfg = fps.running;
    *fn = hw_dia();
    *ctl = fps.savctl;
}

/* VIRP -- debug: return supervisor flag. */
int virp(void)
{
    return fps.supervisor;
}

/* ============================================================
 * FDAPEX routines (translated from FORTRAN)
 * ============================================================ */

/* Load module table */
#define LMT_MAX 10
static struct {
    int id;
    int option;
    int lun;
} lmt[LMT_MAX];
static int lmte = 0;                      /* number of LMT entries */

/* AP load common block */
static struct {
    int      ipav[33];                     /* parameter address vector */
    int      nu2;
    int      idlm;                         /* current load module ID */
    int      nu1;
    int      ippaad;                       /* PPA start address */
    int      ippand;                       /* PPA end address */
    int      iovs[33];                     /* overlay ID array */
} apldcm;

/* System common block */
static struct {
    int super;                             /* supervisor mode */
    int start;                             /* supervisor start address */
    int bootst;                            /* bootstrap address */
} sys;

/* Error common */
static int halt_addr;
static int stop_num;

/* APSTOP -- error handler with message.
 * Prints error message and optionally continues. */
void apstop(int ernum)
{
    static const char *msgs[] = {
        /* 1-13 */
        "AP.1 - P.S. MEMORY OVERFLOW",
        "AP.2 - PARAMETER MISMATCH",
        "AP.3 - AP DATA LATE ERROR",
        "AP.4 - AP STACK OVERFLOW",
        "AP.5 - PARITY ERROR ON MD READ/WRITE",
        "AP.6 - ILLEGAL DMA FORMAT REQUESTED",
        "AP.7 - SYSTEM SERVICE ERROR",
        "AP.8 - TOO MANY LOAD MODULES",
        "AP.9 - LOAD MODULE NOT INITIALIZED",
        "AP.10 - BAD AP LOAD MODULE",
        "AP.11 - MAIN DATA PPA OVERFLOW",
        "AP.12 - AP HALTED",
        "AP.13 - UNABLE TO OPEN LOAD MODULE FILE",
    };
    if (ernum >= 1 && ernum <= 13)
        fprintf(stderr, " %s\n", msgs[ernum - 1]);
    else if (ernum == 12)
        fprintf(stderr, " AP.12 - AP HALTED AT %d STOP NUMBER = %d\n",
                halt_addr, stop_num);
    else
        fprintf(stderr, " AP ERROR %d\n", ernum);
}

/* LOADPS -- load program store from host array.
 * Writes 64-bit PS words via the DEP mechanism (4 x 16-bit per word). */
void loadps(const uint16_t *host, uint16_t ps_addr, int nwords)
{
    /* Set TMA to starting PS address */
    hw_doa(ps_addr);
    hw_doas(FN_DEP | REG_TMA);             /* DEP into TMA */

    for (int i = 0; i < nwords; i++) {
        /* Write 4 x 16-bit words per PS instruction */
        for (int w = 0; w < 4; w++) {
            hw_doa(host[i * 4 + w]);        /* SWR = word */
            uint16_t cmd = FN_DEP | REG_PS_TMA | (w << 4);
            if (w == 3) cmd |= (3 << 6);    /* INC=TMA on last word */
            hw_doas(cmd);
        }
    }
}

/* APPUT -- transfer data from host to AP via DMA.
 * host: host data array, ap: AP memory address,
 * n: element count, fmt: format (0=32-bit, 1=16-bit int, 2=float). */
void apput(const uint16_t *host, uint16_t ap, int n, int fmt)
{
    uint16_t ctl;
    int wc = n;

    switch (fmt) {
    case 0: ctl = 0x00; wc = n * 2; break;  /* 32-bit, host→AP */
    case 1: ctl = 0x02; break;               /* 16-bit integer */
    case 2: ctl = 0x04; wc = n * 2; break;   /* float conversion */
    default: apstop(6); return;
    }
    rundma((uint16_t)(uintptr_t)host, ap, (uint16_t)wc, ctl);
}

/* APGET -- transfer data from AP to host via DMA.
 * Same as APPUT but in reverse direction. */
void apget(uint16_t *host, uint16_t ap, int n, int fmt)
{
    uint16_t ctl;
    int wc = n;

    switch (fmt) {
    case 0: ctl = 0x20; wc = n * 2; break;  /* 32-bit, AP→host */
    case 1: ctl = 0x22; break;               /* 16-bit integer */
    case 2: ctl = 0x24; wc = n * 2; break;   /* float conversion */
    default: apstop(6); return;
    }
    rundma((uint16_t)(uintptr_t)host, ap, (uint16_t)wc, ctl);
}

/* OAPME -- select MD page for DMA.
 * Writes the page select value via DEP into DPA register. */
void oapme(int page)
{
    hw_doa((uint16_t)page);
    hw_doas(FN_DEP | REG_DPA);
}

/* APRUN -- start an AP program (from FDAPEX.FTN).
 * psaddr: PS entry address, locadr: local data block address,
 * option: call type (1=ADC, 2/3=UDC), ovflg: overlay flag,
 * brkloc: breakpoint. */
void aprun(uint16_t psaddr, uint16_t locadr, int option, int ovflg,
           uint16_t brkloc)
{
    uint16_t entry = psaddr;
    uint16_t slist[16];
    int code[4] = {0};

    if (ovflg && apldcm.iovs[1] != 0) {
        /* Load overlay IDs via DMA */
        apldcm.iovs[0] = entry;
        rundma((uint16_t)(uintptr_t)&apldcm.iovs[0],
               (sys.super) ? 0 : 10,
               (uint16_t)(apldcm.iovs[1] + 2), DMA_CTL_16BIT);
    }

    if (option == 1) {
        /* ADC call: load parameter addresses via DMA */
        int nparam = apldcm.ipav[0];
        if (nparam > 0) {
            rundma((uint16_t)(uintptr_t)&apldcm.ipav[1],
                   locadr, (uint16_t)nparam, DMA_CTL_16BIT);
        }
        apwd();
        slist[0] = locadr;
        slist[1] = (uint16_t)nparam;
        spldgo(slist, 2, entry, brkloc);
        apwr();
    } else {
        /* UDC call */
        if (ovflg && apldcm.iovs[1] != 0)
            apwd();
        spldgo((uint16_t *)&apldcm.ipav[1], apldcm.ipav[0],
               entry, brkloc);
        if (option == 3)
            apwr();
    }
    apldcm.iovs[1] = 0;

    /* Check for AP FORTRAN STOP statement */
    if (sys.super) return;
    apout(2, 1024);                        /* EXAM PSA */
    int psa = apin(3);                     /* read LITES (contains PSA?) */
    if (psa == 14) return;                 /* normal halt at bootstrap */
    /* AP stopped with STOP number */
    apexam(REG_CB, 3);                     /* get stop number */
    halt_addr = psa;
    stop_num = code[3];
    apstop(12);
    runap((uint16_t)psa, 1, 0, 0x3FFF);    /* continue */
}

/* APLLI -- initialize load module loader.
 * Associates a file with a load module ID. */
void aplli(const char *filename, int lun, int option, int lmid)
{
    (void)filename;  /* file I/O handled separately on DG */
    /* Check if already registered */
    for (int i = 0; i < lmte; i++) {
        if (lmt[i].id == lmid) return;
    }
    if (lmte >= LMT_MAX) {
        apstop(8);
        return;
    }
    lmt[lmte].id = lmid;
    lmt[lmte].option = option;
    lmt[lmte].lun = lun;
    lmte++;
}

/* APOVIN -- place overlay handler in PS.
 * Loads the hardcoded overlay handler microcode into PS at address 16. */
void apovin(void)
{
    /* Overlay handler microcode (from FDAPEX.FTN DATA statements).
     * 74 PS words = 296 16-bit values. */
    static const uint16_t ov[] = {
         4616,     0,     0,     3,  4616,     0,     0,    29,
         4616,     0,     0,    35,     3, 33792,  1024,    15,
            0,     0,     0,     0, 17404,     0,  3072,   208,
          956,    82,  1024,    15,   952,   402,  3072,   208,
          703, 33359,  3072,     0,     3, 33792,  1024,    11,
          932,     0,  1024,    12,     3, 33792,  1024,    12,
          936,     0,  2560,     0,   616,     0,     0,     0,
          680,     0,     0,     0,   928,   404,  2560,     0,
         4620,     0,     0,    21,   612,     0,  3072,    48,
            0,    76,     0,     0,     3, 33792,  1024,    10,
         4876,     0,     0,     2,     0,   224,     0,     0,
            3, 34304,  2560,     0,     3, 33792,  1024,    16,
          896,     0,  1024,    16,   643, 33280,  3072,    16,
          896,   495,  2560,     0,   896,     0,  2560,     0,
         4628,     0,     0,     0,  4608,     0,     0,    13,
            3, 33792,  1024,    10,     0,     0,     0,     0,
            0,     0,     0,     0,     3, 33792,  2560,     0,
            0,     0,     0,     0,     0,     0,     0,     0,
          928,     0,  2560,     0,     3, 33792,  1024,     1,
          948,     0,  1024,     4,   952,     0,     0,    16,
          940,     0,  2560,     0,   623, 36352,  1024,    26,
          947, 33792,  2560,     0, 13216,    32,     0,     0,
          684,   404,     0,     0,   952,   402, 18949,     0,
         9072,    77,     0,    48,     3, 61440,  1024,    65534,
          923, 51200,   512,     0,     3, 49152,     0,     0,
            3, 36352,  1024,    24,     3, 34304,  1024,     0,
          927, 51200,   512,    32,   956,     0,  1024,    27,
            0,     0,  7680, 32800,   952,     0,  2560,     0,
        17336,     0, 19460,    32,     3, 34304,  2560,     0,
        17405, 56320,   256,     0,
    };
    loadps(ov, 16, sizeof(ov) / (4 * sizeof(uint16_t)));
    apwd();
}

/* APSEIN -- place sign extend code in PS (no-op for 16-bit hosts). */
void apsein(void) { }

/* APGSEI -- get sign-extended integers (no-op for 16-bit hosts). */
void apgsei(uint16_t *host, uint16_t ap, int n) { (void)host; (void)ap; (void)n; }

/* APEXC -- execute channel program (no-op, CPAPEX not implemented). */
void apexc(void) { }

/* APMODE -- switch CPAPEX modes (no-op). */
void apmode(int m) { (void)m; }

/* APGMOD -- get CPAPEX mode (always step mode). */
int apgmod(void) { return 1; }
