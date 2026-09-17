"""Stitch isolated ground pours and the USB reference corridor to In1 ground."""
import sys,math,json
from main_routing import *

def stitch(stem):
 b=load(stem);b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones())
 bp=p.SHAPE_POLY_SET();b.GetBoardPolygonOutlines(bp,False)
 ps=[]
 for f in b.GetFootprints():
  for d in f.Pads():
   bb=d.GetBoundingBox();ps.append((d,tuple(p.ToMM(v) for v in [bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom()])))
 def clear(q):
  for i in range(16):
   pt=(q[0]+.451*math.cos(i*math.pi/8),q[1]+.451*math.sin(i*math.pi/8))
   if not bp.Contains(vec(pt)):return False
  for d,bb in ps:
   if point_rect(q,bb)<.14:return False
   if d.GetNetname()!='GND' and point_rect(q,bb)<.403:return False
   if d.GetAttribute()==p.PAD_ATTRIB_NPTH and math.dist(q,xy(d.GetPosition()))<p.ToMM(d.GetDrillSize().x)/2+.326:return False
  for t in b.GetTracks():
   if isinstance(t,p.PCB_VIA):
    if math.dist(q,xy(t.GetPosition()))<(.46 if t.GetNetname()=='GND' else .153+.25+p.ToMM(t.GetWidth(p.F_Cu))/2):return False
   elif t.GetNetname()!='GND' and point_line(q,xy(t.GetStart()),xy(t.GetEnd()))<.403+p.ToMM(t.GetWidth())/2:return False
  return True
 added=[];failed=[]
 for z in list(b.Zones()):
  if z.GetNetname()!='GND' or z.GetLayer()==p.In1_Cu:continue
  poly=z.GetFilledPolysList(z.GetLayer())
  for i in range(poly.OutlineCount()):
   grounds=[xy(t.GetPosition()) for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()=='GND']
   grounds += [xy(d.GetPosition()) for d,bb in ps if d.GetAttribute()==p.PAD_ATTRIB_PTH and d.GetNetname()=='GND']
   if any(poly.Contains(vec(q),i) for q in grounds):continue
   c=poly.COutline(i);pts=[xy(c.CPoint(j)) for j in range(c.PointCount())];x0,x1=min(q[0] for q in pts),max(q[0] for q in pts);y0,y1=min(q[1] for q in pts),max(q[1] for q in pts)
   cand=[(x0+ix*.1,y0+iy*.1) for ix in range(int((x1-x0)/.1)+1) for iy in range(int((y1-y0)/.1)+1)]
   cand.sort(key=lambda q:(q[0]-(x0+x1)/2)**2+(q[1]-(y0+y1)/2)**2)
   good=next((q for q in cand if poly.Contains(vec(q),i) and clear(q)),None)
   if good:via(b,'GND',good);added.append((b.GetLayerName(z.GetLayer()),good))
   else:failed.append((b.GetLayerName(z.GetLayer()),[x0,y0,x1,y1]))
 # Additional distributed connections keep the narrow USB ground reference tied
 # to the adjacent continuous ground plane along its length.
 refs=[z.GetFilledPolysList(z.GetLayer()) for z in b.Zones() if z.GetNetname()=='GND' and z.GetLayer()==p.In2_Cu]
 if refs:
  for y in [54+i*3 for i in range(11)]:
   cand=[(35.5+i*.15,y+dy) for dy in [0,.3,-.3,.6,-.6] for i in range(134)]
   q=next((q for q in cand if any(poly.Contains(vec(q)) for poly in refs) and clear(q) and all(math.dist(q,xy(v.GetPosition()))>2 for v in b.GetTracks() if isinstance(v,p.PCB_VIA) and v.GetNetname()=='GND')),None)
   if q:via(b,'GND',q);added.append(('USB reference',q))
 save(b,'stitched');print(json.dumps({'added':added,'unstiched_islands':failed},indent=2));(OUT/'stitch-results.json').write_text(json.dumps({'added':added,'unstitched_islands':failed},indent=2))
if __name__=='__main__':stitch(sys.argv[1])
