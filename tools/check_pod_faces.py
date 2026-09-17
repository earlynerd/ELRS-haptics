"""Check the enclosure-face edit against the user's saved electrical layout."""
import json,sys,hashlib,xml.etree.ElementTree as E
from kicad_edit import *
from readable_schematic import props
V=HW/'verification/project-split'
MECHANICAL={'H1','H2','H3','H4'}

def norm(x):
 if isinstance(x,list):return tuple(norm(y) for y in x)
 try:return float(x)
 except ValueError:return uq(x) if x.startswith('"') else x

def geometry(name):
 m=json.loads((HW/'mounting-layout.json').read_text());old=load(ROOT/m['backup']/name/(name+'.kicad_pcb'));new=load(HW/name/(name+'.kicad_pcb'))
 fps=lambda a:{props(f)['Reference']:f for f in children(a,'footprint')}
 a,b=fps(old),fps(new)
 assert set(b)==(set(a)-MECHANICAL)|MECHANICAL
 for ref in set(a)-MECHANICAL:
  assert norm(child(a[ref],'at'))==norm(child(b[ref],'at')),(ref,'moved')
  assert norm(child(a[ref],'layer'))==norm(child(b[ref],'layer')),(ref,'flipped')
  assert norm(children(a[ref],'pad'))==norm(children(b[ref],'pad')),(ref,'pads changed')
  assert a[ref][1]==b[ref][1],(ref,'footprint changed')
 for kind in ['segment','via','arc']:
  assert {norm(x) for x in children(old,kind)}=={norm(x) for x in children(new,kind)},kind
 ox,oy=m['origins_mm'][name]
 for ref,(x,y) in m['mount_centres_local_mm'].items():
  f=b[ref];at=child(f,'at');assert abs(float(at[1])-ox-x)<1e-6 and abs(float(at[2])-oy-y)<1e-6
  assert all(not children(p,'net') for p in children(f,'pad'))
  if name=='main':
   p=child(f,'pad');assert p[2]=='np_thru_hole' and float(child(p,'drill')[1])==1.8
  else:
   copper=[p for p in children(f,'pad') if q('F.Cu') in child(p,'layers')]
   assert len(copper)==1 and norm(child(copper[0],'size')[1:])==(4.,4.) and not children(copper[0],'drill')
 old_graphics={uq(child(x,'uuid')[1]) for x in old if isinstance(x,list) and x[0].startswith('gr_') and children(x,'uuid')}
 def edges(layer):return [x for x in new if isinstance(x,list) and x[0] in ['gr_line','gr_arc'] and uq(child(x,'layer')[1])==layer and uq(child(x,'uuid')[1]) not in old_graphics]
 def check_outline(layer,inset,radius):
  es=edges(layer);assert len(es)==8,(layer,len(es))
  pts=[child(e,k) for e in es for k in ['start','end']]
  bounds=[min(float(p[1]) for p in pts),min(float(p[2]) for p in pts),max(float(p[1]) for p in pts),max(float(p[2]) for p in pts)]
  assert all(abs(a-b)<1e-5 for a,b in zip(bounds,[ox+inset,oy+inset,ox+20-inset,oy+46-inset]))
  arcs=[e for e in es if e[0]=='gr_arc'];assert len(arcs)==4
  for e in arcs:
   s,z=child(e,'start'),child(e,'end');assert abs(abs(float(s[1])-float(z[1]))-radius)<1e-5
 check_outline('Edge.Cuts',0,2.5);check_outline('Cmts.User',1.2,1.3);check_outline('Dwgs.User',1.5,1)
 # This migration must preserve project settings, including the user's routing rules.
 assert json.loads((ROOT/m['backup']/name/(name+'.kicad_pro')).read_text())==json.loads((HW/name/(name+'.kicad_pro')).read_text())
 return {'outline_mm':[20,46],'corner_radius_mm':2.5,'mounts':m['mount_centres_local_mm'],'electrical_components_preserved':len(set(a)-MECHANICAL),'existing_electrical_placements_pads_and_routes_preserved':True,'actuator_cutouts':0,'tpu_contact_band_mm':1.2,'placement_inset_mm':1.5}

def check(name):
 g=geometry(name)
 def circuit(path):
  t=E.parse(path);cs={c.get('ref'):(c.findtext('value'),c.findtext('footprint')) for c in t.findall('components/comp') if c.get('ref') not in MECHANICAL}
  ns={frozenset((n.get('ref'),n.get('pin')) for n in net.findall('node') if n.get('ref') in cs) for net in t.findall('nets/net')};ns.discard(frozenset());return cs,ns
 assert circuit(HW/f'verification/pod-faces/before-{name}.xml')==circuit(V/f'{name}.xml')
 erc=json.loads((V/f'{name}-erc.json').read_text());items=[v for s in erc['sheets'] for v in s['violations']];assert not items,items
 drc=json.loads((V/f'{name}-drc.json').read_text());assert not drc['schematic_parity'],drc['schematic_parity']
 if name=='satellite':assert not drc['violations'] and not drc['unconnected_items']
 result={'status':'PRESERVATION PASS; USER PLACEMENT IN PROGRESS' if name=='main' else 'PASS','project':name,'geometry':g,'electrical_circuit_preserved':True,'erc_violations':0,'schematic_parity':0,'drc_violations':len(drc['violations']),'open_connections':len(drc['unconnected_items']),'remaining_drc':[{'type':v['type'],'items':[i['description'] for i in v['items']]} for v in drc['violations']],'standoff_height':'TBD; family land pattern only','pcb_sha256':hashlib.sha256((HW/name/(name+'.kicad_pcb')).read_bytes()).hexdigest()}
 (V/f'{name}-checks.json').write_text(json.dumps(result,indent=2)+'\n')
 (HW/f'verification/pod-faces/{name}-checks.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='remaining_drc'},indent=2))

if __name__=='__main__':check(sys.argv[1])
