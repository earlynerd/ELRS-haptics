"""Match the simplified USB circuit while preserving retained PCB placement."""
import copy,xml.etree.ElementTree as E
from simplify_usb import BACK,REMOVED,NEW
from readable_schematic import props
from kicad_edit import *
path=HW/'main/main.kicad_pcb'
assert path.read_bytes()==(BACK/path.name).read_bytes(),'PCB changed after snapshot; preserve user edits'
a=load(path);root=E.parse(HW/'verification/project-split/main.xml').getroot()
comps={c.attrib['ref']:c for c in root.findall('components/comp')}
def escaped(n):return n.replace('/','{slash}') if n.startswith('unconnected-') else n
nodes={(x.attrib['ref'],x.attrib['pin']):escaped(n.attrib['name']) for n in root.findall('nets/net') for x in n.findall('node')}
sample=copy.deepcopy(next(f for f in children(a,'footprint') if props(f)['Reference']=='R26'))
for f in children(a,'footprint'):
 ref=props(f)['Reference']
 if ref in REMOVED:a.remove(f);continue
 for pad in children(f,'pad'):
  if children(pad,'net'):child(pad,'net')[1]=q(nodes.get((ref,uq(pad[1])),''))
for ref,(x,y) in NEW.items():
 f=copy.deepcopy(sample);child(f,'at')[1:]=[str(x),str(y)]
 def uuids(z):
  if not isinstance(z,list):return
  if z[0]=='uuid':z[1]=q(uid())
  for v in z:uuids(v)
 uuids(f)
 for z in children(f,'property'):
  if uq(z[1])=='Reference':z[2]=q(ref)
  elif uq(z[1])=='Value':z[2]=q('5.1k 1%')
 c=comps[ref];child(f,'path')[1]=q(c.find('sheetpath').attrib['tstamps']+c.findtext('tstamps'))
 for pad in children(f,'pad'):child(pad,'net')[1]=q(nodes[(ref,uq(pad[1]))])
 a.append(f)
save(path,a)
print('PCB matched: 15 components removed, two CC resistors added; retained placement unchanged.')
