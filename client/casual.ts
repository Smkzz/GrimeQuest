namespace GQ {
  type CasualStage = 'home' | 'before' | 'clean' | 'after' | 'result' | 'wins' | 'settings';

  // The shipped game records a player's visible progress. It neither
  // identifies materials nor authorizes a cleaning product or technique.
  // Legacy matching logic remains isolated for data/migration compatibility.
  export class CasualGame {
    private stage: CasualStage = 'home';
    private data: Store = readStore();
    private camera = new Camera();
    private shot = '';
    private quest: Quest | null = null;
    private uploadGeneration = 0;
    private message = '';
    private busy = false;
    private resetArmed = false;

    constructor(private readonly host: HTMLElement) {}

    start(): void {
      this.host.addEventListener('click', event => {
        const el = (event.target as Element).closest<HTMLElement>('[data-quick]');
        if (!el) return;
        event.preventDefault();
        void this.action(el.dataset.quick || '');
      });
      this.host.addEventListener('change', event => {
        const input = event.target as HTMLInputElement;
        if (input.id === 'quick-file') void this.selectFile(input);
      });
      window.addEventListener('pagehide', () => this.camera.stop());
      document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
          this.camera.stop();
          const button = this.host.querySelector<HTMLButtonElement>('[data-quick="snap"]');
          if (button) button.disabled = true;
        }
      });
      this.render();
    }

    private get progress(): { xp: number; clears: number; level: number } {
      return stats(this.data, 'guided');
    }
    private cleanStatus(): string {
      return 'Your result is self-reported, not AI verified. Always follow the real product and surface-care instructions. Never mix cleaners.';
    }
    private nav(): string {
      return '<header class="quick-header"><button class="quick-brand" data-quick="home" aria-label="GrimeQuest home">✦ grimequest<span>.</span></button>' +
        '<nav aria-label="Game navigation"><button data-quick="home" class="' + (this.stage === 'home' ? 'active' : '') + '">Play</button>' +
        '<button data-quick="wins" class="' + (this.stage === 'wins' ? 'active' : '') + '">My wins</button>' +
        '<button data-quick="settings" aria-label="About and settings">⋯</button></nav></header>';
    }
    private btn(text: string, action: string, secondary = false, disabled = false): string {
      return '<button type="button" class="quick-btn ' + (secondary ? 'quick-secondary' : '') +
        '" data-quick="' + action + '"' + (disabled ? ' disabled' : '') + '>' + text + '</button>';
    }
    private homeView(): string {
      const p = this.progress;
      const legacyWarning = this.data.active
        ? '<div class="quick-warning"><b>Previous task still active.</b> Follow its actual product instructions before starting another cleaning job.' +
          this.btn('I checked the previous task', 'old-task-checked', true) + '</div>'
        : '';
      return '<section class="quick-hero"><p class="quick-eyebrow">A TINY QUEST FOR A REAL CHORE</p>' +
        '<div class="quick-mascot" aria-hidden="true">✦</div>' +
        '<h1 tabindex="-1">A little mess.<br><em>Big little win.</em></h1>' +
        '<p>Point your camera at the grime. Clean it. Snap the result. Get points.</p>' +
        this.btn('📸  Find some grime', 'start') +
        '<p class="quick-note">No account. No setup. No product menus.</p></section>' +
        '<section class="quick-stats" aria-label="Your game progress"><div><strong>' + p.xp + '</strong><span>XP earned</span></div>' +
        '<div><strong>' + p.clears + '</strong><span>Little wins</span></div>' +
        '<div><strong>' + p.level + '</strong><span>Level</span></div></section>' +
        legacyWarning +
        '<section class="quick-how"><b>3 tiny steps</b><div><span>1</span>Snap the dirt</div>' +
        '<div><span>2</span>Clean at your own pace</div><div><span>3</span>Snap again & collect XP</div></section>';
    }

    private imageView(url: string, label: string): string {
      return '<img class="quick-image" src="' + escapeHTML(url) + '" alt="' + escapeHTML(label) + '">';
    }
    private captureView(): string {
      const after = this.stage === 'after';
      return '<section class="quick-step"><p class="quick-eyebrow">' + (after ? 'STEP 3 OF 3' : 'STEP 1 OF 3') + '</p>' +
        '<h1 tabindex="-1">' + (after ? 'Show the glow-up.' : 'Spot the grime.') + '</h1>' +
        '<p>' + (after ? 'Take a photo of the same spot after cleaning.' : 'Point at one dirty spot and snap a before photo.') + '</p></section>' +
        (after && this.quest ? '<details class="quick-before-ref"><summary>See before photo</summary>' +
          this.imageView(this.quest.before, 'Original dirty spot') + '</details>' : '') +
        '<section class="quick-camera" id="quick-camera" aria-label="Camera view">' +
        (this.shot ? this.imageView(this.shot, after ? 'After photo preview' : 'Before photo preview') :
          '<div class="quick-placeholder"><span aria-hidden="true">⌾</span><b>Camera preview</b><small>Or choose a photo below</small></div>') +
        '</section>' +
        '<div class="quick-camera-actions">' +
        (this.shot ?
          this.btn('↻ Retake', 'retake', true) :
          this.btn('📸 Take photo', 'snap', false, true) +
          this.btn('Open camera', 'camera', true) +
          '<label class="quick-file">Choose photo<input id="quick-file" type="file" accept="image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif" capture="environment"></label>') +
        '</div>' +
        (this.shot ? '<div class="quick-next">' +
          (after ? this.btn('✨ It’s clean! +300 XP', 'claim') + this.btn('Not clean yet', 'back-clean', true) :
            this.btn('Let’s clean!', 'before-ready')) + '</div>' : '') +
        '<div class="quick-bottom">' + this.btn(after ? '← Back to cleaning' : 'Cancel quest', after ? 'back-clean' : 'home', true) + '</div>';
    }

    private cleaningView(): string {
      if (!this.quest) return this.homeView();
      return '<section class="quick-step"><p class="quick-eyebrow">STEP 2 OF 3</p>' +
        '<h1 tabindex="-1">Time to clean!</h1><p>Do your thing. No timer, no rush.</p></section>' +
        '<div class="quick-before-preview">' + this.imageView(this.quest.before, 'Your before photo') + '<span>BEFORE</span></div>' +
        '<section class="quick-clean-cta"><div class="quick-mascot small" aria-hidden="true">✧</div>' +
        '<p>Use a method you already know is suitable for this item. The game does not choose a cleaner for you.</p>' +
        this.btn('Done cleaning →', 'after') + '</section>' +
        '<p class="quick-safety">Never mix cleaners. Follow the actual label and surface-care instructions. Stop if the material or residue is uncertain.</p>' +
        this.btn('Start over', 'home', true);
    }

    private resultView(): string {
      if (!this.quest || this.quest.phase !== 'result') return this.homeView();
      const p = this.progress;
      return '<section class="quick-victory"><p class="quick-eyebrow">QUEST COMPLETE</p>' +
        '<div class="quick-mascot" aria-hidden="true">★</div>' +
        '<h1 tabindex="-1">Grime defeated!</h1><strong class="quick-xp">+300 XP</strong>' +
        '<p>You said the spot looks clean. Nice little win!</p></section>' +
        '<div class="quick-comparison"><figure>' + this.imageView(this.quest.before, 'Before cleaning') +
        '<figcaption>BEFORE</figcaption></figure><figure>' +
        this.imageView(this.quest.after || '', 'After cleaning') + '<figcaption>AFTER</figcaption></figure></div>' +
        '<p class="quick-note">Self-reported progress, not AI verification or a hygiene measurement.</p>' +
        '<p class="quick-level">Total: ' + p.xp + ' XP · Level ' + p.level + '</p>' +
        this.btn('Clean another spot', 'start') +
        this.btn('See my wins', 'wins', true);
    }

    private winsView(): string {
      const items = this.data.history.filter(h => h.mode === 'guided');
      const p = this.progress;
      return '<section class="quick-step"><p class="quick-eyebrow">YOUR PROGRESS</p><h1 tabindex="-1">Little wins add up.</h1>' +
        '<p>' + p.xp + ' XP · ' + p.clears + ' completed quests</p></section>' +
        (items.length ? '<section class="quick-wins">' +
          items.map(item => '<article><span aria-hidden="true">✦</span><div><b>' + escapeHTML(item.name) +
            '</b><small>' + escapeHTML(item.date.slice(0, 10)) + ' · Self-reported</small></div>' +
            '<strong>' + (item.xp ? '+' + item.xp + ' XP' : 'No XP') + '</strong></article>').join('') +
          '</section>' : '<p class="quick-empty">No wins yet. Your first little victory is waiting!</p>') +
        this.btn('Find some grime', 'start');
    }

    private settingsView(): string {
      return '<section class="quick-step"><p class="quick-eyebrow">THE SIMPLE RULES</p><h1 tabindex="-1">Play, not paperwork.</h1>' +
        '<p>No account, product menus, or AI setup. Take before and after photos, then tell us if you cleaned it.</p></section>' +
        '<section class="quick-how"><b>Good to know</b><p>' + this.cleanStatus() + '</p>' +
        '<p>Photos stay temporarily in this browser tab and are not uploaded in the casual game. Your points and wins are saved on this device.</p>' +
        '<p><a href="/privacy.html">Privacy</a> · <a href="/safety.html">Safety</a> · <a href="/update.html">Refresh the installed app</a></p></section>' +
        this.btn('Install / share', 'install', true) +
        (this.resetArmed ?
          '<div class="quick-warning"><p>Delete local GrimeQuest progress, history and old inventory data? This cannot be undone.</p>' +
          this.btn('Yes, delete my local data', 'reset-confirm', true) +
          this.btn('Keep my progress', 'reset-cancel', true) + '</div>' :
          this.btn('Delete local progress', 'reset-arm', true)) +
        this.btn('Back to game', 'home');
    }

    private render(): void {
      this.camera.stop();
      const content = this.stage === 'home' ? this.homeView() :
        this.stage === 'before' || this.stage === 'after' ? this.captureView() :
        this.stage === 'clean' ? this.cleaningView() :
        this.stage === 'result' ? this.resultView() :
        this.stage === 'wins' ? this.winsView() : this.settingsView();
      this.host.innerHTML = '<a class="skip" href="#quick-main">Skip to game</a><div class="quick-app">' +
        this.nav() + (storageWarning ? '<p class="quick-warning">' + escapeHTML(storageWarning) + '</p>' : '') +
        '<main id="quick-main">' + content + '</main>' +
        (this.message ? '<p class="quick-message" role="status">' + escapeHTML(this.message) + '</p>' : '') +
        '<footer class="quick-footer">Small chores. Real wins. · <button type="button" class="quick-install-link" data-quick="install">Install / share</button> · <a href="/privacy.html">Privacy</a> · <a href="/safety.html">Safety</a></footer></div>';
      window.scrollTo({ top: 0, behavior: 'instant' });
    }

    private async openCamera(): Promise<void> {
      if (this.stage !== 'before' && this.stage !== 'after') return;
      const host = this.host.querySelector<HTMLElement>('#quick-camera');
      if (!host || this.shot) return;
      try {
        await this.camera.start(host);
        if (!host.isConnected || (this.stage !== 'before' && this.stage !== 'after')) return;
        const button = this.host.querySelector<HTMLButtonElement>('[data-quick="snap"]');
        if (button) button.disabled = false;
      } catch {
        if (!host.isConnected || (this.stage !== 'before' && this.stage !== 'after')) return;
        this.message = 'Camera unavailable. Choose a photo instead.';
        const notice = this.host.querySelector<HTMLElement>('.quick-message');
        if (notice) notice.textContent = this.message;
        else {
          const main = this.host.querySelector('main');
          main?.insertAdjacentHTML('beforeend', '<p class="quick-message" role="status">Camera unavailable. Choose a photo instead.</p>');
        }
      }
    }

    private async selectFile(input: HTMLInputElement): Promise<void> {
      const file = input.files?.[0];
      if (!file || this.busy) return;
      const generation = ++this.uploadGeneration;
      const stage = this.stage;
      this.busy = true;
      this.host.querySelector('main')?.insertAdjacentHTML('beforeend',
        '<p class="quick-message" role="status">Preparing your photo on this device…</p>');
      try {
        const shot = await normalizePhoto(file);
        if (generation !== this.uploadGeneration || stage !== this.stage) return;
        this.shot = shot;
        this.message = '';
        this.render();
      } catch (err) {
        this.message = err instanceof Error ? err.message : 'Unable to open this photo.';
        this.render();
      } finally {
        this.busy = false;
      }
    }

    private beginQuest(): void {
      if (!this.shot) throw new Error('Take a photo of the dirty spot first.');
      const observation: Analysis = {
        object_name: 'Player-selected cleaning spot', surface: 'unknown', soil: 'unknown',
        visible_soil: true, image_quality: 'usable', material_certainty: 'unknown',
        hazards: ['none'], target_box: { x: 0, y: 0, width: 1, height: 1 }
      };
      const draft: Quest = {
        id: crypto.randomUUID(), mode: 'guided', phase: 'identified',
        name: 'Grime defeated', room: 'My place', before: this.shot,
        surface: 'unknown', soil: 'unknown', analysis: observation
      };
      this.quest = transition(draft, { type: 'begin-casual' });
      this.shot = '';
      this.stage = 'clean';
    }

    private claimWin(): void {
      if (!this.quest || this.quest.phase !== 'cleaning' || !this.shot)
        throw new Error('Take an after photo of your cleaned spot first.');
      if (this.quest.before === this.shot)
        throw new Error('Before and after photos are identical. Take a new after photo.');
      const result: Result = {
        encounter_id: this.quest.id, status: 'clear', xp: 300,
        provenance: 'self_attested',
        reason: 'Player reported the spot visibly cleaner. Not independently verified.'
      };
      const finished = transition(this.quest, { type: 'result', result, after: this.shot });
      this.data = recordResult(this.data, finished);
      this.quest = finished;
      if (!saveStore(this.data)) this.message = 'Points saved in this tab only. Local storage is unavailable.';
      else this.message = '';
      this.shot = '';
      this.stage = 'result';
    }

    private async action(action: string): Promise<void> {
      if (this.busy) return;
      try {
        this.message = '';
        switch (action) {
          case 'home':
            this.uploadGeneration++;
            this.quest = null;
            this.shot = '';
            this.stage = 'home';
            this.render();
            break;
          case 'wins':
            this.stage = 'wins'; this.render(); break;
          case 'settings':
            this.stage = 'settings'; this.render(); break;
          case 'start':
            if (this.data.active) throw new Error('Check the previous cleaning task first. Follow its real product label.');
            this.quest = null;
            this.shot = '';
            this.stage = 'before';
            this.render();
            void this.openCamera();
            break;
          case 'camera': void this.openCamera(); break;
          case 'snap':
            if (this.stage !== 'before' && this.stage !== 'after') return;
            this.shot = this.camera.capture();
            this.render();
            break;
          case 'retake':
            this.shot = '';
            this.render();
            void this.openCamera();
            break;
          case 'before-ready':
            if (this.stage !== 'before') return;
            this.beginQuest();
            this.render();
            break;
          case 'after':
            if (this.stage !== 'clean' || !this.quest) return;
            this.shot = '';
            this.stage = 'after';
            this.render();
            void this.openCamera();
            break;
          case 'back-clean':
            if (!this.quest) return;
            this.shot = '';
            this.stage = 'clean';
            this.render();
            break;
          case 'claim':
            if (this.stage !== 'after') return;
            this.claimWin();
            this.render();
            break;
          case 'old-task-checked':
            this.data = { ...this.data, active: null };
            saveStore(this.data);
            this.render();
            break;
          case 'install':
            window.dispatchEvent(new Event('grimequest:show-install')); break;
          case 'reset-arm':
            this.resetArmed = true;
            this.render();
            break;
          case 'reset-cancel':
            this.resetArmed = false;
            this.render();
            break;
          case 'reset-confirm':
            if (!this.resetArmed) return;
            resetStore();
            setAccessCode('');
            this.data = emptyStore();
            saveStore(this.data);
            this.quest = null;
            this.shot = '';
            this.resetArmed = false;
            this.stage = 'home';
            this.render();
            break;
        }
      } catch (err) {
        this.message = err instanceof Error ? err.message : 'Something went wrong. You can try again.';
        this.render();
      }
    }
  }
}
