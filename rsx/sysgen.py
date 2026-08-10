#!/usr/bin/env python3
"""Drive the RSX-11M V4.0 SYSGEN by QUESTION TEXT, not by position.

Each answer is bound to a distinctive fragment of its own question, so a
changed question count cannot silently misalign the rest -- which is what
broke the positional replay.  SimH expect rules are one-shot, and each
question is asked once, so one rule per question is the right shape.
Unanswered questions simply stall, and the log shows exactly which.
"""
import subprocess, sys, os

SIM = "/home/fletto/ext/src/claude/ap120/simh/BIN/pdp11"

# (fragment of the question, answer).  "" means take the default.
QA = [
    # --- boot of the unmapped baseline, then switch to the mapped one ---
    ("PLEASE ENTER TIME AND DATE",      "12:00 09-AUG-86"),
    ("ENTER LINE WIDTH",                "\\rINS $BOO\\rBOO [1,54]RSX11M"),
    # --- the mapped baseline comes up and runs STARTUP again ---
    ("PLEASE ENTER TIME AND DATE",      "12:00 09-AUG-86"),
    ("ENTER LINE WIDTH",                "\\rINS $PIP\\rSET /UIC=[200,200]\\r@SYSGEN"),
    # --- SYSGEN phase I, setup ---
    # Autoconfigure=Y appeared to hang after question 2, but that judgement
    # came from a log that had stopped growing -- the same reasoning that was
    # WRONG at the K-series question, which turned out to be merely slow.
    # Retesting with a long window, because autoconfigure removes the entire
    # per-device interrogation that the manual path requires.
    # Retest result: autoconfigure=Y does NOT hang -- it reached questions 3
    # and 4, so the earlier "hangs after question 2" claim was wrong (it was
    # read off a log that had merely stopped flushing).  But with Q1 and Q2
    # asked back to back the sends overlap and misdeliver: Q2 received "YY"
    # and Q4 got N where Y was sent.  The manual path delivers every answer
    # correctly, so stay on it and pay the per-device cost.
    ("Autoconfigure the host",          "N"),
    ("inhibit execution of MCR",        "N"),
    ("made a copy of the distribution", "Y"),
    ("generating a mapped system",      "Y"),
    ("be deleted?",                     "Y"),
    ("input saved answer file",         "N"),
    # Y takes DEC's canned answers for the whole executive-options section
    # instead of asking them one at a time -- which is dozens of questions,
    # each costing a full ~10-minute run to discover.  The standard set is
    # what a general-purpose system wants anyway.
    ("Standard Function System",        "Y"),
    ("output saved answer file",        ""),
    ("Clean up files from previous",    "Y"),
    ("Chain to Phase II",               "Y"),
    ("EXCPRV disk",                     ""),
    # --- target configuration ---
    ("Processor Type  [D:",             "11/44"),
    ("switch register",                 ""),
    # BISECT: 1920 is V4.0's documented maximum and the generated system,
    # while it boots, cannot execute ANY MCR command -- not even an invalid
    # one, which needs no disk.  The baseline that works on this same
    # emulated machine runs at 124 K.  Testing a modest size to find out
    # whether memory size is what breaks it.
    ("Memory size",                     "512"),
    ("K-series devices",                "N"),
    # --- 11/44 CPU options: FPP and CIS are both fitted on the target ---
    # SimH's expect is CASE-SENSITIVE, and SYSGEN's capitalisation is not
    # predictable ("Extended instruction set (EIS)", not "...Instruction
    # Set").  Every fragment below therefore starts one character in, so the
    # case of the leading letter cannot matter.
    ("loating point processor",         "Y"),
    ("(EIS)",                           "Y"),
    ("(CIS)",                           "Y"),
    ("(FIS)",                           "N"),
    ("arity support",                   "N"),
    ("ighest interrupt vector",         ""),
    ("ache memory",                     "N"),
    ("apping registers",                "Y"),
    # Speculative rules for questions not yet reached.  A rule that never
    # matches costs nothing, and each one that does saves a whole ~8-minute
    # run, so it is worth arming ahead of the dialogue.
    ("xtended memory",                  "Y"),
    ("assbus",                          "N"),
    ("XDT",                             "N"),
    ("rror logging",                    "N"),
    ("ulti-user protection",            "Y"),
    ("oadable driver",                  "Y"),
    ("heckpointing",                    "Y"),
    ("ECnet",                           "N"),
    # Question 15 repeats until "." terminates it.  SimH fires rules with the
    # SAME match string in definition order, so one rule per repetition works.
    # The first "*" makes SYSGEN print its device table, which is the
    # authoritative list of mnemonics and the entry syntax.
    ("Devices [S]",                     "*"),
    ("Devices [S]",                     "DM 1"),   # RK611: 2x RK07 + 1x RK06
    ("Devices [S]",                     "DL 1"),   # RL11, for the RL02 kit
    # DZ REMOVED for now, deliberately.  With two DZ11s configured, RSX
    # numbers TT0:-TT15: onto the DZ lines and MCR's session lands on TT0: --
    # a DZ line with nothing connected under SimH -- while the DL11 console
    # still receives all CO: output.  That matches the symptom exactly: the
    # banner appears, typed characters echo, and MCR never acts on them.
    # The real machine's 16 lines can be added once the console is proven.
    # ("Devices [S]",                   "DZ 2"),
    ("Devices [S]",                     "DD 1"),   # TU58
    ("Devices [S]",                     "."),
    # --- peripheral options section ---
    ("line printer available",          "N"),
    ("RT terminal",                     "Y"),
    ("ideo terminal",                   "Y"),
    ("120 columns",                     "Y"),
    ("ssembly listings device",         ""),   # NL: -- discard listings
    # "ap device" ALSO matched "listing/map device have at least 120
    # columns", answering that question with a default and shifting the
    # 120-columns answer onto the next one.  Speculative fragments must be
    # long enough to be unique -- the risk of arming guesses ahead.
    ("ap device for Executive",         ""),
    ("communications products",         "N"),   # no DECnet / comm drivers
    ("CDA memory dump device",          "DM0:"),  # crash dumps to the RK07
    ("crash dump",                      "DM0:"),
    ("memory dump device CSR",          ""),    # default 177440 = the RK611
    ("memory dump device vector",       ""),
    # --- system options ---
    # Keep the default system name RSX11M: it names the saved system image,
    # and every documented boot command (BOO [1,54]RSX11M, VMR SAV) uses it.
    ("name would you like to give your system", ""),
    ("system UIC",                      ""),
    ("in ticks",                        ""),
    # --- peripheral configuration: one question per controller, each with a
    # correct default already shown (e.g. "YL controller 0 [D: 60,177560,NO]").
    # Same-string rules fire in definition order, so a batch of identical
    # rules defaults them in sequence.  Note the trailing space: it stops
    # these matching "number of controllers" in the earlier device prompt.
    ("controller ",                     ""),
    ("controller ",                     ""),
    ("controller ",                     ""),
    ("controller ",                     ""),
    ("controller ",                     ""),
    ("controller ",                     ""),
    ("controller ",                     ""),
    ("controller ",                     ""),
    ("controller ",                     ""),
    ("controller ",                     ""),
    ("controller ",                     ""),
    ("controller ",                     ""),
    ("controller ",                     ""),
    ("controller ",                     ""),

    ("ueue Manager",                    "N"),
    ("nstall tasks",                    ""),
    ("System image name",               ""),
    ("Highest UIC",                     ""),
    # Speculative terminal/system options.  With a Standard Function System
    # most of these should be preset, but a rule that never fires is free.
    ("nsolicited input",                ""),
    ("ariable length terminal",         "Y"),
    ("ransparent read",                 ""),
    ("old screen",                      ""),
    ("reakthrough write",               ""),
    ("ower case",                       ""),
    ("intrps./sec",                     ""),
    ("atchdog timer",                   "N"),
    ("ine frequency",                   ""),
    # --- after Phase II: boot the generated system and make it self-booting.
    # The baseline is consumed by the generation, so this must happen in the
    # SAME run -- the RSXM32 volume will not boot on its own until SAV /WB
    # has written a bootstrap for the new system.
    ("End of SYSGEN phase II",          r"\rBOO [1,54]RSX11M"),
    # Match the REAL banner, not SYSGEN's printed example.  SYSGEN's closing
    # instructions contain the literal line
    #     ;       RSX11M V4.0 BL32     1920.K  MAPPED
    # so a "1920.K" fragment fires on the documentation and consumes the rule
    # long before the system actually boots.  Anchoring on CR-LF immediately
    # before the name excludes the example, whose line starts with ";".
    # SAV also refuses while the checkpoint file is active
    # ("SAV -- Checkpoint file still in use on DL0:"), so release it first.
    # The freshly booted system echoes typed characters before MCR is ready
    # to act on them -- the first send lost its leading "T" (TIM -> IM) and
    # neither ACS nor SAV was ever executed, while the CPU sat in RSX's idle
    # loop at 98%.  Give MCR time to come up before typing at it.
    # A freshly booted RSX terminal does NOT dispatch unsolicited input to
    # MCR.  CTRL/C is what attracts it, and MCR answers with "MCR>".  That
    # prompt accepts ONE command and then returns, so every command needs
    # its own CTRL/C -- sent as a block, all but the first are lost.
    # (This was the real cause of the "generated system has no CLI" dead
    # end; the CLI was fine and nothing was listening to the typing.)
    (r"\r\nRSX11M V4.0 BL32",
     # ACS dropped: a freshly booted system has no checkpoint file, so
     # deallocating one is a no-op at best.  SAV alone, fewest variables.
     "\\003\\rSAV /WB", 400000000),
    (r"\r\nRSX11M V4.0 BL32",
     "\\003\\rRED DL:=SY:\\r\\003\\rRED DL:=LB:\\r"
     "\\003\\rMOU DL:RSXM32\\r\\003\\r@DL:[1,2]STARTUP",
     400000000),
]

