"""Register the mounting libraries and refill copper after the mechanical edit."""
import sys
from kicad_edit import *
import pcbnew as p

name=sys.argv[1]
for table,lib,kind,uri in [
 ('fp-lib-table','MountingHole','KiCad','${KICAD10_FOOTPRINT_DIR}/MountingHole.pretty'),
 ('sym-lib-table','Mechanical','KiCad','${KICAD10_SYMBOL_DIR}/Mechanical.kicad_sym')]:
 file=HW/name/table; a=load(file)
 if not any(uq(child(x,'name')[1])==lib for x in children(a,'lib')):
  a.append(parse(f'(lib (name "{lib}") (type "{kind}") (uri "{uri}") (options "") (descr ""))'))
  save(file,a)
file=HW/name/(name+'.kicad_pcb'); project=file.with_suffix('.kicad_pro'); original=project.read_bytes()
b=p.LoadBoard(str(file))
for f in b.GetFootprints():
 if f.GetReference() in ['H1','H2']: f.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL)
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(file),b)
project.write_bytes(original)
