"""Render exported meshes; ring pose is an illustrative assembly, not FEA."""
from pathlib import Path
import json, math
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/flat-band-v0.8'
P=OUT/'print'
data=json.loads((OUT/'cad-checks.json').read_text())
starts=data['flat_shell_starts_mm']; widths=[24]+[20]*7
RIGID=(90,111,128); SOFT=(37,184,164); BG=(243,244,240)
def load(name):return trimesh.load_mesh(P/name)
def split(mesh):
    parent=list(range(len(mesh.vertices)))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for a,b,c in mesh.faces:parent[find(a)]=find(b);parent[find(c)]=find(b)
    groups={}
    for i,f in enumerate(mesh.faces):groups.setdefault(find(f[0]),[]).append(i)
    return [mesh.submesh([indices],append=True,repair=False) for indices in groups.values()]
rigid=load('rigid-strip.stl'); soft=load('tpu-links.stl')

def render(items,size,camera):
    camera=np.array(camera,dtype=float);camera/=np.linalg.norm(camera)
    right=np.cross([0,0,1],camera);right/=np.linalg.norm(right)
    up=np.cross(camera,right)
    projected=[m.vertices@np.stack([right,up,camera]).T for m,c in items]
    allp=np.concatenate(projected);lo=allp[:,:2].min(0);hi=allp[:,:2].max(0)
    scale=min((size[0]-35)/(hi[0]-lo[0]),(size[1]-35)/(hi[1]-lo[1]))
    center=(lo+hi)/2;faces=[]
    for (m,base),p in zip(items,projected):
        screen=(p[:,:2]-center)*scale;screen[:,0]+=size[0]/2;screen[:,1]=size[1]/2-screen[:,1]
        for f,n in zip(m.faces,m.face_normals):
            if n@camera<=.0001:continue
            shade=np.clip(.64+.36*(n@np.array([-.3,-.4,.86])),.35,1)
            faces.append((p[f,2].mean(),screen[f],tuple(int(v*shade) for v in base)))
    im=Image.new('RGB',size,BG);d=ImageDraw.Draw(im)
    for _,tri,col in sorted(faces,key=lambda f:f[0]):d.polygon([tuple(p) for p in tri],fill=col)
    return im

im=Image.new('RGB',(1700,1260),BG);d=ImageDraw.Draw(im)
font=lambda s,b=False:ImageFont.truetype('arialbd.ttf' if b else 'arial.ttf',s)
d.text((45,28),'FLAT PRINT  /  WRAP INTO A RING',font=font(38,True),fill=(26,43,54))
d.text((47,83),'v0.8   |   PET-GF15 shells + TPU hinges   |   195 mm wrist reference',font=font(23),fill=(78,94,105))
im.paste(render([(rigid,RIGID),(soft,SOFT)],(1590,410),[.25,-1.3,2]),(55,130))
d.text((65,540),'ONE ALIGNED TWO-MATERIAL STRIP',font=font(22,True),fill=(26,43,54))
d.text((65,574),'Approximately 221 x 72 mm. Shell floors and all TPU links start on the bed.',font=font(22),fill=(78,94,105))

detail_r=load('coupon-rigid.stl');detail_s=load('coupon-tpu.stl')
im.paste(render([(detail_r,RIGID),(detail_s,SOFT)],(770,405),[.85,-1.3,1.8]),(35,660))
d.text((65,1090),'INTERIOR AND HINGE ROOTS',font=font(23,True),fill=(26,43,54))
d.text((65,1130),'Native-outline PCB ledges; open wire corridors.',font=font(21),fill=(78,94,105))
d.text((65,1161),'The material overlap is resolved by the slicer.',font=font(21),fill=(78,94,105))

# Place exact rigid meshes tangentially around a circular reference. Soft meshes
# are deformed for communication only; this does not predict a relaxed band.
radius=195/(2*math.pi)
spans=[2*math.asin(w/(2*radius)) for w in widths]
ga=(2*math.pi-sum(spans))/8
angles=[0.]
for i in range(1,8):angles.append(angles[-1]+spans[i-1]/2+ga+spans[i]/2)
angles=[-t for t in angles]
def point(i,x,y,z):
    t=angles[i];x=x-starts[i]-widths[i]/2
    return np.array([x*math.cos(t)-(radius+z)*math.sin(t),x*math.sin(t)+(radius+z)*math.cos(t),y])
def transform(m,i):
    m=m.copy();m.vertices=np.array([point(i,*v) for v in m.vertices]);m.invert();return m
ring=[]
for i in range(8):
    pieces=[m for m in split(rigid) if starts[i]-.01<=m.bounds[0,0] and m.bounds[1,0]<=starts[i]+widths[i]+.01]
    for m in pieces:ring.append((transform(m,i),RIGID))
    m=load('main-lid.stl' if i==0 else 'satellite-lid.stl');m.apply_translation([starts[i],0,9.5])
    ring.append((transform(m,i),RIGID))
for m in split(soft):
    if m.bounds[0,0]>starts[7]:
        v,f=trimesh.remesh.subdivide_to_size(m.vertices,m.faces,max_edge=.7)
        bent=[];end=starts[7]+widths[7];gap=data['flex_gap_mm']
        for x,y,z in v:
            q=x-end
            if q<0:p=point(7,x,y,z)
            elif q<gap:p=(1-q/gap)*point(7,end,y,z)+(q/gap)*point(0,0,y,z)
            elif q<gap+12.7:p=point(0,0,y,z+(q-gap)*11.3/12.7)
            else:p=point(0,q-gap-12.7,y,z+11.3)
            bent.append(p)
        b=trimesh.Trimesh(bent,f);b.invert();ring.append((b,SOFT));continue
    i=next(i for i in range(7) if starts[i]+widths[i]-3<=m.bounds[0,0]<=starts[i]+widths[i])
    v,f=trimesh.remesh.subdivide_to_size(m.vertices,m.faces,max_edge=1.0)
    bent=[];edge=starts[i]+widths[i];nextedge=starts[i+1]
    for x,y,z in v:
        if x<=edge:p=point(i,x,y,z)
        elif x>=nextedge:p=point(i+1,x,y,z)
        else:
            u=(x-edge)/(nextedge-edge)
            p=(1-u)*point(i,edge,y,z)+u*point(i+1,nextedge,y,z)
        bent.append(p)
    b=trimesh.Trimesh(bent,f);b.invert();ring.append((b,SOFT))
im.paste(render(ring,(780,430),[1.3,1.8,1.05]),(865,640))
d.text((890,1090),'ASSEMBLY POSE REFERENCE',font=font(23,True),fill=(26,43,54))
d.text((890,1130),'Lids fitted; bend the seven links around the wrist.',font=font(21),fill=(78,94,105))
d.text((890,1161),'Final TPU tabs wrap onto the main-lid buttons.',font=font(21),fill=(78,94,105))
d.text((45,1220),'Actual exported CAD meshes. Ring pose is illustrative; closure strain, wrist fit and printing remain unverified.',font=font(19),fill=(95,106,112))
im.save(OUT/'design-overview.png')

# Flat close-up of the exact main lid makes the fastening/button arrangement visible.
lid=load('main-lid.stl')
detail=render([(lid,RIGID)],(850,1000),[.6,-1.3,2.4])
detail.save(OUT/'main-lid-detail.png')
print(OUT/'design-overview.png')
