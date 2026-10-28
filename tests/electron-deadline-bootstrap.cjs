'use strict';
const Module=require('node:module'),path=require('node:path'),original=Module._load;
const entry=path.resolve(__dirname,'../apps/windows-ui/main.cjs').replaceAll('\\','/').toLowerCase();
Module._load=function(request,parent,isMain){
 if(typeof request==='string'&&request.replaceAll('\\','/').toLowerCase()===entry){Module._load=original;require('./electron-deadline-native.cjs');}
 return original.call(this,request,parent,isMain);
};
