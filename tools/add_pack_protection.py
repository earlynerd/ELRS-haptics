"""One-time native schematic migration: implement the selected high-side protector."""
from kicad_edit import *
import shutil, hashlib

backup = HW/'backups/before-pack-protection'
if backup.exists() or (HW/'protection.kicad_sch').exists():
    raise SystemExit('Protection migration already ran; edit the native files.')
backup.mkdir(parents=True)
for name in ['power.kicad_sch','HapticBracelet.kicad_sym','fp-lib-table']:
    shutil.copy2(HW/name, backup/name)

def props(s): return {uq(p[1]):uq(p[2]) for p in children(s,'property')}
def prop(s,k,v):
    ps=[p for p in children(s,'property') if uq(p[1])==k]
    if ps: ps[0][2]=q(v)
    else: s.append(parse(f'(property {q(k)} {q(v)} (at 0 0 0) {fx(hide=True)})'))

power=Sheet('power.kicad_sch')
existing=children(power.a,'symbol')[0]
power.path=uq(child(child(child(existing,'instances'),'project'),'path')[1])
# Remove the old placeholder and only its three label stubs.
j4=next(s for s in children(power.a,'symbol') if props(s).get('Reference')=='J4')
lib=next(s for s in children(child(power.a,'lib_symbols'),'symbol') if s[1]==child(j4,'lib_id')[1])
x,y=map(float,child(j4,'at')[1:3]); assert child(j4,'at')[3]=='0'
points={(round(x+float(child(p,'at')[1]),4),round(y-float(child(p,'at')[2]),4))
        for sub in children(lib,'symbol') for p in children(sub,'pin')}
ends=set()
for w in list(children(power.a,'wire')):
    wp={tuple(map(float,pt[1:3])) for pt in children(child(w,'pts'),'xy')}
    if points & wp: ends|=wp; power.a.remove(w)
for typ in ['label','global_label','no_connect']:
    for obj in list(children(power.a,typ)):
        if tuple(map(float,child(obj,'at')[1:3])) in points|ends: power.a.remove(obj)
power.a.remove(j4)
for t in list(children(power.a,'text')):
    if uq(t[1]).startswith('J4:'): power.a.remove(t)
    elif uq(t[1]).startswith('PACK BOUNDARY'):
        t[1]=q('PACK PROTECTION / see child sheet\nU27 S-821AAAC: 4.590 V OV / 2.500 V UV (prototype selection).\nVBAT_RAW remains live with pod power OFF; cells retain local fuses.\nJ3 carries protected terminals and the charger thermistor only.')
sid=uid()
power.add(f'(sheet (at 243.84 218.44) (size 144.78 25.4) (stroke (width 0.254) (type default)) (fill (color 0 0 0 0)) (uuid {sid}) (property "Sheetname" "High-side pack protection" (at 243.84 215.9 0) {fx()}) (property "Sheetfile" "protection.kicad_sch" (at 243.84 246.38 0) {fx()}) (instances (project "haptic-bracelet" (path {q(power.path)} (page "14")))))')
sh=Sheet('protection.kicad_sch',path=power.path+'/'+sid,title='High-side 1S pack protection')
sh.text('ONE CENTRAL PROTECTOR / COMMON GROUND / SIX-WIRE POD CHAIN',20.32,15.24,1.5)
sh.text('Raw parallel-cell bus -> shunt -> charge FET -> discharge FET -> BQ25186 BAT. All pack current uses this path.',20.32,25.4,1.0)

R=stock('Device','R'); C=stock('Device','C'); FLAG=stock('power','PWR_FLAG')
ds='https://www.ablic.com/en/doc/datasheet/battery_protection/S821AA_E.pdf'
U=custom('S-821AAAC-H8T7S',[
 ('A2','VDD',-22.86,12.7,0,'power_in'),('D1','VINI',-22.86,5.08,0,'input'),
 ('B1','TH',-22.86,-10.16,0,'input'),('A1','VSS',-22.86,-17.78,0,'power_in'),
 ('B2','CO',22.86,12.7,180,'output'),('C2','DO',22.86,5.08,180,'output'),
 ('D2','VM',22.86,-5.08,180,'input'),('C1','PS',22.86,-17.78,180,'input')],w=20.32,h=20.32,ds=ds)
