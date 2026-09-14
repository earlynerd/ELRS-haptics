"""Create separate native projects with wired functional schematics."""
from readable_schematic import *
MAIN=HW/'main';SAT=HW/'satellite';VERIFY=HW/'verification/project-split'
TOP=load(ARCH/'haptic-bracelet.kicad_sch');ROOTID=uq(child(TOP,'uuid')[1]);ROOTPATH='/'+ROOTID
SHEETS={props(s)['Sheetfile']:s for s in children(TOP,'sheet')}
LOCALPATH=ROOTPATH+'/'+uq(child(SHEETS['haptics.kicad_sch'],'uuid')[1])
SATROOT=uq(child(load(ARCH/'pod_6.kicad_sch'),'uuid')[1]);SATPATH='/'+SATROOT
SATREF={'U24':'U1','U9':'U2','R160':'R1','R161':'R2','R162':'R3','R163':'R4','R165':'R5','R20':'R6','R21':'R7','C160':'C1','C161':'C2','C163':'C3','C162':'C4','C23':'C5','C24':'C6','C25':'C7','J124':'J1','J125':'J2','J126':'J3','J206':'J4','J127':'J5','F106':'F1','M7':'M1'}
GLOBALS={'I2C_SDA','I2C_SCL','USB_D_P','USB_D_N','MCU_EN','BOOT_IO9','BOOT_IO8','UART_TX','UART_RX','RING_D0','RING_D1','RING_RETURN','RING_nRESET','CHG_ALLOW','CHG_nINT','CC_nINT','VBUS_nPRESENT','USB_INPUT_OFF','USB_LIMIT_ENABLE','USB_LIMIT_HIGH','USB_5V_LIMITED','LED_R_N','LED_G_N','LED_B_N'}
def make_top():
    a=copy.deepcopy(TOP)
    def walk(x):
        if not isinstance(x,list):return
        if x and x[0]=='project':x[1]=q('main')
        if x and x[0] in ['global_label','label']:
            if uq(x[1])=='3V3':x[1]=q('+3V3')
            if uq(x[1])=='POD_3V3':x[1]=q('+3V3_POD')
        for z in x:walk(z)
    walk(a)
    for sheet in children(a,'sheet'):
        for pp in children(sheet,'property'):
            if uq(pp[1])=='Sheetfile' and uq(pp[2])=='haptics.kicad_sch':pp[2]=q('local-pod.kicad_sch')
            if uq(pp[1])=='Sheetname' and uq(pp[2])=='Eight ring pods':pp[2]=q('Local haptic pod and harness')
        page={'local-pod.kicad_sch':2,'power.kicad_sch':3,'usb.kicad_sch':4,'controller-support.kicad_sch':5}[props(sheet)['Sheetfile']]
        child(child(child(child(sheet,'instances'),'project'),'path'),'page')[1]=q(page)
    # The obsolete QOD wire was left below the redrawn, already-connected resistor.
    for w in children(a,'wire'):
        if uq(child(w,'uuid')[1])=='4bb0e1d6-262f-4888-a349-75f16c3aea6c':a.remove(w)
    for lab in children(a,'label'):
        if uq(child(lab,'uuid')[1])=='3c26fe4c-2bdb-4442-95be-79b7e0a06da8':a.remove(lab)
    for t in children(a,'text'):
        if uq(t[1]).startswith('ATTITUDE FEEDBACK'):t[1]=q('HAPTIC BRACELET / MAIN PCBA')
    save(MAIN/'main.kicad_sch',a)

