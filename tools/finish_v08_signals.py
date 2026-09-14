import sys, math
import pcbnew as p
from close_v08 import PATH,OUT,route
from routing_v08 import pad,track,via,refill
from plane_fanout import xy,point_rect,line_rect,point_line,segment_dist

def fan(ref,num):
    b=p.LoadBoard(str(PATH));target=pad(b,ref,num);net=target.GetNetname();start=xy(target.GetPosition());width=.15
    pads=[]
    for f in b.GetFootprints():
        for q in f.Pads():
            bb=q.GetBoundingBox();pads.append((q.GetNetname(),(p.ToMM(bb.GetX()),p.ToMM(bb.GetY()),p.ToMM(bb.GetRight()),p.ToMM(bb.GetBottom()))))
    ts=list(b.GetTracks());chosen=None
    for radius in [x*.1 for x in range(7,41)]:
        for angle in range(0,360,15):
            a=math.radians(angle);end=(start[0]+radius*math.cos(a),start[1]+radius*math.sin(a))
            if not (103.51<end[0]<119.49 and 96.51<end[1]<130.49):continue
            if line_rect(start,end,(107,106,114,121),.51):continue
            if any(point_rect(end,bb)<(.26 if n==net else .455) or (n!=net and line_rect(start,end,bb,.28)) for n,bb in pads):continue
            bad=False
            for t in ts:
                if isinstance(t,p.PCB_VIA):
                    q=xy(t.GetPosition());r=p.ToMM(t.GetWidth(p.F_Cu))/2
                    if math.dist(q,end)<r+.455 or (t.GetNetname()!=net and point_line(q,start,end)<r+.28):bad=True;break
                elif t.GetNetname()!=net:
                    a,z=xy(t.GetStart()),xy(t.GetEnd());r=p.ToMM(t.GetWidth())/2
                    if point_line(end,a,z)<r+.455 or (t.GetLayer()==p.F_Cu and segment_dist(start,end,a,z)<r+.28):bad=True;break
            if not bad:chosen=end;break
        if chosen:break
    assert chosen,(ref,num,'no via')
    local=lambda q:(q[0]-103,q[1]-96)
    track(b,net,[local(start),local(chosen)],width);via(b,net,local(chosen),.5,.2);refill(b,PATH)
    print(ref,num,local(chosen),net)
    return net,local(chosen)

if __name__=='__main__':
    if sys.argv[1]=='fan':fan(sys.argv[2],sys.argv[3])
