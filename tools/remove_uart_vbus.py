"""Bounded main-only removal of redundant UART pads and discrete VBUS sensing."""
import sys, xml.etree.ElementTree as E
from kicad_edit import *
from readable_schematic import props

REMOVED={'J1','Q4','R34','R35','R36'}
BACK=HW/'backups/before-uart-vbus-removal'

def get(name):
    p=HW/'main'/name
    assert p.read_bytes()==(BACK/'main'/name).read_bytes(), 'File changed since backup: '+name
    return p,load(p)

def points(w):return [tuple(map(float,p[1:])) for p in children(child(w,'pts'),'xy')]

def schematic():
    p,a=get('main.kicad_sch')
    for s in children(a,'symbol'):
        if props(s)['Reference']=='J1':a.remove(s)
    # J1's six isolated labelled stubs; remove the now-unused ESP signal stubs too.
    nc={(88.9,63.5),(88.9,66.04),(58.42,71.12)}
    count=0
    for w in children(a,'wire'):
        pts=points(w)
        if all(109<=x<=115 and 36<=y<=50 for x,y in pts) or any(pt in nc for pt in pts):
            a.remove(w);count+=1
    assert count==9,count
    for z in children(a,'global_label'):
        x,y=map(float,child(z,'at')[1:3])
        if (109<=x<=115 and 36<=y<=50) or uq(z[1]) in {'UART_TX','UART_RX','VBUS_nPRESENT'}:a.remove(z)
    for x,y in sorted(nc):a.append(parse(f'(no_connect (at {x} {y}) (uuid {uid()}))'))
    for t in children(a,'text'):
        v=uq(t[1])
        if 'GPIO0/14/22/23 spare' in v:
            t[1]=q(v.replace('GPIO0/14/22/23 spare (USB controls removed)','GPIO0/1/14/22/23 spare (USB controls removed)\nUART0 pads removed; native USB handles programming/debug'))
    save(p,a)
    p,a=get('usb.kicad_sch')
    for s in children(a,'symbol'):
        if props(s)['Reference'] in REMOVED|{'#PWR13978','#PWR13979','#PWR13980'}:a.remove(s)
    count=0
    for w in children(a,'wire'):
        if all(140<=x<=177 and 138<=y<=205 for x,y in points(w)):a.remove(w);count+=1
    assert count==8,count
    for kind in ['global_label','junction']:
        for z in children(a,kind):
            x,y=map(float,child(z,'at')[1:3])
            if 140<=x<=177 and 138<=y<=205:a.remove(z)
    for t in children(a,'text'):
        if uq(t[1])=='VBUS presence / 3.3 V logic':a.remove(t)
        elif 'USB_VBUS connects directly' in uq(t[1]):
            t[1]=q(uq(t[1])+'\nRead VIN_PGOOD_STAT over charger I2C for usable input-power status.\nNo discrete VBUS detector or UART service bank.')
    save(p,a)
    print('Removed J1 and VBUS detector; GPIO1/RXD0/TXD0 now NC.')

def pcb():
    p,a=get('main.kicad_pcb')
    root=E.parse(HW/'verification/project-split/main.xml').getroot()
    nodes={(n.attrib['ref'],n.attrib['pin']):net.attrib['name'].replace('/','{slash}') if net.attrib['name'].startswith('unconnected-') else net.attrib['name'] for net in root.findall('nets/net') for n in net.findall('node')}
    for f in children(a,'footprint'):
        ref=props(f)['Reference']
        if ref in REMOVED:a.remove(f);continue
        for pad in children(f,'pad'):
            if children(pad,'net'):child(pad,'net')[1]=q(nodes.get((ref,uq(pad[1])),''))
    save(p,a)
    print('Five footprints removed; retained PCB placement unchanged.')

if __name__=='__main__':{'schematic':schematic,'pcb':pcb}[sys.argv[1]]()
