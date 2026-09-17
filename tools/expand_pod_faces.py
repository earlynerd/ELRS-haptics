"""Expand both PCBA masters to enclosure faces; retain user electrical placement."""
import copy,json,shutil,math
from kicad_edit import *
from readable_schematic import props

BACK=HW/'backups/pre-pod-faces-20260915'
assert not BACK.exists(),'Migration already applied'
for name in ['main','satellite']:
 (BACK/name).mkdir(parents=True)
 for f in (HW/name).iterdir():
  if f.suffix in ['.kicad_pcb','.kicad_pro','.kicad_sch'] or f.name in ['fp-lib-table','sym-lib-table']:shutil.copy2(f,BACK/name/f.name)
shutil.copy2(HW/'mounting-layout.json',BACK/'mounting-layout.json')
origins={'main':(33.5,34.6),'satellite':(101.5,90.5)}
centres={'H1':(3.5,3.5),'H2':(16.5,3.5),'H3':(3.5,42.5),'H4':(16.5,42.5)}
libdir=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
mount_name='SMT_Standoff_M1p6_D3p3_ClosedBase_HeightTBD'
hole_name='Screw_Clearance_M1p6_1p8mm_Stack'
mount=load(libdir/'Mounting_Wuerth.pretty/Mounting_Wuerth_WA-SMSI-M1.6_H6mm_ThreadDepth2mm_NoNPTH_97730606330.kicad_mod')
mount[1]=q(mount_name)
child(mount,'descr')[1]=q('Wurth WA-SMSI M1.6 bottom-closed family: D3.3 body, D4 solder land. Height and final MPN pending stack selection. Land/paste copied from KiCad 97730606330, manufacturer drawing 97730606330R. Electrically isolated mechanical land.')
for x in list(children(mount,'model')):mount.remove(x)
for pad in children(mount,'pad'):pad[1]=q('')
for pr in children(mount,'property'):
 if uq(pr[1])=='Reference':child(pr,'layer')[1]=q('F.Fab')
 if uq(pr[1])=='Value':pr[2]=q('M1.6 STANDOFF H TBD')
mount.append(['zone_connect','2'])
save(HW/'HapticBracelet.pretty'/f'{mount_name}.kicad_mod',mount)
hole=parse(f'''(footprint "{hole_name}" (version 20260206) (generator "pcbnew") (layer "F.Cu")
 (descr "M1.6 clearance hole, 1.8 mm NPTH; D4.5 envelopes on both faces for head and mating standoff")
 (property "Reference" "REF**" (at 0 -3 0) (layer "F.Fab") (effects (font (size 1 1) (thickness .15))))
 (property "Value" "M1.6 CLEARANCE" (at 0 3 0) (layer "F.Fab") (effects (font (size 1 1) (thickness .15))))
 (attr exclude_from_pos_files exclude_from_bom) (zone_connect 2)
 (fp_circle (center 0 0) (end 1.65 0) (stroke (width .1) (type solid)) (fill none) (layer "F.Fab"))
 (fp_circle (center 0 0) (end 2.25 0) (stroke (width .05) (type solid)) (fill none) (layer "F.CrtYd"))
 (fp_circle (center 0 0) (end 2.25 0) (stroke (width .05) (type solid)) (fill none) (layer "B.CrtYd"))
 (pad "" np_thru_hole circle (at 0 0) (size 1.8 1.8) (drill 1.8) (layers "*.Cu" "*.Mask")) (embedded_fonts no))''')
save(HW/'HapticBracelet.pretty'/f'{hole_name}.kicad_mod',hole)

def rounded(b,ox,oy,w,h,r,layer,width=.05,dash='default'):
 def emit(kind,pts):
  s=' '.join(f'({k} {ox+x:.6f} {oy+y:.6f})' for k,x,y in pts)
  b.append(parse(f'(gr_{kind} {s} (stroke (width {width}) (type {dash})) (layer "{layer}") (uuid {uid()}))'))
 for x1,y1,x2,y2 in [(r,0,w-r,0),(w,r,w,h-r),(w-r,h,r,h),(0,h-r,0,r)]:emit('line',[('start',x1,y1),('end',x2,y2)])
 d=r/math.sqrt(2)
 for x,y,aa,bb in [(w-r,r,-90,0),(w-r,h-r,0,90),(r,h-r,90,180),(r,r,180,270)]:
  emit('arc',[(k,x+r*math.cos(math.radians(a)),y+r*math.sin(math.radians(a))) for k,a in [('start',aa),('mid',(aa+bb)/2),('end',bb)]])

def note(b,t,x,y,layer='Dwgs.User',size=.8):
 b.append(parse(f'(gr_text {q(t)} (at {x} {y}) (layer "{layer}") (uuid {uid()}) (effects (font (size {size} {size}) (thickness .12)) (justify left top)))'))

