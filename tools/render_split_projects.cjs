const fs=require('fs');
const sharp=require('C:/Users/mmsyl/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const out='hardware/verification/project-split/';
(async()=>{
  for (const name of ['main-front','front','back','ground','power']) {
    let svg=fs.readFileSync(out+name+'.svg','utf8');
    const [x,y,w,h]=name==='main-front'?[34.4,39.4,22.2,57.2]:[102.4,95.4,18.2,36.2];
    svg=svg.replace(/width="[^"]+" height="[^"]+" viewBox="[^"]+"/,`width="${w*25}" height="${h*25}" viewBox="${x} ${y} ${w} ${h}"`);
    svg=svg.replace(/(<desc>.*?<\/desc>)/,`$1<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="#10161f"/>`);
    fs.writeFileSync(out+name+'-crop.svg',svg);
    await sharp(Buffer.from(svg)).resize({width:name==='main-front'?650:650}).png().toFile(out+name+'.png');
  }
  const labels=['F.Cu - components / signals','B.Cu - signals','In1.Cu - GND','In2.Cu - +3V3_POD / VBAT'];
  const names=['front','back','ground','power'];
  const items=[];
  for(let i=0;i<4;i++) {
    const buf=await sharp(out+names[i]+'.png').resize({width:420}).png().toBuffer();
    items.push({input:buf,left:20+i*440,top:90});
  }
  const head=`<svg width="1780" height="90"><rect width="1780" height="90" fill="#10161f"/><text x="20" y="30" font-size="22" font-family="sans-serif" fill="white">Universal satellite - JP1 selects NORMAL / END</text>${labels.map((s,i)=>`<text x="${20+i*440}" y="66" font-size="17" font-family="sans-serif" fill="#cbd5e1">${s}</text>`).join('')}</svg>`;
  items.push({input:Buffer.from(head),left:0,top:0});
  await sharp({create:{width:1780,height:945,channels:4,background:'#10161f'}}).composite(items).png().toFile(out+'layers.png');
})();
