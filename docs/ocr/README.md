# OCR'd FPS-100 manuals

The FPS manual scans on bitsavers are images with no text layer, which
made them unsearchable and left several reconstruction details resting on
inference. These are `tesseract --psm 6` transcriptions at 300 dpi.

They are **OCR output, not proofread text**: figures do not survive, table
columns are often mangled, and digits are the least reliable characters of
all -- `0`/`O`, `1`/`l`, `5`/`S`. Check any number against the page image
before relying on it. Page images can be regenerated with

    pdftoppm -r 300 -gray -png <manual>.pdf pg

| file | source PDF | pages |
|---|---|---|
| `FPS100_Linker.txt`  | `FPS100_Linker.pdf`  | 38 |
| `FPS100_Loader.txt`  | `FPS100_Loader.pdf`  | 97 |
| `SUPERVISOR.txt`     | `FPS100_SupervisorRefMan.pdf` | 125 |
| `LIBEDITOR.txt`      | `FPS100_LibraryEditor.pdf` | 11 |
| `VFC100.txt`         | `FPS100_VectorFuncChainer.pdf` | 40 |
| `SWDEVEL.txt`        | `7292_AP-120B_swDevelMan.pdf` | 111 |
| `MATHLIB.txt`        | `860-7288-004_AP_mathLibr.pdf` | 153 |

## Not OCR: extracted text

`800-7428-001` (ASM100) and `860-7292-002` (AP-120B Program Development
Software) already carry a text layer, so these two are `pdftotext -layout`
output rather than OCR -- lossless, and far more trustworthy for digits
than anything above. Kept here so they are as quick to grep as the rest.

| file | source PDF | pages |
|---|---|---|
| `ASM100.txt` | `800-7428-001_..._ASM100_Reference_Manual_197909.pdf` | 109 |
| `PDS.txt`    | `860-7292-002_AP-120B_Program_Development_Software_Manual_Sep78.pdf` | 134 |

Their cover pages still come out as noise (`FPs-1cg Asserril?ler`) because
those *are* images; the body text is clean.

## What these settled

Facts that had been guesses until the text existed:

- **LNK100 figure 4-3** -- the E command load module is a leading count of
  program words, then four values per line, **decimal**, zero padded to
  five digits, each followed by a period. Both `lnk100.py` and the
  `LNK100.FTN` reconstruction had emitted octal with no count line.
- **LNK100 figure 4-4** -- the A command module opens `DATA CODE(1)/ 8/`
  with the instruction count, then groups of four `:oooooo` octal words.
- **Loader table 2-1 / Supervisor table 2-2** -- the overlay table entry is
  eight MD words: segment number, MD address, PS address, length, task id,
  residency bits, first-partition pointer, partition count. Both manuals
  agree; the reconstruction's guess was right.
- **Loader table 2-2** -- the TCB. RLINK/LLINK, RPRI, LENGTH, ID, OVLPTR,
  OVLCNT, DPRI, STATUS, RCLOCK/LCLOCK, TADDR, APSTAT3 = 55260 octal,
  SRS(0)=termination routine, SRS(1)=task PS address.
- **STATUS bits** -- 004000 unless `/M`, 010000 if `/S`, and 001000 only
  **when READYQ is defined**. `/I` is *not* a status bit: it places the
  task at the front of the ready queue.
- **OVLPTR is an address**, not an index -- Supervisor 2.2.3.2 and the
  Loader both say "address in the overlay table".
- **RCLOCK/LCLOCK point at RCLOCK itself** when the task is not queued.
- **ASM100 3.4.1** -- `$TASK idn {/M} {priority} {/I} {/S}`, priority
  decimal 1-255 and 100 by default. It is not read in the current radix.
- **One overlay table per task** (`.MPnnn`) plus `ISRMAP` for the interrupt
  service routines, but **one** PS partition table for the whole
  supervisor environment.
