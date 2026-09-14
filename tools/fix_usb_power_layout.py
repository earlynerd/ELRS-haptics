"""Bounded visual/ERC cleanup after the USB/power migration."""
from kicad_edit import *
usb=Sheet('usb.kicad_sch')
# Separate external source flags: the previous vertical stubs touched.
for a in list(children(usb.a,'symbol')):
    if any(p[1]=='"Reference"' and uq(p[2]).startswith('#FLG') for p in children(a,'property')): usb.a.remove(a)
for a in list(children(usb.a,'wire')):
    pts=child(a,'pts')
    if all(float(p[1])==15.24 for p in pts[1:]) and max(float(p[2]) for p in pts[1:])<50.8: usb.a.remove(a)
for key in ['label','global_label']:
    for a in list(children(usb.a,key)):
        pos=child(a,'at')
        if float(pos[1])==15.24 and float(pos[2])<50.8: usb.a.remove(a)
FLAG=stock('power','PWR_FLAG')
usb.connected(FLAG,'#FLG01',15.24,38.1,{'1':'VBUS'},['GND'])
usb.connected(FLAG,'#FLG02',35.56,38.1,{'1':'GND'},['GND'])
# Preserve stock library definition, while retaining actual source URL on instances.
key=stock('Power_Protection','TPD2EUSB30')
libs=child(usb.a,'lib_symbols')
for a in list(children(libs,'symbol')):
    if a[1]==q(key):
        replacement=copy.deepcopy(symbols[key]); replacement[1]=q(key); libs[libs.index(a)]=replacement

# Keep field text horizontal on rotated R/L symbols.
power=Sheet('power.kicad_sch')
for sh in [usb,power]:
    for a in children(sh.a,'symbol'):
        angle=child(a,'at')[3]
        if angle=='90':
            for p in children(a,'property'):
                if uq(p[1]) in ['Reference','Value']: child(p,'at')[3]='90'
    sh.save()
print('Separated source flags and corrected field orientation/library cache.')
