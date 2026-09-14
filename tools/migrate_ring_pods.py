"""One-time native schematic migration. Never rerun over edited pod sheets."""
from kicad_edit import *
import shutil

if (HW/'pod_0.kicad_sch').exists():
    raise SystemExit('Ring pods already exist; edit the native schematics instead.')
backup=HW/'backups/before-ring-pods'
backup.mkdir(parents=True,exist_ok=False)
for p in HW.iterdir():
    if p.is_file() and (p.suffix.startswith('.kicad_') or p.name.endswith('-table')):
        shutil.copy2(p,backup/p.name)

R=stock('Device','R'); C=stock('Device','C')
ESP=stock('RF_Module','ESP32-C6-MINI-1'); FET=stock('Transistor_FET','2N7002')
SW=stock('Switch','SW_Push')
CON={n:stock('Connector_Generic',f'Conn_01x{n:02}') for n in [2,4,5,6]}
lib=load(HW/'HapticBracelet.kicad_sym')
for s in children(lib,'symbol'): symbols['HapticBracelet:'+uq(s[1])]=copy.deepcopy(s)
DRV='HapticBracelet:DRV2625_YFF'; ACT='HapticBracelet:Actuator_TBD'
# Nuvoton M2003 series datasheet Rev 1.00, TSSOP20 pin assignment.
left=[('4','PE15 / nRESET','input'),('18','PF1 / RXD1 / ICE_CLK','bidirectional'),
      ('8','PF0 / TXD1 / ICE_DAT','bidirectional'),('2','PB2 / ADC0_CH2','bidirectional'),
      ('1','PB1','bidirectional'),('3','PB3','bidirectional'),('20','PB0','bidirectional'),('10','PC14','bidirectional')]
right=[('5','PB4 / I2C0_SDA','bidirectional'),('6','PB5 / I2C0_SCL','bidirectional'),
       ('13','PB13','bidirectional'),('11','PB15','bidirectional'),('12','PB14','bidirectional'),
       ('14','PB12','bidirectional'),('15','PB7','bidirectional'),('16','PB8','bidirectional'),
       ('17','PB9','bidirectional'),('19','PB11','bidirectional')]
pins=[]
for group,x,ang in [(left,-30.48,0),(right,30.48,180)]:
    pins += [(num,nm,x,22.86-i*5.08,ang,typ) for i,(num,nm,typ) in enumerate(group)]
pins += [('9','VDD',0,30.48,270,'power_in'),('7','VSS',0,-30.48,90,'power_in')]
MCU=custom('M2003FC1AE',pins,w=27.94,h=27.94,ds='https://www.nuvoton.com/export/resource-files/en-us--DS_M2003_Series_EN_Rev1.00.pdf')
PWR=custom('TPS22918DBV',[
 ('1','VIN',-15.24,7.62,0,'power_in'),('3','ON',-15.24,0,0,'input'),
 ('4','CT',-15.24,-7.62,0,'passive'),('2','GND',0,-15.24,90,'power_in'),
 ('6','VOUT',15.24,7.62,180,'power_out'),('5','QOD',15.24,-7.62,180,'passive')],
 ds='https://www.ti.com/lit/ds/symlink/tps22918.pdf')
for key in [MCU,PWR]: lib.append(copy.deepcopy(symbols[key]))

top=Sheet('haptic-bracelet.kicad_sch'); rid=child(top.a,'uuid')[1]; top.path='/'+rid
old_sheets={uq(next(p[2] for p in children(s,'property') if p[1]==q('Sheetfile'))):s for s in children(top.a,'sheet')}
hid=child(old_sheets['haptics.kicad_sch'],'uuid')[1]
def clear(sh,title):
    sh.a[:]=[a for a in sh.a if not isinstance(a,list) or a[0] in ['version','generator','uuid','paper','sheet_instances','embedded_fonts']]
    sh.add('(lib_symbols)')
    sh.add(f'(title_block (title {q(title)}) (date "2026-09-11") (rev "0.3") (comment 1 "One wrist / eight ring pods / schematic draft"))')
