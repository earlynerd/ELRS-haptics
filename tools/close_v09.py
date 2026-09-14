"""Complete selected outer-layer links without cutting either inner power plane."""
import sys,json,heapq,math
import pcbnew as p
from routing_v08 import HW,OUT,vec,track,via,pad,refill
from plane_fanout import xy,point_line,segment_dist,line_rect
PATH=OUT/'complete-input-routed.kicad_pcb'
def stubs():
    b=p.LoadBoard(str(OUT/'prepared.kicad_pcb'))
    track(b,'POD_3V3',[(6.31,.85),(6.31,1.8)],.2);via(b,'POD_3V3',(6.31,1.8))
    track(b,'GND',[(1.05,5.55),(2.35,5.55)],.2);via(b,'GND',(2.35,5.55))
    track(b,'GND',[(7.58,.85),(7.58,1.8)],.2);via(b,'GND',(7.58,1.8))
    track(b,'GND',[(13.65,9.07),(13.65,8.4)],.2);via(b,'GND',(13.65,8.4))
    track(b,'POD_3V3',[(14.7,9.04),(15.35,9.04)],.2);via(b,'POD_3V3',(15.35,9.04))
    track(b,'POD_3V3',[(14.21,3.9),(14.21,4.6)],.2);via(b,'POD_3V3',(14.21,4.6))
    track(b,'RING_nRESET',[(1.1,18),(2.5,18)],.2);via(b,'RING_nRESET',(2.5,18))
    track(b,'RING_RETURN',[(1.1,22),(1.1,23.6)],.2);via(b,'RING_RETURN',(1.1,23.6))
    track(b,'RING_RETURN',[(15.9,22),(14.9,22)],.2);via(b,'RING_RETURN',(14.9,22))
    net=pad(b,'U9','A3').GetNetname()
    track(b,net,[(13.5,22.3),(13.9,21.9),(13.9,21.6)],.11);via(b,net,(13.9,21.6),.5,.2)
    track(b,net,[(15.35,25.85),(15.35,26.9)],.2);via(b,net,(15.35,26.9))
    refill(b,OUT/'complete-input.kicad_pcb')
def route(net,start,end,path=PATH,width=.2,origin=(103,96)):
    b=p.LoadBoard(str(path));layer=p.B_Cu
    ox,oy=origin
    start=(ox+start[0],oy+start[1]);end=(ox+end[0],oy+end[1])
    vias=[(xy(v.GetPosition()),p.ToMM(v.GetWidth(layer))/2) for v in b.GetTracks() if isinstance(v,p.PCB_VIA) and v.GetNetname()!=net]
    tracks=[(xy(t.GetStart()),xy(t.GetEnd()),p.ToMM(t.GetWidth())/2) for t in b.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetLayer()==layer and t.GetNetname()!=net]
    grid=.05
    def key(q):return round((q[0]-ox)/grid),round((q[1]-oy)/grid)
    def pos(k):return ox+k[0]*grid,oy+k[1]*grid
    def allowed(a,z):
        if line_rect(a,z,(ox+4,oy+10,ox+11,oy+25),.34):return False
        for q in [a,z]:
            x,y=q[0]-ox,q[1]-oy
            if not (.35<x<16.65 and .35<y<34.65):return False
            if 3.66<x<11.34 and 9.66<y<25.34:return False
        if any(point_line(q,a,z)<r+width/2+.205 for q,r in vias):return False
        return not any(segment_dist(a,z,c,d)<r+width/2+.205 for c,d,r in tracks)
    first,last=key(start),key(end);queue=[(0,0,first)];cost={first:0};prev={};found=False
    while queue:
        _,c,k=heapq.heappop(queue)
        if c>cost[k]+1e-9:continue
        if k==last:found=True;break
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
            nk=(k[0]+dx,k[1]+dy);a=start if k==first else pos(k);z=end if nk==last else pos(nk)
            if not allowed(a,z):continue
            nc=c+math.hypot(dx,dy)
            if nc<cost.get(nk,float('inf')):
                cost[nk]=nc;prev[nk]=k;heapq.heappush(queue,(nc+math.hypot(nk[0]-last[0],nk[1]-last[1]),nc,nk))
    assert found,('No bottom path',net,start,end)
    keys=[last]
    while keys[-1]!=first:keys.append(prev[keys[-1]])
    pts=[start]+[pos(k) for k in reversed(keys[1:-1])]+[end]
    # String-pull using collision checks; reduces grid staircases to clean runs.
    def regular(a,z):
        dx,dy=abs(a[0]-z[0]),abs(a[1]-z[1]);return min(dx,dy)<.000002 or abs(dx-dy)<.000002
    simple=[pts[0]];j=0
    while j<len(pts)-1:
        k=len(pts)-1
        while k>j+1 and (not allowed(pts[j],pts[k]) or not regular(pts[j],pts[k])):k-=1
        simple.append(pts[k]);j=k
    track(b,net,[(x-103,y-96) for x,y in simple],width,layer)
    refill(b,path);print(net,len(simple)-1,'segments')
if __name__=='__main__':
    if sys.argv[1]=='stubs':stubs()
    else:
        net=sys.argv[1];start=tuple(map(float,sys.argv[2].split(',')));end=tuple(map(float,sys.argv[3].split(',')))
        route(net,start,end)