ini = ["set cpu 11/44", "set cpu 4M", "set cpu fpp", "set cpu cis",
       "set console log=sysgen.log",
       "set rl enabled", "set rl0 rl02", "set rl1 rl02", "set rl2 rl02", "set rl3 rl02",
       "att rl0 m40/rsxm32.dsk", "att rl1 m40/excprv.dsk",
       "att rl2 m40/mcrsrc.dsk", "att rl3 m40/rlutil.dsk",
       # noautosize is REQUIRED before the type: with autosize on, SimH sizes
       # the drive from the existing container and silently overrides the
       # type, so "set hk2 rk06" still autoconfigured as an RK07.
       "set hk enabled",
       "set hk0 noautosize", "set hk1 noautosize", "set hk2 noautosize",
       "set hk0 rk07", "set hk1 rk07", "set hk2 rk06",
       "att hk0 usagi0.dsk", "att hk1 usagi1.dsk", "att hk2 usagi2.dsk",
       "set dz disabled", "set xu enabled"]
for entry in QA:
    frag, ans = entry[0], entry[1]
    after = entry[2] if len(entry) > 2 else 15000000
    # NO leading \r: it answers the current prompt with a default and
    # shifts every subsequent answer one question late.
    # No prefix character at all:
    #   - a leading CR answers the current prompt with a default and shifts
    #     every later answer one question late;
    #   - a leading space is NOT ignored by RSX -- " Y" is rejected and the
    #     prompt simply repeats.
    # The dropped-first-character effect is avoided instead by waiting long
    # enough after the match for RSX to have posted its terminal read.
    ini.append('expect "%s" send after=%d,delay=250000,"%s\\r"; continue'
               % (frag, after, ans))
ini.append("boot rl0")
open("sysgen.ini","w").write("\n".join(ini) + "\n")

# SYSGEN WRITES TO THE DISTRIBUTION DISKS.  A second run that boots the
# half-generated rsxm32 crashes ("SYSTEM CRASH AT LOCATION 011520" during
# SAV, before SYSGEN is even reached), so every attempt must start from the
# pristine kit.  m40.orig/ is the untouched extract of rsx11m40.zip.
import shutil, glob
for src in glob.glob("m40.orig/*.dsk"):
    shutil.copy2(src, "m40/" + os.path.basename(src))

# Kill any simulator left over from an earlier run FIRST.  A stale one keeps
# reading this same sysgen.ini, writing this same sysgen.log and holding the
# same disk containers, so two machines interleave into one log and the run
# looks like it stalls at a random question.
subprocess.run(["pkill", "-9", "-f", SIM], stdout=subprocess.DEVNULL,
               stderr=subprocess.DEVNULL)

secs = int(sys.argv[1]) if len(sys.argv) > 1 else 200
if os.path.exists("sysgen.log"): os.remove("sysgen.log")
subprocess.run(["timeout", str(secs), SIM, "sysgen.ini"],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("%d question rules armed" % len(QA))
