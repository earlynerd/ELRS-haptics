"""Constrained placement from the user's functional group checkpoint.

Real pad positions and courtyard bounds; fixed connector/RF anchors, weighted
critical pin connections, body clearance, orthogonal rotations, repeatable search.
Writes a candidate only. Active board application is a separate guarded step.
"""
import json, math, sys, html
from pathlib import Path
import numpy as np
import pcbnew as p

ROOT=Path(__file__).resolve().parents[1];HW=ROOT/'hardware'
OUT=HW/'verification/main-placement-v2'
SRC=OUT/'input.kicad_pcb'
FIXED={'U1','J2','J101','J103','J200','M1'}
RAILS={'GND','+3V3','+3V3_POD','VBAT','/Charger and regulated supply/SYS','USB_VBUS'}
GROUPS={
 'esp':['U1','C2','C3','R1','R2','R4','R42','R43','R24','R25'],
 'reset':['SW1','R3','C1'], 'boot':['SW2','R5'],
 'charger':['U11','C34','C35','C36','Q1','R37','R38','R39','R62'],
 'regulator':['U12','L1','C37','C38','C39','R40','R41'],
 'podpower':['U26','C41','C42','C43','R45','R46'],
 'mcu':['U18','C100','C101','C102','C103','R100','R101','R102','R103','R105','J1'],
 'driver':['U3','C5','C6','C7','R8','R9'],
 'usb':['J2','U14','U15','R60','R61','C32'],
 'indicator':['D1','R47','R49','R51'], 'button':['SW3'],
 'battery':['J200','F100'], 'harness':['J101'], 'ntc':['J103'], 'lra':['M1']}
TARGET={r:g[0] for g in GROUPS.values() for r in g[1:]}
TARGET.update({'R3':'U1','C1':'U1','R5':'U1','R4':'U1','C102':'U18','R105':'U18','R39':'Q1','F100':'J200'})
PAIR={
 'C2':('U1','3',18),'C3':('U1','3',7),'C100':('U18','9',18),'C101':('U18','9',5),
 'C5':('U3','C2',14),'C7':('U3','C2',10),'C6':('U3','A2',20),
 'C34':('U11','10',16),'C35':('U11','1',16),'C36':('U11','2',14),
 'C37':('U12','10',24),'C38':('U12','6',24),'C39':('U12','6',12),
 'C41':('U26','1',12),'C43':('U26','6',12)}

def xy(v):return p.ToMM(v.x),p.ToMM(v.y)
def rot(arr,a):
 t=math.radians(a);return arr @ np.array([[math.cos(t),-math.sin(t)],[math.sin(t),math.cos(t)]])

b=p.LoadBoard(str(SRC));fps={f.GetReference():f for f in b.GetFootprints()};model={};placed={}
for ref,f in fps.items():
 x,y=xy(f.GetPosition());ang=f.GetOrientationDegrees();f.BuildCourtyardCaches();bb=f.GetCourtyard(p.F_CrtYd).BBox()
 box=[p.ToMM(bb.GetX()),p.ToMM(bb.GetY()),p.ToMM(bb.GetRight()),p.ToMM(bb.GetBottom())]
 if ref=='U1':box=[38.65,40.1,52.35,51.6] # antenna-only extension lies outside board
 if ref=='M1':box=[x-1.1,y-1.5,x+1.1,y+1.5] # FPC contact area; actuator body is in cutout
 pads=[{'pin':d.GetNumber(),'net':d.GetNetname(),'xy':list(xy(d.GetPosition())),'size':list(xy(d.GetSize()))} for d in f.Pads() if d.GetNumber()]
 corners=np.array([[box[0],box[1]],[box[0],box[3]],[box[2],box[1]],[box[2],box[3]]])-[x,y]
 model[ref]={'start':[x,y,ang],'corners':corners,'pads':pads,'padlocal':np.array([d['xy'] for d in pads])-[x,y]}
 if ref in FIXED:placed[ref]=(x,y,ang)

def offsets(ref,ang):
 z=rot(model[ref]['corners'],ang-model[ref]['start'][2]);return np.r_[z.min(axis=0),z.max(axis=0)]
