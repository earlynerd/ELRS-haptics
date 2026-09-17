"""Compare retained satellite CAD against the frozen v0.10 release."""
from pathlib import Path
import json
from build123d import import_step, Compound, Box, Align, Pos

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'mechanical/myo-flat-v0.11'
data=json.loads((OUT/'cad-checks.json').read_text())
before=import_step(ROOT/'mechanical/myo-flat-v0.10/cad/flat-strip.step')
after=import_step(OUT/'cad/flat-strip.step')
def difference(a,b):return (a-b).volume+(b-a).volume
def satellite(shape,x):
    parts=[s for s in shape.solids() if abs(s.bounding_box().min.X-x)<1e-5 and abs(s.bounding_box().max.X-x-20)<1e-5]
    assert len(parts)==1
    return parts[0]
changes=[]
for i,x in enumerate(data['shell_origins_mm'][1:],1):
    v=difference(satellite(before,x),satellite(after,x));assert v<1e-5
    changes.append({'satellite':i,'symmetric_difference_mm3':v})
def rails(shape):return Compound([s for s in shape.solids() if s.bounding_box().size.X>200])
origins=data['shell_origins_mm'];length=origins[7]+20-origins[1]
region=Pos(origins[1],-24,-.1)*Box(length,48,12,align=(Align.MIN,Align.MIN,Align.MIN))
v=difference(rails(before)&region,rails(after)&region);assert v<1e-5,v
assert (ROOT/'mechanical/myo-flat-v0.10/print/satellite-lid.stl').read_bytes()==(OUT/'print/satellite-lid.stl').read_bytes()
assert max(data['free_centerline_XY_lengths_mm'])-min(data['free_centerline_XY_lengths_mm'])<1e-8
result={'passed':True,'satellite_shells':changes,'satellite_rail_region_difference_mm3':v,
        'satellite_lid_bytes_unchanged':True,'all_free_fold_lengths_equal':True}
(OUT/'revision-checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
