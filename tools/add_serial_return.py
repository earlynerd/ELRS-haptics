"""One-time six-conductor harness migration; physical chain, logical UART ring."""
from kicad_edit import *
import shutil

backup=HW/'backups/before-serial-return'
backup.mkdir(parents=True,exist_ok=False)
for p in HW.glob('*.kicad_sch'): shutil.copy2(p,backup/p.name)
J6=stock('Connector_Generic','Conn_01x06'); R=stock('Device','R')
def props(s): return {uq(p[1]):uq(p[2]) for p in children(s,'property')}
def remove_connector(sh,ref):
    sym=next(s for s in children(sh.a,'symbol') if props(s).get('Reference')==ref)
    lib=next(s for s in children(child(sh.a,'lib_symbols'),'symbol') if s[1]==child(sym,'lib_id')[1])
    pos=child(sym,'at');x,y=map(float,pos[1:3]);assert pos[3]=='0'
    points={(round(x+float(child(p,'at')[1]),4),round(y-float(child(p,'at')[2]),4)) for sub in children(lib,'symbol') for p in children(sub,'pin')}
    ends=set()
    for w in list(children(sh.a,'wire')):
        wp={(float(pt[1]),float(pt[2])) for pt in children(child(w,'pts'),'xy')}
        if points&wp: ends|=wp;sh.a.remove(w)
    for typ in ['label','global_label','no_connect']:
        for label in list(children(sh.a,typ)):
            lp=child(label,'at')
            if (float(lp[1]),float(lp[2])) in ends|points: sh.a.remove(label)
    sh.a.remove(sym)
    return x,y

for i in range(8):
    sh=Sheet(f'pod_{i}.kicad_sch')
    existing=children(sh.a,'symbol')[0]
    sh.path=uq(child(child(child(existing,'instances'),'project'),'path')[1])
    for off,name,net in [(0,'CHAIN IN','RING_RX'),(1,'CHAIN OUT','RING_TX')]:
        ref=f'J{100+4*i+off}'; x,y=remove_connector(sh,ref)
        sh.connected(J6,ref,x,y,{'1':'POD_3V3','2':'GND','3':net,'4':'RING_nRESET','5':'VBAT_RAW','6':'RING_RETURN'},
                     ['POD_3V3','GND','RING_nRESET','VBAT_RAW','RING_RETURN'],value=name,footprint='',
                     notes='Six solder-pad/wire interface. Pin6 passes back to ESP RX. Seven wired gaps; no wire across clasp. Pin3 is local RX/forward TX, not return.')
    sh.text('Pin 6 RETURN: passive IN-to-OUT connection; do not connect intermediate MCU TX here.',20.32,266.7,1)
    if i==7:
        sh.passive(R,'R53','0',294.64,210.82,'RING_TX','RING_RETURN',['RING_RETURN'],angle=90,
                   notes='END POD ONLY: bridge final TX after R171 source resistor onto pin6 return. No cable on J129. Not a parallel connection to other TX outputs.')
        # Keep horizontal resistor labels readable in KiCad.
        s=next(s for s in children(sh.a,'symbol') if props(s).get('Reference')=='R53')
        for p in children(s,'property'):
            if uq(p[1]) in ['Reference','Value']: child(p,'at')[3]='90'
        sh.text('END POD: R53 joins TX to RETURN locally.\nJ129 is unused at the mechanical clasp; no closing cable.',238.76,233.68,1)
    sh.save()

top=Sheet('haptic-bracelet.kicad_sch')
for lab in children(top.a,'global_label'):
    if uq(lab[1])=='RING_D8':lab[1]=q('RING_RETURN')
for t in children(top.a,'text'):
    if uq(t[1]).startswith('250 kbaud:'): t[1]=q('250 kbaud logical ring: ESP TX -> pod 0 -> ... -> pod 7 -> RETURN -> ESP RX.\nPhysical six-wire chain; RETURN runs back through the same links. No electrical connection across clasp.')
top.save()
over=Sheet('haptics.kicad_sch')
for t in children(over.a,'text'):
    v=uq(t[1])
    if v.startswith('EIGHT PODS /'): t[1]=q('EIGHT PODS / SIX-WIRE CHAIN / LOGICAL UART RING')
    elif v.startswith('IN/OUT:'):t[1]=q('IN/OUT: 1 switched 3V3, 2 GND, 3 forward DATA, 4 MCU reset, 5 VBAT_RAW, 6 RETURN to ESP RX.')
    elif v.startswith('ESP TX ->'):t[1]=q('ESP TX -> D0 -> pod 0 -> D1 -> ... -> pod 7 -> D8 -> R53 -> RETURN -> ESP RX\nRETURN passes through each intermediate board without an MCU connection. R53 fitted at end pod only.\nWire J101->J104, J105->J108, ... J125->J128 pin-for-pin. No cable between end pod and main pod across clasp.\nPower, GND, reset and VBAT_RAW follow the chain; each fitted cell retains its local positive fuse.')
over.save()
print('Added sixth return conductor and R53 end-pod bridge. Clasp is electrically open.')
