namespace GQ {
  type Screen='home'|'inventory'|'journal'|'settings'|'capture'|'confirm'|'loadout'|'clean'|'result'|'product-scan';
  let screen: Screen='home';
  let mode: Mode='guided';
  let store=emptyStore();
  let quest: Quest | null=null;
  let health: Health | null=null;
  let healthFailed=false;
  let busy=false;
  let camera: Camera;
  let capturePurpose: 'target'|'after'='target';
  let captureImage='';
  let uploadGeneration=0;
  let productFront='';
  let productBack='';
  let ocrFailedForThesePhotos=false;
  let barcodeValue='';
  let barcodeStatus:'idle'|'detected'|'found'|'missing'|'unavailable'='idle';
  let barcodeCandidate:ProductCandidate|null=null;
  let productSearchTerm='';
  let productSearchResults:ProductCandidate[]=[];
  let productSearchStatus:'idle'|'results'|'empty'|'unavailable'='idle';
  let barcodeScanner:BarcodeScanner|null=null;
  let barcodeCameraActive=false;
  let observation: {name:string;label_text:string;label_readable:boolean}|null=null;
  let root: HTMLElement;
  const e=escapeHTML;
  const icons: Record<string,string> = {
    sparkle:'M12 2l2.4 7.6L22 12l-7.6 2.4L12 22l-2.4-7.6L2 12l7.6-2.4L12 2Z',
    camera:'M4 7h4l2-3h4l2 3h4v13H4V7Zm8 3a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z',
    home:'m3 11 9-8 9 8v10h-7v-7h-4v7H3V11Z',
    bottle:'M9 3h6v4l3 5v9H6v-9l3-5V3Zm-3 11h12M9 7h6',
    book:'M4 3h13a3 3 0 0 1 3 3v15H6a2 2 0 0 1-2-2V3Zm0 14h16M8 7h8M8 11h6',
    gear:'M9 3h6l1 3 3 1 2 5-2 5-3 1-1 3H9l-1-3-3-1-2-5 2-5 3-1 1-3Zm3 5a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z',
    arrow:'M4 12h16m-6-6 6 6-6 6',
    shield:'m12 3 8 3v7c0 5-8 8-8 8s-8-3-8-8V6l8-3Zm-4 9 3 3 5-6',
    check:'m5 12 4 4L19 6',
    close:'m6 6 12 12M6 18 18 6',
    leaf:'M20 3C10 2 3 7 4 15c1 8 13 8 16-12ZM5 19 16 8',
    trophy:'M8 3h8v8a4 4 0 0 1-8 0V3Zm0 2H3v4c0 3 3 4 5 4m8-8h5v4c0 3-3 4-5 4m-4 2v5m-5 1h10',
    upload:'M12 16V3m-5 5 5-5 5 5M4 14v7h16v-7',
    info:'M12 11v7M12 7v1M3 12a9 9 0 1 0 18 0 9 9 0 0 0-18 0Z'
  };
  function icon(name:string):string {return `<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${icons[name]||icons.sparkle}"/></svg>`;}
  function mascot(kind='mint',small=false):string {return `<div class="mascot ${kind} ${small?'small':''}" aria-hidden="true"><i class="eye left"></i><i class="eye right"></i><i class="cheek left"></i><i class="cheek right"></i><i class="mouth"></i><i class="shine"></i></div>`;}
  function button(label:string,action:string,cls='primary',extra=''):string {return `<button class="btn ${cls}" data-action="${action}" ${extra}>${label}</button>`;}
  function back(action='home',label='Back'):string {return `<button class="back" data-action="${action}">← ${label}</button>`;}
  function tag(label:string,cls=''):string {return `<span class="tag ${cls}">${label}</span>`;}
  function check(name:string,label:string):string {return `<label class="check-row"><input type="checkbox" name="${name}"><span>${label}</span></label>`;}
  function picture(src:string,alt:string,cls=''):string {return `<img class="${cls}" src="${e(src)}" alt="${e(alt)}">`;}
  function heading(kicker:string,title:string,description:string):string {return `<div class="page-heading"><p class="eyebrow">${kicker}</p><h1 tabindex="-1">${title}</h1><p class="subtitle">${description}</p></div>`;}
  function steps(active:number):string {return `<ol class="steps" aria-label="Quest progress">${['Identify','Choose','Clean','Compare'].map((s,i)=>`<li class="${i===active?'current':i<active?'complete':''}" ${i===active?'aria-current="step"':''}><span>${i<active?'✓':i+1}</span>${s}</li>`).join('')}</ol>`;}
  function productArt(p:Product):string {const brand=p.name.startsWith('Kiilto')?'kiilto':'method';return `<div class="bottle-art ${e(p.color)}" aria-hidden="true"><span class="bottle-trigger"></span><span class="bottle-body"><span>${brand}</span><i>${p.category==='glass'?'gls':'kit'}</i></span></div>`;}
  function topStats():string {
    const s=stats(store,mode);
    return `<div class="top-meta"><span class="level-avatar">${icon('leaf')}</span><div><b>Level ${s.level} · ${s.level>1?'Grime hunter':'Fresh start'}</b><span>${s.xp} ${mode==='practice'?'practice ':mode==='guided'?'guided ':''}XP</span></div></div>`;
  }
  function shell(content:string):string {
    const nav:[string,string,Screen][]=[['home','Quests','home'],['bottle','Arsenal','inventory'],['book','Journal','journal'],['gear','Settings','settings']];
    return `<a class="skip" href="#main">Skip to content</a><aside class="sidebar"><a class="brand" href="#" data-action="home"><span class="brand-mark">${icon('sparkle')}</span>grimequest<span class="brand-dot">.</span></a><p class="brand-caption">Small chores. Real wins.</p><nav aria-label="Main navigation">${nav.map(([ic,l,s])=>`<button data-action="${s}" class="nav-item ${screen===s?'selected':''}" ${screen===s?'aria-current="page"':''}>${icon(ic)}<span>${l}</span>${s==='inventory'?`<small>${store.inventory.length}</small>`:''}</button>`).join('')}</nav><div class="sidebar-bottom">${icon('shield')}<b>Real care comes first.</b><p>No mixing. No rushing.<br>No made-up cleanliness scores.</p><span>PROTOTYPE · v0.1.0</span></div></aside><div class="workspace"><header class="topbar"><div class="mobile-brand"><span class="brand-mark">${icon('sparkle')}</span>grimequest.</div><div class="location-label">${icon('home')} YOUR HOME, YOUR ADVENTURE</div>${topStats()}</header><div class="mode-banner ${mode==='live'?'live':''}">${icon(mode==='practice'?'info':'camera')}<span><b>${mode==='practice'?'Practice mode':mode==='guided'?'Camera quest · Self-reported':'AI preview mode'}</b> · ${mode==='practice'?'Illustrated examples, not real cleaning evidence.':mode==='guided'?'Real before/after photos stay on your phone. You assess your own result; no AI or upload.':'AI photos are sent only when you explicitly consent. Never a hygiene guarantee.'}</span><button data-action="settings">${mode==='practice'?'Choose play mode':'Settings'} ${icon('arrow')}</button></div>${storageWarning?`<div class="notice warning">${e(storageWarning)}</div>`:''}${store.active?`<div class="notice warning persistent">${icon('shield')}<span><b>An unfinished cleaning task may have residues:</b> ${e(store.active.product)}. Do not add another cleaner.</span><button data-action="resolve-active">Review</button></div>`:''}<main id="main" aria-busy="${busy}">${content}</main><footer>Real-world care. Game-world delight. <span class="footer-links">${button('Use on phone','show-install','text')}<a href="/privacy.html">Privacy</a><a href="/safety.html">Safety</a><button data-action="settings">Settings</button></span></footer></div><div id="toast" class="toast" role="status" aria-live="polite" aria-atomic="true"></div>`;
  }
  function homeView():string {
    const s=stats(store,mode);
    return `<section class="home-intro"><div><p class="eyebrow">A FRESH START IS ONE QUEST AWAY</p><h1 tabindex="-1">A little mess.<br>A real-life <span>quest.</span></h1><p class="hero-copy">Find the grime. Pick the right tool.<br>Make a real difference, one small clean at a time.</p><div class="hero-actions">${button(`${icon(mode==='practice'?'sparkle':'camera')}${mode==='live'?'Find grime with AI':mode==='guided'?'Start camera quest':'Try practice quest'}`,mode==='live'?'find':mode==='guided'?'guided-first':'practice-first')} ${button(mode==='practice'?'Start real camera quest':'Try practice tutorial',mode==='practice'?'guided-first':'practice-first','secondary')}</div><p class="micro">${icon('shield')} ${mode==='practice'?'No account. No API key. Just a walkthrough.':mode==='guided'?'No account, server setup, or upload. You report visible results yourself.':'Camera stays off until you open it; each AI upload requires consent.'}</p></div><div class="hero-illustration" aria-label="Illustration of a cheerful grime character on a tile cleaning quest"><div class="tile-board"><span class="tile-stain s1"></span><span class="tile-stain s2"></span><span class="tile-stain s3"></span></div><span class="floating-badge top">${icon('sparkle')} ENCOUNTER FOUND</span>${mascot('mint')}<span class="spark star1">✧</span><span class="spark star2">✧</span><span class="floating-badge bottom">${icon('check')} Real action. Real progress.</span></div></section><section class="metrics" aria-label="Your progress"><div>${icon('trophy')}<span><b>${s.clears}</b><small>${mode==='practice'?'Practice clears':mode==='guided'?'Self-reported clears':'AI-observed clears'}</small></span></div><div>${icon('sparkle')}<span><b>${s.xp}</b><small>${mode==='practice'?'Practice XP':mode==='guided'?'Guided XP':'AI quest XP'}</small></span></div><div>${icon('bottle')}<span><b>${store.inventory.length}</b><small>Products in your arsenal</small></span></div></section>${quest && quest.phase!=='result'?`<div class="notice">Your current quest is still here. ${button('Resume quest','resume','secondary')}</div>`:''}<section class="section"><div class="section-heading"><div><p class="eyebrow">${mode==='practice'?'EXPLORE THE GAME LOOP':mode==='guided'?'CAMERA QUESTS · NO SERVER REQUIRED':'AI CAMERA QUESTS'}</p><h2>${mode==='practice'?'Three small adventures.':mode==='guided'?'Ready to tackle one spot?':'Ready for a fresh start?'}</h2></div>${tag(mode==='practice'?'SIMULATED SCENES':mode==='guided'?'SELF-REPORTED QUESTS':'BETA · AI OBSERVATION')}</div>${mode==='practice'?`<div class="quest-grid">${scenarios.map((c,i)=>`<button class="quest-card ${c.color}" data-action="scenario" data-id="${c.id}"><div class="quest-thumb">${picture(c.before,`Illustrated ${c.room.toLowerCase()} cleaning target`)}<span class="quest-number">0${i+1}</span>${tag(i===2?'KNOW WHEN TO STOP':'PRACTICE QUEST')}</div><div class="quest-description"><span>${e(c.room)}</span><h3>${e(c.name)}</h3><p>${e(c.subtitle)}</p><span class="quest-link">${i===2?'Test the safety gate':'Play this example'} ${icon('arrow')}</span></div></button>`).join('')}</div>`:mode==='guided'?`<div class="panel live-empty">${icon('camera')}<div><h3>Photograph one visible spot.</h3><p>Use your phone camera to track a real chore from start to finish. You check your own surface, method, and visible result. This is not AI verification, and nothing is uploaded.</p></div>${button('Start camera quest','guided-first')}</div><h3 class="guided-tutorial-title">Or try a simulated tutorial</h3><div class="quest-grid">${scenarios.map((c,i)=>`<button class="quest-card ${c.color}" data-action="scenario" data-id="${c.id}"><div class="quest-thumb">${picture(c.before,`Illustrated ${c.room.toLowerCase()} cleaning target`)}<span class="quest-number">0${i+1}</span>${tag(i===2?'KNOW WHEN TO STOP':'PRACTICE QUEST')}</div><div class="quest-description"><span>${e(c.room)}</span><h3>${e(c.name)}</h3><p>${e(c.subtitle)}</p><span class="quest-link">${i===2?'Test the safety gate':'Play this example'} ${icon('arrow')}</span></div></button>`).join('')}</div>`:`<div class="panel live-empty">${icon('camera')}<div><h3>Start with one clearly visible spot.</h3><p>AI observations are experimental. Use only exact reviewed bottles on user-confirmed glass or glazed ceramic, and follow their actual labels.</p></div>${button('Open camera','find')}</div>`}</section><section class="bottom-note">${icon('leaf')}<p><b>Use what you already own.</b> No shopping list, no pressure to buy. Only a match when the evidence is there.</p></section>`;
  }
  function confirmView():string {
    if(!quest) return homeView();
    return `${back()}${steps(0)}${heading('ENCOUNTER FOUND',`Meet ${e(quest.name.toLowerCase())}.`,quest.mode==='guided'?'You describe this target yourself. No AI has identified it. Choose only a material you know from its care information.':'A photograph suggests a target. You confirm what the surface actually is.')}<div class="split"><div class="scene-card">${picture(quest.before,'Before view of the cleaning target')}<div class="scene-caption">${tag(quest.mode==='practice'?'ILLUSTRATED EXAMPLE':'BEFORE PHOTO')}<span>Visible target, not a hygiene assessment</span></div></div><section class="panel"><h2>Know your battlefield.</h2><div class="field"><label for="surface">What is the surface?</label><select id="surface">${Object.entries(surfaceNames).map(([k,v])=>`<option value="${k}" ${quest?.surface===k?'selected':''}>${v}</option>`).join('')}</select></div><div class="field other-material-field" id="other-surface-field" ${quest.surface==='other'?'':'hidden'}><label for="other-surface-detail">Which material is it?</label><input id="other-surface-detail" maxlength="80" autocomplete="off" value="${e(quest.surfaceDetail||'')}" placeholder="e.g. laminate, painted wall, fabric"><p class="hint">Name the material you have identified from the actual object's care information.</p></div><div class="field"><label for="soil">What is the visible problem?</label><select id="soil">${Object.entries(soilNames).map(([k,v])=>`<option value="${k}" ${quest?.soil===k?'selected':''}>${v}</option>`).join('')}</select></div><p class="hint">A camera cannot establish coatings, heat, residues or material compatibility. Choose “I'm not sure” rather than guessing.</p>${check('surface-confirm',quest.mode==='practice'?'Use this example surface and soil.':quest.mode==='guided'?'I know the actual material and visible problem, and checked the surface care instructions.':'I know this material from its care information, not just its appearance.')}<div class="notice soft">${icon('shield')} All known surfaces can use a private guided quest with your independently checked method. If you do not know the material or detect a hazard, stop and identify it first.</div>${quest.mode==='guided'?check('guided-safe-scene','This is a cool, undamaged, unpowered household target with no mould, body fluids, unknown chemicals, or other hazards.'):''}${button('Confirm target '+icon('arrow'),'confirm-target','primary wide')}</section></div>`;
  }
  function loadoutView():string {
    if(!quest) return homeView();
    const q=quest;
    const available=q.mode==='practice'?products:q.mode==='guided'?[]:products.filter(p=>store.inventory.some(i=>i.catalogId===p.id));
    const selected=(q.mode==='practice'||available.some(p=>p.id===q.productId))?products.find(p=>p.id===q.productId):undefined;
    const gated=matchProduct(q.surface,q.soil,products[0]?.id||'',allConfirmed(),q.analysis.hazards);
    const unknowns=q.mode==='practice'?[{id:'unreviewed-demo',name:'An unfamiliar descaler',note:'No reviewed label. Not a playable chemical.'}]:q.mode==='guided'?store.inventory.map(i=>({id:i.id,name:i.name,note:'Your saved product. GrimeQuest has NOT checked it for this surface.'})):store.inventory.filter(i=>!i.catalogId).map(i=>({id:i.id,name:i.name,note:'Scanned or recorded, but not reviewed for recommendations.'}));
    const guidedReady=q.mode==='guided'&&guidedTargetSupported(q.surface,q.soil,q.analysis.hazards,q.surfaceDetail);
    const selectedSurface=q.surface==='other'&&q.surfaceDetail?q.surfaceDetail:surfaceNames[q.surface];
    return `${back('confirm-back','Target')}${steps(1)}${heading('YOUR REAL INVENTORY IS YOUR LOADOUT','Choose your tool.','A good match is supported by the exact product instructions, not by bottle color.')}<div class="target-strip">${picture(q.before,'Current target')}<span><b>${e(q.name)}</b><small>${e(selectedSurface)} · ${e(soilNames[q.soil])}</small></span>${tag(q.mode==='practice'?'PRACTICE':q.mode==='guided'?'GUIDED · SELF-REPORTED':'AI PREVIEW')}</div>${q.mode==='guided'&&!guidedReady?`<div class="notice warning"><span>${icon('shield')}</span><div><b>Identify the target first.</b><p>Choose a known material and visible soil, or specify the other known material. Any heat, damage, electrical, chemical or biological hazard remains a stop. No chemical recommendation is made.</p>${button('Change target','confirm-back','secondary')}</div></div>`:q.mode!=='guided' && ['SURFACE_UNSUPPORTED','SOIL_UNSUPPORTED','HAZARD','CATALOG_STALE'].includes(gated.code)?`<div class="notice warning"><span>${icon('shield')}</span><div><b>No reviewed product match.</b><p>${e(gated.reason)}</p></div></div>`:''}${q.mode==='live'&&guidedTargetSupported(q.surface,q.soil,q.analysis.hazards,q.surfaceDetail)?`<section class="panel guided-method"><h2>No reviewed cleaner? Keep playing.</h2><p>Use the same before photo to continue as a <b>private, self-reported camera quest</b> with your independently checked method. This is not an AI-approved cleaner or a model-verified result.</p>${button('Continue as private camera quest','switch-to-guided','primary wide')}</section>`:''}${guidedReady?`<section class="panel guided-method"><h2>Every known surface can be a camera quest</h2><p>Use only your <b>independently verified</b> material-specific cleaning method. For natural stone, wood, coatings, hobs or mineral deposits, check the actual object's care and product directions first. GrimeQuest is not approving a chemical or a technique.</p>${button('Use my own checked method','choose-guided-method','primary wide')}<p class="hint">No account, special cleaner or API setup needed. Or choose one of your saved products below after verifying it yourself.</p></section>`:''}<div class="product-grid">${available.map(p=>`<button class="product-card ${q.productId===p.id?'chosen':''}" data-action="choose-product" data-id="${p.id}" aria-pressed="${q.productId===p.id}"><span class="product-index">${q.productId===p.id?'✓ SELECTED':matchProduct(q.surface,q.soil,p.id,allConfirmed(),q.analysis.hazards).status==='eligible'?'REFERENCE PRODUCT':'NOT IN SUPPORTED SCOPE'}</span>${productArt(p)}<h2>${e(p.name)}</h2><p>${e(p.variant)}</p><span class="product-pick">${q.productId===p.id?'View directions below':'Check this match'} ${icon('arrow')}</span></button>`).join('')}${unknowns.map(i=>`<button class="product-card unknown" data-action="${q.mode==='guided'?'choose-guided-method':'choose-product'}" data-id="${e(i.id)}" ${q.mode==='guided'&&!guidedReady?'disabled':''}><span class="product-index">${q.mode==='guided'?'PLAYER CHOICE · NOT VERIFIED':'UNREVIEWED'}</span><div class="unknown-bottle">${icon('bottle')}<span>?</span></div><h2>${e(i.name)}</h2><p>${e(i.note)}</p><span class="product-pick">${q.mode==='guided'?'Use only after checking label and care':'Why this stays locked'} ${icon('shield')}</span></button>`).join('')}</div>${!available.length && q.mode==='live'?`<div class="notice">No reviewed products in your arsenal yet. ${button('Add a product','inventory','secondary')}</div>`:''}${q.mode==='guided' && q.productId===GUIDED_METHOD_ID?`<section class="panel evidence-panel"><div><p class="eyebrow">SELF-SELECTED METHOD · UNVERIFIED</p><h2>${e(q.guidedProductName||'Your own checked approach')}</h2><p>This is your own choice, not a GrimeQuest chemical recommendation. Follow the exact product/tool label and material care instructions; do not mix cleaners.</p></div>${button('Continue to care checks','prepare')}</section>`:selected?`<section class="panel evidence-panel"><div><p class="eyebrow">CONDITIONAL LABEL MATCH</p><h2>${e(selected.name)}</h2><p>${e(selected.evidence_summary)}</p><p class="hint">This is not a safety certification. Exact variant, current label and surface-care confirmation are still required.</p><a href="${e(selected.source)}" target="_blank" rel="noopener noreferrer">Read manufacturer guidance ↗</a></div>${button('Prepare to clean '+icon('arrow'),'prepare')}</section>`:`<div class="bottom-note">${icon('shield')}<p>${q.mode==='guided'?'Choose your independently checked method above; GrimeQuest does not authorize cleaning products.':'No reviewed cleaner match does not prove chemical incompatibility. Follow the actual material care and product label.'}</p></div>`}`;
  }
  function cleanView():string {
    if(!quest) return homeView();
    const q=quest;
    if(q.mode==='live' && q.phase==='equipped' && q.productId && !store.inventory.some(i=>i.catalogId===q.productId)) return loadoutView();
    const ownMethod=q.mode==='guided'&&q.productId===GUIDED_METHOD_ID;
    const p=ownMethod?{name:q.guidedProductName||'Your own checked method',variant:'Chosen by you · GrimeQuest has not approved this material, product or method',steps:['Check the actual material, finish, coating and care instructions. Follow every instruction for any product or tool, if used.','Proceed only with your independently verified method. Keep appliances cool and safely unpowered. Never mix or layer cleaners or work on unknown residues.','Finish according to the real care directions and photograph the same target when dry. Do not clean to chase XP.'],restrictions:['This app has not reviewed your chosen product, method or material. It gives no chemical-use permission. For stone, wood, delicate finishes, hobs or mineral deposits, follow the exact care documentation.'],source:''}:products.find(p=>p.id===q.productId);
    if(!p) return loadoutView();
    const active=q.phase==='cleaning';
    return `${back('loadout-back','Loadout')}${steps(2)}${heading(active?'ONE METHOD. NO RUSH.':'A LITTLE CARE BEFORE THE QUEST',active?'The real action is yours.':'Ready, carefully.',q.mode==='practice'?'This walkthrough simulates a cleaning session. It does not claim a real chore was completed.':'Set the phone somewhere dry and away from the cleaning area. Follow the actual label, not a game timer.')}<div class="split"><section class="panel"><div class="selected-product">${ownMethod?icon('shield'):productArt(p as Product)}<div>${tag(ownMethod?'YOUR METHOD · NOT RECOMMENDED':'SELECTED TOOL')}<h2>${e(p.name)}</h2><p>${e(p.variant)}</p></div></div><ol class="instructions">${p.steps.map((s,i)=>`<li><span>${i+1}</span><p>${e(s)}</p></li>`).join('')}</ol><details><summary>Scope and restrictions</summary>${p.restrictions.map(r=>`<p>${e(r)}</p>`).join('')}${ownMethod?'':`<a href="${e(p.source)}" target="_blank" rel="noopener noreferrer">Manufacturer guidance ↗</a>`}</details><div class="notice warning">${icon('shield')} Never mix or layer cleaners. A dry appearance does not prove that chemical residues are absent.</div></section><section class="panel">${active?`<h2>${q.mode==='practice'?'Explore the comparison.':'When the label-directed task is done…'}</h2><p>${q.mode==='practice'?'Choose an explicitly simulated outcome to see how the game responds. Only “clear” earns practice XP.':'Photograph the same target, from the same angle and with similar lighting, after it is dry. No reward for speed or extra product.'}</p>${q.mode==='practice'?`<div class="field"><label for="practice-outcome">Example outcome</label><select id="practice-outcome"><option value="clear">Clear · visible target removed</option><option value="partial">Partial · visible residue remains</option><option value="unverifiable">Unverifiable · glare / framing changed</option></select></div>${button('Run practice comparison '+icon('arrow'),'practice-compare','primary wide')}`:`${button(icon('camera')+'Capture after photo','capture-after','primary wide')}<p class="hint">${q.mode==='guided'?'No photos are uploaded. You will compare them yourself and report the outcome.':'You will approve sending both photos to the AI provider before analysis.'}</p>`}`:`<h2>The five-point care check.</h2><p>${q.mode==='practice'?'In practice, these stand in for checks you must actually make with the real bottle.':'Confirm each point using the actual bottle and the surface-care instructions.'}</p>${check('exact_product',ownMethod?'I selected my own product/tool (if any) and checked that my method is suitable for this material and visible soil.':'This is the exact product and variant in its original labeled container.')}${check('label_allows_target','Any product or tool instructions permit this target, and I read the relevant directions and warnings.')}${check('surface_care_allows','The actual surface-care instructions permit this method, including any finish, coating or sealant restrictions.')}${check('no_other_product','No other cleaner is present or being used. I will not mix or layer products.')}${check('cool_and_safe','The target is cool, safely unpowered and free of known hazards; I have followed any food-contact or material-specific precautions.')}${button('Start '+(q.mode==='practice'?'practice clean':q.mode==='guided'?'camera quest':'cleaning'),'start-cleaning','primary wide')}`}</section></div>`;
  }
  function resultView():string {
    const q=quest;
    if(!q?.result) return homeView();
    const r=q.result,clear=r.status==='clear';
    return `${steps(3)}<div class="result-intro">${tag(q.mode==='practice'?'SIMULATED RESULT':q.mode==='guided'?'SELF-REPORTED VISIBLE CHANGE':'MODEL-ASSESSED VISIBLE CHANGE',q.mode==='practice'?'':'green')}<div class="result-mascot">${mascot(clear?'mint':'peach',true)}<span>${icon(clear?'sparkle':'shield')}</span></div><h1 tabindex="-1">${clear?'Small chore. Big little win.':r.status==='partial'?'A little grime remains.':'Let’s not guess.'}</h1><p>${clear?`${e(q.name)} ${q.mode==='practice'?'cleared in practice.':q.mode==='guided'?'reported visibly improved by you.':'visibly improved in an AI comparison.'}`:e(r.reason)}</p>${clear?`<div class="xp-reward">+300 <span>${q.mode==='practice'?'practice ':q.mode==='guided'?'guided ':''}XP</span></div>`:`<p class="no-reward">No XP awarded. No pressure to keep cleaning.</p>`}</div><div class="comparison"><figure>${picture(q.before,'Before comparison')}<figcaption>BEFORE ${q.mode==='practice'?'· ILLUSTRATION':''}</figcaption></figure><figure>${picture(q.after||q.before,'After comparison')}<figcaption>AFTER ${q.mode==='practice'?'· SIMULATED':''}</figcaption></figure></div><div class="result-footnote">${icon('info')}<p>${e(r.reason)} ${q.mode==='practice'?'Practice XP is separate from other modes.':q.mode==='guided'?'This is your self-reported progress, NOT AI validation, disinfection or certified cleanliness.':''}</p></div><div class="result-actions">${clear?button('Back to quests '+icon('arrow'),'finish'):button('Try another comparison','retry')}${button('View journal','journal','secondary')}${!clear?button('End this quest','abandon','text'):''}</div>`;
  }
  function inventoryView():string {
    return `${heading('USE WHAT YOU ALREADY OWN','Your cleaning arsenal.','Products are remembered on this device. Scanned text never automatically becomes a safety rule.')}<div class="toolbar">${button(icon('camera')+'Scan barcode','scan-product')}${button('Enter product name','manual-product','secondary')}</div>${store.inventory.length?`<section class="inventory-list">${store.inventory.map(i=>`<article class="inventory-item"><span class="inventory-symbol">${icon('bottle')}</span><div><h2>${e(i.name)}</h2><p>${i.catalogId?'Linked reference entry. Exact label must still be confirmed at each use.':'Unreviewed. Cannot unlock a cleaning recommendation.'}</p>${i.barcode?`<p class="barcode-id">GTIN: ${e(i.barcode)}</p>`:''}${i.note?`<details><summary>Your unreviewed notes</summary><p class="label-text">${e(i.note)}</p></details>`:''}</div><button class="icon-button" data-action="remove-product" data-id="${e(i.id)}" aria-label="Remove ${e(i.name)}">${icon('close')}</button></article>`).join('')}</section>`:`<div class="empty-state">${icon('bottle')}<h2>A good loadout starts under your sink.</h2><p>Add a product you already own. No one needs a new bottle just to play.</p></div>`}<section class="section"><div class="section-heading"><div><p class="eyebrow">SMALL, SOURCE-LINKED REFERENCE CATALOG</p><h2>Do you own this exact variant?</h2></div>${tag(products.length+' REVIEWED DEMO PRODUCTS')}</div><p class="hint">These are early source-reviewed examples, not an international product database. Find products worldwide through barcode/name search above, but only these exact catalog entries can be suggested as cleaners in this prototype.</p><div class="catalog-list">${products.map(p=>`<article class="catalog-item">${productArt(p)}<div><h3>${e(p.name)}</h3><p>${e(p.variant)}</p><a href="${e(p.source)}" target="_blank" rel="noopener noreferrer">Manufacturer guidance ↗</a></div>${button(store.inventory.some(i=>i.catalogId===p.id)?'Added':'I own this exact variant','add-catalog','secondary',`data-id="${p.id}" ${store.inventory.some(i=>i.catalogId===p.id)?'disabled':''}`)}</article>`).join('')}</div><p class="micro">Reference review: ${catalog.reviewed_on}. Suggestions expire ${catalog.valid_until} unless the catalog is reviewed.</p></section>`;
  }
  function journalView():string {
    const histories=store.history.filter(h=>h.mode===mode);
    return `${heading('LITTLE WINS, REMEMBERED','Your quest journal.','This is a history of assessed quests, not a measurement of how clean your home is.')}<div class="toolbar">${tag(mode==='practice'?'PRACTICE HISTORY':mode==='guided'?'SELF-REPORTED HISTORY':'AI-COMPARED HISTORY')}${button(icon('upload')+'Export local history','export','secondary',histories.length?'':'disabled')}</div>${histories.length?`<div class="history-list">${histories.map(h=>`<article class="history-item"><span class="history-icon ${h.status==='clear'?'success':''}">${icon(h.status==='clear'?'check':'info')}</span><div><h2>${e(h.name)}</h2><p>${e(h.room)} · ${e(h.date.slice(0,10))} · ${e(h.status)}</p></div><span class="history-xp">${h.xp?`+${h.xp} XP`:'No XP'}<small>${h.mode==='practice'?'SIMULATED':h.mode==='guided'?'SELF-REPORTED':'MODEL-ASSESSED'}</small></span></article>`).join('')}</div>`:`<div class="empty-state">${icon('book')}<h2>Your first little win is waiting.</h2><p>Completed comparisons appear here. Practice results never become live evidence.</p>${button('Find a quest','home','secondary')}</div>`}<div class="bottom-note">${icon('shield')}<p>No before/after photos are stored in this journal. The latest 200 comparisons are retained; displayed XP is derived from that history. Local records can be edited or lost; this is not a tamper-proof leaderboard.</p></div>`;
  }
  function settingsView():string {
    const publicAccess=health?.access_mode==='public_rate_limited';
    return `${heading('MAKE IT YOURS','A little setup. A lot of clarity.','No account or server setup is needed for guided camera quests. Optional AI analysis is hosted by GrimeQuest, never configured by players.')}<div class="settings-grid"><section class="panel"><h2>Pick how to play</h2><p>Camera quest works immediately, including offline. You assess the before/after photos yourself. AI Beta adds optional model observations if the GrimeQuest server offers them.</p><div class="segmented" role="group" aria-label="Application mode">${button('Camera quest','mode-guided',mode==='guided'?'primary':'secondary')}${button('Practice tutorial','mode-practice',mode==='practice'?'primary':'secondary')}${health?.live_ready&&publicAccess?button('AI Beta','mode-live',mode==='live'?'primary':'secondary'):''}</div><div class="server-status"><span class="status-dot ${health?.live_ready?'ready':''}"></span>${health?.live_ready&&publicAccess?'AI Beta available':'AI Beta unavailable · Camera quests work'}</div><p class="hint">${health?.live_ready?`Destination: ${e(health.provider_host)}<br>Model: ${e(health.provider_model)}<br>Limits: ${health.max_calls_hour}/hour · ${health.max_calls_day}/day per server.${health.source_sha?`<br>Release: ${e(health.source_sha.slice(0,8))}`:''} Provider fees may apply.`:'AI processing is temporarily unavailable or not enabled. You can still complete real camera quests with locally held photos and self-reported results. No player setup is required.'}</p>${publicAccess?`<div class="notice soft">${icon('shield')}<p><b>Public demo access.</b> No shared code is required. Same-origin checks and the server’s hourly/daily ceilings still apply.</p></div><p class="micro">Provider credentials remain server-side. When capacity is exhausted, live analysis fails closed instead of falling back to a simulated result.</p>`:`<p class="micro">AI model routing, spending limits and credentials are operator-managed. Players never need an API key or server configuration.</p>${health?.live_ready?`<details id="private-test-controls" class="private-test-controls"><summary>Advanced private testing (operator only)</summary><p class="hint">Only for authorized testers with an operator-issued code. Ordinary camera quests never require this.</p><label class="field"><span>Private test access code</span><input id="access-code" type="password" autocomplete="off" maxlength="160" placeholder="Operator-issued access code" value="${e(getAccessCode())}"></label>${button('Save code','save-code','secondary')}${button('Start private AI test','mode-live','secondary')}</details>`:''}`}</section><section class="panel"><h2>Privacy by default</h2><div class="settings-fact">${icon('camera')}<p><b>Photos are temporary.</b> Kept in memory for the current quest. Closing or reloading the page discards them.</p></div><div class="settings-fact">${icon('shield')}<p><b>You decide when to send.</b> Live analysis sends re-encoded photos through your server to its configured provider. Its retention policy still applies.</p></div><div class="settings-fact">${icon('book')}<p><b>Your device remembers.</b> Inventory notes, quest history and an interrupted-task warning are stored locally. Do not put personal information in label notes.</p></div><p class="hint">Avoid photographing people, addresses, documents or other private information. EXIF is stripped; visible personal information is not automatically removed.</p><p class="legal-links"><a href="/privacy.html">Full privacy notice →</a></p></section><section class="panel"><h2>Care is a hard rule.</h2><p>Self-reported camera quests support any independently identified, care-checked material. GrimeQuest recommends cleaners only for a narrow reviewed glass/tile catalog. Stop for unknown materials, damaged or hot/powered targets, hazardous chemicals, mould, body fluids and chemical mixtures.</p><p>No camera claim of disinfection. No “percent clean.” No speed bonuses. An app cannot physically prevent someone from using the wrong product.</p><p>When in doubt, stop and consult the surface/product manufacturer. If an exposure occurs, stop using the app and contact local poison/emergency services.</p><a href="https://www.cdc.gov/hygiene/about/when-and-how-to-clean-and-disinfect-your-home.html" target="_blank" rel="noopener noreferrer">CDC: label-directed household cleaning ↗</a><p class="legal-links"><a href="/safety.html">Full safety boundaries →</a></p></section><section class="panel"><h2>This device</h2><p>To install on your phone, use the browser’s Install App or Add to Home Screen option when available.</p><p>Offline support covers the camera quest, manually chosen methods, arsenal, journal and practice examples after the app loads. Your photo is not uploaded in guided mode. AI Beta requires internet and separate photo consent.</p><p class="legal-links"><a href="/update.html">Refresh or repair this installation →</a></p>${store.active?`${check('resolve-check','I have stopped the previous task and checked the actual label before doing anything else.')}${button('Clear interrupted-task warning','clear-active','secondary')}`:''}<details><summary>Delete my local data</summary><p>This removes this app’s inventory, history, access code and interrupted-task warning. It does not remove physical cleaner residues.</p>${check('delete-confirm','I understand this permanently deletes local GrimeQuest data.')}${button('Delete local data','delete-data','danger')}</details></section></div>`;
  }
  function guidedCaptureView():string {
    const after=capturePurpose==='after';
    const choice=after?`<div class='field'><label for='guided-outcome'>What do your two photos show?</label><select id='guided-outcome'><option value='unverifiable'>Unsure / not comparable</option><option value='partial'>Some visible grime remains</option><option value='clear'>I see no remaining visible grime</option></select></div>`:'';
    const confirm=after?`${check('guided-same-target','Both photos show the exact same target from a comparable angle and lighting.')}${check('guided-dry','The target is dry and any product-label procedure is complete.')}`:`${check('guided-before-confirm','This photo shows a real visible target without people, documents, or private information.')}`;
    const submit=after?button('Record my own visual comparison','guided-compare','primary wide',captureImage?'':'disabled'):button('Describe this target','guided-identify','primary wide',captureImage?'':'disabled');
    return `${back(after?'resume':'home')}${heading('REAL CAMERA QUEST · NO AI',after?'Compare your photos.':'Choose your before photo.',after?'Take the same photo again once your label-directed work is finished and the target is dry.':'Take a picture of one visible mess. You decide what the material and soil actually are; GrimeQuest does not identify them by AI in this mode.')}<div class='split'><section class='capture-panel'><div class='camera-window' id='camera-host'>${captureImage?picture(captureImage,'Selected image preview'):`<div class='camera-placeholder'>${icon('camera')}<h2>Your camera is off.</h2><p>Open it or choose a photo.</p></div>`}</div>${after&&quest?`<details class='reference-photo' open><summary>Original before photo</summary>${picture(quest.before,'Before photo to compare against')}</details>`:''}<div class='camera-controls'>${button(icon('camera')+'Open camera','open-camera','secondary')}${button('Take photo','take-photo','secondary')}<label class='btn secondary file-button'>${icon('upload')}Choose photo<input id='photo-file' type='file' accept='image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif' capture='environment'></label></div></section><section class='panel'><h2>${after?'You decide what changed.':'One target, one photo.'}</h2><p>${after?'The game cannot verify hygiene or whether the chore was completed. Your choice is a self-report, not an AI result.':'No account, API key, server configuration, or photo upload is needed.'}</p>${choice}${confirm}${submit}<p class='micro'>Images are processed locally, kept only during this quest, and never sent to a model in guided mode. Game XP is self-reported, not measured cleanliness.</p></section></div>`;
  }
  function captureView():string {
    if(mode==='guided')return guidedCaptureView();
    const after=capturePurpose==='after';
    return `${back(after?'resume':'home')}${heading(after?'SAME TARGET. SAME LIGHT.':'ONE TARGET, ONE PHOTO.',after?'Show what changed.':'Find a little grime.',after?'Let the target dry and match the original framing. A changed angle is not a cleaning result.':'Keep people, documents and private details out of the frame.')}<div class="split"><section class="capture-panel"><div class="camera-window" id="camera-host">${captureImage?picture(captureImage,'Selected image preview'):`<div class="camera-placeholder">${icon('camera')}<h2>Your camera is off.</h2><p>Open it below, or choose an existing photo.</p></div>`}</div>${after&&quest?`<details class="reference-photo" open><summary>Original view to match</summary>${picture(quest.before,'Before reference for manual alignment')}</details>`:''}<div class="camera-controls">${button(icon('camera')+'Open camera','open-camera','secondary')}${button('Take photo','take-photo','secondary')}<label class="btn secondary file-button">${icon('upload')}Choose photo<input id="photo-file" type="file" accept="image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif" capture="environment"></label></div></section><section class="panel"><h2>${after?'Compare, don’t assume.':'A deliberate photo check.'}</h2><p>${after?'Both images will be sent to the configured vision provider. The result may be clear, partial or unverifiable.':'A vision model will propose a visible target and material. You will still need to confirm the surface.'}</p><p class="hint">Destination: ${e(health?.provider_host||'Not configured')}. Provider retention terms apply.</p>${check('photo-consent',`I approve sending ${after?'both photos':'this photo'} to the configured AI provider for this analysis.`)}${after?check('procedure-done','I completed the actual product-label procedure; this photo shows the dry target.'):''}${button(after?'Analyze before / after':'Analyze target','analyze-photo','primary wide',captureImage?'':'disabled')}${!after&&captureImage?button('Continue as private camera quest','guided-from-ai-photo','secondary wide'):''}<p class="micro">Full-resolution JPEG, PNG, WebP and supported HEIC/HEIF photos are resized and compressed on this device before upload. No silent uploads or automatic retries.</p></section></div>`;
  }
  export function labelReadGate(ready:boolean|null, publicAccess:boolean, hasCode:boolean, liveMode:boolean, front:boolean, back:boolean, failed=false):{enabled:boolean;code:string;message:string}{
    if(ready===null)return {enabled:false,code:failed?'offline':'checking',message:failed?'Could not reach the AI service. Check your connection, or enter product details manually.':'Checking whether AI label reading is available. Your photos stay on your device.'};
    if(!ready)return {enabled:false,code:'disabled',message:'AI label reading is switched off on this GrimeQuest deployment. Your photos are working, but the AI service is not available for this release. This is not a phone setting. You can add this product manually below.'};
    if(!publicAccess && !hasCode)return {enabled:false,code:'code',message:'AI reading is available only to private testers. Enter the operator-provided access code. It stays in this app session; your photos are not sent without consent.'};
    if(!liveMode)return {enabled:false,code:'mode',message:'AI reading is available in private testing, but Practice mode does not make paid AI calls. Enable Live mode explicitly; model charges may apply.'};
    if(!front||!back)return {enabled:false,code:'photos',message:'Select both the front and the directions/warnings label photos before reading.'};
    return {enabled:true,code:'ready',message:'Both photos are ready. Tick the consent box before reading. The AI transcription may contain errors and does not approve any cleaning product.'};
  }
  function labelGate():{enabled:boolean;code:string;message:string}{
    return labelReadGate(health?.live_ready??null,health?.access_mode==='public_rate_limited',getAccessCode().length>=24,mode==='live'||(mode==='guided'&&health?.access_mode==='public_rate_limited'),!!productFront,!!productBack,healthFailed);
  }
  function refreshProductView():void {
    if(screen!=='product-scan')return;
    const draftName=val('product-name'),draftNote=val('product-note');
    const userChecked=checked('barcode-review');
    const draftSearch=val('product-search') || productSearchTerm;
    barcodeCameraActive=false;
    barcodeScanner?.stop();
    render(false);
    const name=root.querySelector<HTMLInputElement>('#product-name');
    const note=root.querySelector<HTMLTextAreaElement>('#product-note');
    if(name&&draftName)name.value=draftName;
    if(note&&draftNote)note.value=draftNote;
    const term=root.querySelector<HTMLInputElement>('#product-search');
    if(term)term.value=draftSearch;
    const confirm=root.querySelector<HTMLInputElement>('input[name="barcode-review"]');
    if(confirm)confirm.checked=userChecked;
  }
  export function ocrNameForReview(name:string|undefined):string {
    const value=(name||'').trim();
    // A decorative mark and 2–3 scrambled letters aren't a product name.
    // Require at least two plausible printed words; users can enter any
    // legitimate single-word brand manually after viewing the actual bottle.
    const words=(value.match(/\p{L}+/gu)||[]).filter(word=>word.length>=3);
    return words.length>=2 && words.reduce((sum,word)=>sum+word.length,0)>=8
      && !value.startsWith('Product name unclear') ? value : '';
  }
  // Accept only fixed identity providers and deterministic source URLs.
  const PRODUCT_SOURCES: Record<ProductCategory,{name:string;prefix:string}>={
    general:{name:'Open Products Facts',prefix:'https://world.openproductsfacts.org/product/'},
    beauty:{name:'Open Beauty Facts',prefix:'https://world.openbeautyfacts.org/product/'},
    food:{name:'Open Food Facts',prefix:'https://world.openfoodfacts.org/product/'},
    petfood:{name:'Open Pet Food Facts',prefix:'https://world.openpetfoodfacts.org/product/'},
    upc:{name:'UPCitemdb',prefix:'https://www.upcitemdb.com/upc/'},
    ean:{name:'EAN-Suche',prefix:'https://ean-suche.net/produkt/'},
    web:{name:'Web search',prefix:'https://www.google.com/search?q='}
  };
  export function validProductCandidate(raw:unknown):raw is ProductCandidate {
    if(!raw || typeof raw!=='object')return false;
    const item=raw as ProductCandidate;
    if(!validGTIN(item.barcode) || typeof item.found!=='boolean' ||
       typeof item.name!=='string' || item.name.length>180 ||
       typeof item.brand!=='string' || item.brand.length>100 ||
       typeof item.quantity!=='string' || item.quantity.length>80 ||
       item.review_status!=='unreviewed' || item.recommendation_permission!==false)return false;
    if(!Object.prototype.hasOwnProperty.call(PRODUCT_SOURCES,item.category))return false;
    const source=PRODUCT_SOURCES[item.category];
    if(item.source!==source.name || item.source_url!==source.prefix+item.barcode)return false;
    return !item.found || item.name.trim().length>=3;
  }

