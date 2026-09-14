"""Close a remaining cross-pod reset connection on In2.Cu, preserving In1 ground.

Uses existing reset vias; no new drilled holes. KiCad refills the power plane
around this short signal exception and independently checks connectivity/DRC.
"""
from pathlib import Path
import sys,json,heapq,math
import pcbnew as p
from plane_fanout import xy,dist,point_line,line_rect,segment_dist
HW=Path(__file__).resolve().parents[1]/'hardware'
def finish(i,net='RING_nRESET',layer=p.In2_Cu,endpoints=None):
    path=HW/f'verification/routing/pod-{i}/pod-{i}-routed.kicad_pcb';b=p.LoadBoard(str(path))
    spec=json.loads((HW/'verification/placement/placement.json').read_text())['pods'][i]
    ox,oy=spec['origin'];w,h=spec['width'],spec['height'];cx0,cy0,cx1,cy1=spec['cutout']
    vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
    ends=[t for t in vias if t.GetNetname()==net]
    assert len(ends)>=2
    # Connect all reset vias on In2; existing outer-layer routes then remain valid.
    left=min(ends,key=lambda v:v.GetPosition().x);right=max(ends,key=lambda v:v.GetPosition().x)
    start,goal=xy(left.GetPosition()),xy(right.GetPosition())
    if endpoints:start,goal=endpoints
    obstacles=[xy(v.GetPosition()) for v in vias if v.GetNetname()!=net]
    copper=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetLayer()==layer and t.GetNetname()!=net]
    grid=.1
    def key(pt):return round((pt[0]-ox)/grid),round((pt[1]-oy)/grid)
    def pos(k):return ox+k[0]*grid,oy+k[1]*grid
    def allowed(a,z):
        for pt in [a,z]:
            x,y=pt[0]-ox,pt[1]-oy
            if not (.4<x<w-.4 and spec['top_edge']+.4<y<h-.4):return False
            if cx0-.34<x<cx1+.34 and cy0-.34<y<cy1+.34:return False
        if not all(point_line(q,a,z)>.455 for q in obstacles):return False
        for t in copper:
            c,d=xy(t.GetStart()),xy(t.GetEnd())
            if segment_dist(a,z,c,d)<.23:return False
        return True
    first,last=key(start),key(goal);queue=[(0,0,first)];cost={first:0};prev={};found=False
    while queue:
        _,c,k=heapq.heappop(queue)
        if c>cost[k]+1e-9:continue
        if k==last:found=True;break
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
            nk=(k[0]+dx,k[1]+dy);a=start if k==first else pos(k);z=goal if nk==last else pos(nk)
            if not allowed(a,z):continue
            nc=c+math.hypot(dx,dy)
            if nc<cost.get(nk,float('inf')):
                cost[nk]=nc;prev[nk]=k;heapq.heappush(queue,(nc+math.hypot(nk[0]-last[0],nk[1]-last[1]),nc,nk))
    assert found,('No In2 reset path',i)
    keys=[last]
    while keys[-1]!=first:keys.append(prev[keys[-1]])
    points=[start]+[pos(k) for k in reversed(keys[1:-1])]+[goal]
    simplified=[points[0]]
    for j in range(1,len(points)-1):
        a,z,c=simplified[-1],points[j],points[j+1]
        if abs((z[0]-a[0])*(c[1]-z[1])-(z[1]-a[1])*(c[0]-z[0]))>1e-7:simplified.append(z)
    simplified.append(goal)
    for a,z in zip(simplified,simplified[1:]):
        t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));t.SetEnd(p.VECTOR2I(p.FromMM(z[0]),p.FromMM(z[1])))
        t.SetWidth(p.FromMM(.15));t.SetLayer(layer);t.SetNet(left.GetNet());b.Add(t)
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
    print(i,net,p.LayerName(layer),'link segments',len(simplified)-1)
if __name__=='__main__':
    for i in map(int,sys.argv[1:]):finish(i)
