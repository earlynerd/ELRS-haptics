"""One-time bounded five-wire migration. Never run after further user edits."""
from kicad_edit import *
BACK=HW/'backups/before-five-wire'
REMOVED={'J100','Q5','R6','R7','R44','C40'}
def props(s):return {uq(x[1]):uq(x[2]) for x in children(s,'property')}
def nc(a,x,y):a.append(parse(f'(no_connect (at {x} {y}) (uuid {uid()}))'))
def inside(x,y):return 129<=x<=175 and 118<=y<=150
def migrate_top():
 path=HW/'main/main.kicad_sch';a=load(path)
 assert any(props(s).get('Reference')=='Q5' for s in children(a,'symbol')),'Already migrated'
 for s in list(a):
  if not isinstance(s,list):continue
  k=s[0];ats=children(s,'at')
  if k=='symbol' and (props(s).get('Reference') in REMOVED or (props(s).get('Reference','').startswith('#') and inside(*map(float,child(s,'at')[1:3])))):a.remove(s)
  elif k=='wire':
   pts=child(s,'pts')[1:]
   if all(inside(*map(float,z[1:3])) for z in pts) or any(z[1:3]==['93.98','83.82'] for z in pts):a.remove(s)
  elif k in ['junction','label','global_label'] and ats and (inside(*map(float,ats[0][1:3])) or (k=='global_label' and uq(s[1])=='RING_RESET_ASSERT')):a.remove(s)
  elif k=='text':
   t=uq(s[1])
   if 'six-wire' in t:s[1]=q(t.replace('six-wire','five-wire'))
   if t.startswith('One shared 10k'):s[1]=q('Pod recovery: cycle +3V3_POD through U26.\nNo shared reset wire; local ICE reset only.')
   elif t.startswith('TX pulldown'):s[1]=q('TX pulldown keeps the ring quiet while U1 resets.\nBefore pod power OFF: detach UART, TX low;\nRX input with pull-up disabled. No signal isolators.')
   elif t.startswith('GPIO19 ring TX'):s[1]=q('GPIO19 ring TX / GPIO2 ring RX\nGPIO18 spare (no connect)\nGPIO3 high powers pods\nGPIO6/7: main-board power/USB I2C only')
 nc(a,88.9,83.82);save(path,a)
def migrate_pod(sat):
 path=HW/('satellite/satellite.kicad_sch' if sat else 'main/local-pod.kicad_sch');a=load(path)
 for s in list(a):
  if not isinstance(s,list):continue
  if s[0]=='symbol' and not sat and props(s).get('Reference')=='J100':a.remove(s)
  elif s[0]=='wire':
   pts=child(s,'pts')[1:];xy=[tuple(map(float,z[1:3])) for z in pts]
   if xy==[(71.12,190.5),(137.16,190.5)]:a.remove(s)
   elif not sat and any(pt in xy for pt in [(71.12,187.96),(71.12,195.58)]):a.remove(s)
   elif not sat and xy[0][0]==71.12 and xy[0][1] in [182.88,185.42,193.04]:pts[0][1]='104.14'
  elif s[0] in ['label','global_label']:
   pos=tuple(map(float,child(s,'at')[1:3]))
   if uq(s[1])=='RING_nRESET':
    if pos==(104.14,190.5):a.remove(s)
    else:
     s[0]='label';s[1]=q('LOCAL_nRESET')
     for c in children(s,'shape')+children(s,'property'):s.remove(c)
   elif not sat and pos in [(76.2,187.96),(76.2,195.58)]:a.remove(s)
  elif s[0]=='text' and uq(s[1]).startswith('Only CHAIN OUT'):s[1]=q('CHAIN OUT connects to satellite 1.\nLocal MCU receives directly from ESP32; no CHAIN IN bank.')
 nc(a,137.16,190.5)
 if sat:nc(a,71.12,190.5)
 note=q('Five-wire harness: pad 4 unused. Local nRESET uses internal pull-up.\nICE reset affects only this MCU; cycle pod power for chain recovery.')
 a.append(parse(f'(text {note} (at 30.48 259.08 0) (effects (font (size 1.27 1.27)) (justify left top)) (uuid {uid()}))'))
 save(path,a)
if __name__=='__main__':
 migrate_top();migrate_pod(False);migrate_pod(True)
