'use strict';
const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const vm=require('node:vm');
function harness(extra={}) {const NativeDate=Date;class FixtureDate extends NativeDate{constructor(...a){super(...(a.length?a:['2026-10-06T12:00:00Z']));}static now(){return new NativeDate('2026-10-06T12:00:00Z').getTime();}}const c={console,Date:FixtureDate,...extra};vm.createContext(c);vm.runInContext(fs.readFileSync('web/app.js','utf8'),c);return c.GQ;}
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
 const g=harness({URL:{createObjectURL:()=>{created.push('blob:fixture');return 'blob:fixture';},revokeObjectURL:v=>revoked.push(v)},Image:ImageFixture,document:{createElement:tag=>{assert.equal(tag,'canvas');return canvas;}}});
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
 await assert.rejects(()=>g.normalizePhoto({type:'image/heic',name:'huge.heic',size:9000000}),/smaller than 8 MB/);
});
test('camera rejects insecure context',async()=>{const g=harness({window:{isSecureContext:false},navigator:{}});await assert.rejects(new g.Camera().start({isConnected:true}),/HTTPS/);});
test('camera stops tracks after late permission resolution',async()=>{
 let resolve,stopped=0;const g=harness({window:{isSecureContext:true},navigator:{mediaDevices:{getUserMedia:()=>new Promise(r=>resolve=r)}}});
 const c=new g.Camera(),pending=c.start({isConnected:true});c.stop();resolve({getTracks:()=>[{stop:()=>stopped++}]});await pending;assert.equal(stopped,1);
});
test('camera captures only after ready preview',()=>assert.throws(()=>new G.Camera().capture(),/not ready/));

test('service worker only handles allowlisted app shell requests',async()=>{
 const listeners={};const cacheNames=['other-app','grimequest-old'];let added=[],deleted=[],claimed=0,matches=0;
 const context={URL,console,self:{location:{origin:'https://app.example'},clients:{claim:async()=>claimed++},addEventListener:(n,fn)=>listeners[n]=fn},caches:{open:async()=>({addAll:async paths=>added=paths,match:async()=>{matches++;return 'cached'}}),keys:async()=>cacheNames,delete:async k=>{deleted.push(k)}},fetch:()=>{throw Error('Unexpected network')}};
 vm.createContext(context);vm.runInContext(fs.readFileSync('web/sw.js','utf8'),context);
 let pending;listeners.install({waitUntil:p=>pending=p});await pending;assert.ok(added.includes('/app.js'));assert.ok(!added.some(p=>p.startsWith('/api/')));
 listeners.activate({waitUntil:p=>pending=p});await pending;assert.deepEqual(deleted,['grimequest-old']);assert.equal(claimed,1);
 for(const [url,method] of [['https://app.example/api/health','GET'],['https://app.example/api/verify','POST'],['https://evil.example/app.js','GET'],['https://app.example/app.js?private=1','GET'],['https://app.example/user-photo.jpg','GET']])listeners.fetch({request:{url,method},respondWith:()=>assert.fail('Private request cached')});
 listeners.fetch({request:{url:'https://app.example/app.js',method:'GET'},respondWith:p=>pending=p});assert.equal(await pending,'cached');assert.equal(matches,1);
});
