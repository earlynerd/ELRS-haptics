"""Replace the initial green LED addition with a common-anode RGB indicator."""
from kicad_edit import *

def props(s): return {uq(p[1]):uq(p[2]) for p in children(s,'property')}
top=Sheet('haptic-bracelet.kicad_sch'); sh=Sheet('controller-support.kicad_sch')
assert any(props(s).get('Value')=='STATUS GREEN / TBD' for s in children(sh.a,'symbol')), 'Expected initial LED addition'
# Only the freshly added lower section is replaced; verify its contents against the untouched backup.
base=load(HW/'backups/before-status-led/controller-support.kicad_sch')
base_items={dump(a) for a in base if isinstance(a,list) and a[0]!='lib_symbols'}
for a in list(sh.a):
    if not isinstance(a,list) or a[0]=='lib_symbols' or dump(a) in base_items: continue
    assert a[0] in ['symbol','text','wire','global_label','label']
    if a[0]=='symbol': assert props(a).get('Reference') in ['D1','R47','R48']
    sh.a.remove(a)
top.path='/'+child(top.a,'uuid')[1]
sheet=next(s for s in children(top.a,'sheet') if props(s).get('Sheetfile')=='controller-support.kicad_sch')
sh.path=top.path+'/'+child(sheet,'uuid')[1]
for a in children(top.a,'global_label'):
    if uq(a[1])=='STATUS_LED': a[1]=q('LED_G_N')
esp=next(s for s in children(top.a,'symbol') if props(s).get('Reference')=='U1')
lib=next(s for s in children(child(top.a,'lib_symbols'),'symbol') if uq(s[1])==uq(child(esp,'lib_id')[1]))
at=child(esp,'at'); assert float(at[3])==0
for num,name,net in [('9','IO4','LED_R_N'),('20','IO15','LED_B_N')]:
    p=next(p for sub in children(lib,'symbol') for p in children(sub,'pin') if uq(child(p,'number')[1])==num)
    assert uq(child(p,'name')[1])==name
    pa=child(p,'at'); pos=(round(float(at[1])+float(pa[1]),4),round(float(at[2])-float(pa[2]),4))
    nc=next(n for n in children(top.a,'no_connect') if tuple(map(float,child(n,'at')[1:3]))==pos)
    top.a.remove(nc);top.net(pos,net,int(pa[3]),True)
R=stock('Device','R'); LED=stock('Device','LED_RGBA')
sh.text('RGB USER STATUS / COMMON ANODE / ACTIVE LOW',20.32,177.8)
for i,(net,res,pull,cath) in enumerate([('LED_R_N','R47','R48','LED_R_K'),('LED_G_N','R49','R50','LED_G_K'),('LED_B_N','R51','R52','LED_B_K')]):
    y=195.58+i*22.86
    sh.passive(R,pull,'100k',60.96,y,'3V3',net,('3V3',net),notes='Default LED off. GPIO4/5 SDIO straps high (SDIO unused); GPIO15 high preserves USB JTAG selection.')
    sh.passive(R,res,'2.2k',144.78,y,net,cath,(net,),angle=90,notes='Initial per-color current resistor. Select LED MPN and tune brightness; resistor limits channel below 1.6mA at 3.3V even at zero Vf.')
sh.connected(LED,'D1',269.24,218.44,{'1':'LED_R_K','2':'LED_G_K','3':'LED_B_K','4':'3V3'},('3V3',),value='STATUS RGB CA / TBD',footprint='',notes='Discrete four-terminal common-anode RGB LED, MPN and footprint pending. Low cathode GPIO lights channel. GPIO4=R, GPIO5=G, GPIO15=B; high/high-Z off via pullups.')
sh.text('GPIO4/5/15: low = color ON; high = OFF. PWM permitted. Set all high before sleep.\nSW3 (power sheet) is the accessible WAKE / OFF button; SW1/SW2 stay internal for recovery.\nGPIO4/5 select unused SDIO timing; GPIO15 pull-up preserves native USB JTAG. No eFuse change.',20.32,264.16,1.0)
top.save();sh.save()
print('RGB D1 added: GPIO4/5/15, active low, 100k pullups and 2.2k series resistors.')
