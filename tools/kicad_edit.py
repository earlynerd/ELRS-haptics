"""Small native KiCad schematic editor used by bounded project migrations."""
from pathlib import Path
import json,re,uuid,math,copy

ROOT=Path(__file__).resolve().parents[1]
HW=ROOT/'hardware'
LIB=Path('C:/Program Files/KiCad/10.0/share/kicad/symbols')
def uid(): return str(uuid.uuid4())
def q(s): return json.dumps(str(s))
def uq(s): return json.loads(s) if s.startswith('"') else s
def parse(s):
    stack=[]; result=None
    for t in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',s):
        if t=='(':
            a=[]
            if stack: stack[-1].append(a)
            stack.append(a)
        elif t==')': result=stack.pop()
        else: stack[-1].append(t)
    assert not stack
    return result
def dump(a): return '('+' '.join(dump(x) if isinstance(x,list) else x for x in a)+')'
def children(a,k): return [x for x in a if isinstance(x,list) and x[0]==k]
def child(a,k): return next(x for x in a if isinstance(x,list) and x[0]==k)
def load(p): return parse(Path(p).read_text(encoding='utf-8'))
def save(p,a): Path(p).write_text(dump(a)+'\n',encoding='utf-8')
def fx(size=1.0,hide=False): return f'(effects (font (size {size} {size})) '+('(hide yes)' if hide else '(justify left)')+')'
symbols={}
def stock(lib,name):
    tree=load(LIB/f'{lib}.kicad_sym')
    def get(n):
        a=copy.deepcopy(next(x for x in children(tree,'symbol') if x[1]==q(n)))
        if children(a,'extends'):
            parent=uq(child(a,'extends')[1]); base=get(parent)
            a.remove(child(a,'extends'))
            for k in ['symbol','pin_names','pin_numbers']:
                for entry in children(base,k):
                    entry=copy.deepcopy(entry)
                    if k=='symbol': entry[1]=q(uq(entry[1]).replace(parent+'_',n+'_'))
                    a.append(entry)
        return a
    key=f'{lib}:{name}'; symbols[key]=get(name); return key
def custom(name,pins,w=12.7,h=15.24,ds='',ref='U'):
    s=f'(symbol {q(name)} (pin_names (offset 0.635)) (in_bom yes) (on_board yes)'
    for k,v in [('Reference',ref),('Value',name),('Footprint',''),('Datasheet',ds)]: s+=f'(property {q(k)} {q(v)} (at 0 0 0) {fx(hide=k in ["Footprint","Datasheet"])})'
    s+=f'(symbol {q(name+"_0_1")} (rectangle (start {-w} {h}) (end {w} {-h}) (stroke (width 0.254) (type default)) (fill (type background)))) (symbol {q(name+"_1_1")}'
    for num,nm,x,y,angle,typ in pins:
        s+=f'(pin {typ} line (at {x} {y} {angle}) (length 2.54) (name {q(nm)} (effects (font (size 1 1)))) (number {q(num)} (effects (font (size 1 1)))))'
    s+='))'; key='HapticBracelet:'+name; symbols[key]=parse(s); return key

