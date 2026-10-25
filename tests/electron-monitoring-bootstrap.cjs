'use strict';
// Development instrumentation only; never packaged. Loads actual application main/preload.
const Module=require('node:module'),path=require('node:path');
const entry=path.resolve(__dirname,'../apps/windows-ui/main.cjs').replaceAll('\\','/').toLowerCase(),load=Module._load;
Module._load=function(request,parent,isMain){
  if(typeof request==='string'&&request.replaceAll('\\','/').toLowerCase()===entry){Module._load=load;require('./electron-monitoring-native.cjs');}
  return load.call(this,request,parent,isMain);
};
