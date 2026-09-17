"""Local ESP placement revision; preserve all other component locations."""
import json,math,shutil
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/verification/main-recovery-pads'
shutil.copy2(ROOT/'hardware/main/main.kicad_pro',OUT/'input.kicad_pro')
b=p.LoadBoard(str(OUT/'input.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()}
positions={
 'C3':(36.3,42.5,90), 'C1':(38,47.8,270),'R3':(36.2,46.7,0),
 'R1':(42,52.8,90),'R2':(43.15,52.8,90),
 'R24':(44.3,52.8,90),'R25':(45.7,52.8,90),
 'R4':(48.7,52.8,90),'R5':(50,52.8,90),
 'R42':(53.6,49.7,0),'R43':(53.2,47.8,90),
 'D1':(38.3,55.2,0),'R47':(37.3,52.7,270),'R49':(38.65,52.7,270),'R51':(40.3,55,180)}
before={r:[p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y),f.GetOrientationDegrees()] for r,f in fps.items()}
for ref,(x,y,a) in positions.items():
 f=fps[ref];f.SetOrientationDegrees(a);f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
b.BuildConnectivity();p.SaveBoard(str(OUT/'main.kicad_pcb'),b)
manifest=json.loads((ROOT/'hardware/main/placement-reference.json').read_text())
manifest['source']=str(OUT/'input.kicad_pcb');manifest['recovery_pads']=True
manifest['placements']={r:[p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y),f.GetOrientationDegrees()] for r,f in fps.items()}
manifest['layers']={r:b.GetLayerName(f.GetLayer()) for r,f in fps.items()}
manifest['groups']['reset']=['C1','R3'];manifest['groups']['boot']=['R5'];manifest['groups']['recovery']=['J3']
manifest['grid_mm']=None;manifest['method']='Manual local placement by pin geometry; native DRC validates clearances'
(OUT/'placement.json').write_text(json.dumps(manifest,indent=2)+'\n')
def point(r,pin):
 d=next(d for d in fps[r].Pads() if d.GetNumber()==pin);return(p.ToMM(d.GetPosition().x),p.ToMM(d.GetPosition().y))
pairs=[('U1','3','C2','1'),('U1','8','C1','1'),('U1','15','R1','2'),('U1','16','R2','2'),('U1','17','R24','2'),('U1','18','R25','2'),('U1','22','R4','2'),('U1','23','R5','2'),('U1','25','R42','1')]
distances={f'{r}.{n}-{s}.{m}':round(math.dist(point(r,n),point(s,m)),3) for r,n,s,m in pairs}
(OUT/'esp-distances.json').write_text(json.dumps(distances,indent=2)+'\n')
print('Moved only',sorted(positions));print(json.dumps(distances,indent=2))
