"""Migrate the integrated main schematic to a controller-only daughterboard.

Requires the pre-stacked-controller-20260914 backup; keeps surviving identities.
"""
import copy,json,hashlib
from kicad_edit import *
from readable_schematic import Drawing,props

BACK=HW/'backups/pre-stacked-controller-20260914'
OUT=HW/'verification/stacked-controller'
assert not (HW/'stacked-architecture.json').exists(), 'Migration already applied; do not overwrite subsequent edits.'
main=load(BACK/'main/main.kicad_sch')
local=load(BACK/'main/local-pod.kicad_sch')
removed=sorted(props(s)['Reference'] for s in children(local,'symbol') if not props(s)['Reference'].startswith('#') and props(s)['Reference']!='J101')
sheet=next(s for s in children(main,'sheet') if props(s).get('Sheetfile')=='local-pod.kicad_sch')
for pr in children(sheet,'property'):
 if uq(pr[1])=='Sheetname':pr[2]=q('Stacked universal pod interface')
 if uq(pr[1])=='Sheetfile':pr[2]=q('pod-interface.kicad_sch')
for t in children(main,'text'):
 if uq(t[1])=='HAPTIC BRACELET / MAIN PCBA':t[1]=q('HAPTIC BRACELET / CONTROLLER DAUGHTERBOARD')
 if '250 kbaud logical ring:' in uq(t[1]):t[1]=q('250 kbaud ring: ESP TX -> J101 -> universal pod 0 -> ... -> pod 7 -> RETURN -> ESP RX.\n8 identical pod PCBAs + 1 controller daughterboard; protected batteries/NTCs on pods 1-7 only.')
if children(main,'title_block'):
 t=child(main,'title_block');child(t,'title')[1]=q('Haptic bracelet - stacked controller');child(t,'date')[1]=q('2026-09-14')
save(HW/'main/main.kicad_sch',main)

path='/'+uq(child(main,'uuid')[1])+'/'+uq(child(sheet,'uuid')[1])
d=Drawing(BACK/'main/local-pod.kicad_sch',HW/'main/pod-interface.kicad_sch','main',path,'Controller to universal pod stack')
d.inst('J101',139.7,101.6)
s=d.instances['J101']
for pr in children(s,'property'):
 if uq(pr[1])=='Value':pr[2]=q('STACK TO POD 0')
 if uq(pr[1])=='BOM Comments':pr[2]=q('Five electrical contacts to universal pod 0 J1, pin-for-pin. Existing wire pads retained; stacking connector mechanics pending.')
for pin,net in [('1','+3V3_POD'),('2','GND'),('3','RING_D0'),('4','VBAT'),('5','RING_RETURN')]:d.term('J101',pin,net,global_=True,length=22.86)
d.text('CONTROLLER DAUGHTERBOARD / FIVE-CONTACT STACK INTERFACE',25.4,25.4,2)
d.text('J101 connects pin-for-pin to J1 on universal pod 0.\nThe existing five-pad footprint is retained until the mechanical stack is set.',25.4,40.64,1.27)
d.text('1  Switched 3.3 V: daughterboard -> all eight pods\n2  Common ground\n3  ESP TX through R42 -> pod 0 RX\n4  Protected VBAT bus: seven cells <-> charger\n5  Last pod TX return -> ESP RX',172.72,88.9,1.27)
d.text('SYSTEM ASSEMBLY\nOne controller daughterboard; eight copies of satellite/satellite.kicad_pro.\nPod 0 sits beneath this board: no battery and no external NTC fitted.\nPods 1-7 each carry one protected pouch cell and its external NTC.\nThe pod PCBA and component population are identical in all positions.',25.4,139.7,1.27)
d.text('CHAIN AND RETURN\nDaughterboard J101 -> pod 0 J1. Each pod J2 -> next pod J1.\nPods 0-6: JP1 NORMAL (1-2). Pod 7: cut 1-2, bridge 2-3 END.\nPod 7 J2 is uncabled. The clasp gap remains unwired.',25.4,177.8,1.27)
d.text('POWER AND TEMPERATURE\nAll eight M2003/DRV2625 nodes share switched +3V3_POD.\nOnly pod 0 battery/NTC sockets are unused; keep its sensing/fuse circuitry.\nFirmware expects seven required cell sensors on pods 1-7.\nDisable charging if a required sensor is missing, stale or out of range.\nSeven-cell charge/load limits still require firmware configuration.',25.4,213.36,1.27)
d.finish()
# Remove the obsolete active child; its full circuit is retained in the backup.
(HW/'main/local-pod.kicad_sch').unlink()
power=load(HW/'main/power.kicad_sch')
for t in children(power,'text'):
 if 'Cell and NTC use J200/J103' in uq(t[1]):t[1]=q('C34: IN bypass    C35: SYS reservoir    C36: BAT bypass\nSW3: wake/ship button. R62: fixed TS/MR termination.\nVBAT arrives through J101 from seven protected cells on pods 1-7.\nNo cell or NTC in pod 0. Require fresh temperatures from pods 1-7 before charge.')
