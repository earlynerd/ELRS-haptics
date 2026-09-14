"""One-time KiCad 10 project seed. Native KiCad files become the editable source.

Refuses to overwrite an existing project. Uses the installed KiCad symbol library.
"""
from pathlib import Path
import json
import re
import uuid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware'
LIB = Path('C:/Program Files/KiCad/10.0/share/kicad/symbols')
OUT.mkdir(exist_ok=True)
if (OUT / 'haptic-bracelet.kicad_sch').exists():
    raise SystemExit('Project already exists; edit it in KiCad. Seed will not overwrite.')

def uid(): return str(uuid.uuid4())
def q(s): return json.dumps(str(s))
def n(v): return f'{v:.4f}'.rstrip('0').rstrip('.') if v else '0'
def at(x,y): return f'{n(x)} {n(y)}'
def effects(size=1.27,extra=''): return f'(effects (font (size {size} {size})) {extra})'

def parse(s):
    tokens=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',s)
    stack=[]; result=None
    for t in tokens:
        if t=='(':
            a=[]
            if stack: stack[-1].append(a)
            stack.append(a)
        elif t==')': result=stack.pop()
        else: stack[-1].append(t)
    return result
def dump(a): return '('+' '.join(dump(x) if isinstance(x,list) else x for x in a)+')'
def child(a,key): return next(x for x in a if isinstance(x,list) and x[0]==key)
def children(a,key): return [x for x in a if isinstance(x,list) and x[0]==key]
def unquote(t): return json.loads(t) if t.startswith('"') else t

symbols={}
def stock(lib,name):
    key=f'{lib}:{name}'
    a=next(x for x in parse((LIB/f'{lib}.kicad_sym').read_text(encoding='utf-8')) if isinstance(x,list) and x[:2]==['symbol',q(name)])
    assert not children(a,'extends'), key
    symbols[key]=a
    return key

MCU=stock('RF_Module','ESP32-C6-MINI-1')
MUX=stock('Interface_Expansion','TCA9548APWR')
RES=stock('Device','R')
CAP=stock('Device','C')
CON=stock('Connector_Generic','Conn_01x06')
SW=stock('Switch','SW_Push')

def custom(name,ref,pins,w=10.16,h=12.7,ds=''):
    s=f'(symbol {q(name)} (pin_names (offset 0.635)) (in_bom yes) (on_board yes)'
    for k,v in [('Reference',ref),('Value',name),('Footprint',''),('Datasheet',ds)]:
        s+=f'(property {q(k)} {q(v)} (at 0 0 0) {effects(extra="(hide yes)" if k in ["Footprint","Datasheet"] else "")})'
    s+=f'(symbol {q(name+"_0_1")} (rectangle (start {-w} {h}) (end {w} {-h}) (stroke (width 0.254) (type default)) (fill (type background))))'
    s+=f'(symbol {q(name+"_1_1")}'
    for number,label,x,y,angle,typ in pins:
        s+=f'(pin {typ} line (at {at(x,y)} {angle}) (length 2.54) (name {q(label)} {effects(1.0)}) (number {q(number)} {effects(1.0)}))'
    s+='))'
    key=f'HapticBracelet:{name}'; symbols[key]=parse(s); return key

DRV=custom('DRV2625_YFF','U',[
 ('B1','SDA',-12.7,7.62,0,'bidirectional'),('C1','SCL',-12.7,2.54,0,'input'),
 ('B2','NRST',-12.7,-2.54,0,'input'),('A1','TRIG/INTZ',-12.7,-7.62,0,'bidirectional'),
 ('C2','VDD',0,15.24,270,'power_in'),('B3','GND',0,-15.24,90,'power_in'),
 ('A3','OUT+',12.7,7.62,180,'output'),('C3','OUT-',12.7,2.54,180,'output'),
 ('A2','REG',12.7,-7.62,180,'passive')],ds='https://www.ti.com/lit/ds/symlink/drv2625.pdf')
