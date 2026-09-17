"""Hide metadata fields and verify the bounded final edit."""
from kicad_edit import *
import re,json
path=HW/'main/main.kicad_pcb'; text=path.read_text()
start=text.index('(footprint "HapticBracelet:SW_SPST_Panasonic_EVPAW_3x2mm_H0.6mm"')
end=text.find('\n\t(footprint ',start+1)
assert end!=-1
s=text[start:end]
for key in ['MPN','Manufacturer','BOM Comments']:
    pattern=r'(\(property "'+key+r'".*?)(?=\n\t\t\(property|\n\t\t\(path|\n\t\t\(attr)'
    def fix(m):
        z=m[0].replace('(layer "B.SilkS")','(layer "B.Fab")\n\t\t\t(hide yes)')
        return z
    s,n=re.subn(pattern,fix,s,count=1,flags=re.S);assert n==1,key
text=text[:start]+s+text[end:];path.write_text(text)
before=load(HW/'backups/pre-sw3-evpaw-20260917/main.kicad_pcb');after=load(path)
def without_switch(a):
    return [x for x in a if not (isinstance(x,list) and x[0]=='footprint' and any(uq(z[1])=='Reference' and uq(z[2])=='SW3' for z in children(x,'property')))]
assert without_switch(before)==without_switch(after)
bs=load(HW/'backups/pre-sw3-evpaw-20260917/power.kicad_sch');ns=load(HW/'main/power.kicad_sch')
def strip_properties(a):
    if isinstance(a,list):
        return [strip_properties(x) for x in a if not (isinstance(x,list) and x[0]=='property' and uq(x[1]) in ['MPN','Manufacturer','Footprint','Datasheet','BOM Comments'])]
    return a
assert strip_properties(bs)==strip_properties(ns)
print('All other PCB items preserved; schematic circuit and SW3 identity preserved.')
