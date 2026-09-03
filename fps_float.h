/* fps_float.h -- the AP 38-bit floating point arithmetic.

   SHARED BY BOTH DEVICE MODULES.  `nova_fps.c` and `pdp11_fps.c` each
   carry their own copy of the AP execution engine, and this file records
   at length how far the PDP-11 copy drifted: roughly twenty defects,
   including a mantissa scale that made every operand twice its value.
   Hand-porting is what allowed that drift, so the arithmetic -- which is
   entirely host-independent -- lives here and is included by both.

   Everything in this file references only its own functions and the FP_*
   constants: no device state, no registers, no host memory.  The AP
   format is 10-bit biased exponent in bits 37-28 and a 28-bit TWO'S
   COMPLEMENT mantissa in 27-0, scaled 2**27 -- the ROM's own convention,
   which SIM100's TMROM triples confirm (TM(66) = (513,1024,0) is 1.0).

   Covered by test_apo_exec.py (12 routines from the shipped libraries)
   and test_hsr_identity.py.  */

static int32 fp_get_exp (t_uint64 val)
{
return (int32)((val >> FP_EXP_SHIFT) & FP_EXP_MASK);
}

static int32 fp_get_mant (t_uint64 val)
{
int32 mant = (int32)(val & FP_MANT_MASK);
if (mant & 0x08000000)                                 /* Sign extend 28-bit */
    mant |= (int32)0xF0000000;
return mant;
}

/* 38-bit AP float -> double, for tracing only. */
static double fps_38bit_to_double (t_uint64 val)
{
int32 exp = fp_get_exp (val);
int32 mant = fp_get_mant (val);
if (mant == 0) return 0.0;
/* MANTISSA SCALE IS 2**27, the ROM's own convention -- see the SPUFLT
   note in CLAUDE.md.  FPS's source hard-codes it: SPUFLT floats an
   integer with "LDSPI C27; DB=27." and MDPX re-exponents to 512+27, which
   is only correct if a mantissa divides by 2**27. */
return (double)mant / 134217728.0 * pow (2.0, (double)(exp - FP_EXP_BIAS));
}

static t_uint64 fp_pack (int32 exp, int32 mant)
{
return ((t_uint64)(exp & FP_EXP_MASK) << FP_EXP_SHIFT) |
       ((t_uint64)mant & FP_MANT_MASK);
}

/* OPERAND ALIGNMENT, shared by the add and the LOGICAL ops.  SIM100
   reaches its AND (label 500) and OR (600) THROUGH the same alignment
   path as the add (200/250), so they must get the identical treatment --
   the >32 saturation and the sticky bit included.  Keeping a second copy
   inline in the FAND/FOR arms is how those two came to lack both. */
static void fps_38bit_align (t_uint64 a, t_uint64 b,
                             int32 *ma_out, int32 *mb_out, int32 *ec_out)
{
int32 ea = fp_get_exp (a), eb = fp_get_exp (b);
int32 ma = fp_get_mant (a), mb = fp_get_mant (b);
int32 diff = ea - eb, sticky;

*ec_out = (diff >= 0) ? ea : eb;
if (diff > 0) {
    if (diff > 32) { sticky = (mb != 0); mb = 0; }
    else if (diff == 32) { sticky = (mb != 0); mb = (mb < 0) ? -1 : 0; }
    else { sticky = ((mb & ((1 << diff) - 1)) != 0); mb >>= diff; }
    if (sticky && !(mb & 1)) mb |= 1;
    }
else if (diff < 0) {
    int32 sh = -diff;
    if (sh > 32) { sticky = (ma != 0); ma = 0; }
    else if (sh == 32) { sticky = (ma != 0); ma = (ma < 0) ? -1 : 0; }
    else { sticky = ((ma & ((1 << sh) - 1)) != 0); ma >>= sh; }
    if (sticky && !(ma & 1)) ma |= 1;
    }
*ma_out = ma; *mb_out = mb;
}

/* NORMALISE A MANTISSA/EXPONENT PAIR -- SIM100's `CALL NORMAL` at label
   1000, which EVERY arithmetic path exits through: the add and subtract
   at 300/400, the LOGICAL ops at 500/600, and the single-operand
   conversions.  Shared so the logical ops cannot drift from the add, the
   way FAND and FOR did before they were folded onto fps_38bit_align. */
static t_uint64 fps_38bit_normalise (int32 result_exp, int32 result_mant)
{
if (result_mant == 0) return 0;
while (result_mant > 0x07FFFFFF || result_mant < -0x08000000) {
    result_mant >>= 1;
    result_exp++;
    }
while (result_mant != 0 &&
       result_mant < 0x04000000 && result_mant >= -0x04000000) {
    result_mant <<= 1;
    result_exp--;
    }
if (result_exp >= (int32)FP_EXP_MASK || result_exp <= 0) return 0;
return fp_pack (result_exp, result_mant);
}