for name,sheetfile in [('main','pod-interface'),('satellite','satellite')]:
 sh=Sheet(name+'/'+sheetfile+'.kicad_sch');oldhs={props(s)['Reference']:s for s in children(sh.a,'symbol') if props(s)['Reference'] in centres}
 base=copy.deepcopy(oldhs['H1'])
 for s in oldhs.values():sh.a.remove(s)
 for t in list(children(sh.a,'text')):
  if uq(t[1]).startswith('H1/H2:'):sh.a.remove(t)
 b=load(HW/name/(name+'.kicad_pcb'))
 for f in list(children(b,'footprint')):
  if props(f)['Reference'] in centres:b.remove(f)
 for g in list(b):
  if isinstance(g,list) and g[0].startswith('gr_') and children(g,'layer') and uq(child(g,'layer')[1])=='Edge.Cuts':b.remove(g)
 ox,oy=origins[name]
 rounded(b,ox,oy,20,46,2.5,'Edge.Cuts')
 rounded(b,ox+1.2,oy+1.2,17.6,43.6,1.3,'Cmts.User',.1)
 rounded(b,ox+1.5,oy+1.5,17,43,1,'Dwgs.User',.1,'dash')
 for i,(ref,(x,y)) in enumerate(centres.items()):
  sym=copy.deepcopy(oldhs.get(ref,base))
  if ref not in oldhs:child(sym,'uuid')[1]=q(uid())
  sx,sy=(190.5+(i%2)*43.18,111.76+(i//2)*20.32) if name=='main' else (30.48+i*35.56,230)
  child(sym,'at')[1:]=[str(sx),str(sy),'0']
  value='M1.6 CLEARANCE' if name=='main' else 'M1.6 STANDOFF'
  fpname=hole_name if name=='main' else mount_name
  fields={'Reference':ref,'Value':value,'Footprint':'HapticBracelet:'+fpname,'Datasheet':'' if name=='main' else 'https://www.we-online.com/components/products/datasheet/97730606330R.pdf','BOM Comments':'M1.6 screw clearance; align to lower-board standoff.' if name=='main' else 'D3.3 closed-base solderable M1.6 family, D4 isolated land. Height/final MPN TBD; 6 mm family member is land-pattern reference only. TPU needs D4.6 local relief.'}
  for pr in children(sym,'property'):
   key=uq(pr[1]);pr[2]=q(fields.get(key,uq(pr[2])));child(pr,'at')[1:]=[str(sx+3.81),str(sy+(-2.54 if key=='Reference' else 0)),'0']
  child(sym,'in_bom')[1]='no' if name=='main' else 'yes'
  if children(sym,'in_pos_files'):child(sym,'in_pos_files')[1]='no' if name=='main' else 'yes'
  inst=child(child(sym,'instances'),'project');inst[1]=q(name);child(child(inst,'path'),'reference')[1]=q(ref)
  sh.a.append(sym)
  f=copy.deepcopy(hole if name=='main' else mount);f[1]=q('HapticBracelet:'+fpname)
  f.insert(2,['at',str(ox+x),str(oy+y)]);f.append(['uuid',q(uid())])
  path=uq(child(inst,'path')[1]);symuid=uq(child(sym,'uuid')[1]);f.append(['path',q(('/'+path.split('/')[-1] if name=='main' else '')+'/'+symuid)])
  f.append(['sheetname',q('/Stacked universal pod interface/' if name=='main' else '/')]);f.append(['sheetfile',q(sheetfile+'.kicad_sch')])
  for pr in children(f,'property'):
   if uq(pr[1]) in ['Reference','Value']:pr[2]=q(fields[uq(pr[1])])
  f.append(parse(f'(property "BOM Comments" {q(fields["BOM Comments"])} (at 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1) (thickness .15))))'))
  if fields['Datasheet']:f.append(parse(f'(property "Datasheet" {q(fields["Datasheet"])} (at 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1) (thickness .15))))'))
  b.append(f)
  # Proposed spacer relief, distinct from the copper or component clearance.
  b.append(parse(f'(gr_circle (center {ox+x} {oy+y}) (end {ox+x+2.3} {oy+y}) (stroke (width .1) (type dash)) (fill none) (layer "Cmts.User") (uuid {uid()}))'))
 sh.text('H1-H4: four corner M1.6 mounts.\n20 x 46 mm PCB faces / TPU spacer.\nStandoff height and screw length TBD.',172.72 if name=='main' else 25.4,148 if name=='main' else 245,1)
 sh.save()
 note(b,'20 x 46 mm POD FACE / R2.5\nCmts.User: TPU contact inner edge, 1.2 mm inset\nDwgs.User dashed: placement limit, 1.5 mm inset\nCorner circles: D4.6 TPU standoff relief\nHeight / screw length TBD; drawings are not copper keepouts',ox,oy+48)
 if name=='satellite':
  # Adhesive-mounted actuator body proposal in the former cutout; tails remain untouched.
  b.append(parse(f'(gr_rect (start {ox+8} {oy+17}) (end {ox+12} {oy+29}) (stroke (width .1) (type dash)) (fill none) (layer "Dwgs.User") (uuid {uid()}))'))
  note(b,'Dashed 4 x 12: LRA body proposal; factory tape\nM1 flex-contact placement remains to be adjusted',ox,oy+55)
 save(HW/name/(name+'.kicad_pcb'),b)

manifest={'revision':'pod-faces-v1','outline_mm':[20,46],'outer_corner_radius_mm':2.5,'outline_reference':'tools/build_myo_flat_v011.py: regular pod shell/lid 20 x 46 mm, R2.5','origins_mm':origins,'mount_centres_local_mm':centres,'tpu_contact_band_mm':1.2,'placement_inset_mm':1.5,'tpu_corner_relief_diameter_mm':4.6,'lower_standoff_thread':'M1.6','lower_standoff_body_diameter_mm':3.3,'lower_standoff_land_diameter_mm':4,'lower_standoff_footprint':'HapticBracelet:'+mount_name,'upper_clearance_hole_diameter_mm':1.8,'upper_clearance_footprint':'HapticBracelet:'+hole_name,'standoff_height_mm':None,'standoff_reference_mpn':'97730606330R (land pattern only; final height/MPN open)','main_actuator_cutout':False,'satellite_actuator_cutout':False,'component_positions':'Preserved from user saved sources on 2026-09-15; all existing electrical pads and routes unchanged','actuator':'Retain VLV041235L with supplied peel-and-stick tape; schematic M1 electrical contacts unchanged','backup':str(BACK.relative_to(ROOT))}
(HW/'mounting-layout.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps(manifest,indent=2))
