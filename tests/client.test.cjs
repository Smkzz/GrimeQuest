'use strict';
const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const vm=require('node:vm');
function harness(extra={}) {const NativeDate=Date;class FixtureDate extends NativeDate{constructor(...a){super(...(a.length?a:['2026-10-06T12:00:00Z']));}static now(){return new NativeDate('2026-10-06T12:00:00Z').getTime();}}const c={console,Date:FixtureDate,...extra};if(c.document && !c.document.getElementById)c.document.getElementById=()=>null;vm.createContext(c);vm.runInContext(fs.readFileSync('web/app.js','utf8'),c);return c.GQ;}
const G=harness();
const product='method-kitchen-clementine-uk-828';
const analysis={object_name:'Tiled splashback',surface:'glazed_ceramic',soil:'grease',visible_soil:true,image_quality:'usable',material_certainty:'tentative',hazards:['none'],target_box:{x:0.1,y:0.1,width:0.8,height:0.8}};
function quest(mode='practice'){return {id:'q1',mode,phase:'identified',name:'Grease gremlin',room:'Kitchen',surface:'glazed_ceramic',soil:'grease',before:'synthetic',analysis};}
function cleaning(mode='practice'){return G.transition(G.transition(G.transition(quest(mode),{type:'confirm',surface:'glazed_ceramic',soil:'grease'}),{type:'equip',productId:product}),{type:'start'});}
function result(status='clear',mode='practice'){return {encounter_id:'q1',status,xp:status==='clear'?300:0,reason:'Test evidence',provenance:mode==='practice'?'practice_fixture':'model_observation',...(mode==='live'?{receipt:'test-receipt-not-real-but-bounded'}:{})};}
for(const mode of ['practice','live'])test(`state machine full ${mode} flow and idempotent reward`,()=>{
  let q=cleaning(mode);q=G.transition(q,{type:'result',result:result('clear',mode),after:'other'});
  let s=G.recordResult(G.emptyStore(),q);s=G.recordResult(s,q);
  assert.equal(s.history.length,1);assert.equal(G.stats(s,mode).xp,300);
  assert.equal(G.stats(s,mode==='practice'?'live':'practice').xp,0);
});
for(const status of ['partial','unverifiable'])test(`retry ${status} without duplicate XP`,()=>{
 let q=G.transition(cleaning(),{type:'result',result:result(status),after:'other'});let s=G.recordResult(G.emptyStore(),q);
 assert.equal(G.stats(s,'practice').xp,0);q=G.transition(q,{type:'retry'});q=G.transition(q,{type:'result',result:result(),after:'new'});s=G.recordResult(s,q);
 assert.equal(s.history.length,1);assert.equal(G.stats(s,'practice').xp,300);
});
test('invalid sequence rejected',()=>{for(const ev of [{type:'start'},{type:'equip',productId:product},{type:'result',result:result(),after:'x'},{type:'retry'}])assert.throws(()=>G.transition(quest(),ev));});
test('clear cannot be retried',()=>assert.throws(()=>G.transition(G.transition(cleaning(),{type:'result',result:result(),after:'x'}),{type:'retry'})));
test('wrong quest result rejected',()=>assert.throws(()=>G.transition(cleaning(),{type:'result',result:{...result(),encounter_id:'other'},after:'x'})));
test('mode separation in both directions',()=>{
 assert.throws(()=>G.transition(cleaning('live'),{type:'result',result:result(),after:'x'}));
 assert.throws(()=>G.transition(cleaning(),{type:'result',result:result('clear','live'),after:'x'}));
 assert.throws(()=>G.recordResult(G.emptyStore(),{...cleaning(),phase:'result',result:result('clear','live')}));
});
test('live clear requires receipt',()=>{const r=result('clear','live');delete r.receipt;assert.throws(()=>G.transition(cleaning('live'),{type:'result',result:r,after:'x'}));});
test('model numeric XP is not trusted',()=>{
 let q=G.transition(cleaning(),{type:'result',result:{...result(),xp:999999},after:'x'});assert.equal(G.recordResult(G.emptyStore(),q).history[0].xp,300);
});
test('missing or unusable before photo rejected',()=>{for(const patch of [{visible_soil:false},{image_quality:'unusable'}])assert.throws(()=>G.transition({...quest(),analysis:{...analysis,...patch}},{type:'confirm',surface:'glazed_ceramic',soil:'grease'}));});
test('unknown product and known hazard cannot equip',()=>{
 const q=G.transition(quest(),{type:'confirm',surface:'glazed_ceramic',soil:'grease'});
 assert.throws(()=>G.transition(q,{type:'equip',productId:'unreviewed'}));
 assert.throws(()=>G.transition({...q,analysis:{...analysis,hazards:['heat']}},{type:'equip',productId:product}));
});
test('empty attestations do not vacuously pass',()=>assert.equal(G.matchProduct('glazed_ceramic','grease',product,{},['none'],'2026-10-06').code,'CONFIRMATIONS_REQUIRED'));
test('HTML escaping includes attributes',()=>assert.equal(G.escapeHTML('<img src=x onerror="alert(1)"> & \'x\''),'&lt;img src=x onerror=&quot;alert(1)&quot;&gt; &amp; &#39;x&#39;'));
test('prototype inherited names are not surfaces or soils',()=>{assert.equal(G.isSurface('__proto__'),false);assert.equal(G.isSoil('constructor'),false);});
test('valid store round trips',()=>assert.ok(G.safeStore(JSON.parse(JSON.stringify(G.emptyStore())))));
for(const bad of [null,[],{}, {version:2,history:[],inventory:[],active:null}, {version:1,history:[],inventory:[],active:'bad'}, {version:1,history:[null],inventory:[],active:null}])test(`bad store ${JSON.stringify(bad)}`,()=>assert.equal(G.safeStore(bad),null));
test('duplicate history and receiptless live clear rejected',()=>{
 const s=G.recordResult(G.emptyStore(),G.transition(cleaning(),{type:'result',result:result(),after:'x'}));s.history.push(s.history[0]);assert.equal(G.safeStore(s),null);
 s.history.pop();s.history[0].mode='live';assert.equal(G.safeStore(s),null);
});
test('invalid dates rejected',()=>{let s=G.recordResult(G.emptyStore(),G.transition(cleaning(),{type:'result',result:result(),after:'x'}));s.history[0].date='never';assert.equal(G.safeStore(s),null);});
test('bounded history and fixed level formula',()=>{
 let s=G.emptyStore();for(let i=0;i<203;i++){let q={...cleaning(),id:'q'+i};s=G.recordResult(s,G.transition(q,{type:'result',result:{...result(),encounter_id:q.id},after:'x'}));}
 assert.equal(s.history.length,200);assert.equal(G.stats(s,'practice').level,67);
});
test('analysis validation rejects omitted hazards or boxes',()=>{
 assert.equal(G.validateAnalysis(analysis),true);
 for(const patch of [{hazards:[]},{hazards:['fictional']},{target_box:null},{target_box:{x:0,y:0,width:2,height:1}},{material_certainty:'certain'},{object_name:'x'.repeat(241)}])assert.equal(G.validateAnalysis({...analysis,...patch}),false);
});
test('result validation checks reward and provenance',()=>{
 assert.equal(G.validateResult(result()),true);
 for(const patch of [{xp:Infinity},{xp:100},{receipt:'x'.repeat(15000)},{provenance:'magic'},{encounter_id:42}])assert.equal(G.validateResult({...result(),...patch}),false);
});
function storage(){const m=new Map();return {getItem:k=>m.get(k)??null,setItem:(k,v)=>m.set(k,String(v)),removeItem:k=>m.delete(k)};}
test('storage round trip and tab scoped access',()=>{const local=storage(),session=storage(),g=harness({localStorage:local,sessionStorage:session});assert.ok(g.saveStore(g.emptyStore()));assert.equal(g.readStore().version,1);g.setAccessCode('secret');assert.equal(g.getAccessCode(),'secret');assert.equal(local.getItem('grimequest.access'),null);});
test('corrupted original is not silently overwritten',()=>{const local=storage();local.setItem('grimequest.v1','not-json');const g=harness({localStorage:local});assert.equal(g.readStore().history.length,0);assert.ok(g.storageWarning);assert.equal(g.saveStore(g.emptyStore()),false);assert.equal(local.getItem('grimequest.v1'),'not-json');g.resetStore();assert.equal(g.storageWarning,'');assert.equal(local.getItem('grimequest.v1'),null);});
test('quota denied is visible',()=>{const g=harness({localStorage:{getItem:()=>null,setItem:()=>{throw Error('quota')},removeItem:()=>{}}});assert.equal(g.saveStore(g.emptyStore()),false);assert.match(g.storageWarning,/only in this tab/);});

