const fs = require('fs');
const sharp = require('C:/Users/mmsyl/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const base = 'hardware/verification/pod-faces/';
(async () => {
  for (const [name, x, y] of [['main', 31.5, 32.6], ['satellite', 99.5, 88.5]]) {
    let svg = fs.readFileSync(base + name + '.svg', 'utf8');
    svg = svg.replace(/width="[^"]+"/, 'width="600"')
      .replace(/height="[^"]+"/, 'height="1250"')
      .replace(/viewBox="[^"]+"/, `viewBox="${x} ${y} 24 50"`);
    await sharp(Buffer.from(svg)).flatten({background: '#ffffff'}).png().toFile(base + name + '.png');
  }
  const lower = await sharp(base + 'satellite.png').resize(432, 900).toBuffer();
  const upper = await sharp(base + 'main.png').resize(432, 900).toBuffer();
  const labels = Buffer.from(`<svg width="1000" height="1050">
    <rect width="1000" height="1050" fill="white"/>
    <g font-family="Arial" fill="#253349">
    <text x="45" y="32" font-size="23">20 × 46 mm PCB faces · four M1.6 corner mounts</text>
    <text x="45" y="65" font-size="17">Universal lower board — solderable standoff lands</text>
    <text x="520" y="65" font-size="17">Controller upper plate — screw clearance holes</text>
    <text x="45" y="995" font-size="17">Blue: TPU contact boundary and Ø4.6 mm corner relief</text>
    <text x="45" y="1022" font-size="17">Mount centres 2.75 mm from edges · Standoffs pass through the TPU band</text>
    </g></svg>`);
  await sharp(labels).composite([{input: lower, left: 45, top: 80}, {input: upper, left: 520, top: 80}])
    .png().toFile(base + 'overview.png');
})().catch(e => { console.error(e); process.exit(1); });
