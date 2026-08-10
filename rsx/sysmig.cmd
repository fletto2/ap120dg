; Move the RSX-11M V4.0 system from the RL02 to an RK07.
;
; The RL02 is 10240 blocks and the install needs LIB100.OLB on LB:
; alongside room for TKB's work file; 468 blocks free does not cover
; both.  The machine this is for -- Usagi's PDP-11/44 -- has an 84 MB
; Fujitsu behind an Emulex SC12 presenting RK07s, so an RK07 system
; disk is the correct configuration, not a workaround.
;
INS $PIP
INS $UFD
INS $INI
INS $MOU
ALL DM1:
; /BAD=[NOAUTO]: an emulated pack carries no manufacturer bad-sector
; file, and INI rejects the volume without one.  This is INI's own
; documented option for that case, not a way round it.
INI DM1:RSXBIG/BAD=[NOAUTO]
MOU DM1:RSXBIG
SET /UIC=[1,1]
UFD DM1:[1,1]
PIP DM1:[1,1]/NV/CO=DL0:[1,1]*.*
SET /UIC=[1,2]
UFD DM1:[1,2]
PIP DM1:[1,2]/NV/CO=DL0:[1,2]*.*
SET /UIC=[1,3]
UFD DM1:[1,3]
PIP DM1:[1,3]/NV/CO=DL0:[1,3]*.*
SET /UIC=[1,4]
UFD DM1:[1,4]
PIP DM1:[1,4]/NV/CO=DL0:[1,4]*.*
SET /UIC=[1,6]
UFD DM1:[1,6]
PIP DM1:[1,6]/NV/CO=DL0:[1,6]*.*
SET /UIC=[1,7]
UFD DM1:[1,7]
PIP DM1:[1,7]/NV/CO=DL0:[1,7]*.*
SET /UIC=[1,20]
UFD DM1:[1,20]
PIP DM1:[1,20]/NV/CO=DL0:[1,20]*.*
SET /UIC=[1,24]
UFD DM1:[1,24]
PIP DM1:[1,24]/NV/CO=DL0:[1,24]*.*
SET /UIC=[1,30]
UFD DM1:[1,30]
PIP DM1:[1,30]/NV/CO=DL0:[1,30]*.*
SET /UIC=[1,34]
UFD DM1:[1,34]
PIP DM1:[1,34]/NV/CO=DL0:[1,34]*.*
SET /UIC=[1,50]
UFD DM1:[1,50]
PIP DM1:[1,50]/NV/CO=DL0:[1,50]*.*
SET /UIC=[1,54]
UFD DM1:[1,54]
PIP DM1:[1,54]/NV/CO=DL0:[1,54]*.*
SET /UIC=[1,60]
UFD DM1:[1,60]
PIP DM1:[1,60]/NV/CO=DL0:[1,60]*.*
SET /UIC=[1,64]
UFD DM1:[1,64]
PIP DM1:[1,64]/NV/CO=DL0:[1,64]*.*
SET /UIC=[11,10]
UFD DM1:[11,10]
PIP DM1:[11,10]/NV/CO=DL0:[11,10]*.*
SET /UIC=[11,20]
UFD DM1:[11,20]
PIP DM1:[11,20]/NV/CO=DL0:[11,20]*.*
SET /UIC=[11,24]
UFD DM1:[11,24]
PIP DM1:[11,24]/NV/CO=DL0:[11,24]*.*
SET /UIC=[11,40]
UFD DM1:[11,40]
PIP DM1:[11,40]/NV/CO=DL0:[11,40]*.*
SET /UIC=[12,20]
UFD DM1:[12,20]
PIP DM1:[12,20]/NV/CO=DL0:[12,20]*.*
SET /UIC=[12,24]
UFD DM1:[12,24]
PIP DM1:[12,24]/NV/CO=DL0:[12,24]*.*
SET /UIC=[200,200]
UFD DM1:[200,200]
PIP DM1:[200,200]/NV/CO=DL0:[200,200]*.*
SET /UIC=[1,54]
PIP DM1:/FR
;
; SYSMIG DONE
;
