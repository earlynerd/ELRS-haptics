"""Staged main routing. Works only in verification/main-routing until accepted."""
import sys,json,math,shutil,re
from pathlib import Path
import pcbnew as p
from plane_fanout import xy,point_rect,line_rect,point_line,segment_dist
ROOT=Path(__file__).resolve().parents[1];HW=ROOT/'hardware';OUT=HW/'verification/main-routing'
def vec(q):return p.VECTOR2I(p.FromMM(q[0]),p.FromMM(q[1]))
def load(stem):
 shutil.copy2(HW/'backups/pre-main-routing-20260913/main.kicad_pro',OUT/(stem+'.kicad_pro'))
 return p.LoadBoard(str(OUT/(stem+'.kicad_pcb')))
def save(b,stem):
 b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(OUT/(stem+'.kicad_pcb')),b)
 shutil.copy2(HW/'backups/pre-main-routing-20260913/main.kicad_pro',OUT/(stem+'.kicad_pro'))
def pads(b):return {(f.GetReference(),d.GetNumber()):d for f in b.GetFootprints() for d in f.Pads() if d.GetNumber()}
def track(b,net,points,w=.2,layer=p.F_Cu):
 for a,z in zip(points,points[1:]):
  if math.dist(a,z)<1e-7:continue
  t=p.PCB_TRACK(b);t.SetStart(vec(a));t.SetEnd(vec(z));t.SetWidth(p.FromMM(w));t.SetLayer(layer);t.SetNet(b.FindNet(net));t.SetLocked(True);b.Add(t)
def via(b,net,q,diam=.5):
 v=p.PCB_VIA(b);v.SetPosition(vec(q));v.SetWidth(p.FromMM(diam));v.SetDrill(p.FromMM(.25));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet(net));v.SetLocked(True);b.Add(v)
def zone(b,net,layer,points,priority=0):
 z=p.ZONE(b);z.SetNet(b.FindNet(net));z.SetLayer(layer);z.SetLocalClearance(p.FromMM(.1524));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetMinThickness(p.FromMM(.1524));z.SetAssignedPriority(priority)
 z.Outline().NewOutline()
 for pt in points:z.Outline().Append(int(p.FromMM(pt[0])),int(p.FromMM(pt[1])))
 b.Add(z)
def prepare():
 b=load('main');pd=pads(b)
 def link(r,n,s,m,mid=(),w=.2):
  a,z=pd[(r,n)],pd[(s,m)];assert a.GetNetname()==z.GetNetname();track(b,a.GetNetname(),[xy(a.GetPosition()),*mid,xy(z.GetPosition())],w)
 # Short switching loops, necked at the 0.5-mm-pitch IC and widened thereafter.
 for n,m,x in [('9','1',40.1),('7','2',41.7)]:
  a=xy(pd[('U12',n)].GetPosition());track(b,pd[('U12',n)].GetNetname(),[a,(a[0],83.6),(x,83.3)],.2)
  track(b,pd[('U12',n)].GetNetname(),[(x,83.3),(x,82.25)],.5)
 link('U12','10','C37','1',[(39.25,84.25),(39.2,84.2)],.25)
 link('U12','1','C37','1',[(39.2,85.9),(38.15,84.85)],.2)
 link('U12','6','C38','1',[(42.3,84.25),(42.7,83.85)],.25)
 link('C38','1','C39','1',w=.6)
 link('C38','2','C39','2',w=.5)
 link('U12','4','R40','2',[(41.4,86.7),(42.09,87.39)],.1524)
 link('R40','2','R41','1',w=.1524)
 # Charger input, system output and battery capacitor paths.
 link('U11','10','C34','1',[(37.5,79.475)],.2)
 link('U11','1','C35','1',[(41.55,78.1)],.2)
 link('U11','2','C36','1',[(40.25,77.7),(40.55,77.4),(40.55,75.975)],.1524)
 link('U26','1','C41','1',[(49.75,69.37)],.3)
 link('U26','6','C43','1',[(49.75,64.3),(51.58,64.3)],.25)
 link('U18','9','C100','1',[(51.705,76.025)],.3)
 link('C100','1','C101','1',[(51.8,74.65)],.3)
 link('U3','A2','C6','1',[(49.4,71.08)],.1524)
 link('U3','C2','C5','1',[(49.4,73.65),(49.25,73.8)],.1524)
 link('C5','1','C7','1',[(47.68,74.6),(46.28,74.6),(45.48,73.8)],.2)
 link('U1','3','C2','1',[(38.02,43.3)],.3)
 link('C2','1','C3','1',[(36.43,43.32)],.3)
 link('U1','8','C1','1',[(38.02,47.3)],.2)
 # Planes: continuous ground, main 3V3 and explicit local power regions.
 outline=[(35,40.1),(56,40.1),(56,96),(35,96)]
 zone(b,'GND',p.In1_Cu,outline)
 zone(b,'+3V3',p.In2_Cu,outline)
 zone(b,'+3V3_POD',p.In2_Cu,[(48.5,54),(56,54),(56,82.7),(43,82.7),(43,73.4),(48.5,73.4)],1)
 zone(b,'VSYS',p.In2_Cu,[(37.3,74.2),(42.9,74.2),(42.9,86.6),(37.3,86.6)],2)
 # Top ground stitching is filled natively; the router receives inner planes only.
 zone(b,'GND',p.F_Cu,outline)
 save(b,'power')
 print('Power connections and plane regions prepared.')

