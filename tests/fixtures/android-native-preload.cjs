// Test-only fake bridges. Never imported by production HTML, Android or Electron.
const {contextBridge}=require('electron');
const calls=[];
const record=name=>(...args)=>{calls.push({name,args});};
contextBridge.exposeInMainWorld('LoneAppInfo',{getVersionName:()=> '2.0.0-fixture'});
if(!process.argv.includes('--fixture-no-native')){
  contextBridge.exposeInMainWorld('LoneAndroid',{sendWake:record('sendWake')});
  contextBridge.exposeInMainWorld('LoneAgent',{
    refreshStatus:record('refreshStatus'),showPairing:record('showPairing'),
    refreshAppPermissions:record('refreshAppPermissions'),refreshLaunchResult:record('refreshLaunchResult'),
    requestAppLaunch:record('requestAppLaunch')
  });
}
contextBridge.exposeInMainWorld('__fixture',{snapshot:()=>JSON.parse(JSON.stringify(calls)),reset:()=>{calls.length=0;}});
