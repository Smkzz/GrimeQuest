namespace GQ {
  const STORE_KEY='grimequest.v1';
  export let storageWarning='';
  export function readStore(): Store {
    try {
      const value=localStorage.getItem(STORE_KEY);
      if(!value) return emptyStore();
      if(value.length>3_500_000) throw new Error('Local data is too large.');
      const parsed=safeStore(JSON.parse(value));
      if(!parsed) throw new Error('Local data format is invalid.');
      return parsed;
    } catch {
      storageWarning='Saved data could not be read. This session starts empty; the original data is not overwritten until you explicitly reset it.';
      return emptyStore();
    }
  }
  export function saveStore(store: Store): boolean {
    if(storageWarning) return false;
    try {localStorage.setItem(STORE_KEY,JSON.stringify(store)); return true;}
    catch {storageWarning='Browser storage is unavailable or full. Progress is kept only in this tab.';return false;}
  }
  export function resetStore(): void {
    try {localStorage.removeItem(STORE_KEY);} catch {/* Storage may be denied. */}
    storageWarning='';
  }
  export function getAccessCode(): string {
    try {return sessionStorage.getItem('grimequest.access')||'';} catch{return '';}
  }
  export function setAccessCode(value:string): boolean {
    try {sessionStorage.setItem('grimequest.access',value);return true;} catch{return false;}
  }
}
