"""Render actual v0.10 meshes; oval/taper assembly is explicitly a pose study."""
from pathlib import Path
import json, math
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'mechanical/myo-flat-v0.10';P=OUT/'print'
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
            tri.append((p[f,2],xy[f],tuple(int(v*shade) for v in col)))
    # Per-pixel depth avoids false diagonal occlusion on long ribbon triangles.
    pixels=np.empty((size[1],size[0],3),dtype=np.uint8);pixels[:]=BG
    depth=np.full((size[1],size[0]),-np.inf)
    for z,t,c in tri:
        x0=max(0,int(np.floor(t[:,0].min())));x1=min(size[0]-1,int(np.ceil(t[:,0].max())))
        y0=max(0,int(np.floor(t[:,1].min())));y1=min(size[1]-1,int(np.ceil(t[:,1].max())))
        if x1<x0 or y1<y0:continue
        a,b,cpt=t;den=(b[1]-cpt[1])*(a[0]-cpt[0])+(cpt[0]-b[0])*(a[1]-cpt[1])
        if abs(den)<1e-10:continue
        yy,xx=np.mgrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
        u=((b[1]-cpt[1])*(xx-cpt[0])+(cpt[0]-b[0])*(yy-cpt[1]))/den
        v=((cpt[1]-a[1])*(xx-cpt[0])+(a[0]-cpt[0])*(yy-cpt[1]))/den
        w=1-u-v;zz=u*z[0]+v*z[1]+w*z[2]
        region=depth[y0:y1+1,x0:x1+1]
        mask=(u>=-1e-7)&(v>=-1e-7)&(w>=-1e-7)&(zz>region)
        region[mask]=zz[mask];pixels[y0:y1+1,x0:x1+1][mask]=c
    return Image.fromarray(pixels)
rigid=trimesh.load_mesh(OUT/'reference-only/render-rigid.stl');soft=load('tpu-end-flexures.stl')
im=Image.new('RGB',(1800,1370),BG);d=ImageDraw.Draw(im)
font=lambda n,b=False:ImageFont.truetype('arialbd.ttf' if b else 'arial.ttf',n)
d.text((45,30),'FULL-HEIGHT TPU RIBBONS',font=font(39,True),fill=(27,43,55))
d.text((47,88),'v0.10  |  1.2 mm wall x 9.5 mm height  |  Eight pods, sixteen ribbon flexures',font=font(24),fill=(75,94,107))
im.paste(render([(rigid,RIGID),(soft,SOFT)],(1710,510),[.15,-1,2.1]),(45,135))
d.text((60,650),'ACTUAL FLAT PRINT LAYOUT  /  approx. 239 x 72 mm',font=font(24,True),fill=(27,43,55))
d.text((60,689),'Whole wrist face + wall  →  seven satellites  →  whole outer face + complementary wall.',font=font(22),fill=(75,94,107))
cr=trimesh.load_mesh(OUT/'reference-only/render-coupon-rigid.stl');cs=load('coupon-tpu.stl')
im.paste(render([(cr,RIGID),(cs,SOFT)],(810,440),[.55,-1,1.9]),(40,774))
d.text((65,1220),'TWO-POD PRINT COUPON',font=font(23,True),fill=(27,43,55))
d.text((65,1259),'Thin ribbon wall, the same height as the rigid shell.',font=font(21),fill=(75,94,107))
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
for i in range(1,8):
    m=load('satellite-lid.stl');m.apply_translation([origins[i],0,9.5]);ring.append((posed(m,i),RIGID))
v,f=trimesh.remesh.subdivide_to_size(soft.vertices,soft.faces,max_edge=2.0)
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
render([(cr,RIGID),(cs,SOFT)],(1300,1000),[.65,-1.2,1.2]).save(OUT/'ribbon-flexure-detail.png')
print(OUT/'design-overview.png')

# Main closure, in local assembled coordinates. Exploded lift is illustrative.
lower=trimesh.load_mesh(OUT/'reference-only/render-main-lower.stl')
upper=trimesh.load_mesh(OUT/'reference-only/render-main-upper.stl')
ls=soft.submesh([np.flatnonzero(soft.triangles_center[:,0]<24.001)],append=True,repair=False)
us=soft.submesh([np.flatnonzero(soft.triangles_center[:,0]>terminal-.001)],append=True,repair=False)
us.apply_translation([-terminal,0,0])
upper_lift=upper.copy();upper_lift.apply_translation([0,0,18])
us_lift=us.copy();us_lift.apply_translation([0,0,18])
detail=Image.new('RGB',(1800,1200),BG);dd=ImageDraw.Draw(detail)
dd.text((45,25),'STEPPED MAIN CLAMSHELL',font=font(36,True),fill=(27,43,55))
dd.text((45,78),'Full wrist face + full outer face. Ribbon ends meet at the vertical wall handoff.',font=font(25),fill=(75,94,107))
detail.paste(render([(lower,RIGID),(upper_lift,(140,164,181)),(ls,SOFT),(us_lift,SOFT)],(860,910),[1,-1.6,.8]),(30,145))
detail.paste(render([(lower,RIGID),(upper,(140,164,181)),(ls,SOFT),(us,SOFT)],(850,910),[1,-1.6,.8]),(920,145))
dd.text((45,1080),'EXPLODED  /  upper half lifted for clarity',font=font(24,True),fill=(27,43,55))
dd.text((935,1080),'CLOSED  /  ribbon joints share Z = 0–9.5 mm',font=font(24,True),fill=(27,43,55))
dd.text((45,1130),'The wall handoff sits beside the USB aperture. Recessed screws stay within rounded pod ends.',font=font(23),fill=(75,94,107))
detail.save(OUT/'main-clamshell-detail.png')
