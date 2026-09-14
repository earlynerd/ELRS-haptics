"""One-time visual cleanup of the initial native schematic properties."""
from pathlib import Path
import json,re

root=Path(__file__).resolve().parents[1]/'hardware'
for file in ['haptic-bracelet.kicad_sch','haptics.kicad_sch','power.kicad_sch']:
    path=root/file
    s=path.read_text(encoding='utf-8').replace('(rev "0.1 - schematic start")','(rev "0.1")')
    pattern=r'\(symbol \(lib_id "([^"]+)"\) \(at ([\d.]+) ([\d.]+) 0\)(.*?)(?=\(symbol \(lib_id|\(wire |\(text |\(no_connect |\(label |\(global_label |\(sheet |\(sheet_instances |\(embedded_fonts no\)\)\s*$)'
    def change(m):
        lib=m[1]; x=float(m[2]); y=float(m[3]); block=m[0]
        if lib in ['Device:R','Device:C']:
            for prop,dy in [('Reference',-1.27),('Value',1.27)]:
                block=re.sub(r'(\(property "'+prop+r'" "[^"]*" \(at )[-\d.]+ [-\d.]+ 0\)',lambda z:z[1]+f'{x+3.81:.4f} {y+dy:.4f} 0)',block)
        elif lib=='HapticBracelet:Actuator_TBD':
            block=block.replace('"Actuator TBD"','"TBD"')
            for prop in ['Reference','Value']:
                block=re.sub(r'(\(property "'+prop+r'" "[^"]*" \(at )[-\d.]+ ([-\d.]+) 0\)',lambda z:z[1]+f'{x-5.08:.4f} {z[2]} 0)',block)
        else:
            for prop in ['Reference','Value']:
                block=re.sub(r'(\(property "'+prop+r'" "[^"]*" \(at )[-\d.]+ ([-\d.]+) 0\)',lambda z:z[1]+f'{x+10.16:.4f} {z[2]} 0)',block)
        return block
    s=re.sub(pattern,change,s,flags=re.S)
    path.write_text(s,encoding='utf-8')
print('Adjusted symbol text positions.')
