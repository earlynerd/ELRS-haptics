"""Editable, rectilinear fit-only shells and reference gauges. No CAD kernel required.

Boundary meshes are generated from occupied rectangular cells, not overlapping
STL boxes. Lids are plain tape-retained coupons; final TPU links and clips await fit.
"""
from pathlib import Path
import json, itertools, hashlib
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/fit-mockup';OUT.mkdir(parents=True,exist_ok=True)
P=json.loads((ROOT/'hardware/verification/placement/placement.json').read_text())
report=[]
def mesh_boxes(name,positive,negative=(),reference=False):
    boxes=positive+list(negative)
    axes=[sorted(set(b[k] for b in boxes)|set(b[k+3] for b in boxes)) for k in range(3)]
    shape=tuple(len(a)-1 for a in axes);filled=set()
    def inside(pt,b):return all(b[i]<pt[i]<b[i+3] for i in range(3))
    for idx in itertools.product(*(range(n) for n in shape)):
        pt=[(axes[d][idx[d]]+axes[d][idx[d]+1])/2 for d in range(3)]
        if any(inside(pt,b) for b in positive) and not any(inside(pt,b) for b in negative):filled.add(idx)
    vertices=[];faces=[];lookup={}
    # Each face has outward winding. Adjacent occupied cells share no internal faces.
    face_defs=[((-1,0,0),[(0,0,0),(0,0,1),(0,1,1),(0,1,0)]),((1,0,0),[(1,0,0),(1,1,0),(1,1,1),(1,0,1)]),((0,-1,0),[(0,0,0),(1,0,0),(1,0,1),(0,0,1)]),((0,1,0),[(0,1,0),(0,1,1),(1,1,1),(1,1,0)]),((0,0,-1),[(0,0,0),(0,1,0),(1,1,0),(1,0,0)]),((0,0,1),[(0,0,1),(1,0,1),(1,1,1),(0,1,1)])]
    for idx in sorted(filled):
        for delta,corners in face_defs:
            if tuple(idx[d]+delta[d] for d in range(3)) in filled:continue
            ids=[]
            for c in corners:
                key=tuple(axes[d][idx[d]+c[d]] for d in range(3))
                if key not in lookup:lookup[key]=len(vertices);vertices.append(key)
                ids.append(lookup[key])
            faces.extend([(ids[0],ids[1],ids[2]),(ids[0],ids[2],ids[3])])
    m=trimesh.Trimesh(vertices=np.array(vertices),faces=np.array(faces),process=False)
    folder=OUT/('reference-only' if reference else 'print');folder.mkdir(exist_ok=True)
    file=folder/(name+'.stl');m.export(file)
    reread=trimesh.load_mesh(file)
    assert reread.is_watertight and reread.is_winding_consistent and reread.volume>0,name
    assert np.isfinite(reread.vertices).all() and reread.area_faces.min()>1e-10,name
    parent=list(range(len(reread.vertices)))
    def find(a):
        while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
        return a
    for face in reread.faces:
        for a,b in zip(face,face[1:]):parent[find(int(a))]=find(int(b))
    assert len({find(i) for i in range(len(parent))})==1,name
    report.append({'file':str(file.relative_to(OUT)),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'watertight':True,'one_connected_mesh':True,'bounds_mm':reread.bounds.tolist(),'volume_mm3':float(reread.volume),'faces':len(reread.faces)})
