const fs = require('fs');
const path = require('path');
const sharp = require('C:/Users/mmsyl/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const dir = path.resolve(__dirname, '../hardware/preview/ring-revision');
(async () => {
  for (const file of fs.readdirSync(dir).filter(f => f.endsWith('.svg'))) {
    await sharp(path.join(dir,file), {density:130}).png().toFile(path.join(dir,file.replace(/\.svg$/,'.png')));
  }
  console.log('Rendered all ring revision schematic previews.');
})().catch(e => { console.error(e); process.exitCode=1; });
