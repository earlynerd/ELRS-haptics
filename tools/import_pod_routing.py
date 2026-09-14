"""Import routed sessions and refill the native copper planes for DRC."""
from pathlib import Path
import sys,shutil
import pcbnew as p
HW=Path(__file__).resolve().parents[1]/'hardware'
for i in map(int,sys.argv[1:]):
    dest=HW/f'verification/routing/pod-{i}'
    b=p.LoadBoard(str(dest/f'pod-{i}.kicad_pcb'))
    assert p.ImportSpecctraSES(b,str(dest/f'pod-{i}.ses'))
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones())
    p.SaveBoard(str(dest/f'pod-{i}-routed.kicad_pcb'),b)
    shutil.copy2(HW/'haptic-bracelet.kicad_pro',dest/f'pod-{i}-routed.kicad_pro')
    print(i,len(list(b.GetTracks())))
