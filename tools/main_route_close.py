"""Bounded octilinear outer-layer repair router with native DRC as final authority."""
import sys,json,math,heapq,time
import numpy as np
import pcbnew as p
from main_routing import OUT,load,save,track,via,vec,xy
G=.025;OX=35;OY=40;NX=841;NY=2241
def route(b,net,start,end,slayers,elayers,width=.1524,allowvia=True):
 # Layer 0 is front and layer 1 back. Ground/power pours are refilled afterwards.
 blocked=np.zeros((2,NY,NX),dtype=bool);vblocked=np.zeros((NY,NX),dtype=bool)
 def region(bb):
  x0=max(0,int(math.floor((bb[0]-OX)/G)));x1=min(NX,int(math.ceil((bb[2]-OX)/G))+1)
  y0=max(0,int(math.floor((bb[1]-OY)/G)));y1=min(NY,int(math.ceil((bb[3]-OY)/G))+1)
  return x0,x1,y0,y1
 def rect(arr,bb,margin):
  x0,x1,y0,y1=region((bb[0]-margin,bb[1]-margin,bb[2]+margin,bb[3]+margin));arr[y0:y1,x0:x1]=True
 def capsule(arr,a,z,r):
  x0,x1,y0,y1=region((min(a[0],z[0])-r,min(a[1],z[1])-r,max(a[0],z[0])+r,max(a[1],z[1])+r))
  if x0>=x1 or y0>=y1:return
  yy,xx=np.mgrid[y0:y1,x0:x1];xx=OX+xx*G;yy=OY+yy*G;dx=z[0]-a[0];dy=z[1]-a[1];den=dx*dx+dy*dy
  t=np.clip(((xx-a[0])*dx+(yy-a[1])*dy)/den,0,1) if den else 0
  arr[y0:y1,x0:x1] |= (xx-a[0]-t*dx)**2+(yy-a[1]-t*dy)**2 < r*r
 layers=[p.F_Cu,p.B_Cu];margin=.153+width/2
 for f in b.GetFootprints():
  for d in f.Pads():
   bb=d.GetBoundingBox();box=tuple(p.ToMM(v) for v in [bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom()])
   rect(vblocked,box,.14) # keep every via hole out of every solder land
   if d.GetNetname()!=net:
    for i,l in enumerate(layers):
     if d.IsOnLayer(l):
      if d.GetShape()==p.PAD_SHAPE_CIRCLE:capsule(blocked[i],xy(d.GetPosition()),xy(d.GetPosition()),p.ToMM(d.GetSize().x)/2+(max(margin,.205+width/2) if d.GetAttribute()==p.PAD_ATTRIB_NPTH else margin))
      else:rect(blocked[i],box,margin)
    if d.GetShape()==p.PAD_SHAPE_CIRCLE:capsule(vblocked,xy(d.GetPosition()),xy(d.GetPosition()),p.ToMM(d.GetSize().x)/2+.408)
    else:rect(vblocked,box,.408)
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA):
   q=xy(t.GetPosition());same=t.GetNetname()==net
   capsule(vblocked,q,q,.46 if same else .158+.25+p.ToMM(t.GetWidth(p.F_Cu))/2)
   if not same:
    for a in blocked:capsule(a,q,q,p.ToMM(t.GetWidth(p.F_Cu))/2+margin)
  elif t.GetNetname()!=net:
   a,z=xy(t.GetStart()),xy(t.GetEnd());r=p.ToMM(t.GetWidth())/2
   if t.GetLayer() in layers:capsule(blocked[layers.index(t.GetLayer())],a,z,r+margin)
   capsule(vblocked,a,z,r+.408)
 # Conservative outline/cutout clipping, including the corner chamfers.
 yy,xx=np.mgrid[0:NY,0:NX];xx=OX+xx*G;yy=OY+yy*G
 def edges(radius):
  m=.205+radius
  return (xx<35+m)|(xx>56-m)|(yy<40.1+m)|(yy>96-m)|((xx>41-m)&(xx<48+m)&(yy>58-m)&(yy<73+m))|((xx+yy)<75.8+m*1.42)|((yy-xx)>60.3-m*1.42)|((xx+yy)>151.3-m*1.42)|((xx-yy)>15.2-m*1.42)
 blocked|=edges(width/2)[None,:,:];vblocked|=edges(.25)
 def key(q):return int(round((q[0]-OX)/G)),int(round((q[1]-OY)/G))
 def point(k):return OX+k[0]*G,OY+k[1]*G
 sx,sy=key(start);ex,ey=key(end);starts=[(sx,sy,l) for l in slayers if not blocked[l,sy,sx]];goals={(ex,ey,l) for l in elayers if not blocked[l,ey,ex]}
 if not starts or not goals:return False,'blocked endpoint'
 queue=[];cost={};prev={};serial=0
 for k in starts:cost[k]=0;heapq.heappush(queue,(0,0,serial,k));serial+=1
 moves=[(1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.414214),(1,-1,1.414214),(-1,1,1.414214),(-1,-1,1.414214)]
 begin=time.monotonic();last=None
 while queue:
  _,c,_,k=heapq.heappop(queue)
  if c>cost[k]+1e-7:continue
  if k in goals:last=k;break
  if time.monotonic()-begin>30:return False,'search timeout'
  x,y,l=k
  nxt=[]
  for dx,dy,w in moves:
   nx,ny=x+dx,y+dy
   if not(0<=nx<NX and 0<=ny<NY) or blocked[l,ny,nx]:continue
   if dx and dy and (blocked[l,y,nx] or blocked[l,ny,x]):continue
   nxt.append(((nx,ny,l),w))
  if allowvia and not vblocked[y,x] and not blocked[1-l,y,x]:nxt.append(((x,y,1-l),60))
  for nk,w in nxt:
   nc=c+w
   if nc>=cost.get(nk,float('inf')):continue
   cost[nk]=nc;prev[nk]=k;dx,dy=abs(nk[0]-ex),abs(nk[1]-ey);heur=max(dx,dy)+.414214*min(dx,dy)
   heapq.heappush(queue,(nc+heur,nc,serial,nk));serial+=1
 if last is None:return False,'no path'
 ks=[last]
 while ks[-1] in prev:ks.append(prev[ks[-1]])
 ks.reverse();parts=[];pts=[start]
 def regular_append(a,z):
  dx,dy=z[0]-a[0],z[1]-a[1];v=min(abs(dx),abs(dy));bend=(a[0]+math.copysign(v,dx),a[1]+math.copysign(v,dy))
  return [bend,z] if math.dist(a,bend)>1e-8 and math.dist(bend,z)>1e-8 else [z]
 pts+=regular_append(start,point(ks[0]));current=ks[0][2]
 for i,k in enumerate(ks[1:],1):
  if k[2]!=current:
   parts.append((current,pts));q=point(k);via(b,net,q);pts=[q];current=k[2]
  else:
   prevk=ks[i-1];nextk=ks[i+1] if i+1<len(ks) else None
   if nextk and nextk[2]==k[2] and (k[0]-prevk[0],k[1]-prevk[1])==(nextk[0]-k[0],nextk[1]-k[1]):continue
   pts.append(point(k))
 pts+=regular_append(pts[-1],end);parts.append((current,pts))
 def clearline(a,z,l):
  n=max(2,int(math.dist(a,z)/G*3)+1)
  xs=np.rint((np.linspace(a[0],z[0],n)-OX)/G).astype(int);ys=np.rint((np.linspace(a[1],z[1],n)-OY)/G).astype(int)
  return not blocked[l,ys,xs].any()
 compact=[]
 for l,pts in parts:
  out=[pts[0]];i=0
  while i<len(pts)-1:
   found=False
   for j in range(len(pts)-1,i,-1):
    a,z=pts[i],pts[j];dx,dy=z[0]-a[0],z[1]-a[1];d=min(abs(dx),abs(dy))
    for c in [(a[0]+math.copysign(d,dx),a[1]+math.copysign(d,dy)),(z[0]-math.copysign(d,dx),z[1]-math.copysign(d,dy))]:
     if clearline(a,c,l) and clearline(c,z,l):
      if math.dist(out[-1],c)>1e-7:out.append(c)
      if math.dist(out[-1],z)>1e-7:out.append(z)
      i=j;found=True;break
    if found:break
   if not found:i+=1;out.append(pts[i])
  compact.append((l,out))
 parts=compact
 for l,pts in parts:track(b,net,pts,width,layers[l])
 return True,{'segments':sum(len(q)-1 for _,q in parts),'length':round(sum(math.dist(a,z) for _,q in parts for a,z in zip(q,q[1:])),3),'paths':parts}

