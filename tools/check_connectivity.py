"""Check exported topology against the intended eight-node UART ring."""
from kicad_edit import *
import xml.etree.ElementTree as ET
doc=ET.parse(HW/'verification/netlist.xml').getroot()
nets={}
for net in doc.findall('./nets/net'):
    nodes={(n.attrib['ref'],n.attrib['pin']) for n in net.findall('node')}
    for node in nodes:
        assert node not in nets,node
        nets[node]=(net.attrib['name'],nodes)
def same(*nodes):
    assert len({nets[n][0] for n in nodes})==1,[(n,nets.get(n)) for n in nodes]
def exact(*nodes):
    same(*nodes)
    assert nets[nodes[0]][1]==set(nodes),(nodes,nets[nodes[0]])
def different(*nodes): assert len({nets[n][0] for n in nodes})==len(nodes),nodes
components={c.attrib['ref']:c for c in doc.findall('./components/comp')}
values={ref:c.findtext('value') for ref,c in components.items()}
for value in ['M2003FC1AE','DRV2625','VLV041235L']: assert sum(v==value for v in values.values())==8
assert 'U2' not in components
assert not any('TCA9548' in v for v in values.values())
local=[]
for i in range(8):
    m=f'U{18+i}';d=f'U{3+i}';b=100+10*i;j=100+4*i
    for mp,dp,r in [('5','B1',f'R{8+2*i}'),('6','C1',f'R{9+2*i}')]:
        exact((m,mp),(d,dp),(r,'2'));same((r,'1'),('U26','6'))
        local.append(nets[(m,mp)][0])
    exact((m,'13'))  # Former driver reset GPIO is intentionally unused.
    same((d,'B2'),(d,'C2'),('U26','6'))
    assert f'R{b+4}' not in components
    exact((d,'A3'),(f'M{i+1}','1'));exact((d,'C3'),(f'M{i+1}','2'))
    exact((d,'A2'),(f'C{6+3*i}','1'))
    exact((d,'A1'))  # Explicitly unused TRIG/INTZ, no-connect flag on each pod.
    same((m,'9'),(d,'C2'),('U26','6'),(f'C{b}','1'),(f'C{b+1}','1'),(f'C{5+3*i}','1'),(f'C{7+3*i}','1'))
    same((m,'7'),(d,'B3'),('U1','1'),(f'C{b}','2'),(f'C{b+1}','2'),(f'C{5+3*i}','2'),(f'C{6+3*i}','2'),(f'C{7+3*i}','2'))
    same((m,'4'),('R6','2'),('R44','1'),('C40','1'))
    # Debug is on the MCU side of BOTH removable UART series links.
    exact((m,'18'),(f'R{b}','2'),(f'R{b+2}','2'),(f'J{j+2}','4'))
    exact((m,'8'),(f'R{b+1}','1'),(f'R{b+3}','2'),(f'J{j+2}','3'))
    same((f'R{b+2}','1'),(f'R{b+3}','1'),('U26','6'))
    assert values[f'R{b}']=='0' and values[f'R{b+1}']=='33'
    for ref in [f'J{j}',f'J{j+1}',f'J{j+2}']:
        same((ref,'1'),('U26','6'));same((ref,'2'),('U1','1'))
    same((f'J{j}','4'),(f'J{j+1}','4'),(f'J{j+2}','5'),(m,'4'))
    same((f'J{j}','5'),(f'J{j+1}','5'),(f'F{100+i}','2'),('U11','2'))
    exact((f'J{200+i}','1'),(f'F{100+i}','1'))
    same((f'J{200+i}','2'),('U1','1'))
    same((f'C{b+3}','1'),('U26','6')); same((f'C{b+3}','2'),('U1','1'))
    assert values[f'C{b+3}']=='22u 10V X5R'
    assert values[f'J{200+i}']=='PROTECTED CELL 90mAh'
    same((f'J{j}','3'),(f'R{b}','1'));same((f'J{j+1}','3'),(f'R{b+1}','2'))
    exact((m,'2'),(f'R{b+5}','2'),(f'C{b+2}','1'),(f'J{j+3}','1'))
    same((f'R{b+5}','1'),('U26','6'));same((f'C{b+2}','2'),(f'J{j+3}','2'),('U1','1'))
    for pin in ['1','3','10','11','12','14','15','16','17','19','20']:
        assert nets[(m,pin)][1]=={(m,pin)},(m,pin,nets[(m,pin)])
assert len(set(local))==16
# A segment has two endpoints plus wiring pads, never two TX drivers.
exact(('R42','2'),('R100','1'),('J100','3'))
segments=[nets[('R42','2')][0]]
for i in range(7):
    exact((f'R{101+10*i}','2'),(f'J{101+4*i}','3'),(f'R{110+10*i}','1'),(f'J{104+4*i}','3'))
    segments.append(nets[(f'R{101+10*i}','2')][0])