def pod(satellite):
    dlt=0 if satellite else -6
    def rr(ref):
        if satellite:return ref
        n=int(ref[1:]);c=ref[0]
        return c+str(n+(dlt if c in ['U','M','F'] or (c=='J' and n>=200) else (4*dlt if c=='J' else 10*dlt if n>=100 else (3*dlt if c=='C' else 2*dlt))))
    d=Drawing('pod_6.kicad_sch' if satellite else 'pod_0.kicad_sch',SAT/'satellite.kicad_sch' if satellite else MAIN/'local-pod.kicad_sch','satellite' if satellite else 'main',SATPATH if satellite else LOCALPATH,'Universal satellite / MCU, haptics and chain selection' if satellite else 'Local haptic pod / main PCBA',SATREF if satellite else {})
    I=lambda r,x,y,a=0:d.inst(rr(r),x,y,a)
    P=lambda r,n:d.pt(rr(r),str(n))
    N=lambda r,n:(rr(r),str(n))
    I('U24',121.92,101.6);I('U9',248.92,86.36)
    # MCU SDA/SCL and driver pins share the same two horizontal wires.
    for r,x,y in [('R20',218.44,63.5),('R21',208.28,63.5)]:I(r,x,y)
    d.join(N('U24',5),N('U9','B1'));d.join(N('U24',6),N('U9','C1'))
    for r,n in [('R20',5),('R21',6)]:
        x,y=P(r,2);yy=P('U24',n)[1];d.wire((x,y),(x,yy));d.dot((x,yy))
    # Decoupling is wired to one visible supply rail, grouped beside each IC.
    for r,x in [('C160',50.8),('C161',35.56),('C163',20.32),('C23',271.78),('C25',287.02)]:I(r,x,53.34)
    d.rail('+3V3_POD',[N('U24',9),N('U9','C2'),N('R20',1),N('R21',1)]+[N(r,1) for r in ['C160','C161','C163','C23','C25']],40.64)
    d.rail('GND',[N(r,2) for r in ['C160','C161','C163']],60.96);d.rail('GND',[N(r,2) for r in ['C23','C25']],63.5)
    d.term(*N('U9','B2'),'+3V3_POD',power=True)
    I('M7',309.88,81.28)
    for dp,mp in [('A3',1),('C3',2)]:
        a,z=P('U9',dp),P('M7',mp);d.wire(a,(z[0],a[1]),z)
    I('C24',281.94,97.79);d.join(N('U9','A2'),N('C24',1));d.term(*N('C24',2),'GND',power=True)
    # Receive/transmit resistors and ICE pullups are part of the MCU circuit.
    I('R160',55.88,83.82,90);I('R161',55.88,88.9,270)
    d.join(N('R160',2),N('U24',18));d.join(N('R161',1),N('U24',8))
    I('R162',73.66,71.12);I('R163',83.82,71.12)
    for r,other,n in [('R162','U24',18),('R163','U24',8)]:
        x,y=P(r,2);yy=P(other,n)[1];d.wire((x,y),(x,yy));d.dot((x,yy))
    d.rail('+3V3_POD',[N('R162',1),N('R163',1)],63.5)
    d.term(*N('R160',1),'RING_RX' if satellite else 'RING_D0',global_=not satellite)
    d.term(*N('R161',2),'TX_OUT' if satellite else 'RING_D1',global_=not satellite)
    I('R165',63.5,111.76);I('C162',78.74,127);I('J127',40.64,123.19,180)
    adc=P('U24',2);bottom=P('R165',2);cap=P('C162',1);ntc=P('J127',1)
    d.wire(adc,(88.9,adc[1]),(88.9,119.38),(63.5,119.38),bottom);d.wire((63.5,119.38),(63.5,cap[1]),cap);d.dot((63.5,119.38));d.dot((63.5,cap[1]));d.wire(ntc,(63.5,ntc[1]));d.term(*N('R165',1),'+3V3_POD',power=True);d.term(*N('C162',2),'GND',power=True);d.term(*N('J127',2),'GND',power=True)
    d.text('MCU / local I2C and optional cell NTC',30.48,22.86)
    d.text('DRV2625 / local energy storage and actuator',223.52,22.86)
    d.text('Harness and initial programming',30.48,165.1)
    # External interfaces are below the complete local circuit. Shared power/reset
    # rails are drawn continuously between the two connector banks.
    d.inst(rr('J124'),66.04,187.96,mirror='y');I('J125',142.24,187.96);I('J126',246.38,193.04)
    for pin,name in [(1,'+3V3_POD'),(2,'GND'),(4,'RING_nRESET'),(5,'VBAT')]:
        a,z=P('J124',pin),P('J125',pin);d.wire(a,z);d.label(name,((a[0]+z[0])/2,a[1]),not satellite and name in ['GND','RING_nRESET'])
    d.term(*N('J124',3),'RING_RX' if satellite else 'RING_D0',global_=not satellite)
    d.term(*N('J125',3),'TX_OUT' if satellite else 'RING_D1',global_=not satellite)
    d.term(*N('U24',4),'RING_nRESET',global_=not satellite)
    if satellite:
        key=stock('Jumper','SolderJumper_3_Bridged12');d.libs[key]=copy.deepcopy(symbols[key]);d.libs[key][1]=q(key)
        s=copy.deepcopy(d.old[rr('R20')]);child(s,'lib_id')[1]=q(key)
        for pp in children(s,'property'):
            if uq(pp[1])=='Reference':pp[2]=q('JP1')
            if uq(pp[1])=='Value':pp[2]=q('RETURN SELECT')
            if uq(pp[1])=='Footprint':pp[2]=q('Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm')
        child(s,'uuid')[1]=q(str(uuid.uuid5(uuid.NAMESPACE_URL,'haptic-bracelet/satellite/JP1')))
        for pp in children(s,'pin'):s.remove(pp)
        child(s,'in_bom')[1]='no';d.old['JP1']=s;d.inst('JP1',104.14,228.6,180)
        d.wire(P('J124',6),(104.14,195.58),d.pt('JP1',2));d.label('RETURN_UP',(88.9,195.58))
        d.wire(P('J125',6),(127,195.58),(127,228.6),d.pt('JP1',1));d.label('RETURN_DOWN',(127,215.9))
        d.term('JP1','3','TX_OUT')
        d.text('JP1: 1-2 NORMAL (factory bridge)\nLast satellite: cut 1-2; solder 2-3 END.\nCentre feeds upstream return; never bridge all three.',160.02,238.76,1.27)
        for k in ['sheet_instances']:
            for x in children(d.a,k):d.a.remove(x)
        d.add('(sheet_instances (path "/" (page "1")))')
    else:
        d.term(*N('J124',6),'RING_RETURN',global_=True);d.term(*N('J125',6),'RING_RETURN',global_=True)
        d.text('Only CHAIN OUT is cabled to satellite 1.\nCHAIN IN pads are local access to ESP TX/return.',30.48,243.84,1.27)
    # Battery positive is visibly wired through its branch fuse.
    I('J206',322.58,190.5,180);I('F106',345.44,190.5,90)
    d.join(N('J206',1),N('F106',1));d.term(*N('J206',2),'GND',power=True);d.term(*N('F106',2),'VBAT',power=True)
    d.text('Protected cell output only\nRetain factory PCM; fuse is secondary.',309.88,213.36,1.27)
    # Debug connector labels refer to explicitly wired MCU-side nets.
    for r,pin,n in [('R160',2,'UART_RX_LOCAL'),('R161',1,'UART_TX_LOCAL')]:d.label(n,P(r,pin))
    for num,n in [(1,'+3V3_POD'),(2,'GND'),(3,'UART_TX_LOCAL'),(4,'UART_RX_LOCAL'),(5,'RING_nRESET')]:d.term(*N('J126',num),n,power=n=='+3V3_POD',global_=(not satellite and n in ['GND','RING_nRESET']))
    d.text('Remove RX and TX series links for ICE isolation.\nMCU reset does not reset driver; cycle pod power.',208.28,218.44,1.27)
    if satellite:
        d.power('PWR_FLAG',(121.92,40.64));d.dot((121.92,40.64))
        d.term(*N('U24',7),'GND',power=True);d.power('PWR_FLAG',(121.92,137.16))
        d.power('PWR_FLAG',(P('F106',2)[0]+5.08,P('F106',2)[1]))
    d.finish(GLOBALS if not satellite else ())

