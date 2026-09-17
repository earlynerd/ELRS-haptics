"""Myo-like end flexures, with the flat-strip assembly seam inside the main pod.

Units mm. Frozen v0.8 helpers supply reference outlines and export functions.
"""
from pathlib import Path
import argparse, copy, hashlib, json, math
from build123d import (Align, Box, Circle, Compound, Edge, Face, Matrix, Pos, Rot,
                       Wire, extrude, export_step, import_step)
import build_flat_band as old

ROOT=old.ROOT
OUT=ROOT/'mechanical/myo-flat-v0.9'
WIDTHS=[24.]+[20.]*7
HEIGHTS=[64.]+[38.]*7
FLOOR=1.; DEPTH=9.5; WALL=1.2
SPLIT=7.; ROOT_Z=.6; ROOT_OVERLAP=1.0; END_MARGIN=1.0
FLEX_THICKNESS=1.2; RAIL_WIDTH=2.4; BEND_R=1.7; MAIN_LID=2.0; FLAT_GAP=6.4
box=old.box; plate=old.roundplate; cyl=old.cyl

def lid(main):
    if not main:return old.lid(20,38,False,old.anchors())
    a=old.anchors();s=plate(12,0,24,64,MAIN_LID)
    for y in [-34,34]:
        for x in [3.3,20.7]:
            s+=plate(x,y-math.copysign(.6,y),6,5.2,MAIN_LID,r=1)
            s-=cyl(x,y,-.1,1.15,MAIN_LID+.2)
    x,y=a['D1'];s-=plate(x,y,3,3,MAIN_LID+.2,-.1,r=.4)
    return s

def shell(main):
    w,h=(24,64) if main else (20,38)
    s=old.shell(w,h,main,old.anchors())
    if main:
        # Replace external ears: each main half gets its own two screws.
        s-=box(-1,-40,-.1,26,8,12)+box(-1,32,-.1,26,8,12)
        for y in [-34,34]:
            for x in [3.3,20.7]:
                s+=plate(x,y-math.copysign(.6,y),6,5.2,DEPTH,r=1)
                s-=cyl(x,y,4.5,.8,5.2)
        # Remove the 0.2 mm sliver between split and USB opening.
        s-=box(6.9,30.79,FLOOR,.31,1.3,10)
    outline,profile=old.board_profiles('main' if main else 'satellite')
    b=outline.bounding_box();y0=b.min.Y+1.2;dy=b.max.Y-b.min.Y-2.4
    s+=box(b.min.X-.4,y0,1,1.1,dy,1)+box(b.max.X-.7,y0,1,1.1,dy,1)
    board=Pos(0,0,2)*extrude(profile,amount=.8,dir=(0,0,1))
    assert (s&board).volume<1e-6
    return s,board

def split_main(main):
    left=main&box(-1,-40,-1,SPLIT+1,80,15)
    right=main&box(SPLIT,-40,-1,25-SPLIT,80,15)
    for y in [-20,20]:
        left+=box(SPLIT-.2,y-2,0,1.7,4,1)
        right-=box(SPLIT-.1,y-2.2,-.1,1.8,4.4,1.2)
    assert left.is_valid and right.is_valid
    assert len(left.solids())==len(right.solids())==1
    assert (left&right).volume<1e-6
    # Closing motion: translation of left piece towards fixed right piece.
    for dx in [-4,-2,-1,-.5,-.2,0]:
        assert ((Pos(dx,0,0)*left)&right).volume<1e-6
    return left,right

def layout(wrist):
    radius=wrist/(2*math.pi)
    spans=[2*math.atan(w/(2*radius)) for w in WIDTHS]
    a=(2*math.pi-sum(spans))/8
    assert a>0
    angles=[0.]
    for i in range(1,8):angles.append(angles[-1]+spans[i-1]/2+a+spans[i]/2)
    def point(i,x,z):
        t=-angles[i];return (x*math.cos(t)-(radius+z)*math.sin(t),x*math.sin(t)+(radius+z)*math.cos(t))
    gaps=[]
    for i in range(8):
        j=(i+1)%8;p=point(i,WIDTHS[i]/2,ROOT_Z);q=point(j,-WIDTHS[j]/2,ROOT_Z)
        gaps.append(max(FLAT_GAP,math.dist(p,q)))
    return radius,angles,gaps

def capsule(a,b,r):
    dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
    face=Pos((a[0]+b[0])/2,(a[1]+b[1])/2)*Rot(0,0,math.degrees(math.atan2(dy,dx)))*old.RectangleRounded(length+2*r,2*r,r*.999)
    return face

