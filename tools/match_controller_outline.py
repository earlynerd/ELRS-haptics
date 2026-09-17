"""Copy the universal pod perimeter and add two diagonal locating holes."""
import copy,json
from kicad_edit import *
from readable_schematic import props
BACK=HW/'backups/pre-matched-outlines-20260914'
assert not (HW/'mounting-layout.json').exists(),'Already applied'
origins={'main':(35,40.1),'satellite':(103,96)}
local={'H1':(15,1.8),'H2':(2.5,32.5)}
key=stock('Mechanical','MountingHole')
template=load(Path('C:/Program Files/KiCad/10.0/share/kicad/footprints/MountingHole.pretty/MountingHole_2mm.kicad_mod'))
symbol_data={}
for name,file in [('main','pod-interface'),('satellite','satellite')]:
 sh=Sheet(name+'/'+file+'.kicad_sch')
 ex=next(s for s in children(sh.a,'symbol') if not props(s)['Reference'].startswith('#'))
 sh.path=uq(child(child(child(ex,'instances'),'project'),'path')[1])
 for i,ref in enumerate(local):
  x,y=(195.58+i*35.56,124.46) if name=='main' else (30.48+i*35.56,228.6)
  sh.inst(key,ref,x,y,value='2mm LOCATING',footprint='MountingHole:MountingHole_2mm',notes='Unplated locating hole; diagonally opposed pair shared by both PCBAs. Printed ledges/lid provide support and retention.')
  s=children(sh.a,'symbol')[-1];child(child(s,'instances'),'project')[1]=q(name);child(s,'in_bom')[1]='no';s.append(['in_pos_files','no'])
  symbol_data[(name,ref)]=(copy.deepcopy(s),sh.path,file)
 sh.text('H1/H2: diagonal locating holes shared by both boards.\nPrinted supports/lid retain the boards; no screw head assumed.',172.72 if name=='main' else 25.4,139.7 if name=='main' else 243.84,1)
 sh.save()

sat=load(BACK/'satellite/satellite.kicad_pcb')
outer=[]
for item in sat:
 if not isinstance(item,list) or not item[0].startswith('gr_') or not children(item,'layer') or uq(child(item,'layer')[1])!='Edge.Cuts':continue
 pts=[child(item,k) for k in ['start','mid','end'] if children(item,k)]
 if any(float(pt[1])<=104 or float(pt[1])>=119 or float(pt[2])<=97 or float(pt[2])>=130 for pt in pts):outer.append(item)
assert len(outer)==8
for name in ['main','satellite']:
 b=load(BACK/name/(name+'.kicad_pcb'))
 if name=='main':
  for item in list(b):
   if isinstance(item,list) and item[0].startswith('gr_') and children(item,'layer') and uq(child(item,'layer')[1])=='Edge.Cuts':b.remove(item)
  dx,dy=origins['main'][0]-origins['satellite'][0],origins['main'][1]-origins['satellite'][1]
  for edge in outer:
   e=copy.deepcopy(edge);child(e,'uuid')[1]=q(uid())
   for k in ['start','mid','end']:
    if children(e,k):
     a=child(e,k);a[1:]=[str(round(float(a[1])+dx,6)),str(round(float(a[2])+dy,6))]
   b.append(e)
 for ref,(x,y) in local.items():
  s,path,file=symbol_data[(name,ref)];f=copy.deepcopy(template);f[1]=q('MountingHole:MountingHole_2mm')
  f.insert(2,['at',str(round(origins[name][0]+x,6)),str(round(origins[name][1]+y,6))])
  f.append(['uuid',q(uid())]);f.append(['path',q('/'.join(path.split('/')[2:])+'/'+uq(child(s,'uuid')[1]) if name=='main' else '/'+uq(child(s,'uuid')[1]))])
  if name=='main':child(f,'path')[1]=q('/'+path.split('/')[-1]+'/'+uq(child(s,'uuid')[1]))
  f.append(['sheetname',q('/Stacked universal pod interface/' if name=='main' else '/')]);f.append(['sheetfile',q(file+'.kicad_sch')])
  for pr in children(f,'property'):
   if uq(pr[1])=='Reference':pr[2]=q(ref)
   if uq(pr[1])=='Value':pr[2]=q('2mm LOCATING')
   if uq(pr[1])=='Reference':
    child(pr,'layer')[1]=q('F.Fab')
  # Carry user-visible symbol fields through to PCB parity.
  notes=props(s)['BOM Comments']
  f.append(parse(f'(property "BOM Comments" {q(notes)} (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1) (thickness .15))))'))
  b.append(f)
 save(HW/name/(name+'.kicad_pcb'),b)
manifest={'outline_mm':[17,35],'outer_corner_radius_mm':1,'origins_mm':origins,'locating_holes_local_mm':local,'hole_diameter_mm':2,'holes':'non-plated','component_positions':'unchanged; user will rearrange controller and any affected pod parts','main_actuator_cutout':False,'satellite_actuator_cutout':True,'backup':str(BACK.relative_to(ROOT))}
(HW/'mounting-layout.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
