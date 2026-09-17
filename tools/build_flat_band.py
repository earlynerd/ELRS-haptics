"""Flat co-print housing prototype; dimensions in mm. Does not modify PCB sources.

Run with the installed Python314/build123d runtime. Mesh QA and rendering use
the bundled workspace Python. Earlier housing revisions remain untouched.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import math
import zipfile
from build123d import (Align, Axis, Box, Compound, Cone, Cylinder, Pos, Rot,
                       RectangleRounded, Edge, Wire, Face, offset, extrude, export_step, export_stl, import_step)
from build_myo_band import binary_stl_xml
from kicad_edit import load, children, child, uq

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical/flat-band-v0.8'
WALL, FLOOR, DEPTH, LID = 1.2, 1.0, 9.5, 1.2
WIDTHS = [24.] + [20.] * 7
HEIGHTS = [64.] + [38.] * 7
LINK_Y, LINK_W, OVERLAP = 13.5, 6., 2.5
BUTTON_Y = 18.0

def box(x, y, z, dx, dy, dz):
    return Pos(x,y,z) * Box(dx,dy,dz,align=(Align.MIN,Align.MIN,Align.MIN))

def roundplate(cx, cy, w, h, t, z=0, r=1.5):
    return Pos(cx,cy,z) * extrude(RectangleRounded(w,h,r), amount=t)

def cyl(x,y,z,r,h):
    return Pos(x,y,z)*Cylinder(r,h,align=(Align.CENTER,Align.CENTER,Align.MIN))

def anchors():
    board = load(ROOT/'hardware/main/main.kicad_pcb')
    result = {}
    for f in children(board,'footprint'):
        ref = next(uq(p[2]) for p in children(f,'property') if uq(p[1])=='Reference')
        if ref in ['J2','SW3','D1','J3']:
            at = child(f,'at')
            # Native common board origin 35,35; shell margin 1.5.
            # X circumferential, Y along arm; main shell centered at Y=0.
            result[ref] = [float(at[1])-35+1.5, float(at[2])-35+1.5-32]
    return result

def board_profiles(name):
    board=load(ROOT/'hardware'/name/(name+'.kicad_pcb'))
    origin=(33.5,65.5) if name=='main' else (101.5,113.5)
    def pt(e,key):
        x,y=map(float,child(e,key)[1:]);return (x-origin[0],y-origin[1],0)
    edges=[Edge.make_line(pt(e,'start'),pt(e,'end')) for e in children(board,'gr_line') if uq(child(e,'layer')[1])=='Edge.Cuts']
    edges += [Edge.make_three_point_arc(pt(e,'start'),pt(e,'mid'),pt(e,'end')) for e in children(board,'gr_arc') if uq(child(e,'layer')[1])=='Edge.Cuts']
    profiles=[Face(w) for w in Wire.combine(edges)]
    assert len(profiles)==2
    profiles.sort(key=lambda p:p.area,reverse=True)
    return profiles[0], profiles[0]-profiles[1]

def shell(w,h,main,a):
    s = roundplate(w/2,0,w,h,DEPTH)
    s -= roundplate(w/2,0,w-2*WALL,h-2*WALL,DEPTH+1,FLOOR,r=.3)
    # Open-top slots remove the old horizontal wire-mouth bridges.
    for x in [-.1,w-WALL-.1]:
        s -= box(x,-7,3.3,WALL+.2,14,DEPTH)
    if main:
        ux,uy = a['J2']
        # USB and button copied from current native footprints, not v0.6 JSON.
        s -= box(ux-4.8,h/2-WALL-.1,2.6,9.6,WALL+.2,DEPTH)
        bx,by = a['SW3']
        x = -.1 if bx < w/2 else w-WALL-.1
        s -= box(x,by-1.8,2.8,WALL+.2,3.6,DEPTH)
        rx,ry = a['J3']
        s -= roundplate(rx,ry,6.4,3.2,FLOOR+.2,-.1,r=.5)
    # Two external end bosses avoid the board and battery allocations.
    for sign in [-1,1]:
        y = sign*(h/2+2)
        sx=3.3 if main and sign==1 else w/2
        s += roundplate(sx,y-sign*.6,6,5.2,DEPTH,r=1.0)
        s -= cyl(sx,y,DEPTH-5,0.8,5.2)
    return s

def lid(w,h,main,a):
    s = roundplate(w/2,0,w,h,LID)
    for sign in [-1,1]:
        y = sign*(h/2+2)
        sx=3.3 if main and sign==1 else w/2
        s += roundplate(sx,y-sign*.6,6,5.2,LID,r=1.0)
        s -= cyl(sx,y,-.1,1.15,LID+.2)
    if main:
        x,y=a['D1']
        s -= roundplate(x,y,3,3,LID+.2,-.1,r=.4)
        # Broad filleted-by-taper retaining buttons, outside the electronics.
        # The TPU hole stretches over the 4.4 mm head onto a 2.8 mm neck.
        for y in [-BUTTON_Y,BUTTON_Y]:
            s += cyl(3.7,y,LID,1.4,1.4)
            s += Pos(3.7,y,LID+1.4)*Cone(1.4,2.2,.8,align=(Align.CENTER,Align.CENTER,Align.MIN))
            s += Pos(3.7,y,LID+2.2)*Cone(2.2,1.6,.6,align=(Align.CENTER,Align.CENTER,Align.MIN))
    return s

def save_stl(shape,path):
    assert shape.is_valid, path
    # OCCT tessellation can invalidate cached BRep checks on these offset edges.
    # Tessellate a copy so later CAD checks inspect the original exact geometry.
    export_stl(copy.deepcopy(shape),path,tolerance=.025,angular_tolerance=.12)

def package(parts,path,title):
    objects=[]
    for i,(name,p,soft) in enumerate(parts,2):
        v,t=binary_stl_xml(p)
        objects.append(f'<object id="{i}" type="model" name="{name}" pid="1" pindex="{int(soft)}"><mesh><vertices>{v}</vertices><triangles>{t}</triangles></mesh></object>')
    assembly=len(parts)+2
    model=f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
<metadata name="Title">{title}</metadata><resources>
<basematerials id="1"><base name="PET-GF15" displaycolor="#50616FFF"/><base name="TPU" displaycolor="#29B8A9FF"/></basematerials>
{''.join(objects)}<object id="{assembly}" type="model" name="{title}"><components>{''.join(f'<component objectid="{i}"/>' for i in range(2,assembly))}</components></object>
</resources><build><item objectid="{assembly}"/></build></model>'''
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr('3D/3dmodel.model',model)

def build(wrist,thickness):
    for d in ['print','cad','reference-only']:(OUT/d).mkdir(parents=True,exist_ok=True)
    a=anchors()
    # Developed skin path, not a claim of circular/oval wrist conformity.
    # Add pi*t for one complete turn at the flexible strip's neutral surface.
    gap=(wrist-sum(WIDTHS)+math.pi*thickness)/8
    assert gap>2, 'Pod widths leave insufficient flex length at this wrist size'
    starts=[0.]
    for w in WIDTHS[:-1]:starts.append(starts[-1]+w+gap)
    rigid=[]; soft=[]; cover=[]; contact=[]
    pcb_gauges=[]
    for i,(x,w,h) in enumerate(zip(starts,WIDTHS,HEIGHTS)):
        outline,profile=board_profiles('main' if i==0 else 'satellite')
        # Straight side ledges avoid both rounded PCB corners and tiny Boolean
        # slivers where offset arcs meet the rounded shell cavity.
        bounds=outline.bounding_box()
        y0,y1=bounds.min.Y+1.2,bounds.max.Y-1.2
        ledge=box(bounds.min.X-.4,y0,FLOOR,1.1,y1-y0,2-FLOOR)
        ledge+=box(bounds.max.X-.7,y0,FLOOR,1.1,y1-y0,2-FLOOR)
        s=Pos(x,0,0)*(shell(w,h,i==0,a)+ledge)
        pcb=Pos(x,0,2)*extrude(profile,amount=.8)
        assert (s&pcb).volume<1e-5
        pcb_gauges.append(pcb)
        rigid.append(s)
        l=lid(w,h,i==0,a)
        cover.append(Pos(x,0,DEPTH)*l)
        assert (cover[-1]&s).volume<1e-5
        if i==0:
            ux,_=a['J2']
            usb_probe=box(ux-4.8,HEIGHTS[0]/2-WALL,2.6,9.6,8,3.9)
            assert (usb_probe&s).volume<1e-5, 'USB opening obstructed'
        if i in [0,1]:save_stl(l,OUT/'print'/('main-lid.stl' if i==0 else 'satellite-lid.stl'))
    for i in range(7):
        x=starts[i]+WIDTHS[i]
        for y in [-LINK_Y,LINK_Y]:
            f=roundplate(x+gap/2,y,gap+2*OVERLAP,LINK_W,thickness,r=1.4)
            soft.append(f)
            contacts=[j for j,s in enumerate(rigid) if (f&s).volume>1e-5]
            assert contacts==[i,i+1],contacts
            contact.append({'gap':i,'y':y,'pods':contacts})
    # The eighth pair has a free end. It wraps up the main side onto lid buttons.
    # Extra 2 mm accommodates the folded seam. Tail length is a fit parameter.
    end=starts[-1]+WIDTHS[-1]
    button_distance=gap+DEPTH+LID+3.7+2.0
    tail_length=button_distance+6
    for sign in [-1,1]:
        # Splay the tabs outward so the closed strap clears the current LED.
        dy=sign*(BUTTON_Y-LINK_Y)
        dx=button_distance+OVERLAP
        angle=math.degrees(math.atan2(dy,dx))
        length=math.hypot(dx,dy)+6
        tail=Pos(end-OVERLAP,sign*LINK_Y,0)*Rot(0,0,angle)*roundplate(length/2,0,length,8,thickness,r=2.0)
        tail-=cyl(end+button_distance,sign*BUTTON_Y,-.1,1.45,thickness+.2)
        assert (tail&rigid[-1]).volume>0
        soft.append(tail)
    rb=Compound(children=rigid,label='PET_GF15_SHELLS')
    sb=Compound(children=soft,label='TPU_LINKS_AND_CLOSURE_TABS')
    save_stl(rb,OUT/'print/rigid-strip.stl')
    save_stl(sb,OUT/'print/tpu-links.stl')
    package([('Rigid shells',OUT/'print/rigid-strip.stl',False),('TPU links and tabs',OUT/'print/tpu-links.stl',True)],OUT/'print/flat-band.3mf','Flat band v0.8')
    # Two-pod coupon keeps the real shell roots and link geometry.
    coupon_r=Compound([rigid[i] for i in [1,2]])
    coupon_s=Compound(soft[2:4])
    save_stl(coupon_r,OUT/'print/coupon-rigid.stl')
    save_stl(coupon_s,OUT/'print/coupon-tpu.stl')
    package([('Coupon shells',OUT/'print/coupon-rigid.stl',False),('Coupon links',OUT/'print/coupon-tpu.stl',True)],OUT/'print/hinge-coupon.3mf','Two pod hinge coupon')
    assy=Compound(children=[rb,sb,Compound(children=cover)],label='FLAT_HOUSING_WITH_LIDS')
    export_step(assy,OUT/'cad/flat-band-with-lids.step')
    reopened=import_step(OUT/'cad/flat-band-with-lids.step')
    assert reopened.is_valid and len(reopened.solids())==32
    # Check pod reference envelopes; full component clearances are not inferred.
    gauges=[]
    for i,(x,w,h) in enumerate(zip(starts,WIDTHS,HEIGHTS)):
        battery=box(x+(5 if i==0 else 3),(22-32 if i==0 else 2-19),5.8,14,34,3.5)
        assert all((battery&s).volume<1e-6 for s in rigid)
        assert (battery&cover[i]).volume<1e-6
        gauges.append(battery)
    export_step(Compound(children=gauges),OUT/'reference-only/battery-allocations.step')
    export_step(Compound(children=pcb_gauges),OUT/'reference-only/native-board-outlines.step')
    checks={'status':'PASS','units':'mm','wrist_reference_mm':wrist,'hinge_thickness_mm':thickness,
      'flex_gap_mm':gap,'skin_developed_reference_mm':wrist,'neutral_developed_length_mm':wrist+math.pi*thickness,
      'flat_shell_starts_mm':starts,'tail_button_distance_mm':button_distance,'strip_length_mm':end+tail_length,
      'main_native_anchors_in_shell_coordinates':a,'rigid_solids':8,'soft_solids':16,'lid_solids':8,
      'step_reimport_valid':True,'step_reimport_solids':len(reopened.solids()),'link_contacts':contact,
      'battery_allocation_intersections_mm3':0,'bare_board_intersections_mm3':0,
      'board_support':'Side ledges referenced to native outline, Z=2 mm; 0.7 mm bearing width',
      'print_orientation':'Floor and links at Z=0; lids separate, exterior up',
      'source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'hardware/main/main.kicad_pcb',ROOT/'hardware/satellite/satellite.kicad_pcb',ROOT/'mechanical/pod-study/dimensions.json']},
      'limits':['No full component STEP model; PCB ledges locate/support but do not latch the board','No bend/strain/closure simulation','No slicing or physical fit evidence','TPU type not selected; thickness is a prototype parameter']}
    (OUT/'cad-checks.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(checks,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--wrist-mm',type=float,default=195)
    p.add_argument('--hinge-mm',type=float,default=1.0)
    args=p.parse_args()
    if not math.isfinite(args.wrist_mm) or not math.isfinite(args.hinge_mm) or not .6<=args.hinge_mm<=1.6:p.error('Finite wrist size and hinge thickness 0.6..1.6 mm required')
    build(args.wrist_mm,args.hinge_mm)
