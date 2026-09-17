"""Attach the local nominal STEP model without resaving unrelated board items."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
hw=root/'hardware'
name='SW_SPST_Panasonic_EVPAW_3x2mm_H0.6mm'
model='''(model "${KIPRJMOD}/../HapticBracelet.3dshapes/EVPAWBD4A_nominal.step"
 (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))'''
assert (hw/'HapticBracelet.3dshapes/EVPAWBD4A_nominal.step').exists()
fp=hw/'HapticBracelet.pretty'/f'{name}.kicad_mod'
s=fp.read_text(); assert '(model ' not in s
fp.write_text(s.rstrip()[:-1]+'\n '+model+'\n)\n')
pcb=hw/'main/main.kicad_pcb';s=pcb.read_text()
start=s.index('(footprint "HapticBracelet:'+name+'"')
depth=0;quoted=False;escape=False
for end in range(start,len(s)):
    c=s[end]
    if quoted:
        if escape:escape=False
        elif c=='\\':escape=True
        elif c=='"':quoted=False
    elif c=='"':quoted=True
    elif c=='(':depth+=1
    elif c==')':
        depth-=1
        if depth==0:break
pcb.write_text(s[:end]+'\n '+model+'\n'+s[end:])
print('Attached STEP model in footprint library and placed SW3')
