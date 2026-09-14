"""Check KiCad-exported USB/power connectivity and independent datasheet pin maps."""
from kicad_edit import *
import xml.etree.ElementTree as ET

doc=ET.parse(HW/'verification/netlist.xml').getroot()
nets={}
for net in doc.findall('./nets/net'):
    nodes={(n.attrib['ref'],n.attrib['pin']) for n in net.findall('node')}
    for node in nodes: nets[node]=(net.attrib['name'],nodes)
def same(*nodes):
    names={nets[n][0] for n in nodes}
    assert len(names)==1,(nodes,names)
def different(*nodes): assert len({nets[n][0] for n in nodes})==len(nodes)
def exact(*nodes):
    same(*nodes)
    assert nets[nodes[0]][1]==set(nodes),(nodes,nets[nodes[0]])

# Both connector orientations, independent polarity, ESD and series resistors.
exact(('J2','A6'),('J2','B6'),('U14','1'),('R25','1'))
exact(('J2','A7'),('J2','B7'),('U14','2'),('R24','1'))
same(('R24','2'),('U1','17'))
same(('R25','2'),('U1','18'))
different(('U1','17'),('U1','18'),('U1','3'),('U1','1'))
same(('J2','A5'),('U13','1'),('U15','1'))
same(('J2','B5'),('U13','2'),('U15','2'))
different(('U13','1'),('U13','2'),('U1','3'),('U1','1'))
same(('U13','3'),('U13','5'),('U13','11'),('U1','1'))
same(('U13','12'),('U1','3'))
same(('U13','7'),('U11','7'),('U1','15'),('R1','2'))
same(('U13','8'),('U11','8'),('U1','16'),('R2','2'))
exact(('U13','4'),('R26','2'))
same(('R26','1'),('J2','A4'))
same(('U13','6'),('R27','2'),('U1','12'))

# Power rails must be distinct; check source, input limiting, charger and output.
different(('J2','A4'),('U16','6'),('U11','1'),('U11','2'),('U12','6'),('U1','1'))
same(('J2','A4'),('J2','A9'),('J2','B4'),('J2','B9'),('U16','1'),('U17','3'),('U17','5'))
same(('U16','6'),('U11','10'),('C34','1'))
same(('U11','1'),('U12','10'),('U12','1'),('C35','1'),('C37','1'),('R38','1'))
same(('U11','2'),('J3','1'),('C36','1'))
same(('U11','5'),('U11','11'),('J3','2'),('J3','4'),('U1','1'))
same(('U11','6'),('J3','3'),('SW3','1'))
same(('U11','4'),('R38','2'),('Q1','3'))
same(('Q1','1'),('R39','1'),('U1','26'))
same(('Q1','2'),('R39','2'),('U1','1'))
same(('U11','9'),('U1','27'),('R37','2'))
exact(('U12','9'),('L1','1'))
exact(('U12','7'),('L1','2'))
same(('U12','6'),('R40','1'),('C38','1'),('C39','1'),('U1','3'))
exact(('U12','4'),('R40','2'),('R41','1'))
same(('U12','3'),('U12','8'),('U12','2'),('R41','2'),('U1','1'))

# Hardware reset/default controls and current-limit selection.
exact(('U16','5'),('U17','4'))
exact(('U17','1'),('R28','1'),('R29','1'))
same(('R28','2'),('Q3','2'),('U1','1'))
exact(('R29','2'),('Q3','3'))
same(('U17','6'),('R31','1'),('U1','28'))
same(('Q3','1'),('R30','1'),('U1','29'))
same(('U16','3'),('R32','2'),('Q2','3'))
same(('Q2','1'),('R33','1'),('U1','19'))
same(('Q4','3'),('R36','2'),('U1','13'))
same(('Q4','2'),('R35','2'),('U1','1'))
exact(('R34','2'),('R35','1'),('Q4','1'))

# Pin numbers independently transcribed from manufacturer pin tables.
expected={
 'BQ25186DLH':{'10':'IN','1':'SYS','2':'BAT','5':'GND','11':'EP','4':'~{CE}','7':'SDA','8':'SCL','9':'~{INT}','3':'~{PG}/GPO','6':'TS/MR'},
 'TPS63802DLA':{'1':'EN','2':'MODE','3':'AGND','4':'FB','5':'PG','6':'VOUT','7':'L2','8':'GND','9':'L1','10':'VIN'},
 'TUSB320LAIRWB':{'1':'CC1','2':'CC2','3':'PORT','4':'VBUS_DET','5':'ADDR','6':'~{INT}','7':'SDA','8':'SCL','9':'ID','10':'GND','11':'~{EN}','12':'VDD'},
 'TPS2553DBV':{'1':'IN','2':'GND','3':'EN','4':'~{FAULT}','5':'ILIM','6':'OUT'},
 'TS5A3159DBV':{'1':'NO','2':'GND','3':'NC','4':'COM','5':'V+','6':'IN'},
}
lib=load(HW/'HapticBracelet.kicad_sym')
for name,pins in expected.items():
    sym=next(s for s in children(lib,'symbol') if s[1]==q(name))
    actual={uq(child(p,'number')[1]):uq(child(p,'name')[1]) for sub in children(sym,'symbol') for p in children(sub,'pin')}
    assert pins==actual,(name,pins,actual)

# Values come from the exported design, not the generator.
values={c.attrib['ref']:c.findtext('value') for c in doc.findall('./components/comp')}
def resistance(ref):
    s=values[ref].split()[0]
    return float(s[:-1])*1000 if s.endswith('k') else float(s)
vout=.5*(1+resistance('R40')/resistance('R41'))
assert 3.30<vout<3.32
rlo=resistance('R28')/1000
rhi=1/(1/rlo+1000/resistance('R29'))
imax_lo=22980/(rlo*.99)**.94
imax_hi=22980/(rhi*.99)**.94
assert imax_lo<490 and imax_hi<1200
report={'status':'PASS','pinmaps_checked':list(expected),'regulator_nominal_V':vout,'usb_programmed_limits_mA':{'normal_min':25230/(rlo*1.01)**1.016,'normal_max':imax_lo,'high_min':25230/(rhi*1.01)**1.016,'high_max':imax_hi},'limit_model':'TPS2553 datasheet section 9.5.1; resistor tolerance 1%; switch R/leakage and dynamics excluded','scope':'Netlist and nominal/worst-resistor calculations; not SPICE, USB compliance, pack or bench validation.'}
(HW/'verification/usb-power-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
