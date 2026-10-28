'use strict';
// Default deny. Only the primary local window can ask for an audio-only, timed consent.
function createMediaPermissions({trusted,ask,now=Date.now}={}){
 const leases=new Map();
 function check(contents,permission,_origin,details){return permission==='media'&&details?.isMainFrame===true&&details.mediaType==='audio'&&trusted(contents)&&(leases.get(contents.id)||0)>now();}
 async function request(contents,permission,callback,details){
  if(permission!=='media'||!trusted(contents)||details?.isMainFrame!==true||!Array.isArray(details.mediaTypes)||details.mediaTypes.length!==1||details.mediaTypes[0]!=='audio'){callback(false);return;}
  try{if(await ask()){leases.set(contents.id,now()+10000);callback(true);}else callback(false);}catch{callback(false);}
 }
 return Object.freeze({check,request,clear:()=>leases.clear()});
}
module.exports={createMediaPermissions};