test('native iPhone HEIC and HEIF input is normalized into JPEG',async()=>{
 const revoked=[],created=[];
 class ImageFixture {constructor(){this.width=320;this.height=240;}set src(v){this.srcValue=v;}async decode(){}}
 const canvas={width:0,height:0,getContext:()=>({fillRect(){},drawImage(){}}),toDataURL:(type,quality)=>{assert.equal(type,'image/jpeg');assert.equal(quality,0.85);return 'data:image/jpeg;base64,AA==';}};
 const g=harness({URL:{createObjectURL:()=>{created.push('blob:fixture');return 'blob:fixture';},revokeObjectURL:v=>revoked.push(v)},Image:ImageFixture,document:{getElementById:()=>null,createElement:tag=>{assert.equal(tag,'canvas');return canvas;}}});
 for(const [type,name] of [['image/heic','iPhone.HEIC'],['image/heif','iPhone.heif'],['','iPhone.HEIC']]){
   const result=await g.normalizePhoto({type,name,size:10000});
   assert.equal(result,'data:image/jpeg;base64,AA==');
 }
 assert.equal(created.length,3);assert.deepEqual(revoked,['blob:fixture','blob:fixture','blob:fixture']);
});
test('unsupported HEIC decoder returns JPEG fallback advice and releases blob',async()=>{
 const revoked=[];
 class Undecodable {set src(v){}async decode(){throw Error('unsupported codec');}}
 const g=harness({URL:{createObjectURL:()=> 'blob:unsupported',revokeObjectURL:v=>revoked.push(v)},Image:Undecodable});
 await assert.rejects(()=>g.normalizePhoto({type:'image/heic',name:'photo.heic',size:12345}),/Use Safari 17\+ or export the photo as JPEG/);
 assert.deepEqual(revoked,['blob:unsupported']);
 await assert.rejects(()=>g.normalizePhoto({type:'image/svg+xml',name:'malicious.svg',size:123}),/SVG is not supported/);
 await assert.rejects(()=>g.normalizePhoto({type:'image/heic',name:'raw-like.heic',size:101000000}),/over 100 MB/);
});
test('camera rejects insecure context',async()=>{const g=harness({window:{isSecureContext:false},navigator:{}});await assert.rejects(new g.Camera().start({isConnected:true}),/HTTPS/);});
test('camera stops tracks after late permission resolution',async()=>{
 let resolve,stopped=0;const g=harness({window:{isSecureContext:true},navigator:{mediaDevices:{getUserMedia:()=>new Promise(r=>resolve=r)}}});
 const c=new g.Camera(),pending=c.start({isConnected:true});c.stop();resolve({getTracks:()=>[{stop:()=>stopped++}]});await pending;assert.equal(stopped,1);
});
test('camera captures only after ready preview',()=>assert.throws(()=>new G.Camera().capture(),/not ready/));

