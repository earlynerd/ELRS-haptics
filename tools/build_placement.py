"""Create the first unrouted native placement from schematic nets; KiCad Python.

Explicitly rerunning replaces PCB placement. Backups preserve the prior revision.
"""
from pathlib import Path
if (Path(__file__).resolve().parents[1]/'hardware/verification/routing/board-migration.json').exists():
    raise SystemExit('Historical 0.6 generator disabled: the native PCB has advanced to four-layer routing. Edit the current board instead.')
import shutil, json, math, re, xml.etree.ElementTree as ET
import pcbnew as p
from kicad_edit import load,save,children,child,q,uq,parse
ROOT=Path(__file__).resolve().parents[1]; HW=ROOT/'hardware'
LIB=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
CUSTOM=HW/'HapticBracelet.pretty'
BACK=HW/'backups/before-placement'
if not BACK.exists():
    BACK.mkdir(parents=True)
    for f in HW.glob('*.kicad_*'):shutil.copy2(f,BACK/f.name)
    shutil.copytree(CUSTOM,BACK/CUSTOM.name)
def rect(a,b,layer='F.CrtYd',width=.05):
    return f'(fp_rect (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width {width}) (type default)) (fill none) (layer "{layer}"))'
def makefp(name,pads,w,h,descr):
    s=f'(footprint "{name}" (version 20241229) (generator "pcbnew") (layer "F.Cu") (descr {q(descr)}) (attr smd)'
    for prop,val,y,layer in [('Reference','REF**',-h/2-.8,'F.SilkS'),('Value',name,h/2+.8,'F.Fab')]:
        s+=f'(property "{prop}" "{val}" (at 0 {y} 0) (layer "{layer}") (effects (font (size .7 .7) (thickness .1))))'
    s+=rect((-w/2,-h/2),(w/2,h/2),'F.Fab',.1)
    for num,x,y,sx,sy,shape,paste in pads:
        rr='(roundrect_rratio .15)' if shape=='roundrect' else ''
        s+=f'(pad "{num}" smd {shape} (at {x} {y}) (size {sx} {sy}) (layers "F.Cu" "F.Mask" '+('"F.Paste"' if paste else '')+f') {rr})'
    x0=min([-w/2]+[a[1]-a[3]/2 for a in pads])-.2;x1=max([w/2]+[a[1]+a[3]/2 for a in pads])+.2
    y0=min([-h/2]+[a[2]-a[4]/2 for a in pads])-.2;y1=max([h/2]+[a[2]+a[4]/2 for a in pads])+.2
    s+=rect((x0,y0),(x1,y1))+')'
    (CUSTOM/(name+'.kicad_mod')).write_text(s+'\n')
makefp('DRV2625_YFF_9_0.4mm',[(r+str(c),.4*(c-2),.4*(i-1),.225,.225,'circle',True) for i,r in enumerate('ABC') for c in [1,2,3]],1.498,1.361,'TI DRV2625 YFF0009, datasheet Rev C board land pattern page 73; 0.225 mm NSMD lands, 0.4 mm pitch.')
drvpath=CUSTOM/'DRV2625_YFF_9_0.4mm.kicad_mod'
drva=load(drvpath);drva.append(['solder_mask_margin','0.025']);save(drvpath,drva)
lrapath=CUSTOM/'Vybronics_VLV041235L_FPC_Contact_Draft.kicad_mod'
lraa=load(lrapath)
for x in children(lraa,'fp_text'):
    if children(x,'layer') and uq(child(x,'layer')[1])=='F.SilkS':child(x,'layer')[1]=q('F.Fab')
save(lrapath,lraa)
makefp('TPS63802_DLA0010A',[(str(i+1),-.9,-1+.5*i,.6,.25,'roundrect',True) for i in range(5)]+[(str(10-i),.55 if i==2 else .75,-1+.5*i,1.3 if i==2 else .9,.25,'roundrect',True) for i in range(5)],2,3,'TI TPS63802 DLA0010A example board layout; asymmetric pin 8 ground land. Datasheet package land drawing.')
for n,pitch,size in [(2,2,(1.4,1.6)),(4,1.5,(1,1.1)),(5,1.27,(.85,.9)),(6,2,(1.4,1.6))]:
    makefp(f'WirePads_{n}_P{pitch}mm',[(str(i+1),0,(i-(n-1)/2)*pitch,*size,'roundrect',False) for i in range(n)],size[0],(n-1)*pitch+size[1],'Hand solder wire / probe lands. No paste. Provide strain relief in enclosure; pin order from schematic.')
