"""Helpers for explicit, wired circuit drawings while retaining source identities."""
import copy,math,json,xml.etree.ElementTree as E
from kicad_edit import *
ARCH=HW/'backups/before-two-projects'
BASE=E.parse(HW/'verification/routing-v09/netlist.xml').getroot()
PIN_NET={(n.attrib['ref'],n.attrib['pin']):net.attrib['name'] for net in BASE.findall('nets/net') for n in net.findall('node')}
def props(s):return {uq(p[1]):uq(p[2]) for p in children(s,'property')}
def nice(net):
    return {'3V3':'+3V3','POD_3V3':'+3V3_POD'}.get(net,net.split('/')[-1])
class Drawing:
    def __init__(self,source,dest,project,path,title,renames=None):
        old=load(ARCH/source);self.old={props(s)['Reference']:s for s in children(old,'symbol')};self.libs={uq(s[1]):s for s in children(child(old,'lib_symbols'),'symbol')}
        self.a=copy.deepcopy(old)
        for k in ['symbol','wire','junction','label','global_label','hierarchical_label','no_connect','text','text_box','sheet','polyline']:
            for x in children(self.a,k):self.a.remove(x)
        child(self.a,'lib_symbols')[1:]=[]
        self.dest=dest;self.project=project;self.path=path;self.rename=renames or {};self.pins={};self.used=set();self.instances={};self.nodes={};self.junctions=set();self.serial={'satellite':5000}.get(project,1000+sum(map(ord,dest.name))*10)
        if children(self.a,'title_block'):
            t=child(self.a,'title_block');child(t,'title')[1]=q(title);child(t,'rev')[1]=q('1.0');child(t,'date')[1]=q('2026-09-13')
        else:self.a.append(parse(f'(title_block (title {q(title)}) (date "2026-09-13") (rev "1.0"))'))
    def add(self,s):self.a.append(parse(s))
    def text(self,t,x,y,size=1.5):self.add(f'(text {q(t)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left top)) (uuid {uid()}))')
    def inst(self,ref,x,y,angle=0,mirror=None):
        s=copy.deepcopy(self.old[ref]);libid=uq(child(s,'lib_id')[1]);lib=self.libs[libid]
        embed=child(self.a,'lib_symbols')
        if not any(z[1]==q(libid) for z in children(embed,'symbol')):embed.append(copy.deepcopy(lib))
        child(s,'at')[1:]=[str(x),str(y),str(angle)]
        for k in ['mirror','instances']:
            for z in children(s,k):s.remove(z)
        if mirror:s.append(['mirror',mirror])
        newref=self.rename.get(ref,ref)
        for z in children(s,'property'):
            key=uq(z[1]);
            if key=='Reference':z[2]=q(newref)
            if key in ['Reference','Value']:
                dx,dy=(3.0,-1.27 if key=='Reference' else 1.27) if libid in ['Device:R','Device:C','Device:Fuse'] and angle==0 else (-2.54,-5.08 if key=='Reference' else -2.54)
                if libid not in ['Device:R','Device:C','Device:L','Device:Fuse']:
                    xs=[];ys=[]
                    for sub in children(lib,'symbol'):
                        for p in children(sub,'pin'):xs.append(float(child(p,'at')[1]));ys.append(float(child(p,'at')[2]))
                    dx=-max(xs or [3])+2.54;dy=-max(ys or [3])-5.08+(2.54 if key=='Value' else 0)
                if libid.startswith('Connector_Generic:') and angle==180:dx=0;dy=-10.16+(2.54 if key=='Value' else 0)
                if 'TPD2EUSB30' in libid or libid=='Device:LED_RGBA':dy-=7.62
                child(z,'at')[1:]=[str(round(x+dx,4)),str(round(y+dy,4)),str(angle%180)]
                effects=child(z,'effects')
                for h in children(effects,'hide'):effects.remove(h)
                for j in children(effects,'justify'):effects.remove(j)
                if not (libid.startswith('Connector_Generic:') and angle==180):effects.append(['justify','left'])
                child(child(effects,'font'),'size')[1:]=['1.0','1.0']
        s.append(parse(f'(instances (project {q(self.project)} (path {q(self.path)} (reference {q(newref)}) (unit 1))))'))
        self.a.append(s);self.instances[ref]=s
        rad=math.radians(angle)
        for sub in children(lib,'symbol'):
            for pin in children(sub,'pin'):
                at=child(pin,'at');px,py=map(float,at[1:3]);num=uq(child(pin,'number')[1]);ang=int(at[3])
                if mirror=='y':px=-px;ang=(180-ang)%360
                if mirror=='x':py=-py;ang=(-ang)%360
                self.pins[(ref,num)]=(round(x+px*math.cos(rad)-py*math.sin(rad),4),round(y-px*math.sin(rad)-py*math.cos(rad),4));self.nodes[(ref,num)]=(ang+angle)%360
        return s
    def pt(self,ref,num):return self.pins[(ref,str(num))]
    def wire(self,*points):
        for a,b in zip(points,points[1:]):
            if a==b:continue
            assert a[0]==b[0] or a[1]==b[1],('Non orthogonal wire',a,b)
            self.add(f'(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) (stroke (width 0) (type default)) (uuid {uid()}))')
        self.used.update(k for k,p in self.pins.items() if p in points)
    def join(self,*nodes,via=()):
        pts=[self.pt(*n) for n in nodes];self.wire(pts[0],*via,*pts[1:]);self.used.update(nodes)
    def dot(self,pt):
        if pt not in self.junctions:self.add(f'(junction (at {pt[0]} {pt[1]}) (diameter 0) (color 0 0 0 0) (uuid {uid()}))');self.junctions.add(pt)
    def label(self,name,pt,global_=False,angle=0):
        kind='global_label' if global_ else 'label';shape='(shape bidirectional)' if global_ else ''
        self.add(f'({kind} {q(name)} {shape} (at {pt[0]} {pt[1]} {angle}) (effects (font (size 1 1)) (justify {"right" if angle==180 else "left"} bottom)) (uuid {uid()}))')
    def power(self,name,pt):
        # Power symbols intentionally carry global rail names; signal labels stay at block boundaries.
        key='power:'+('PWR_FLAG' if name=='PWR_FLAG' else 'GND' if name=='GND' else '+3V3')
        if key not in symbols:stock('power',key.split(':')[1])
        lib=copy.deepcopy(symbols[key]);lib[1]=q(key)
        embed=child(self.a,'lib_symbols')
        if not any(z[1]==q(key) for z in children(embed,'symbol')):embed.append(lib)
        self.serial+=1;ref=f'#PWR{self.serial:03d}';x,y=pt
        self.add(f'(symbol (lib_id {q(key)}) (at {x} {y} 0) (unit 1) (in_bom no) (on_board yes) (dnp no) (uuid {uid()}) (property "Reference" {q(ref)} (at {x} {y} 0) (effects (font (size 1 1)) (hide yes))) (property "Value" {q(name)} (at {x} {y+(3.81 if name=="GND" else -3.81)} 0) (effects (font (size 1 1)))) (instances (project {q(self.project)} (path {q(self.path)} (reference {q(ref)}) (unit 1)))))')
        if name=='PWR_FLAG':
            for pp in children(children(self.a,'symbol')[-1],'property'):
                if uq(pp[1])=='Value':child(pp,'effects').append(['hide','yes'])
    def term(self,ref,num,name=None,power=False,length=5.08,global_=False):
        k=(ref,str(num));pt=self.pins[k];ang=self.nodes[k];dx,dy={0:(-length,0),180:(length,0),90:(0,length),270:(0,-length)}[ang]
        end=(round(pt[0]+dx,4),round(pt[1]+dy,4));self.wire(pt,end);self.used.add(k)
        name=name or nice(PIN_NET[k]);self.power(name,end) if power else self.label(name,end,global_,180 if ang==0 else 0)
    def nc(self,k):
        pt=self.pins[k];self.add(f'(no_connect (at {pt[0]} {pt[1]}) (uuid {uid()}))');self.used.add(k)
    def finish(self,globals=()):
        for k in self.pins:
            if k in self.used:continue
            net=PIN_NET.get(k,'')
            if not net or net.startswith('unconnected-'):self.nc(k)
            else:
                name=nice(net);self.term(*k,name,power=name in ['GND','+3V3','+3V3_POD','VBAT'],global_=name in globals)
        save(self.dest,self.a)
    def rail(self,name,nodes,y):
        pts=[self.pt(*n) for n in nodes];xs=sorted(set(p[0] for p in pts));self.wire(*[(x,y) for x in xs])
        for x,py in pts:self.wire((x,py),(x,y));self.dot((x,y))
        self.power(name,(xs[0],y));self.used.update(nodes)
