"""Extract two PCB masters, preserving the saved user's placement and routing.

Run only against the immutable before-two-projects snapshot. Net names and
schematic UUID paths come from fresh XML exports of the two new projects.
"""
import sys,copy,re
import xml.etree.ElementTree as ET
from redraw_projects import ARCH,HW,MAIN,SAT,VERIFY,SATREF,load,save,child,children,uq,q,parse,props

def escaped(s):return s.replace('/','{slash}') if s.startswith('unconnected-') else s

def split(name):
    sat=name=='satellite';folder=SAT if sat else MAIN
    root=ET.parse(VERIFY/(name+'.xml')).getroot()
    comps={c.attrib['ref']:c for c in root.findall('components/comp')}
    nodes={(n.attrib['ref'],n.attrib['pin']):escaped(net.attrib['name']) for net in root.findall('nets/net') for n in net.findall('node')}
    a=load(ARCH/'haptic-bracelet.kicad_pcb');rename=SATREF if sat else {}
    ox,oy,w,h=(103,96,17,35) if sat else (35,35,21,61)
    def inside(x):
        xx,yy=map(float,x[1:3]);return ox-.01<=xx<=ox+w+.01 and oy-.01<=yy<=oy+h+.01
    for typ,field in [('footprint','at'),('segment','start'),('via','at'),('gr_line','start')]:
        for item in children(a,typ):
            if not inside(child(item,field)):a.remove(item)
    for z in children(a,'zone'):
        if not inside(child(child(z,'polygon'),'pts')[1]):a.remove(z)
    nets={}
    for f in children(a,'footprint'):
        oldref=props(f)['Reference'];ref=rename.get(oldref,oldref);comp=comps[ref]
        for pp in children(f,'property'):
            if uq(pp[1])=='Reference':pp[2]=q(ref)
        path=comp.find('sheetpath').attrib['tstamps']+comp.findtext('tstamps')
        child(f,'path')[1]=q(path)
        for pad in children(f,'pad'):
            num=uq(pad[1]);nn=nodes.get((ref,num),'')
            if children(pad,'net'):
                old=uq(child(pad,'net')[1]);child(pad,'net')[1]=q(nn)
                if old!='RING_RETURN' or not sat:
                    assert old not in nets or nets[old]==nn,(ref,num,old,nn,nets.get(old));nets[old]=nn
    if sat:
        # Split the physical return at the open bottom bay. Incoming half
        # keeps the left run; the outgoing half keeps the right run.
        up=nodes[('J1','6')];down=nodes[('J2','6')]
    for typ in ['segment','via','zone']:
        for t in children(a,typ):
            if not children(t,'net'):continue
            old=uq(child(t,'net')[1])
            if sat and old=='RING_RETURN':
                if typ=='segment':
                    p1,p2=child(t,'start'),child(t,'end')
                    if abs(float(p1[2])-124.35)<.001 and abs(float(p2[2])-124.35)<.001:
                        a.remove(t);continue
                    nn=up if (float(p1[1])+float(p2[1]))/2<113 else down
                else:nn=up if float(child(t,'at')[1])<113 else down
            else:nn=nets[old]
            child(t,'net')[1]=q(nn)
            if not sat and typ=='segment' and float(child(t,'width')[1])<.1524:child(t,'width')[1]='0.1524'
    if children(a,'title_block'):
        title=child(a,'title_block')
        if children(title,'title'):child(title,'title')[1]=q('Haptic bracelet / '+name+' PCBA')
    if sat:
        # No new populated part: this is the stock copper net-tie selector.
        comp=comps['JP1'];fp=load('C:/Program Files/KiCad/10.0/share/kicad/footprints/Jumper.pretty/SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm.kicad_mod')
        fp[1]=q('Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm')
        fp.append(parse('(at 113.5 126.8)'))
        fp.append(['path',q(comp.find('sheetpath').attrib['tstamps']+comp.findtext('tstamps'))])
        for pp in children(fp,'property'):
            if uq(pp[1])=='Reference':pp[2]=q('JP1');child(pp,'at')[1:3]=['0','-1.7']
            if uq(pp[1])=='Value':pp[2]=q(comp.findtext('value'));pp.append(['hide','yes'])
        for pad in children(fp,'pad'):pad.append(['net',q(nodes[('JP1',uq(pad[1]))])])
        a.append(fp)
    save(folder/(name+'.kicad_pcb'),a)
    print(name,'footprints',len(children(a,'footprint')),'tracks',len(children(a,'segment')),'vias',len(children(a,'via')))

if __name__=='__main__':
    if '--replace-from-snapshot' not in sys.argv:
        raise SystemExit('Historical migration only. Explicit --replace-from-snapshot is required to discard subsequent PCB edits.')
    split(sys.argv[1])
