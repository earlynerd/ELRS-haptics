"""One-time migration: add USB-C Serial/JTAG and the accepted power architecture."""
from kicad_edit import *
import shutil

if (HW/'usb.kicad_sch').exists(): raise SystemExit('USB migration already applied; edit native files.')
backup=HW/'backups'/'before-usb-power'
backup.mkdir(parents=True,exist_ok=True)
for name in ['haptic-bracelet.kicad_sch','power.kicad_sch','HapticBracelet.kicad_sym','sym-lib-table','fp-lib-table']:
    shutil.copy2(HW/name,backup/name)

R=stock('Device','R'); C=stock('Device','C'); L=stock('Device','L')
J=stock('Connector','USB_C_Receptacle_USB2.0_16P')
J4=stock('Connector_Generic','Conn_01x04'); SW=stock('Switch','SW_Push')
FET=stock('Transistor_FET','2N7002'); ESD=stock('Power_Protection','TPD2EUSB30')
FLAG=stock('power','PWR_FLAG')
for p in children(symbols[ESD],'property'):
    if p[1]=='"Datasheet"': p[2]=q('https://www.ti.com/lit/ds/symlink/tpd2eusb30.pdf')

BQ=custom('BQ25186DLH',[
 ('10','IN',-15.24,10.16,0,'power_in'),('1','SYS',15.24,10.16,180,'power_out'),
 ('2','BAT',15.24,2.54,180,'passive'),('5','GND',0,-17.78,90,'power_in'),
 ('11','EP',2.54,-17.78,90,'passive'),('4','~{CE}',-15.24,2.54,0,'input'),
 ('7','SDA',-15.24,-2.54,0,'bidirectional'),('8','SCL',-15.24,-7.62,0,'input'),
 ('9','~{INT}',-15.24,-12.7,0,'open_collector'),('3','~{PG}/GPO',15.24,-5.08,180,'open_collector'),
 ('6','TS/MR',15.24,-12.7,180,'bidirectional')],ds='https://www.ti.com/lit/ds/symlink/bq25186.pdf')
REG=custom('TPS63802DLA',[
 ('10','VIN',-15.24,10.16,0,'power_in'),('1','EN',-15.24,2.54,0,'input'),
 ('2','MODE',-15.24,-5.08,0,'input'),('9','L1',-5.08,17.78,270,'passive'),
 ('7','L2',5.08,17.78,270,'passive'),('6','VOUT',15.24,10.16,180,'power_out'),
 ('4','FB',15.24,2.54,180,'input'),('5','PG',15.24,-7.62,180,'open_collector'),
 ('3','AGND',-2.54,-17.78,90,'power_in'),('8','GND',2.54,-17.78,90,'power_in')],ds='https://www.ti.com/lit/ds/symlink/tps63802.pdf')
CC=custom('TUSB320LAIRWB',[
 ('1','CC1',-15.24,10.16,0,'bidirectional'),('2','CC2',-15.24,5.08,0,'bidirectional'),
 ('4','VBUS_DET',-15.24,-2.54,0,'input'),('3','PORT',-15.24,-7.62,0,'input'),
 ('5','ADDR',-15.24,-12.7,0,'input'),('11','~{EN}',15.24,-12.7,180,'input'),
 ('12','VDD',0,17.78,270,'power_in'),('10','GND',0,-17.78,90,'power_in'),
 ('7','SDA',15.24,10.16,180,'bidirectional'),('8','SCL',15.24,5.08,180,'input'),
 ('6','~{INT}',15.24,-2.54,180,'open_collector'),('9','ID',15.24,-7.62,180,'open_collector')],ds='https://www.ti.com/lit/ds/symlink/tusb320lai.pdf')
LIMIT=custom('TPS2553DBV',[
 ('1','IN',-12.7,7.62,0,'power_in'),('2','GND',0,-12.7,90,'power_in'),
 ('3','EN',-12.7,-5.08,0,'input'),('6','OUT',12.7,7.62,180,'power_out'),
 ('5','ILIM',12.7,0,180,'input'),('4','~{FAULT}',12.7,-7.62,180,'open_collector')],w=10.16,h=10.16,ds='https://www.ti.com/lit/ds/symlink/tps2553.pdf')
