"""One-time addition of a GPIO-driven status LED to the native schematic."""
from kicad_edit import *
import shutil

top=Sheet('haptic-bracelet.kicad_sch')
support=Sheet('controller-support.kicad_sch')
def props(s): return {uq(p[1]):uq(p[2]) for p in children(s,'property')}
assert not any(props(s).get('Reference')=='D1' for s in children(support.a,'symbol')), 'Already added'
backup=HW/'backups/before-status-led'
backup.mkdir(parents=True,exist_ok=False)
for sh in [top,support]: shutil.copy2(sh.file,backup/sh.file.name)
top.path='/'+child(top.a,'uuid')[1]
sheet=next(s for s in children(top.a,'sheet') if props(s).get('Sheetfile')=='controller-support.kicad_sch')
support.path=top.path+'/'+child(sheet,'uuid')[1]
esp=next(s for s in children(top.a,'symbol') if props(s).get('Reference')=='U1')
key=uq(child(esp,'lib_id')[1]); lib=next(s for s in children(child(top.a,'lib_symbols'),'symbol') if uq(s[1])==key)
pin=next(p for sub in children(lib,'symbol') for p in children(sub,'pin') if uq(child(p,'number')[1])=='10')
assert uq(child(pin,'name')[1])=='IO5'
at=child(esp,'at'); assert float(at[3])==0
pa=child(pin,'at'); pos=(round(float(at[1])+float(pa[1]),4),round(float(at[2])-float(pa[2]),4))
nc=next(n for n in children(top.a,'no_connect') if tuple(map(float,child(n,'at')[1:3]))==pos)
top.a.remove(nc)
top.net(pos,'STATUS_LED',int(pa[3]),True)
R=stock('Device','R'); LED=stock('Device','LED')
support.text('USER STATUS LED / GPIO5',20.32,182.88)
support.passive(R,'R48','100k',55.88,210.82,'STATUS_LED','GND',('STATUS_LED','GND'),notes='Defines LED off and GPIO5 SDIO timing strap low during reset. SDIO is unused.')
support.passive(R,'R47','2.2k',137.16,210.82,'STATUS_LED','STATUS_LED_A',('STATUS_LED','GND'),angle=90,notes='Initial brightness resistor; tune for selected high-efficiency LED and light pipe.')
support.connected(LED,'D1',228.6,210.82,{'1':'GND','2':'STATUS_LED_A'},('GND',),value='STATUS GREEN / TBD',footprint='LED_SMD:LED_0603_1608Metric',notes='Single status LED, MPN pending. GPIO5 high illuminates. Off before sleep; no always-on power indicator.')
support.text('GPIO5 high lights D1; low = OFF. Keep low through sleep. No continuous power LED.\nGPIO5 also selects an SDIO timing strap; SDIO is unused here. Native USB and boot straps remain intact.\nSW3 on power sheet is the accessible WAKE / OFF button. SW1/SW2 remain internal recovery controls.',20.32,243.84,1.0)
top.save();support.save()
print('Added D1/R47/R48 on GPIO5; retained SW3 as user button.')
