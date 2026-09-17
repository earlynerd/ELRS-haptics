"""Create a bounded placement candidate; apply is a separate verified step."""
from pathlib import Path
import shutil,json,hashlib,math
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];HW=ROOT/'hardware';OUT=HW/'verification/main-group-refinement'
OUT.mkdir(exist_ok=True)
src=HW/'main/main.kicad_pcb'
if not (OUT/'input.kicad_pcb').exists():
 shutil.copy2(src,OUT/'input.kicad_pcb')
 (OUT/'input-sha256.txt').write_text(hashlib.sha256(src.read_bytes()).hexdigest())
for f in (HW/'main').iterdir():
 if f.suffix in ['.kicad_sch','.kicad_pro'] or f.name in ['fp-lib-table','sym-lib-table']:
  (OUT/f.name).write_text(f.read_text().replace('${KIPRJMOD}/../','${KIPRJMOD}/../../'))
shutil.copy2(HW/'main/main.kicad_pro',OUT/'input.kicad_pro')
b=p.LoadBoard(str(OUT/'input.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()}
positions={
 'R5':(39.2,58.3,90,'B'), 'R4':(40.4,58.3,90,'B'),
 'R24':(44.5,58.3,90,'B'), 'R25':(43.3,58.3,90,'B'),
 'C2':(51.2,48.9,90,'B'),
 'R42':(35.5,55.3,90,'B'), 'R43':(35.5,53.1,90,'B'),
 'R51':(35.5,73.0,90,'F'),
 'R45':(48.9,61.5,0,'F'), 'C42':(48.5,59.4,90,'F'),
 'R46':(48.6,56.3,0,'F'),
 'U14':(45.2,65.75,0,'F'), 'C41':(51.0,69.6,0,'F')}
for ref,(x,y,a,side) in positions.items():
 f=fps[ref]
 if f.GetLayer()!=(p.B_Cu if side=='B' else p.F_Cu):f.Flip(f.GetPosition(),p.FLIP_DIRECTION_LEFT_RIGHT)
 f.SetOrientationDegrees(a);f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
b.BuildConnectivity();p.SaveBoard(str(OUT/'main.kicad_pcb'),b)
shutil.copy2(HW/'main/main.kicad_pro',OUT/'main.kicad_pro')
# Candidate paths differ; active board paths will be retained at apply time.
file=OUT/'main.kicad_pcb';file.write_text(file.read_text().replace('${KIPRJMOD}/../','${KIPRJMOD}/../../'))
(OUT/'moves.json').write_text(json.dumps(positions,indent=2))
print(OUT)