SEL=custom('TS5A3159DBV',[
 ('4','COM',-12.7,5.08,0,'passive'),('3','NC',12.7,5.08,180,'passive'),
 ('1','NO',12.7,0,180,'passive'),('6','IN',-12.7,-5.08,0,'input'),
 ('5','V+',0,12.7,270,'power_in'),('2','GND',0,-12.7,90,'power_in')],w=10.16,h=10.16,ds='https://www.ti.com/lit/ds/symlink/ts5a3159.pdf')

top=Sheet('haptic-bracelet.kicad_sch')
rid=child(top.a,'uuid')[1]; top.path='/'+rid
power_sheet=next(s for s in children(top.a,'sheet') if any(p[1]=='"Sheetfile"' and p[2]=='"power.kicad_sch"' for p in children(s,'property')))
pid=child(power_sheet,'uuid')[1]; usid=uid()
power=Sheet('power.kicad_sch',f'/{rid}/{pid}')
power.a=[a for a in power.a if not (isinstance(a,list) and a[0] in ['text','lib_symbols'])]
power.a.append(['lib_symbols'])
tb=child(power.a,'title_block'); child(tb,'title')[1]=q('Haptic bracelet - charger and regulated supply'); child(tb,'rev')[1]=q('0.2')
usb=Sheet('usb.kicad_sch',f'/{rid}/{usid}','Haptic bracelet - USB-C data and input power')
G={'3V3','GND','I2C_SDA','I2C_SCL','USB_D_P','USB_D_N','VBUS_nPRESENT','CC_nINT','CHG_ALLOW','CHG_nINT','USB_LIMIT_ENABLE','USB_LIMIT_HIGH','USB_INPUT_OFF','USB_5V_LIMITED'}

# Extend existing MCU connections without replacing its symbol or instance UUID.
mcu=next(s for s in children(top.a,'symbol') if any(p[1]=='"Reference"' and p[2]=='"U1"' for p in children(s,'property')))
lib=next(s for s in children(child(top.a,'lib_symbols'),'symbol') if s[1]==child(mcu,'lib_id')[1])
mx,my=map(float,child(mcu,'at')[1:3])
mapping={'17':'USB_D_N','18':'USB_D_P','12':'CC_nINT','13':'VBUS_nPRESENT','26':'CHG_ALLOW','27':'CHG_nINT','28':'USB_LIMIT_ENABLE','29':'USB_LIMIT_HIGH','19':'USB_INPUT_OFF'}
for sub in children(lib,'symbol'):
    for pin in children(sub,'pin'):
        num=uq(child(pin,'number')[1])
        if num not in mapping: continue
        pp=child(pin,'at'); pos=(round(mx+float(pp[1]),4),round(my-float(pp[2]),4))
        top.a=[a for a in top.a if not (isinstance(a,list) and a[0]=='no_connect' and tuple(map(float,child(a,'at')[1:3]))==pos)]
        top.net(pos,mapping[num],int(pp[3]),True)
for a in children(top.a,'label'):
    if uq(a[1]) in ['I2C_SDA','I2C_SCL']:
        a[0]='global_label'; a.insert(3,['shape','bidirectional'])
for a in children(top.a,'text'):
    if 'Battery supply and actuator' in uq(a[1]): a[1]=q('Draft: USB-C data/power and charger installed. Protected pack, actuators and mechanics remain open.')
for p in children(power_sheet,'property'):
    if p[1]=='"Sheetname"': p[2]=q('Charger and regulated supply')
top.add(f'(sheet (at 292.1 15.24) (size 101.6 22.86) (stroke (width 0.254) (type default)) (fill (color 0 0 0 0)) (uuid {usid}) (property "Sheetname" "USB-C data and power" (at 292.1 13.97 0) {fx()}) (property "Sheetfile" "usb.kicad_sch" (at 292.1 39.37 0) {fx()}) (instances (project "haptic-bracelet" (path "/{rid}" (page "4")))))')
child(child(top.a,'title_block'),'rev')[1]=q('0.2')