  function productScanView():string {
    const suggestion=barcodeCandidate?.found?barcodeCandidate:null;
    const widerSearchUrl='https://www.google.com/search?q='+encodeURIComponent(productSearchTerm+' product');
    const widerBarcodeUrl='https://www.google.com/search?q='+encodeURIComponent(barcodeValue);
    const searchPanel=productSearchStatus==='results' && productSearchResults.length
      ? `<div class='product-search-results' role='status' aria-live='polite'>
          <p><b>Found ${productSearchResults.length} possible products.</b> These are unverified community suggestions across countries and categories.</p>
          ${productSearchResults.map((item,i)=>`<button type='button' class='product-search-result' data-action='select-search-result' data-id='${i}'>
            <span class='product-search-result-name'>${e(item.name)}</span>
            <small>${e(item.brand)}${item.quantity?' · '+e(item.quantity):''} · ${e(item.source)}</small>
            <span class='product-search-result-action'>Review this exact item →</span>
          </button>`).join('')}
          <p class='micro'>Select a suggestion to see the source; then check the exact bottle before saving.</p>
        </div>`
      :productSearchStatus==='empty'
        ? `<div class='notice soft' role='status'>No matching community records. You can still type the name from your bottle or <a href='${e(widerSearchUrl)}' target='_blank' rel='noopener noreferrer' referrerpolicy='no-referrer'>search the wider web ↗</a> to verify it yourself. The web search opens only if you click.</div>`
        :productSearchStatus==='unavailable'
          ? `<div class='notice soft' role='status'>Community search is unavailable. Type the product name yourself or <a href='${e(widerSearchUrl)}' target='_blank' rel='noopener noreferrer' referrerpolicy='no-referrer'>search the wider web ↗</a> in a separate tab.</div>`
          : "";
    const status=barcodeStatus==='found'&&suggestion
      ? `<div class='notice soft' role='status'><b>Possible product match</b><p>${e(suggestion.name)} ${suggestion.brand?'· '+e(suggestion.brand):''} ${suggestion.quantity?'· '+e(suggestion.quantity):''}</p><p>Unverified. Confirm the exact name and variant on your actual bottle. Never infer cleaner safety from barcode data.</p><a href='${e(suggestion.source_url)}' target='_blank' rel='noopener noreferrer'>${e(suggestion.source)} source ↗</a></div>`
      :barcodeStatus==='missing'
        ? `<div class='notice soft' role='status'>No exact match from our available sources. Type the product name below, or <a href='${e(widerBarcodeUrl)}' target='_blank' rel='noopener noreferrer' referrerpolicy='no-referrer'>search the wider web by barcode ↗</a> (opens only if you click).</div>`
        :barcodeStatus==='unavailable'
          ? "<div class='notice soft' role='status'>Product lookup is temporarily unavailable. Enter the name from the bottle to continue playing.</div>"
          :barcodeStatus==='detected'
            ? "<div class='notice soft' role='status'>Barcode detected on this device. Searching automatically…</div>"
            : "";
    return `${back('inventory','Arsenal')}${heading('WORLDWIDE PRODUCT DISCOVERY · NO PHOTO OCR','Find your bottle.','Scan a barcode once, search by name, or enter the exact label. Verify the physical packaging before saving.')}
      <div class='split'>
        <section class='panel barcode-panel'>
          <h2>1. Scan a barcode</h2>
          <p>Point at the barcode on the bottle. GrimeQuest starts looking up the number automatically. Camera video stays <b>on this device</b>.</p>
          <div class='barcode-scanner-actions'>
            ${button(icon('camera')+' Scan barcode','start-barcode-camera','primary')}
            <label class='btn secondary file-button'>${icon('upload')} Choose barcode photo<input id='barcode-photo' type='file' accept='image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif' capture='environment'></label>
          </div>
          <div id='barcode-camera-area' class='barcode-camera-area' hidden>
            <video id='barcode-video' autoplay muted playsinline aria-label='Live local barcode camera'></video>
            <p>Hold the EAN bars inside the frame. Nothing is recorded or uploaded.</p>
            ${button('Stop camera','stop-barcode-camera','secondary')}
          </div>
          <div class='field barcode-entry'>
            <label for='product-code'>Barcode number (EAN / UPC / GTIN)</label>
            <input id='product-code' type='text' inputmode='numeric' autocomplete='off' maxlength='14' pattern='[0-9]*' value='${e(barcodeValue)}' placeholder='Numbers printed under the barcode'>
          </div>
          ${button('Look up entered barcode','lookup-barcode','secondary wide')}
          ${status}
          <p class='micro'>Only the barcode digits go to the worldwide product sources; no camera image is uploaded. Wider web lookup needs an operator-provided key, never a player key.</p>
          <div class='barcode-search-divider'></div>
          <h2>2. Or search by name</h2>
          <p>Search multilingual Open Facts records by brand or product name.</p>
          <div class='field'>
            <label for='product-search'>Brand or product name</label>
            <input id='product-search' type='search' maxlength='72' autocomplete='off' value='${e(productSearchTerm)}' placeholder='e.g. Sanytol, Lysol, Cif, Kiilto'>
          </div>
          ${button('Search products worldwide','search-product-name','secondary wide')}
          <p class='micro'>Name search is sent only when requested. It does not upload photos.</p>
          ${searchPanel}
          <p class='micro'>No database is complete. If lookup fails, enter the exact name to continue playing.</p>
        </section>
        <section class='panel barcode-entry-panel'>
          <h2>3. Confirm or enter the product</h2>
          <p>Read the bottle yourself. A barcode identifies a product candidate, not its ingredients, directions or compatibility with your surface.</p>
          <div class='field'>
            <label for='product-name'>Exact product name</label>
            <input id='product-name' maxlength='240' value='${e(suggestion?.name||'')}' placeholder='Brand and product variant printed on the bottle'>
          </div>
          <div class='field'>
            <label for='product-note'>Your notes (optional, unreviewed)</label>
            <textarea id='product-note' rows='5' maxlength='6000' placeholder='Only details you personally confirmed from the bottle'>${''}</textarea>
          </div>
          ${suggestion?check('barcode-review','I checked this suggested name and exact product variant against the bottle.'):''}
          ${button('Save product to my arsenal','save-product','primary wide')}
          <p class='micro'>Saved only on this device. Unreviewed products do not unlock chemical/surface safety recommendations. You can complete guided quests with your own instruction-checked method.</p>
          <p class='micro'>Sources: <a href='https://world.openproductsfacts.org/' target='_blank' rel='noopener noreferrer'>Open Facts</a> · <a href='https://ean-suche.net/api-doku' target='_blank' rel='noopener noreferrer'>EAN-Suche</a> · <a href='https://www.upcitemdb.com/api/' target='_blank' rel='noopener noreferrer'>UPCitemdb</a>. None certify chemical-use safety.</p>
        </section>
      </div>`;
  }