def power():
    path=ROOTPATH+'/'+uq(child(SHEETS['power.kicad_sch'],'uuid')[1]);d=Drawing('power.kicad_sch',MAIN/'power.kicad_sch','main',path,'Charger and buck-boost supply')
    I=d.inst;P=d.pt
    I('U11',101.6,81.28);I('U12',292.1,81.28)
    I('C34',66.04,110.49);d.wire(P('U11',10),(66.04,P('U11',10)[1]),P('C34',1));d.term('C34',2,'GND',power=True);d.label('USB_5V_LIMITED',(66.04,71.12),True)
    I('C35',144.78,83.82);I('C36',160.02,83.82)
    d.wire(P('U11',1),(144.78,P('U11',1)[1]),P('C35',1));d.label('SYS',(144.78,71.12));d.term('C35',2,'GND',power=True)
    d.wire(P('U11',2),(160.02,P('U11',2)[1]),P('C36',1));d.power('VBAT',(160.02,78.74));d.term('C36',2,'GND',power=True)
    d.power('PWR_FLAG',(160.02,78.74))
    d.rail('GND',[('U11','5'),('U11','11')],109.22)
    I('R38',48.26,66.04);I('Q1',48.26,109.22);I('R39',27.94,116.84)
    # Pull-up and drain meet CE; gate has its own pulldown and command boundary.
    d.wire(P('R38',2),(48.26,P('U11',4)[1]),P('U11',4));d.dot((48.26,P('U11',4)[1]));d.wire(P('Q1',3),(P('Q1',3)[0],78.74),(48.26,78.74));d.dot((P('Q1',3)[0],78.74));d.term('R38',1,'SYS')
    gate=P('Q1',1);d.wire(gate,(27.94,gate[1]),P('R39',1));d.label('CHG_ALLOW',(27.94,gate[1]),True);d.dot((27.94,gate[1]));d.rail('GND',[('Q1','2'),('R39','2')],132.08)
    I('SW3',144.78,127,90);d.wire(P('U11',6),(134.62,P('U11',6)[1]),(134.62,P('SW3',1)[1]),P('SW3',1));d.term('SW3',2,'GND',power=True)
    I('J3',193.04,111.76);d.term('J3',1,'VBAT',power=True);d.term('J3',2,'GND',power=True);d.term('J3',4,'GND',power=True)
    a,z=P('J3',3),P('U11',6);d.wire(a,(175.26,a[1]),(175.26,z[1]),z)
    I('R37',76.2,53.34);d.term('R37',1,'+3V3',power=True)
    d.wire(P('R37',2),(76.2,93.98),P('U11',9));d.dot((76.2,93.98));d.wire((76.2,93.98),(76.2,99.06));d.label('CHG_nINT',(76.2,99.06),True,180)
    # Inductor is drawn directly between the two switch nodes.
    I('L1',292.1,48.26,90)
    for n,lp in [(9,1),(7,2)]:
        a,z=P('U12',n),P('L1',lp);d.wire(a,(a[0],z[1]),z)
    I('C37',251.46,83.82);d.wire(P('U12',10),(251.46,71.12),P('C37',1));d.label('SYS',(251.46,71.12));d.term('C37',2,'GND',power=True)
    d.wire(P('U12',1),(264.16,P('U12',1)[1]),(264.16,71.12));d.dot((264.16,71.12))
    I('C38',337.82,82.55);I('C39',358.14,82.55)
    d.wire(P('U12',6),(337.82,71.12),(358.14,71.12));
    for r in ['C38','C39']:d.wire(P(r,1),(P(r,1)[0],71.12));d.dot((P(r,1)[0],71.12))
    d.power('+3V3',(358.14,71.12));d.rail('GND',[('C38','2'),('C39','2')],96.52)
    I('R40',325.12,100.33);I('R41',325.12,120.65)
    d.wire(P('R40',1),(325.12,71.12));d.dot((325.12,71.12))
    d.wire(P('R40',2),(325.12,111.76),P('R41',1));d.wire(P('U12',4),(314.96,P('U12',4)[1]),(314.96,111.76),(325.12,111.76));d.dot((325.12,111.76));d.term('R41',2,'GND',power=True)
    d.rail('GND',[('U12','2'),('U12','3'),('U12','8')],137.16)
    d.text('BQ25186 power path / protected 1S bus',25.4,22.86)
    d.text('TPS63802 / regulated +3V3',238.76,22.86)
    d.text('C34: IN bypass    C35: SYS reservoir    C36: BAT bypass\nSW3 is the user wake/ship button. J3 includes the charger thermistor.\nCharge-enable defaults off; firmware configures the protected pack.',25.4,180.34,1.27)
    d.text('Keep SYS at 4.5 V when USB powered.\nMODE low selects power-save operation.\nFeedback: 511k / 91k; nominal output 3.308 V.',238.76,180.34,1.27)
    d.finish(GLOBALS)