static t_uint64 fps_38bit_add (t_uint64 a, t_uint64 b)
{
int32 exp_a = fp_get_exp (a), exp_b = fp_get_exp (b);
int32 mant_a = fp_get_mant (a), mant_b = fp_get_mant (b);
int32 result_exp, result_mant, diff;

/* NO EARLY RETURN.  SIM100 sends every ALU result through CALL NORMAL at
   label 1000; returning the surviving operand verbatim skips the normalise
   loops below, so `FADD ZERO,x` and `FSUB ZERO,x` -- both common idioms --
   propagate whatever form their operand had.  VDIV builds DPX(1) = -1.0
   with exactly `FSUBR ZERO,TMR` and needs the asymmetric negative form. */
if (mant_a == 0 && mant_b == 0) return 0;
if (mant_a == 0) { result_exp = exp_b; result_mant = mant_b; }
else if (mant_b == 0) { result_exp = exp_a; result_mant = mant_a; }
else {

/* Alignment is the SHARED helper -- see fps_38bit_align.  It was
   duplicated here and in the FAND/FOR arms, and the copies drifted: the
   logical ops lacked both the >32 saturation and the sticky bit until
   they were folded onto the helper.  One copy, one place to source. */
fps_38bit_align (a, b, &mant_a, &mant_b, &result_exp);

result_mant = mant_a + mant_b;
    }

/* Normalize */
if (result_mant == 0) return 0;
while (result_mant > 0x07FFFFFF || result_mant < -0x08000000) {
    result_mant >>= 1;
    result_exp++;
    }
/* Negative normalises into [-2**27,-2**26): SIM100 NORMAL label 300,
   "LOOK FOR 01 OR 10 AS THE TWO HIGH BITS".  Applied together with the
   F2CSM magnitude clamp below -- either alone is worse than neither. */
while (result_mant != 0 &&
       result_mant < 0x04000000 && result_mant >= -0x04000000) {
    result_mant <<= 1;
    result_exp--;
    }
if (result_exp >= (int32)FP_EXP_MASK || result_exp <= 0) return 0;
return fp_pack (result_exp, result_mant);
}

static t_uint64 fps_38bit_sub (t_uint64 a, t_uint64 b)
{
int32 exp_b = fp_get_exp (b);
int32 mant_b = fp_get_mant (b);
if (mant_b == 0) return a;
/* NEGATING -2**27 OVERFLOWS A 28-BIT TWO'S COMPLEMENT MANTISSA and wraps
   straight back to -2**27, so the subtraction silently becomes an add.
   That value is not exotic: since negatives normalise to [-2**27,-2**26)
   -- SIM100 NORMAL label 300 -- **every** normalised -1.0-style operand
   has it, and MDPX copies such a mantissa verbatim.  VDIV's
   `FSUB ZERO,MDPX(1)` is exactly this case, and it was inverting the
   scale factor 2**(-E-1) and with it every result the routine stores.
   Represent the magnitude one bit down with the exponent carried. */
if (mant_b == -0x08000000) {
    mant_b = 0x04000000;
    exp_b++;
    return fps_38bit_add (a, fp_pack (exp_b, mant_b));
    }
return fps_38bit_add (a, fp_pack (exp_b, -mant_b));
}

static t_uint64 fps_38bit_mul (t_uint64 a, t_uint64 b)
{
int32 exp_a = fp_get_exp (a), exp_b = fp_get_exp (b);
int32 mant_a = fp_get_mant (a), mant_b = fp_get_mant (b);
t_int64 prod;
int32 result_exp, result_mant;

if (mant_a == 0 || mant_b == 0) return 0;

prod = (t_int64)mant_a * (t_int64)mant_b;
/* A mantissa m represents m/2^28 -- fps_38bit_to_double divides by
   268435456.0 -- so the product of two of them, scaled 2^-56, has to
   come back by 28 bits, not 27.  Shifting by 27 left every product
   exactly a factor of two high, which is what VMUL returned: 8, 20, 36
   for an expected 4, 10, 18. */
/* With TRUE operands the derivation holds: two mantissas scaled 2**-27
   give a product scaled 2**-54, which comes back 27 bits.  While every
   stored value was 2x too large this had to be 28 to compensate, and
   VSQ returning 2, 8, 18 with 27 was the DMA defect showing through. */
result_mant = (int32)(prod >> 27);
result_exp = exp_a + exp_b - FP_EXP_BIAS;

/* Normalize */
if (result_mant == 0) return 0;
while (result_mant > 0x07FFFFFF || result_mant < -0x08000000) {
    result_mant >>= 1;
    result_exp++;
    }
/* NEGATIVE VALUES NORMALISE ASYMMETRICALLY.  SIM100's NORMAL, label 300,
   is "LOOK FOR 01 OR 10 AS THE TWO HIGH BITS" -- MOD(MC(1)/64,4) over
   mantissa bits 27:26 -- so a positive mantissa normalises into
   [2**26, 2**27) but a NEGATIVE one into [-2**27, -2**26).  -2**26 has
   bits 11 and is NOT normalised; it must shift once more.  A 28-bit two's
   complement mantissa holds -2**27 but not +2**27, and that extra bit is
   what -1.0 needs: mantissa -2**27 at exponent 512, not -2**26 at 513.
   Stopping at `> -0x04000000` threw it away -- invisible to add/multiply
   on positive data, fatal to any routine consuming a negative constant's
   MANTISSA BITS, which VDIV does through MDPX. */
while (result_mant < 0x04000000 && result_mant >= -0x04000000) {
    result_mant <<= 1;
    result_exp--;
    }
if (result_exp >= (int32)FP_EXP_MASK || result_exp <= 0) return 0;
return fp_pack (result_exp, result_mant);
}