ACT=custom('Actuator_TBD','M', [('1','+',-7.62,2.54,0,'passive'),('2','-',-7.62,-2.54,0,'passive')],w=5.08,h=5.08)

root_id=uid(); haptic_sheet_id=uid(); power_sheet_id=uid()

class Sheet:
    def __init__(self,file,title,ident,path,page):
        self.file=file; self.title=title; self.id=ident; self.path=path; self.page=page
        self.items=[]; self.libs=set()
    def text(self,t,x,y,size=1.27):
        self.items.append(f'(text {q(t)} (at {at(x,y)} 0) {effects(size,"(justify left top)")} (uuid {uid()}))')
    def wire(self,p1,p2):
        self.items.append(f'(wire (pts (xy {at(*p1)}) (xy {at(*p2)})) (stroke (width 0) (type default)) (uuid {uid()}))')
    def label(self,t,p,angle=0,kind='label'):
        shape=' (shape bidirectional)' if kind=='hierarchical_label' else ''
        justify='right bottom' if angle==180 else 'left bottom'
        self.items.append(f'({kind} {q(t)} (at {at(*p)} {angle}){shape} {effects(1.0,f"(justify {justify})")} (uuid {uid()}))')
    def net(self,p,t,direction=0,length=5.08):
        dx,dy={0:(-length,0),180:(length,0),90:(0,length),270:(0,-length)}[direction]
        end=(round(p[0]+dx,4),round(p[1]+dy,4)); self.wire(p,end)
        self.label(t,end,180 if direction==0 else 0)
        return end
    def nc(self,p): self.items.append(f'(no_connect (at {at(*p)}) (uuid {uid()}))')
    def inst(self,key,ref,x,y,value=None,footprint=None):
        self.libs.add(key); a=symbols[key]; ident=uid()
        props={unquote(p[1]):unquote(p[2]) for p in children(a,'property')}
        s=f'(symbol (lib_id {q(key)}) (at {at(x,y)} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {ident})'
        maxy=max(float(child(p,'at')[2]) for sub in children(a,'symbol') for p in children(sub,'pin'))
        for k,v,px,py,hidden in [('Reference',ref,x+3.81,y-maxy-5.08,False),('Value',value or props['Value'],x+3.81,y-maxy-2.54,False),('Footprint',props.get('Footprint','') if footprint is None else footprint,x,y,True),('Datasheet',props.get('Datasheet',''),x,y,True)]:
            s+=f'(property {q(k)} {q(v)} (at {at(px,py)} 0) {effects(1.0,"(hide yes)" if hidden else "(justify left)")})'
        pins={}
        for sub in children(a,'symbol'):
            for p in children(sub,'pin'):
                number=unquote(child(p,'number')[1]); pa=child(p,'at'); label=unquote(child(p,'name')[1])
                pins[number]=((round(x+float(pa[1]),4),round(y-float(pa[2]),4)),int(pa[3]),label,p[1])
                s+=f'(pin {q(number)} (uuid {uid()}))'
        s+=f'(instances (project "haptic-bracelet" (path {q(self.path)} (reference {q(ref)}) (unit 1)))))'
        self.items.append(s); return pins
    def passive(self,key,ref,val,x,y,net1,net2):
        footprint='Resistor_SMD:R_0402_1005Metric' if key==RES else 'Capacitor_SMD:C_0402_1005Metric'
        p=self.inst(key,ref,x,y,val,footprint)
        for num,net in [('1',net1),('2',net2)]: self.net(p[num][0],net,p[num][1],2.54)
    def save(self):
        embedded=[]
        for key in sorted(self.libs):
            a=json.loads(json.dumps(symbols[key])); a[1]=q(key); embedded.append(dump(a))
        txt=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {self.id}) (paper "A3") (title_block (title {q(self.title)}) (date "2026-09-11") (rev "0.1 - schematic start") (comment 1 "One wrist / eight channels - design in progress")) (lib_symbols '+''.join(embedded)+')'+''.join(self.items)
        if self.page==1: txt+='(sheet_instances (path "/" (page "1")))'
        txt+='(embedded_fonts no))'
        (OUT/self.file).write_text(txt,encoding='utf-8')