def support():
    path=ROOTPATH+'/'+uq(child(SHEETS['controller-support.kicad_sch'],'uuid')[1]);d=Drawing('controller-support.kicad_sch',MAIN/'controller-support.kicad_sch','main',path,'Controller support / reset, straps and RGB status')
    I=d.inst;P=d.pt
    for r,x in [('R1',45.72),('R2',63.5),('C2',93.98),('C3',116.84)]:I(r,x,53.34)
    d.rail('+3V3',[(r,'1') for r in ['R1','R2','C2','C3']],40.64)
    d.rail('GND',[('C2','2'),('C3','2')],68.58)
    d.term('R1',2,'I2C_SDA',global_=True);d.term('R2',2,'I2C_SCL',global_=True)
    I('R3',172.72,50.8);I('C1',193.04,74.93);I('SW1',172.72,83.82)
    d.term('R3',1,'+3V3',power=True)
    d.wire(P('R3',2),(172.72,66.04),(193.04,66.04),P('C1',1));d.label('MCU_EN',(172.72,66.04),True);d.dot((172.72,66.04))
    d.wire((172.72,66.04),(162.56,66.04),(162.56,83.82),P('SW1',1));d.rail('GND',[('SW1','2'),('C1','2')],99.06)
    I('R5',264.16,50.8);I('SW2',264.16,83.82)
    d.term('R5',1,'+3V3',power=True);d.wire(P('R5',2),(264.16,66.04),(254,66.04),(254,83.82),P('SW2',1));d.label('BOOT_IO9',(264.16,66.04),True);d.term('SW2',2,'GND',power=True)
    I('R4',345.44,53.34);d.term('R4',1,'+3V3',power=True);d.term('R4',2,'BOOT_IO8',global_=True)
    I('D1',269.24,167.64)
    for series,pull,x,y,name,pin in [('R47','R48',190.5,162.56,'LED_R_N',1),('R49','R50',180.34,167.64,'LED_G_N',2),('R51','R52',170.18,172.72,'LED_B_N',3)]:
        I(series,208.28+17.78*(pin-1),y,90);I(pull,x,139.7);d.join((series,'2'),('D1',str(pin)));d.wire(P(series,1),(152.4,y));d.label(name,(152.4,y),True);d.wire(P(pull,2),(x,y));d.dot((x,y))
    d.rail('+3V3',[(r,'1') for r in ['R48','R50','R52']],124.46);d.term('D1',4,'+3V3',power=True)
    d.text('I2C pullups and ESP supply bypass',25.4,22.86)
    d.text('Reset / enable',157.48,22.86);d.text('Download boot',246.38,22.86);d.text('Boot strap',330.2,22.86)
    d.text('RGB status / common anode, active-low GPIOs',142.24,109.22)
    d.text('Pullups keep all colours off while the ESP GPIOs are undriven.\nFirmware assigns charging, connection and fault indications.',142.24,195.58,1.27)
    d.finish(GLOBALS)