test('service worker only handles allowlisted app shell requests',async()=>{
 const listeners={};const cacheNames=['other-app','grimequest-old'];let added=[],deleted=[],claimed=0,matches=0,skip=0,precacheReady=false;
 const context={URL,console,self:{location:{origin:'https://app.example'},clients:{claim:async()=>claimed++},skipWaiting:async()=>{assert.equal(precacheReady,true,'activation waits for full offline-shell precache');skip++;},addEventListener:(n,fn)=>listeners[n]=fn},caches:{open:async()=>({addAll:async paths=>{added=paths;precacheReady=true;},match:async()=>{matches++;return 'cached'}}),keys:async()=>cacheNames,delete:async k=>{deleted.push(k)}},fetch:()=>{throw Error('Unexpected network')}};
 vm.createContext(context);vm.runInContext(fs.readFileSync('web/sw.js','utf8'),context);
 let pending;listeners.install({waitUntil:p=>pending=p});await pending;assert.equal(skip,1);assert.ok(added.includes('/app.js'));
 assert.ok(added.includes('/update-client.js'));assert.ok(!added.some(p=>p.startsWith('/api/')));
 assert.ok(!added.some(p=>['/update.html','/update.js','/update.css'].includes(p)));
 listeners.message({data:{type:'GRIMEQUEST_ACTIVATE_UPDATE'},waitUntil:p=>pending=p});await pending;assert.equal(skip,2);
 listeners.activate({waitUntil:p=>pending=p});await pending;assert.deepEqual(deleted,['grimequest-old']);assert.equal(claimed,1);
 for(const [url,method] of [['https://app.example/api/health','GET'],['https://app.example/api/verify','POST'],['https://app.example/update.html','GET'],['https://app.example/update.js','GET'],['https://app.example/update.css','GET'],['https://evil.example/app.js','GET'],['https://app.example/app.js?private=1','GET'],['https://app.example/user-photo.jpg','GET']])listeners.fetch({request:{url,method},respondWith:()=>assert.fail('Private request cached')});
 listeners.fetch({request:{url:'https://app.example/app.js',method:'GET'},respondWith:p=>pending=p});assert.equal(await pending,'cached');assert.equal(matches,1);
});

