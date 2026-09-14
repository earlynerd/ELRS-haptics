"""Correct reset supply labels to the existing global pod rail."""
from kicad_edit import *
for i in range(8):
    sh=Sheet(f'pod_{i}.kicad_sch')
    for label in list(children(sh.a,'label')):
        if uq(label[1])=='POD_3V3':
            at=child(label,'at')
            sh.a.remove(label)
            sh.label('POD_3V3',tuple(map(float,at[1:3])),True,int(at[3]))
    sh.save()
