"""Bounded SW3 replacement; preserve all other source text and placement."""
import re, json, shutil
from pathlib import Path
import pcbnew as p
from kicad_edit import parse, children, child, uq

ROOT=Path(__file__).resolve().parents[1]
HW=ROOT/'hardware'
OUT=HW/'verification/sw3-evpaw'
BACK=HW/'backups/pre-sw3-evpaw-20260917'
NAME='SW_SPST_Panasonic_EVPAW_3x2mm_H0.6mm'
DS='https://industrial.panasonic.com/cdbs/www-data/pdf/ATK0000/ATK0000C364.pdf'
NOTES='Outward-facing top-push SW3; EVPAWBD4A, 1.6 N, 0.6 mm height. Momentary TS/MR wake/ship function unchanged. 0.1 mm stencil, 80% paste area. Keep central 1.9 x 2 mm underside free of exposed copper and vias; flexible cover fit remains pending.'

def block(text, keyword, ref):
    for m in re.finditer(r'\('+keyword+r'\s', text):
        depth=0; quoted=False; escape=False
        for end in range(m.start(),len(text)):
            c=text[end]
            if quoted:
                if escape: escape=False
                elif c=='\\': escape=True
                elif c=='"': quoted=False
            elif c=='"': quoted=True
            elif c=='(': depth+=1
            elif c==')':
                depth-=1
                if depth==0: break
        s=text[m.start():end+1]
        if f'(property "Reference" "{ref}"' in s:
            return m.start(),end+1,s
    raise ValueError(ref)

def prop(s,key,value):
    pat=r'(\(property "'+re.escape(key)+r'" )"(?:\\.|[^"\\])*"'
    s,n=re.subn(pat,lambda m:m[1]+json.dumps(value),s,count=1)
    assert n==1,key
    return s

BACK.mkdir(exist_ok=True)
for name in ['main.kicad_pcb','power.kicad_sch']:
    if (BACK/name).exists():
        assert (BACK/name).read_bytes()==(HW/'main'/name).read_bytes(), 'Source changed since backup'
    else: shutil.copy2(HW/'main'/name,BACK/name)
boardfile=HW/'main/main.kicad_pcb'
original=boardfile.read_text(encoding='utf-8')
b=p.LoadBoard(str(boardfile))
old=next(f for f in b.GetFootprints() if f.GetReference()=='SW3')
nets={x.GetNumber():x.GetNet() for x in old.Pads()}
new=p.FootprintLoad(str(HW/'HapticBracelet.pretty'),NAME)
b.Add(new)
new.SetFPID(p.LIB_ID('HapticBracelet',NAME))
new.SetReference('SW3'); new.SetValue(old.GetValue())
new.SetPath(old.GetPath()); old_uuid=old.m_Uuid.AsString()
new.SetPosition(old.GetPosition())
new.Flip(new.GetPosition(),p.FLIP_DIRECTION_LEFT_RIGHT)
new.SetOrientationDegrees(old.GetOrientationDegrees())
new.Reference().SetVisible(False)
new.SetField('MPN','EVPAWBD4A'); new.SetField('Manufacturer','Panasonic')
new.SetField('Datasheet',DS); new.SetField('BOM Comments',NOTES)
for key in ['MPN','Manufacturer','BOM Comments']:
    new.GetField(key).SetVisible(False)
    new.GetField(key).SetLayer(p.B_Fab)
    new.GetField(key).SetMirrored(True)
for pad in new.Pads(): pad.SetNet(nets[pad.GetNumber()])
b.Remove(old)
p.SaveBoard(str(OUT/'candidate.kicad_pcb'),b)
candidate=(OUT/'candidate.kicad_pcb').read_text(encoding='utf-8')
start,end,_=block(original,'footprint','SW3')
_,_,replacement=block(candidate,'footprint','SW3')
replacement=re.sub(r'\(uuid "[^"]+"\)', '(uuid "'+old_uuid+'")',replacement,count=1)
boardfile.write_text(original[:start]+replacement+original[end:],encoding='utf-8')

sf=HW/'main/power.kicad_sch'; original_s=sf.read_text(encoding='utf-8')
start,end,s=block(original_s,'symbol','SW3')
for k,v in [('Footprint','HapticBracelet:'+NAME),('MPN','EVPAWBD4A'),('Manufacturer','Panasonic'),('Datasheet',DS),('BOM Comments',NOTES)]:s=prop(s,k,v)
sf.write_text(original_s[:start]+s+original_s[end:],encoding='utf-8')

# Exact preservation of every other top-level PCB item and all circuit nodes.
before=parse((BACK/'main.kicad_pcb').read_text(encoding='utf-8'))
after=parse(boardfile.read_text(encoding='utf-8'))
def without_sw3(a):
    return [x for x in a if not (isinstance(x,list) and x[0]=='footprint' and any(uq(z[1])=='Reference' and uq(z[2])=='SW3' for z in children(x,'property')))]
assert without_sw3(before)==without_sw3(after)
verified=p.LoadBoard(str(boardfile)); f=next(f for f in verified.GetFootprints() if f.GetReference()=='SW3')
assert f.GetLayer()==p.B_Cu
assert {x.GetNumber():x.GetNetname() for x in f.Pads()}=={'1':'/Charger and regulated supply/TS_MR','2':'GND'}
report={'other_pcb_items_preserved':True,'reference':'SW3','mpn':'EVPAWBD4A','layer':f.GetLayerName(),'position_mm':[p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y)],'pads':[{ 'number':x.GetNumber(),'net':x.GetNetname(),'size_mm':[p.ToMM(x.GetSize().x),p.ToMM(x.GetSize().y)]} for x in f.Pads()]}
(OUT/'checks.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