top=Sheet('haptic-bracelet.kicad_sch','Haptic bracelet - controller and I2C fanout',root_id,'/'+root_id,1)
top.text('ATTITUDE FEEDBACK / ONE WRIST',20.32,15.24,2.54)
top.text('ESP-NOW telemetry -> ESP32-C6 -> TCA9548A -> eight DRV2625 / actuator channels',20.32,22.86)
top.text('Draft: module, GPIOs and passive packages are initial choices. Battery supply and actuator selection remain open.',20.32,30.48)
p=top.inst(MCU,'U1',76.2,85.09)
mapping={'3':'3V3','1':'GND','8':'MCU_EN','15':'I2C_SDA','16':'I2C_SCL','24':'MUX_nRESET','25':'HAPTIC_nRESET','22':'BOOT_IO8','23':'BOOT_IO9','30':'UART_RX','31':'UART_TX'}
seen=set()
for num,(pos,ang,name,typ) in p.items():
    if pos in seen: continue
    seen.add(pos)
    if num in mapping: top.net(pos,mapping[num],ang)
    elif typ!='no_connect': top.nc(pos)
top.text('MINI-1 is a provisional ESP32-C6 implementation.\nUnused GPIOs can be reassigned in the next pass.',20.32,123.19)
p=top.inst(MUX,'U2',190.5,85.09)
mapping={'1':'GND','2':'GND','21':'GND','12':'GND','24':'3V3','3':'MUX_nRESET','22':'I2C_SCL','23':'I2C_SDA'}
for num,net in mapping.items(): top.net(p[num][0],net,p[num][1])

sheet_pins=[]
for i,(sd,sc) in enumerate([('4','5'),('6','7'),('8','9'),('10','11'),('13','14'),('15','16'),('17','18'),('19','20')]):
    for num,name in [(sc,f'SCL{i}'),(sd,f'SDA{i}')]:
        pos=p[num][0]; endpoint=(254,pos[1]); top.wire(pos,endpoint)
        top.label(name,(223.52,pos[1]))
        sheet_pins.append(f'(pin {q(name)} bidirectional (at {at(*endpoint)} 180) {effects(1.0,"(justify left)")} (uuid {uid()}))')
top.items.append(f'(sheet (at 254 50.8) (size 101.6 63.5) (stroke (width 0.254) (type default)) (fill (color 0 0 0 0)) (uuid {haptic_sheet_id}) (property "Sheetname" "Eight haptic channels" (at 254 49.53 0) {effects(extra="(justify left bottom)")}) (property "Sheetfile" "haptics.kicad_sch" (at 254 115.57 0) {effects(extra="(justify left top)")}) '+''.join(sheet_pins)+f'(instances (project "haptic-bracelet" (path "/{root_id}" (page "2")))))')
top.text('Mux address: 0x70 (A2:A0 = 000).\nSelect one channel for individual driver transactions.\nEach driver retains its output when its I2C branch is disconnected.',152.4,124.46)