exact(('R171','2'),('J129','3'),('R53','1'))
segments.append(nets[('R171','2')][0]);assert len(set(segments))==9
# Passive serial return traverses all six-pad interfaces, driven only by end-pod TX via R53.
return_nodes={('U1','5'),('R53','2')}|{(f'J{100+4*i+off}','6') for i in range(8) for off in [0,1]}
assert nets[('U1','5')][1]==return_nodes, nets[('U1','5')]
assert values['R53']=='0'
different(('R53','1'),('R53','2'))
for i in range(8):
    for off in [0,1]:
        c=components[f'J{100+4*i+off}']
        assert c.find('libsource').get('part')=='Conn_01x06'
exact(('U1','25'),('R42','1'),('R43','1'));same(('R43','2'),('U1','1'))
# Switched rail and reset must have no always-on pull-up into the pod domain.
same(('U26','1'),('U1','3'),('C41','1'))
same(('U26','6'),('R6','1'),('R46','1'),('C43','1'))
different(('U26','1'),('U26','6'),('U1','1'))
assert 'J4' not in components
different(('U11','2'),('U26','1'),('U26','6'),('U1','1'))
same(('J3','1'),('U11','2'))
assert nets[('U11','2')][0]=='VBAT'
assert nets[('U11','2')][1]=={('U11','2'),('J3','1'),('C36','1')}|{(f'F{100+i}','2') for i in range(8)}|{(f'J{100+4*i+off}','5') for i in range(8) for off in [0,1]}
assert not set(['U27','Q6','Q7','R54','R55','R56','C44']) & set(components)
assert values['C42']=='4.7n 25V'
exact(('U26','3'),('U1','6'),('R45','1'))
exact(('U26','4'),('C42','1'));exact(('U26','5'),('R46','2'))
same(('U26','2'),('C41','2'),('C42','2'),('C43','2'),('R45','2'),('U1','1'))
exact(('Q5','1'),('U1','24'),('R7','1'));exact(('Q5','3'),('R44','2'))
same(('Q5','2'),('R7','2'),('C40','2'),('U1','1'))
same(('U1','15'),('R1','2'),('U11','7'),('U13','7'))
same(('U1','16'),('R2','2'),('U11','8'),('U13','8'))
same(('U1','8'),('R3','2'),('C1','1'),('SW1','1'),('J1','6'))
same(('U1','22'),('R4','2'));same(('U1','23'),('R5','2'),('SW2','1'),('J1','5'))
same(('U1','30'),('J1','4'));same(('U1','31'),('J1','3'))
# Independent manufacturer physical pin tables.
expected={'M2003FC1AE':{'1':'PB1','2':'PB2 / ADC0_CH2','3':'PB3','4':'PE15 / nRESET','5':'PB4 / I2C0_SDA',
 '6':'PB5 / I2C0_SCL','7':'VSS','8':'PF0 / TXD1 / ICE_DAT','9':'VDD','10':'PC14','11':'PB15','12':'PB14',
 '13':'PB13','14':'PB12','15':'PB7','16':'PB8','17':'PB9','18':'PF1 / RXD1 / ICE_CLK','19':'PB11','20':'PB0'},
 'TPS22918DBV':{'1':'VIN','2':'GND','3':'ON','4':'CT','5':'QOD','6':'VOUT'}}
lib=load(HW/'HapticBracelet.kicad_sym')
for name,pins in expected.items():
    sym=next(s for s in children(lib,'symbol') if s[1]==q(name))
    actual={uq(child(p,'number')[1]):uq(child(p,'name')[1]) for sub in children(sym,'symbol') for p in children(sub,'pin')}
    assert actual==pins,(name,actual)
fp=load(Path('C:/Program Files/KiCad/10.0/share/kicad/footprints/Package_SO.pretty/TSSOP-20_4.4x6.5mm_P0.65mm.kicad_mod'))
assert {uq(p[1]) for p in children(fp,'pad')}=={str(i) for i in range(1,21)}
report={'status':'PASS','components':len(components),'pods':8,'interpod_conductors':6,'physical_wired_gaps':7,'serial_return':{'net':nets[('U1','5')][0],'end_bridge':'R53','pad':6,'intermediate_mcu_connections':0,'clasp_wiring':False},'fused_protected_battery_branches':8,'pack_protection':'Factory PCM on each battery; no central protection stage','additional_bulk_uF_per_pod':22,'uart_segments':segments,'independent_local_control_nets':len(set(local)),
 'pinmaps_checked':list(expected),'power_control':'GPIO3 ON; GPIO18 reset assert; GPIO19 TX low and GPIO2 RX no pull-up before power off',
 'scope':'Native connectivity, symbol and footprint pin counts. Firmware sequencing, loader port and hardware remain untested.'}
(HW/'verification/ring-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