# Murata 2016 power-inductor body envelope; supplier land-pattern confirmation remains explicit.
makefp('L_DFE201612E_Placement', [('1',-.85,0,.9,1.8,'roundrect',True),('2',.85,0,.9,1.8,'roundrect',True)],2,1.6,'DFE201612E 2 x 1.6 mm body. Placement-only proposed lands: supplier land-pattern sign-off required before routing release.')
FP={
 'U11':'Package_DFN_QFN:Texas_DLH0010A_WSON-10-1EP_2.2x2mm_P0.4mm_EP0.9x1.5mm',
 'U12':'HapticBracelet:TPS63802_DLA0010A',
 'U13':'Package_DFN_QFN:Texas_X2QFN-12_1.6x1.6mm_P0.4mm',
 'J2':'Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal',
 'D1':'LED_SMD:LED_LiteOn_LTST-C19HE1WT',
 'SW3':'Button_Switch_SMD:Panasonic_EVQPUJ_EVQPUA',
 'SW1':'Button_Switch_SMD:SW_SPST_TL3305A','SW2':'Button_Switch_SMD:SW_SPST_TL3305A',
 'L1':'HapticBracelet:L_DFE201612E_Placement',
 'C3':'Capacitor_SMD:C_0805_2012Metric',
}
MPN={'J2':('USB4105-GF-A','GCT'),'D1':('LTST-C19HE1WT','Lite-On'),'SW3':('EVQPUJ02K','Panasonic'),'SW1':('TL3305AF160QG','E-Switch'),'SW2':('TL3305AF160QG','E-Switch'),'L1':('DFE201612E-R47M=P2','Murata')}
for i in range(8):
    FP[f'U{3+i}']='HapticBracelet:DRV2625_YFF_9_0.4mm'
    MPN[f'U{3+i}']=('DRV2625YFFR','Texas Instruments')
    FP[f'M{i+1}']='HapticBracelet:Vybronics_VLV041235L_FPC_Contact_Draft'
    MPN[f'M{i+1}']=('VLV041235L','Vybronics')
    FP[f'F{100+i}']='Resistor_SMD:R_0805_2012Metric'
    for j,n,pitch in [(100+4*i,6,2),(101+4*i,6,2),(102+4*i,5,1.27),(103+4*i,2,2),(200+i,2,2)]:
        FP[f'J{j}']=f'HapticBracelet:WirePads_{n}_P{pitch}mm'
FP['J1']='HapticBracelet:WirePads_6_P2mm';FP['J3']='HapticBracelet:WirePads_4_P1.5mm'
def prop(s,k,v):
    a=next((a for a in children(s,'property') if uq(a[1])==k),None)
    if a:a[2]=q(v)
    else:s.append(parse(f'(property {q(k)} {q(v)} (at 0 0 0) (effects (font (size 1 1)) (hide yes)))'))
for file in HW.glob('*.kicad_sch'):
    a=load(file); dirty=False
    for s in children(a,'symbol'):
        props={uq(x[1]):uq(x[2]) for x in children(s,'property')};ref=props.get('Reference')
        if ref in FP:prop(s,'Footprint',FP[ref]);dirty=True
        if ref in MPN:
            mpn,mfr=MPN[ref];prop(s,'MPN',mpn);prop(s,'Manufacturer',mfr)
            if ref.startswith('M') or ref in ['D1','J2']:prop(s,'Value',mpn)
            if ref in ['D1','J2']:prop(s,'BOM Comments','Physical pad numbering checked against manufacturer drawing; prototype placement selected.')
        if ref=='L1':prop(s,'BOM Comments','DFE201612E-R47M=P2 0.47uH, 5.5A saturation. Body fit established; proposed land geometry pending supplier land-pattern confirmation.')
        if ref and ref.startswith('F'):prop(s,'BOM Comments','0805 fuse provision only; fuse MPN/rating and clearance around cell leads remain to select.')
    if dirty:save(file,a)
