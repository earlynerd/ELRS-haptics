"""Remove grid stair steps using checked 45-degree doglegs only."""
import math
from routing_v08 import HW,p,track,refill
from plane_fanout import xy,point_line,segment_dist,line_rect
path=HW/'verification/routing-v09/pod-7.kicad_pcb';b=p.LoadBoard(str(path));net='RING_D8';width=.1524
target=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.B_Cu and t.GetNetname()==net]
others=[(xy(t.GetStart()),xy(t.GetEnd()),p.ToMM(t.GetWidth())/2) for t in b.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.B_Cu and t.GetNetname()!=net]
vias=[(xy(t.GetPosition()),p.ToMM(t.GetWidth(p.B_Cu))/2) for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()!=net]
def allowed(a,z):
    if line_rect(a,z,(135,106,142,121),.34):return False
    if not all(131.35<q[0]<147.65 and 96.35<q[1]<130.65 for q in [a,z]):return False
    if any(point_line(q,a,z)<r+width/2+.205 for q,r in vias):return False
    return not any(segment_dist(a,z,c,d)<r+width/2+.205 for c,d,r in others)
def options(a,z):
    dx,dy=z[0]-a[0],z[1]-a[1];sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1;m=min(abs(dx),abs(dy))
    if min(abs(dx),abs(dy))<1e-6 or abs(abs(dx)-abs(dy))<1e-6:return [[a,z]]
    return [[a,(a[0]+sx*m,a[1]+sy*m),z],[a,(z[0]-sx*m,z[1]-sy*m),z]]
points=[(145.4,111.3)];remaining=target.copy()
while remaining:
    t=next(t for t in remaining if math.dist(xy(t.GetStart()),points[-1])<1e-5 or math.dist(xy(t.GetEnd()),points[-1])<1e-5)
    a,z=xy(t.GetStart()),xy(t.GetEnd());points.append(z if math.dist(a,points[-1])<1e-5 else a);remaining.remove(t)
simple=[points[0]];j=0
while j<len(points)-1:
    found=None
    for k in range(len(points)-1,j,-1):
        found=next((q for q in options(points[j],points[k]) if all(allowed(a,z) for a,z in zip(q,q[1:]))),None)
        if found:break
    assert found;simple.extend(found[1:]);j=k
for t in target:b.Remove(t)
track(b,net,[(x-103,y-96) for x,y in simple],width,p.B_Cu)
for t in b.GetTracks():t.SetLocked(False)
refill(b,path);print(len(target),'->',len(simple)-1,'bridge segments')