# The CSD17318Q2 has the same physical pin map and DQK land pattern as this stock symbol.
base=stock('Transistor_FET','CSD16301Q2')
fet=copy.deepcopy(symbols[base]); fet[1]=q('CSD17318Q2')
for sub in children(fet,'symbol'): sub[1]=q(uq(sub[1]).replace('CSD16301Q2','CSD17318Q2'))
for k,v in [('Value','CSD17318Q2'),('Datasheet','https://www.ti.com/lit/ds/symlink/csd17318q2.pdf'),('Description','30 V N-channel MOSFET; D=1,2,5,6,8; G=3; S=4,7; TI DQK')]: prop(fet,k,v)
F='HapticBracelet:CSD17318Q2'; symbols[F]=fet
GN=('VBAT_RAW','BAT_PROTECTED','GND')
rp=sh.inst(R,'R54',81.28,66.04,value='0.003 1%',angle=90,footprint='Resistor_SMD:R_0805_2012Metric',
    mpn='D1MPC0805DR003FF-T5',manufacturer='Thin Film Technology Corp.',notes='3 mOhm 1%, 0.5 W. Kelvin route VDD/VINI to opposite pad edges. Prototype limit; verify against cells, wire and load.')
q6=sh.inst(F,'Q6',152.4,63.5,value='CSD17318Q2',angle=270,mpn='CSD17318Q2',manufacturer='Texas Instruments',notes='Charge control FET: source toward raw cell via R54, drain common with Q7.')
q7=sh.inst(F,'Q7',208.28,68.58,value='CSD17318Q2',angle=90,mpn='CSD17318Q2',manufacturer='Texas Instruments',notes='Discharge control FET: source toward protected pack, drain common with Q6.')
sh.wire((40.64,66.04),rp['1'][0]);sh.label('VBAT_RAW',(40.64,66.04),True,180)
sh.wire(rp['2'][0],q6['4'][0]); sh.label('PROT_SENSE',(104.14,66.04))
sh.wire(q6['1'][0],q7['1'][0]); sh.label('PROT_COMMON_DRAIN',(175.26,66.04))
sh.wire(q7['4'][0],(281.94,66.04)); sh.label('BAT_PROTECTED',(281.94,66.04),True)
sh.net(q6['3'][0],'PROT_CO',270);sh.net(q7['3'][0],'PROT_DO',90)
sh.text('CHARGE CONTROL',137.16,38.1,1);sh.text('DISCHARGE CONTROL',200.66,38.1,1)
sh.connected(U,'U27',160.02,132.08,{'A2':'VBAT_RAW','D1':'PROT_SENSE','B1':'PROT_VSS','A1':'PROT_VSS','B2':'PROT_CO','C2':'PROT_DO','D2':'PROT_VM'},GN,
    footprint='HapticBracelet:ABLIC_WLP-8V_1.08x1.52mm_P0.4x0.76mm',mpn='S-821AAAC-H8T7S',manufacturer='ABLIC Inc.',
    notes='Prototype-selected 4.590 V OV / 2.500 V UV. PS open; TH tied to VSS. No power-down or overheat function in this suffix.')
sh.passive(R,'R55','1k',60.96,157.48,'PROT_VSS','GND',GN,notes='ABLIC Figure 19 R1: reference/ESD resistor. No load current through this resistor; do not directly short U27 VSS to system GND.')
sh.passive(C,'C44','100n',60.96,111.76,'VBAT_RAW','PROT_VSS',GN,notes='ABLIC Figure 19 C1: directly across U27 VDD/VSS, not system GND.')
sh.passive(R,'R56','22',251.46,137.16,'BAT_PROTECTED','PROT_VM',GN,notes='ABLIC Figure 19 R2: VM input protection, close to U27.')
sh.connected(FLAG,'#FLG08',40.64,91.44,{'1':'VBAT_RAW'},GN)
sh.connected(FLAG,'#FLG09',86.36,157.48,{'1':'PROT_VSS'},GN)
sh.text('3 mOhm nominal trips: discharge 1.93 A / 128 ms; short 6.83 A / 280 us; charge 6.67 A / 32 ms.\n4.590 V overcharge / 512 ms; 2.500 V overdischarge / 64 ms. Delays and thresholds are nominal.\nCurrent thresholds are coupled by this suffix; charger current remains programmed separately.',20.32,190.5,1.0)
sh.text('LAYOUT: Kelvin sense R54 at its pads; keep U27/C44/R55 close. Common drains must not connect to another rail.\nPS has an explicit no-connect; TH ties to filtered VSS. No optional PS/TH features enabled.\nFault recovery: USB charger connection may be needed after cell connection, undervoltage or overload.\nSelected prototype OV threshold is above conventional 4.20 V cell limits; see docs/protection-sourcing.md.',20.32,218.44,1.0)

