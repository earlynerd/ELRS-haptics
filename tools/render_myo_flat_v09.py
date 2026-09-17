"""Render actual v0.9 meshes; oval/taper assembly is explicitly a pose study."""
from pathlib import Path
import json, math
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'mechanical/myo-flat-v0.9';P=OUT/'print'
data=json.loads((OUT/'cad-checks.json').read_text());origins=data['shell_origins_mm'];terminal=data['terminal_main_origin_mm']
widths=[24]+[20]*7;gaps=data['gaps_flat_at_root_height_mm']
BG=(244,245,241);RIGID=(79,106,133);SOFT=(220,76,58)
def load(name):return trimesh.load_mesh(P/name)
def split(mesh):
    parent=list(range(len(mesh.vertices)))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for a,b,c in mesh.faces:parent[find(a)]=find(b);parent[find(c)]=find(b)
    groups={}
    for i,f in enumerate(mesh.faces):groups.setdefault(find(f[0]),[]).append(i)
    return [mesh.submesh([g],append=True,repair=False) for g in groups.values()]
def render(items,size,camera):
    camera=np.array(camera,dtype=float);camera/=np.linalg.norm(camera)
    right=np.cross([0,0,1],camera)
    if np.linalg.norm(right)<.01:right=np.array([1.,0,0])
    else:right/=np.linalg.norm(right)
    up=np.cross(camera,right);proj=[m.vertices@np.stack([right,up,camera]).T for m,c in items]
    pts=np.concatenate(proj);lo=pts[:,:2].min(0);hi=pts[:,:2].max(0);center=(lo+hi)/2
    scale=min((size[0]-30)/(hi[0]-lo[0]),(size[1]-30)/(hi[1]-lo[1]));tri=[]
    for (m,col),p in zip(items,proj):
        xy=(p[:,:2]-center)*scale;xy[:,0]+=size[0]/2;xy[:,1]=size[1]/2-xy[:,1]
        for f,n in zip(m.faces,m.face_normals):
            if n@camera<=.001:continue
            shade=np.clip(.69+.31*n@np.array([-.3,-.4,.86]),.4,1)
            tri.append((p[f,2].mean(),xy[f],tuple(int(v*shade) for v in col)))
    im=Image.new('RGB',size,BG);d=ImageDraw.Draw(im)
    for _,t,c in sorted(tri,key=lambda a:a[0]):d.polygon([tuple(v) for v in t],fill=c)
    return im
rigid=load('rigid-strip.stl');soft=load('tpu-end-flexures.stl')
im=Image.new('RGB',(1800,1370),BG);d=ImageDraw.Draw(im)
font=lambda n,b=False:ImageFont.truetype('arialbd.ttf' if b else 'arial.ttf',n)
d.text((45,30),'END RAILS + INWARD U-FOLDS',font=font(39,True),fill=(27,43,55))
d.text((47,88),'v0.9  |  Matches the red/blue sketch  |  Eight pods, sixteen planar flexures',font=font(24),fill=(75,94,107))
im.paste(render([(rigid,RIGID),(soft,SOFT)],(1710,510),[0,0,1]),(45,135))
d.text((60,650),'ACTUAL FLAT PRINT LAYOUT  /  approx. 217 x 72 mm',font=font(24,True),fill=(27,43,55))
d.text((60,689),'Main shell right half  →  seven satellites  →  main shell left half. One lid joins the two ends.',font=font(22),fill=(75,94,107))
cr=load('coupon-rigid.stl');cs=load('coupon-tpu.stl')
im.paste(render([(cr,RIGID),(cs,SOFT)],(810,440),[.55,-1,1.9]),(40,774))
d.text((65,1220),'TWO-POD PRINT COUPON',font=font(23,True),fill=(27,43,55))
d.text((65,1259),'One fold at each end. Open center for the harness.',font=font(21),fill=(75,94,107))
d.text((65,1293),'The two folds can open by different amounts.',font=font(21),fill=(75,94,107))

# Oval and mild taper demonstration: each pod stays rigid under its transform.
# Soft mesh interpolation communicates the pose; it is not a constitutive model.
a,b=1.2,1.;per=math.pi*(3*(a+b)-math.sqrt((3*a+b)*(a+3*b)))
a*=195/per;b*=195/per;beta=math.radians(5)
bases=[]
for angle in data['reference_angles_rad']:
    phi=math.pi/2-angle;center=np.array([a*math.cos(phi),b*math.sin(phi),0.])
    n=np.array([math.cos(phi)/a,math.sin(phi)/b,0.]);n/=np.linalg.norm(n)
    t=np.array([n[1],-n[0],0.]);z=np.array([0.,0,1.])
    axial=z*math.cos(beta)+n*math.sin(beta);normal=n*math.cos(beta)-z*math.sin(beta)
    bases.append((center,t,axial,normal))
def point(i,x,y,z,origin=None):
    c,t,ax,n=bases[i];origin=origins[i] if origin is None else origin
    return c+t*(x-origin-widths[i]/2)+ax*y+n*z
def posed(mesh,i,origin=None):
    m=mesh.copy();m.vertices=np.array([point(i,*v,origin) for v in m.vertices]);m.invert();return m
ring=[]
for m in split(rigid):
    if m.bounds[0,0]>terminal-.01:ring.append((posed(m,0,terminal),RIGID));continue
    i=next(i for i in range(8) if origins[i]-.01<=m.bounds[0,0] and m.bounds[1,0]<=origins[i]+widths[i]+.01)
    ring.append((posed(m,i),RIGID))
for i in range(8):
    m=load('main-bridge-lid.stl' if i==0 else 'satellite-lid.stl');m.apply_translation([origins[i],0,9.5]);ring.append((posed(m,i),RIGID))
v,f=trimesh.remesh.subdivide_to_size(soft.vertices,soft.faces,max_edge=1.0)
points=[]
for x,y,z in v:
    if x>=terminal:p=point(0,x,y,z,terminal)
    else:
        for i in range(8):
            edge=origins[i]+widths[i];end=edge+gaps[i]
            if x<=edge:p=point(i,x,y,z);break
            if x<end:
                u=(x-edge)/gaps[i];j=(i+1)%8
                p=(1-u)*point(i,edge,y,z)+u*point(j,end,y,z,terminal if j==0 else None);break
    points.append(p)
m=trimesh.Trimesh(points,f);m.invert();ring.append((m,SOFT))
im.paste(render(ring,(835,455),[1.3,1.7,1.25]),(910,760))
d.text((935,1220),'OVAL + TAPER POSE STUDY',font=font(23,True),fill=(27,43,55))
d.text((935,1259),'Rigid pods tilted 5 degrees around an oval reference.',font=font(21),fill=(75,94,107))
d.text((935,1293),'Illustrates conformity; does not predict force or strain.',font=font(21),fill=(75,94,107))
im.save(OUT/'design-overview.png')
render([(cr,RIGID),(cs,SOFT)],(1300,1000),[0,0,1]).save(OUT/'planar-flexure-detail.png')
print(OUT/'design-overview.png')
