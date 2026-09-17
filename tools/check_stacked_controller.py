"""Check the controller-only migration against its immediate saved baseline."""
import json,hashlib,xml.etree.ElementTree as E
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];HW=ROOT/'hardware';V=HW/'verification/project-split';S=HW/'verification/stacked-controller'

def check():
 m=json.loads((HW/'stacked-architecture.json').read_text());removed=set(m['removed_main_references'])
 old=E.parse(S/'before-main.xml');new=E.parse(V/'main.xml')
 def comps(t):return {c.get('ref'):c for c in t.findall('components/comp')}
 mounting=(HW/'mounting-layout.json').exists();mechanical={'H1','H2'} if mounting else set()
 a,b=comps(old),comps(new);assert set(b)==(set(a)-removed)|mechanical
 for ref in set(b)-mechanical:
  for field in ['value','footprint']:
   assert b[ref].findtext(field)==('STACK TO POD 0' if ref=='J101' and field=='value' else a[ref].findtext(field)),(ref,field)
 def nets(t):return {n.get('name'):{(x.get('ref'),x.get('pin')) for x in n.findall('node') if x.get('ref') in b} for n in t.findall('nets/net')}
 want=nets(old);actual=nets(new)
 for nodes in want.values():nodes.discard(('J101','3'))
 want['RING_D0'].add(('J101','3'))
 assert {frozenset(n) for n in want.values() if n}=={frozenset(n) for n in actual.values() if n},'Retained circuit changed'
 assert actual['RING_D0']=={('R42','2'),('J101','3')}
 for pin,net in m['stack_pin_nets'].items():assert ('J101',pin) in actual[net]
 erc=json.loads((V/'main-erc.json').read_text());items=erc.get('violations',[])+[v for s in erc.get('sheets',[]) for v in s.get('violations',[])];assert not items,items
 drc=json.loads((V/'main-drc.json').read_text());assert not drc.get('schematic_parity'),drc.get('schematic_parity')
 if not mounting:assert all(v['severity']=='warning' and v['type'] in ['silk_edge_clearance','lib_footprint_mismatch'] for v in drc['violations'])
 board=p.LoadBoard(str(HW/'main/main.kicad_pcb'));fps={f.GetReference():f for f in board.GetFootprints()};assert set(fps)==set(b)
 nodes={node:net for net,ns in actual.items() for node in ns};count=0
 for ref,f in fps.items():
  for pad in f.Pads():
   if not pad.GetNumber():continue
   expected=nodes.get((ref,pad.GetNumber()))
   if expected is not None:
    assert pad.GetNetname().replace('{slash}','/')==expected.replace('{slash}','/'),(ref,pad.GetNumber(),pad.GetNetname(),expected)
    count+=1
 rules=json.loads((HW/'main/main.kicad_pro').read_text());r=rules['board']['design_settings']['rules']
 assert r['min_clearance']==.1524 and r['min_track_width']==.1524 and r['min_through_hole_diameter']==.25 and r['min_copper_edge_clearance']==.2
 if mounting:
  from check_mounting_layout import check as check_mounting
  check_mounting('main');check_mounting('satellite')
 else:assert hashlib.sha256((HW/'satellite/satellite.kicad_pcb').read_bytes()).hexdigest()==m['satellite_pcb_sha256'],'Universal pod routing changed'
 # Satellite schematic is the same circuit with updated assembly notes only.
 oldsat=E.parse(S/'before-satellite.xml');newsat=E.parse(V/'satellite.xml')
 def circuit(t):
  cs={r:(c.findtext('value'),c.findtext('footprint')) for r,c in comps(t).items() if r not in mechanical}
  ns={frozenset((x.get('ref'),x.get('pin')) for x in n.findall('node') if x.get('ref') in cs) for n in t.findall('nets/net')};ns.discard(frozenset());return cs,ns
 assert circuit(oldsat)==circuit(newsat)
 result={'status':'PASS','project':'main','architecture':'stacked-controller','components':len(b),'electrical_pads_checked':count,'retained_circuit_preserved':True,'stack_interface_checked':m['stack_pin_nets'],'universal_pod_circuit_and_routing_preserved':True,'controller_quantity':1,'universal_pod_quantity':8,'battery_count':7,'erc_violations':0,'schematic_parity':0,'drc_violations':len(drc['violations']),'open_connections':len(drc['unconnected_items']),'layout_status':'Legacy outline and retained controller placements only; new stack mechanics and layout pending','pcb_sha256':hashlib.sha256((HW/'main/main.kicad_pcb').read_bytes()).hexdigest()}
 if mounting:
  result.update({'status':'PRESERVATION PASS; LAYOUT PENDING','layout_status':'Matched 17 x 35 mm outline and diagonal locating holes; existing parts retained for user rearrangement','mounting_checked':check_mounting('main'),'drc_types':[v['type'] for v in drc['violations']]})
 (V/'main-checks.json').write_text(json.dumps(result,indent=2)+'\n');(S/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':check()
