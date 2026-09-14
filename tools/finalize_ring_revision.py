"""Finish the distributed-cell revision's labels, notes and preview archive."""
from kicad_edit import *
import shutil
power=Sheet('power.kicad_sch')
for label in children(power.a,'global_label'):
    if uq(label[1])=='BAT_PROTECTED':
        label[0]='label';label.remove(child(label,'shape'))
for t in children(power.a,'text'):
    if uq(t[1]).startswith('J3 pin 3:'):
        t[1]=q('J3 pin 3: pack NTC to pin 4, selected for U11 TS profile.\nAdditional cell sensors are on pod sheets.\nNTC selection and charging supervision firmware remain open.')
tb=child(power.a,'title_block');child(tb,'date')[1]=q('2026-09-12');child(tb,'rev')[1]=q('0.3')
child(tb,'comment')[2]=q('One wrist / ring pod schematic draft')
power.save()
p=ROOT/'docs/power-architecture.md';s=p.read_text(encoding='utf-8')
s=s.replace('A pack protector with bidirectional disconnect separates','A pack protector with a high-side bidirectional disconnect separates')
s=s.replace('This is a functional diagram, not a completed protection schematic.','VBAT_RAW is the fifth conductor around the ring. Each pod has an optional cell connection and fuse provision. J4 on the power sheet exposes raw positive, protected positive and common GND for the still-unimplemented high-side protector.\n\nThis is a functional diagram, not a completed protection schematic.')
s=s.replace('the external pack protector and branch circuits are not yet implemented.','the high-side pack protector is still an interface boundary. Cell/fuse provisions are drawn on the pod sheets, with parts and ratings pending.')
p.write_text(s,encoding='utf-8')
# Preserve old preview files once; current sheets live in ring-revision/.
dest=HW/'backups/before-ring-pods/preview';dest.mkdir(exist_ok=True)
for p in (HW/'preview').iterdir():
    if p.is_file() and p.suffix in ['.png','.svg']:
        assert p.resolve().is_relative_to(HW.resolve()) and dest.resolve().is_relative_to(HW.resolve())
        if not (dest/p.name).exists():shutil.move(str(p),str(dest/p.name))
print('Finalized labels and archived superseded previews.')
