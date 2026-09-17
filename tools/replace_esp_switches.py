"""Prepare a bounded ESP recovery-pad and placement revision; never overwrite main."""
import copy, json, shutil, hashlib
from pathlib import Path
from kicad_edit import *

OUT=HW/'verification/main-recovery-pads';BACKUP=HW/'backups/pre-esp-recovery-pads-20260913'
OUT.mkdir(exist_ok=True);BACKUP.mkdir(exist_ok=False)
for f in (HW/'main').iterdir():
    if f.is_file():shutil.copy2(f,BACKUP/f.name)
hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in BACKUP.iterdir()}
(OUT/'input-hashes.json').write_text(json.dumps(hashes,indent=2))
for f in (HW/'main').iterdir():
    if f.suffix in ['.kicad_sch','.kicad_pro'] or f.name in ['fp-lib-table','sym-lib-table']:
        text=f.read_text(encoding='utf-8').replace('${KIPRJMOD}/../HapticBracelet','${KIPRJMOD}/../../HapticBracelet')
        (OUT/f.name).write_text(text,encoding='utf-8')

footprint='''(footprint "ESP_Recovery_3Pads_P1.5mm" (version 20241229) (generator "pcbnew")
 (layer "F.Cu") (descr "EN, GND, BOOT recovery probe pads; no paste, no fitted component")
 (attr smd exclude_from_pos_files exclude_from_bom)
 (property "Reference" "REF**" (at 0 -1.8 0) (layer "F.Fab") (effects (font (size .6 .6) (thickness .1))))
 (property "Value" "ESP RECOVERY" (at 0 1.8 0) (layer "F.Fab") (effects (font (size .6 .6) (thickness .1))))
 (fp_rect (start -2.2 -3.1) (end 2.2 .7) (stroke (width .05) (type default)) (fill none) (layer "F.CrtYd"))
'''
for i,name in enumerate(['EN','GND','BOOT'],1):
    x=(i-2)*1.5
    footprint+=f'(pad "{i}" smd circle (at {x} 0) (size 1 1) (layers "F.Cu" "F.Mask"))\n'
    footprint+=f'(fp_text user "{name}" (at {x} -1.8 90) (layer "F.SilkS") (effects (font (size .65 .65) (thickness .1))))\n'
footprint+=')\n'
(HW/'HapticBracelet.pretty/ESP_Recovery_3Pads_P1.5mm.kicad_mod').write_text(footprint)

sheet=Sheet('verification/main-recovery-pads/controller-support.kicad_sch')
def properties(s):return {uq(x[1]):uq(x[2]) for x in children(s,'property')}
old=next(s for s in children(sheet.a,'symbol') if properties(s).get('Reference')=='SW1')
sheet.path=uq(child(child(child(old,'instances'),'project'),'path')[1])
for s in list(children(sheet.a,'symbol')):
    if properties(s).get('Reference') in ['SW1','SW2','#PWR30016']:sheet.a.remove(s)
# Remove only branches that ran to the two switches. Keep reset RC and straps.
remove_ids={'06666efd-d56f-454c-b2a0-b5628b7209f2','87717af7-0a10-401b-b0a6-df0c17e49bc6',
 'f3cc776b-9f8d-405f-ab35-6bcd3cfb86c3','f92b240d-6867-4611-990b-7e947d55dba5',
 '10ac4dba-e8de-42cc-9924-9c1bbe0ffe0d','d8b2c88a-c105-4302-92f1-858bd4fde68e',
 'e251dfb9-a4f9-4994-93ad-13caa838b885','e7e7f13a-2cdf-41f8-9409-628da884cb29'}
for w in list(children(sheet.a,'wire')):
    if uq(child(w,'uuid')[1]) in remove_ids:sheet.a.remove(w)
key=stock('Connector_Generic','Conn_01x03')
pins=sheet.inst(key,'J3',215.9,86.36,value='ESP RECOVERY',footprint='HapticBracelet:ESP_Recovery_3Pads_P1.5mm',notes='Bare underside pads: 1 EN, 2 GND, 3 BOOT/GPIO9. Ground BOOT, pulse EN low, release EN then BOOT to enter ROM download. No connector fitted.')
j=next(s for s in children(sheet.a,'symbol') if properties(s).get('Reference')=='J3')
child(j,'in_bom')[1]='no';j.append(['in_pos_files','no']);child(child(j,'instances'),'project')[1]=q('main')
# Wired connector next to the reset RC, rather than detached global labels.
sheet.wire((195.58,66.04),(210.82,66.04));sheet.wire((210.82,66.04),pins['1'][0])
sheet.wire(pins['2'][0],(203.2,88.9));sheet.wire((203.2,88.9),(203.2,99.06));sheet.wire((203.2,99.06),(193.04,99.06))
sheet.wire(pins['3'][0],(233.68,91.44));sheet.wire((233.68,91.44),(233.68,66.04));sheet.wire((233.68,66.04),(264.16,66.04))
for x,y in [(193.04,66.04),(193.04,99.06)]:
    if not any(child(z,'at')[1:3]==[str(x),str(y)] for z in children(sheet.a,'junction')):
        sheet.add(f'(junction (at {x} {y}) (diameter 0) (color 0 0 0 0) (uuid {uid()}))')
sheet.text('UNDERSIDE RECOVERY PADS: 1 EN / 2 GND / 3 BOOT\nHold BOOT low; pulse EN low; release EN, then BOOT.',162.56,114.3,1)
sheet.save()
print('Prepared schematic and footprint; originals backed up to',BACKUP)
