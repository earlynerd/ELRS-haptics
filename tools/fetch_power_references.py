"""Cache primary-source PDFs and hashes for the USB/power design."""
from pathlib import Path
import hashlib,json,urllib.request
base=Path(__file__).resolve().parents[1]/'hardware/datasheets'
base.mkdir(exist_ok=True)
sources={n:f'https://www.ti.com/lit/ds/symlink/{n.lower()}.pdf' for n in ['BQ25186','TPS63802','TPS2553','TS5A3159','TUSB320LAI','TPD2EUSB30']}
manifest={}
for name,url in sources.items():
    path=base/f'{name}.pdf'
    if not path.exists():
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=30) as r: data=r.read()
        assert data.startswith(b'%PDF'), name
        path.write_bytes(data)
    data=path.read_bytes()
    manifest[name]={'file':path.name,'datasheet_url':url,'manufacturer':'Texas Instruments','status':'ok','sha256':hashlib.sha256(data).hexdigest(),'size_bytes':len(data)}
(base/'manifest.json').write_text(json.dumps({'retrieved':'2026-09-11','parts':manifest},indent=2)+'\n')
print('Cached',len(manifest),'TI datasheets.')
