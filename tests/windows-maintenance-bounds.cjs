'use strict';
// Fake filesystem only: never enumerate or remove system/user temp files.
const assert=require('node:assert/strict'),path=require('node:path');
const {createInspector}=require('../apps/windows-ui/maintenance-inspector.cjs');
const root=path.resolve(__dirname,'fixture-virtual-root');
let checks=0;
function inspect(io){return createInspector({ownCache:root,io}).inspect('own');}
const missing=inspect({lstatSync(){throw Object.assign(Error(),{code:'ENOENT'});}});
assert.equal(missing.state,'preview');assert.equal(missing.root_absent,true);assert.equal(missing.denied,0);checks+=3;
const denied=inspect({lstatSync(){throw Object.assign(Error(),{code:'EACCES'});}});
assert.equal(denied.state,'unavailable');assert.equal(denied.denied,1);assert.equal(denied.root_absent,false);checks+=3;
const dir={isDirectory:()=>true,isSymbolicLink:()=>false,nlink:1};
let entryReads=0;
const bounded=inspect({
 lstatSync(file){if(file!==root)entryReads++;return dir;},
 readdirSync(){return Array.from({length:1001},(_,i)=>'folder-'+i);}
});
assert.equal(bounded.visited,2000);assert.equal(bounded.truncated,true);
// Each directory is rechecked on descent; entries, not metadata syscalls, are capped.
assert(entryReads<=2*bounded.visited);assert.equal(bounded.execution_enabled,false);checks+=4;
// Metadata disappearing below a present root is an error, not an absent root.
let first=true;
const race=inspect({lstatSync(){if(first){first=false;return dir;}throw Object.assign(Error(),{code:'ENOENT'});},readdirSync:()=>['child.tmp']});
assert.equal(race.root_absent,false);assert.equal(race.denied,1);checks+=2;
console.log(JSON.stringify({ok:true,checks,realFilesystemTraversal:false,realCleanup:false}));