for main in [False,True]:
    s=P['pods'][0 if main else 1];w,h,t=s['shell'];name='main' if main else 'satellite'
    wall=1.2;floor=1;cx,cy=[a+1.5 for a in s['lra_center']]
    # Flat bottom is the rigid LRA bonding surface, z=1.0. No battery shelf.
    pos=[(0,0,0,w,h,9.5)]
    neg=[(wall,wall,floor,w-wall,h-wall,10)]
    # Open wire notches at the axial LRA datum. Leads require external strain relief.
    neg.extend([(-.1,cy-7,3.3,wall+.1,cy+7,5.7),(w-wall-.1,cy-7,3.3,w+.1,cy+7,5.7)])
    if main:
        usb=P['components']['J2'];ux=usb['x']+1.5
        neg.append((ux-4.8,h-wall-.1,2.6,ux+4.8,h+.1,6.5))
        sw=P['components']['SW3'];sy=sw['y']+1.5
        neg.append((w-wall-.1,sy-1.6,2.8,w+.1,sy+1.6,5.8))
    mesh_boxes(name+'-shell',pos,neg)
    # Plain lid with LED window. Temporary tape retention avoids speculative clips.
    holes=[]
    if main:
        led=P['components']['D1'];x,y=led['x']+1.5,led['y']+1.5
        holes=[(x-1.2,y-1.2,-.1,x+1.2,y+1.2,1.1)]
    mesh_boxes(name+'-lid',[(0,0,0,w,h,1)],holes)
    x0,y0,x1,y1=s['cutout']
    mesh_boxes(name+'-pcb-gauge',[(0,s['top_edge'],0,s['width'],s['height'],.8)],[(x0,y0,-.1,x1,y1,.9)],True)
mesh_boxes('protected-cell-body-12x32x3',[(0,0,0,12,32,3)],reference=True)
mesh_boxes('LRA-body-4x12x3p5',[(0,0,0,4,12,3.5)],reference=True)
(OUT/'mesh-checks.json').write_text(json.dumps({'status':'PASS','files':report,'scope':'Reopened STL topology, winding, connectedness, finite geometry, dimensions. No print, wrist fit, assembly or electronics qualification.'},indent=2)+'\n')
(OUT/'README.md').write_text('''# First fit mockup — revision 0.6

Print **seven satellite shells/lids and one main shell/lid** from `print/`, in millimetres. These are simple flat fit coupons: 20 × 38 × 10.5 mm regular, 24 × 64 × 10.5 mm main when closed. Shells print floor down; lids print flat. The 14 mm wire mouths have a 2.4 mm-high opening and need a short bridge in an upright shell print; inspect the sliced bridge. Use temporary tape to retain the lids and an external elastic wrap for a wrist size trial. There are no clips, final TPU links or clasp yet.

The `reference-only/` meshes are rigid **nonfunctional gauges**, kept separate from printable housing parts. The cell gauge represents only the nominal 12 × 32 × 3 mm protected battery body, not leads, expansion or tolerance. The LRA gauge excludes its adhesive, foam and flex tail. PCB gauges simplify the native board chamfers into square corners; use native PCB outlines for the eventual manufactured boards.

Cells bond to the lid inner surface; there is no compartment or shelf. The flat 1 mm shell floor is the LRA bonding surface. The PCB datum is 2 mm above the shell's wrist face. These first coupons do not include PCB retention/support ledges: use removable 1 mm spacers above the 1 mm floor for a bench fit trial. Do not populate cells during an unsupported PCB fit test. Final supports must avoid components and wire terminations.

Main shell openings follow the current USB and side-button placement; the LED has a 2.4 mm square lid window. No light pipe/button extender is modeled. The main cell allocation remains x=5..19, y=22..56 mm; regular allocation x=3..17, y=2..36 mm. Battery allocation z=5.8..9.3 mm, adhesive z=9.3..9.5 mm. Check a physical sample with its factory PCM and lead bend. LRA lands are 1 mm offset from the old centred-opening study to accommodate the tail.

`mesh-checks.json` records successful post-export watertightness, winding, single connected mesh, positive volume and dimensions for each STL. These checks establish mesh integrity only. The 195 mm wrist fit, curved contact pressure, material flexibility, cable strain, actual component heights, tail folding, lid removal, and RF performance remain physical design work.

Regenerate with the bundled dependency Python and `tools/build_fit_mockup.py`. Source geometry is the editable Python plus the native placement JSON. These STL coupons are not a finished wearable enclosure or STEP solids.
''',encoding='utf-8')
print(f'PASS: {len(report)} exported and reopened fit meshes.')
