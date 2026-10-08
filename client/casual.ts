namespace GQ {
  type CasualStage='home'|'before'|'clean'|'after'|'result'|'wins'|'settings';
  const GAME_URL='https://grimequest-web-production.up.railway.app/';
  const E=escapeHTML;
  const glyphs:Record<string,string>={camera:'M4 7h4l2-3h4l2 3h4v13H4V7Zm8 3a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z',arrow:'M4 12h16m-6-6 6 6-6 6',check:'m5 12 4 4L19 6',star:'m12 3 2.8 5.8 6.4.9-4.6 4.5 1.1 6.4-5.7-3-5.7 3 1.1-6.4-4.6-4.5 6.4-.9Z',lock:'M6 10h12v11H6V10Zm3 0V7a3 3 0 0 1 6 0v3',leaf:'M20 3C10 2 3 7 4 15c1 8 13 8 16-12ZM5 19 16 8',share:'M12 15V3m-4 4 4-4 4 4M4 12v9h16v-9',pause:'M8 5v14M16 5v14'};
  const ico=(key:string)=>`<svg class="gq-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"> <path d="${glyphs[key]||glyphs.star}"/></svg>`;

  /** Public game: fictional foes, actual chores, explicitly self-reported wins.
   * No provider calls, chemical permissions or image recognition occur here.
   * The illustrated demo never enters the scoring/storage path. */
  export class CasualGame {
    private stage:CasualStage='home';
    private data:Store=readStore();
    private camera=new Camera();
    private shot='';
    private quest:Quest|null=null;
    private generation=0;
    private message='';
    private busy=false;
    private resetArmed=false;
    private discardArmed=false;
    private resumeStage:'clean'|'after'='clean';
    private foe:GrimeCreature=monsterProgress(this.data).next;
    private demo=false;
    private previousLevel=1;
    private celebrating=false;
    private newCreature=false;
    private alignment=false;

    constructor(private readonly host:HTMLElement) {}
    start():void {
      this.host.addEventListener('click',event=>{
        const button=(event.target as Element).closest<HTMLElement>('[data-quick]');
        if(!button||button instanceof HTMLButtonElement&&button.disabled)return;
        event.preventDefault();void this.action(button.dataset.quick||'');
      });
      this.host.addEventListener('keydown',event=>{
        if(!this.discardArmed)return;
        if(event.key==='Escape'){event.preventDefault();void this.action('discard-cancel');return;}
        if(event.key==='Tab'){
          const buttons=this.host.querySelectorAll<HTMLButtonElement>('.gq-discard button');
          const first=buttons[0],last=buttons[buttons.length-1];
          if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}
          else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}
        }
      });
      this.host.addEventListener('change',event=>{
        const field=event.target as HTMLInputElement;
        if(field.id==='quick-file')void this.selectFile(field);
      });
      this.host.addEventListener('input',event=>{
        const field=event.target as HTMLInputElement;
        if(field.id==='gq-reveal'){
          const value=Math.max(0,Math.min(100,Number(field.value)||0));
          this.host.querySelector<HTMLElement>('.gq-reveal')?.style.setProperty('--reveal',value+'%');
          field.setAttribute('aria-valuetext',value+' percent of before photo visible');
        }
      });
      window.addEventListener('pagehide',()=>this.camera.stop());
      document.addEventListener('visibilitychange',()=>{if(document.hidden){this.camera.stop();this.setCameraReady(false);} });
      window.addEventListener('beforeunload',event=>{
        if(!this.demo&&(this.quest?.phase==='cleaning'||this.shot)) {event.preventDefault();event.returnValue='';}
      });
      this.render(false);
    }
    private get pending():boolean {return this.quest?.phase==='cleaning';}
    private get before():string {return this.demo?demoScene(false):(this.quest?.before||'');}
    private btn(label:string,action:string,kind='primary',disabled=false):string {
      return `<button type="button" class="gq-button ${kind}" data-quick="${action}"${disabled?' disabled':''}>${label}</button>`;
    }
    private picture(src:string,alt:string,cls=''):string {return `<img class="quick-image ${cls}" src="${E(src)}" alt="${E(alt)}" draggable="false">`;}
    private heading(kicker:string,title:string,description:string):string {
      return `<div class="gq-heading"><p class="gq-eyebrow">${kicker}</p><h1 tabindex="-1">${title}</h1><p>${description}</p></div>`;
    }
    private nav():string {
      return `<header class="gq-nav"><button class="gq-brand" data-quick="home" aria-label="GrimeQuest home"><span class="gq-brand-mark">${ico('star')}</span>grimequest<span class="gq-brand-dot">.</span></button><nav aria-label="Game navigation"><button data-quick="home"${this.stage==='home'?' aria-current="page"':''}>Play</button><button data-quick="wins"${this.stage==='wins'?' aria-current="page"':''}>My wins</button><button class="gq-settings" data-quick="settings" aria-label="About and settings">•••</button></nav></header>`;
    }
    private meter(value:number,max:number,label:string):string {
      return `<progress value="${Math.min(value,max)}" max="${max}" aria-label="${E(label)}">${Math.min(value,max)} / ${max}</progress>`;
    }
    private homeView():string {
      const p=monsterProgress(this.data),next=p.next;
      const opponent=this.pending?this.foe:next;
      return `<section class="gq-home-hero"><div class="gq-hero-copy"><span class="gq-pill">${ico('leaf')} REAL CHORES. LITTLE MONSTERS.</span><h1 tabindex="-1">A little mess.<br><span>A monster to beat.</span></h1><p>Your camera turns a dirty spot into a tiny boss battle. Clean the real mess. Evict the monster.</p><div class="gq-hero-actions">${this.btn(this.pending?'Continue cleaning '+ico('arrow'):ico('camera')+' Find some grime',this.pending?'resume':'start')}${this.pending?this.btn('Discard unfinished quest','discard','text'):this.btn('See a 15-second demo '+ico('arrow'),'demo','text')}</div><p class="gq-private-line">${ico('lock')} No account. No uploads. Just one little win.</p></div><div class="gq-hero-arena" aria-label="Fictional monster for your next cleaning quest"><span class="gq-orbit a">✧</span><span class="gq-orbit b">✦</span><span class="gq-speech">“${E(opponent.taunt)}”</span><div class="gq-hero-monster">${monsterSVG(opponent)}</div><div class="gq-opponent"><span>${opponent.boss?'NEXT UP · BOSS ENCOUNTER':'YOUR NEXT OPPONENT'}</span><strong>${E(opponent.name)}</strong><small>${E(opponent.title)}</small></div><span class="gq-xp-tag">${ico('star')} +300 XP</span></div></section>`+
        (this.data.active?`<aside class="gq-alert"><b>Previous task still active.</b><p>Check the actual product directions before starting another cleaning job.</p>${this.btn('I checked the previous task','old-task-checked','secondary')}</aside>`:'')+
        `<section class="gq-progress-card" aria-label="Your game progress"><div class="gq-level-badge">${ico('star')}<strong>${p.level}</strong></div><div class="gq-level-info"><div><b>Level ${p.level} · ${p.level===1?'Grime rookie':p.level<4?'Grime hunter':'Little legend'}</b><span>${p.xp} XP</span></div>${this.meter(p.levelXP,900,'XP toward the next level')}<small>${900-p.levelXP} XP to your next level · every real win counts</small></div></section>`+
        `<section class="gq-home-bottom"><div class="gq-three"><h2>Less planning. More playing.</h2><div><span>01</span><p><b>Find a spot</b>One before photo. No forms.</p></div><div><span>02</span><p><b>Do your thing</b>No timer. Follow your usual care instructions.</p></div><div><span>03</span><p><b>Claim your win</b>After photo. Monster out. You up.</p></div></div><div class="gq-next-reward"><span class="gq-eyebrow">THE GRIME COLLECTION</span><div class="gq-mini-crew">${GRIME_CREW.slice(0,3).map(c=>`<span class="${p.collected.includes(c.id)?'':'uncollected'}">${monsterSVG(c)}</span>`).join('')}</div><h2>${p.collected.length} of ${GRIME_CREW.length} evicted</h2><p>Every win reveals a new little freeloader. Collect the whole crew.</p>${this.btn('View collection '+ico('arrow'),'wins','text')}</div></section><p class="gq-honesty">The monsters are make-believe. Your progress is self-reported. The chore is real.</p>`;
    }
    private steps(active:number):string {
      return `<ol class="gq-steps" aria-label="Quest progress">${['Find','Clean','Defeat'].map((name,i)=>`<li class="${i===active?'current':i<active?'complete':''}"${i===active?' aria-current="step"':''}><span>${i<active?'✓':i+1}</span>${name}</li>`).join('')}</ol>`;
    }
    private captureView():string {
      const after=this.stage==='after';
      const hasPhoto=Boolean(this.shot);
      return this.steps(after?2:0)+this.heading(after?'ONE LITTLE FINISH':'YOUR QUEST STARTS HERE',after?'Show the glow-up.':'Spot the grime.',after?'Same spot, similar light. Snap it when you’re done.':'Point at one small mess. Big jobs can wait.')+
        `<div class="gq-capture-layout"><div><div class="gq-camera-frame"><section id="quick-camera" class="gq-camera" aria-label="Camera view">${hasPhoto?this.picture(this.shot,after?'After photo preview':'Before photo preview'):`<div class="gq-camera-placeholder">${ico('camera')}<b>Your next little win is here.</b><span>Open the camera or choose a photo below.</span></div>`}</section>${!hasPhoto?'<span class="gq-frame-corner tl"></span><span class="gq-frame-corner tr"></span><span class="gq-frame-corner bl"></span><span class="gq-frame-corner br"></span>':''}${after&&this.alignment&&this.before?`<div class="gq-alignment" aria-hidden="true">${this.picture(this.before,'Before photo alignment guide')}</div>`:''}</div>${after&&this.before?`<div class="gq-align-bar">${this.btn(this.alignment?'Hide alignment guide':'Align with before photo','align','text')}<span>Visual guide only</span></div>`:''}<div class="gq-camera-controls">${hasPhoto?this.btn('Retake photo','retake','text'):this.btn(ico('camera')+' Take photo','snap','primary',true)+`<div class="gq-camera-fallbacks">${this.btn('Open camera','camera','secondary')}<label class="gq-file">Choose photo<input id="quick-file" type="file" accept="image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif" capture="environment"></label></div>`}</div></div><section class="gq-capture-side">${after?`<div class="gq-mini-encounter">${monsterSVG(this.foe)}<p><b>${E(this.foe.name)} is still here.</b><br>Your after photo is the finishing move.</p></div>`:`<div class="gq-capture-note"><span class="gq-note-icon">${ico('leaf')}</span><h2>One spot is enough.</h2><p>A real little chore, not your entire home. No material menus. No cleaner choices.</p></div>`}${hasPhoto?`<div class="gq-next">${after?this.btn('It’s clean! +300 XP '+ico('star'),'claim')+this.btn('Not clean yet','back-clean','secondary'):this.btn('Let’s clean! '+ico('arrow'),'before-ready')}</div>`:''}<p class="gq-private-line">${ico('lock')} Photos stay on this device.</p>${after?`<p class="gq-fineprint">You judge the result. No AI or hygiene claims.</p>`:''}${!after||!hasPhoto?this.btn(after?'← Back to cleaning':'Cancel quest',after?'back-clean':'home','text'):''}</section></div>`;
    }
    private cleaningView():string {
      if(!this.quest&&!this.demo)return this.homeView();
      return this.steps(1)+this.heading(this.foe.boss?'BOSS ENCOUNTER':'MONSTER ENCOUNTERED','Time to clean!',`${E(this.foe.name)} has moved in. Time for a friendly eviction.`)+
        `<div class="gq-battle-layout"><div class="gq-battle-scene">${this.picture(this.before,'Your before photo')}<div class="gq-battle-shade"></div><span class="gq-photo-badge">${this.demo?'ILLUSTRATED DEMO':'YOUR BEFORE PHOTO'}</span><div class="gq-battle-monster">${monsterSVG(this.foe)}</div><span class="gq-battle-quote">“${E(this.foe.taunt)}”</span><span class="gq-fiction-label">Fictional game character · not image recognition</span></div><section class="gq-battle-instructions"><span class="gq-pill">${ico('star')} ${this.demo?'DEMO · NO XP':'+300 XP · ONE REAL CHORE'}</span><h2>A little clean.<br>A little victory.</h2><p>${this.demo?'This is an illustrated walkthrough. No actual cleaning is being shown or verified.':'Set your phone somewhere dry and clean at your own pace. Use a method you already know is suitable for the item.'}</p><div class="gq-no-rush">${ico('pause')} No timer. No perfect-home pressure.</div>${this.btn(this.demo?'Reveal demo result '+ico('arrow'):'Done cleaning '+ico('arrow'),'after')}<p class="gq-care">Follow the actual label and surface-care instructions. Never mix cleaners. Stop if the material or residue is uncertain.</p>${this.btn(this.demo?'Exit demo':'Discard this quest',this.demo?'demo-exit':'discard','text')}</section></div>`;
    }
    private demoAfterView():string {
      return this.steps(2)+this.heading('ILLUSTRATED DEMO · NO XP','Show the glow-up.','In a real quest, this is where you take the after photo.')+this.reveal(demoScene(false),demoScene(true))+this.btn('Defeat demo monster '+ico('star'),'claim')+this.btn('Exit demo','demo-exit','text');
    }
    private reveal(before:string,after:string):string {
      return `<section class="gq-reveal-wrap"><div class="gq-reveal"><div class="gq-reveal-after">${this.picture(after,'After cleaning')}</div><div class="gq-reveal-before">${this.picture(before,'Before cleaning')}</div><span class="gq-photo-badge before-label">BEFORE</span><span class="gq-photo-badge after-label">AFTER</span><span class="gq-reveal-handle" aria-hidden="true">‹ ›</span><input id="gq-reveal" type="range" min="0" max="100" value="50" aria-label="Slide to compare before and after photos" aria-valuetext="50 percent of before photo visible"></div><p class="gq-slider-hint">↔ Slide to see the difference. This is your own visual comparison.</p></section>`;
    }
    private resultView():string {
      if(!this.demo&&this.quest?.phase!=='result')return this.homeView();
      const p=monsterProgress(this.data),after=this.demo?demoScene(true):this.quest?.after||'';
      return `<section class="gq-victory ${this.celebrating?'celebrate':''}">${this.celebrating?`<div class="gq-confetti" aria-hidden="true">${Array.from({length:16},()=>'<i></i>').join('')}</div>`:''}<div class="gq-victory-creature">${monsterSVG(this.foe,'defeated')}<span>${ico('check')}</span></div><div><span class="gq-pill">${this.demo?'DEMO COMPLETE · NO XP':'REAL CHORE. LITTLE VICTORY.'}</span><h1 tabindex="-1">Grime defeated!</h1><p>${this.demo?'Imagine this being your real before and after.':`${E(this.foe.name)} has officially been evicted. By you.`}</p><strong class="gq-xp">${this.demo?'Try it for real':'+300 XP'}</strong></div></section>`+
        (this.demo?'<p class="gq-demo-proof">Illustrated sample only. No points, wins or creatures have been added.</p>':`<p class="gq-report-badge">${ico('check')} Self-reported win · not AI verified</p>`)+this.reveal(this.before,after)+
        (!this.demo?`<div class="gq-reward-row"><section class="gq-unlock">${monsterSVG(this.foe,'defeated')}<div><span class="gq-eyebrow">${this.newCreature?'NEW CREATURE COLLECTED':'ANOTHER LITTLE VICTORY'}</span><b>${E(this.foe.name)}</b><small>${p.collected.length} / ${GRIME_CREW.length} creatures in your collection</small></div></section><section class="gq-result-level"><b>${p.level>this.previousLevel?'Level up! ':''}Level ${p.level}</b>${this.meter(p.levelXP,900,'Progress to your next level')}<small>${p.xp} total XP · ${900-p.levelXP} to level ${p.level+1}</small></section></div>`:'')+
        `<div class="gq-result-actions">${this.btn(this.demo?'Find some real grime '+ico('camera'):'Clean another spot '+ico('arrow'),this.demo?'demo-exit-start':'start')}${this.demo?this.btn('Back to game','demo-exit','secondary'):this.btn(ico('share')+' Share this win','share','secondary')}${!this.demo?this.btn('See my wins','wins','text'):''}</div><p class="gq-gentle">${this.demo?'Your own photos stay on your device.':'One spot is a win. You do not have to clean anything else today.'}</p>`;
    }
    private winsView():string {
      const p=monsterProgress(this.data),items=this.data.history.filter(h=>h.mode==='guided');
      return this.heading('YOUR PROGRESS','Little wins add up.',`${p.xp} XP earned. ${items.filter(h=>h.status==='clear').length} chores reported.`)+
        `<section class="gq-collection"><div class="gq-section-title"><h2>Your grime collection</h2><span>${p.collected.length} / ${GRIME_CREW.length} EVICTED</span></div><p>Six fictional freeloaders. Earn each one by finishing a real little chore.</p><div class="gq-collection-grid">${GRIME_CREW.map((c,i)=>{const has=p.collected.includes(c.id);return `<article class="gq-collection-card ${has?'collected':'locked'}" aria-label="${has?E(c.name)+' collected':'Creature '+(i+1)+' not yet collected'}"><span class="gq-collection-number">0${i+1}</span>${monsterSVG(c,has?'defeated':'idle')}<b>${has?E(c.name):'Mystery freeloader'}</b><small>${has?'EVICTED ✓':c.boss?'THE BOSS AWAITS':'Complete another quest'}</small></article>`;}).join('')}</div></section>`+
        `<section class="gq-journal"><div class="gq-section-title"><h2>Recent wins</h2><span>ON THIS DEVICE</span></div>${items.length?items.slice(0,30).map(h=>{const c=creatureForHistory(h.name);return `<article>${c?monsterSVG(c,'defeated'):`<span class="gq-old-win">${ico('star')}</span>`}<div><b>${E(h.name)}</b><small>${E(new Date(h.date).toLocaleDateString(undefined,{month:'short',day:'numeric'}))} · Self-reported</small></div><strong>${h.xp?'+'+h.xp+' XP':'No XP'}</strong></article>`;}).join(''):'<div class="gq-empty">Your first little victory is waiting. One spot is all it takes.</div>'}</section>`+
        (this.pending?'':this.btn('Find some grime','start'))+'<p class="gq-fineprint">Progress is local to this browser. The latest 200 entries are kept; this is not a verified leaderboard.</p>';
    }
    private settingsView():string {
      return this.heading('LESS SETUP. MORE LITTLE WINS.','Play, not paperwork.','A camera, a tiny chore, and a little motivation.')+
        `<section class="gq-about"><h2>The monsters are pretend.<br>The chore is yours.</h2><p>They are fictional characters chosen by your game progress. GrimeQuest does not identify dirt, materials or cleaning products. It does not inspect your cleaning.</p><h3>Your photos stay yours.</h3><p>Photos stay temporarily in this tab and are never uploaded by the game. Closing or reloading loses unfinished photos. Completed XP and wins stay on this device. Sharing a win sends only text and the app link, not your photos.</p><h3>Real-world care comes first.</h3><p>Follow the actual product and surface instructions. Never mix cleaners. Skip unsafe or uncertain tasks. There is no timer and no hygiene or disinfection claim.</p><p><a href="/privacy.html">Privacy</a> · <a href="/safety.html">Safety</a> · <a href="/update.html">Refresh the installed app</a></p></section>`+
        this.btn('Install / share','install','secondary')+
        (this.resetArmed?`<section class="gq-alert"><b>Delete your local progress?</b><p>Points, wins and old inventory will be removed. This cannot be undone.</p>${this.btn('Yes, delete my local data','reset-confirm','danger')}${this.btn('Keep my progress','reset-cancel','secondary')}</section>`:this.btn('Delete local progress','reset-arm','text'))+this.btn('Back to game','home');
    }
    private render(focus=true):void {
      this.camera.stop();
      const content=this.stage==='home'?this.homeView():this.stage==='before'||this.stage==='after'?(this.demo?this.demoAfterView():this.captureView()):this.stage==='clean'?this.cleaningView():this.stage==='result'?this.resultView():this.stage==='wins'?this.winsView():this.settingsView();
      this.host.innerHTML=`<a class="skip" href="#quick-main">Skip to game</a><div class="monster-game">${this.nav()}${this.demo?`<aside class="gq-demo-banner">ILLUSTRATED DEMO · NO XP ${this.btn('Exit demo','demo-exit','text')}</aside>`:''}${this.pending&&['wins','settings'].includes(this.stage)?`<aside class="gq-resume"><span>Quest in progress. Your photos are still here.</span>${this.btn('Return to cleaning','resume','secondary')}</aside>`:''}${storageWarning?`<p class="gq-alert">${E(storageWarning)}</p>`:''}<main id="quick-main" aria-busy="${this.busy}">${content}</main><p class="quick-message gq-message" role="status" aria-live="polite"${this.message?'':' hidden'}>${E(this.message)}</p>${this.discardArmed?`<section class="gq-discard" role="dialog" aria-label="Discard unfinished quest" aria-modal="true"><div><h2>Leave this little quest?</h2><p>Your unsaved photos will be discarded. You will not lose any earned points.</p>${this.btn('Keep cleaning','discard-cancel')}${this.btn('Discard quest','discard-confirm','secondary')}</div></section>`:''}<footer class="gq-footer"><span>SMALL CHORES. REAL WINS.</span><div><button data-quick="install">Install / share</button><a href="/privacy.html">Privacy</a><a href="/safety.html">Safety</a></div></footer></div>`;
      if(focus){this.host.querySelector<HTMLElement>('h1')?.focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'});}
      if(this.discardArmed)this.host.querySelector<HTMLButtonElement>('[data-quick="discard-cancel"]')?.focus();
      this.celebrating=false;
    }
    private notice(text:string):void {
      this.message=text;
      const p=this.host.querySelector<HTMLElement>('.gq-message');
      if(p){p.textContent=text;p.hidden=!text;}
    }
    private setCameraReady(ready:boolean):void {
      const button=this.host.querySelector<HTMLButtonElement>('[data-quick="snap"]');
      if(button)button.disabled=!ready;
    }
    private async openCamera():Promise<void> {
      if(this.demo||!['before','after'].includes(this.stage)||this.shot)return;
      const host=this.host.querySelector<HTMLElement>('#quick-camera');if(!host)return;
      try{
        await this.camera.start(host);
        if(!host.isConnected||!['before','after'].includes(this.stage))return;
        const video=host.querySelector('video');
        const ready=()=>{if(host.isConnected&&video&&video.readyState>=2&&video.videoWidth>0)this.setCameraReady(true);};
        ready();video?.addEventListener('loadeddata',ready,{once:true});video?.addEventListener('canplay',ready,{once:true});
      }catch{if(host.isConnected&&!this.shot)this.notice('Camera unavailable. Choose a photo instead.');}
    }
    private async selectFile(input:HTMLInputElement):Promise<void> {
      const file=input.files?.[0];if(!file||this.busy||this.demo)return;
      const generation=++this.generation,stage=this.stage;
      this.busy=true;this.host.querySelector('main')?.setAttribute('aria-busy','true');this.camera.stop();
      this.notice('Preparing your photo on this device…');
      try{
        const shot=await normalizePhoto(file);
        if(generation!==this.generation||stage!==this.stage)return;
        this.shot=shot;this.message='';this.busy=false;this.render();
      }catch(err){if(generation===this.generation)this.notice(err instanceof Error?err.message:'Unable to open this photo.');}
      finally{if(generation===this.generation){this.busy=false;this.host.querySelector('main')?.setAttribute('aria-busy','false');}}
    }
    private beginQuest():void {
      if(!this.shot)throw new Error('Take a before photo to start your quest.');
      this.foe=monsterProgress(this.data).next;
      const draft:Quest={id:crypto.randomUUID(),mode:'guided',phase:'identified',name:`Grime defeated · ${this.foe.name}`,room:'My place',before:this.shot,surface:'unknown',soil:'unknown',analysis:{object_name:'Player-selected spot',surface:'unknown',soil:'unknown',visible_soil:true,image_quality:'usable',material_certainty:'unknown',hazards:['none'],target_box:{x:0,y:0,width:1,height:1}}};
      this.quest=transition(draft,{type:'begin-casual'});this.shot='';this.stage='clean';this.resumeStage='clean';
    }
    private claim():void {
      if(this.demo){this.stage='result';this.celebrating=true;return;}
      if(this.quest?.phase!=='cleaning'||!this.shot)throw new Error('Take an after photo of the same spot first.');
      if(this.quest.before===this.shot)throw new Error('Before and after photos are identical. Take a new after photo.');
      const old=monsterProgress(this.data);this.previousLevel=old.level;this.newCreature=!old.collected.includes(this.foe.id);
      const result:Result={encounter_id:this.quest.id,status:'clear',xp:300,provenance:'self_attested',reason:'Player reported visible improvement. Not AI verified or a hygiene claim.'};
      const finished=transition(this.quest,{type:'result',result,after:this.shot});
      this.data=recordResult(this.data,finished);this.quest=finished;this.shot='';this.stage='result';this.celebrating=true;
      if(!saveStore(this.data))this.message='Your win is in this tab only. Browser storage is unavailable.';
    }
    private clearQuest():void {
      this.generation++;this.busy=false;this.demo=false;this.quest=null;this.shot='';this.resumeStage='clean';this.discardArmed=false;this.alignment=false;
    }
    private async share():Promise<void> {
      if(this.demo||this.quest?.phase!=='result')return;
      const payload={title:'GrimeQuest · A little win',text:`I evicted ${this.foe.name} by cleaning one real little spot. +300 XP, self-reported. Your mess could be a monster too.`,url:GAME_URL};
      try{
        if(navigator.share){await navigator.share(payload);return;}
        if(navigator.clipboard?.writeText){await navigator.clipboard.writeText(payload.text+' '+GAME_URL);this.notice('Win text and app link copied. Your photos stay private.');return;}
        this.notice(payload.text+' '+GAME_URL);
      }catch(err){if(!(err instanceof Error&&err.name==='AbortError'))this.notice('Sharing unavailable here. Your win is still saved.');}
    }
    private async action(action:string):Promise<void> {
      if(this.busy&&!['home','discard','discard-confirm','discard-cancel'].includes(action))return;
      try{
        this.notice('');
        switch(action){
          case 'home':
            if(this.busy){this.generation++;this.busy=false;}
            if(this.stage==='after'&&!this.demo)this.resumeStage='after';
            if(this.demo||!this.pending)this.clearQuest();
            this.stage='home';this.render();break;
          case 'wins':case 'settings':
            if(this.stage==='after'&&!this.demo)this.resumeStage='after';
            if(this.demo)this.clearQuest();
            this.stage=action;this.render();break;
          case 'start':case 'demo-exit-start':
            if(this.pending)throw new Error('Finish or discard your current quest first.');
            if(this.data.active)throw new Error('Check the previous cleaning task first. Follow its real product label.');
            this.clearQuest();this.foe=monsterProgress(this.data).next;this.stage='before';this.render();void this.openCamera();break;
          case 'demo':
            if(this.pending)throw new Error('Finish your current quest before trying the demo.');
            this.clearQuest();this.demo=true;this.foe=GRIME_CREW[0]!;this.stage='clean';this.render();break;
          case 'demo-exit':this.clearQuest();this.stage='home';this.render();break;
          case 'camera':void this.openCamera();break;
          case 'snap':if(!this.demo&&['before','after'].includes(this.stage)){this.shot=this.camera.capture();this.render();}break;
          case 'retake':if(!this.demo&&['before','after'].includes(this.stage)){this.shot='';this.render();void this.openCamera();}break;
          case 'before-ready':if(this.stage==='before'&&!this.demo){this.beginQuest();this.render();}break;
          case 'after':if(this.stage==='clean'&&(this.pending||this.demo)){this.shot='';this.stage='after';this.resumeStage='after';this.alignment=false;this.render();if(!this.demo)void this.openCamera();}break;
          case 'back-clean':if(this.pending){this.shot='';this.stage='clean';this.resumeStage='clean';this.render();}break;
          case 'claim':if(this.stage==='after'){this.claim();this.render();}break;
          case 'align':
            if(this.stage!=='after'||this.demo||!this.before)return;
            this.alignment=!this.alignment;
            const frame=this.host.querySelector('.gq-camera-frame');
            this.host.querySelector('.gq-alignment')?.remove();
            if(this.alignment)frame?.insertAdjacentHTML('beforeend',`<div class="gq-alignment" aria-hidden="true">${this.picture(this.before,'Before photo alignment guide')}</div>`);
            const button=this.host.querySelector<HTMLButtonElement>('[data-quick="align"]');if(button)button.textContent=this.alignment?'Hide alignment guide':'Align with before photo';
            break;
          case 'resume':if(this.pending){this.stage=this.resumeStage;this.render();if(this.stage==='after'&&!this.shot)void this.openCamera();}break;
          case 'discard':if(this.pending||this.shot){this.discardArmed=true;this.render();}else{this.clearQuest();this.stage='home';this.render();}break;
          case 'discard-cancel':this.discardArmed=false;this.render();break;
          case 'discard-confirm':if(this.discardArmed){this.clearQuest();this.stage='home';this.render();}break;
          case 'old-task-checked':this.data={...this.data,active:null};saveStore(this.data);this.render();break;
          case 'share':await this.share();break;
          case 'install':window.dispatchEvent(new Event('grimequest:show-install'));break;
          case 'reset-arm':this.resetArmed=true;this.render();break;
          case 'reset-cancel':this.resetArmed=false;this.render();break;
          case 'reset-confirm':if(this.resetArmed){resetStore();setAccessCode('');this.data=emptyStore();saveStore(this.data);this.clearQuest();this.resetArmed=false;this.stage='home';this.render();}break;
        }
      }catch(err){this.notice(err instanceof Error?err.message:'Something went wrong. Try again.');}
    }
  }
}
