"""Load the draft footprint through KiCad; verify pad geometry and render inputs."""
from pathlib import Path
import json
import pcbnew
root=Path(__file__).resolve().parents[1]
lib=root/'hardware/HapticBracelet.pretty'
name='Vybronics_VLV041235L_FPC_Contact_Draft'
fp=pcbnew.FootprintLoad(str(lib),name)
assert fp is not None
pads=sorted(fp.Pads(),key=lambda p:p.GetNumber())
assert len(pads)==2
pad_data=[]
for p,x in zip(pads,[-.9,.9]):
    assert abs(pcbnew.ToMM(p.GetPosition().x)-x)<1e-6
    assert p.GetPosition().y==0
    assert abs(pcbnew.ToMM(p.GetSize().x)-1)<1e-6
    assert abs(pcbnew.ToMM(p.GetSize().y)-2.2)<1e-6
    assert p.IsOnLayer(pcbnew.F_Cu) and p.IsOnLayer(pcbnew.F_Mask)
    assert not p.IsOnLayer(pcbnew.F_Paste)
    pad_data.append({'number':p.GetNumber(),'x_mm':x,'y_mm':0,'size_mm':[1,2.2]})
board=pcbnew.BOARD();board.Add(fp);fp.SetReference('M1');fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(20),pcbnew.FromMM(20)))
pcbnew.SaveBoard(str(root/'hardware/verification/lra-contact-preview.kicad_pcb'),board)
(root/'hardware/verification/lra-contact-checks.json').write_text(json.dumps({'status':'PASS','pads':pad_data,'pitch_mm':1.8,'scope':'KiCad load, pad dimensions and copper/mask/no-paste layers. Mechanical fit and soldering not tested.'},indent=2)+'\n')
print('PASS: KiCad loaded two 1.0x2.2 mm lands at 1.8 mm pitch; no paste apertures.')
