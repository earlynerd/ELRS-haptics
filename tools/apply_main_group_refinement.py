"""Apply only reviewed moved footprints, guarded against concurrent edits."""
from pathlib import Path
import re,json,hashlib,shutil,math
from kicad_edit import parse,children,child,uq
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];HW=ROOT/'hardware';OUT=HW/'verification/main-group-refinement'
source=HW/'main/main.kicad_pcb';before=source.read_text()
assert hashlib.sha256(source.read_bytes()).hexdigest()==(OUT/'input-sha256.txt').read_text(),'User board changed; rebase candidate'
moves=json.loads((OUT/'moves.json').read_text())
def blocks(s):
 result={}
 for m in re.finditer(r'\(footprint "',s):
  depth=0;quoted=False;esc=False
  for end in range(m.start(),len(s)):
   c=s[end]
   if quoted:
    if esc:esc=False
    elif c=='\\':esc=True
    elif c=='"':quoted=False
   elif c=='"':quoted=True
   elif c=='(':depth+=1
   elif c==')':
    depth-=1
    if depth==0:break
  block=s[m.start():end+1];ref=re.search(r'\(property "Reference" "([^"]+)"',block)[1]
  result[ref]=(m.start(),end+1,block)
 return result
old=blocks(before);new=blocks((OUT/'main.kicad_pcb').read_text())
after=before
for ref in sorted(moves,key=lambda r:old[r][0],reverse=True):
 start,end,_=old[ref]
 after=after[:start]+new[ref][2].replace('${KIPRJMOD}/../../','${KIPRJMOD}/../')+after[end:]
def unedited(tree):
 return [x for x in tree if not(isinstance(x,list) and x[0]=='footprint' and any(uq(z[1])=='Reference' and uq(z[2]) in moves for z in children(x,'property')))]
assert unedited(parse(before))==unedited(parse(after))
def circuit(tree):
 result={}
 for f in children(tree,'footprint'):
  props={uq(z[1]):uq(z[2]) for z in children(f,'property')}
  pads=sorted((uq(z[1]),tuple(child(z,'net')[1:]) if children(z,'net') else ()) for z in children(f,'pad'))
  result[props['Reference']]=(f[1],props['Value'],child(f,'uuid'),child(f,'path') if children(f,'path') else None,pads)
 return result
assert circuit(parse(before))==circuit(parse(after))
backup=HW/'backups/pre-main-group-refinement-20260917';backup.mkdir(exist_ok=False)
shutil.copy2(source,backup/source.name)
source.write_text(after)
b=p.LoadBoard(str(OUT/'input.kicad_pcb'));a=p.LoadBoard(str(source))
bf={f.GetReference():f for f in b.GetFootprints()};af={f.GetReference():f for f in a.GetFootprints()}
def dist(fs,r,pin,s,q):
 def pos(ref,num):return next(x.GetPosition() for x in fs[ref].Pads() if x.GetNumber()==num)
 v=pos(r,pin);w=pos(s,q);return math.hypot(p.ToMM(v.x-w.x),p.ToMM(v.y-w.y))
pairs=[('R5','2','U1','23'),('R4','2','U1','22'),('C2','1','U1','3'),('R24','2','U1','17'),('R25','2','U1','18'),('R42','1','U1','25'),('R51','2','D1','3'),('R45','1','U26','3'),('C42','1','U26','4'),('U14','1','J2','A6'),('U14','2','J2','B7')]
report={'untouched_items_preserved':True,'circuit_identity_and_pad_nets_preserved':True,'moved':moves,'distances_mm':{'-'.join(pair):{'before':round(dist(bf,*pair),3),'after':round(dist(af,*pair),3)} for pair in pairs}}
(OUT/'applied-checks.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report['distances_mm'],indent=2))
