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
    # Memory size is NOT implicated: 512 K behaves identically to 1920 K,
    # so back to the target's real size.
    ("Memory size",                     "1920"),
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
    # Restored: a block replacement for the controller rules spanned these
    # and deleted them, which stalled the run at question 9 with no error.
    ("intrps./sec",                     ""),    # KW11-P not used
    ("ine frequency",                   ""),    # default A = 60 Hz
    ("atchdog timer",                   "N"),
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
    # SYNTAX IS dev=n, NOT "dev n".  "DM 1" is rejected with
    #   SGN -- Unrecognizable string "DM 1" -- Ignored
    # and SYSGEN then reports "Disks: None specified" and force-adds only
    # the console YL.  That produced a system with NO disk drivers, which
    # boots but cannot load a single task -- the real cause of the
    # "generated system executes no MCR command" dead end.
    # SYSGEN's own text: 'Enter responses as: dev1=number controllers,...'
    # 'Example: DK,DM=2,YL,NL.'  A trailing "." also terminates the inquiry.
    #   DM = RK611 (2x RK07 + RK06), DL = RL11 (the kit), DD = TU58,
    #   YL = console DL11, YZ = the two DZ11s (16 lines), NL = null.
    ("Devices [S]",                     "DM=1,DL=1,DD=1,YL=1,YZ=2,NL=1."),
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
    # --- peripheral configuration -------------------------------------
    # NOT answerable with a blanket default: the disks take a UNIT COUNT as
    # parameter 3 with no default, and a bare CR gets
    #   SGN -- Attempt to use non-existent default for parameter 3 -- RETRY
    # which loops forever.  Parameter lists read from SGNPER.CMD itself:
    #   DM  DEF1=210 DEF2=177440, p3=units (no default), DEF4="O"
    #   DL  DEF1=160 DEF2=174400, p3=units (no default, max 4)
    #   DD  DEF1=300 DEF2=176500, p3=units (no default, max 2)
    #   YL  DEF1=60  DEF2=177560 DEF3="NO"      -- all defaulted
    #   YZ  no vector/CSR default, p3=highest line (0-7), DEF4="300"
    # Device-specific fragments, so order cannot matter.
    ("DM controller 0",                 "210,177440,3"),   # 2x RK07 + RK06
    ("DL controller 0",                 "160,174400,4"),   # 4x RL02 (kit)
    # TU58 moved off vector 300: its default collides with DZ11 #0, giving
    #   VMR -- *FATAL*-Interrupt vector already in use  /  LOA DD:
    # The DZ addresses are fixed by the hardware (autoconfigure reports
    # 300/160100 and 310/160110), so the TU58 is the one that moves.
    # 320 is free: in use are 60,70,74,154,160,200,210,220,224,254,264,300,310.
    ("DD controller 0",                 "320,176500,2"),   # TU58, 2 units
    ("YL controller 0",                 ""),               # console DL11
    ("YZ controller 0",                 "300,160100,7"),   # DZ11 #0, 8 lines
    ("YZ controller 1",                 "310,160110,7"),   # DZ11 #1, 8 lines
    # Per-unit drive types (SGNPER.CMD 1740 and 1823).  Fragments include
    # the unit number, so each is unique and order does not matter.
    ("unit 0. is an RL01/RL02",         "RL02"),
    ("unit 1. is an RL01/RL02",         "RL02"),
    ("unit 2. is an RL01/RL02",         "RL02"),
    ("unit 3. is an RL01/RL02",         "RL02"),
    # The Usagi drive set: DM0/DM1 are RK07, DM2 is the RK06.
    ("unit 0. is an RK06/RK07",         "RK07"),
    ("unit 1. is an RK06/RK07",         "RK07"),
    ("unit 2. is an RK06/RK07",         "RK06"),
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
    # Is the system still alive after SAV?  Key on the ECHO of the command
    # (preceded by CRLF, so SYSGEN's ";     >SAV /WB" example cannot match)
    # and, long afterwards, send another CTRL/C.  A second "MCR>" means the
    # system survived and SAV simply did nothing visible; silence means SAV
    # wedged it.
    (r"\r\nSAV /WB", "\\003", 2000000000),
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
       "set dz enabled", "set xu enabled"]
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
