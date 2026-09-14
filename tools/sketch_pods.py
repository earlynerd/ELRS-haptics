"""Generate a dimensioned packaging study; these are not production PCB outlines."""
from pathlib import Path
import json
from html import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical' / 'pod-study'
OUT.mkdir(parents=True, exist_ok=True)
P = {
    'units': 'mm', 'revision': 'D - eight protected lid-mounted batteries',
    'regular_shell': {'circumferential': 20, 'axial': 38, 'thickness': 10.5},
    'main_shell': {'circumferential': 24, 'axial': 64, 'thickness': 10.5},
    'regular_pcb_envelope': [17, 35, 0.8],
    'main_pcb_envelope_before_antenna_relief': [21, 61, 0.8],
    'central_pcb_opening': [7, 15],
    'lra_body': [4, 12, 3.5],
    'regular_cell_envelope_excluding_lid_adhesive': [14, 34, 3.5],
    'main_cell_envelope_excluding_lid_adhesive': [14, 34, 3.5],
    'battery': {'example_model': 'YDL301230 protected', 'count': 8,
                'body_W_L_T': [12, 32, 3], 'capacity_mAh_each': 90,
                'regular_allocation_xy': [3, 2], 'main_allocation_xy': [5, 22],
                'connector': 'factory plug removed; leads soldered to pads, PCM retained'},
    'user_wrist_circumference': 195,
    'nominal_gap_flat_length_estimate': 3.875,
    'radial_stack': {'inner_wall': [0, 1], 'adhesive': [1, 1.5],
                     'lra': [1.5, 5], 'pcb': [2, 2.8],
                     'component_height_ceiling': 4.8,
                     'foam_allowance': [5, 5.35],
                     'cell_envelope': [5.8, 9.3], 'lid_adhesive': [9.3, 9.5],
                     'outer_cover': [9.5, 10.5]},
    'limits': ['14 x 34 x 3.5 allocation around the 12 x 32 x 3 body; final lead bends, tolerances and expansion need sample fit.',
               'Main cell allocation starts 22 mm from antenna end; RF performance is not validated.', 'Routing, RF, curvature, clips and link strain are not validated.',
               'Shell widths and circumference sum are a flat length estimate, not a curved wrist fit.']
}
(OUT / 'dimensions.json').write_text(json.dumps(P, indent=2) + '\n', encoding='utf-8')
items=[]
def add(s): items.append(s)
def text(x,y,s,size=16,color='#243545',anchor='start',weight='normal'):
    add(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{escape(s)}</text>')
def rect(x,y,w,h,fill,stroke='#52677a',r=0,dash=''):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.5" stroke-dasharray="{dash}"/>')
def line(x1,y1,x2,y2,color='#52677a',dash=''):
    add(f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{color}" stroke-width="1.3" stroke-dasharray="{dash}"/>')
def dimh(x1,x2,y,label):
    line(x1,y,x2,y); line(x1,y-5,x1,y+5); line(x2,y-5,x2,y+5)
    text((x1+x2)/2,y-9,label,15,anchor='middle')
def dimv(x,y1,y2,label):
    line(x,y1,x,y2);line(x-5,y1,x+5,y1);line(x-5,y2,x+5,y2)
    add(f'<text transform="translate({x-10},{(y1+y2)/2}) rotate(-90)" text-anchor="middle" font-size="15" fill="#243545">{escape(label)}</text>')
add('<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="1120" viewBox="0 0 1280 1120" role="img" aria-label="Provisional haptic bracelet pod plans and thickness section, all dimensions in millimetres">')
add('<rect width="1280" height="1120" fill="#fcfcf9"/><g font-family="Arial, sans-serif">')
text(45,43,'HAPTIC BRACELET / POD PACKAGING STUDY D',25,weight='bold')
text(45,72,'All dimensions in mm. Flat datum study; wrist curvature, clips and routing remain open.',16)
text(110,100,'REGULAR POD',19,weight='bold')
text(475,92,'ESP32 / USB POD',19,weight='bold')
S=7
def pod(x,y,w,h,main=False):
    rect(x,y,w*S,h*S,'#e9edf0',r=3*S)
    rect(x+1.5*S,y+1.5*S,(w-3)*S,(h-3)*S,'#d9ede4','#368165',r=1*S)
    # An indicative edge relief under the antenna; final geometry follows the module land pattern.
    if main:
        rect(x+4.6*S,y+0.7*S,14.8*S,6*S,'#fcfcf9','#a98535',dash='4 3')
        rect(x+5.4*S,y+1.2*S,13.2*S,16.6*S,'#dfe7f7','#5b739d',r=2)
        rect(x+5.4*S,y+1.2*S,13.2*S,5.4*S,'#f9e7af','#a98535')
        text(x+w*S/2,y+4.8*S,'ANT',13,anchor='middle')
        text(x+w*S/2,y+11*S,'C6 MINI-1',13,anchor='middle')
        text(x+w*S/2,y+14*S,'13.2 × 16.6',12,anchor='middle')
    cy=y+h*S/2
    rect(x+(w-7)/2*S,cy-7.5*S,7*S,15*S,'#fcfcf9','#52677a',r=1*S)
    rect(x+(w-5.4)/2*S,cy-6.7*S,5.4*S,13.4*S,'#cbd2d8','#52677a',r=3)
    rect(x+(w-4)/2*S,cy-6*S,4*S,12*S,'#efb78b','#b6662f',r=2)
    add(f'<text transform="translate({x+w*S/2+4},{cy}) rotate(-90)" font-size="13" text-anchor="middle" fill="#613511">LRA 4 × 12</text>')
    # Flex exits laterally; contour is symbolic, not a verified bend design.
    rect(x+(w/2+2)*S,cy-2.7*S,4.4*S,5.4*S,'#f6dfa4','#a98535')
    for off in [-0.9,0.9]:
        rect(x+(w/2+5.2)*S,cy+(off-0.5)*S,1.2*S,1*S,'#e3a652','#946325')
    for side in [-1,1]:
        xx=x-2*S if side==-1 else x+w*S
        for off in [-9,6]:
            rect(xx,cy+off*S,2*S,3*S,'#d6cfee','#83769d',r=2)
    if not main:
        text(x+w*S/2,y+5.5*S,'driver / passives',12,anchor='middle')
        rect(x+6.2*S,y+29*S,7.6*S,7.2*S,'#dfe7f7','#5b739d',r=2)
        text(x+w*S/2,y+33.3*S,'MCU',12,anchor='middle')
    else:
        text(x+w*S/2,y+45*S,'MCU / driver',13,anchor='middle')
        text(x+w*S/2,y+48*S,'power / USB circuitry',12,anchor='middle')
        rect(x+(w-9)/2*S,y+(h-7)*S,9*S,7*S,'#d3d8dc','#52677a',r=3)
        text(x+w*S/2,y+(h-2.3)*S,'USB-C',12,anchor='middle')
        rect(x+(w-1.6)*S,y+(h-10)*S,1.6*S,4*S,'#d6cfee','#83769d',r=2)
        line(x+w*S,y+(h-8)*S,x+w*S+28,y+(h-8)*S)
        text(x+w*S+32,y+(h-8)*S+5,'SW3',13)
        add(f'<circle cx="{x+21*S}" cy="{y+(h-4.5)*S}" r="7" fill="#b9d8ef" stroke="#52677a"/>')
        text(x+21*S,y+(h-1)*S,'RGB',11,anchor='middle')
    # Dashed lid overlays: outer allocation, then actual protected battery body.
    bx,by=(5,22) if main else (3,2)
    rect(x+bx*S,y+by*S,14*S,34*S,'none','#a98535',dash='6 4')
    rect(x+(bx+1)*S,y+(by+1)*S,12*S,32*S,'none','#ba7c14',dash='2 3')
    dimh(x,x+w*S,y-(5 if main else 17),f'{w} around wrist')
    dimv(x-24,y,y+h*S,f'{h} along arm')
    line(x-45,cy,x+w*S+30,cy,'#9babb5','5 5')
    return cy
pod(125,216,20,38)
pod(495,125,24,64,True)
text(90,505,'PCB envelope: 17 × 35 × 0.8',15)
text(90,530,'Dashed: battery on lid above PCB',14)
text(460,596,'PCB: 21 × 61 × 0.8; RF relief pending',14)
text(760,160,'COMMON HAPTIC CORE',18,weight='bold')
for i,t in enumerate(['7 × 15 PCB opening, rounded corners',
                       '5.4 × 13.4 proposed plastic mounting seat',
                       '4 × 12 × 3.5 actuator, axis toward skin',
                       'Flex contacts beside the opening',
                       'Link anchors centered on the haptic core']):text(760,193+26*i,t,15)
text(760,352,'PACKAGING ALLOCATIONS',18,weight='bold')
for i,t in enumerate(['One protected 90 mAh cell in EVERY pod',
                       'Battery body: 12 × 32 × 3.0; PCM retained',
                       'Allocation: 14 × 34 × 3.5 + 0.2 adhesive',
                       'Main cell starts 22 mm from antenna end',
                       'USB block: 9 × 7 placeholder, part not chosen',
                       'Main antenna: no battery or metal cover above']):text(760,385+26*i,t,15)
line(45,605,1235,605,'#cad2d8')
text(45,644,'REGULAR POD / SECTION THROUGH ACTUATOR',20,weight='bold')
text(45,671,'Cell bonded to the inner lid surface; open clearance below, with no shelf or separate compartment.',16)
# Section: around-wrist dimension horizontal; skin datum at z=0.
sx,sy,k=135,930,15
def section(x,z,w,h,fill,stroke='#52677a'):
    rect(sx+x*k,sy-(z+h)*k,w*k,h*k,fill,stroke)
section(0,0,20,1,'#cbd2d8')
section(0,1,1,8.5,'#cbd2d8');section(19,1,1,8.5,'#cbd2d8')
section(0,9.5,20,1,'#cbd2d8')
section(7.3,1,5.4,.5,'#f6dfa4')
section(8,1.5,4,3.5,'#efb78b','#b6662f')
section(8,5,4,.35,'#d6cfee','#83769d')
section(1.5,2,5,.8,'#9bcbb8','#368165');section(13.5,2,5,.8,'#9bcbb8','#368165')
section(2,2.8,3.6,2,'#dfe7f7','#5b739d')
section(14.2,2.8,3.6,2,'#dfe7f7','#5b739d')
section(3,9.3,14,.2,'#d6cfee','#83769d')
section(3,5.8,14,3.5,'#f5e9c5','#a98535')
text(sx+10*k,sy-7.15*k,'CELL ENVELOPE',15,anchor='middle')
dimv(sx-25,sy-10.5*k,sy,'10.5 overall')
dimh(sx,sx+20*k,sy+31,'20 overall')
text(sx+10*k,sy+58,'SKIN / inner wall datum',15,anchor='middle')
labels=[(10,'1.0 lid; 0.2 adhesive allowance on its inner face'),(7.3,'3.5 allocation for 3.0 protected battery body'),
        (5.575,'0.45 gap above 0.35 LRA foam allowance; no shelf'),
        (3.6,'3.5 LRA on 0.5 supplied adhesive'),
        (2.4,'0.8 PCB; component tops limited to z = 4.8'),
        (.5,'1.0 inner wall; curvature not included in stack')]
for z,t in labels:
    yy=sy-z*k
    line(sx+20*k+8,yy,510,yy)
    text(525,yy+5,t,16)
text(45,1050,'195 mm WRIST: 164 mm rigid width + 31 mm across seven wired links and one purely mechanical clasp.',16)
text(45,1077,'Six wires per link; no wires across clasp. Equal-gap estimate: 3.875 mm. Curvature and clasp geometry remain open.',15)
add('</g></svg>')
(OUT / 'pod-dimensions.svg').write_text('\n'.join(items), encoding='utf-8')
print(f'Wrote {OUT / "pod-dimensions.svg"}')
