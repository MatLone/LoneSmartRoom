// NODE_OPTIONS loads before Electron's built-in modules exist. Attach the test
// only when Electron is about to load the actual application entry point.
'use strict';
const Module=require('node:module'),path=require('node:path');
const entry=path.resolve(__dirname,'../apps/windows-ui/main.cjs').replaceAll('\\','/').toLowerCase();
const original=Module._load;
Module._load=function(request,parent,isMain){
  if(typeof request==='string'&&request.replaceAll('\\','/').toLowerCase()===entry){
    Module._load=original;require('./electron-desktop-native.cjs');
  }
  return original.call(this,request,parent,isMain);
};