def fanout(stem):
 b=load(stem);pd=pads(b);allpads=[]
 for f in b.GetFootprints():
  for d in f.Pads():
   bb=d.GetBoundingBox();allpads.append((f.GetReference(),d,tuple(p.ToMM(v) for v in [bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom()])))
 def clear(a,z,net,w,layer,withvia=False):
  if not all(35.45<=q[0]<=55.55 and 40.55<=q[1]<=95.5 for q in [a,z]):return False
  if line_rect(a,z,(41,58,48,73),.2+w/2):return False
  if withvia and point_rect(z,(41,58,48,73))<.46:return False
  for r,d,bb in allpads:
   if withvia and point_rect(z,bb)<.135:return False # no hole in any pad
   if withvia and d.GetNetname()!=net and point_rect(z,bb)<.4074:return False
   if d.IsOnLayer(layer) and d.GetNetname()!=net and line_rect(a,z,bb,.1525+w/2):return False
  for t in b.GetTracks():
   if isinstance(t,p.PCB_VIA):
    if withvia and math.dist(z,xy(t.GetPosition()))<(.5 if t.GetNetname()==net else .653):return False
    if t.GetNetname()!=net and point_line(xy(t.GetPosition()),a,z)<p.ToMM(t.GetWidth(layer))/2+.1525+w/2:return False
   elif t.GetNetname()!=net:
    if withvia and point_line(z,xy(t.GetStart()),xy(t.GetEnd()))<.4025+p.ToMM(t.GetWidth())/2:return False
    if t.GetLayer()==layer and segment_dist(a,z,xy(t.GetStart()),xy(t.GetEnd()))<.1525+(w+p.ToMM(t.GetWidth()))/2:return False
  return True
 targets=[('U12','8'),('U12','2'),('U12','3'),('C37','2'),('C38','2'),('C39','2'),('U11','11'),('C34','2'),('C35','2'),('C36','2'),('C100','2'),('U18','7'),('U3','B3'),('C5','2'),('C6','2'),('C7','2'),('C41','2'),('C43','2'),('U26','2'),('C2','2'),('C3','2')]
 # One plane tap per local supply group, plus other unpaired supply pads.
 direct_supplies={'U1','U11','U12','U26','U18','U3','C7','C39','C101'}
 targets += [(r,n) for (r,n),d in pd.items() if d.GetNetname() in ['+3V3','+3V3_POD','VSYS'] and r not in direct_supplies]
 targets += [('C2','1')]
 completed=[];failed=[]
 # Small constrained pads first. Avoid duplicates and redundant taps on connected stubs.
 targets=sorted(set(targets),key=lambda k:pd[k].GetSize().x*pd[k].GetSize().y)
 for key in targets:
  d=pd[key];net=d.GetNetname();start=xy(d.GetPosition());w=.1524 if key[0] in ['U3','U12','U11'] else .2
  # Nearby same-net via plus a clear short connection can be reused.
  found=False
  for v in list(b.GetTracks()):
   if isinstance(v,p.PCB_VIA) and v.GetNetname()==net and math.dist(start,xy(v.GetPosition()))<1.5:
    end=xy(v.GetPosition());dx,dy=abs(end[0]-start[0]),abs(end[1]-start[1])
    if (min(dx,dy)<1e-6 or abs(dx-dy)<1e-6) and clear(start,end,net,w,d.GetLayer()):track(b,net,[start,end],w,d.GetLayer());found=True;break
  if found:continue
  candidates=[]
  for radius in [.45+i*.05 for i in range(34)]:
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
    end=(round(start[0]+radius*dx,6),round(start[1]+radius*dy,6))
    if clear(start,end,net,w,d.GetLayer(),True):candidates.append((math.dist(start,end),end))
   if candidates:break
  if not candidates:failed.append(key);continue
  end=min(candidates)[1];via(b,net,end);track(b,net,[start,end],w,d.GetLayer());completed.append((key,end))
 save(b,'fanout');(OUT/'fanout.json').write_text(json.dumps({'completed':completed,'failed':failed},indent=2));print('Fanout',len(completed),'failed',failed)

