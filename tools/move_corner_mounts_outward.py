"""Move the shared corner mounts into the TPU contact band, preserving circuitry."""
import json
import shutil
from kicad_edit import *
from readable_schematic import props

manifest = HW / 'mounting-layout.json'
m = json.loads(manifest.read_text())
before = {'H1': [3.5, 3.5], 'H2': [16.5, 3.5], 'H3': [3.5, 42.5], 'H4': [16.5, 42.5]}
after = {'H1': [2.75, 2.75], 'H2': [17.25, 2.75], 'H3': [2.75, 43.25], 'H4': [17.25, 43.25]}
assert m['mount_centres_local_mm'] == before, 'Migration already applied or geometry changed'
backup = HW / 'backups/pre-outward-mounts-20260915'
backup.mkdir(exist_ok=False)
shutil.copy2(manifest, backup / manifest.name)
for name in ['main', 'satellite']:
    file = HW / name / (name + '.kicad_pcb')
    shutil.copy2(file, backup / file.name)
    board = load(file)
    ox, oy = m['origins_mm'][name]
    fps = {props(f)['Reference']: f for f in children(board, 'footprint')}
    for ref, (x, y) in before.items():
        at = child(fps[ref], 'at')
        assert abs(float(at[1]) - ox - x) < 1e-6 and abs(float(at[2]) - oy - y) < 1e-6
        nx, ny = after[ref]
        at[1:3] = [str(ox + nx), str(oy + ny)]
        circles = [c for c in children(board, 'gr_circle')
                   if uq(child(c, 'layer')[1]) == 'Cmts.User'
                   and abs(float(child(c, 'center')[1]) - ox - x) < 1e-6
                   and abs(float(child(c, 'center')[2]) - oy - y) < 1e-6]
        assert len(circles) == 1, (name, ref, 'relief circle')
        for key in ['center', 'end']:
            point = child(circles[0], key)
            point[1:3] = [str(float(point[1]) + nx - x), str(float(point[2]) + ny - y)]
    save(file, board)
m['mount_centres_local_mm'] = after
m['outward_mount_revision_backup'] = str(backup.relative_to(ROOT))
manifest.write_text(json.dumps(m, indent=2) + '\n')
print('Moved four mounts and matching TPU relief circles on both boards.')
