namespace GQ {
  export interface GrimeCreature { id:string; name:string; title:string; taunt:string; color:string; shape:string; boss:boolean; }
  // Original fictional characters. Sequence depends on game history, NOT image recognition.
  export const GRIME_CREW: readonly GrimeCreature[] = [
    {id:'smudgie',name:'Smudgie',title:'The tiny freeloader',taunt:'I was just getting comfortable.',color:'mint',shape:'blob',boss:false},
    {id:'dusty',name:'Dusty',title:'Professional shelf squatter',taunt:'You cannot see me. Probably.',color:'lilac',shape:'fuzz',boss:false},
    {id:'crumb',name:'Crumb Goblin',title:'Keeper of the last crumbs',taunt:'These crumbs are my kingdom.',color:'peach',shape:'horn',boss:false},
    {id:'splodge',name:'Splodge',title:'A splash of mischief',taunt:'Call it modern art.',color:'blue',shape:'drop',boss:false},
    {id:'grubble',name:'Grubble',title:'Master of doing nothing',taunt:'We could both do this tomorrow.',color:'rose',shape:'round',boss:false},
    {id:'lord-grime',name:'Lord Grime',title:'The final boss of small chores',taunt:'All this effort. For a little spot?',color:'gold',shape:'crown',boss:true}
  ];
  export function creatureForHistory(name:string):GrimeCreature|undefined {
    return GRIME_CREW.find(c=>name===`Grime defeated · ${c.name}`);
  }
  export function monsterProgress(store:Store,now=new Date()):{defeated:number;collected:string[];next:GrimeCreature;today:number;level:number;xp:number;levelXP:number} {
    const completed=store.history.filter(h=>h.mode==='guided'&&h.status==='clear');
    const monsterWins=completed.filter(h=>creatureForHistory(h.name)!==undefined);
    const collected=GRIME_CREW.filter(c=>monsterWins.some(h=>creatureForHistory(h.name)?.id===c.id)).map(c=>c.id);
    const day=(d:Date)=>`${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
    const today=completed.filter(h=>day(new Date(h.date))===day(now)).length;
    const xp=completed.reduce((total,h)=>total+h.xp,0);
    return {defeated:monsterWins.length,collected,next:GRIME_CREW[monsterWins.length%GRIME_CREW.length]!,today,level:Math.floor(xp/900)+1,xp,levelXP:xp%900};
  }
  export function monsterSVG(c:GrimeCreature,pose:'idle'|'defeated'='idle'):string {
    const shapes:Record<string,string>={
      blob:'M48 179C27 144 45 109 63 94C61 61 91 38 119 46C148 25 184 43 189 76C220 88 228 124 214 147C236 183 200 211 175 202C146 221 107 209 89 205C59 220 33 203 48 179Z',
      fuzz:'M40 160L24 139L46 126L29 103L58 97L48 71L76 72L81 41L106 57L127 26L145 52L172 36L179 67L207 66L205 91L231 106L217 128L235 150L211 163L216 190L188 192L176 218L149 204L127 228L110 208L78 218L74 195L45 192Z',
      horn:'M55 105L38 43L91 67Q130 38 169 67L219 40L205 107Q233 159 201 195Q173 218 127 209Q74 220 48 185Q30 144 55 105Z',
      drop:'M129 27C121 48 106 67 76 91C35 122 37 162 56 188C80 221 178 222 203 186C229 149 211 105 174 80C157 68 135 39 129 27Z',
      round:'M42 124C34 76 77 45 126 45C185 40 221 80 217 127C232 174 201 214 160 208C136 222 99 211 81 212C44 211 24 172 42 124Z',
      crown:'M44 110L41 59L81 79L111 32L140 74L185 43L196 101C220 116 229 145 213 176C208 208 158 218 128 208C81 220 43 199 42 173C24 156 27 130 44 110Z'
    };
    const eyes=pose==='defeated'?'<path d="M85 126q12 13 24 0M151 126q12 13 24 0" fill="none" stroke="#173d32" stroke-width="7" stroke-linecap="round"/>':
      '<ellipse cx="98" cy="120" rx="17" ry="22" fill="#fffdf2"/><ellipse cx="161" cy="120" rx="17" ry="22" fill="#fffdf2"/><ellipse cx="102" cy="125" rx="7" ry="10" fill="#173d32"/><ellipse cx="157" cy="125" rx="7" ry="10" fill="#173d32"/><circle cx="104" cy="122" r="2" fill="white"/><circle cx="159" cy="122" r="2" fill="white"/>';
    return `<svg class="gq-creature creature-${c.color} pose-${pose}" viewBox="0 0 260 250" aria-hidden="true" focusable="false"><ellipse cx="130" cy="226" rx="75" ry="10" fill="#173d32" opacity=".09"/><path class="gq-monster-body" d="${shapes[c.shape]||shapes.blob}"/><path d="M74 178q-15 21-26 7M184 177q13 25 30 11" fill="none" class="gq-monster-limb" stroke-width="14" stroke-linecap="round"/>${eyes}<ellipse cx="73" cy="146" rx="12" ry="7" fill="#f4a18f" opacity=".5"/><ellipse cx="186" cy="146" rx="12" ry="7" fill="#f4a18f" opacity=".5"/><path d="M111 162q19 18 37-1" fill="none" stroke="#173d32" stroke-width="6" stroke-linecap="round"/><path d="M78 88q3-17 22-21" fill="none" stroke="white" opacity=".35" stroke-width="10" stroke-linecap="round"/>${c.boss?'<path d="M82 70l15-25 28 23 25-32 24 26-9 25H92Z" fill="#f5b938" stroke="#906b1c" stroke-width="3"/><circle cx="129" cy="65" r="5" fill="#fff3bc"/>':''}</svg>`;
  }
  export function demoScene(clean:boolean):string {
    const dirt=clean?'': '<g fill="#bd885e" opacity=".66"><ellipse cx="205" cy="235" rx="83" ry="30" transform="rotate(-17 205 235)"/><circle cx="284" cy="298" r="15"/><circle cx="144" cy="317" r="12"/><ellipse cx="386" cy="191" rx="34" ry="18"/><circle cx="420" cy="243" r="9"/></g>';
    const shine=clean?'<g stroke="#709a71" stroke-width="4" stroke-linecap="round"><path d="M265 181v29m-15-15h30M377 279v22m-11-11h22"/></g>':'';
    return 'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480" viewBox="0 0 640 480"><rect width="640" height="480" fill="#e5eddf"/><path d="M0 120h640M0 240h640M0 360h640M160 0v480M320 0v480M480 0v480" stroke="#d0ddc9" stroke-width="4"/><ellipse cx="506" cy="354" rx="110" ry="19" fill="#bccdb3"/><path d="M429 280l112-13 37 63-138 24Z" fill="#b8d483"/><path d="M432 280l15 41 126-14" fill="none" stroke="#d3e5b7" stroke-width="9"/>${dirt}${shine}<rect x="18" y="18" width="167" height="29" rx="14" fill="#173d32" opacity=".85"/><text x="102" y="38" font-family="sans-serif" font-size="12" text-anchor="middle" fill="white">ILLUSTRATED DEMO</text></svg>`);
  }
}