class Sheet:
    def __init__(self,file,path=None,title=None):
        self.file=HW/file
        if self.file.exists(): self.a=load(self.file)
        else: self.a=parse(f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {uid()}) (paper "A3") (title_block (title {q(title)}) (date "2026-09-11") (rev "0.2") (comment 1 "One wrist / initial circuit")) (lib_symbols) (embedded_fonts no))')
        self.path=path
    def add(self,s): self.a.append(parse(s))
    def text(self,t,x,y,size=1.27): self.add(f'(text {q(t)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left top)) (uuid {uid()}))')
    def wire(self,p1,p2):
        assert p1!=p2
        self.add(f'(wire (pts (xy {p1[0]} {p1[1]}) (xy {p2[0]} {p2[1]})) (stroke (width 0) (type default)) (uuid {uid()}))')
    def label(self,net,p,global_=False,angle=0):
        key='global_label' if global_ else 'label'; shape='(shape bidirectional)' if global_ else ''
        self.add(f'({key} {q(net)} (at {p[0]} {p[1]} {angle}) {shape} (effects (font (size 1 1)) (justify {"right" if angle==180 else "left"} bottom)) (uuid {uid()}))')
    def net(self,p,name,angle=0,global_=False,length=5.08):
        dx,dy={0:(-length,0),180:(length,0),90:(0,length),270:(0,-length)}[angle]
        end=(round(p[0]+dx,4),round(p[1]+dy,4)); self.wire(p,end); self.label(name,end,global_,180 if angle==0 else 0)
    def nc(self,p): self.add(f'(no_connect (at {p[0]} {p[1]}) (uuid {uid()}))')
    def inst(self,key,ref,x,y,value=None,footprint=None,mpn=None,manufacturer=None,dnp=False,notes=None,angle=0):
        lib=symbols[key]; embed=child(self.a,'lib_symbols')
        if not any(a[1]==q(key) for a in children(embed,'symbol')):
            a=copy.deepcopy(lib); a[1]=q(key); embed.append(a)
        props={uq(a[1]):uq(a[2]) for a in children(lib,'property')}
        ident=uid(); pins={}; maxy=0
        rad=math.radians(angle)
        for sub in children(lib,'symbol'):
            for pin in children(sub,'pin'):
                pos=child(pin,'at'); px=float(pos[1]); py=float(pos[2]);
                xx=px*math.cos(rad)-py*math.sin(rad); yy=px*math.sin(rad)+py*math.cos(rad)
                maxy=max(maxy,yy)
                pins[uq(child(pin,'number')[1])]=((round(x+xx,4),round(y-yy,4)),(int(pos[3])+angle)%360,uq(child(pin,'name')[1]),pin[1])
        s=f'(symbol (lib_id {q(key)}) (at {x} {y} {angle}) (unit 1) (in_bom yes) (on_board yes) (dnp {"yes" if dnp else "no"}) (uuid {ident})'
        data=[('Reference',ref),('Value',value or props['Value']),('Footprint',props.get('Footprint','') if footprint is None else footprint),('Datasheet',props.get('Datasheet',''))]
        if mpn: data+=[('MPN',mpn),('Manufacturer',manufacturer)]
        if notes: data+=[('BOM Comments',notes)]
        for k,v in data:
            hidden=k not in ['Reference','Value']; px=x+7.62; py=y-maxy-5.08+(2.54 if k=='Value' else 0)
            if key in ['Device:R','Device:C','Device:L']:
                px=x+3.81 if angle==0 else x-3.81
                py=y+(-1.27 if k=='Reference' else 1.27) if angle==0 else y+(-5.08 if k=='Reference' else -2.54)
            s+=f'(property {q(k)} {q(v)} (at {px} {py} 0) {fx(hide=hidden)})'
        for num in pins: s+=f'(pin {q(num)} (uuid {uid()}))'
        s+=f'(instances (project "haptic-bracelet" (path {q(self.path)} (reference {q(ref)}) (unit 1)))))'
        self.add(s); return pins
    def connected(self,key,ref,x,y,nets,global_nets=(),**kw):
        pins=self.inst(key,ref,x,y,**kw); seen=set()
        for num,(pos,ang,name,typ) in pins.items():
            if pos in seen: continue
            seen.add(pos)
            if num in nets:
                net=nets[num]
                self.net(pos,net,ang,net in global_nets)
            else: self.nc(pos)
        return pins
    def passive(self,key,ref,value,x,y,net1,net2,global_nets=(),footprint=None,**kw):
        if footprint is None: footprint={'Device:R':'Resistor_SMD:R_0402_1005Metric','Device:C':'Capacitor_SMD:C_0402_1005Metric','Device:L':''}[key]
        return self.connected(key,ref,x,y,{'1':net1,'2':net2},global_nets,value=value,footprint=footprint,**kw)
    def save(self): save(self.file,self.a)
