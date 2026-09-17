"""Check geometry and preserved electrical layout for the locating-hole edit."""
import json
from kicad_edit import *
from readable_schematic import props

def check(name):
 m=json.loads((HW/'mounting-layout.json').read_text())
 if m.get('revision')=='pod-faces-v1':
  from check_pod_faces import geometry
  return geometry(name)
 old=load(ROOT/m['backup']/name/(name+'.kicad_pcb'))
 new=load(HW/name/(name+'.kicad_pcb'))
 def fps(a):return {props(f)['Reference']:f for f in children(a,'footprint')}
 a,b=fps(old),fps(new)
 assert set(b)==set(a)|{'H1','H2'}
 for ref,f in a.items():
  assert child(f,'at')==child(b[ref],'at'),(ref,'placement changed')
  assert children(f,'pad')==children(b[ref],'pad'),(ref,'pads changed')
 # Native serialization may reformat numbers, so compare parsed numeric tokens.
 def norm(x):
  if isinstance(x,list):return tuple(norm(y) for y in x)
  try:return float(x)
  except ValueError:return x
 for kind in ['segment','via','arc']:
  assert {norm(x) for x in children(old,kind)}=={norm(x) for x in children(new,kind)},kind
 ox,oy=m['origins_mm'][name]
 for ref,(x,y) in m['locating_holes_local_mm'].items():
  f=b[ref];at=child(f,'at');assert abs(float(at[1])-ox-x)<1e-6 and abs(float(at[2])-oy-y)<1e-6
  pad=child(f,'pad');assert pad[2]=='np_thru_hole' and float(child(pad,'drill')[1])==2
  assert not children(pad,'net')
 edges=[x for x in new if isinstance(x,list) and x[0].startswith('gr_') and children(x,'layer') and uq(child(x,'layer')[1])=='Edge.Cuts']
 assert len(edges)==(8 if name=='main' else 16)
 points=[child(x,k) for x in edges for k in ['start','end'] if children(x,k)]
 assert abs(min(float(x[1]) for x in points)-ox)<1e-6
 assert abs(max(float(x[1]) for x in points)-ox-17)<1e-6
 assert abs(min(float(x[2]) for x in points)-oy)<1e-6
 assert abs(max(float(x[2]) for x in points)-oy-35)<1e-6
 return {'outline_mm':[17,35],'diagonal_holes_mm':m['locating_holes_local_mm'],'hole_diameter_mm':2,'electrical_placements_pads_and_routes_preserved':True}

if __name__=='__main__':
 import sys
 print(json.dumps(check(sys.argv[1]),indent=2))
