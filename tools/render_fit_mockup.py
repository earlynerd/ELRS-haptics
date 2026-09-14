"""Create an exploded SVG directly from the exported fit-coupon STL meshes."""
from pathlib import Path
import numpy as np,trimesh
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'mechanical/fit-mockup'
parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">','<rect width="1400" height="900" fill="#f5f4ef"/>','<g font-family="Arial,sans-serif" fill="#213944">']
def text(x,y,s,size=18):parts.append(f'<text x="{x}" y="{y}" font-size="{size}">{s}</text>')
text(55,55,'HAPTIC BRACELET / FIRST FIT COUPONS',29)
text(55,86,'Exploded views from the exported meshes. Spacing is exaggerated; dimensions are in mm.',18)
def render(name,offset,z,color,origin):
    m=trimesh.load_mesh(OUT/name);verts=m.vertices+np.array([offset[0],offset[1],z]);faces=m.faces
    polygons=[]
    rgb=tuple(int(color[k:k+2],16) for k in [1,3,5])
    for face in faces:
        vv=verts[face];normal=np.cross(vv[1]-vv[0],vv[2]-vv[0]);normal/=np.linalg.norm(normal)
        # Positive view vector has an exposed top and two side faces.
        if np.dot(normal,[.5,1,1])<=0:continue
        shade=.72+.28*max(normal[2],0)
        fill='#'+''.join(f'{int(c*shade):02x}' for c in rgb)
        xy=[(origin[0]+6*(x-.5*y),origin[1]+6*(.25*x+.35*y-zz)) for x,y,zz in vv]
        polygons.append((vv.mean(axis=0)@np.array([.5,1,1]),xy,fill))
    for _,xy,fill in sorted(polygons):
        pts=' '.join(f'{x:.2f},{y:.2f}' for x,y in xy);parts.append(f'<polygon points="{pts}" fill="{fill}" stroke="{fill}" stroke-width=".3"/>')
for main,origin in [(False,(285,610)),(True,(980,610))]:
    name='main' if main else 'satellite';w,h=(24,64) if main else (20,38)
    text(origin[0]-130,143,'MAIN POD / 24 × 64 × 10.5' if main else 'SATELLITE / 20 × 38 × 10.5',22)
    render('print/'+name+'-shell.stl',(0,0),0,'#73919d',origin)
    render('reference-only/LRA-body-4x12x3p5.stl',(w/2-3,h/2-6),1.5,'#c49b56',origin)
    render('reference-only/'+name+'-pcb-gauge.stl',(1.5,1.5),18,'#499b7b',origin)
    render('reference-only/protected-cell-body-12x32x3.stl',((w-12)/2,23 if main else 3),32,'#aebbc4',origin)
    render('print/'+name+'-lid.stl',(0,0),45,'#73919d',origin)
    labelx=origin[0]+165
    for y,label in [(385,'Plain lid'),(445,'Protected cell body'),(525,'PCB outline gauge'),(635,'Open shell / LRA seat')]:text(labelx,y,label,16)
text(55,837,'Print 7 satellite pairs + 1 main pair. Temporary tape closure; no TPU links or PCB supports yet.',19)
text(55,866,'Coloured reference bodies are fit gauges. Electronics, flex tails, wiring and final mounting features are omitted.',17)
parts.append('</g></svg>');(OUT/'exploded-preview.svg').write_text('\n'.join(parts),encoding='utf-8')
print('Rendered exported fit meshes to exploded-preview.svg')