top.text('CONTROLLER SUPPORT / INITIAL VALUES',20.32,149.86,1.8)
for args in [(RES,'R1','4.7k',25.4,172.72,'3V3','I2C_SDA'),(RES,'R2','4.7k',58.42,172.72,'3V3','I2C_SCL'),(RES,'R3','10k',91.44,172.72,'3V3','MCU_EN'),(CAP,'C1','1u',124.46,172.72,'MCU_EN','GND'),(RES,'R4','10k',157.48,172.72,'3V3','BOOT_IO8'),(RES,'R5','10k',190.5,172.72,'3V3','BOOT_IO9'),(RES,'R6','10k',223.52,172.72,'3V3','MUX_nRESET'),(RES,'R7','10k',256.54,172.72,'HAPTIC_nRESET','GND')]: top.passive(*args)
for args in [(CAP,'C2','100n',25.4,208.28,'3V3','GND'),(CAP,'C3','10u',58.42,208.28,'3V3','GND'),(CAP,'C4','100n',91.44,208.28,'3V3','GND')]: top.passive(*args)
top.text('C2/C3: U1 local supply\nC4: U2 local supply',20.32,224.79)
for ref,name,x in [('SW1','RESET',147.32),('SW2','BOOT',198.12)]:
    pins=top.inst(SW,ref,x,208.28,name,footprint='')
    top.net(pins['1'][0],'MCU_EN' if ref=='SW1' else 'BOOT_IO9',pins['1'][1])
    top.net(pins['2'][0],'GND',pins['2'][1])
pins=top.inst(CON,'J1',325.12,175.26,'UART / BOOT / RESET',footprint='')
for num,net in enumerate(['3V3','GND','UART_TX','UART_RX','BOOT_IO9','MCU_EN'],1): top.net(pins[str(num)][0],net,pins[str(num)][1])
top.text('3.3 V logic. Connector footprint TBD.\n3V3 is the common supply rail, not a 5 V input.',292.1,195.58)
top.text('HAPTIC_nRESET is pulled low during MCU reset.\nGPIO19 releases all eight drivers; configure each over I2C.\nGPIO18 can reset the mux independently.',139.7,231.14)
top.items.append(f'(sheet (at 292.1 215.9) (size 76.2 22.86) (stroke (width 0.254) (type default)) (fill (color 0 0 0 0)) (uuid {power_sheet_id}) (property "Sheetname" "Battery and power - pending" (at 292.1 214.63 0) {effects(extra="(justify left bottom)")}) (property "Sheetfile" "power.kicad_sch" (at 292.1 240.03 0) {effects(extra="(justify left top)")}) (instances (project "haptic-bracelet" (path "/{root_id}" (page "3")))))')