def box(ref,pos):
 z=offsets(ref,pos[2]);return z+np.array([pos[0],pos[1],pos[0],pos[1]])
def padxy(ref,pos):return rot(model[ref]['padlocal'],pos[2]-model[ref]['start'][2])+np.array(pos[:2])
def collide(a,z,gap=.12):return a[0]<z[2]+gap and a[2]>z[0]-gap and a[1]<z[3]+gap and a[3]>z[1]-gap
def inside(bb):return bb[0]>=35.15 and bb[2]<=55.75 and bb[1]>=40.4 and bb[3]<=95.7 and not collide(bb,[41,58,48,73],.2)
def valid(ref,pos):
 bb=box(ref,pos)
 return inside(bb) and not any(collide(bb,box(r,v)) for r,v in placed.items() if r!=ref)

# Macro seeds: locked connectors remain untouched; cores fit into the available
# bands around the actuator opening. Pin-level refinement follows these seeds.
CORE={
 'U18':(47.2,78.3,180),'U12':(40.9,85.0,90),'U11':(38.6,77.3,180),'Q1':(38.3,71.8,0),
 'U26':(50.7,66.85,90),'U3':(49.4,72.7,0),
 'SW1':(37.8,56.7,90),'SW2':(48.7,54.4,0),'SW3':(38.5,65.75,90),
 'J1':(50.85,60.8,90),'D1':(54.35,43.8,0),
 'U14':(45.5,87.75,0),'U15':(49.0,87.3,90),'L1':(40.9,82.25,0),'C38':(44.0,84.8,270),'C39':(46.2,84.8,270),'R40':(42.6,87.8,180),'R41':(40.4,87.8,180)}
for ref,pos in CORE.items():
 if not valid(ref,pos): print('SEED COLLISION',ref,pos,box(ref,pos),[(r,box(r,v).tolist()) for r,v in placed.items() if collide(box(ref,pos),box(r,v))],flush=True)
 placed[ref]=pos

LINK={'R1':('U1','15',12),'R2':('U1','16',12),'R24':('U1','17',14),'R25':('U1','18',14),'R3':('U1','8',7),'R4':('U1','22',10),'R5':('U1','23',10),'R8':('U3','B1',8),'R9':('U3','C1',8),'R100':('U18','18',12),'R101':('U18','8',12),'R102':('U18','18',8),'R103':('U18','8',8)}