# USB page: data, CC termination/current detection, then power input/current selection.
usb.text('USB-C / NATIVE SERIAL + JTAG / 5 V SINK',15.24,12.7,2.54)
usb.text('D- -> GPIO12, D+ -> GPIO13. USB 2.0 full speed. No USB bridge, PD negotiation or source mode.',15.24,22.86)
usb.connected(J,'J2',40.64,66.04,{'A1':'GND','SH':'GND','A4':'VBUS','A5':'CC1','B5':'CC2','A6':'USB_CONN_P','B6':'USB_CONN_P','A7':'USB_CONN_N','B7':'USB_CONN_N'},G,footprint='',notes='USB-C USB2 receptacle, 16-pin contact map. Mechanical MPN/footprint pending.')
usb.connected(ESD,'U14',106.68,71.12,{'1':'USB_CONN_P','2':'USB_CONN_N','3':'GND'},G,mpn='TPD2EUSB30DRTR',manufacturer='Texas Instruments',notes='Place at USB connector; short return to GND.')
usb.passive(R,'R24','22',157.48,60.96,'USB_CONN_N','USB_D_N',G,angle=90)
usb.passive(R,'R25','22',157.48,81.28,'USB_CONN_P','USB_D_P',G,angle=90)
usb.passive(C,'C29','TUNE / DNP',200.66,60.96,'USB_D_N','GND',G,dnp=True,notes='Optional USB shunt tuning capacitor; unpopulated initially.')
usb.passive(C,'C30','TUNE / DNP',233.68,81.28,'USB_D_P','GND',G,dnp=True,notes='Optional USB shunt tuning capacitor; unpopulated initially.')
usb.text('22 ohm resistors and optional capacitors near U1.\nJoin duplicate D contacts close to J2; route as 90-ohm differential pair.',20.32,104.14)
usb.connected(CC,'U13',312.42,66.04,{'1':'CC1','2':'CC2','4':'CC_VBUS_DET','3':'GND','5':'GND','11':'GND','12':'3V3','10':'GND','7':'I2C_SDA','8':'I2C_SCL','6':'CC_nINT'},G,footprint='',mpn='TUSB320LAIRWBR',manufacturer='Texas Instruments',notes='RWB pin map; footprint pending. PORT=GND sink only, ADDR=GND 0x47. Internal Rd including dead-battery termination; do not add external 5.1k Rd.')
usb.passive(R,'R26','887k 1%',269.24,114.3,'VBUS','CC_VBUS_DET',G)
usb.passive(R,'R27','10k',320.04,114.3,'3V3','CC_nINT',G)
usb.passive(C,'C31','100n',370.84,114.3,'3V3','GND',G)
usb.connected(ESD,'U15',365.76,43.18,{'1':'CC1','2':'CC2','3':'GND'},G,mpn='TPD2EUSB30DRTR',manufacturer='Texas Instruments',notes='CC ESD protection only; not short-to-VBUS overvoltage protection.')
usb.text('U13: internal Rd on CC1/CC2; I2C 0x47.\nDead-battery attach supported. CC current class is read in firmware.',254,137.16)

