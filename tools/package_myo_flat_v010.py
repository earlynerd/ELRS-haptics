"""Check and package the v0.10 prototype without changing earlier releases."""
from pathlib import Path
import hashlib, json, re, zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/myo-flat-v0.10'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

cad=json.loads((OUT/'cad-checks.json').read_text())
mesh=json.loads((OUT/'mesh-checks.json').read_text())
assert cad['status']=='PASS' and mesh['passed']
expected={'rigid-strip.stl':9,'tpu-end-flexures.stl':2,'satellite-lid.stl':1,
          'coupon-rigid.stl':2,'coupon-tpu.stl':2,'main-clamshell-fit-parts.stl':2,
          'closure-coupon-rigid.stl':2,'closure-coupon-tpu.stl':2}
for part in mesh['parts']:
    path=OUT/'print'/Path(part['path']).name
    assert digest(path)==part['sha256']
    assert part['vertex_connected_components']==expected[path.name]
assert len(mesh['parts'])==len(expected)
for name,sha in cad['source_hashes'].items():assert digest(ROOT/name)==sha

previous=ROOT/'mechanical/haptic-myo-flat-v0.9.zip'
old_hash=digest(previous)
with zipfile.ZipFile(previous) as z:
    assert z.testzip() is None
    preserved=[]
    for name in z.namelist():
        if name.endswith('/'):continue
        assert (ROOT/name).read_bytes()==z.read(name),f'Previous input changed: {name}'
        preserved.append(name)

ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
packages=[]
for path in sorted((OUT/'print').glob('*.3mf')):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        model=ET.fromstring(z.read('3D/3dmodel.model'))
    assert model.attrib['unit']=='millimeter'
    assert len(model.findall('.//m:basematerials/m:base',ns))==2
    assert len(model.findall('.//m:components/m:component',ns))==2
    assert len(model.findall('.//m:build/m:item',ns))==1
    packages.append(path.name)

for target in re.findall(r'\]\(([^)]+)\)',(OUT/'README.md').read_text(encoding='utf-8')):
    assert (OUT/target).exists(),target
report={'passed':True,'expected_mesh_components':expected,'three_mf_packages':packages,
        'source_inputs_unchanged':True,'previous_release_files_checked':len(preserved),
        'previous_zip_sha256':old_hash,'cad_generator_sha256':digest(ROOT/'tools/build_myo_flat_v010.py'),
        'limits':'CAD, mesh and archive checks only. No slicing or physical qualification.'}
(OUT/'delivery-checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')

files=sorted(p for p in OUT.rglob('*') if p.is_file())
files += [ROOT/'tools'/name for name in ['build_myo_flat_v010.py','render_myo_flat_v010.py',
          'build_flat_band.py','build_myo_band.py','kicad_edit.py']]
files += [ROOT/name for name in cad['source_hashes']]
target=ROOT/'mechanical/haptic-myo-flat-v0.10.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
    for path in files:z.write(path,path.relative_to(ROOT).as_posix())
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None and len(z.namelist())==len(files)
    for path in files:assert z.read(path.relative_to(ROOT).as_posix())==path.read_bytes()
assert digest(previous)==old_hash
print(json.dumps({'passed':True,'archive':str(target),'files':len(files),
                  'bytes':target.stat().st_size,'previous_files_preserved':len(preserved)},indent=2))
