"""Myo-like end flexures, with the flat-strip assembly seam inside the main pod.

Units mm. Frozen v0.8 helpers supply reference outlines and export functions.
"""
from pathlib import Path
import argparse, copy, hashlib, json, math
from build123d import (Align, Box, Circle, Compound, Edge, Face, Matrix, Pos, Rot,
                       Wire, extrude, export_step, import_step)
import build_flat_band as old

ROOT=old.ROOT
OUT=ROOT/'mechanical/myo-flat-v0.11'
WIDTHS=[24.]+[20.]*7
HEIGHTS=[72.]+[46.]*7
FLOOR=1.; DEPTH=9.5; WALL=1.2
ROOT_Z=.6; ROOT_OVERLAP=1.0; END_MARGIN=1.0
FLEX_THICKNESS=DEPTH; RAIL_WIDTH=2.4; BEND_R=1.7; MAIN_LID=2.0; SAT_LID=1.6; FLAT_GAP=6.4
WALL_HANDOFF_X=18.0
MAIN_SEAM=0.0
UPPER_HEIGHT=DEPTH+MAIN_LID
box=old.box; plate=old.roundplate; cyl=old.cyl

def screw_positions(main):
    return [(x,y) for y in [-32.8,32.8] for x in [3.3,20.7]] if main else [(10,-19.5),(10,19.5)]

def lid(main):
    from build123d import Cone
    w,h,t=(24,72,MAIN_LID) if main else (20,46,SAT_LID)
    s=plate(w/2,0,w,h,t,r=2.5)
    for x,y in screw_positions(main):
        s-=cyl(x,y,-.1,1.15,t+.2)
        s-=Pos(x,y,t-.9)*Cone(1.15,2.05,.9,align=(Align.CENTER,Align.CENTER,Align.MIN))
    if main:
        x,y=old.anchors()['D1'];s-=plate(x,y,3,3,t+.2,-.1,r=.4)
    return s

def shell(main):
    w,h,old_h=(24,72,64) if main else (20,46,38)
    s=plate(w/2,0,w,h,DEPTH,r=2.5)
    # The original electronics cavity stays unchanged. Rounded full-width
    # shoulders occupy the old screw-ear envelope and contain the fasteners.
    s-=plate(w/2,0,w-2*WALL,old_h-2*WALL,DEPTH+1,FLOOR,r=.3)
    for x in [-.1,w-WALL-.1]:s-=box(x,-7,3.3,WALL+.2,14,DEPTH)
    if main:
        a=old.anchors();ux,_=a['J2']
        s-=box(ux-4.8,30.79,2.6,9.6,5.5,DEPTH)
        bx,by=a['SW3'];sx=-.1 if bx<w/2 else w-WALL-.1
        s-=box(sx,by-1.8,2.8,WALL+.2,3.6,DEPTH)
        rx,ry=a['J3'];s-=plate(rx,ry,6.4,3.2,FLOOR+.2,-.1,r=.5)
    for x,y in screw_positions(main):s-=cyl(x,y,4.5,.8,5.2)
    outline,profile=old.board_profiles('main' if main else 'satellite')
    b=outline.bounding_box();y0=b.min.Y+1.2;dy=b.max.Y-b.min.Y-2.4
    s+=box(b.min.X-.4,y0,1,1.1,dy,1)+box(b.max.X-.7,y0,1,1.1,dy,1)
    board=Pos(0,0,2)*extrude(profile,amount=.8,dir=(0,0,1))
    assert (s&board).volume<1e-6
    return s,board

def main_rail(sign, side, wall):
    """Full-height end rail continuing down the outside wall to satellite Y."""
    strip=plate(12,sign*35.4,24,1.2,DEPTH,r=.4)
    if side=='right':
        strip &= box(WALL_HANDOFF_X,-40,-.1,24-WALL_HANDOFF_X,80,12)
        x=24.
    else:
        strip &= box(0,-40,-.1,WALL_HANDOFF_X,80,12)
        x=0.
    # Rounded side run is bonded to the main wall; only the U below Y=22 is free.
    path=capsule((x,sign*22),(x,sign*33.5),wall/2)
    path+=capsule((x,sign*33.5),(x+(-.5 if side=='right' else .5),sign*35.4),wall/2)
    strip+=extrude(path,amount=DEPTH,dir=(0,0,1))
    if sign>0:
        ux,_=old.anchors()['J2'];strip-=box(ux-4.8,30.8,2.6,9.6,8,DEPTH)
    return strip