def search(ref,radius=None):
 anchor=TARGET.get(ref);cx,cy=placed[anchor][:2] if anchor in placed else model[ref]['start'][:2]
 obs=np.array([box(r,v) for r,v in placed.items() if r!=ref]+[[40.87,57.87,48.13,73.13]])
 # 0.2 mm positional grid, orthogonal rotations; pad offsets stay exact.
 xx,yy=np.meshgrid(np.arange(35.4,55.61,.2),np.arange(40.6,95.61,.2));base=np.c_[xx.ravel(),yy.ravel()]
 if radius is not None:base=base[np.linalg.norm(base-[cx,cy],axis=1)<=radius]
 netpoints={}
 for r,v in placed.items():
  if r==ref:continue
  for pt,pad in zip(padxy(r,v),model[r]['pads']):
   if pad['net'] and not pad['net'].startswith('unconnected-'):netpoints.setdefault(pad['net'],[]).append((r,pt))
 best=None
 for angle in [0,90,180,270]:
  off=offsets(ref,angle);bb=np.c_[base,base]+off
  good=(bb[:,0]>=35.25)&(bb[:,2]<=55.75)&(bb[:,1]>=40.4)&(bb[:,3]<=95.7)
  for z in obs:good&=~((bb[:,0]<z[2]+.12)&(bb[:,2]>z[0]-.12)&(bb[:,1]<z[3]+.12)&(bb[:,3]>z[1]-.12))
  pts=base[good]
  if len(pts)==0:continue
  # Functional group affinity matters even for shared supply rails.
  cost=np.linalg.norm(pts-[cx,cy],axis=1)*(3.0 if ref in TARGET else .05)
  local=rot(model[ref]['padlocal'],angle-model[ref]['start'][2])
  for pad,delta in zip(model[ref]['pads'],local):
   net=pad['net']
   if not net or net.startswith('unconnected-') or net=='GND':continue
   other=netpoints.get(net,[])
   if net in RAILS:other=[(r,q) for r,q in other if r==anchor]
   if other:
    pp=pts+delta;dd=np.min([np.linalg.norm(pp-q,axis=1) for r,q in other],axis=0)
    cost+=dd*(.5 if net in RAILS else 2.5)
  if ref in PAIR:
   ar,pin,weight=PAIR[ref]
   q=next(pt for pt,pad in zip(padxy(ar,placed[ar]),model[ar]['pads']) if pad['pin']==pin)
   sig=[delta for pad,delta in zip(model[ref]['pads'],local) if pad['net']!='GND']
   cost+=np.min([np.linalg.norm(pts+d-q,axis=1) for d in sig],axis=0)*weight
  if ref in LINK:
   ar,pin,weight=LINK[ref]
   q,npad=next((pt,pad) for pt,pad in zip(padxy(ar,placed[ar]),model[ar]['pads']) if pad['pin']==pin)
   delta=next(delta for pad,delta in zip(model[ref]['pads'],local) if pad['net']==npad['net'])
   cost+=np.linalg.norm(pts+delta-q,axis=1)*weight
  # Avoid bunching pads close to the physical opening / outline by an extra
  # small term without forcing decouplers away from their IC.
  idx=int(cost.argmin());option=(float(cost[idx]),(float(pts[idx,0]),float(pts[idx,1]),angle))
  if best is None or option[0]<best[0]:best=option
 return best

def report():
 return [(r,s) for i,r in enumerate(placed) for s in list(placed)[i+1:] if collide(box(r,placed[r]),box(s,placed[s]),0)]

if __name__=='__main__':
 assert not report(),report()
 assert all(valid(r,v) for r,v in CORE.items()),'Invalid core seeds'
 # Place electrical-critical capacitors first, then larger bodies and remaining support.
 priority=['C37','C38','C39','C34','C35','C36','C100','C101','C103','C2','C3','C41','C43','C6','C5','C7','Q1','F100','R40','R41','R24','R25']
 todo=[r for r in priority if r in fps and r not in placed]+sorted(set(fps)-set(placed)-set(priority))
 for ref in todo:
  if ref in placed:continue
  found=search(ref)
  assert found,('Cannot fit',ref)
  placed[ref]=found[1];print('FIT',ref,[round(v,3) for v in found[1]],round(found[0],2),flush=True)
 # Coordinate descent of support parts against the now complete placement.
 for step in range(3):
  for ref in todo:
   found=search(ref,10)
   if found:placed[ref]=found[1]
  print('REFINEMENT',step+1,'overlaps',report(),flush=True)
 assert not report(),report()
 for ref,pos in placed.items():
  f=fps[ref];f.SetOrientationDegrees(pos[2]);f.SetPosition(p.VECTOR2I(p.FromMM(pos[0]),p.FromMM(pos[1])))
 # The user moved the driver but its single old tie did not follow. Reattach
 # the same NRST-to-VDD segment to the real B2/C2 pad positions.
 tracks=list(b.GetTracks());assert len(tracks)==1 and not isinstance(tracks[0],p.PCB_VIA)
 dp={d.GetNumber():d for d in fps['U3'].Pads()};tracks[0].SetStart(dp['B2'].GetPosition());tracks[0].SetEnd(dp['C2'].GetPosition())
 b.BuildConnectivity();p.SaveBoard(str(OUT/'main.kicad_pcb'),b)
 result={'source':str(SRC),'anchors':sorted(FIXED),'placements':{r:list(v) for r,v in placed.items()},'groups':GROUPS,'overlaps':report(),'gap_mm':.12,'grid_mm':.2}
 (OUT/'placement.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Saved candidate',OUT/'main.kicad_pcb',flush=True)