save(HW/'main/power.kicad_sch',power)

sat=load(HW/'satellite/satellite.kicad_sch')
sat.append(parse(f'(text {q("ASSEMBLY: eight identical pod PCBAs per wrist. Pod 0 stacks beneath the controller; leave J4 battery and J5 NTC unwired. Pods 1-7 fit protected cells and NTCs. JP1 NORMAL on pods 0-6; END on pod 7.")} (at 25.4 274.32 0) (effects (font (size 1 1)) (justify left top)) (uuid {uid()}))'))
save(HW/'satellite/satellite.kicad_sch',sat)

# Synchronize fitted footprints without attempting the new mechanical placement.
b=load(BACK/'main/main.kicad_pcb')
for f in list(children(b,'footprint')):
 ref=props(f)['Reference']
 if ref in removed:b.remove(f)
 elif ref=='J101':
  for pr in children(f,'property'):
   if uq(pr[1])=='Value':pr[2]=q('STACK TO POD 0')
  for pad in children(f,'pad'):
   if uq(pad[1])=='3':child(pad,'net')[1]=q('RING_D0')
# The sole saved trace is the removed driver's B2-C2 tie.
assert len(children(b,'segment'))==1 and not children(b,'via') and not children(b,'zone')
for t in children(b,'segment'):b.remove(t)
save(HW/'main/main.kicad_pcb',b)
placement=json.loads((HW/'main/placement-reference.json').read_text())
for key in ['placements','layers']:
 if key in placement:
  for ref in removed:placement[key].pop(ref,None)
placement.update({'architecture':'stacked-controller','placement_status':'Surviving controller positions and legacy outline only; new daughterboard outline and placement pending','removed_local_pod_references':removed})
(HW/'main/placement-reference.json').write_text(json.dumps(placement,indent=2)+'\n')

# Preserve current project metadata, restoring the user's already-selected rules.
pro=json.loads((HW/'main/main.kicad_pro').read_text())
rules=json.loads((HW/'backups/pre-main-routing-20260913/main.kicad_pro').read_text())
pro['board']['design_settings']=rules['board']['design_settings']
pro['net_settings']=rules['net_settings']
(HW/'main/main.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
manifest={'architecture':'stacked-controller','controller_pcba_quantity':1,'universal_pod_pcba_quantity':8,'battery_count':7,'battery_pods':list(range(1,8)),'no_battery_pods':[0],'required_cell_ntc_pods':list(range(1,8)),'normal_jumper_pods':list(range(7)),'end_jumper_pod':7,'stack_pin_nets':{'1':'+3V3_POD','2':'GND','3':'RING_D0','4':'VBAT','5':'RING_RETURN'},'removed_main_references':removed,'main_outline_and_placement':'pending mechanical stack design','baseline':'hardware/backups/pre-stacked-controller-20260914','satellite_pcb_sha256':hashlib.sha256((HW/'satellite/satellite.kicad_pcb').read_bytes()).hexdigest()}
(HW/'stacked-architecture.json').write_text(json.dumps(manifest,indent=2)+'\n')
(OUT/'migration.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Removed local functions from main:',', '.join(removed))
