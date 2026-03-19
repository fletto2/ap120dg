/* fdapex.h -- FPS AP-120B / FPS-100 Host Driver API
 *
 * C translation of the FDAPEX.FTN + DAPEX.MAC driver stack.
 * Platform provides a single function: fps_io(pulse, code, data)
 */

#ifndef FDAPEX_H
#define FDAPEX_H

#include <stdint.h>

/* ---- Platform interface (one function) ---- */
extern uint16_t fps_io(int pulse, int code, uint16_t data);

/* ---- DAPEX layer (host-dependent, was assembly) ---- */

int      apasgn(int apno, int action);
void     aprlse(void);
void     aprset(void);

void     apout(int num, uint16_t val);
uint16_t apin(int num);
uint16_t apexam(int regsel, int word);

void     runap(uint16_t psa, int noload, uint16_t swr, uint16_t fn);
void     spldgo(const uint16_t *slist, int nspads, uint16_t start, uint16_t brkloc);
int      tstrun(void);
int      wtrun(void);
int      apwr(void);

void     rundma(uint16_t host, uint16_t apma, uint16_t wc, uint16_t ctl);
void     apwd(void);
int      tstdma(void);
int      wtdma(void);

void     apiena(void);
void     apidis(void);
void     apwi(void);
int      tstint(void);

void     apsupv(int mode);
int      hput(uint16_t datum);
uint16_t hget(void);
uint16_t htst(void);

void     apstop(int ernum);
void     looky(uint16_t *swr, int *runfg, uint16_t *fn, uint16_t *ctl);
int      virp(void);

/* ---- FDAPEX layer (host-dependent FORTRAN, now C) ---- */

void     aprun(uint16_t psaddr, uint16_t locadr, int option, int ovflg, uint16_t brkloc);
void     apovin(void);
void     loadps(const uint16_t *host, uint16_t ps_addr, int nwords);
void     apput(const uint16_t *host, uint16_t ap, int n, int fmt);
void     apget(uint16_t *host, uint16_t ap, int n, int fmt);
void     oapme(int page);
void     aplli(const char *filename, int lun, int option, int lmid);
void     apsein(void);
void     apgsei(uint16_t *host, uint16_t ap, int n);
void     apexc(void);
void     apmode(int m);
int      apgmod(void);

#endif /* FDAPEX_H */
