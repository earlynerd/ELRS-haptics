"""Bounded USB simplification from the saved pre-change main project."""
import copy
from readable_schematic import Drawing,props
from kicad_edit import *
BACK=HW/'backups/before-simple-usb/main'
REMOVED={'U13','U16','U17','Q2','Q3','C31','C33',*[f'R{i}' for i in range(26,34)]}
NEW={'R60':(37.75,71.4),'R61':(37.75,72.6)}
GLOBALS={'USB_D_N','USB_D_P','USB_VBUS','VBUS_nPRESENT'}

def schematic():
 for file in ['usb.kicad_sch','main.kicad_sch','power.kicad_sch']:
  assert (HW/'main'/file).read_bytes()==(BACK/file).read_bytes(),'Schematic changed after snapshot'
 old=load(BACK/'usb.kicad_sch')
 sample=next(x for x in children(old,'symbol') if props(x).get('Reference')=='R26')
 instancepath=uq(child(child(child(sample,'instances'),'project'),'path')[1])
 d=Drawing(BACK/'usb.kicad_sch',HW/'main/usb.kicad_sch','main',instancepath,'USB-C / passive CC, native USB and VBUS sensing')
 for ref in NEW:
  s=copy.deepcopy(sample);child(s,'uuid')[1]=q(uid())
  for pin in children(s,'pin'):child(pin,'uuid')[1]=q(uid())
  for z in children(s,'property'):
   if uq(z[1])=='Reference':z[2]=q(ref)
   elif uq(z[1])=='Value':z[2]=q('5.1k 1%')
  d.old[ref]=s
 I=d.inst;P=d.pt
 I('J2',40.64,73.66)
 for pins,x,y,r,net in [(['A7','B7'],66.04,71.12,'R24','USB_D_N'),(['A6','B6'],71.12,78.74,'R25','USB_D_P')]:
  for n in pins:d.wire(P('J2',n),(x,P('J2',n)[1]),(x,y))
  d.dot((x,y));I(r,152.4,y,90);d.wire((x,y),P(r,1));d.wire(P(r,2),(220.98,y));d.label(net,(220.98,y),True)
 I('U14',106.68,93.98)
 for n,y in [('1',78.74),('2',71.12)]:
  x,py=P('U14',n);d.wire((x,py),(x,y));d.dot((x,y))
 # Confirm device pin polarity through the preservation check, not just labels.
 for r,x,y in [('C29',187.96,71.12),('C30',208.28,78.74)]:
  I(r,x,97.79);d.wire(P(r,1),(x,y));d.dot((x,y));d.term(r,2,'GND',power=True)
 I('U15',248.92,60.96)
 for pin,x,y,res,rx,esd in [('A5',81.28,43.18,'R60',289.56,'1'),('B5',86.36,48.26,'R61',312.42,'2')]:
  I(res,rx,63.5);a=P('J2',pin);d.wire(a,(x,a[1]),(x,y),(rx,y),P(res,1))
  px,py=P('U15',esd);d.wire((px,py),(px,y));d.dot((px,y))
 d.rail('GND',[('R60','2'),('R61','2')],83.82)
 d.term('J2','A4','USB_VBUS',global_=True)
 d.rail('GND',[('J2','A1'),('J2','SH')],109.22)
 d.power('PWR_FLAG',(33.02,109.22));d.dot((33.02,109.22))
 I('C32',66.04,160.02);d.term('C32',1,'USB_VBUS',global_=True);d.term('C32',2,'GND',power=True)
 d.power('PWR_FLAG',(66.04,151.13))
 I('R34',142.24,157.48);I('R35',142.24,195.58);I('Q4',172.72,177.8);I('R36',175.26,147.32)
 d.term('R34',1,'USB_VBUS',global_=True)
 d.wire(P('R34',2),(142.24,177.8),P('R35',1));d.wire((142.24,177.8),P('Q4',1));d.dot((142.24,177.8))
 d.term('R35',2,'GND',power=True);d.term('Q4',2,'GND',power=True)
 d.term('R36',1,'+3V3',power=True);d.wire(P('R36',2),P('Q4',3));d.label('VBUS_nPRESENT',P('Q4',3),True)
 d.text('USB 2.0 data / ESD and native Serial-JTAG',25.4,22.86)
 d.text('5 V sink / independent CC pull-downs',238.76,22.86)
 d.text('Connector bypass',25.4,134.62);d.text('VBUS presence / 3.3 V logic',124.46,124.46)
 d.text('USB_VBUS connects directly to charger U11 IN and C34.\nBQ25186 provides input-current limiting; no external current selector.\nNo CC current-advertisement detection or USB PD negotiation.',25.4,233.68,1.27)
 d.text('R60 and R61 each terminate one CC pin to GND.\nUSB 2.0 contacts are paired for either plug orientation.\nC29/C30 remain optional DNP tuning capacitors.',238.76,116.84,1.27)
 for ref in ['J2','Q4']:
  for z in children(d.instances[ref],'property'):
   if uq(z[1]) not in ['Reference','Value']:continue
   isref=uq(z[1])=='Reference'
   child(z,'at')[1:3]=(['25.4','48.26' if isref else '50.8'] if ref=='J2' else ['182.88','176.53' if isref else '179.07'])
 d.finish(GLOBALS)
 a=load(BACK/'main.kicad_sch');retired={'CC_nINT','USB_INPUT_OFF','USB_LIMIT_ENABLE','USB_LIMIT_HIGH'}
 for lab in list(children(a,'global_label')):
  if uq(lab[1]) not in retired:continue
  pt=tuple(map(float,child(lab,'at')[1:3]));matches=[]
  for w in children(a,'wire'):
   xy=[tuple(map(float,z[1:3])) for z in child(w,'pts')[1:]]
   if pt in xy:matches.append((w,xy[1-xy.index(pt)]))
  assert len(matches)==1
  w,other=matches[0];a.remove(w);a.remove(lab)
  a.append(parse(f'(no_connect (at {other[0]} {other[1]}) (uuid {uid()}))'))
 for t in children(a,'text'):
  if 'GPIO6/7:' in uq(t[1]):t[1]=q(uq(t[1]).replace('main-board power/USB I2C only','charger I2C only')+'\nGPIO0/14/22/23 spare (USB controls removed)')
 save(HW/'main/main.kicad_sch',a)
 a=load(BACK/'power.kicad_sch')
 for x in a:
  if isinstance(x,list) and x[0] in ['label','global_label'] and uq(x[1])=='USB_5V_LIMITED':x[1]=q('USB_VBUS')
 save(HW/'main/power.kicad_sch',a)

if __name__=='__main__':schematic()