def close(stem,report):
 b=load(stem);drc=json.loads((OUT/report).read_text());items={str(x.m_Uuid.AsString()):x for x in b.GetTracks()}
 for f in b.GetFootprints():
  for d in f.Pads():items[str(d.m_Uuid.AsString())]=d
 def endpoints(t):
  if isinstance(t,p.PCB_VIA):return [(xy(t.GetPosition()),[0,1])]
  if isinstance(t,p.PCB_TRACK):return [(xy(t.GetStart()),[0 if t.GetLayer()==p.F_Cu else 1]),(xy(t.GetEnd()),[0 if t.GetLayer()==p.F_Cu else 1])]
  return [(xy(t.GetPosition()),[i for i,l in enumerate([p.F_Cu,p.B_Cu]) if t.IsOnLayer(l)])]
 results=[]
 for v in drc['unconnected_items']:
  a,z=[items.get(i['uuid']) for i in v['items']]
  if a is None or z is None:continue
  choices=sorted([(math.dist(s,e),s,e,sl,el) for s,sl in endpoints(a) for e,el in endpoints(z)])
  net=a.GetNetname();ok=False;info=''
  for _,s,e,sl,el in choices:
   ok,info=route(b,net,s,e,sl,el)
   if ok:break
  print(net,ok,{k:v for k,v in info.items() if k!='paths'} if isinstance(info,dict) else info,flush=True);results.append((net,ok,info))
 save(b,'closed');(OUT/'close-results.json').write_text(json.dumps(results,indent=2))
if __name__=='__main__':close(sys.argv[1],sys.argv[2])
