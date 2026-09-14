const fs=require('fs');
const sharp=require('C:/Users/mmsyl/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const out='hardware/verification/routing-v08/';
(async()=>{
  for (const name of ['overview','front','back','ground','power']) {
    let svg=fs.readFileSync(out+name+'.svg','utf8');
    const [x,y,w,h]=name==='overview'?[32,32,148,103]:[102.4,95.4,18.2,36.2];
    svg=svg.replace(/width="[^"]+" height="[^"]+" viewBox="[^"]+"/,`width="${w*25}" height="${h*25}" viewBox="${x} ${y} ${w} ${h}"`);
    svg=svg.replace(/(<desc>.*?<\/desc>)/,`$1<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="#10161f"/>`);
    fs.writeFileSync(out+name+'-crop.svg',svg);
    await sharp(Buffer.from(svg)).resize({width:name==='overview'?2000:650}).png().toFile(out+name+'.png');
  }
  const labels=['F.Cu - components / signals','B.Cu - signals','In1.Cu - GND','In2.Cu - POD_3V3 / VBAT'];
  const names=['front','back','ground','power'];
  const items=[];
  for(let i=0;i<4;i++) {
    const buf=await sharp(out+names[i]+'.png').resize({width:420}).png().toBuffer();
    items.push({input:buf,left:20+i*440,top:90});
  }
  const head=`<svg width="1780" height="90"><rect width="1780" height="90" fill="#10161f"/><text x="20" y="30" font-size="22" font-family="sans-serif" fill="white">Satellite pod 6 - revision 0.8</text>${labels.map((s,i)=>`<text x="${20+i*440}" y="66" font-size="17" font-family="sans-serif" fill="#cbd5e1">${s}</text>`).join('')}</svg>`;
  items.push({input:Buffer.from(head),left:0,top:0});
  await sharp({create:{width:1780,height:945,channels:4,background:'#10161f'}}).composite(items).png().toFile(out+'layers.png');
})();