def block(sh,file,name,x,y,w,h,page,ident=None,ports=()):
    ident=ident or uid()
    s=f'(sheet (at {x} {y}) (size {w} {h}) (stroke (width 0.254) (type default)) (fill (color 0 0 0 0)) (uuid {ident})'
    s+=f'(property "Sheetname" {q(name)} (at {x} {y-2.54} 0) {fx()})'
    s+=f'(property "Sheetfile" {q(file)} (at {x} {y+h+2.54} 0) {fx()})'
    for name,typ,px,py,ang in ports:
        s+=f'(pin {q(name)} {typ} (at {px} {py} {ang}) {fx()} (uuid {uid()}))'
    s+=f'(instances (project "haptic-bracelet" (path {q(sh.path)} (page {q(page)})))))'
    sh.add(s); return ident
clear(top,'Haptic bracelet - controller, switched ring supply and reset')
G=['3V3','POD_3V3','GND','RING_nRESET','RING_D0','RING_D8','POD_POWER_ON','RING_RESET_ASSERT',
   'I2C_SDA','I2C_SCL','CC_nINT','VBUS_nPRESENT','USB_D_N','USB_D_P','USB_INPUT_OFF',
   'CHG_ALLOW','CHG_nINT','USB_LIMIT_ENABLE','USB_LIMIT_HIGH']
top.text('ATTITUDE FEEDBACK / ESP32 MASTER + EIGHT UART RING PODS',15.24,12.7,2.54)
top.text('250 kbaud: ESP TX -> pod 0 -> ... -> pod 7 -> ESP RX. Shared MCU reset; local driver control in each pod.',15.24,22.86)
mapping={'3':'3V3','1':'GND','8':'MCU_EN','15':'I2C_SDA','16':'I2C_SCL','24':'RING_RESET_ASSERT',
 '25':'RING_TX_MCU','5':'RING_D8','6':'POD_POWER_ON','22':'BOOT_IO8','23':'BOOT_IO9','30':'UART_RX','31':'UART_TX',
 '12':'CC_nINT','13':'VBUS_nPRESENT','17':'USB_D_N','18':'USB_D_P','19':'USB_INPUT_OFF',
 '26':'CHG_ALLOW','27':'CHG_nINT','28':'USB_LIMIT_ENABLE','29':'USB_LIMIT_HIGH'}
top.connected(ESP,'U1',73.66,83.82,mapping,G)
top.text('GPIO19 ring TX / GPIO2 ring RX\nGPIO18 high asserts pod reset\nGPIO3 high powers pods\nGPIO6/7: main-board power/USB I2C only',20.32,129.54)
block(top,'haptics.kicad_sch','Eight ring pods',294.64,50.8,86.36,25.4,2,hid)
block(top,'power.kicad_sch','Charger and regulated supply',294.64,96.52,86.36,25.4,11,child(old_sheets['power.kicad_sch'],'uuid')[1])
block(top,'usb.kicad_sch','USB-C data and power',294.64,142.24,86.36,25.4,12,child(old_sheets['usb.kicad_sch'],'uuid')[1])
top.connected(CON[6],'J1',342.9,203.2,dict(zip(map(str,range(1,7)),['3V3','GND','UART_TX','UART_RX','BOOT_IO9','MCU_EN'])),G,value='ESP UART / BOOT / RESET',footprint='')
top.passive(R,'R42','33',190.5,45.72,'RING_TX_MCU','RING_D0',G)
top.passive(R,'R43','100k',241.3,45.72,'RING_TX_MCU','GND',G)
top.text('TX pulldown keeps the ring quiet while U1 resets.\nBefore pod power OFF: reset pods, detach UART, TX low;\nRX input with pull-up disabled. No signal isolators.',149.86,63.5,1)
top.connected(FET,'Q5',200.66,111.76,{'1':'RING_RESET_ASSERT','2':'GND','3':'RESET_D'},G,
 notes='Open drain shared pod reset; pull-up is on switched rail.')
