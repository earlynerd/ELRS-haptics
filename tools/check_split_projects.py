"""Verify the two PCBA masters against the verified pre-split circuit.

Run with KiCad Python after refreshing project-split XML/ERC/DRC reports.
Each process loads one PCB, avoiding cross-board SWIG lifetime issues.
"""
import sys,json,math,hashlib
from pathlib import Path
mount_manifest=Path(__file__).resolve().parents[1]/'hardware/mounting-layout.json'
if mount_manifest.exists() and json.loads(mount_manifest.read_text()).get('revision')=='pod-faces-v1':
    from check_pod_faces import check
    check(sys.argv[1])
    sys.exit(0)
if sys.argv[1]=='main' and (Path(__file__).resolve().parents[1]/'hardware/stacked-architecture.json').exists():
    from check_stacked_controller import check
    check()
    sys.exit(0)
import pcbnew as p
from redraw_projects import HW,ARCH,VERIFY,SATREF,load,children,child,props,uq,E
from split_pcb_projects import escaped
from simplify_usb import REMOVED as USB_REMOVED,NEW as USB_NEW
from pod_symmetry import REMOVED as SYMMETRY_REMOVED,NEW as SYMMETRY_NEW
from remove_uart_vbus import REMOVED as UART_VBUS_REMOVED

name=sys.argv[1];sat=name=='satellite';rename=SATREF if sat else {};reverse={v:k for k,v in rename.items()}
base=E.parse(HW/'verification/routing-v09/netlist.xml').getroot()
fresh=E.parse(VERIFY/(name+'.xml')).getroot()
oldpcb=load(ARCH/'haptic-bracelet.kicad_pcb')
ox,oy,w,h=(103,96,17,35) if sat else (35,35,21,61)
oldfps={props(f)['Reference']:f for f in children(oldpcb,'footprint') if ox-.01<=float(child(f,'at')[1])<=ox+w+.01 and oy-.01<=float(child(f,'at')[2])<=oy+h+.01}
if not sat:
    for ref in ['J100','Q5','R6','R7','R44','C40']:oldfps.pop(ref)
    for ref in USB_REMOVED:oldfps.pop(ref)
    for ref in SYMMETRY_REMOVED:oldfps.pop(ref)
    for ref in UART_VBUS_REMOVED:oldfps.pop(ref)
    placement_file=HW/'main/placement-reference.json'
    placement_reference=json.loads(placement_file.read_text()) if placement_file.exists() else None
    if placement_reference:
        for ref in ['J102','C29','C30']:oldfps.pop(ref)
else:placement_reference=None
recovery_pads=bool(placement_reference and placement_reference.get('recovery_pads'))
if recovery_pads:
    for ref in ['SW1','SW2']:oldfps.pop(ref)
reset_harness={('J124','4'),('J125','4')} if sat else {('J101','4')}
harness_refs={'J1','J2'} if sat else {'J101'}
old_harness_refs={'J124','J125'} if sat else {'J101'}
comps={c.attrib['ref']:c for c in fresh.findall('components/comp')}
expected={rename.get(r,r) for r in oldfps}|({'JP1'} if sat else set(USB_NEW)|set(SYMMETRY_NEW))
mounting=(HW/'mounting-layout.json').exists()
if mounting:expected|={'H1','H2'}
if placement_reference:expected.add('J1')
if recovery_pads:expected.add('J3')
assert set(comps)==expected,(set(comps)-expected,expected-set(comps))
basecomps={c.attrib['ref']:c for c in base.findall('components/comp')}
for oldref in oldfps:
    c=comps[rename.get(oldref,oldref)];old=basecomps[oldref]
    for field in ['value','footprint']:
        want='HapticBracelet:WirePads_5_P2mm' if field=='footprint' and oldref in old_harness_refs else old.findtext(field)
        assert c.findtext(field)==want,(oldref,field)
def groups(root,isnew):
    out=set()
    for net in root.findall('nets/net'):
        def baseline_node(n):
            ref=reverse.get(n.attrib['ref'],n.attrib['ref']) if isnew else n.attrib['ref'];pin=n.attrib['pin']
            if isnew and ref in old_harness_refs:pin={'4':'5','5':'6'}.get(pin,pin)
            return ref,pin
        nodes=frozenset(baseline_node(n) for n in net.findall('node') if baseline_node(n)[0] in oldfps)
        nodes=frozenset(n for n in nodes if n not in reset_harness)
        if nodes:out.add(nodes)
    return out
original=groups(base,False);current=groups(fresh,True)
if sat:
    original.remove(frozenset([('J124','6'),('J125','6')]))
    original.update([frozenset([('J124','6')]),frozenset([('J125','6')])])
