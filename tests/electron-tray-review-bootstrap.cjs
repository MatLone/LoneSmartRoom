'use strict';
// Optional manual review instrumentation. Never packaged or loaded by production.
const Module=require('node:module'),path=require('node:path');
const entry=path.resolve(__dirname,'../apps/windows-ui/main.cjs').replaceAll('\\','/').toLowerCase();
const load=Module._load;
Module._load=function(request,parent,isMain){
  if(typeof request==='string'&&request.replaceAll('\\','/').toLowerCase()===entry){
    Module._load=load;require('./electron-tray-review.cjs');
  }
  return load.call(this,request,parent,isMain);
};
