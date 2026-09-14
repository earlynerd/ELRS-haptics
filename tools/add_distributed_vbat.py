"""Add raw parallel-cell bus to pod interfaces, without bypassing pack protection."""
from kicad_edit import *
import shutil
backup=HW/'backups/before-distributed-vbat'
if backup.exists():raise SystemExit('VBAT migration already ran; edit native files.')
backup.mkdir(parents=True)
for p in HW.glob('*.kicad_sch'):shutil.copy2(p,backup/p.name)
J5=stock('Connector_Generic','Conn_01x05');J2=stock('Connector_Generic','Conn_01x02');J3=stock('Connector_Generic','Conn_01x03')
F=stock('Device','Fuse')
def remove_with_stubs(sh,ref):
    sym=next(s for s in children(sh.a,'symbol') if any(p[1:3]==[q('Reference'),q(ref)] for p in children(s,'property')))
    lib=next(s for s in children(child(sh.a,'lib_symbols'),'symbol') if s[1]==child(sym,'lib_id')[1])
    pos=child(sym,'at');x=float(pos[1]);y=float(pos[2]);assert pos[3]=='0'
    points={(round(x+float(child(p,'at')[1]),4),round(y-float(child(p,'at')[2]),4)) for sub in children(lib,'symbol') for p in children(sub,'pin')}
    ends=set()
    for w in list(children(sh.a,'wire')):
        wp={(float(pt[1]),float(pt[2])) for pt in children(child(w,'pts'),'xy')}
        if points&wp:ends|=wp;sh.a.remove(w)
    for typ in ['label','global_label','no_connect']:
        for label in list(children(sh.a,typ)):
            lp=child(label,'at')
            if (float(lp[1]),float(lp[2])) in ends|points:sh.a.remove(label)
    sh.a.remove(sym)
    return x,y

for i in range(8):
    sh=Sheet(f'pod_{i}.kicad_sch');existing=children(sh.a,'symbol')[0]
    sh.path=uq(child(child(child(existing,'instances'),'project'),'path')[1])
    j=100+4*i;PG=['POD_3V3','GND','RING_nRESET','VBAT_RAW']
    for off,nm,net in [(0,'RING IN','RING_RX'),(1,'RING OUT','RING_TX')]:
        x,y=remove_with_stubs(sh,f'J{j+off}')
        sh.connected(J5,f'J{j+off}',x,y,{'1':'POD_3V3','2':'GND','3':net,'4':'RING_nRESET','5':'VBAT_RAW'},PG,value=nm,footprint='')
    # The cell connector and fuse represent an optional populated cell branch.
    sh.connected(J2,f'J{200+i}',35.56,88.9,{'1':'CELL_POS','2':'GND'},PG,value='CELL (optional)',footprint='',
      notes='Single matched pouch cell branch. Fit local positive fuse adjacent to cell; cell model and connector TBD.')
    sh.connected(F,f'F{100+i}',35.56,116.84,{'1':'CELL_POS','2':'VBAT_RAW'},PG,value='CELL FUSE TBD',footprint='',
      notes='Populate with cell branch. Rating/interruption capability and placement require selected cell/wire data. Do not replace with a wire.')
    for t in children(sh.a,'text'):
        if uq(t[1]).startswith('C100-family'):t[1]=q('MCU bypass capacitors adjacent to VDD.\nVBAT_RAW stays live when POD_3V3 is OFF.\nOptional cell + fuse and NTC fitted at cell locations.')
    sh.save()
overview=Sheet('haptics.kicad_sch')
for t in children(overview.a,'text'):
    text=uq(t[1])
    if text.startswith('EIGHT PODS /'):t[1]=q('EIGHT PODS / FIVE-CONDUCTOR INTER-POD WIRING')
    elif text.startswith('IN/OUT pin order:'):t[1]=q('IN/OUT: 1 switched 3V3, 2 GND, 3 DATA, 4 MCU reset, 5 VBAT_RAW (parallel cell bus).')
    elif text.startswith('ESP TX ->'):t[1]=q('ESP TX -> D0 -> pod 0 -> D1 -> ... -> pod 7 -> D8 -> ESP RX\nVBAT_RAW, switched 3V3, ground and reset are common; DATA is point-to-point.\nEach fitted cell joins VBAT_RAW through its own nearby fuse. Main positive-path pack protection feeds BAT_PROTECTED.')
overview.save()
power=Sheet('power.kicad_sch');existing=children(power.a,'symbol')[0]
power.path=uq(child(child(child(existing,'instances'),'project'),'path')[1])
power.connected(J3,'J4',304.8,226.06,{'1':'VBAT_RAW','2':'BAT_PROTECTED','3':'GND'},['VBAT_RAW','BAT_PROTECTED','GND'],
 value='PACK PROTECTOR INTERFACE',footprint='',notes='External/provisional high-side bidirectional 1S pack protector: pin1 raw cell positive, pin2 protected positive, pin3 common ground. Circuit/thresholds pending. Never short pins1-2.')
power.text('J4: positive-path pack protection REQUIRED (implementation pending).\nCommon negative / GND; raw and protected positives remain separate.\nCells + branch fuses are shown on pod sheets. J3 carries protected\nterminals and the charger NTC; no raw-cell connection on J3.',243.84,241.3,1)
for t in children(power.a,'text'):
    text=uq(t[1])
    if text.startswith('PACK BOUNDARY'):t[1]=q('PACK BOUNDARY\nJ4 defines an unimplemented high-side bidirectional protector.\nSelect branch fuses, protector and thresholds against actual cells.\nVBAT_RAW remains energized when pod logic/actuator power is off.')
power.save()
print('Added fifth VBAT conductor, eight optional fused cell branches and explicit high-side protector interface.')