def export(stem):
 b=load(stem)
 # Do not freeze outer copper pours as router obstacles. Native KiCad refills them.
 assert p.ExportSpecctraDSN(b,str(OUT/(stem+'.dsn')))
 text=(OUT/(stem+'.dsn')).read_text()
 text=text.replace('(layer In1.Cu\n      (type signal)','(layer In1.Cu\n      (type power)').replace('(layer In2.Cu\n      (type signal)','(layer In2.Cu\n      (type power)')
 text=re.sub(r'\(plane [^\s]+ \(polygon .*?\)\)', '',text,flags=re.S)
 planes=[]
 for z in b.Zones():
  if z.GetLayer() in [p.F_Cu,p.B_Cu]:continue
  layer=z.GetLayer();poly=z.GetFilledPolysList(layer)
  def polygon(chain):
   pts=[chain.CPoint(j) for j in range(chain.PointCount())]
   return '(polygon '+b.GetLayerName(layer)+' 0 '+' '.join(f'{p.ToMM(v.x)*1000:.3f} {-p.ToMM(v.y)*1000:.3f}' for v in pts)+')'
  for i in range(poly.OutlineCount()):
   s='(plane "'+z.GetNetname()+'" '+polygon(poly.COutline(i))
   for j in range(poly.HoleCount(i)):s+=' (window '+polygon(poly.CHole(i,j))+')'
   planes.append(s+')')
 insert=text.index('    (via ');text=text[:insert]+'\n'.join(planes)+'\n'+text[insert:]
 # Native pour handles all surface ground pads. Keep them as obstacles, but do
 # not ask the router to draw tracks through the ESP module's ground grid.
 text=re.sub(r'(\(net GND\s*\(pins).*?(\)\s*\))',r'\1\2',text,flags=re.S)
 # Routing minimum, not the smaller SMD exemption from the generic exporter.
 text=re.sub(r'\(clearance [\d.]+ \(type smd_smd\)\)','(clearance 152.4 (type smd_smd))',text)
 # Margin protects cutout and outer edge beyond router's conductor clearance.
 def offset(m):
  vals=list(map(float,m.group(2).split()));xs=vals[::2];ys=vals[1::2];mx=(min(xs)+max(xs))/2;my=(min(ys)+max(ys))/2
  delta=-80 if 'path pcb' in m.group(1) else 80
  return m.group(1)+' '+' '.join(str(round(v+delta*(1 if v>mid else -1),3)) for pair in zip(xs,ys) for v,mid in zip(pair,[mx,my]))+m.group(3)
 text=re.sub(r'(\(path pcb 0|\(polygon signal 0)\s+([\d.\s-]+)(\))',offset,text)
 settings='(autoroute_settings (fanout off) (autoroute on) (postroute on) (vias on)'
 for name,active,direction in [('F.Cu','on','vertical'),('In1.Cu','off','horizontal'),('In2.Cu','off','vertical'),('B.Cu','on','horizontal')]:
  settings+=f' (layer_rule {name} (active {active}) (preferred_direction {direction}) (preferred_direction_trace_costs 1) (against_preferred_direction_trace_costs 1.5))'
 settings+=')'
 # Freerouting 2.4.1's inline autoroute_settings reader can consume the later
 # placement scope. Power-type inner layers keep routing on the two outer layers.
 (OUT/(stem+'.dsn')).write_text(text)
 print('Exported',stem,'with',len(planes),'plane contours.')
def import_session(stem):
 b=load(stem);assert p.ImportSpecctraSES(b,str(OUT/(stem+'.ses')));save(b,'routed');print('Imported route session.')
if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare()
 if sys.argv[1]=='fanout':fanout(sys.argv[2])
 if sys.argv[1]=='export':export(sys.argv[2])
 if sys.argv[1]=='import':import_session(sys.argv[2])
