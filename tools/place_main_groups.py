"""Bounded main placement experiment from the saved pre-placement board.

Critical circuits are explicitly placed and oriented; remaining small support
parts are fitted against real courtyards and their electrical neighbours.
"""
from pathlib import Path
import math,json,shutil,sys
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];HW=ROOT/'hardware';OUT=HW/'verification/main-placement';SRC=HW/'backups/before-main-placement/main.kicad_pcb'
analysis=json.loads((HW/'verification/project-split/main-placement-analysis.json').read_text())
b=p.LoadBoard(str(SRC));fps={f.GetReference():f for f in b.GetFootprints()}
models={f['reference']:f for f in analysis['footprints']}
mf=models['M1'];mf['courtyard']={'min_x':mf['x']-1.1,'max_x':mf['x']+1.1,'min_y':mf['y']-1.4,'max_y':mf['y']+1.4}
before=json.loads((OUT/'before-pads.json').read_text())
def vec(x,y):return p.VECTOR2I(p.FromMM(x+35),p.FromMM(y+35))
def rotate(x,y,a):
 t=math.radians(a);return x*math.cos(t)+y*math.sin(t),-x*math.sin(t)+y*math.cos(t)
def offsets(ref,angle):
 f=models[ref];c=f['courtyard'];corners=[(x-f['x'],y-f['y']) for x,y in [(c['min_x'],c['min_y']),(c['max_x'],c['min_y']),(c['max_x'],c['max_y']),(c['min_x'],c['max_y'])]]
 corners=[rotate(x,y,angle-f['angle']) for x,y in corners]
 return min(x for x,y in corners),min(y for x,y in corners),max(x for x,y in corners),max(y for x,y in corners)
def box(ref,pos):
 x,y,a=pos;z=offsets(ref,a);return (x+z[0],y+z[1],x+z[2],y+z[3])
def collide(a,z,gap=.035):return a[0]<z[2]+gap and a[2]>z[0]-gap and a[1]<z[3]+gap and a[3]>z[1]-gap
def positions(ref,pos):
 x,y,a=pos;o=before[ref];out=[]
 for pad in o['pads']:
  dx,dy=rotate(pad['x']-o['x'],pad['y']-o['y'],a-o['angle']);out.append((pad['pin'],x+dx,y+dy,pad['net']))
 return out
def place(ref,pos):
 f=fps[ref];f.SetOrientationDegrees(pos[2]);f.SetPosition(vec(*pos[:2]));placed[ref]=pos

placed={}
# Preserve enclosure / RF / actuator anchors. Remove the uncabled template IN bank.
removed=fps.pop('J100');b.Remove(removed)
for r in ['U1','J2','SW3','D1','M1','SW2']:place(r,(before[r]['x'],before[r]['y'],before[r]['angle']))
fixed={
 'J1':(20,11.7,0),'SW1':(3,26.5,90),'J101':(19.55,28.5,0),'J102':(5,34.75,0),'J200':(15.5,32.5,90),'F100':(19.75,36.2,90),'J103':(2.3,33.7,90),
 'U12':(5.5,49,0),'L1':(8.15,49,270),'C37':(5.65,46.2,0),'C38':(4.4,52.85,180),'C39':(8,52.85,0),'R40':(4.75,51.25,0),'R41':(6.8,51.25,0),
 'U11':(11.1,50,270),'C35':(13.5,47.3,90),'C36':(10.7,46.7,90),'C34':(13.8,50.8,90),
 'U18':(8,41.6,180),'C100':(12.85,38.65,0),'C101':(12.85,41,270),
 'U3':(15.15,36.5,0),'C6':(15.15,34.45,90),'C5':(15.2,38.55,180),'C7':(17.8,38.5,0),
 'C102':(13,43.9,0),'R105':(13.5,45,180),
 'U16':(2,38.7,270),'C32':(2,35.65,180),'U17':(2,43.9,270),'C33':(2,41.3,180),
 'R28':(1,46.625,0),'R29':(2.95,46.625,0),'Q3':(2,49,0),'R30':(1.6,52,0),'R32':(1.6,53.3,0),
 'Q2':(2,55.65,0),'R33':(4.5,55.6,90),
 'U14':(10.75,52.9,0),'U15':(13,53.15,0),'U13':(18,54.9,180),'C31':(20.25,54.9,90),'R26':(18.4,52.95,0),'R27':(15.5,52.95,0),
 'Q1':(18.4,42.8,0),'R39':(15.6,44.6,90),
 'Q4':(2,18.6,0),'R34':(2.5,15.1,0),'R35':(2.5,16.2,0),
 'U26':(8,20.5,0),'C41':(4.95,19.6,180),'R45':(4.95,20.8,180),'C43':(11.3,19.6,0),'R46':(11.3,20.65,0),'C42':(11.3,21.7,0),
 'Q5':(16.25,19.05,0),'C40':(13.25,19,90),'R44':(15.8,21.3,0),'R6':(13.3,21.25,0),
 'C2':(2.7,8.3,180),'C3':(1.3,10.9,270),'C103':(16,40.05,0),
 'R47':(16.5,57.7,90),'R49':(16.5,59.7,90),'R51':(20.3,58.5,90),
 'R24':(9.7,17.6,90),'R25':(10.8,17.6,90),'C29':(7.6,17.6,90),'C30':(8.6,17.6,90),
 'R1':(6.6,17.6,90),'R2':(5.5,17.6,90),'R3':(2,13.6,90),'R42':(18,14.6,90),'R43':(18,16.4,270)
}
for r,pos in fixed.items():place(r,pos)
def bounds():
 out={r:box(r,v) for r,v in placed.items()};out['U1']=(3.65,5.1,17.35,16.55);return out