def flexure(edge,gap,y0,y1,wall):
    """Planar U: top rail folds towards the center, bottom rail mirrors it."""
    sign=1 if y0>0 else -1
    y0,y1=abs(y0),abs(y1)
    r=wall/2;cx=edge+gap/2;cy=min(y0,y1)-7.5
    A=(edge+1.3,y0);B=(edge+gap-1.3,y1)
    def tangent(p,left):
        dx,dy=p[0]-cx,p[1]-cy
        angle=math.atan2(dy,dx)+(1 if left else -1)*math.acos(BEND_R/math.hypot(dx,dy))
        return (cx+BEND_R*math.cos(angle),cy+BEND_R*math.sin(angle)),angle
    ta,aa=tangent(A,True);tb,ab=tangent(B,False)
    if ab<aa:ab+=2*math.pi
    def p(rad,angle):return (cx+rad*math.cos(angle),cy+rad*math.sin(angle),0)
    outer=BEND_R+r;inner=BEND_R-r;mid=(aa+ab)/2
    edges=[Edge.make_three_point_arc(p(outer,aa),p(outer,mid),p(outer,ab)),
           Edge.make_line(p(outer,ab),p(inner,ab)),
           Edge.make_three_point_arc(p(inner,ab),p(inner,mid),p(inner,aa)),
           Edge.make_line(p(inner,aa),p(outer,aa))]
    profile=Face(Wire(edges))
    for u,v in [((edge-ROOT_OVERLAP,y0),A),(A,ta),(tb,B),(B,(edge+gap+ROOT_OVERLAP,y1))]:
        profile+=capsule(u,v,r)
    f=extrude(profile,amount=FLEX_THICKNESS,dir=(0,0,1))
    if sign<0:
        from build123d import Plane
        f=f.mirror(Plane.XZ)
    assert f.is_valid and len(f.solids())==1
    length=math.dist(A,ta)+BEND_R*(ab-aa)+math.dist(tb,B)
    return f,length

