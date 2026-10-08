namespace GQ {
  export const surfaceNames: Record<Surface, string> = {
    uncoated_glass: 'Ordinary uncoated glass', glazed_ceramic: 'Sound glazed ceramic', stainless_steel: 'Stainless steel',
    glass_ceramic_hob: 'Glass-ceramic hob (cool, switched off)', natural_stone: 'Natural stone', wood: 'Wood', other: 'Another known material', unknown: "I'm not sure what it is"
  };
  export const soilNames: Record<Soil, string> = {
    grease: 'Light grease / food spill', fingerprints: 'Fingerprints', light_grime: 'Light visible grime', limescale: 'Limescale / mineral deposits', unknown: "I'm not sure"
  };
  export const scenarios: Scenario[] = [
    {id:'kitchen', name:'The grease gremlin', room:'Kitchen', subtitle:'A little splashback rescue.', surface:'glazed_ceramic', soil:'grease', color:'peach', before:'assets/kitchen-before.svg', after:'assets/kitchen-after.svg', partial:'assets/kitchen-partial.svg'},
    {id:'glass', name:'The smudge sprite', room:'Living room', subtitle:'Give the view a fresh start.', surface:'uncoated_glass', soil:'fingerprints', color:'mint', before:'assets/glass-before.svg', after:'assets/glass-after.svg', partial:'assets/glass-partial.svg'},
    {id:'mystery', name:'The mystery surface', room:'Safety check', subtitle:'Sometimes the right move is to stop.', surface:'unknown', soil:'light_grime', color:'lavender', before:'assets/mystery-before.svg', after:'assets/mystery-before.svg', partial:'assets/mystery-before.svg'}
  ];
  export function allConfirmed(): Attestations {
    return {exact_product:true, label_allows_target:true, surface_care_allows:true, no_other_product:true, cool_and_safe:true};
  }
  export function matchProduct(surface: Surface, soil: Soil, productId: string, a: Attestations, hazards: string[], today = new Date().toISOString().slice(0,10)): Match {
    const no = (status: Match['status'], code: string, reason: string): Match => ({status,code,reason,product_id:productId});
    if(hazards.some(h=>h!=='none')) return no('blocked','HAZARD',"A possible hazard was identified. This job is outside the prototype's scope.");
    if(['unknown','other'].includes(surface)) return no('uncertain','SURFACE_UNSUPPORTED','The reviewed product catalog cannot verify this material. An independent guided method is not a product recommendation.');
    if(['unknown','limescale'].includes(soil)) return no('uncertain','SOIL_UNSUPPORTED','This soil needs a procedure that is not in the reviewed catalog.');
    const p = products.find(p=>p.id===productId);
    if(!p?.enabled) return no('uncertain','PRODUCT_UNREVIEWED','No reviewed entry for this exact product. A scanned label alone does not establish suitability.');
    if(today > catalog.valid_until) return no('uncertain','CATALOG_STALE','The reference catalog needs review before it can suggest products.');
    if(p.excluded.includes(surface)||!p.surfaces.includes(surface)) return no('blocked','OUTSIDE_SCOPE','This product is not enabled for the selected surface. This is not a claim that it is chemically incompatible.');
    if(!p.soils.includes(soil)) return no('uncertain','NO_SOIL_EVIDENCE','The catalog does not establish this product as a match for that visible soil.');
    if(!['exact_product','label_allows_target','surface_care_allows','no_other_product','cool_and_safe'].every(k=>a[k as keyof Attestations]===true)) return no('uncertain','CONFIRMATIONS_REQUIRED','Confirm the exact bottle, current label, surface care, absence of other cleaners and a cool, safe target.');
    return {status:'eligible',code:'LABEL_MATCH',reason:"Conditional label match within this prototype's narrow scope. Follow the current package and surface-care instructions.",product_id:productId,source:p.source,steps:p.steps};
  }
  export const GUIDED_METHOD_ID='guided-user-method';
  export function validOtherMaterial(value:unknown):value is string {
    return typeof value==='string' && value.trim().length>=3 && value.trim().length<=80 &&
      /\p{L}/u.test(value) && !/[\p{C}]/u.test(value);
  }
  // Guided play records the player's own method, not chemical-product approval.
  // "Unknown" and observed hazards stay stopped until the target is identified.
  export function guidedTargetSupported(surface:Surface,soil:Soil,hazards:string[],surfaceDetail?:string):boolean {
    return Object.prototype.hasOwnProperty.call(surfaceNames,surface) && surface!=='unknown' &&
      (surface!=='other'||validOtherMaterial(surfaceDetail)) &&
      Object.prototype.hasOwnProperty.call(soilNames,soil) && soil!=='unknown' &&
      hazards.length===1 && hazards[0]==='none';
  }
  export type QuestEvent = {type:'confirm';surface:Surface;soil:Soil} | {type:'equip'; productId:string} | {type:'equip-guided'} | {type:'start'} | {type:'result';result:Result;after:string} | {type:'retry'};
  export function transition(q: Quest, event: QuestEvent): Quest {
    if(event.type==='confirm' && q.phase==='identified') {
      if(!q.analysis.visible_soil || q.analysis.image_quality!=='usable') throw new Error('A usable before photo and visible target are required.');
      return {...q,phase:'confirmed',surface:event.surface,soil:event.soil};
    }
    if(event.type==='equip-guided' && q.mode==='guided' && (q.phase==='confirmed'||q.phase==='equipped')) {
      if(!guidedTargetSupported(q.surface,q.soil,q.analysis.hazards,q.surfaceDetail)) throw new Error('Identify the material and visible problem, and stop for any hazard before using your own care-checked method.');
      return {...q,phase:'equipped',productId:GUIDED_METHOD_ID};
    }
    if(event.type==='equip' && (q.phase==='confirmed'||q.phase==='equipped')) {
      const m=matchProduct(q.surface,q.soil,event.productId,allConfirmed(),q.analysis.hazards);
      if(m.status!=='eligible') throw new Error(m.reason);
      return {...q,phase:'equipped',productId:event.productId};
    }
    if(event.type==='start' && q.phase==='equipped' && q.productId) return {...q,phase:'cleaning'};
    if(event.type==='result' && q.phase==='cleaning') {
      if(event.result.encounter_id!==q.id) throw new Error('Result does not belong to this quest.');
      if(q.mode==='live' && !['model_observation','deterministic_guard'].includes(event.result.provenance)) throw new Error('Live quests require an actual server observation or deterministic guard.');
      if(q.mode==='guided' && event.result.provenance!=='self_attested') throw new Error('Guided camera quests require an explicitly self-reported result.');
      if(q.mode==='practice' && event.result.provenance!=='practice_fixture') throw new Error('Only simulated outcomes can be used in practice mode.');
      if(event.result.status==='clear' && q.mode==='live' && !event.result.receipt) throw new Error('Missing completion receipt.');
      return {...q,phase:'result',result:event.result,after:event.after};
    }
    if(event.type==='retry' && q.phase==='result' && q.result?.status!=='clear') return {...q,phase:'cleaning',result:undefined,after:undefined};
    throw new Error('Invalid quest transition. Start from the previous step.');
  }
  export function emptyStore(): Store {return {version:1,history:[],inventory:[],active:null};}
  export function recordResult(store: Store, quest: Quest, now = new Date().toISOString()): Store {
    if(quest.phase!=='result'||!quest.result) throw new Error('No result to record.');
    const r=quest.result;
    if(r.encounter_id!==quest.id) throw new Error('Mismatched result.');
    if(quest.mode==='live' && !['model_observation','deterministic_guard'].includes(r.provenance)) throw new Error('Self-reported or practice outcomes cannot award live XP.');
    if(quest.mode==='guided' && r.provenance!=='self_attested') throw new Error('Guided outcomes must be marked self-reported.');
    if(quest.mode==='practice' && r.provenance!=='practice_fixture') throw new Error('Only simulated outcomes can award practice XP.');
    if(quest.mode==='live' && r.status==='clear' && !r.receipt) throw new Error('Receipt required.');
    const existing=store.history.find(h=>h.id===quest.id && h.mode===quest.mode);
    if(existing?.status==='clear') return store;
    const xp=r.status==='clear'?300:0; // The client never trusts a model-provided numeric reward.
    const item: HistoryItem={id:quest.id,name:quest.name,room:quest.room,mode:quest.mode,status:r.status,xp,date:now,...(r.receipt?{receipt:r.receipt}:{})};
    const others=store.history.filter(h=>h.id!==quest.id||h.mode!==quest.mode);
    return {...store,history:[item,...others].slice(0,200),active:r.status==='clear'?null:store.active};
  }
  export function stats(store: Store, mode: Mode): {xp:number;clears:number;level:number} {
    const items=store.history.filter(h=>h.mode===mode && h.status==='clear');
    const xp=items.reduce((sum,h)=>sum+h.xp,0);
    return {xp,clears:items.length,level:Math.floor(xp/900)+1};
  }
  export function escapeHTML(value: unknown): string {
    return String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c] ?? c));
  }
  export function isSurface(v: unknown): v is Surface {return typeof v==='string' && Object.prototype.hasOwnProperty.call(surfaceNames,v);}
  export function isSoil(v: unknown): v is Soil {return typeof v==='string' && Object.prototype.hasOwnProperty.call(soilNames,v);}
  export function safeStore(raw: unknown): Store | null {
    if(!raw || typeof raw!=='object') return null;
    const s=raw as Record<string,unknown>;
    if(s.version!==1 || !Array.isArray(s.history)||!Array.isArray(s.inventory)||s.history.length>200||s.inventory.length>40) return null;
    const str=(v:unknown,max:number)=>typeof v==='string' && v.length<=max;
    if(!s.history.every((h:HistoryItem)=>h && str(h.id,100)&&str(h.name,240)&&str(h.room,100)&&['practice','live','guided'].includes(h.mode)&&['clear','partial','unverifiable'].includes(h.status)&&h.xp===(h.status==='clear'?300:0)&&str(h.date,40)&&Number.isFinite(Date.parse(h.date))&&(!h.receipt||str(h.receipt,14000))&&(h.mode!=='live'||h.status!=='clear'||typeof h.receipt==='string'&&h.receipt.length>20))) return null;
    const keys=s.history.map((h:HistoryItem)=>h.mode+':'+h.id);
    if(new Set(keys).size!==keys.length) return null;
    if(!s.inventory.every((i:InventoryItem)=>i&&str(i.id,100)&&str(i.name,240)&&(i.catalogId===null||str(i.catalogId,100))&&str(i.note,6000)&&str(i.addedAt,40)&&(i.barcode===undefined||typeof i.barcode==='string'&&validGTIN(i.barcode)))) return null;
    if(s.active!==null) {
      if(!s.active||typeof s.active!=='object') return null;
      const a=s.active as Record<string,unknown>;
      if(!str(a.product,240)||!str(a.startedAt,40)) return null;
    }
    return {version:1,history:s.history as HistoryItem[],inventory:s.inventory as InventoryItem[],active:s.active as Store['active']};
  }
  export function validateAnalysis(raw: unknown): raw is Analysis {
    if(!raw||typeof raw!=='object') return false;
    const a=raw as Analysis;
    return typeof a.object_name==='string' && a.object_name.length<=240 && isSurface(a.surface) && isSoil(a.soil) && typeof a.visible_soil==='boolean' && ['usable','unusable'].includes(a.image_quality) && ['tentative','unknown'].includes(a.material_certainty) && !!a.target_box && ['x','y','width','height'].every(k=>typeof a.target_box[k as keyof Analysis['target_box']]==='number' && Number.isFinite(a.target_box[k as keyof Analysis['target_box']])) && a.target_box.x>=0 && a.target_box.y>=0 && a.target_box.width>0 && a.target_box.height>0 && a.target_box.x+a.target_box.width<=1.001 && a.target_box.y+a.target_box.height<=1.001 && Array.isArray(a.hazards) && a.hazards.length>0 && a.hazards.length<=6 && a.hazards.every(h=>['none','heat','electrical','mould','body_fluid','unknown_chemical','damage'].includes(h));
  }
  export function validateResult(raw: unknown): raw is Result {
    if(!raw||typeof raw!=='object') return false;
    const r=raw as Result;
    return typeof r.encounter_id==='string' && r.encounter_id.length<=100 && ['clear','partial','unverifiable'].includes(r.status) && typeof r.reason==='string' && r.reason.length<1500 && ['practice_fixture','model_observation','deterministic_guard','self_attested'].includes(r.provenance) && typeof r.xp==='number' && r.xp===(r.status==='clear'?300:0) && (!r.receipt||typeof r.receipt==='string'&&r.receipt.length<=14000);
  }
}