for s in children(sh.a,'symbol'):
    ref=props(s).get('Reference')
    if ref in ['Q6','Q7']: prop(s,'DigiKey','296-49599-1-ND')
    if ref=='R54':
        prop(s,'DigiKey','4463-D1MPC0805DR003FF-T5CT-ND')
        prop(s,'Datasheet','https://media.digikey.com/pdf/Data%20Sheets/Thin%20Film%20Tech%20PDFs/D1MPC%20Series.pdf')
    if ref=='U27': prop(s,'DigiKey','1662-S-821AAAC-H8T7SCT-ND')

slib=load(HW/'HapticBracelet.kicad_sym')
slib.extend([copy.deepcopy(symbols[U]),copy.deepcopy(symbols[F])])
save(HW/'HapticBracelet.kicad_sym',slib)
fp=load(HW/'fp-lib-table')
if not any(uq(child(l,'name')[1])=='Package_SON' for l in children(fp,'lib')):
    fp.append(parse('(lib (name "Package_SON") (type "KiCad") (uri "${KICAD10_FOOTPRINT_DIR}/Package_SON.pretty") (options "") (descr ""))'))
save(HW/'fp-lib-table',fp)

# ABLIC package bottom view is mirrored to PCB top view: A1 upper left, A2 upper right.
name='ABLIC_WLP-8V_1.08x1.52mm_P0.4x0.76mm'
f=f'(footprint "{name}" (version 20250114) (generator "pcbnew") (layer "F.Cu") (attr smd) (descr "ABLIC HV008-A-P-SD-2.0 and HV008-A-L-SD-1.0; S821AA Rev1.3 pp48,51; 0.18 mm lands")'
f+='(fp_text reference "REF**" (at 0 -1.4) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.1))))'
f+=f'(fp_text value "{name}" (at 0 1.4) (layer "F.Fab") (effects (font (size 0.6 0.6) (thickness 0.1))))'
f+='(fp_rect (start -0.54 -0.76) (end 0.54 0.76) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))'
f+='(fp_rect (start -0.81 -1.03) (end 0.81 1.03) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))'
f+='(fp_circle (center -0.67 -0.9) (end -0.60 -0.9) (stroke (width 0.1) (type default)) (fill solid) (layer "F.SilkS"))'
for row,yy in zip('ABCD',[-0.6,-0.2,0.2,0.6]):
    for col,xx in [(1,-0.38),(2,0.38)]:
        f+=f'(pad "{row}{col}" smd circle (at {xx} {yy}) (size 0.18 0.18) (layers "F.Cu" "F.Paste" "F.Mask") (solder_mask_margin 0.025))'
(HW/'HapticBracelet.pretty'/f'{name}.kicad_mod').write_text(f+')\n',encoding='utf-8')

manifest=json.loads((HW/'datasheets/manifest.json').read_text())
for mpn,file,url,maker in [
 ('S-821AAAC-H8T7S','S821AA.pdf',ds,'ABLIC Inc.'),
 ('CSD17318Q2','CSD17318Q2.pdf','https://www.ti.com/lit/ds/symlink/csd17318q2.pdf','Texas Instruments'),
 ('D1MPC0805DR003FF-T5','D1MPC.pdf','https://media.digikey.com/pdf/Data%20Sheets/Thin%20Film%20Tech%20PDFs/D1MPC%20Series.pdf','Thin Film Technology Corp.')]:
    data=(HW/'datasheets'/file).read_bytes()
    manifest['parts'][mpn]={'file':file,'datasheet_url':url,'manufacturer':maker,'status':'ok','retrieved':'2026-09-12','sha256':hashlib.sha256(data).hexdigest(),'size_bytes':len(data),'selection':'Implemented prototype pack protection; cell and bench qualification pending.'}
(HW/'datasheets/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
power.save();sh.save()
print('Replaced J4 with protection child sheet: U27, Q6/Q7, R54/R55/R56, C44; added ABLIC land pattern.')