test('native 48 MP phone photo over previous size caps is accepted and reduced to server dimensions',async()=>{
 const revoked=[],seen=[];
 class HugeImage {constructor(){this.width=8064;this.height=6048;}set src(v){}async decode(){}}
 const canvas={width:0,height:0,getContext:()=>({fillRect(){},drawImage(){}}),toDataURL:(mime,q)=>{
   assert.equal(mime,'image/jpeg');assert.equal(q,0.85);seen.push([canvas.width,canvas.height]);
   return 'data:image/jpeg;base64,AA==';
 }};
 const g=harness({URL:{createObjectURL:()=> 'blob:48mp',revokeObjectURL:url=>revoked.push(url)},
   Image:HugeImage,document:{createElement:()=>canvas}});
 const jpg=await g.normalizePhoto({type:'image/jpeg',name:'IMG_48MP.jpg',size:27000000});
 assert.equal(jpg,'data:image/jpeg;base64,AA==');
 assert.deepEqual(seen,[[1600,1200]]);
 assert.deepEqual(revoked,['blob:48mp']);
});

test('large phone portrait remains portrait when reduced',async()=>{
 const bounds=[];
 class TallImage {constructor(){this.width=6000;this.height=8000;}set src(v){}async decode(){}}
 const canvas={width:0,height:0,getContext:()=>({fillRect(){},drawImage(){}}),
   toDataURL:()=>{bounds.push([canvas.width,canvas.height]);return 'data:image/jpeg;base64,AA==';}};
 const g=harness({URL:{createObjectURL:()=> 'blob:portrait',revokeObjectURL:()=>{}},Image:TallImage,
   document:{createElement:()=>canvas}});
 await g.normalizePhoto({type:'image/heic',name:'portrait.heic',size:14000000});
 assert.deepEqual(bounds,[[1200,1600]]);
});

test('large noisy photo adjusts JPEG quality without rejecting the original resolution',async()=>{
 class HugeImage {constructor(){this.width=8000;this.height=6000;}set src(v){}async decode(){}}
 const calls=[];
 const tooLarge='data:image/jpeg;base64,'+'A'.repeat(2600000);
 const canvas={width:0,height:0,getContext:()=>({fillRect(){},drawImage(){}}),toDataURL:(_,q)=>{
   calls.push([canvas.width,canvas.height,q]);return q===0.85?tooLarge:'data:image/jpeg;base64,AA==';
 }};
 const g=harness({URL:{createObjectURL:()=> 'blob:noise',revokeObjectURL:()=>{}},Image:HugeImage,
   document:{createElement:()=>canvas}});
 assert.equal(await g.normalizePhoto({type:'image/jpeg',name:'complex.jpg',size:25000000}),'data:image/jpeg;base64,AA==');
 assert.deepEqual(calls,[[1600,1200,0.85],[1600,1200,0.72]]);
});