else:
    # Removing the external input limiter joins raw VBUS and charger IN.
    raw=next(g for g in original if ('J2','A4') in g)
    limited=next(g for g in original if ('U11','10') in g)
    original.remove(raw);original.remove(limited);original.add(raw|limited)
assert original==current,('Circuit changed',original-current,current-original)
netnodes={net.attrib['name']:{(n.attrib['ref'],n.attrib['pin']) for n in net.findall('node')} for net in fresh.findall('nets/net')}
nodes={node:escaped(net) for net,parts in netnodes.items() for node in parts}
if recovery_pads:
    assert comps['J3'].findtext('footprint')=='HapticBracelet:ESP_Recovery_3Pads_P1.5mm'
    assert nodes[('J3','1')]==nodes[('U1','8')]==nodes[('C1','1')]==nodes[('R3','2')]=='MCU_EN'
    assert nodes[('J3','2')]=='GND'
    assert nodes[('J3','3')]==nodes[('U1','23')]==nodes[('R5','2')]=='BOOT_IO9'
localreset='/LOCAL_nRESET' if sat else '/Local haptic pod and harness/LOCAL_nRESET'
assert netnodes[localreset]==({('U1','4'),('J3','5')} if sat else {('U18','4'),('J1','3') if placement_reference else ('J102','5')})
if placement_reference:
    assert comps['J1'].findtext('footprint')=='Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical'
    for pin,ref,pin2 in [('1','U18','9'),('2','U18','8'),('3','U18','4'),('4','U18','18'),('5','U18','7')]:
        assert nodes[('J1',pin)]==nodes[(ref,pin2)]
    assert nodes[('J1','6')].startswith('unconnected-')
    assert nodes[('U3','B3')]=='GND'
for ref in harness_refs:
    assert nodes[(ref,'1')]=='+3V3_POD' and nodes[(ref,'2')]=='GND' and nodes[(ref,'4')]=='VBAT'
    assert (ref,'6') not in nodes and not nodes[(ref,'5')].startswith('unconnected-')
assert not any('RING_nRESET' in net or 'RING_RESET_ASSERT' in net for net in netnodes)
if not sat:
    assert netnodes['VBUS' if placement_reference else 'USB_VBUS']=={('J2','A4'),('J2','A9'),('J2','B4'),('J2','B9'),('C32','1'),('C34','1'),('U11','10')}
    for ref,pin,esdpin in [('R60','A5','1'),('R61','B5','2')]:
        assert comps[ref].findtext('value')=='5.1k 1%'
        assert comps[ref].findtext('footprint')=='Resistor_SMD:R_0402_1005Metric'
        assert netnodes[nodes[(ref,'1')]]=={(ref,'1'),('J2',pin),('U15',esdpin)}
        assert nodes[(ref,'2')]=='GND'
    for pin in ['12','13','19','28','29','30','31']:assert nodes[('U1',pin)].startswith('unconnected-')
    assert not any(n in netnodes for n in ['USB_5V_LIMITED','CC_nINT','USB_INPUT_OFF','USB_LIMIT_ENABLE','USB_LIMIT_HIGH','VBUS_nPRESENT','UART_TX','UART_RX'])
    assert comps['R62'].findtext('value')=='10k'
    assert comps['R62'].findtext('footprint')=='Resistor_SMD:R_0402_1005Metric'
    assert netnodes[nodes[('U11','6')]]=={('U11','6'),('SW3','1'),('R62','1')}
    assert nodes[('R62','2')]==nodes[('SW3','2')]=='GND'
    assert netnodes[nodes[('J103','1')]]=={('J103','1'),('U18','2'),('R105','2'),('C102','1')}
    assert netnodes[nodes[('J200','1')]]=={('J200','1'),('F100','1')}
    assert nodes[('F100','2')]=='VBAT'
    for net,r,pin in [('LED_R_N','R47','9'),('LED_G_N','R49','10'),('LED_B_N','R51','20')]:
        assert netnodes[net]=={(r,'1'),('U1',pin)}
if sat:
    assert netnodes['/RETURN_UP']=={('J1','5'),('JP1','2')}
    assert netnodes['/RETURN_DOWN']=={('J2','5'),('JP1','1')}
    assert netnodes['/TX_OUT']=={('R2','2'),('J2','3'),('JP1','3')}
    assert comps['JP1'].findtext('footprint')=='Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm'
    # Explicit solder states: verify the return includes exactly the chosen side.
    normal=netnodes['/RETURN_UP']|netnodes['/RETURN_DOWN']
    end=netnodes['/RETURN_UP']|netnodes['/TX_OUT']
    assert ('J2','5') in normal and ('R2','2') not in normal
    assert ('R2','2') in end and ('J2','5') not in end
