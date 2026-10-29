'use strict';
// Same version/runtime as the reviewed dev.9; separate feature candidate, never overwrite r12.
const base=require('./electron-builder.development.cjs');
module.exports={...base,directories:{...base.directories,output:'../../.cache/artifacts/windows/desktop-dev9-openrgb-candidate-r2'},
 nsis:{...base.nsis,artifactName:'Lone-Smart-Room-${version}-x64-OpenRGB-Candidate-Setup.${ext}'},
 portable:{...base.portable,artifactName:'Lone-Smart-Room-${version}-x64-OpenRGB-Candidate-Portable.${ext}'}};
