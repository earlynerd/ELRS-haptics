"""Inspectable top-side placement and critical pin-distance comparison."""
import sys,math,json,html
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/verification/main-placement-v2'
if len(sys.argv)>2:OUT=Path(sys.argv[2])
groups=json.loads((OUT/'placement.json').read_text())['groups']
colors=['#76b7f2','#d2a5f8','#bf93d4','#f8b375','#f9d771','#7cd3cb','#a6df89','#79c8a0','#acb9f4','#f3a5c9','#eb9bb8','#eac589','#bccadb','#9ed4cd','#dbb8a2']
col={r:colors[i%len(colors)] for i,g in enumerate(groups.values()) for r in g}
source=Path(sys.argv[1]) if len(sys.argv)>1 else OUT/'main.kicad_pcb'
b=p.LoadBoard(str(source));fps={f.GetReference():f for f in b.GetFootprints()}
def mm(x):return p.ToMM(x)
def xy(v):return mm(v.x),mm(v.y)
s=['<svg xmlns="http://www.w3.org/2000/svg" width="840" height="1580" viewBox="33 33 25 66"><rect x="33" y="33" width="25" height="66" fill="#111923"/>', '<style>text{font-family:Arial,sans-serif}</style>']
s.append('<path d="M35.7 40.1H55.3L56 40.8V95.3L55.3 96H35.7L35 95.3V40.8Z M41.5 58H47.5L48 58.5V72.5L47.5 73H41.5L41 72.5V58.5Z" fill="#253846" fill-rule="evenodd" stroke="#dbe9ef" stroke-width=".06"/>')
s.append('<rect x="38.7" y="34.7" width="13.6" height="5.4" fill="#8c5757" opacity=".4"/><text x="45.5" y="37.6" fill="#e9aaaa" text-anchor="middle" font-size=".75">ESP32 antenna / off-board</text>')
for ref,f in fps.items():
 x,y=xy(f.GetPosition());back=f.GetLayer()==p.B_Cu;f.BuildCourtyardCaches();bb=f.GetCourtyard(p.B_CrtYd if back else p.F_CrtYd).BBox();x0,y0,x1,y1=[mm(v) for v in [bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom()]]
 if ref=='U1':x0,y0,x1,y1=38.65,40.1,52.35,51.6
 if ref=='M1':x0,y0,x1,y1=x-1.1,y-1.5,x+1.1,y+1.5
 c=col.get(ref,'#ccc')
 dash='stroke-dasharray=".18 .12"' if back else ''
 s.append(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="{c}" fill-opacity=".09" stroke="{c}" stroke-width=".045" {dash}/>')
 for pad in f.Pads():
  px,py=xy(pad.GetPosition());w,h=xy(pad.GetSize());a=-pad.GetOrientationDegrees()
  if pad.GetAttribute()==p.PAD_ATTRIB_NPTH:
   s.append(f'<circle cx="{px}" cy="{py}" r="{w/2}" fill="#111923" stroke="#dbe9ef" stroke-width=".035"/>')
   continue
  fill='#cbad6a' if pad.GetNetname()=='GND' else '#eee0a7'
  if back:
   s.append(f'<circle cx="{px}" cy="{py}" r="{w/2}" fill="none" stroke="#d2a5f8" stroke-width=".08" stroke-dasharray=".15 .1"/>')
   continue
  s.append(f'<rect x="{px-w/2}" y="{py-h/2}" width="{w}" height="{h}" rx=".04" fill="{fill}" transform="rotate({a} {px} {py})"/>')
 # Ref centered; large IC pads leave room, tiny passive refs sit just above body.
 size=.6 if ref.startswith(('U','J','SW')) else .48
 label=ref+' (underside)' if back else ref
 s.append(f'<text x="{x}" y="{y-.15 if not back else y+1.2}" fill="{c}" text-anchor="middle" font-size="{size}" stroke="#111923" stroke-width=".09" paint-order="stroke">{label}</text>')
s.append('<text x="44.5" y="65.5" text-anchor="middle" fill="#9bb0be" font-size=".6" transform="rotate(-90 44.5 65.5)">LRA opening</text></svg>')
(OUT/'placement.svg').write_text(''.join(s),encoding='utf-8')

critical=[('U12','9','L1','1'),('U12','7','L1','2'),('U12','10','C37','1'),('U12','6','C38','1'),('U12','6','C39','1'),('U12','4','R40','2'),('U12','4','R41','1'),('U11','10','C34','1'),('U11','1','C35','1'),('U11','2','C36','1'),('U18','9','C100','1'),('U3','C2','C5','1'),('U3','C2','C7','1'),('U3','A2','C6','1'),('U1','3','C2','1')]
def point(fs,r,pin):return xy(next(d for d in fs[r].Pads() if d.GetNumber()==pin).GetPosition())
dist={f'{r}.{pin}-{z}.{pn}':round(math.dist(point(fps,r,pin),point(fps,z,pn)),3) for r,pin,z,pn in critical}
print(json.dumps(dist,indent=2));(OUT/'critical-distances.json').write_text(json.dumps(dist,indent=2)+'\n')