erc=json.loads((VERIFY/(name+'-erc.json')).read_text())
erc_items=[v for s in erc['sheets'] for v in s['violations']]
if placement_reference:
    # TC2030 models reset as open drain; the M2003's documented internal
    # reset pull-up is not represented by the symbol's input pin type.
    assert len(erc_items)<=1
    assert all(v['type']=='pin_not_driven' and len(v['items'])==1 and 'U18 Pin 4' in v['items'][0]['description'] for v in erc_items),erc_items
else:assert not erc_items
drc=json.loads((VERIFY/(name+'-drc.json')).read_text());assert not drc['schematic_parity']
b=p.LoadBoard(str(HW/name/(name+'.kicad_pcb')));fps={f.GetReference():f for f in b.GetFootprints()};assert set(fps)==expected
rules_file=HW/'verification/routing-rules'/(name+'-changes.json')
if rules_file.exists():
    project=json.loads((HW/name/(name+'.kicad_pro')).read_text());settings=project['board']['design_settings'];rules=settings['rules']
    assert rules['min_clearance']==.1524 and rules['min_track_width']==.1524
    assert rules['min_through_hole_diameter']==.25 and rules['min_copper_edge_clearance']==.2
    assert settings['defaults']['zones']['min_clearance']==.1524
    assert all(c['clearance']==.1524 and c['via_drill']>=.25 for c in project['net_settings']['classes'])
    assert all(v['drill']==0 or v['drill']>=.25 for v in settings['via_dimensions'])
    for zone in b.Zones():
        if not zone.GetIsRuleArea():
            assert zone.GetPadConnection()==p.ZONE_CONNECTION_FULL
            assert abs(p.ToMM(zone.GetLocalClearance())-.1524)<1e-6
    for f in fps.values():
        assert f.GetLocalZoneConnection()==p.ZONE_CONNECTION_FULL
        for pad in f.Pads():
            if pad.GetAttribute()!=p.PAD_ATTRIB_NPTH:assert pad.GetLocalZoneConnection()==p.ZONE_CONNECTION_FULL
    assert all(p.ToMM(v.GetDrillValue())>=.25 for v in b.GetTracks() if isinstance(v,p.PCB_VIA))
assert b.GetCopperLayerCount()==4 and abs(p.ToMM(b.GetDesignSettings().GetBoardThickness())-.8)<1e-6
padcount=0
for ref,f in fps.items():
    comp=comps[ref]
    assert str(f.GetPath().AsString())==comp.find('sheetpath').attrib['tstamps']+comp.findtext('tstamps'),(ref,'Symbol association')
    if ref in harness_refs:
        assert {pad.GetNumber() for pad in f.Pads()}=={'1','2','3','4','5'}
        yy=[p.ToMM(pad.GetPosition().y) for pad in sorted(f.Pads(),key=lambda pad:pad.GetNumber())]
        assert all(abs(z-a-2)<1e-6 for a,z in zip(yy,yy[1:]))
    for pad in f.Pads():
        if not pad.GetNumber():continue
        for member in pad.GetNumber().split('/'):assert pad.GetNetname()==nodes.get((ref,member),''),(ref,member)
        padcount+=1
    if ref=='JP1' or (mounting and ref in ['H1','H2']):continue
    if placement_reference:
        x,y,angle=placement_reference['placements'][ref]
        assert abs(p.ToMM(f.GetPosition().x)-x)<1e-6 and abs(p.ToMM(f.GetPosition().y)-y)<1e-6,(ref,'Moved since placement checkpoint')
        assert abs(((f.GetOrientationDegrees()-angle+180)%360)-180)<1e-5
        if 'layers' in placement_reference:assert b.GetLayerName(f.GetLayer())==placement_reference['layers'][ref]
        if ref=='J3' and recovery_pads:
            assert f.GetLayer()==p.B_Cu
            assert all(not pad.IsOnLayer(p.B_Paste) and not pad.IsOnLayer(p.F_Paste) for pad in f.Pads())
        continue
    if not sat and ref in (USB_NEW|SYMMETRY_NEW):
        x,y=(USB_NEW|SYMMETRY_NEW)[ref]
        assert abs(p.ToMM(f.GetPosition().x)-x)<1e-6 and abs(p.ToMM(f.GetPosition().y)-y)<1e-6
        continue
    a=child(oldfps[reverse.get(ref,ref)],'at');dy=-1 if ref in harness_refs else 0
    assert abs(p.ToMM(f.GetPosition().x)-float(a[1]))<1e-6 and abs(p.ToMM(f.GetPosition().y)-float(a[2])-dy)<1e-6,(ref,'Moved')
    oldangle=float(a[3]) if len(a)>3 else 0;assert abs(((f.GetOrientationDegrees()-oldangle+180)%360)-180)<1e-5
