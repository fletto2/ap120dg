/* pdp11_fps_load.c: FPS AP-120B .APO microcode file loader

   Loads .APO (AP Object) files into the FPS Program Store memory.
   Called from the SimH command line:
     sim> attach FPS filename.APO

   .APO format (text):
     ***TITLE
     routinename
     ***FPB (function parameter block)
     ...
     ***AENTRY / ***ENTRY
     name  addr  nargs  nwords
     ***CODE
     loadaddr  0  pssize  mdsize      (header)
     *  reloc_info                     (relocation records)
     w0  w1  w2  w3                   (4 octal 16-bit words = 1 PS word)
     ...
     ***EXT
     external_name
     ***END

   Each routine in the .APO file is loaded at the address specified
   in its ENTRY record. The CODE section contains the actual 64-bit
   microcode as four octal 16-bit words per line.
*/

#include "pdp11_defs.h"
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stdlib.h>

/* From nova_fps.c */
extern t_uint64 *fps_ps;
extern int32 fps_psa;

#define PS_SIZE 4096

/* Load a single .APO routine's CODE section into PS */
static int fps_load_code_section (FILE *f, int32 base_addr)
{
char line[256];
int32 addr = base_addr;
int32 count = 0;

while (fgets (line, sizeof (line), f)) {
    char *p = line;
    int32 w0, w1, w2, w3;

    /* Skip leading whitespace */
    while (*p && isspace (*p)) p++;

    /* Skip relocation records (start with '*' but NOT '***') */
    if (*p == '*' && strstr(p, "***") == NULL) continue;

    /* Check for section markers (may have numeric prefix) */
    if (strstr (p, "***") != NULL) {
        /* Push back so outer loop can re-read this line */
        fseek (f, -(long)strlen(line), SEEK_CUR);
        return count;
        }

    /* Skip empty lines */
    if (*p == '\0' || *p == '\n') continue;

    /* Parse 4 octal words */
    if (sscanf (p, "%o %o %o %o", &w0, &w1, &w2, &w3) == 4) {
        if (fps_ps && addr < PS_SIZE) {
            t_uint64 word = ((t_uint64)(w0 & 0xFFFF) << 48) |
                            ((t_uint64)(w1 & 0xFFFF) << 32) |
                            ((t_uint64)(w2 & 0xFFFF) << 16) |
                            (t_uint64)(w3 & 0xFFFF);
            fps_ps[addr] = word;
            addr++;
            count++;
            }
        }
    }
return count;
}


/* Load an entire .APO file */

t_stat fps_load_apo (FILE *f)
{
char line[256];
int32 total_words = 0;
int32 total_routines = 0;
int32 entry_addr = 0;
char current_routine[64] = "";

if (fps_ps == NULL)
    return SCPE_MEM;

rewind (f);

while (fgets (line, sizeof (line), f)) {
    char *p = line;
    while (*p && isspace (*p)) p++;

    /* ***TITLE - next line is routine name */
    if (strstr (p, "***TITLE") != NULL) {
        if (fgets (line, sizeof (line), f)) {
            p = line;
            while (*p && isspace (*p)) p++;
            /* Copy routine name, strip newline */
            strncpy (current_routine, p, sizeof(current_routine) - 1);
            current_routine[sizeof(current_routine) - 1] = '\0';
            p = current_routine;
            while (*p && *p != '\n' && *p != '\r') p++;
            *p = '\0';
            }
        continue;
        }

    /* ***ENTRY - parse entry point address */
    if (strstr (p, "***ENTRY") != NULL) {
        if (fgets (line, sizeof (line), f)) {
            char name[64];
            int32 addr, nargs, nwords;
            if (sscanf (line, "%s %d %d %d", name, &addr, &nargs, &nwords) >= 2)
                entry_addr = addr;
            }
        continue;
        }

    /* ***CODE - load microcode */
    if (strstr (p, "***CODE") != NULL) {
        int32 load_addr = 0, ps_size = 0, md_size = 0;

        /* Read header line (load address, 0, ps_size, md_size) */
        if (fgets (line, sizeof (line), f)) {
            int32 dummy;
            sscanf (line, "%o %o %o %o", &load_addr, &dummy, &ps_size, &md_size);
            }

        /* Skip first relocation record (if present) */
        /* Then load code words */
        int32 n = fps_load_code_section (f, load_addr);
        total_words += n;
        total_routines++;

        sim_printf ("FPS: Loaded %s at PS[%04o], %d words\n",
                    current_routine, load_addr, n);
        continue;
        }
    }

sim_printf ("FPS: Loaded %d routines, %d total PS words\n",
            total_routines, total_words);
return SCPE_OK;
}
