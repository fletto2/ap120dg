# Hardware reference load modules

Each `.LM` here was produced by the **recovered LOD100** running on the
PDP-11/44 replica and extracted from its volume with `ods1make.py -x`.
They are ground truth: `test_lm_refs.py` builds the same jobs with
`lod100.py` and compares word for word.

| reference | job | what it exercises |
|---|---|---|
| `VATAN.LM` | `at.cmd` | the PC-relative rule, via the two relocations in all nine libraries that discriminate it |
| `VADD4.LM` | `v2.cmd` | a closure spanning four libraries |
| `NINE.LM` | `n9.cmd` | nine separate `LIB` commands, and the externals they leave unresolved |
| `APLIB.LM` | `apl.cmd` | one concatenated library looped to a fixed point |
| `OVERLAID.LM` | `ovh.cmd` | `TREE`/`OV`, and a child segment resolving a parent's symbol |
| `TASK1.LM` | `tk2.cmd` | `MODE TASK`, data blocks, TCB, partition table, ready queue |
| `TASK2.LM` | `tl.cmd` | the same across two `LINK` phases |
| `TWOTASK.LM` | `t2.cmd` | two tasks, three phases, one overlay table per task |

`TABLES.APO` is the supervisor's system commons, assembled from the
tape's `TABLES.S` by the original ASM100 on the replica; it is kept here
because reproducing it needs the PDP-11.  `APLIB.APO` is generated on
demand by `test_lm_refs.py` -- it is simply the nine shipped libraries
concatenated, which is what APEEL builds.

Run `test_lm_refs.py --self-test` to confirm the comparison still detects
a one-bit change.  It is written to fail loudly: an empty or short output
is an error rather than "nothing differs", which is the failure mode a
`min(len(a), len(b))` comparison hides.
