'use strict';
const Module=require('node:module'),path=require('node:path'),load=Module._load;
const entry=path.resolve(__dirname,'../apps/windows-ui/main.cjs').replaceAll('\\','/').toLowerCase();
Module._load=function(request,parent,isMain){
 if(typeof request==='string'&&request.replaceAll('\\','/').toLowerCase()===entry){Module._load=load;require('./electron-focused-native.cjs');}
 return load.call(this,request,parent,isMain);
};
