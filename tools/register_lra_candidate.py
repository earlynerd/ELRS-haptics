"""Register a reviewable contact-only footprint and cache source provenance."""
from kicad_edit import *
import hashlib
fp=load(HW/'fp-lib-table')
if not any(uq(child(e,'name')[1])=='HapticBracelet' for e in children(fp,'lib')):
    fp.append(parse('(lib (name "HapticBracelet") (type "KiCad") (uri "${KIPRJMOD}/HapticBracelet.pretty") (options "") (descr "Project-specific draft footprints"))'))
save(HW/'fp-lib-table',fp)
p=HW/'datasheets/VLV041235L.pdf';m=HW/'datasheets/manifest.json';data=json.loads(m.read_text())
data['parts']['VLV041235L']={'file':p.name,'datasheet_url':'https://www.vybronics.com/wp-content/uploads/datasheet-files/Vybronics-VLV041235L-datasheet.pdf','manufacturer':'Vybronics','status':'ok','retrieved':'2026-09-12','revision':'A/2','sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size_bytes':p.stat().st_size,'notes':'Candidate. Page 10 contact geometry; PCB lands are a draft engineering allowance, not a vendor footprint.'}
m.write_text(json.dumps(data,indent=2)+'\n')
p=ROOT/'README.md';s=p.read_text()
line='\nThe proposed [VLV041235L actuator and draft flex contact footprint](docs/lra-candidate.md) are documented separately; the schematic actuator placeholders remain pending final selection.\n'
if 'docs/lra-candidate.md' not in s:p.write_text(s+line)
p=ROOT/'DECISIONS.md';s=p.read_text(encoding='utf-8')
if '## 2026-09-12 - VLV041235L flex contact candidate' not in s:
    p.write_text(s+'''\n## 2026-09-12 - VLV041235L flex contact candidate

- **Decision:** Evaluate the user-proposed VLV041235L with direct flex-to-PCB solder pads. Add a contact-only draft footprint with 1.8 mm pitch and separate body retention; leave schematic actuator placeholders until selection and fit are confirmed.
- **Why:** Vybronics explicitly supports direct PCB attachment of the double-sided flex contacts. Body placement remains a mechanical choice.
- **Supersedes:** No actuator candidate or contact geometry.
- **Affects:** hardware/HapticBracelet.pretty and docs/lra-candidate.md. S-821AAAI protector sourcing remains unresolved; other suffixes are not threshold-equivalent substitutes.
''',encoding='utf-8')
print('Registered draft contact footprint and cached datasheet. Schematic circuit unchanged.')
