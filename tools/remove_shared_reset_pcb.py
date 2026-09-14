"""Apply reset-only connectivity changes without moving any retained footprint."""
import sys,xml.etree.ElementTree as E,hashlib
from kicad_edit import *
from remove_shared_reset import REMOVED,props,BACK
name=sys.argv[1];sat=name=='satellite';path=HW/name/(name+'.kicad_pcb')
assert path.read_bytes()==(BACK/name/path.name).read_bytes(),'PCB changed since reset snapshot; do not overwrite user edits'
a=load(path);root=E.parse(HW/'verification/project-split'/f'{name}.xml').getroot()
def escaped(s):return s.replace('/','{slash}') if s.startswith('unconnected-') else s
nodes={(x.attrib['ref'],x.attrib['pin']):escaped(n.attrib['name']) for n in root.findall('nets/net') for x in n.findall('node')}
for f in children(a,'footprint'):
 ref=props(f)['Reference']
 if not sat and ref in REMOVED:a.remove(f);continue
 for pad in children(f,'pad'):
  if children(pad,'net'):child(pad,'net')[1]=q(nodes.get((ref,uq(pad[1])),''))
# Keep the already-routed direct MCU-to-ICE path. All harness reset branches,
# their vias and the tiny redundant pad-centre segment are removed.
keep={'1df6d765-78aa-4079-a42c-0d77d8e8777c','44abb8cf-24bd-4084-aa30-a708f8247c6a','7f1743e7-9685-4c1a-a8a2-f7723253f163','caca634b-e965-439e-a960-1773fab071a9','e46289c6-e610-4043-b702-a13008874964'}
removed_tracks=0
for kind in ['segment','via','zone']:
 for t in children(a,kind):
  if children(t,'net') and 'RING_nRESET' in uq(child(t,'net')[1]):
   if sat and kind=='segment' and uq(child(t,'uuid')[1]) in keep:child(t,'net')[1]=q('/LOCAL_nRESET')
   else:a.remove(t);removed_tracks+=1
save(path,a)
print(name,'removed reset copper items',removed_tracks)