  function render(focus=true):void {
    camera?.stop();
    if(barcodeCameraActive){barcodeScanner?.stop();barcodeCameraActive=false;}
    const content=screen==='home'?homeView():screen==='confirm'?confirmView():screen==='loadout'?loadoutView():screen==='clean'?cleanView():screen==='result'?resultView():screen==='inventory'?inventoryView():screen==='journal'?journalView():screen==='settings'?settingsView():screen==='capture'?captureView():productScanView();
    root.innerHTML=shell(content);
    if(focus) requestAnimationFrame(()=>{root.querySelector<HTMLElement>('h1')?.focus({preventScroll:true}); window.scrollTo({top:0,behavior:'instant'});});
  }
  function go(s:Screen):void {screen=s;render();}
  let toastTimer:number|undefined;
  function toast(message:string,error=false):void {
    const host=document.getElementById('toast');
    if(!host) return;
    window.clearTimeout(toastTimer);host.textContent=message;host.className=`toast visible ${error?'error':''}`;
    toastTimer=window.setTimeout(()=>host.classList.remove('visible'),9000);
  }
  function checked(name:string):boolean {return !!root.querySelector<HTMLInputElement>(`input[name="${name}"]`)?.checked;}
  function val(id:string):string {return root.querySelector<HTMLInputElement|HTMLSelectElement|HTMLTextAreaElement>(`#${id}`)?.value.trim()||'';}
  function persist():void {saveStore(store);}
  async function api<T>(path:string,payload:unknown,timeoutMs=35000):Promise<T> {
    if(location.protocol==='file:') throw new Error('This standalone preview has no backend. Use the source package to run live mode.');
    const headers:Record<string,string>={'Content-Type':'application/json'};
    if(health?.access_mode!=='public_rate_limited') headers['X-GQ-Access']=getAccessCode();
    const response=await fetch(`/api/${path}`,{method:'POST',headers,body:JSON.stringify(payload),cache:'no-store',credentials:'omit',signal:AbortSignal.timeout(timeoutMs)});
    let body:unknown;
    try {body=await response.json();} catch {throw new Error('Server returned an invalid response. No result was awarded.');}
    if(!response.ok) {
      const b=body as {error?:{message?:string};match?:{reason?:string}};
      throw new Error(b.error?.message||b.match?.reason||'The request could not be completed.');
    }
    return body as T;
  }
  async function work(fn:()=>Promise<void>):Promise<void> {
    if(busy) return;busy=true;
    root.querySelector('main')?.setAttribute('aria-busy','true');
    root.querySelectorAll<HTMLButtonElement>('button').forEach(b=>{b.dataset.wasDisabled=String(b.disabled);b.disabled=true;});
    toast('Working on this request. No result is assumed while it runs.');
    try {await fn();} catch(err) {toast(err instanceof Error?err.message:'Something went wrong. No result was assumed.',true);}
    finally {busy=false;root.querySelector('main')?.setAttribute('aria-busy','false');root.querySelectorAll<HTMLButtonElement>('button[data-was-disabled]').forEach(b=>{b.disabled=b.dataset.wasDisabled==='true';delete b.dataset.wasDisabled;});}
  }
  function newPractice(id:string):void {
    if(store.active) throw new Error('Review the interrupted live cleaning task before starting another.');
    const c=scenarios.find(c=>c.id===id);if(!c) return;
    mode='practice';quest={id:crypto.randomUUID(),mode,phase:'identified',name:c.name,room:c.room,before:c.before,surface:c.surface,soil:c.soil,scenario:c.id,analysis:{object_name:c.room+' target',surface:c.surface,soil:c.soil,visible_soil:true,image_quality:'usable',material_certainty:c.surface==='unknown'?'unknown':'tentative',hazards:['none'],target_box:{x:0.1,y:0.1,width:0.8,height:0.8}}};go('confirm');
  }
  function resume():void {
    if(!quest) {go('home');return;}
    if(quest.mode==='live' && quest.phase==='equipped' && quest.productId && !store.inventory.some(i=>i.catalogId===quest?.productId)) {
      quest={...quest,phase:'confirmed',productId:undefined,encounterTicket:undefined};
      toast('That reviewed product is no longer in your arsenal. Choose the bottle you actually own.',true);
      go('loadout');
      return;
    }
    const map:Record<Phase,Screen>={identified:'confirm',confirmed:'loadout',equipped:'clean',cleaning:'clean',result:'result'};
    go(map[quest.phase]);
  }
  function requireLive():void {
    if(!health?.live_ready) throw new Error('AI Beta is unavailable. Choose Camera quest to play without an account or server setup.');
    if(health.access_mode!=='public_rate_limited' && getAccessCode().length<24) throw new Error('AI Beta is limited to authorized testers. Choose Camera quest for no-setup play.');
  }
  function exportHistory():void {
    const data={format:'grimequest-journal-v1',exportedAt:new Date().toISOString(),mode,notice:'No photos or API keys. Local records are not tamper-proof proof of cleaning.',history:store.history.filter(h=>h.mode===mode)};
    const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');
    a.href=url;a.download='grimequest-journal.json';a.click();window.setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  async function findBarcodeProduct(code:string):Promise<void> {
    if(!validGTIN(code))throw new Error('Barcode digits are incomplete or the check digit is wrong. Enter the digits printed below the bars.');
    // A new scan must never inherit a previous product's reviewed checkbox/name.
    if(barcodeCandidate?.found) {
      const name=root.querySelector<HTMLInputElement>('#product-name');
      if(name && name.value===barcodeCandidate.name)name.value='';
    }
    barcodeValue=code;barcodeCandidate=null;barcodeStatus='detected';
    refreshProductView();
    await work(async()=>{
      let result:ProductCandidate;
      try {
        result=await api<ProductCandidate>('product-lookup',{barcode:code},16000);
      }catch {
        barcodeStatus='unavailable';barcodeCandidate=null;
        refreshProductView();
        toast('Online product lookup is unavailable. Enter the product name directly; no setup is needed.',true);
        return;
      }
      if(!validProductCandidate(result)||result.barcode!==code)
        throw new Error('The global product result could not be verified. Enter the name manually.');
      barcodeCandidate=result.found?result:null;
      barcodeStatus=result.found?'found':'missing';
      refreshProductView();
      toast(result.found?'Possible product found. Confirm the exact bottle before saving.':
        'No matching record. Enter the exact bottle name to continue.');
    });
  }

  async function findProductsByName(raw:string):Promise<void> {
    const query=raw.trim();
    if(query.length<2||query.length>72 || !/[\p{L}\p{N}]/u.test(query))
      throw new Error('Enter at least two letters or numbers of the product name or brand.');
    productSearchTerm=query;
    await work(async()=>{
      let response:ProductSearchResponse;
      try {
        response=await api<ProductSearchResponse>('product-search',{query},12500);
      }catch {
        productSearchResults=[];productSearchStatus='unavailable';
        refreshProductView();
        toast('Global product search is unavailable. Enter the exact name from your bottle instead.',true);
        return;
      }
      if(!response||response.source!=='Open Facts'||response.review_status!=='unreviewed'||
         response.recommendation_permission!==false||!Array.isArray(response.results)||
         response.results.length>10||!response.results.every(item=>validProductCandidate(item)&&item.found))
        throw new Error('The community search returned invalid product information. Enter the name manually.');
      productSearchResults=response.results;
      productSearchStatus=response.results.length?'results':'empty';
      refreshProductView();
      toast(response.results.length
        ?'Worldwide matches found. Tap the matching variant, then confirm against your bottle.'
        :'No public match yet. You can still type the name and save the product.');
    });
  }

  async function action(name:string,id?:string):Promise<void> {
    if(busy) return;
    try {
      if(['home','inventory','journal','settings'].includes(name)) {go(name as Screen);return;}
      switch(name) {
        case 'show-install':window.dispatchEvent(new Event('grimequest:show-install'));break;
        case 'how': toast('Identify one target → confirm its material → choose an evidence-backed product → do the real task → compare photos. Practice simulates those steps.');break;
        case 'practice-first':newPractice('kitchen');break;
        case 'guided-first':if(store.active)throw new Error('Review the interrupted cleaning task before starting a new one.');mode='guided';quest=null;capturePurpose='target';captureImage='';go('capture');break;
        case 'guided-from-ai-photo':{
          if(mode!=='live'||capturePurpose!=='target'||!captureImage)throw new Error('Choose a target photo first.');
          if(store.active)throw new Error('Review the unfinished task before switching modes.');
          mode='guided';quest=null;go('capture');
          toast('Continuing privately. Your photo stays on this device; AI is not used.');break;
        }
        case 'scenario':newPractice(id||'');break;
        case 'resume':resume();break;
        case 'confirm-back': if(quest){quest={...quest,phase:'identified',productId:undefined};go('confirm');}break;
        case 'loadout-back':if(quest?.phase==='cleaning'){toast('The selected product is locked while cleaning. Do not switch products mid-task.',true);}else go('loadout');break;
        case 'confirm-target': {
          if(!quest) break;
          if(quest.mode==='guided'&&!checked('guided-safe-scene'))throw new Error('Confirm this is an ordinary, undamaged, cool target without electrical or chemical hazards.');
          const surface=val('surface'),soil=val('soil');
          if(!checked('surface-confirm')) throw new Error('Confirm the material check, or choose “I’m not sure.”');
          if(!isSurface(surface)||!isSoil(soil)) throw new Error('Choose a valid material and visible problem.');
          const surfaceDetail=surface==='other'?val('other-surface-detail').trim():undefined;
          if(surface==='other'&&!validOtherMaterial(surfaceDetail))throw new Error('Enter the actual material name (3–80 characters) after checking its care information.');
          quest={...transition(quest,{type:'confirm',surface,soil}),surfaceDetail,guidedProductName:undefined};
          go('loadout');break;
        }
        case 'choose-product': if(quest){quest=transition(quest,{type:'equip',productId:id||''});render(false);toast('Conditional match found. Check the current bottle and surface instructions before use.');}break;
        case 'choose-guided-method':if(quest?.mode==='guided'){
          const picked=id?store.inventory.find(i=>i.id===id):undefined;
          if(id&&!picked)throw new Error('This product is no longer in your Arsenal. Choose another or use your own method.');
          quest=transition(quest,{type:'equip-guided'});
          quest={...quest,guidedProductName:picked?.name};
          render(false);
          toast('Your own method was selected by you, not recommended or assessed by GrimeQuest.');
        }break;
        case 'switch-to-guided':{
          if(!quest||quest.mode!=='live'||quest.phase!=='confirmed'||store.active)throw new Error('Only an unstarted safe target can switch to private camera play.');
          if(!guidedTargetSupported(quest.surface,quest.soil,quest.analysis.hazards,quest.surfaceDetail))throw new Error('Identify the target and stop for hazards before choosing an independently checked method.');
          mode='guided';
          quest={...quest,id:crypto.randomUUID(),mode:'guided',productId:undefined,guidedProductName:undefined,targetTicket:undefined,encounterTicket:undefined};
          go('loadout');
          toast('Now in private camera-quest mode. Any result is self-reported, not AI-verified.');
          break;
        }
        case 'prepare':go('clean');break;
        case 'start-cleaning': {
          if(!quest?.productId) break;
          if(quest.mode==='live' && !store.inventory.some(i=>i.catalogId===quest?.productId)) throw new Error('That reviewed product is no longer in your arsenal. Add or select the bottle you actually own.');
          const a:Attestations={exact_product:checked('exact_product'),label_allows_target:checked('label_allows_target'),surface_care_allows:checked('surface_care_allows'),no_other_product:checked('no_other_product'),cool_and_safe:checked('cool_and_safe')};
          if(!Object.values(a).every(Boolean)) throw new Error('Complete all five care checks before continuing.');
          if(quest.mode==='guided' && quest.productId===GUIDED_METHOD_ID){
            if(!guidedTargetSupported(quest.surface,quest.soil,quest.analysis.hazards,quest.surfaceDetail))throw new Error('Identify the material and soil and resolve hazards before starting the guided quest.');
          }else{
            const current=matchProduct(quest.surface,quest.soil,quest.productId,a,quest.analysis.hazards);
            if(current.status!=='eligible')throw new Error(current.reason);
          }
          if(quest.mode==='practice'){quest=transition(quest,{type:'start'});go('clean');break;}
          if(quest.mode==='guided'){
            quest=transition(quest,{type:'start'});
            store={...store,active:{product:quest.productId===GUIDED_METHOD_ID?(quest.guidedProductName||'User-chosen cleaning method'):products.find(p=>p.id===quest?.productId)?.name||'User-selected product',startedAt:new Date().toISOString()}};
            persist();go('clean');break;
          }
          const q=quest;
          await work(async()=>{
            const r=await api<{encounter_id:string;encounter_ticket:string;match:Match}>('start',{target_ticket:q.targetTicket,surface:q.surface,soil:q.soil,product_id:q.productId,attestations:a});
            if(!r.encounter_ticket||r.match?.status!=='eligible') throw new Error('Invalid start response.');
            quest=transition({...q,id:r.encounter_id,encounterTicket:r.encounter_ticket},{type:'start'});
            store={...store,active:{product:products.find(p=>p.id===q.productId)?.name||'Selected product',startedAt:new Date().toISOString()}};persist();go('clean');
          });break;
        }
        case 'guided-identify': {
          if(mode!=='guided'||capturePurpose!=='target'||!captureImage||!checked('guided-before-confirm'))throw new Error('Choose a before photo and confirm it is suitable for a private guided quest.');
          const image=captureImage;
          quest={id:crypto.randomUUID(),mode:'guided',phase:'identified',name:'Your cleaning quest',room:'Your home',surface:'unknown',soil:'unknown',before:image,
            analysis:{object_name:'User-described target',surface:'unknown',soil:'unknown',visible_soil:true,image_quality:'usable',material_certainty:'unknown',hazards:['none'],target_box:{x:0,y:0,width:1,height:1}}};
          captureImage='';go('confirm');break;
        }
        case 'guided-compare': {
          if(mode!=='guided'||!quest||quest.mode!=='guided'||quest.phase!=='cleaning'||capturePurpose!=='after'||!captureImage)throw new Error('A valid guided after-photo is required.');
          if(!checked('guided-same-target')||!checked('guided-dry'))throw new Error('Confirm matching photos, completed instructions and a dry target before reporting a result.');
          if(quest.before===captureImage)throw new Error('Before and after photos are identical. Take a new photo; do not claim a clear result.');
          const outcome=val('guided-outcome') as ResultStatus;
          if(!['clear','partial','unverifiable'].includes(outcome))throw new Error('Choose a valid comparison outcome.');
          const report:Result={encounter_id:quest.id,status:outcome,xp:outcome==='clear'?300:0,provenance:'self_attested',
            reason:outcome==='clear'?'You reported that the same dry target now shows no visible grime. This is self-reported, not AI analysis, hygiene or disinfection.':
              outcome==='partial'?'You reported some visible grime remains. Do not add or change cleaners to chase points.':
              'You reported an uncertain or non-comparable view. No result is inferred.'};
          quest=transition(quest,{type:'result',result:report,after:captureImage});store=recordResult(store,quest);persist();captureImage='';go('result');break;
        }
        case 'practice-compare': {
          if(!quest||quest.mode!=='practice') break;
          const outcome=val('practice-outcome') as ResultStatus;
          if(!['clear','partial','unverifiable'].includes(outcome)) break;
          const c=scenarios.find(c=>c.id===quest?.scenario);if(!c) break;
          const r:Result={encounter_id:quest.id,status:outcome,xp:outcome==='clear'?300:0,provenance:'practice_fixture',reason:outcome==='clear'?'This illustrated after-scene is a predetermined clear example, not a model analysis or real cleaning evidence.':outcome==='partial'?'The example still has visible residue. Adding another cleaner is not a game mechanic.':'The example cannot be reliably compared. No success is inferred.'};
          quest=transition(quest,{type:'result',result:r,after:outcome==='clear'?c.after:c.partial});store=recordResult(store,quest);persist();go('result');break;
        }
        case 'retry':if(quest){quest=transition(quest,{type:'retry'});go('clean');}break;
        case 'finish':quest=null;captureImage='';productFront='';productBack='';observation=null;go('home');break;
        case 'abandon':quest=null;captureImage='';productFront='';productBack='';observation=null;go(store.active?'settings':'home');break;
        case 'mode-guided': if(store.active)throw new Error('Review the unfinished cleaning task before changing modes.');mode='guided';quest=null;render();break;
        case 'mode-practice': if(store.active) throw new Error('Review the unfinished live task first.');mode='practice';quest=null;render();break;
        case 'mode-live':requireLive();if(store.active) throw new Error('Review or resume the unfinished live task before changing mode.');mode='live';quest=null;render();break;
        case 'save-code': if(!setAccessCode(val('access-code'))) throw new Error('Session storage is unavailable.');toast('Private access code saved for this tab.');break;
        case 'find':requireLive();if(store.active) throw new Error('Review the unfinished task before selecting another product.');mode='live';capturePurpose='target';captureImage='';go('capture');break;
        case 'capture-after':if(quest?.phase==='cleaning'){capturePurpose='after';captureImage='';go('capture');}break;
        case 'open-camera': {
          const host=document.getElementById('camera-host');if(!host) break;
          camera.start(host).catch(err=>toast(err instanceof Error?err.message:'Camera unavailable. Choose a photo instead.',true));break;
        }
        case 'take-photo':captureImage=camera.capture();go('capture');break;
        case 'analyze-photo': {
          if(!captureImage||!checked('photo-consent')) throw new Error('Select a photo and explicitly approve this analysis first.');
          const image=captureImage;
          if(capturePurpose==='target') {
            await work(async()=>{
              const r=await api<{analysis:unknown;target_ticket:string}>('analyze-target',{image,consent:true});
              if(!validateAnalysis(r.analysis)||typeof r.target_ticket!=='string') throw new Error('Invalid target response. No cleaning recommendation was made.');
              const a=r.analysis;
              quest={id:crypto.randomUUID(),mode:'live',phase:'identified',name:a.soil==='grease'?'The grease gremlin':a.soil==='fingerprints'?'The smudge sprite':'A little cleaning quest',room:a.object_name,before:image,surface:a.surface,soil:a.soil,analysis:a,targetTicket:r.target_ticket};
              captureImage='';go('confirm');
            });
          } else {
            if(!checked('procedure-done')) throw new Error('Confirm that the actual label-directed procedure is complete and the target is dry.');
            if(!quest||quest.phase!=='cleaning') throw new Error('The active quest was lost. No result can be issued.');
            const q=quest;
            await work(async()=>{
              const r=await api<unknown>('verify',{encounter_ticket:q.encounterTicket,before_image:q.before,after_image:image,consent:true,procedure_completed:true,surface_dry:true});
              if(!validateResult(r)) throw new Error('Invalid comparison response. No XP awarded.');
              quest=transition(q,{type:'result',result:r,after:image});store=recordResult(store,quest);persist();captureImage='';go('result');
            });
          }break;
        }
        case 'add-catalog': {
          const p=products.find(p=>p.id===id);if(!p) break;
          if(store.inventory.length>=40) throw new Error('This prototype supports up to 40 inventory entries.');
          if(!store.inventory.some(i=>i.catalogId===p.id))store={...store,inventory:[...store.inventory,{id:crypto.randomUUID(),name:p.name+' · '+p.variant,catalogId:p.id,note:'Owner-selected reference entry. Confirm exact label and surface-care instructions at every use.',addedAt:new Date().toISOString()}]};
          persist();render(false);toast('Added to your arsenal. This does not certify the product or its use.');break;
        }
        case 'remove-product':store={...store,inventory:store.inventory.filter(i=>i.id!==id)};persist();render(false);break;
        case 'scan-product':case 'manual-product':{
          barcodeScanner?.stop();barcodeCameraActive=false;
          barcodeValue='';barcodeCandidate=null;barcodeStatus='idle';
          productSearchTerm='';productSearchResults=[];productSearchStatus='idle';
          productFront='';productBack='';observation=null;ocrFailedForThesePhotos=false;
          go('product-scan');
          if(name==='manual-product'){
            root.querySelector<HTMLInputElement>('#product-name')?.focus({preventScroll:true});
          }
          break;
        }
        case 'lookup-barcode':await findBarcodeProduct(val('product-code'));break;
        case 'search-product-name':await findProductsByName(val('product-search'));break;
        case 'select-search-result':{
          const index=Number(id);
          if(!Number.isInteger(index)||index<0||index>=productSearchResults.length)
            throw new Error('That community result is no longer available.');
          const candidate=productSearchResults[index];
          if(!candidate||!validProductCandidate(candidate)||!candidate.found)
            throw new Error('The community result is invalid. Enter the product manually.');
          barcodeCandidate=candidate;barcodeStatus='found';barcodeValue=candidate.barcode;
          refreshProductView();
          const field=root.querySelector<HTMLInputElement>('#product-name');
          if(field)field.value=candidate.name;
          const reviewed=root.querySelector<HTMLInputElement>('input[name="barcode-review"]');
          if(reviewed)reviewed.checked=false;
          field?.focus({preventScroll:true});
          toast('Suggested '+candidate.source+' name selected. Confirm the exact product and variant on the bottle before saving.');
          break;
        }
        case 'start-barcode-camera':{
          const video=root.querySelector<HTMLVideoElement>('#barcode-video');
          const panel=root.querySelector<HTMLElement>('#barcode-camera-area');
          if(!video||!panel)throw new Error('Barcode camera area unavailable.');
          panel.hidden=false;
          barcodeScanner??=new BarcodeScanner();barcodeCameraActive=true;
          try {
            await barcodeScanner.start(video,code=>{
              if(screen!=='product-scan')return;
              barcodeCameraActive=false;
              void findBarcodeProduct(code);
            });
          }catch(error) {
            barcodeScanner?.stop();barcodeCameraActive=false;panel.hidden=true;
            throw error;
          }
          break;
        }
        case 'stop-barcode-camera':{
          barcodeScanner?.stop();barcodeCameraActive=false;
          const panel=root.querySelector<HTMLElement>('#barcode-camera-area');if(panel)panel.hidden=true;
          break;
        }
        case 'focus-manual-product':{
          const field=root.querySelector<HTMLInputElement>('#product-name');
          field?.scrollIntoView({behavior:'smooth',block:'center'});field?.focus({preventScroll:true});break;
        }
        case 'save-label-code': {
          const code=val('label-private-code');
          if(code.length<24)throw new Error('Enter the operator-provided access code (at least 24 characters).');
          if(!setAccessCode(code))throw new Error('Session storage is unavailable.');
          refreshProductView();toast('Private code saved for this app session. No photos have been sent.');break;
        }
        case 'enable-label-live': {
          requireLive();if(store.active)throw new Error('Resolve the unfinished cleaning task first.');
          mode='live';quest=null;refreshProductView();toast('Live AI mode enabled. Reading still requires your consent.');break;
        }
        case 'recheck-label-ai': {
          if(location.protocol==='file:')throw new Error('Standalone preview has no AI server.');
          const response=await fetch('/api/health',{cache:'no-store',credentials:'omit',signal:AbortSignal.timeout(4000)});
          if(!response.ok)throw new Error('Could not reach GrimeQuest server.');
          const h=await response.json();if(typeof h.live_ready!=='boolean'||typeof h.version!=='string')throw new Error('Invalid AI status response.');
          health=h;healthFailed=false;refreshProductView();break;
        }
        case 'read-label-ocr': {
          if(!health?.label_ocr_ready)throw new Error('Automatic text recognition is unavailable. Enter the label manually.');
          if(!productFront||!productBack)throw new Error('Take both the front and directions/warnings photos first.');
          if(!checked('product-consent'))throw new Error('Check the consent box before uploading both photos to GrimeQuest for text recognition.');
          const draftName=val('product-name'),draftNote=val('product-note');
          await work(async()=>{
            let r:{observation:{name:string;label_text:string;label_readable:boolean};extraction:string};
            try{
              r=await api<typeof r>('read-labels',
                {front_image:productFront,back_image:productBack,consent:true},16000);
            }catch(error){
              // Error categories remain actionable and sanitized by the
              // backend; never mislabel a credential rejection as a timeout.
              // No automatic retries, no fabricated OCR, no lost photos.
              const reason=error instanceof Error?error.message:'Cloud Vision could not complete this scan.';
              ocrFailedForThesePhotos=true;
              observation=null;
              refreshProductView();
              const field=root.querySelector<HTMLInputElement>('#product-name');
              field?.scrollIntoView({behavior:'smooth',block:'center'});
              field?.focus({preventScroll:true});
              toast(reason+' Your photos are still selected; enter the details manually without rescanning.',true);
              return;
            }
            const o=r.observation;
            ocrFailedForThesePhotos=false;
            if(!o||typeof o.name!=='string'||!o.name||o.name.length>240||
               typeof o.label_text!=='string'||o.label_text.length>6000||typeof o.label_readable!=='boolean'||
               r.extraction!=='google_cloud_vision')throw new Error('Invalid OCR response. No product was approved.');
            observation=o;render(false);
            const name=root.querySelector<HTMLInputElement>('#product-name');
            const note=root.querySelector<HTMLTextAreaElement>('#product-note');
            if(name&&draftName)name.value=draftName;
            if(note&&draftNote)note.value=(draftNote+'\n\n'+o.label_text).slice(0,6000);
            toast(o.label_readable?'Text detected. Confirm the name and every warning on the bottle before saving.':'The scan is uncertain. Retake a closer photo or correct the name and warnings manually. No cleaner was approved.',!o.label_readable);
          });break;
        }
        case 'analyze-product': {
          requireLive();if(mode!=='live'&&!(mode==='guided'&&health?.access_mode==='public_rate_limited'))throw new Error('Live AI label reading is not available in this mode.');if(!productFront||!productBack||!checked('product-ai-consent')) throw new Error('Choose both labels and explicitly approve external AI processing first.');
          await work(async()=>{const r=await api<{observation:{name:string;label_text:string;label_readable:boolean}}>('analyze-product',{front_image:productFront,back_image:productBack,consent:true});const o=r.observation;if(!o||typeof o.name!=='string'||o.name.length>240||typeof o.label_text!=='string'||o.label_text.length>6000||typeof o.label_readable!=='boolean') throw new Error('Label response was invalid.');observation=o;render();});break;
        }
        case 'save-product': {
          const name=val('product-name'),note=val('product-note');
          const code=val('product-code');
          if(!name||name.length>240||note.length>6000)
            throw new Error('Enter the exact product name from your bottle. Notes are optional.');
          if(code && !validGTIN(code))
            throw new Error('Check the barcode digits, or clear the barcode field to save by name.');
          if(barcodeCandidate?.found && !checked('barcode-review'))
            throw new Error('Confirm the suggested name and exact variant against the real bottle before saving.');
          if(store.inventory.length>=40) throw new Error('Inventory limit reached.');
          store={...store,inventory:[...store.inventory,{
            id:crypto.randomUUID(),name,catalogId:null,note,addedAt:new Date().toISOString(),
            ...(code?{barcode:code}:{})
          }]};
          persist();barcodeScanner?.stop();barcodeCameraActive=false;
          barcodeValue='';barcodeCandidate=null;barcodeStatus='idle';
          productFront='';productBack='';observation=null;
          go('inventory');toast('Product saved locally. It remains unreviewed and cannot authorize cleaner use.');break;
        }
        case 'resolve-active':go('settings');break;
        case 'clear-active':if(!checked('resolve-check')) throw new Error('Read and confirm the interrupted-task check first.');store={...store,active:null};quest=null;persist();render();toast('Warning cleared. This is not a guarantee that the surface is free of product residues.');break;
        case 'delete-data':if(!checked('delete-confirm')) throw new Error('Confirm local data deletion first.');resetStore();setAccessCode('');store=emptyStore();quest=null;captureImage='';productFront='';productBack='';observation=null;mode='practice';render();toast('Local inventory, history and access code deleted.');break;
        case 'export':exportHistory();break;
      }
    }catch(err){toast(err instanceof Error?err.message:'Something went wrong.',true);}
  }
  async function onFile(input:HTMLInputElement):Promise<void> {
    const file=input.files?.[0];if(!file) return;
    try {
      const generation=++uploadGeneration;
      if(input.id==='barcode-photo'){
        barcodeScanner??=new BarcodeScanner();
        barcodeCameraActive=false;barcodeScanner.stop();
        const code=await barcodeScanner.fromPhoto(file);
        if(generation!==uploadGeneration || screen!=='product-scan')return;
        await findBarcodeProduct(code);
        return;
      }
      if(file.size>8_000_000) toast('Optimizing the large photo on this device. Nothing is uploaded without your consent.');
      const img=await normalizePhoto(file);
      if(generation!==uploadGeneration || !input.isConnected) return;
      if(input.id==='photo-file') captureImage=img;
      else if(input.id==='product-front'){productFront=img;ocrFailedForThesePhotos=false;}
      else if(input.id==='product-back'){productBack=img;ocrFailedForThesePhotos=false;}
      if(screen==='product-scan')refreshProductView();
      else render(false);
    } catch(err){toast(err instanceof Error?err.message:'Could not open that photo.',true);}
  }
  export function boot():void {
    root=document.getElementById('app')!;if(!root) return;
    store=readStore();camera=new Camera();render(false);
    root.addEventListener('click',ev=>{const target=(ev.target as Element).closest<HTMLElement>('[data-action]');if(target){ev.preventDefault();void action(target.dataset.action||'',target.dataset.id);}});
    root.addEventListener('change',ev=>{
      const target=ev.target as HTMLInputElement;
      if(target.type==='file')void onFile(target);
      if(target.id==='surface'){
        const detail=root.querySelector<HTMLElement>('#other-surface-field');
        if(detail)detail.hidden=target.value!=='other';
      }
    });
    root.addEventListener('input',ev=>{
      const target=ev.target as HTMLInputElement;
      if(target.id==='product-code'){
        barcodeValue=target.value.trim();
        barcodeCandidate=null;barcodeStatus='idle';
      }
      if(target.id==='product-search'){
        productSearchTerm=target.value;
      }
    });
    window.addEventListener('pagehide',()=>{camera.stop();barcodeScanner?.stop();barcodeCameraActive=false;});
    document.addEventListener('visibilitychange',()=>{
      if(document.hidden){
        camera.stop();barcodeScanner?.stop();barcodeCameraActive=false;
        const pane=root.querySelector<HTMLElement>('#barcode-camera-area');if(pane)pane.hidden=true;
      }
    });
    window.addEventListener('offline',()=>toast('You are offline. Practice, saved arsenal and journal remain available. Live analysis does not.'));
    if(location.protocol!=='file:') {
      const pollHealth=(attempt:number):void=>{
        fetch('/api/health',{cache:'no-store',credentials:'omit',signal:AbortSignal.timeout(5000)}).then(async r=>{
          if(!r.ok)throw new Error('Server health unavailable');
          const h:Health=await r.json();
          if(typeof h.live_ready!=='boolean'||typeof h.version!=='string')throw new Error('Invalid server health state');
          health=h;healthFailed=false;
          if(screen==='product-scan')refreshProductView();
          else if(screen==='home'||(screen==='settings'&&!(document.activeElement instanceof HTMLInputElement)))render(false);
          if(!h.live_ready && h.access_mode==='public_rate_limited' && attempt<3)
            window.setTimeout(()=>pollHealth(attempt+1),attempt===0?6000:12000);
        }).catch(()=>{health=null;healthFailed=true;if(screen==='product-scan')refreshProductView();});
      };
      pollHealth(0);
      // Service-worker registration and safe-update notices live in update-client.js.
    }
  }
  if(typeof document!=='undefined') {
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
  }
}
