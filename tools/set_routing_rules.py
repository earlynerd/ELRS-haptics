"""Apply the agreed fabrication/routing constraints to one active PCBA master."""
import sys,json,shutil,datetime
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];name=sys.argv[1];assert name in ['main','satellite']
base=ROOT/'hardware'/name/name
backup=ROOT/'hardware/backups/rules-6mil-025mm-20260913'/name
if '--resume' not in sys.argv:
    backup.mkdir(parents=True,exist_ok=False)
    for ext in ['.kicad_pro','.kicad_pcb']:
        shutil.copy2(base.with_suffix(ext),backup/(name+ext))
else:assert backup.exists()
pro=base.with_suffix('.kicad_pro');data=json.loads(pro.read_text());ds=data['board']['design_settings'];rules=ds['rules']
rules.update(min_clearance=.1524,min_track_width=.1524,min_copper_edge_clearance=.2,min_through_hole_diameter=.25,min_microvia_drill=.25,min_microvia_diameter=.5)
ds['defaults']['zones']['min_clearance']=.1524
ds['track_widths']=sorted({v for v in ds['track_widths'] if v==0 or v>=.1524}|{.1524})
for v in ds['via_dimensions']:
    if v['drill'] or v['diameter']:
        v['drill']=max(.25,v['drill']);v['diameter']=max(.5 if v['drill']<=.25 else .6,v['diameter'],v['drill']+2*rules['min_via_annular_width'])
ds['via_dimensions']=list({(v['diameter'],v['drill']):v for v in ds['via_dimensions']}.values())
for c in data['net_settings']['classes']:
    c['clearance']=.1524;c['track_width']=max(.1524,c['track_width']);c['via_drill']=max(.25,c['via_drill'])
    c['microvia_drill']=max(.25,c['microvia_drill']);c['microvia_diameter']=max(.5,c['microvia_diameter'])
pro.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
b=p.LoadBoard(str(base.with_suffix('.kicad_pcb')))
settings=b.GetDesignSettings();defaults=settings.GetDefaultZoneSettings();defaults.m_ZoneClearance=p.FromMM(.1524);defaults.SetPadConnection(p.ZONE_CONNECTION_FULL);settings.SetDefaultZoneSettings(defaults)
changed=[]
for v in b.GetTracks():
    if isinstance(v,p.PCB_VIA) and p.ToMM(v.GetDrillValue())<.25:
        changed.append(str(v.m_Uuid.AsString()));v.SetDrill(p.FromMM(.25))
for z in b.Zones():
    if not z.GetIsRuleArea():z.SetLocalClearance(p.FromMM(.1524));z.SetPadConnection(p.ZONE_CONNECTION_FULL)
for f in b.GetFootprints():
    # Explicit solid footprint override also covers newly drawn planes.
    f.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL)
    if (f.GetLocalClearance() or 0)>0:f.SetLocalClearance(p.FromMM(.1524))
    for pad in f.Pads():
        if pad.GetAttribute()!=p.PAD_ATTRIB_NPTH:pad.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL)
        if (pad.GetLocalClearance() or 0)>0:pad.SetLocalClearance(p.FromMM(.1524))
filler=p.ZONE_FILLER(b);filler.Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(base.with_suffix('.kicad_pcb')),b)
out=ROOT/'hardware/verification/routing-rules';out.mkdir(exist_ok=True)
(out/(name+'-changes.json')).write_text(json.dumps({'project':name,'clearance_mm':.1524,'min_track_mm':.1524,'min_via_drill_mm':.25,'edge_clearance_mm':.2,'zone_connection':'solid','zone_clearance_mm':.1524,'enlarged_via_count':len(changed),'enlarged_via_uuids':changed},indent=2)+'\n')
print(name,'updated;',len(changed),'via drills enlarged;',len(list(b.Zones())),'zones refilled')