top.passive(R,'R44','100',241.3,109.22,'RING_nRESET','RESET_D',G)
top.passive(R,'R6','10k',154.94,109.22,'POD_3V3','RING_nRESET',G)
top.passive(R,'R7','100k',200.66,154.94,'RING_RESET_ASSERT','GND',G)
top.passive(C,'C40','10u 10V',154.94,154.94,'RING_nRESET','GND',G,footprint='Capacitor_SMD:C_0805_2012Metric')
top.text('One shared 10k / 10u reset network.\n100 ohm limits Q5 discharge pulse.\nAllow reset RC to rise before loader traffic.',226.06,137.16,1)
top.connected(PWR,'U26',88.9,200.66,{'1':'3V3','2':'GND','3':'POD_POWER_ON','4':'POD_SLEW','5':'POD_QOD','6':'POD_3V3'},G,
 footprint='Package_TO_SOT_SMD:SOT-23-6',mpn='TPS22918DBVR',manufacturer='Texas Instruments',notes='Switched 3.3V for all pod MCUs and drivers. 2A ceiling, no current limit or reverse blocking; budget pending.')
for key,ref,val,x,y,n1,n2 in [(C,'C41','1u',25.4,205.74,'3V3','GND'),(R,'R45','100k',25.4,251.46,'POD_POWER_ON','GND'),
 (C,'C42','1n 25V',76.2,251.46,'POD_SLEW','GND'),(R,'R46','100',139.7,200.66,'POD_3V3','POD_QOD'),
 (C,'C43','1u',139.7,251.46,'POD_3V3','GND')]: top.passive(key,ref,val,x,y,n1,n2,G)
top.text('POD SUPPLY: default OFF; ESP, USB and charger stay powered.\nCT controls ramp; QOD discharges the ring after shutdown.\nDo not enable UART idle-high until POD_3V3 has settled.\nDisable charging before removing required pod temperature sensing.',177.8,241.3,1)
# Controller support kept on a separate sheet for readable spacing.
sid=block(top,'controller-support.kicad_sch','ESP reset, boot and decoupling',294.64,238.76,86.36,22.86,13)
support=Sheet('controller-support.kicad_sch',top.path+'/'+sid,'ESP32 controller support')
support.text('ESP32 SUPPORT / ALWAYS-POWERED 3V3 DOMAIN',20.32,20.32,2.54)
SG=G+['MCU_EN','BOOT_IO8','BOOT_IO9','UART_TX','UART_RX']
# Root support nets now cross a sheet boundary.
for lab in children(top.a,'label'):
    if uq(lab[1]) in SG:
        lab[0]='global_label'; lab.insert(2,parse('(shape bidirectional)'))
for key,ref,val,x,y,n1,n2 in [(R,'R1','4.7k',40.64,63.5,'3V3','I2C_SDA'),(R,'R2','4.7k',91.44,63.5,'3V3','I2C_SCL'),
 (R,'R3','10k',142.24,63.5,'3V3','MCU_EN'),(C,'C1','1u',193.04,63.5,'MCU_EN','GND'),
 (R,'R4','10k',243.84,63.5,'3V3','BOOT_IO8'),(R,'R5','10k',294.64,63.5,'3V3','BOOT_IO9'),
 (C,'C2','100n',40.64,114.3,'3V3','GND'),(C,'C3','10u',91.44,114.3,'3V3','GND')]:support.passive(key,ref,val,x,y,n1,n2,SG)
support.connected(SW,'SW1',193.04,114.3,{'1':'MCU_EN','2':'GND'},SG,value='ESP RESET',footprint='')
support.connected(SW,'SW2',294.64,114.3,{'1':'BOOT_IO9','2':'GND'},SG,value='ESP BOOT',footprint='')
support.text('C2/C3 adjacent to U1 supply pins. GPIO8/9 retain ESP32 boot straps.\nMain I2C pull-ups serve only the USB-C controller and charger.\nPOD_POWER_ON has an external pulldown on the controller sheet.',20.32,154.94)

