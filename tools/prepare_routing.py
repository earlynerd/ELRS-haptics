"""One-time 0.7 migration: power-cycle driver reset and sourced routing parts."""
from kicad_edit import *
import shutil,json
BACK=HW/'backups/before-routing'
assert not BACK.exists(),'Migration already applied; do not overwrite routing.'
BACK.mkdir()
for f in HW.glob('*.kicad_*'):shutil.copy2(f,BACK/f.name)
shutil.copytree(HW/'HapticBracelet.pretty',BACK/'HapticBracelet.pretty')
def props(s):return {uq(a[1]):uq(a[2]) for a in children(s,'property')}
def prop(s,k,v):
    a=next((x for x in children(s,'property') if uq(x[1])==k),None)
    if a:a[2]=q(v)
    else:s.append(parse(f'(property {q(k)} {q(v)} (at 0 0 0) (effects (font (size 1 1)) (hide yes)))'))
for i in range(8):
    sh=Sheet(f'pod_{i}.kicad_sch');b=100+10*i
    resistor=next(s for s in children(sh.a,'symbol') if props(s).get('Reference')==f'R{b+4}')
    sh.a.remove(resistor)
    # These isolated, labelled stubs have identical sheet coordinates in all pods.
    ends={(152.4,68.58),(228.6,176.53),(228.6,194.31)}
    removed=0
    for wire in list(children(sh.a,'wire')):
        points=[tuple(map(float,x[1:])) for x in child(wire,'pts')[1:]]
        if any(pt in ends for pt in points):sh.a.remove(wire);removed+=1
    assert removed==3,(i,removed)
    for label in list(children(sh.a,'label')+children(sh.a,'global_label')):
        at=tuple(map(float,child(label,'at')[1:3]))
        if at in ends:sh.a.remove(label)
        elif uq(label[1])=='DRV_nRESET':label[1]=q('POD_3V3')
    sh.nc((147.32,68.58)) # MCU PB13 is no longer connected to the haptic driver.
    for s in children(sh.a,'symbol'):
        ref=props(s).get('Reference')
        if ref==f'F{100+i}':
            for k,v in {'Value':'250mA FAST','MPN':'0467.250NR','Manufacturer':'Littelfuse','Footprint':'HapticBracelet:Fuse_Littelfuse_467_0603','Datasheet':'https://www.littelfuse.com/assetdocs/fuse-467-datasheet?assetguid=4a59f034-1cca-460e-a5ba-e1e66247c76d','DigiKey':'F1389CT-ND','BOM Comments':'250 mA secondary branch fuse, 0.565 ohm nominal cold resistance; factory PCM remains primary cell protection. Verify fault/pulse coordination on bench.'}.items():prop(s,k,v)
        if ref==f'U{18+i}':prop(s,'BOM Comments','Existing M2003 stock and robot loader pinout. PB13 is intentionally no-connect; driver NRST is tied to local VDD. Hard recovery power-cycles the switched pod rail.')
    for t in children(sh.a,'text'):
        val=uq(t[1])
        val=val.replace('PB13 is LOW in the existing LDROM, holding the driver in reset.','PB13 is unused. DRV NRST is tied to VDD; hard recovery cycles POD_3V3.')
        val=val.replace('PB13 LOW in loader; pod application releases/configures DRV2625.','Stop playback before loader entry. Application configures DRV2625; power-cycle for full reset.')
        t[1]=q(val)
    child(child(sh.a,'title_block'),'rev')[1]=q('0.7');sh.save()
for file in HW.glob('*.kicad_sch'):
    a=load(file)
    for s in children(a,'symbol'):
        if props(s).get('Reference')=='L1':
            prop(s,'Footprint','HapticBracelet:L_Murata_DFE201612E')
            prop(s,'Datasheet','https://search.murata.co.jp/Ceramy/image/img/P02/J(E)TE243A-0006.pdf')
            prop(s,'BOM Comments','Manufacturer drawing J(E)TE243A-0006D-01 p5: 2.4 mm outer span, 0.8 mm inner gap, 1.8 mm pad height. 0.47uH, 5.5A Isat, 4.5A thermal rating on vendor test board.')
    save(file,a)
# Copy/adjust the placed inductor proposal to the actual manufacturer land pattern.
lp=load(HW/'HapticBracelet.pretty/L_DFE201612E_Placement.kicad_mod');lp[1]=q('L_Murata_DFE201612E')
child(lp,'descr')[1]=q('Murata DFE201612E: manufacturer J(E)TE243A-0006D-01 p5. 0.8 x 1.8 mm pads, 1.6 mm pitch.')
for pad in children(lp,'pad'):
    child(pad,'size')[1:]=['0.8','1.8'];child(pad,'at')[1]=str(-.8 if uq(pad[1])=='1' else .8)
save(HW/'HapticBracelet.pretty/L_Murata_DFE201612E.kicad_mod',lp)
fuse='(footprint "Fuse_Littelfuse_467_0603" (version 20241229) (generator "pcbnew") (layer "F.Cu") (attr smd) (descr "Littelfuse 467 recommended reflow lands: 2.54 outer span, 1.02 gap, 1.09 height; 0603 body.") (property "Reference" "REF**" (at 0 -1.2 0) (layer "F.SilkS") (effects (font (size .8 .8) (thickness .12)))) (property "Value" "0467.250NR" (at 0 1.2 0) (layer "F.Fab") (effects (font (size .8 .8) (thickness .12)))) (fp_rect (start -.8 -.4065) (end .8 .4065) (stroke (width .1) (type default)) (fill none) (layer "F.Fab")) (fp_rect (start -1.5 -.8) (end 1.5 .8) (stroke (width .05) (type default)) (fill none) (layer "F.CrtYd"))'
for n,x in [('1',-.891),('2',.891)]:fuse+=f'(pad "{n}" smd rect (at {x} 0) (size .762 1.09) (layers "F.Cu" "F.Mask" "F.Paste"))'
(HW/'HapticBracelet.pretty/Fuse_Littelfuse_467_0603.kicad_mod').write_text(fuse+')\n')
print('Applied power-cycle reset and sourced parts; export netlist next.')