table=load(HW/'fp-lib-table')
names={uq(child(x,'name')[1]) for x in children(table,'lib')}
for n in sorted(set(v.split(':')[0] for v in FP.values())-names):table.append(parse(f'(lib (name "{n}") (type "KiCad") (uri "${{KICAD10_FOOTPRINT_DIR}}/{n}.pretty") (options "") (descr ""))'))
save(HW/'fp-lib-table',table)
pro=json.loads((HW/'haptic-bracelet.kicad_pro').read_text())
pro['board']['design_settings']['rules']['min_copper_edge_clearance']=.25
(HW/'haptic-bracelet.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
if '--metadata-only' in __import__('sys').argv:
    print('Footprints and schematic properties updated; export netlist before generating placement.');raise SystemExit

root=ET.parse(HW/'verification/netlist.xml').getroot()
board=p.BOARD();board.GetDesignSettings().SetBoardThickness(p.FromMM(.8))
board.GetDesignSettings().m_CopperEdgeClearance=p.FromMM(.25)
board.GetTitleBlock().SetTitle('Haptic bracelet / first placement / UNROUTED')
board.GetTitleBlock().SetRevision('0.6')
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
nets={};node_nets={}
for n in root.findall('nets/net'):
    pcbname=re.sub(r'Pod (\d) / U(\d+)',r'Pod \1 {slash} U\2',n.attrib['name'])
    if pcbname.startswith('unconnected-'):pcbname=pcbname.replace('/','{slash}')
    net=p.NETINFO_ITEM(board,pcbname);board.Add(net);nets[n.attrib['name']]=net
    for x in n.findall('node'):node_nets[(x.attrib['ref'],x.attrib['pin'])]=net
fps={};groups={}; comps={c.attrib['ref']:c for c in root.findall('components/comp')}
for ref,c in comps.items():
    fpn=c.findtext('footprint');assert fpn,(ref,'missing footprint')
    lib,name=fpn.split(':');f=p.FootprintLoad(str(CUSTOM if lib=='HapticBracelet' else LIB/(lib+'.pretty')),name);assert f,(ref,fpn)
    f.SetFPID(p.LIB_ID(lib,name));f.SetReference(ref);f.SetValue(c.findtext('value'))
    f.SetField('Datasheet',c.findtext('datasheet') or '')
    f.SetField('Description',c.findtext("fields/field[@name='Description']") or '')
    f.SetDNP(ref in ['C29','C30'])
    path=p.KIID_PATH()
    # KiCad's root sheet UUID is included in board paths, although XML omits it.
    rootid=uq(child(load(HW/'haptic-bracelet.kicad_sch'),'uuid')[1])
    for ident in [rootid]+c.find('sheetpath').attrib['tstamps'].strip('/').split('/')+[c.findtext('tstamps')]:
        if ident:path.push_back(p.KIID(ident))
    f.SetPath(path)
    for field in c.findall('fields/field'):
        if field.text and field.attrib['name'] not in ['Footprint','Datasheet','Description']:
            pf=p.PCB_FIELD(f,p.FIELD_T_USER,field.attrib['name']);pf.SetText(field.text);pf.SetVisible(False);f.Add(pf)
    f.Reference().SetVisible(False);f.Value().SetVisible(False)
    if ref in [f'U{i}' for i in range(3,11)]:f.SetLocalClearance(p.FromMM(.15))
    for pad in f.Pads():
        num=pad.GetNumber()
        if num:
            # USB combined power contacts share one physical land.
            members=num.split('/')
            ns=[node_nets.get((ref,m)) for m in members]
            if len(members)>1:
                assert all(ns) and len({x.GetNetname() for x in ns})==1,(ref,num)
            elif not ns[0]:continue # explicit symbol NC without a named XML net
            pad.SetNet(ns[0])
    board.Add(f);fps[ref]=f
    sheet=c.find('sheetpath').attrib['names']; idx=0
    import re
    m=re.search(r'Pod (\d)',sheet)
    if m:idx=int(m.group(1))
    groups[ref]=idx

# Panel study has eight independent islands; tabs/rails are intentionally absent.
origins=[(35,35)]+[(75+28*((i-1)%4),48+48*((i-1)//4)) for i in range(1,8)]
specs=[]; occupied={i:[] for i in range(8)}; records={}
def line(x1,y1,x2,y2,layer=p.Edge_Cuts,width=.05):
    g=p.PCB_SHAPE();g.SetShape(p.SHAPE_T_SEGMENT);g.SetStart(v(x1,y1));g.SetEnd(v(x2,y2));g.SetLayer(layer);g.SetWidth(p.FromMM(width));board.Add(g)
def outline(points,layer=p.Edge_Cuts):
    for a,b in zip(points,points[1:]+points[:1]):line(*a,*b,layer)
for i,(ox,oy) in enumerate(origins):
    w,h=(21,61) if i==0 else (17,35);start=5.1 if i==0 else 0;cx=w/2-1;cy=h/2
    # Chamfers create simple closed native outlines, easy to edit and inspect.
    pts=[(.7,start),(w-.7,start),(w,start+.7),(w,h-.7),(w-.7,h),(.7,h),(0,h-.7),(0,start+.7)]
    outline([(ox+x,oy+y) for x,y in pts]);cut=(cx-3.5,cy-7.5,cx+3.5,cy+7.5)
    x0,y0,x1,y1=cut;r=.5
    outline([(ox+x,oy+y) for x,y in [(x0+r,y0),(x1-r,y0),(x1,y0+r),(x1,y1-r),(x1-r,y1),(x0+r,y1),(x0,y1-r),(x0,y0+r)]])
    specs.append({'pod':i,'origin':[ox,oy],'width':w,'height':h,'top_edge':start,'cutout':cut,'lra_center':[cx,cy],'shell':[w+3,h+3,10.5]})
    # Tail reserved along the lower right of the LRA; contact lands occupy this zone.
    occupied[i].append(('CUTOUT',(x0-.25,y0-.25,x1+.25,y1+.25)))
    occupied[i].append(('FLEX',(cx+3.6,cy+3,cx+9.2,cy+8.9)))
    outline([(ox+cx+3.6,oy+cy+3),(ox+cx+9.2,oy+cy+3),(ox+cx+9.2,oy+cy+8.9),(ox+cx+3.6,oy+cy+8.9)],p.Dwgs_User)
def bounds(f):
    pts=[]
    for g in f.GraphicalItems():
        if isinstance(g,p.PCB_SHAPE) and g.GetLayer() in [p.F_CrtYd,p.B_CrtYd]:
            b=g.GetBoundingBox();pts += [(p.ToMM(b.GetX()),p.ToMM(b.GetY())),(p.ToMM(b.GetRight()),p.ToMM(b.GetBottom()))]
    if not pts:
        for g in f.Pads():
            b=g.GetBoundingBox();pts += [(p.ToMM(b.GetX()),p.ToMM(b.GetY())),(p.ToMM(b.GetRight()),p.ToMM(b.GetBottom()))]
    return (min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts))
def intersects(a,b):return a[0]<b[2]-.001 and a[2]>b[0]+.001 and a[1]<b[3]-.001 and a[3]>b[1]+.001
bboxcache={}
def place(ref,x,y,angle=0,fixed=False,back=False):
    i=groups[ref];ox,oy=origins[i];f=fps[ref];key=(ref,angle,back)
    if key not in bboxcache:
        if f.IsFlipped()!=back:f.Flip(f.GetPosition(),False)
        f.SetOrientationDegrees(angle);f.SetPosition(v(0,0));bboxcache[key]=bounds(f)
    a=bboxcache[key];b=(a[0]+x,a[1]+y,a[2]+x,a[3]+y)
    # The antenna courtyard includes external free space. Only module body/pads consume board area.
    if ref=='U1':b=(x-6.85,y-5.6,x+6.85,y+5.85)
    allowed=['FLEX'] if ref.startswith('M') else []
    collisions=[r for r,a in occupied[i] if r not in allowed and (r in ['CUTOUT','FLEX'] or records[r]['side']==('B' if back else 'F')) and intersects(a,b)]
    s=specs[i];inside=b[0]>=.25 and b[2]<=s['width']-.25 and b[1]>=s['top_edge']+.05 and b[3]<=s['height']-.25
    if not fixed and (collisions or not inside):return False
    if collisions:raise AssertionError((ref,'fixed collision',collisions,b))
    if f.IsFlipped()!=back:f.Flip(f.GetPosition(),False)
    f.SetOrientationDegrees(angle);f.SetPosition(v(ox+x,oy+y))
    occupied[i].append((ref,b));records[ref]={'pod':i,'x':x,'y':y,'rotation':angle,'side':'B' if back else 'F','courtyard':b,'footprint':comps[ref].findtext('footprint')}
    return True
for i,s in enumerate(specs):
    cx,cy=s['lra_center'];w=s['width'];j=100+4*i;b=100+10*i
    place(f'M{i+1}',cx+7.78,cy+6,90,True)
    place(f'J{j}',1.45,cy-1,0,True);place(f'J{j+1}',w-1.45,cy-3.5,0,True)
    place(f'U{18+i}',cx,cy+12.5,0,True)
    if i:
        place(f'U{3+i}',8.4,6,0,True)
        place(f'C{5+3*i}',6.4,6,0,True)
        place(f'C{6+3*i}',8.4,4.5,0,True)
        place(f'C{7+3*i}',10.4,6,0,True)
        place(f'C{b}',12.6,27.3,0,True)
        place(f'C{b+1}',14.3,29.1,0,True)
        place(f'C{b+3}',14.3,32.3,0,True)
        place(f'J{j+2}',8.5,1.7,90,True)
        place(f'J{200+i}',2.0,4.5,0,True)
        place(f'J{j+3}',14.5,4.5,0,True)
        place(f'F{100+i}',3,8,0,True)
    else:
        place('U1',10.5,10.7,0,True)
        place('J2',10.5,58.7,0,True)
        place('SW3',18.5,48.5,-90,True)
        place('D1',18.6,58.5,0,True)
        # Service buttons are packed into the remaining accessible board area.
        place('U3',4.1,23.3,0,True)
        place('U12',4.0,48.5,0,True);place('L1',7.2,48.5,0,True)
        place('U11',10.6,49.8,0,True)

# Place remaining components within native courtyard envelopes, prioritizing large parts.
# This is a packing/fit pass. Routing will refine decoupler placement and power-loop geometry.
def area(ref):
    f=fps[ref];f.SetPosition(v(0,0));f.SetOrientationDegrees(0);b=bounds(f);return (b[2]-b[0])*(b[3]-b[1])
remaining=sorted([r for r in fps if r not in records],key=lambda r:(-area(r),r))
for ref in remaining:
    i=groups[ref];s=specs[i];w,h=s['width'],s['height']
    # The preferred target comes from the centroid of already-placed connected components.
    neighbors=set()
    for pad in fps[ref].Pads():
        net=pad.GetNetname()
        if net in ['GND','3V3','VBAT','POD_3V3'] or net.startswith('unconnected'):continue
        for r in records:
            if groups[r]==i and any(x.GetNetname()==net for x in fps[r].Pads()):neighbors.add(r)
    target=(sum(records[r]['x'] for r in neighbors)/len(neighbors),sum(records[r]['y'] for r in neighbors)/len(neighbors)) if neighbors else (w/2,h*.55)
    candidates=[(x/4,y/4) for x in range(3,int(w*4)-2) for y in range(int((s['top_edge']+.5)*4),int(h*4)-2)]
    candidates.sort(key=lambda xy:(xy[0]-target[0])**2+(xy[1]-target[1])**2)
    ok=False
    for x,y in candidates:
        for angle in [0,90]:
            if place(ref,x,y,angle):ok=True;break
        if ok:break
    if not ok and ref.startswith(('R','C')) and '0402' in comps[ref].findtext('footprint'):
        for x,y in candidates:
            for angle in [0,90]:
                if place(ref,x,y,angle,back=True):ok=True;break
            if ok:break
    if not ok:raise RuntimeError(('no room',ref,i))

pcb=HW/'haptic-bracelet.kicad_pcb';p.SaveBoard(str(pcb),board)
out=HW/'verification/placement';out.mkdir(parents=True,exist_ok=True)
(out/'placement.json').write_text(json.dumps({'revision':'0.6','board_thickness':.8,'routed':False,'pods':specs,'components':records,'limits':['Courtyard packing, not routing closure','LRA flex bending and height need sample fit','Inductor land pattern and fuse MPN not released','No fabrication panel tabs or rails']},indent=2)+'\n')
print(f'Saved {len(fps)} footprints on 8 islands; {len(nets)} nets; no tracks. Native courtyard packing passed.')






