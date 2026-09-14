"""Bounded layout correction after inspecting native KiCad SVG exports."""
from kicad_edit import *
top=Sheet('haptic-bracelet.kicad_sch')
for sh in children(top.a,'sheet'):
    if any(p[1:3]==[q('Sheetfile'),q('controller-support.kicad_sch')] for p in children(sh,'property')):
        at=child(sh,'at'); delta=223.52-float(at[2]);at[2]='223.52'
        for p in children(sh,'property'):
            pos=child(p,'at');pos[2]=str(round(float(pos[2])+delta,4))
child(child(top.a,'title_block'),'title')[1]=q('Controller and switched pod power')
top.save()
overview=Sheet('haptics.kicad_sch')
for sh in children(overview.a,'sheet'):
    for pin in children(sh,'pin'):
        if pin[1]==q('RING_TX'):child(child(pin,'effects'),'justify')[1]='right'
overview.save()
for i in range(8):
    pod=Sheet(f'pod_{i}.kicad_sch')
    for sym in children(pod.a,'symbol'):
        ref=uq(next(p[2] for p in children(sym,'property') if p[1]==q('Reference')))
        if ref in [f'U{18+i}',f'U{3+i}']:
            for p in children(sym,'property'):
                if p[1] in [q('Reference'),q('Value')]:child(p,'at')[1]=str(float(child(sym,'at')[1])+15.24)
        if ref==f'J{103+4*i}':
            for p in children(sym,'property'):
                if p[1] in [q('Reference'),q('Value')]:child(p,'at')[1]='365.76'
                if p[1]==q('Value'):p[2]=q('NTC (optional)')
    for label in children(pod.a,'hierarchical_label'):
        child(child(label,'effects'),'justify')[1]='right'
    pod.save()
for file in ['haptic-bracelet.kicad_sch','haptics.kicad_sch','controller-support.kicad_sch']+[f'pod_{i}.kicad_sch' for i in range(8)]:
    sh=Sheet(file);tb=child(sh.a,'title_block')
    child(tb,'date')[1]=q('2026-09-12');child(tb,'rev')[1]=q('0.3')
    child(tb,'comment')[2]=q('One wrist / ring pod schematic draft')
    sh.save()