test('uncompressible image reduces canvas edge instead of rejecting full-resolution input',async()=>{
 class HugeImage {constructor(){this.width=8064;this.height=6048;}set src(v){}async decode(){}}
 const calls=[];
 const tooLarge='data:image/jpeg;base64,'+'A'.repeat(2600000);
 const canvas={width:0,height:0,getContext:()=>({fillRect(){},drawImage(){}}),toDataURL:(_,q)=>{
   calls.push([canvas.width,canvas.height,q]);
   return canvas.width===1600?tooLarge:'data:image/jpeg;base64,AA==';
 }};
 const g=harness({URL:{createObjectURL:()=> 'blob:noise',revokeObjectURL:()=>{}},Image:HugeImage,
   document:{createElement:()=>canvas}});
 const result=await g.normalizePhoto({type:'image/jpeg',name:'highly-textured.jpg',size:40000000});
 assert.equal(result,'data:image/jpeg;base64,AA==');
 assert.deepEqual(calls.map(v=>v[0]),[1600,1600,1600,1280]);
});

test('8+ MB source does not bypass supported file-type or minimum dimension checks',async()=>{
 class TinyImage {constructor(){this.width=60;this.height=60;}set src(v){}async decode(){}}
 let allocated=0,revoked=0;
 const g=harness({URL:{createObjectURL:()=>{allocated++;return 'blob:tiny';},revokeObjectURL:()=>{revoked++;}},
   Image:TinyImage});
 await assert.rejects(()=>g.normalizePhoto({type:'image/jpeg',name:'tiny.jpg',size:35000000}),/at least 64/);
 await assert.rejects(()=>g.normalizePhoto({type:'image/svg+xml',name:'vector.svg',size:35000000}),/SVG is not supported/);
 assert.equal(allocated,1);assert.equal(revoked,1);
});

test('large photo uses supported size-bounded bitmap decoding and promptly releases bitmap',async()=>{
 let closed=0,created=0;const sizes=[];
 const canvas={width:0,height:0,getContext:()=>({fillRect(){},drawImage(){}}),toDataURL:()=>{
  sizes.push([canvas.width,canvas.height]);return 'data:image/jpeg;base64,AA==';
 }};
 const g=harness({
  createImageBitmap:async(file,options)=>{assert.equal(file.size,25000000);assert.equal(options.resizeWidth,1600);assert.equal(options.resizeQuality,'high');
   return {width:1600,height:1200,close:()=>closed++};},
  URL:{createObjectURL:()=>{created++;return 'blob:should-not-happen';},revokeObjectURL:()=>{}},
  document:{createElement:()=>canvas}
 });
 assert.equal(await g.normalizePhoto({type:'image/jpeg',name:'large.jpg',size:25000000}),'data:image/jpeg;base64,AA==');
 assert.equal(closed,1);assert.equal(created,0);assert.deepEqual(sizes,[[1600,1200]]);
});

test('bitmap decoder rejecting HEIC falls back to native Safari image-element decoding',async()=>{
 let bitmapCalls=0,revoked=0;
 class HeicImage{constructor(){this.width=6048;this.height=8064;}set src(v){}async decode(){}}
 const canvas={width:0,height:0,getContext:()=>({fillRect(){},drawImage(){}}),toDataURL:()=> 'data:image/jpeg;base64,AA=='};
 const g=harness({
  createImageBitmap:async()=>{bitmapCalls++;throw Error('codec unavailable here');},Image:HeicImage,
  URL:{createObjectURL:()=> 'blob:heic',revokeObjectURL:()=>revoked++},
  document:{createElement:()=>canvas}
 });
 assert.equal(await g.normalizePhoto({type:'image/heic',name:'portrait.heic',size:17000000}),'data:image/jpeg;base64,AA==');
 assert.equal(bitmapCalls,1);assert.equal(revoked,1);
 assert.equal(canvas.width,1200);assert.equal(canvas.height,1600);
});

