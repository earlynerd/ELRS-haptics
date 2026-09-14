"""Short, checked surface stubs to ordinary through vias for satellite planes.

Conservative rectangular pad obstacles; native KiCad DRC remains authoritative.
No through via is placed in an SMD land, including same-net lands.
"""
import math
import pcbnew as p
def xy(v):return p.ToMM(v.x),p.ToMM(v.y)
def v(pt):return p.VECTOR2I(p.FromMM(pt[0]),p.FromMM(pt[1]))
def dist(a,b):return math.hypot(a[0]-b[0],a[1]-b[1])
def point_rect(q,box):
    return math.hypot(max(box[0]-q[0],0,q[0]-box[2]),max(box[1]-q[1],0,q[1]-box[3]))
def line_rect(a,b,box,margin):
    # Slab intersection against a conservatively expanded rectangle.
    lo,hi=0,1
    for j in range(2):
        delta=b[j]-a[j];mn=box[j]-margin;mx=box[j+2]+margin
        if abs(delta)<1e-8:
            if a[j]<mn or a[j]>mx:return False
        else:
            u,w=sorted(((mn-a[j])/delta,(mx-a[j])/delta));lo=max(lo,u);hi=min(hi,w)
            if lo>hi:return False
    return True
def point_line(q,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1];l=dx*dx+dy*dy
    t=max(0,min(1,((q[0]-a[0])*dx+(q[1]-a[1])*dy)/l)) if l else 0
    return dist(q,(a[0]+t*dx,a[1]+t*dy))
def segment_dist(a,b,c,d):
    def cross(u,v,w):return (v[0]-u[0])*(w[1]-u[1])-(v[1]-u[1])*(w[0]-u[0])
    if cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0:return 0
    return min(point_line(a,c,d),point_line(b,c,d),point_line(c,a,b),point_line(d,a,b))
def fanout(b,spec,selected=None):
    ox,oy=spec['origin'];w,h=spec['width'],spec['height'];cut=spec['cutout']
    cb=(ox+cut[0],oy+cut[1],ox+cut[2],oy+cut[3])
    pads=[]
    for f in sorted(b.GetFootprints(),key=lambda f:f.GetReference()):
        for pad in f.Pads():
            bb=pad.GetBoundingBox();box=(p.ToMM(bb.GetX()),p.ToMM(bb.GetY()),p.ToMM(bb.GetRight()),p.ToMM(bb.GetBottom()))
            pads.append((f.GetReference(),pad,box))
    vias=[];tracks=[];results=[];all_tracks=[]
    for item in b.GetTracks():
        if isinstance(item,p.PCB_VIA):vias.append((xy(item.GetPosition()),item.GetNetname()))
        else:
            rec=(xy(item.GetStart()),xy(item.GetEnd()),item.GetNetname(),p.ToMM(item.GetWidth()));all_tracks.append(rec)
            if item.GetLayer()==p.F_Cu:tracks.append(rec)
    # Small driver pads first so their constrained exits are not blocked by stubs.
    targets=[a for a in pads if ((a[0],a[1].GetNumber()) in selected if selected else a[1].GetNetname() in ['GND','POD_3V3'])]
    targets.sort(key=lambda a:(a[2][2]-a[2][0])*(a[2][3]-a[2][1]))
    for ref,pad,box in targets:
        if pad.GetNumber()=='B2' and ref.startswith('U'):continue # already joined to C2
        net=pad.GetNetname();start=xy(pad.GetPosition());width=.1 if ref in [f'U{i}' for i in range(3,11)] else (.3 if ref.startswith('J') else .15)
        candidates=[]
        for radius in [x*.05 for x in range(8,51)]:
            for angle in range(0,360,45):
                r=math.radians(angle);end=(round(start[0]+radius*math.cos(r),5),round(start[1]+radius*math.sin(r),5))
                candidates.append((radius,end))
        chosen=None
        for radius,end in candidates:
            if not (ox+.49<=end[0]<=ox+w-.49 and oy+spec['top_edge']+.49<=end[1]<=oy+h-.49):continue
            if point_rect(end,cb)<.49 or line_rect(start,end,cb,.25+width/2):continue
            bad=False
            for _,other,ob in pads:
                if point_rect(end,ob)<(.31 if other.GetNetname()==net else .38):bad=True;break
                if other.GetNetname()!=net and line_rect(start,end,ob,.15+width/2+.005):bad=True;break
            if bad:continue
            if any(dist(end,q)<.6 or (n!=net and point_line(q,start,end)<.38+width/2) for q,n in vias):continue
            if any(n!=net and point_line(end,a,z)<.38+tw/2 for a,z,n,tw in all_tracks):continue
            if any(n!=net and (point_line(end,a,z)<.38+tw/2 or segment_dist(start,end,a,z)<(width+tw)/2+.155) for a,z,n,tw in tracks):continue
            chosen=end;break
        if chosen is None:raise RuntimeError(('No safe plane via',ref,pad.GetNumber(),start))
        via=p.PCB_VIA(b);via.SetPosition(v(chosen));via.SetWidth(p.FromMM(.45));via.SetDrill(p.FromMM(.2));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(pad.GetNet());via.SetLocked(True);b.Add(via)
        track=p.PCB_TRACK(b);track.SetStart(v(start));track.SetEnd(v(chosen));track.SetWidth(p.FromMM(width));track.SetLayer(p.F_Cu);track.SetNet(pad.GetNet());track.SetLocked(True);b.Add(track)
        vias.append((chosen,net));tracks.append((start,chosen,net,width));results.append((ref,pad.GetNumber(),chosen))
    return results