overview=Sheet('haptics.kicad_sch',top.path+'/'+hid); clear(overview,'Haptic bracelet - UART ring wiring')
overview.text('EIGHT PODS / ONE FORWARDED UART DATA WIRE PER GAP',20.32,15.24,2.54)
overview.text('Each pod: M2003FC1AE + DRV2625 + LRA. Pod 0 shares its housing with the ESP32/power electronics.',20.32,27.94)
overview.text('IN/OUT pin order: 1 POD_3V3, 2 GND, 3 DATA, 4 RING_nRESET. Battery branch wiring is additional.',20.32,35.56)
overview.text('ESP TX -> D0 -> pod 0 -> D1 -> ... -> pod 7 -> D8 -> ESP RX\nPower, ground and reset are common; DATA is point-to-point, not a multidrop net.\nWiring is represented electrically here; physical closure, pad geometry and panelization remain open.',20.32,228.6)
for i in range(8):
    x=35.56+(i%4)*93.98; y=68.58+(i//4)*83.82; w=60.96; h=40.64
    ports=[('RING_RX','input',x,y+15.24,180),('RING_TX','output',x+w,y+25.4,0)]
    pid=block(overview,f'pod_{i}.kicad_sch',f'Pod {i} / U{18+i}',x,y,w,h,3+i,ports=ports)
    overview.net((x,y+15.24),f'RING_D{i}',0,True)
    overview.net((x+w,y+25.4),f'RING_D{i+1}',180,True)
    pod=Sheet(f'pod_{i}.kicad_sch',overview.path+'/'+pid,f'Pod {i} - M2003, local driver and actuator')
    PG=['POD_3V3','GND','RING_nRESET']
    pod.text(f'POD {i} / M2003 UART RING NODE + LOCAL HAPTIC DRIVER',15.24,12.7,2.54)
    pod.text('PF0/PF1 preserve UART1 and ICE debug pins. PB13 is LOW in the existing LDROM, holding the driver in reset.',15.24,22.86)
    pod.connected(MCU,f'U{18+i}',116.84,81.28,{'9':'POD_3V3','7':'GND','4':'RING_nRESET','18':'UART_RX_LOCAL',
      '8':'UART_TX_LOCAL','5':'LOCAL_SDA','6':'LOCAL_SCL','13':'DRV_nRESET','2':'CELL_TEMP'},PG,
      footprint='Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm',mpn='M2003FC1AE',manufacturer='Nuvoton',
      notes='Existing stock. Preserve robot LDROM startup outputs; unused PB1/PB7/PB8/PB9/PB11/PB12 stay unconnected.')
    pod.connected(DRV,f'U{3+i}',276.86,76.2,{'B1':'LOCAL_SDA','C1':'LOCAL_SCL','B2':'DRV_nRESET','A1':'GND',
      'C2':'POD_3V3','B3':'GND','A2':'DRV_REG','A3':'LRA_P','C3':'LRA_N'},PG,value='DRV2625',footprint='')
    pod.connected(ACT,f'M{i+1}',360.68,71.12,{'1':'LRA_P','2':'LRA_N'},PG,value='LRA TBD',footprint='')
    for key,ref,val,x,y,n1,n2 in [(R,f'R{8+2*i}','4.7k',228.6,129.54,'POD_3V3','LOCAL_SDA'),
      (R,f'R{9+2*i}','4.7k',269.24,129.54,'POD_3V3','LOCAL_SCL'),
      (C,f'C{5+3*i}','100n',309.88,129.54,'POD_3V3','GND'),(C,f'C{6+3*i}','100n',350.52,129.54,'DRV_REG','GND'),
      (C,f'C{7+3*i}','1u',391.16,129.54,'POD_3V3','GND')]:pod.passive(key,ref,val,x,y,n1,n2,PG)
    b=100+10*i; j=100+4*i
    for key,ref,val,x,y,n1,n2 in [(R,f'R{b}','0',45.72,147.32,'RING_RX','UART_RX_LOCAL'),
      (R,f'R{b+1}','33',91.44,147.32,'UART_TX_LOCAL','RING_TX'),
      (R,f'R{b+2}','100k',137.16,147.32,'POD_3V3','UART_RX_LOCAL'),
      (R,f'R{b+3}','100k',182.88,147.32,'POD_3V3','UART_TX_LOCAL'),
      (R,f'R{b+4}','10k',228.6,185.42,'DRV_nRESET','GND'),
      (C,f'C{b}','100n',45.72,195.58,'POD_3V3','GND'),(C,f'C{b+1}','10u',91.44,195.58,'POD_3V3','GND'),
      (R,f'R{b+5}','10k 1%',289.56,190.5,'POD_3V3','CELL_TEMP'),(C,f'C{b+2}','10n',340.36,190.5,'CELL_TEMP','GND')]:
        pod.passive(key,ref,val,x,y,n1,n2,PG,footprint='Capacitor_SMD:C_0805_2012Metric' if ref==f'C{b+1}' else None)
    for nm,py,typ in [('RING_RX',45.72,'input'),('RING_TX',60.96,'output')]:
        pod.add(f'(hierarchical_label {q(nm)} (at 30.48 {py} 0) (shape {typ}) {fx()} (uuid {uid()}))')
        pod.wire((30.48,py),(43.18,py));pod.label(nm,(43.18,py))
    for off,nm,x,net in [(0,'RING IN',45.72,'RING_RX'),(1,'RING OUT',106.68,'RING_TX')]:
        pod.connected(CON[4],f'J{j+off}',x,248.92,{'1':'POD_3V3','2':'GND','3':net,'4':'RING_nRESET'},PG,value=nm,footprint='')
    pod.connected(CON[5],f'J{j+2}',187.96,248.92,{'1':'POD_3V3','2':'GND','3':'UART_TX_LOCAL','4':'UART_RX_LOCAL','5':'RING_nRESET'},PG,
      value='ICE / INITIAL FLASH',footprint='',notes='VTref, GND, ICE_DAT, ICE_CLK, nRESET. Remove RX and TX series links for debug. VTref is sense only.')
    pod.connected(CON[2],f'J{j+3}',388.62,190.5,{'1':'CELL_TEMP','2':'GND'},PG,value='CELL NTC (optional)',footprint='',notes='External 10k NTC candidate; fit only at cell locations. Curve/thresholds pending. Separate from charger PACK_TS thermistor.')
    pod.text(f'INITIAL FLASH / DEBUG: remove R{b} and R{b+1} to isolate both ICE pins from the ring.\nRestore links for operation. Shared reset resets every connected pod.\nUse normal switched supply; debug VTref is not a power input.',228.6,238.76,1)
    pod.text('C100-family decoupling adjacent to MCU VDD.\nNTC reads require pod power; absent/open sensor reads high.\nPB13 LOW in loader; pod application releases/configures DRV2625.',228.6,213.36,1)
    pod.save()

for sh in [top,support,overview]: sh.save()
save(HW/'HapticBracelet.kicad_sym',lib)
fl=load(HW/'fp-lib-table')
if not any(child(e,'name')[1]==q('Package_SO') for e in children(fl,'lib')):
    fl.append(parse('(lib (name "Package_SO") (type "KiCad") (uri "${KICAD10_FOOTPRINT_DIR}/Package_SO.pretty") (options "") (descr ""))'))
save(HW/'fp-lib-table',fl)
# Page references are prose only; hierarchy paths and USB/power circuit stay intact.
power=Sheet('power.kicad_sch')
for t in children(power.a,'text'):
    t[1]=q(uq(t[1]).replace('on sheet 4','on the USB-C sheet'))
power.save()
pro=HW/'haptic-bracelet.kicad_pro'; data=json.loads(pro.read_text())
data['text_variables']['DESIGN_STATUS']='RING POD SCHEMATIC - FIRMWARE, PACK AND LAYOUT PENDING'
pro.write_text(json.dumps(data,indent=2)+'\n')
print('Migrated to eight M2003 ring pods and firmware-sequenced switched pod power. Backup:',backup)