hap=Sheet('haptics.kicad_sch','Haptic bracelet - eight independent actuator channels',uid(),f'/{root_id}/{haptic_sheet_id}',2)
hap.text('EIGHT ACTUATOR CHANNELS / MUX BRANCHES 0-7',15.24,12.7,2.54)
hap.text('Each DRV2625 has address 0x5A. Local REG capacitors are separate nets. Driver and actuator footprints are unassigned.',15.24,20.32)
hap.text('Initial common regulated 3V3 rail; confirm drive headroom after actuator selection. Pull-ups: initial 4.7k, verify bus capacitance.',15.24,27.94)
for i in range(8):
    x=50.8+(i%4)*99.06; y=76.2+(i//4)*104.14
    hap.text(f'CHANNEL {i}',x-33.02,y-36.83,1.8)
    pins=hap.inst(DRV,f'U{i+3}',x,y,'DRV2625',footprint='')
    for num,net in [('B1',f'SDA{i}'),('C1',f'SCL{i}')]:
        end=(x-27.94,pins[num][0][1]); hap.wire(pins[num][0],end); hap.label(net,end,0,'hierarchical_label')
    for num,net in [('B2','HAPTIC_nRESET'),('A1','GND'),('C2','3V3'),('B3','GND'),('A2',f'REG{i}')]: hap.net(pins[num][0],net,pins[num][1],3.81)
    actuator=hap.inst(ACT,f'M{i+1}',x+35.56,y-5.08,'Actuator TBD',footprint='')
    hap.wire(pins['A3'][0],actuator['1'][0]); hap.wire(pins['C3'][0],actuator['2'][0])
    for args in [(RES,f'R{8+2*i}','4.7k',x-30.48,y+35.56,'3V3',f'SDA{i}'),(RES,f'R{9+2*i}','4.7k',x-12.7,y+35.56,'3V3',f'SCL{i}'),(CAP,f'C{5+3*i}','100n',x+5.08,y+35.56,'3V3','GND'),(CAP,f'C{6+3*i}','100n',x+22.86,y+35.56,f'REG{i}','GND'),(CAP,f'C{7+3*i}','1u',x+40.64,y+35.56,'3V3','GND')]: hap.passive(*args)
hap.text('TRIG/INTZ is unused and grounded per TI pin guidance. Outputs connect across the actuator; neither output is ground.',15.24,263.525)

# Shared rails/reset use global labels. Branch signals remain hierarchical/local.
for sh in [top,hap]:
    for idx,item in enumerate(sh.items):
        if item.startswith('(label ') and any(item.startswith('(label '+q(net)+' ') for net in ['3V3','GND','HAPTIC_nRESET']):
            item=item.replace('(label ','(global_label ',1)
            item=item.replace('(effects ','(shape input) (effects ',1)
            sh.items[idx]=item

power=Sheet('power.kicad_sch','Haptic bracelet - battery and power design pending',uid(),f'/{root_id}/{power_sheet_id}',3)
power.text('BATTERY AND POWER / DESIGN RESERVED',25.4,25.4,2.54)
power.text('Battery-powered wrist unit. This sheet intentionally has no electrical implementation yet.',25.4,40.64,1.8)
power.text('To select in the next design pass:\n\n- Cell chemistry, capacity and mechanical envelope\n- Charging interface, charger, protection and power switch\n- Regulated 3V3 supply sized for ESP32-C6 radio plus actuator transients\n- Whether the actuator choice calls for a separate haptic supply\n- Battery measurement and low-battery behavior\n- Connectors / interconnect strategy for the wrist ring',25.4,58.42)
power.text('The present schematic has unpowered 3V3 and GND nets.\nDo not suppress those ERC findings with power flags before adding the supply circuit.',25.4,119.38,1.8)
for sh in [top,hap,power]: sh.save()

(OUT/'HapticBracelet.kicad_sym').write_text('(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor") '+''.join(dump(symbols[k]) for k in [DRV,ACT])+')',encoding='utf-8')
entries=[('HapticBracelet','${KIPRJMOD}/HapticBracelet.kicad_sym')]+[(lib,f'${{KICAD10_SYMBOL_DIR}}/{lib}.kicad_sym') for lib in ['RF_Module','Interface_Expansion','Device','Connector_Generic','Switch']]
(OUT/'sym-lib-table').write_text('(sym_lib_table (version 7) '+''.join(f'(lib (name {q(name)}) (type "KiCad") (uri {q(uri)}) (options "") (descr ""))' for name,uri in entries)+')',encoding='utf-8')
(OUT/'haptic-bracelet.kicad_pro').write_text(json.dumps({'meta':{'filename':'haptic-bracelet.kicad_pro','version':1},'board':{},'boards':[],'cvpcb':{},'erc':{},'libraries':{},'net_settings':{'classes':[{'name':'Default','description':'Initial KiCad defaults; revisit after current budget.','clearance':0.2,'track_width':0.25,'via_diameter':0.6,'via_drill':0.3,'microvia_diameter':0.3,'microvia_drill':0.1,'diff_pair_width':0.2,'diff_pair_gap':0.25,'diff_pair_via_gap':0.25,'wire_width':6,'bus_width':12,'line_style':0,'pcb_color':'rgba(0, 0, 0, 0.000)','schematic_color':'rgba(0, 0, 0, 0.000)'}],'meta':{'version':3}},'pcbnew':{},'schematic':{},'text_variables':{'DESIGN_STATUS':'SCHEMATIC START - POWER AND MECHANICS PENDING'}},indent=2)+'\n',encoding='utf-8')
print('Created three-sheet native KiCad project in',OUT)
