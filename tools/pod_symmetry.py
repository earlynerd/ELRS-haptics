"""One-time main-pod interface cleanup; preserve current placement and identities."""
import copy, sys, xml.etree.ElementTree as E
from kicad_edit import *
from readable_schematic import Drawing, props

BACK = HW/'backups/before-pod-symmetry'
REMOVED = {'J3','R48','R50','R52'}
NEW = {'R62': (48,87)}

def renew(z):
    if not isinstance(z,list): return
    if z[0]=='uuid': z[1]=q(uid())
    for v in z: renew(v)

def schematic():
    path=HW/'main/power.kicad_sch'
    assert path.read_bytes()==(BACK/'main'/path.name).read_bytes(), 'Source changed since backup'
    a=load(path)
    byref={props(s)['Reference']:s for s in children(a,'symbol')}
    pathid=child(child(child(byref['U11'],'instances'),'project'),'path')[1]
    d=Drawing(path,path,'main',uq(pathid),'Charger and buck-boost supply')
    r=copy.deepcopy(byref['R37']);renew(r)
    for p in children(r,'property'):
        if uq(p[1])=='Reference':p[2]=q('R62')
    d.old['R62']=r
    for ref in ['J3','#PWR16249','#PWR16250','#PWR16251','SW3','#PWR16248']:
        a.remove(byref[ref])
    # Replace only the J3 / button branch; keep charger and regulator drawing intact.
    oldwires={
        ((116.84,93.98),(134.62,93.98)),((134.62,93.98),(134.62,132.08)),
        ((134.62,132.08),(144.78,132.08)),((144.78,121.92),(144.78,116.84)),
        ((187.96,109.22),(182.88,109.22)),((187.96,111.76),(182.88,111.76)),
        ((187.96,116.84),(182.88,116.84)),((187.96,114.3),(175.26,114.3)),
        ((175.26,114.3),(175.26,93.98)),((175.26,93.98),(116.84,93.98))}
    for w in children(a,'wire'):
        ends=tuple(tuple(map(float,p[1:])) for p in children(child(w,'pts'),'xy'))
        if ends in oldwires:a.remove(w);oldwires.remove(ends)
    assert not oldwires,oldwires
    d.inst('SW3',144.78,119.38,270)
    for p in children(d.instances['SW3'],'property'):
        if uq(p[1]) in ['Reference','Value']:
            child(p,'at')[1:]=['148.59','118.11' if uq(p[1])=='Reference' else '120.65','90']
    d.inst('R62',160.02,119.38)
    d.label('TS_MR',(134.62,93.98))
    d.wire((116.84,93.98),(134.62,93.98),(134.62,114.3),(144.78,114.3),(160.02,114.3),(160.02,115.57))
    d.wire((144.78,124.46),(144.78,132.08),(160.02,132.08),(160.02,123.19))
    d.dot((144.78,114.3));d.dot((144.78,132.08))
    # Reuse the existing ground symbol UUID and reference.
    g=copy.deepcopy(byref['#PWR16248']);dy=132.08-116.84
    child(g,'at')[2]='132.08'
    for p in children(g,'property'):
        pos=child(p,'at');pos[2]=str(round(float(pos[2])+dy,4))
    a.append(g)
    for z in d.a:
        if isinstance(z,list) and z[0] in ['symbol','wire','junction','label']:a.append(z)
    for t in children(a,'text'):
        if 'J3 includes' in uq(t[1]):
            t[1]=q('C34: IN bypass    C35: SYS reservoir    C36: BAT bypass\nSW3: wake/ship button. R62: fixed TS/MR termination.\nCell and NTC use J200/J103 on the local pod sheet, as on satellites.\nFirmware checks every pod temperature before enabling charge.')
    save(path,a)

    path=HW/'main/controller-support.kicad_sch'
    assert path.read_bytes()==(BACK/'main'/path.name).read_bytes(), 'Source changed since backup'
    a=load(path)
    for s in children(a,'symbol'):
        if props(s)['Reference'] in {'R48','R50','R52','#PWR30018'}:a.remove(s)
    count=0
    for w in children(a,'wire'):
        pts=[tuple(map(float,p[1:])) for p in children(child(w,'pts'),'xy')]
        # The eight pull-up branch wires occupy this otherwise empty region.
        if all(170<=x<=191 and 124<=y<=173 for x,y in pts):a.remove(w);count+=1
    assert count==8,count
    for j in children(a,'junction'):
        x,y=map(float,child(j,'at')[1:])
        if 170<=x<=191 and 124<=y<=173:a.remove(j)
    for t in children(a,'text'):
        if 'Pullups keep all colours' in uq(t[1]):
            t[1]=q('GPIO low lights a colour; high or high-impedance turns it off.\nGPIO4/5 SDIO straps unused; GPIO15 ignored with default JTAG eFuses.\nFirmware assigns charging, connection and fault indications.')
    save(path,a)
    print('Schematics: removed J3 and LED pull-ups; added R62 with SW3 in parallel.')

def pcb():
    path=HW/'main/main.kicad_pcb'
    assert path.read_bytes()==(BACK/'main'/path.name).read_bytes(), 'PCB changed since backup'
    a=load(path);before=copy.deepcopy(a)
    root=E.parse(HW/'verification/project-split/main.xml').getroot()
    comps={c.attrib['ref']:c for c in root.findall('components/comp')}
    nodes={(x.attrib['ref'],x.attrib['pin']):n.attrib['name'].replace('/','{slash}') if n.attrib['name'].startswith('unconnected-') else n.attrib['name'] for n in root.findall('nets/net') for x in n.findall('node')}
    sample=copy.deepcopy(next(f for f in children(a,'footprint') if props(f)['Reference']=='R37'))
    for f in children(a,'footprint'):
        ref=props(f)['Reference']
        if ref in REMOVED:a.remove(f);continue
        for pad in children(f,'pad'):
            if children(pad,'net'):child(pad,'net')[1]=q(nodes.get((ref,uq(pad[1])),''))
    f=sample;renew(f);oldangle=float(child(f,'at')[3]) if len(child(f,'at'))>3 else 0
    child(f,'at')[1:]=['48','87','0']
    for z in children(f,'pad')+children(f,'property'):
        at=child(z,'at')
        if len(at)>3:at[3]=str((float(at[3])-oldangle)%360)
    for p in children(f,'property'):
        if uq(p[1])=='Reference':p[2]=q('R62')
    c=comps['R62'];child(f,'path')[1]=q(c.find('sheetpath').attrib['tstamps']+c.findtext('tstamps'))
    for pad in children(f,'pad'):child(pad,'net')[1]=q(nodes[('R62',uq(pad[1]))])
    a.append(f)
    old={props(f)['Reference']:f for f in children(before,'footprint')}
    for f in children(a,'footprint'):
        ref=props(f)['Reference']
        if ref=='R62':continue
        assert child(f,'at')==child(old[ref],'at'),ref
    save(path,a)
    print('PCB: retained placements unchanged; R62 occupies part of former J3 area.')

if __name__=='__main__':
    {'schematic':schematic,'pcb':pcb}[sys.argv[1]]()