poly=p.SHAPE_POLY_SET();assert b.GetBoardPolygonOutlines(poly,False);assert poly.OutlineCount()==1 and poly.HoleCount(0)==1
tracks=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)];vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
if sat:
    assert not drc['unconnected_items']
    if mounting:
        from check_mounting_layout import check as check_mounting
        check_mounting(name)
        assert all(v['type']=='courtyards_overlap' and any('H1' in i['description'] for i in v['items']) for v in drc['violations']),drc['violations']
    else:assert not drc['violations']
    assert all(t.GetLayer() in [p.F_Cu,p.B_Cu] and p.ToMM(t.GetWidth())>=.1524 for t in tracks)
    for t in tracks:
        a,z=t.GetStart(),t.GetEnd();dx,dy=abs(a.x-z.x),abs(a.y-z.y);assert min(dx,dy)<2000 or abs(dx-dy)<2000
    from plane_fanout import xy,point_rect
    for v in vias:
        assert p.ToMM(v.GetWidth(p.F_Cu))>=.5 and p.ToMM(v.GetDrillValue())>=(.25 if rules_file.exists() else .2)
        for f in fps.values():
            for pad in f.Pads():
                bb=pad.GetBoundingBox();box=tuple(p.ToMM(x) for x in [bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom()]);assert point_rect(xy(v.GetPosition()),box)>p.ToMM(v.GetDrillValue())/2,('Via in pad',f.GetReference(),pad.GetNumber())
    assert all(a.GetPosition().y==z.GetPosition().y for a,z in zip(sorted(fps['J1'].Pads(),key=lambda x:x.GetNumber()),sorted(fps['J2'].Pads(),key=lambda x:x.GetNumber())))
result={'status':'PASS','project':name,'components':len(comps),'preserved_components':len(oldfps),'preserved_component_values_and_footprints':True,'circuit_matches_baseline_except_return_selector_and_reset_removal':True,'reset_is_local_to_ice':True,'harness_wires':5,'placement_preserved':True,'electrical_pads_checked':padcount,'copper_layers':4,'thickness_mm':.8,'board_outlines':1,'actuator_cutouts':1,'erc_violations':0,'schematic_parity':0,'drc_violations':len(drc['violations']),'open_connections':len(drc['unconnected_items']),'segments':len(tracks),'vias':len(vias),'pcb_sha256':hashlib.sha256((HW/name/(name+'.kicad_pcb')).read_bytes()).hexdigest()}
if sat:result.update({'selector_modes_checked':['1-2 NORMAL','2-3 END'],'minimum_track_mm':min(p.ToMM(t.GetWidth()) for t in tracks),'via_in_pad':0,'inner_signal_tracks':0,'non_45_segments':0})
result['harness_pads']=5
result['preservation_exceptions']=['Five-pad harness footprint and centre shifted 1 mm; pins 1-3 stay fixed, VBAT/return move 2 mm','Main J100 and shared reset circuit removed; return selector added']
if not sat:
    assert all(v['severity']=='warning' for v in drc['violations'])
    result['preservation_exceptions'].append('USB CC controller and external input limiter removed; two 5.1k pull-downs added; VBUS directly feeds charger IN')
    result['passive_cc_checked']=True
    result['preservation_exceptions'].append('Main J3 and R48/R50/R52 removed; R62 terminates TS/MR, retaining SW3 and MCU thermistor input')
    result['pod_temperature_interface_checked']=True
    result['preservation_exceptions'].append('Main UART service bank J1 and Q4/R34/R35/R36 VBUS detector removed; charger input status read via I2C')
    result['uart_vbus_removal_checked']=True
if placement_reference:
    result['erc_violations']=len(erc_items)
    result['known_erc_note']='TC2030 open-drain reset and M2003 internal reset pull-up; no external pull-up fitted'
    result['placement_reference']='hardware/main/placement-reference.json'
    result['preservation_exceptions'].append('User removed C29/C30 and replaced main J102 with TC2030 J1; optimized placement with fixed edge anchors; restored U3 ground')
if recovery_pads:
    result['recovery_pads_checked']=True
    result['preservation_exceptions'].append('SW1/SW2 replaced by underside J3 EN/GND/BOOT recovery pads; ESP support placement refined; reset RC and boot pull-ups retained')
if rules_file.exists():result['routing_rules_checked']={'clearance_mm':.1524,'min_track_mm':.1524,'min_via_drill_mm':.25,'edge_clearance_mm':.2,'zone_clearance_mm':.1524,'plane_connections':'solid'}
if mounting:
    result.update({'status':'PRESERVATION PASS; MOUNTING CLEARANCE PENDING' if drc['violations'] else 'PASS','mounting_checked':check_mounting(name),'mounting_note':'H1 courtyard overlaps R3; user will rearrange as needed. No DRC exclusions added.'})
(VERIFY/(name+'-checks.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