def build(wrist,wall):
    for d in ['print','cad','reference-only']:(OUT/d).mkdir(parents=True,exist_ok=True)
    radius,angles,gaps=layout(wrist)
    m,mb= shell(True);sat,sb=shell(False);left,right=split_main(m)
    origins=[-SPLIT]
    for i in range(1,8):origins.append(origins[-1]+WIDTHS[i-1]+gaps[i-1])
    terminal=origins[-1]+20+gaps[7]
    rigid=[Pos(-SPLIT,0,0)*right]+[Pos(origins[i],0,0)*sat for i in range(1,8)]+[Pos(terminal,0,0)*left]
    soft=[];contacts=[];lengths=[]
    for i in range(8):
        j=(i+1)%8;edge=origins[i]+WIDTHS[i]
        for sign in [-1,1]:
            y0=sign*(HEIGHTS[i]/2-END_MARGIN);y1=sign*(HEIGHTS[j]/2-END_MARGIN)
            f,length=flexure(edge,gaps[i],y0,y1,wall)
            c=[k for k,s in enumerate(rigid) if (s&f).volume>1e-5]
            assert c==[i,i+1],(i,sign,c)
            soft.append(f);lengths.append(length)
            contacts.append({'gap':i,'end':sign,'rigid_pieces':c,'axial_roots_mm':[y0,y1]})
    # A single stiff main lid ties both shell halves together with four screws.
    ml=lid(True);sl=lid(False)
    for s in [left,right]:assert (s&(Pos(0,0,DEPTH)*ml)).volume<1e-6
    for z in [DEPTH,DEPTH+1,DEPTH+3,DEPTH+10]:
        assert ((Pos(0,0,z)*ml)&(left+right)).volume<1e-6
    ux,_=old.anchors()['J2'];probe=box(ux-4.8,30.8,2.6,9.6,8,3.9)
    assert ((left+right)&probe).volume<1e-6
    # Reference checks include the spring roots, not just the rigid shells.
    references=[]
    for i in range(8):
        b=box(5 if i==0 else 3,-10 if i==0 else -17,5.8,14,34,3.5)
        b=Pos(origins[i],0,0)*b
        for s in rigid+soft:assert (s&b).volume<1e-6
        references.append(b)
    # main battery also checked against terminal half in assembled coordinates
    assert (left&box(5,-10,5.8,14,34,3.5)).volume<1e-6
    # Continuous TPU rails follow the two pod end edges, as in the sketch.
    rail_solids=[]
    for sign in [-1,1]:
        rail=None
        for i in range(9):
            if i==0:x,w,h=0,17,64
            elif i==8:x,w,h=terminal,7,64
            else:x,w,h=origins[i],20,38
            strip=plate(x+w/2,sign*(h/2-END_MARGIN),w,RAIL_WIDTH,FLEX_THICKNESS,r=.7)
            rail=strip if rail is None else rail+strip
        for f in soft[0 if sign<0 else 1::2]:rail+=f
        assert rail.is_valid and len(rail.solids())==1
        rail_solids.append(rail)
    rb=Compound(rigid);fb=Compound(rail_solids)
    old.save_stl(rb,OUT/'print/rigid-strip.stl');old.save_stl(fb,OUT/'print/tpu-end-flexures.stl')
    old.save_stl(ml,OUT/'print/main-bridge-lid.stl');old.save_stl(sl,OUT/'print/satellite-lid.stl')
    old.package([('PET-GF15 shells',OUT/'print/rigid-strip.stl',False),('TPU end U flexures',OUT/'print/tpu-end-flexures.stl',True)],OUT/'print/myo-flat-band.3mf','Myo flat v0.9')
    # The coupon is the real joint between satellites 1 and 2.
    old.save_stl(Compound(rigid[1:3]),OUT/'print/coupon-rigid.stl')
    old.save_stl((fb&box(origins[1],-24,-.1,20+gaps[1]+20,48,2)),OUT/'print/coupon-tpu.stl')
    old.package([('Coupon shells',OUT/'print/coupon-rigid.stl',False),('Coupon U flexures',OUT/'print/coupon-tpu.stl',True)],OUT/'print/end-flexure-coupon.3mf','Myo end flexure coupon')
    old.save_stl(Compound([left,Pos(5,0,0)*right]),OUT/'print/main-seam-fit-parts.stl')
    export_step(Compound([rb,fb]),OUT/'cad/flat-strip.step')
    export_step(Compound([left,right,Pos(0,0,DEPTH)*ml]),OUT/'cad/main-seam-assembled.step')
    export_step(Compound([mb,sb]),OUT/'reference-only/board-outlines-local.step')
    for file,n in [('flat-strip.step',11),('main-seam-assembled.step',3)]:
        check=import_step(OUT/'cad'/file);assert check.is_valid and len(check.solids())==n
    report={'status':'PASS','units':'mm','revision':'0.9','wrist_reference_mm':wrist,
      'reference_radius_mm':radius,'reference_angles_rad':angles,'gaps_flat_at_root_height_mm':gaps,
      'shell_origins_mm':origins,'terminal_main_origin_mm':terminal,'main_split_x_mm':SPLIT,
      'strip_bounds_mm':[[rb.bounding_box().min.X, min(rb.bounding_box().min.Y,fb.bounding_box().min.Y),0],
                         [rb.bounding_box().max.X,max(rb.bounding_box().max.Y,fb.bounding_box().max.Y),DEPTH]],
      'pod_count':8,'rigid_shell_pieces':9,'flexure_count':16,'flexure_wall_mm':wall,'flexure_thickness_mm':FLEX_THICKNESS,'end_rail_width_mm':RAIL_WIDTH,'soft_continuous_rails':2,
      'flexure_root_height_mm':ROOT_Z,'bend_centerline_radius_mm':BEND_R,'print_plane':'Flexures and end rails in XY, all at Z=0..1.2 mm',
      'free_centerline_XY_lengths_mm':lengths,'root_contacts':contacts,
      'minimum_nominal_straight_leg_to_shell_gap_mm':1.3-wall/2,
      'reference_note':'User sketch: two planar end rails turning inward between pods. 195 mm is a fit reference; flat gap includes fold space and is not a circumference equation.',
      'cad_checks':['valid solids and expected STEP reimport counts','every spring contacts only its two intended shell pieces',
                    'battery envelopes clear shell and spring roots','bare board clearance before main split',
                    'split main closing poses -4,-2,-1,-0.5,-0.2,0 mm clear','main lid vertical insertion poses clear','USB aperture probe clear'],
      'main_lid_mm':MAIN_LID,'satellite_lid_mm':1.2,'assembly_seam':'two 1 mm floor keys; 0.2 mm clearance; four-screw common main lid',
      'source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'hardware/main/main.kicad_pcb',ROOT/'hardware/satellite/satellite.kicad_pcb',ROOT/'mechanical/pod-study/dimensions.json']},
      'limits':['Circular pose is a sizing reference only, not cylindrical anatomy','No material model, FEA, safe extension or spring rate qualification',
                'No slicing, printing or physical fit evidence','Populated board retention, wire slack and strain relief remain unresolved']}
    (OUT/'cad-checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','strip_bounds_mm','gaps_flat_at_root_height_mm','flexure_count']},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--wrist-mm',type=float,default=195);p.add_argument('--wall-mm',type=float,default=1.2)
    a=p.parse_args()
    if not math.isfinite(a.wrist_mm) or not math.isfinite(a.wall_mm) or not .8<=a.wall_mm<=1.6:p.error('Finite wrist size; flexure wall 0.8..1.6 mm required')
    build(a.wrist_mm,a.wall_mm)
