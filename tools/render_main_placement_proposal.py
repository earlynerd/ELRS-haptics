from pathlib import Path
out=Path('hardware/verification/routing-v09')
parts=['''<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="980" viewBox="0 0 1160 980">
<rect width="1160" height="980" fill="#111923"/>
<style>text{font-family:Arial,sans-serif;fill:#e6edf3}.small{font-size:16px}.body{font-size:20px}.title{font-size:29px;font-weight:bold}</style>
<text x="38" y="44" class="title">Main pod: proposed functional groups</text>
<text x="38" y="76" class="small">Existing outline and cutout · block allocation only · native main placement unchanged</text>
<g transform="translate(66,112) scale(12)">
<path d="M .7 5.1 H20.3 L21 5.8 V60.3 L20.3 61 H.7 L0 60.3 V5.8 Z" fill="#202b37" stroke="#b9c6d3" stroke-width=".12"/>
<path d="M6.5 23 H12.5 L13 23.5 V37.5 L12.5 38 H6.5 L6 37.5 V23.5 Z" fill="#111923" stroke="#aab8c6" stroke-width=".12"/>
<rect x="3.9" y="-.3" width="13.2" height="5.4" fill="#ca776f" fill-opacity=".25" stroke="#ee9186" stroke-dasharray=".4 .3" stroke-width=".12"/>
<rect x="3.9" y="5.1" width="13.2" height="11.4" fill="#46799f" stroke="#72b6df" stroke-width=".12"/>
<text x="10.5" y="2.7" text-anchor="middle" font-size="1.15">ANTENNA</text>
<text x="10.5" y="11" text-anchor="middle" font-size="1.45">ESP32</text>
<text x="9.5" y="30.8" text-anchor="middle" font-size="1.0" transform="rotate(-90 9.5 30.8)">LRA opening</text>
<rect x=".4" y="24" width="1.9" height="12" fill="#7b8796"/>
<rect x="18.5" y="22" width="1.9" height="10" fill="#7b8796"/>
<path d="M10.5 54.4 L14 50.9 V20.1 L10 16.1" fill="none" stroke="#76d4e8" stroke-width=".48" stroke-dasharray=".65 .42"/>
''']
def block(x,y,w,h,color,num):
 parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx=".3" fill="{color}" fill-opacity=".7" stroke="{color}" stroke-width=".14"/><text x="{x+w/2}" y="{y+h/2+.65}" text-anchor="middle" font-size="1.8" font-weight="bold">{num}</text>')
block(1,47.7,6.8,6.1,'#ce9742','1')
block(8.7,47.7,4.2,5.8,'#ba7462','2')
block(15.3,51,5,4.5,'#7785ba','3')
block(6,54.1,8.5,1.6,'#7785ba','')
block(3.7,39.2,9,7.5,'#75a46d','4')
block(15.1,32.4,3.0,6.1,'#75a46d','4')
block(.8,17.4,6.4,5,'#b68cba','5')
block(15.8,44.5,4.5,5.4,'#708899','')
parts.append('''<rect x="6" y="55.7" width="9" height="5.5" fill="#48576a" stroke="#b9c6d3" stroke-width=".12"/>
<text x="10.5" y="59.1" text-anchor="middle" font-size="1.4">USB-C</text>
<circle cx="18.6" cy="58.5" r=".9" fill="#89b6be"/>
<text x="10.5" y="64.5" text-anchor="middle" font-size="1.3">21 mm × 61 mm envelope</text></g>''')
rows=[('1','#ce9742','Regulator + inductor + capacitors','U12 / L1 / C37–C39 / R40–R41','Short switching loops; divider on the quiet side.'),('2','#ba7462','Charger + local capacitors','U11 / C34–C36 / charge-enable parts','Keep IN, SYS and BAT paths local.'),('3','#7785ba','USB entry and input-current control','U13–U17 / associated passives','ESD at the contacts; current-limit parts together.'),('4','#75a46d','Local MCU and haptic driver','U18 below cutout; U3 beside the LRA tail','Use the satellite grouping as a starting point.'),('5','#b68cba','ESP support and pod power switch','Decoupling / U26 / slew and discharge parts','Finish placement after the larger groups fit.')]
for i,(num,color,title,refs,note) in enumerate(rows):
 y=154+i*122
 parts.append(f'<circle cx="396" cy="{y-6}" r="19" fill="{color}"/><text x="396" y="{y+1}" text-anchor="middle" font-size="21" font-weight="bold">{num}</text><text x="432" y="{y}" class="body" font-weight="bold">{title}</text><text x="432" y="{y+31}" class="small">{refs}</text><text x="432" y="{y+58}" class="small">{note}</text>')
parts.append('''<path d="M380 790 H422" stroke="#76d4e8" stroke-width="5" stroke-dasharray="9 6"/>
<text x="432" y="796" class="body">Reserve a USB corridor before filling gaps</text>
<text x="432" y="826" class="small">Keep BOOT/RESET access clear; wake/ship and RGB stay accessible.</text>
<text x="380" y="886" class="small">Blocks are not fitted courtyards or a routing feasibility check.</text>
<text x="380" y="916" class="small">Next: place each group with its actual footprints and check spacing.</text></svg>''')
(out/'main-placement-proposal.svg').write_text(''.join(parts),encoding='utf8')
