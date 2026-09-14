"""Route the universal board's three-way selector on outer copper only."""
import pcbnew as p
import sys
from pathlib import Path
from routing_v08 import track,via
PATH=Path(__file__).resolve().parents[1]/'hardware/satellite/satellite.kicad_pcb'
if '--apply-to-fresh-split' not in sys.argv:
 raise SystemExit('Historical migration only. Explicit --apply-to-fresh-split is required; do not apply twice or after native edits.')
b=p.LoadBoard(str(PATH))
for net,pos,points in [
 ('/RETURN_UP',(10.5,29.4),[(5.834315,28.35),(9.45,28.35),(10.5,29.4)]),
 ('/RETURN_DOWN',(13.7,29.4),[(14.065686,28.35),(13.7,28.715686),(13.7,29.4)])]:
 via(b,net,pos,.5,.2);track(b,net,points,.1524,p.B_Cu)
 track(b,net,[pos,(pos[0],30.8)] if net=='/RETURN_UP' else [pos,(13.7,31.8),(13.2,32.3),(9.7,32.3),(9.2,31.8),(9.2,30.8)],.1524,p.F_Cu)
via(b,'/TX_OUT',(14.4,15.3),.5,.2)
via(b,'/TX_OUT',(11.8,29.4),.5,.2)
track(b,'/TX_OUT',[(11.8,29.4),(11.8,30.8)],.1524,p.F_Cu)
track(b,'/TX_OUT',[(14.4,15.3),(16.4,17.3),(16.4,27.6),(12.75,31.25),(12.5,31.25),(11.8,30.55),(11.8,29.4)],.1524,p.B_Cu)
# Source via lands on the existing 45-degree TX trace; split it for an explicit junction.
for t in list(b.GetTracks()):
 if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='/TX_OUT' and t.GetLayer()==p.F_Cu:
  a,z=t.GetStart(),t.GetEnd()
  if abs(p.ToMM(a.x)-117.11)<.0001 and abs(p.ToMM(a.y)-111.01)<.0001 and abs(p.ToMM(z.x)-118.1)<.0001:
   width=p.ToMM(t.GetWidth());b.Remove(t);track(b,'/TX_OUT',[(14.11,15.01),(14.4,15.3),(15.1,16)],width)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(PATH),b)
