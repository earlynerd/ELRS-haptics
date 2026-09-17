"""Create the long USB pair from a clearance-checked center path."""
import sys,json,math
from main_routing import *

def offset(pts,d):
 seg=[]
 for a,z in zip(pts,pts[1:]):
  dx,dy=z[0]-a[0],z[1]-a[1];l=math.hypot(dx,dy);nx,ny=-dy/l*d,dx/l*d
  seg.append(((a[0]+nx,a[1]+ny),(z[0]+nx,z[1]+ny)))
 out=[seg[0][0]]
 for (a,z),(c,e) in zip(seg,seg[1:]):
  u=(z[0]-a[0],z[1]-a[1]);v=(e[0]-c[0],e[1]-c[1]);den=u[0]*v[1]-u[1]*v[0]
  if abs(den)<1e-8:continue
  t=((c[0]-a[0])*v[1]-(c[1]-a[1])*v[0])/den
  out.append((a[0]+t*u[0],a[1]+t*u[1]))
 out.append(seg[-1][1]);return out

if __name__=='__main__':
 b=load('usb-test');pts=json.loads((OUT/'usb-center-path.json').read_text())['paths'][0][1]
 # Merge collinear steps before creating the two mitered parallel paths.
 clean=[]
 for q in pts:
  clean.append(q)
  while len(clean)>2:
   a,c,z=clean[-3:];u=(c[0]-a[0],c[1]-a[1]);v=(z[0]-c[0],z[1]-c[1])
   if abs(u[0]*v[1]-u[1]*v[0])<1e-8 and u[0]*v[0]+u[1]*v[1]>0:clean.pop(-2)
   else:break
 data={}
 for net,d in [('Net-(U14-D+)',.1762),('Net-(U14-D-)',-.1762)]:
  q=offset(clean,d);track(b,net,q,.1524,p.B_Cu);data[net]=q
 for f in b.GetFootprints():
  if f.GetReference()=='R37':f.SetPosition(vec((37.7,81.4)))
 save(b,'usb-pair');(OUT/'usb-pair-paths.json').write_text(json.dumps(data,indent=2))