def usb():
    path=ROOTPATH+'/'+uq(child(SHEETS['usb.kicad_sch'],'uuid')[1]);d=Drawing('usb.kicad_sch',MAIN/'usb.kicad_sch','main',path,'USB-C / native data, CC detection and input limiting')
    I=d.inst;P=d.pt
    I('J2',40.64,73.66);I('U13',325.12,86.36)
    for pins,x,y,r in [(['A7','B7'],66.04,71.12,'R24'),(['A6','B6'],71.12,78.74,'R25')]:
        for n in pins:d.wire(P('J2',n),(x,P('J2',n)[1]),(x,y))
        d.dot((x,y));I(r,152.4,y,90);d.wire((x,y),P(r,1));d.wire(P(r,2),(220.98,y));d.label(nice(PIN_NET[(r,'2')]),(220.98,y),True)
    I('U14',106.68,93.98)
    for n in ['1','2']:
        x,y=P('U14',n);target=71.12 if PIN_NET[('U14',n)].endswith('USB_CONN_N') else 78.74;d.wire((x,y),(x,target));d.dot((x,target))
    for r,x in [('C29',187.96),('C30',208.28)]:
        I(r,x,97.79);target=71.12 if 'USB_D_N' in PIN_NET[(r,'1')] else 78.74;d.wire(P(r,1),(x,target));d.dot((x,target));d.term(r,2,'GND',power=True)
    for pin,ix,yy,fx,n in [('A5',81.28,43.18,299.72,1),('B5',86.36,48.26,294.64,2)]:
        a,z=P('J2',pin),P('U13',n);d.wire(a,(ix,a[1]),(ix,yy),(fx,yy),(fx,z[1]),z)
    I('U15',248.92,60.96)
    for n in ['1','2']:
        x,y=P('U15',n);target=43.18 if PIN_NET[('U15',n)].endswith('CC1') else 48.26;d.wire((x,y),(x,target));d.dot((x,target))
    I('C31',355.6,53.34);I('R27',375.92,71.12)
    d.rail('+3V3',[('U13','12'),('C31','1'),('R27','1')],40.64);d.term('C31',2,'GND',power=True)
    d.wire(P('U13',6),(383.54,88.9));d.label('CC_nINT',(383.54,88.9),True);d.wire(P('R27',2),(375.92,88.9));d.dot((375.92,88.9))
    I('R26',274.32,88.9,90);d.join(('R26','2'),('U13','4'));d.term('R26',1,'VBUS')
    d.rail('GND',[('U13',str(n)) for n in [3,5,10,11]],119.38)
    d.term('J2','A4','VBUS');d.rail('GND',[('J2','A1'),('J2','SH')],109.22)
    # VBUS current limiter and resistor-selection switch.
    I('U16',60.96,180.34);I('U17',142.24,187.96);I('C32',30.48,180.34)
    d.wire(P('U16',1),(30.48,172.72),P('C32',1));d.label('VBUS',(30.48,172.72));d.term('C32',2,'GND',power=True)
    d.wire(P('U16',5),(106.68,180.34),(106.68,182.88),P('U17',4))
    I('C33',160.02,162.56);d.wire(P('U17',5),(142.24,152.4),(180.34,152.4),(180.34,182.88),P('U17',3));d.label('VBUS',(142.24,152.4));d.wire(P('C33',1),(160.02,152.4));d.dot((160.02,152.4));d.term('C33',2,'GND',power=True)
    d.wire(P('U17',1),(205.74,187.96),(238.76,187.96))
    I('R28',205.74,205.74);I('R29',238.76,205.74)
    for r in ['R28','R29']:d.wire(P(r,1),(P(r,1)[0],187.96));d.dot((P(r,1)[0],187.96))
    d.term('R28',2,'GND',power=True);I('Q3',236.22,226.06);d.join(('R29','2'),('Q3','3'))
    I('R30',215.9,233.68);d.wire(P('Q3',1),(215.9,226.06),P('R30',1));d.label('USB_LIMIT_HIGH',(215.9,226.06),True);d.rail('GND',[('R30','2'),('Q3','2')],246.38)
    I('R31',116.84,215.9);d.wire(P('U17',6),(116.84,193.04),P('R31',1));d.label('USB_LIMIT_ENABLE',(116.84,193.04),True);d.term('R31',2,'GND',power=True)
    # Inhibit defaults high through R32; the ESP pulls the input enable low.
    I('R32',27.94,210.82);I('Q2',53.34,236.22);I('R33',33.02,243.84)
    d.term('R32',1,'VBUS');d.wire(P('R32',2),(27.94,223.52),(55.88,223.52),P('Q2',3));d.wire(P('U16',3),(20.32,P('U16',3)[1]),(20.32,223.52),(27.94,223.52));d.dot((27.94,223.52))
    d.wire(P('Q2',1),(33.02,236.22),P('R33',1));d.label('USB_INPUT_OFF',(33.02,236.22),True);d.rail('GND',[('R33','2'),('Q2','2')],256.54)
    # USB presence sensing: divider drives the MOSFET; output is pulled to 3V3.
    I('R34',292.1,175.26);I('R35',292.1,213.36);I('Q4',322.58,195.58);I('R36',325.12,165.1)
    d.term('R34',1,'VBUS');d.wire(P('R34',2),(292.1,195.58),P('R35',1));d.wire((292.1,195.58),P('Q4',1));d.dot((292.1,195.58))
    d.join(('R36','2'),('Q4','3'));d.term('R36',1,'+3V3',power=True);d.wire((325.12,180.34),(365.76,180.34));d.dot((325.12,180.34));d.label('VBUS_nPRESENT',(365.76,180.34),True)
    d.rail('GND',[('R35','2'),('Q4','2')],228.6)
    d.power('PWR_FLAG',(30.48,172.72));d.power('PWR_FLAG',(33.02,109.22));d.dot((33.02,109.22))
    d.text('USB-C receptacle / ESD and native USB',25.4,22.86);d.text('CC current advertisement',294.64,22.86)
    d.text('Input current limit / firmware selects allowable current',25.4,137.16);d.text('VBUS present',292.1,137.16)
    d.text('C29/C30 are optional DNP tuning capacitors.\nCC detection informs firmware before selecting a higher input limit.',266.7,251.46,1.27)
    d.finish(GLOBALS)

if __name__=='__main__':
    import sys
    mode=sys.argv[1]
    if '--replace-from-snapshot' not in sys.argv:
        raise SystemExit('Historical migration only. Edit native projects; explicit --replace-from-snapshot is required to discard subsequent schematic edits.')
    if mode=='top':make_top()
    if mode=='satellite':pod(True)
    if mode=='local':pod(False)
    if mode=='power':power()
    if mode=='support':support()
    if mode=='usb':usb()

