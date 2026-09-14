"""One-time six-position to five-position harness migration, from saved inputs."""
from kicad_edit import *
import copy
BACK=HW/'backups/before-five-pad'
def props(a):return {uq(x[1]):uq(x[2]) for x in children(a,'property')}
fpname='WirePads_5_P2mm'
foot=load(HW/'HapticBracelet.pretty/WirePads_6_P2mm.kicad_mod');foot[1]=q(fpname)
for x in children(foot,'pad'):
 old=int(uq(x[1]))
 if old==4:foot.remove(x);continue
 new=old if old<4 else old-1;x[1]=q(new);child(x,'at')[2]=str(-4+2*(new-1))
for x in children(foot,'fp_rect'):
 for field in ['start','end']:
  z=child(x,field);z[2]=str(float(z[2])+(1 if float(z[2])<0 else -1))
for x in children(foot,'property'):
 if uq(x[1])=='Value':x[2]=q(fpname)
 z=child(x,'at');z[2]=str(float(z[2])+(1 if float(z[2])<0 else -1))
save(HW/'HapticBracelet.pretty'/f'{fpname}.kicad_mod',foot)
symbol=copy.deepcopy(next(s for s in children(load(LIB/'Connector_Generic.kicad_sym'),'symbol') if uq(s[1])=='Conn_01x05'));symbol[1]=q('Connector_Generic:Conn_01x05')
for name,refs,sheet in [('main',{'J101'},'local-pod'),('satellite',{'J1','J2'},'satellite')]:
 target=HW/name/f'{sheet}.kicad_sch';source=BACK/name/target.name
 assert target.read_bytes()==source.read_bytes(),'Schematic changed after snapshot'
 a=load(source);lib=child(a,'lib_symbols')
 if not any(x[1]==symbol[1] for x in children(lib,'symbol')):lib.append(copy.deepcopy(symbol))
 for x in list(a):
  if not isinstance(x,list):continue
  if x[0]=='symbol' and props(x).get('Reference') in refs:
   child(x,'lib_id')[1]=symbol[1]
   for z in children(x,'property'):
    if uq(z[1])=='Footprint':z[2]=q('HapticBracelet:'+fpname)
    elif uq(z[1])=='BOM Comments':z[2]=q('Five wire pads: 1 switched 3V3, 2 GND, 3 forward data, 4 VBAT, 5 return. No wire across clasp.')
   for z in children(x,'pin'):
    old=int(uq(z[1]))
    if old==4:x.remove(z)
    elif old>4:z[1]=q(old-1)
  elif x[0] in ['wire','label','global_label','junction','no_connect']:
   positions=child(x,'pts')[1:] if x[0]=='wire' else children(x,'at')
   for pos in positions:
    xx,yy=map(float,pos[1:3])
    if 70<=xx<=138:
     if yy==190.5 and x[0]=='no_connect':a.remove(x)
     elif yy in [193.04,195.58]:pos[2]=str(round(yy-2.54,2))
  elif x[0]=='text' and 'Five-wire harness: pad 4 unused.' in uq(x[1]):x[1]=q(uq(x[1]).replace('Five-wire harness: pad 4 unused.','Five-pad harness: 4 VBAT, 5 return.'))
 save(target,a)
 target=HW/name/f'{name}.kicad_pcb';source=BACK/name/target.name
 assert target.read_bytes()==source.read_bytes(),'PCB changed after snapshot'
 a=load(source)
 for f in children(a,'footprint'):
  if props(f)['Reference'] not in refs:continue
  assert len(child(f,'at'))==3,'Expected unrotated pad bank'
  f[1]=q('HapticBracelet:'+fpname);child(f,'at')[2]=str(float(child(f,'at')[2])-1)
  for x in children(f,'pad'):
   old=int(uq(x[1]))
   if old==4:f.remove(x);continue
   new=old if old<4 else old-1;x[1]=q(new);child(x,'at')[2]=str(-4+2*(new-1))
  for x in children(f,'fp_rect'):f.remove(x)
  for x in children(foot,'fp_rect'):
   z=copy.deepcopy(x);z.append(['uuid',q(uid())]);f.append(z)
  for x in children(f,'property'):
   if uq(x[1])=='BOM Comments':x[2]=q('Five wire pads: 1 switched 3V3, 2 GND, 3 forward data, 4 VBAT, 5 return. No wire across clasp.')
 if name=='satellite':
  # Reconnect only the two moved lands at either side; all other copper stays.
  removeids={'23b71adc-0a24-44af-a866-c5f7c142932e','41ef499e-6ad3-4280-a7a8-e1b7196c51d8','48fd50cd-1375-4519-aa91-ebdee085e465','adaf3486-88e5-4449-a0c9-6d282613aacd'}
  for t in children(a,'segment'):
   if uq(child(t,'uuid')[1]) in removeids:a.remove(t)
   elif uq(child(t,'uuid')[1]) in ['22418042-6c0e-47ec-86bc-42fbd4ed381f','8bb8b531-d46b-42c0-8056-c6c9acfb80e3']:child(t,'start')[2]='116'
  for pts in [[(104.1,114),(105.45,114),(105.45,116.05)],[(118.9,114),(117.9,114),(117.9,116.014547),(117.5,116.414547)]]:
   for v,w in zip(pts,pts[1:]):a.append(parse(f'(segment (start {v[0]} {v[1]}) (end {w[0]} {w[1]}) (width 0.2) (layer "F.Cu") (net "VBAT") (uuid {uid()}))'))
  for t in children(a,'gr_text'):
   tx=uq(t[1])
   if tx=='NC':a.remove(t)
   elif tx.strip() in ['VBAT','RET']:
    z=child(t,'at');z[2]=str(float(z[2])-1)
 save(target,a)
print('Applied five-pad harness footprint, schematic pin map, and local routing.')
