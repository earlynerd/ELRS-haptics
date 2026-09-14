"""One-time migration to eight externally protected batteries and pod bulk caps."""
from kicad_edit import *
import shutil

backup=HW/'backups/before-protected-cells'
assert not backup.exists(), 'Migration already run; edit native files instead.'
backup.mkdir()
for p in HW.glob('*.kicad_sch'): shutil.copy2(p,backup/p.name)
shutil.copy2(HW/'verification/netlist.xml',backup/'netlist.xml')

def props(s): return {uq(p[1]):uq(p[2]) for p in children(s,'property')}
def prop(s,k,v):
    found=[p for p in children(s,'property') if uq(p[1])==k]
    if found: found[0][2]=q(v)
    else: s.append(parse(f'(property {q(k)} {q(v)} (at 0 0 0) {fx(hide=True)})'))
def walk(a):
    # Labels and embedded text share one deliberate net rename.
    for i,x in enumerate(a):
        if isinstance(x,list): walk(x)
        elif isinstance(x,str) and x.startswith('"'):
            a[i]=q(uq(x).replace('VBAT_RAW','VBAT').replace('BAT_PROTECTED','VBAT'))

for p in HW.glob('*.kicad_sch'):
    if p.name=='protection.kicad_sch': continue
    sh=Sheet(p.name)
    walk(sh.a)
    for sheet in list(children(sh.a,'sheet')):
        if props(sheet).get('Sheetfile')=='protection.kicad_sch':sh.a.remove(sheet)
    tb=child(sh.a,'title_block'); child(tb,'rev')[1]=q('0.5'); child(tb,'date')[1]=q('2026-09-12')
    if p.name.startswith('pod_'):
        i=int(p.stem.split('_')[1]); b=100+10*i
        m=next(s for s in children(sh.a,'symbol') if props(s).get('Reference')==f'U{18+i}')
        sh.path=uq(child(child(child(m,'instances'),'project'),'path')[1])
        for s in children(sh.a,'symbol'):
            ref=props(s).get('Reference')
            if ref==f'J{200+i}':
                prop(s,'Value','PROTECTED CELL 90mAh')
                prop(s,'BOM Comments','One YDL301230-class protected 3 x 12 x 32 mm battery per pod. Pin 1 PACK+, pin 2 PACK-. Keep factory PCM intact; never bypass to raw cell terminals. Battery assembly is off-board; connector/pad footprint TBD.')
                prop(s,'Battery_Model','YDL301230 (protected assembly example)')
                prop(s,'Battery_Capacity','90 mAh nominal')
                prop(s,'Battery_Envelope','3 x 12 x 32 mm; leads outside body')
                prop(s,'Datasheet','https://ydlbattery.com/cdn/shop/files/YDL-301230-90mAh-specification.pdf?v=17344537468879431347')
            if ref==f'F{100+i}': prop(s,'BOM Comments','Retain positive branch fuse next to protected battery output. Rating pending wire, PCM and measured load coordination.')
        C=stock('Device','C')
        sh.passive(C,f'C{b+3}','22u 10V X5R',147.32,195.58,'POD_3V3','GND',('POD_3V3','GND'),
                   footprint='Capacitor_SMD:C_0805_2012Metric',notes='Additional local bulk on switched rail, near driver supply and pod power entry. 22 uF nominal; effective capacitance at 3.3 V depends on selected MPN/DC bias. Retain existing bypass caps.')
        for t in children(sh.a,'text'):
            if uq(t[1]).startswith('MCU bypass'):
                t[1]=q('Local bypass + 10u existing + 22u added bulk.\nVBAT stays live when POD_3V3 is OFF.\nOne protected 90mAh battery per pod; retain branch fuse.\nJ200-J207: PACK+ / PACK- only; factory PCM remains intact.')
    if p.name=='power.kicad_sch':
        u=next(s for s in children(sh.a,'symbol') if props(s).get('Reference')=='U11')
        sh.path=uq(child(child(child(u,'instances'),'project'),'path')[1])
        for s in children(sh.a,'symbol'):
            if props(s).get('Reference')=='J3':prop(s,'Value','VBAT BUS + NTC')
        for t in children(sh.a,'text'):
            if uq(t[1]).startswith('PACK PROTECTION'):
                t[1]=q('EIGHT PROTECTED BATTERIES / 1S8P\nFactory PCM stays on every battery. No central protector.\nEach PACK+ -> local fuse -> VBAT; PACK- -> GND.\nVBAT connects directly to U11 BAT and stays live in ship mode.\n720mAh nominal; 360mA continuous total with equal sharing.')
        FLAG=stock('power','PWR_FLAG')
        sh.connected(FLAG,'#FLG08',289.56,238.76,{'1':'VBAT'},('VBAT',))
        sh.text('22u additional bulk on each POD_3V3 branch.\nC42 = 4.7n: slower controlled pod-rail startup.\nBattery protection is external to these PCBs.',243.84,256.54,1.0)
    if p.name=='haptic-bracelet.kicad_sch':
        for s in children(sh.a,'symbol'):
            if props(s).get('Reference')=='C42':
                prop(s,'Value','4.7n 25V')
                prop(s,'BOM Comments','TPS22918 CT ramp control; increased for eight additional 22 uF pod capacitors. About 8.65 ms typical 10-90% rise at 3.308 V; hold reset until settled.')
    if p.name=='haptics.kicad_sch':
        for t in children(sh.a,'text'):
            t[1]=q(uq(t[1]).replace('each fitted cell retains its local positive fuse.','each pod has a protected battery and local positive fuse.'))
    sh.save()
# Archive the retired child, rather than leaving an apparently active orphan sheet.
(HW/'protection.kicad_sch').unlink() # exact file, backed up above
print('Migrated native schematics; previous revision saved at',backup)