test('app update check never reloads mid-quest and offers an explicit refresh',async()=>{
 const nodes=Object.fromEntries(['app-update-banner','app-update-now','app-update-later'].map(id=>[id,{hidden:true,events:{},addEventListener(k,fn){this.events[k]=fn;}}]));
 const listeners={};let registers=0,checks=0,navigations=[];
 const registration={waiting:null,events:{},addEventListener(k,fn){this.events[k]=fn;},update:async()=>{checks++;}};
 const ctx={console,document:{getElementById:id=>nodes[id]},navigator:{serviceWorker:{controller:{},register:async(script,options)=>{assert.equal(script,'/sw.js');assert.equal(options.updateViaCache,'none');registers++;return registration;},addEventListener(k,fn){listeners[k]=fn;}}},location:{protocol:'https:'},window:{isSecureContext:true,location:{assign:u=>navigations.push(u)}}};
 vm.runInNewContext(fs.readFileSync('web/update-client.js','utf8'),ctx);
 for(let i=0;i<5&&checks===0;i++)await new Promise(r=>setImmediate(r));
 assert.equal(registers,1);assert.equal(checks,1);
 assert.equal(nodes['app-update-banner'].hidden,true);
 listeners.controllerchange();
 assert.equal(nodes['app-update-banner'].hidden,false);
 assert.deepEqual(navigations,[],'worker takeover must never force a quest reload');
 nodes['app-update-later'].events.click();
 assert.equal(nodes['app-update-banner'].hidden,true);
 listeners.controllerchange();assert.equal(nodes['app-update-banner'].hidden,true);
 nodes['app-update-now'].events.click();assert.deepEqual(navigations,['/update.html']);
});

test('stale shell recovery deletes only GrimeQuest caches, preserves saved data, and bypasses old worker URL filter',async()=>{
 const nodes={'refresh-now':{disabled:false,events:{},addEventListener(k,fn){this.events[k]=fn;}},'refresh-status':{textContent:''}};
 const removed=[],deleted=[],navigations=[],locals=new Map([['grimequest.v1','saved inventory'],['notes','personal']]);
 const ctx={console,URL,navigator:{onLine:true,serviceWorker:{getRegistration:async path=>{
  assert.equal(path,'/');return {scope:'https://app.example/',unregister:async()=>{removed.push('root');return true;}};}},},
 location:{origin:'https://app.example',replace:u=>navigations.push(u)},
 window:{caches:true,location:{replace:u=>navigations.push(u)}},
 caches:{keys:async()=>['another-app','grimequest-old','grimequest-previous'],delete:async name=>{deleted.push(name);return true;}},
 localStorage:{getItem:k=>locals.get(k),setItem:()=>assert.fail('recovery must not change localStorage'),removeItem:()=>assert.fail('recovery must not erase user records')},
 Date:{now:()=>1234},document:{getElementById:id=>nodes[id]}};
 vm.runInNewContext(fs.readFileSync('web/update.js','utf8'),ctx);
 await nodes['refresh-now'].events.click();
 assert.deepEqual(removed,['root']);assert.deepEqual(deleted.sort(),['grimequest-old','grimequest-previous']);
 assert.deepEqual(navigations,['/?app_refresh=1234']);
 assert.equal(locals.get('grimequest.v1'),'saved inventory');
 assert.equal(nodes['refresh-now'].disabled,true);
});

test('offline recovery does not unregister or delete anything',async()=>{
 const nodes={'refresh-now':{disabled:false,events:{},addEventListener(k,fn){this.events[k]=fn;}},'refresh-status':{textContent:''}};
 let touched=0;
 const ctx={console,navigator:{onLine:false,serviceWorker:{getRegistration:async()=>{touched++;}}},location:{origin:'https://app.example'},window:{},document:{getElementById:id=>nodes[id]}};
 vm.runInNewContext(fs.readFileSync('web/update.js','utf8'),ctx);
 await nodes['refresh-now'].events.click();
 assert.equal(touched,0);assert.match(nodes['refresh-status'].textContent,/Connect to the internet/);
 assert.equal(nodes['refresh-now'].disabled,false);
});