def conflicts():
 bs=bounds();return [(r,s) for i,r in enumerate(bs) for s in list(bs)[i+1:] if collide(bs[r],bs[s],0)]
print('Explicit group conflicts',conflicts(),flush=True)
# Fit remaining low-current support around the pins it serves; no net edits.
targets={'C1':['U1'],'C29':['U1'],'C30':['U1'],'R1':['U1'],'R2':['U1'],'R3':['U1'],'R4':['U1'],'R5':['U1'],'R7':['Q5'],'R8':['U18','U3'],'R9':['U18','U3'],'R31':['U17'],'R37':['U11'],'R38':['Q1'],'R40':['U12'],'R41':['U12'],'R42':['U1'],'R43':['U1'],'R48':['U1'],'R50':['U1'],'R52':['U1'],'R100':['U18'],'R101':['U18'],'R102':['U18'],'R103':['U18'],'J3':['U11']}
targets['R36']=['Q4']
power={'GND','+3V3','+3V3_POD','VBAT'}
todo=sorted(set(fps)-set(placed),key=lambda r:(r not in ['J3','C1','R40','R41'],r))
for r in todo:
 bs=bounds();tar=targets[r];anchor=[v for t in tar for v in positions(t,placed[t]) if not v[3].startswith('unconnected-')]
 scores=[]
 # Candidates in a bounded local search; fall back to the full board if crowded.
 cx=sum(placed[t][0] for t in tar)/len(tar);cy=sum(placed[t][1] for t in tar)/len(tar)
 for radius in [8,60]:
  for angle in [0,90,180,270]:
   dx0,dy0,dx1,dy1=offsets(r,angle)
   for ix in range(max(1,math.ceil((cx-radius)*5)),min(104,math.floor((cx+radius)*5))+1):
    x=ix/5
    if x+dx0<.05 or x+dx1>20.95:continue
    for iy in range(max(26,math.ceil((cy-radius)*5)),min(303,math.floor((cy+radius)*5))+1):
     y=iy/5;bb=(x+dx0,y+dy0,x+dx1,y+dy1)
     if bb[1]<5.2 or bb[3]>60.8 or collide(bb,(6,23,13,38),.05):continue
     if any(collide(bb,z) for z in bs.values()):continue
     pts=positions(r,(x,y,angle));cost=.25*math.hypot(x-cx,y-cy)
     for pin,px,py,net in pts:
      relevant=[(qx,qy) for _,qx,qy,nn in anchor if nn==net]
      if relevant:
       d=min(math.hypot(px-qx,py-qy) for qx,qy in relevant);cost+=d*(.35 if net in power else 2)
     scores.append((cost,(x,y,angle)))
  if scores:break
 assert scores,('No place',r)
 score,pos=min(scores);place(r,pos);print('Fit',r,pos,round(score,2),flush=True)
# The existing DRV NRST/VDD tie follows its driver exactly.
old=before['U3'];new=placed['U3']
for t in b.GetTracks():
 a=t.GetStart();z=t.GetEnd()
 for pt,setter in [(a,t.SetStart),(z,t.SetEnd)]:
  dx,dy=rotate(p.ToMM(pt.x)-35-old['x'],p.ToMM(pt.y)-35-old['y'],new[2]-old['angle']);setter(vec(new[0]+dx,new[1]+dy))
for f in b.GetFootprints():f.SetLocked(False)
b.BuildConnectivity();p.SaveBoard(str(OUT/'main.kicad_pcb'),b)
(OUT/'placement.json').write_text(json.dumps(placed,indent=2)+'\n')
print('Final explicit overlaps',conflicts())