usb.text('INPUT LIMIT / RESET DEFAULT IS 75 mA TYPICAL',15.24,142.24,1.8)
usb.connected(LIMIT,'U16',60.96,180.34,{'1':'VBUS','2':'GND','3':'USB_IN_EN','6':'USB_5V_LIMITED','5':'ILIM_SELECT'},G,footprint='Package_TO_SOT_SMD:SOT-23-6',mpn='TPS2553DBVR',manufacturer='Texas Instruments',notes='Input current cap; ILIM tied to IN via U17 at reset. 75mA typical, 50-100mA device limit, excluding housekeeping.')
usb.connected(SEL,'U17',152.4,180.34,{'4':'ILIM_SELECT','3':'VBUS','1':'ILIM_R','6':'USB_LIMIT_ENABLE','5':'VBUS','2':'GND'},G,footprint='Package_TO_SOT_SMD:SOT-23-6',mpn='TS5A3159DBVR',manufacturer='Texas Instruments',notes='Control low selects ILIM=VBUS. Control high selects resistor-programmed current. Break-before-make transition requires bench check.')
usb.passive(R,'R28','62k 1%',208.28,175.26,'ILIM_R','GND',G)
usb.passive(R,'R29','43k 1%',246.38,175.26,'ILIM_R','ILIM_HIGH_D',G)
usb.connected(FET,'Q3',279.4,180.34,{'1':'USB_LIMIT_HIGH','2':'GND','3':'ILIM_HIGH_D'},G,notes='Select 3.3V-gate-compatible 2N7002 variant; low-current resistor switching.')
usb.passive(R,'R30','100k',312.42,180.34,'USB_LIMIT_HIGH','GND',G)
usb.passive(R,'R31','100k',182.88,226.06,'USB_LIMIT_ENABLE','GND',G)
usb.passive(C,'C32','1u 10V',20.32,226.06,'VBUS','GND',G,footprint='Capacitor_SMD:C_0603_1608Metric')
usb.passive(C,'C33','100n 10V',55.88,226.06,'VBUS','GND',G)
usb.passive(R,'R32','100k',91.44,226.06,'VBUS','USB_IN_EN',G)
usb.connected(FET,'Q2',137.16,226.06,{'1':'USB_INPUT_OFF','2':'GND','3':'USB_IN_EN'},G,notes='GPIO high disconnects USB input. Reset default input enabled.')
usb.passive(R,'R33','100k',223.52,226.06,'USB_INPUT_OFF','GND',G)
usb.connected(FET,'Q4',335.28,226.06,{'1':'VBUS_GATE','2':'GND','3':'VBUS_nPRESENT'},G,notes='VBUS detection without exposing an ESP32 pin to 5V.')
usb.passive(R,'R34','100k',279.4,226.06,'VBUS','VBUS_GATE',G)
usb.passive(R,'R35','1M',375.92,226.06,'VBUS_GATE','GND',G)
usb.passive(R,'R36','10k',375.92,185.42,'3V3','VBUS_nPRESENT',G)
usb.text('Higher limits require source permission. R28 alone: <500mA; R28 || R29: <1.5A (resistor tolerance included).\nSuspend: CHG_ALLOW=0, force battery power, disconnect USB input; resume must re-evaluate source and limits.\nFirmware and attach/suspend/inrush validation remain pending. No compliant-port claim from ERC.',15.24,258,1.0)

# Charger/regulator page.
power.text('POWER / 1S PARALLEL PACK / USB-C CHARGING',15.24,12.7,2.54)
power.text('USB input is current-limited on sheet 4. U11 power path supplies SYS from USB or the protected battery.',15.24,22.86)
power.connected(BQ,'U11',96.52,71.12,{'10':'USB_5V_LIMITED','1':'SYS','2':'BAT_PROTECTED','5':'GND','11':'GND','4':'CHG_nCE','7':'I2C_SDA','8':'I2C_SCL','9':'CHG_nINT','6':'PACK_TS'},G,footprint='',mpn='BQ25186DLHR',manufacturer='Texas Instruments',notes='DLH exposed pad connected to GND. Footprint pending exact land pattern. 0x6A; hardware charge disabled at reset.')
power.passive(C,'C34','1u 10V',25.4,111.76,'USB_5V_LIMITED','GND',G,footprint='Capacitor_SMD:C_0603_1608Metric')
power.passive(C,'C35','10u 10V',66.04,111.76,'SYS','GND',G,footprint='Capacitor_SMD:C_0805_2012Metric')
power.passive(C,'C36','1u 10V',106.68,111.76,'BAT_PROTECTED','GND',G,footprint='Capacitor_SMD:C_0603_1608Metric')
power.passive(R,'R37','10k',147.32,111.76,'3V3','CHG_nINT',G)
power.connected(J4,'J3',198.12,60.96,{'1':'BAT_PROTECTED','2':'GND','3':'PACK_TS','4':'GND'},G,value='PROTECTED 1S PACK + NTC',footprint='',notes='External matched 1S-NP pack with pack protector, branch fuses and temperature sensing. Not a bare-cell connector.')
power.text('J3 pin 3: pack NTC to pin 4, selected for U11 TS profile.\nNo onboard dummy thermistor. One NTC does not cover all distant cells.\nDistributed temperature supervision and pack hardware still to design.',162.56,81.28,1.0)
power.passive(R,'R38','100k',30.48,172.72,'SYS','CHG_nCE',G)
power.connected(FET,'Q1',83.82,172.72,{'1':'CHG_ALLOW','2':'GND','3':'CHG_nCE'},G,notes='Default OFF disables charging via R38. Firmware asserts only after cell/source/temperature checks.')
power.passive(R,'R39','100k',124.46,172.72,'CHG_ALLOW','GND',G)
power.connected(SW,'SW3',187.96,172.72,{'1':'PACK_TS','2':'GND'},G,value='WAKE / SHIP',footprint='',notes='Momentary TS/MR button per charger application; long-press and ship behavior configured in firmware.')

