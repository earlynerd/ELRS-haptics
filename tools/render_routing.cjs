const sharp = require('C:/Users/mmsyl/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const dir = 'hardware/verification/routing/';
(async () => {
  for (const name of ['overview','pod-1-front','pod-1-back','pod-1-ground','pod-7-power']) {
    await sharp(dir+name+'.svg', {density:300}).trim().resize({width:name==='overview'?1900:650})
      .flatten({background:'#142127'}).png().toFile(dir+name+'.png');
  }
})();