def main_halves(wall):
    """Subtract cavity, access and mating cuts from one rectangular envelope."""
    from build123d import Cone
    outer=plate(12,0,24,72,UPPER_HEIGHT,r=2.5)
    outline,profile=old.board_profiles('main');b=outline.bounding_box()
    board=Pos(0,0,2)*extrude(profile,amount=.8,dir=(0,0,1))
    # Two-depth cavity leaves PCB bearing ledges in the original solid.
    cavity=plate(12,0,21.6,61.6,DEPTH-2,2,r=.3)
    x0=b.min.X+.7;x1=b.max.X-.7
    cavity+=box(x0,-30.8,FLOOR,x1-x0,61.6,1.01)
    closed=outer-cavity
    for x in [-.1,22.7]:closed-=box(x,-7,3.3,1.4,14,4.7)
    a=old.anchors();ux,_=a['J2'];bx,by=a['SW3'];rx,ry=a['J3'];lx,ly=a['D1']
    closed-=box(ux-4.8,30.79,2.6,9.6,5.5,5.4)
    closed-=box(-.1,by-1.8,2.8,1.4,3.6,3.2)
    closed-=plate(rx,ry,6.4,3.2,FLOOR+.2,-.1,r=.5)
    closed-=plate(lx,ly,3,3,MAIN_LID+.2,DEPTH-.1,r=.4)
    # Lower ownership: entire floor, right wall, and continuous internal end bars.
    mask=box(-1,-40,-.1,26,80,FLOOR+.1)
    mask+=box(WALL_HANDOFF_X,-40,FLOOR,25-WALL_HANDOFF_X,80,DEPTH-FLOOR)
    for y in [-34.8,30.8]:mask+=box(1.4,y,FLOOR,WALL_HANDOFF_X-1.4,4.0,6.5)
    lower=closed&mask
    upper=closed-lower
    # Clearance around end-bar seats; bars are integrated into the floor/wall.
    for y in [-35.0,30.6]:upper-=box(1.2,y,FLOOR,WALL_HANDOFF_X-1.2+.2,4.4,6.7)
    # Upper TPU is a full-height inlay; reserve its pocket in the mating floor.
    for sign in [-1,1]:lower-=main_rail(sign,'left',wall)
    for x,y in screw_positions(True):
        seat=7.5 if x<WALL_HANDOFF_X else DEPTH
        lower-=cyl(x,y,2.5,.8,seat-2.5+.1)
        upper-=cyl(x,y,seat-.1,1.15,UPPER_HEIGHT-seat+.2)
        upper-=Pos(x,y,UPPER_HEIGHT-.9)*Cone(1.15,2.05,.9,align=(Align.CENTER,Align.CENTER,Align.MIN))
    assert lower.is_valid and upper.is_valid
    assert len(lower.solids())==len(upper.solids())==1
    assert ((lower+upper)-outer).volume<1e-6
    assert ((lower+upper)&board).volume<1e-6
    for dz in [0,.2,.5,1,2,5,10]:assert ((Pos(0,0,dz)*upper)&lower).volume<1e-6
    return lower,upper,board


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
    sat,sb=shell(False);lower,upper,mb=main_halves(wall)
    origins=[0.]
    for i in range(1,8):origins.append(origins[-1]+WIDTHS[i-1]+gaps[i-1])
    terminal=origins[-1]+20+gaps[7]
    rigid=[lower]+[Pos(origins[i],0,0)*sat for i in range(1,8)]+[Pos(terminal,0,0)*upper]
    # All free ribbons and wall-handoff joints share one full-height extrusion.
    part_heights=[DEPTH]*9
    soft=[];contacts=[];lengths=[]
    for i in range(8):
        j=(i+1)%8;edge=origins[i]+WIDTHS[i]
        for sign in [-1,1]:
            y0=y1=sign*(HEIGHTS[1]/2-END_MARGIN)
            f,length=flexure(edge,gaps[i],y0,y1,wall)
            c=[k for k,part in enumerate(rigid) if (part&f).volume>1e-5]
            assert c==[i,i+1],(i,sign,c)
            soft.append(f);lengths.append(length)
            contacts.append({'gap':i,'end':sign,'rigid_pieces':c,'axial_roots_mm':[y0,y1],
                             'root_ribbon_heights_mm':[part_heights[i],part_heights[i+1]]})
    # Model references remain in their original assembled electronics datums.
    main_closed=lower+Pos(0,0,MAIN_SEAM)*upper
    battery_main=box(5,-10,5.8,14,34,3.5)
    assert (main_closed&mb).volume<1e-6
    assert (main_closed&battery_main).volume<1e-6
    ux,_=old.anchors()['J2'];probe=box(ux-4.8,30.8,2.6,9.6,8,3.9)
    assert (main_closed&probe).volume<1e-6
    rail_solids=[]
    for sign in [-1,1]:
        rail=None
        for i in range(9):
            x=origins[i] if i<8 else terminal
            w=24 if i in [0,8] else 20;h=72 if i in [0,8] else 46
            if i==0:strip=main_rail(sign,'right',wall)
            elif i==8:strip=Pos(terminal,0,0)*main_rail(sign,'left',wall)
            else:strip=plate(x+w/2,sign*(h/2-1.2),w,RAIL_WIDTH,DEPTH,r=.7)
            rail=strip if rail is None else rail+strip
        for f in soft[0 if sign<0 else 1::2]:rail+=f
        if sign>0:
            rail-=box(ux-4.8,30.8,2.6,9.6,8,DEPTH)
            rail-=box(terminal+ux-4.8,30.8,2.6,9.6,8,DEPTH)
        assert rail.is_valid and len(rail.solids())==1
        rail_solids.append(rail)
    rb=Compound(rigid);fb=Compound(rail_solids)
    for i in range(1,8):
        board=Pos(origins[i],0,0)*sb
        battery=box(origins[i]+3,-17,5.8,14,34,3.5)
        cover=Pos(origins[i],0,DEPTH)*lid(False)
        for ref in [board,battery,cover]:assert (fb&ref).volume<1e-6
        assert (rigid[i]&battery).volume<1e-6
    # Isolate main end rails and check them in the closed main-pod coordinates.
    lower_soft=main_rail(-1,'right',wall)+main_rail(1,'right',wall)
    upper_soft=main_rail(-1,'left',wall)+main_rail(1,'left',wall)
    main_soft=lower_soft+upper_soft
    for dz in [0,.2,.5,1,2,5,10]:
        assert ((lower+lower_soft)&(Pos(0,0,dz)*(upper+upper_soft))).volume<1e-6
    # Full contact along the straight supported runs, above the shared floor.
    support_contacts=[]
    for side,body in [('right',lower),('left',upper)]:
        for sign in [-1,1]:
            x=23.5 if side=='right' else .1
            y=22 if sign>0 else -33.4
            gauge=box(x,y,1.1,.4,11.4,8.3)
            bonded=(body&main_rail(sign,side,wall))&gauge
            assert abs(bonded.volume-gauge.volume)<1e-6
            support_contacts.append({'side':side,'end':sign,'verified_straight_span_mm':11.4})
    # Verify both butt joints have the entire 9.5 mm ribbon height on both sides.
    for sign in [-1,1]:
        gauge=box(WALL_HANDOFF_X-.01,sign*35.4-.59,0,.02,1.18,DEPTH)
        assert abs((main_soft&gauge).volume-gauge.volume)<1e-6
    for ref in [mb,battery_main,probe]:assert (main_soft&ref).volume<1e-6
    assert abs(fb.bounding_box().min.Z)<1e-6 and abs(fb.bounding_box().max.Z-DEPTH)<1e-6
    old.save_stl(rb,OUT/'print/rigid-strip.stl');old.save_stl(fb,OUT/'print/tpu-end-flexures.stl')
    old.save_stl(rb-fb,OUT/'reference-only/render-rigid.stl')
    old.save_stl(Compound(rigid[1:3])-fb,OUT/'reference-only/render-coupon-rigid.stl')
    old.save_stl(lid(False),OUT/'print/satellite-lid.stl')
    old.package([('PET-GF15 shells and main cover',OUT/'print/rigid-strip.stl',False),
                 ('TPU ribbon flexures',OUT/'print/tpu-end-flexures.stl',True)],
                OUT/'print/myo-flat-band.3mf','Myo clamshell band v0.11')
    coupon_region=box(origins[1],-24,-.1,20+gaps[1]+20,48,DEPTH+.2)
    old.save_stl(Compound(rigid[1:3]),OUT/'print/coupon-rigid.stl')
    old.save_stl(fb&coupon_region,OUT/'print/coupon-tpu.stl')
    old.package([('Coupon shells',OUT/'print/coupon-rigid.stl',False),('Coupon ribbons',OUT/'print/coupon-tpu.stl',True)],
                OUT/'print/end-flexure-coupon.3mf','Full-height ribbon coupon')
    old.save_stl(Compound([lower,Pos(29,0,0)*upper]),OUT/'print/main-clamshell-fit-parts.stl')
    old.save_stl(lower,OUT/'reference-only/main-lower.stl')
    old.save_stl(upper,OUT/'reference-only/main-upper-print-pose.stl')
    old.save_stl(lower-main_soft,OUT/'reference-only/render-main-lower.stl')
    old.save_stl(upper-main_soft,OUT/'reference-only/render-main-upper.stl')
    old.save_stl(lower_soft,OUT/'reference-only/main-lower-tpu.stl')
    old.save_stl(upper_soft,OUT/'reference-only/main-upper-tpu.stl')
    starter_region=box(-1,-40,-.1,origins[1]+21,80,12)
    old.save_stl(Compound(rigid[:2]),OUT/'print/main-transition-rigid.stl')
    old.save_stl(fb&starter_region,OUT/'print/main-transition-tpu.stl')
    old.save_stl(Compound(rigid[:2])-fb,OUT/'reference-only/render-main-transition.stl')
    old.package([('Main base and satellite',OUT/'print/main-transition-rigid.stl',False),
                 ('Supported main ribbons',OUT/'print/main-transition-tpu.stl',True)],
                OUT/'print/main-transition-coupon.3mf','Main supported-ribbon coupon')
    # Trial the terminal ribbon and clamshell with the lower fit part.
    old.save_stl(Compound(rigid[7:9]),OUT/'print/closure-coupon-rigid.stl')
    old.save_stl(fb&box(origins[7],-40,-.1,20+gaps[7]+24,80,12),OUT/'print/closure-coupon-tpu.stl')
    old.package([('Terminal satellite and main cover',OUT/'print/closure-coupon-rigid.stl',False),
                 ('Terminal constant-height ribbons',OUT/'print/closure-coupon-tpu.stl',True)],
                OUT/'print/closure-transition-coupon.3mf','Clamshell closure transition coupon')
    export_step(Compound([rb,fb]),OUT/'cad/flat-strip.step')
    export_step(Compound([lower,Pos(0,0,MAIN_SEAM)*upper]),OUT/'cad/main-clamshell-assembled.step')
    export_step(Compound([mb,sb]),OUT/'reference-only/board-outlines-local.step')
    for file,n in [('flat-strip.step',11),('main-clamshell-assembled.step',2)]:
        check=import_step(OUT/'cad'/file);assert check.is_valid and len(check.solids())==n
    report={'status':'PASS','units':'mm','revision':'0.11','wrist_reference_mm':wrist,
      'reference_radius_mm':radius,'reference_angles_rad':angles,'gaps_flat_at_root_height_mm':gaps,
      'shell_origins_mm':origins,'terminal_main_origin_mm':terminal,'main_assembly_z_offset_mm':0,'main_wall_handoff_x_mm':WALL_HANDOFF_X,
      'main_base_wall_height_mm':DEPTH,'main_cover_wall_height_mm':DEPTH-FLOOR,'main_cover_height_with_outer_face_mm':UPPER_HEIGHT-FLOOR,
      'main_assembled_height_mm':DEPTH+MAIN_LID,'part_print_heights_mm':[DEPTH]*8+[UPPER_HEIGHT],
      'ribbon_root_heights_mm':part_heights,
      'strip_bounds_mm':[[0,-36,0],[terminal+24,36,DEPTH+MAIN_LID]],
      'pod_count':8,'rigid_shell_pieces':9,'flexure_count':16,'flexure_wall_mm':wall,'flexure_height_mm':FLEX_THICKNESS,
      'end_rail_width_mm':RAIL_WIDTH,'soft_continuous_rails':2,'rail_center_inside_shell_end_mm':1.2,
      'bend_centerline_radius_mm':BEND_R,'print_plane':'Free TPU ribbons and both closure joints Z=0..9.5 mm; no taper or assembly offset',
      'usb_local_relief':'The embedded positive-end rail has a local USB aperture; both ribbon butt joints lie outside that relief',
      'free_centerline_XY_lengths_mm':lengths,'root_contacts':contacts,'main_supported_runs':support_contacts,
      'main_free_fold_matches_satellites':max(lengths)-min(lengths)<1e-8,
      'minimum_end_bar_pilot_web_mm':1.2,'main_end_rail_width_mm':1.2,
      'minimum_nominal_straight_leg_to_shell_gap_mm':1.3-wall/2,
      'fasteners':{'main':'4 x M2 x 8 mm countersunk; left 4 mm / right 6 mm engagement; 1 mm bottom clearance',
                   'satellites':'14 x M2 x 5 mm countersunk; 3.4 mm engagement',
                   'modeled_head':'90 degree, 4.1 mm seat diameter; verify actual screws'},
      'main_outer_face_mm':MAIN_LID,'satellite_lid_mm':SAT_LID,
      'print_support':'Local support beneath terminal roof and wall feet (Z=1); TPU starts on bed; no assembly flip or final Z offset',
      'assembly_seam':'Subtractive rectangular clamshell with continuous end bars, 0.2 mm internal seat clearance and four recessed screws',
      'cad_checks':['valid solids and expected STEP reimport counts','16 intended two-neighbor ribbon contacts',
                    'closed main body and TPU clear board, battery and USB aperture','satellite TPU clear boards, cells and lids',
                    'full-height gauge across both ribbon butt joints','four main wall-bond contact gauges',
                    'clamshell insertion including attached TPU at 0,0.2,0.5,1,2,5,10 mm',
                    'main cover insertion sampled at 0,0.2,0.5,1,2,5,10 mm clearance'],
      'source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'hardware/main/main.kicad_pcb',ROOT/'hardware/satellite/satellite.kicad_pcb',ROOT/'mechanical/pod-study/dimensions.json']},
      'limits':['No FEA, safe extension or spring-rate qualification','Ribbon butt ends meet at vertical wall handoff; physical closure and load transfer need trial',
                'User supplied a v0.10 slicer view; v0.11 has not been sliced or printed','Populated-board retention and harness strain relief remain unresolved']}
    (OUT/'cad-checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','strip_bounds_mm','main_assembly_z_offset_mm','main_wall_handoff_x_mm','flexure_height_mm']},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--wrist-mm',type=float,default=195);p.add_argument('--wall-mm',type=float,default=1.2)
    a=p.parse_args()
    if not math.isfinite(a.wrist_mm) or not math.isfinite(a.wall_mm) or not .8<=a.wall_mm<=1.6:p.error('Finite wrist size; ribbon wall 0.8..1.6 mm required')
    build(a.wrist_mm,a.wall_mm)