power.connected(REG,'U12',307.34,71.12,{'10':'SYS','1':'SYS','2':'GND','9':'SW_L1','7':'SW_L2','6':'3V3','4':'REG_FB','3':'GND','8':'GND'},G,footprint='',mpn='TPS63802DLAR',manufacturer='Texas Instruments',notes='DLA asymmetric HotRod footprint pending. MODE low power-save; EN follows SYS.')
power.passive(L,'L1','0.47uH',307.34,33.02,'SW_L1','SW_L2',G,angle=90,footprint='',notes='Select inductor against low-battery peak current plus margin; TI example 5.4A+ saturation. Land pattern pending.')
power.passive(C,'C37','10u 10V',248.92,119.38,'SYS','GND',G,footprint='Capacitor_SMD:C_0805_2012Metric')
power.passive(C,'C38','22u 10V',297.18,119.38,'3V3','GND',G,footprint='Capacitor_SMD:C_0805_2012Metric',notes='Check effective capacitance at DC bias; regulator minimum 7uF effective.')
power.passive(C,'C39','22u 10V',345.44,119.38,'3V3','GND',G,footprint='Capacitor_SMD:C_0805_2012Metric',notes='Extra local transient reservoir; check converter stability/effective capacitance at layout.')
power.passive(R,'R40','511k 1%',279.4,172.72,'3V3','REG_FB',G)
power.passive(R,'R41','91k 1%',327.66,172.72,'REG_FB','GND',G)
power.text('VOUT = 0.500 x (1 + 511k / 91k) = 3.308 V nominal.\nPlace L1, input and output capacitors tight to U12.\nKeep FB and its return away from L1/L2 switching nodes.',243.84,193.04)
power.text('CHARGING DEFAULT: DISABLED\nU11 /CE is pulled to SYS; Q1 must be enabled to charge.\nSet cell voltage/current/termination and temperature policy first.\nKeep SYS regulation at 4.5 V. No 5.5 V/pass-through setting.\nFirmware must handle charger reset/watchdog and USB suspend.',20.32,210.82)
power.text('PACK BOUNDARY\nCell count/capacity, branch fuses, pack protector thresholds,\nadditional cell temperature sensing and connector remain open.\nJ3 expects the protected pack terminals; do not bypass protection.',20.32,246.38,1.0)
# ERC flags mark actual external source/return boundaries, not fictitious internal supplies.
usb.connected(FLAG,'#FLG01',15.24,38.1,{'1':'VBUS'},G)
usb.connected(FLAG,'#FLG02',15.24,43.18,{'1':'GND'},G)

for sh in [top,power,usb]: sh.save()
local=load(HW/'HapticBracelet.kicad_sym')
for key in [BQ,REG,CC,LIMIT,SEL]: local.append(copy.deepcopy(symbols[key]))
save(HW/'HapticBracelet.kicad_sym',local)
sl=load(HW/'sym-lib-table')
for name in ['Connector','Power_Protection','Transistor_FET','power']:
    if not any(child(e,'name')[1]==q(name) for e in children(sl,'lib')):
        sl.append(parse(f'(lib (name {q(name)}) (type "KiCad") (uri "${{KICAD10_SYMBOL_DIR}}/{name}.kicad_sym") (options "") (descr ""))'))
save(HW/'sym-lib-table',sl)
fl=load(HW/'fp-lib-table')
fl.append(parse('(lib (name "Package_TO_SOT_SMD") (type "KiCad") (uri "${KICAD10_FOOTPRINT_DIR}/Package_TO_SOT_SMD.pretty") (options "") (descr ""))'))
save(HW/'fp-lib-table',fl)
print('Added USB/power sheets and controller connections. Previous files backed up at',backup)
