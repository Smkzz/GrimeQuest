namespace GQ {
  export class Camera {
    private stream: MediaStream | null = null;
    private video: HTMLVideoElement | null = null;
    private generation=0;
    async start(host: HTMLElement): Promise<void> {
      this.stop();
      const generation=this.generation;
      if(!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) throw new Error('Live camera needs HTTPS or localhost. You can still choose a photo below.');
      const stream=await navigator.mediaDevices.getUserMedia({audio:false,video:{facingMode:{ideal:'environment'},width:{ideal:1280},height:{ideal:960}}});
      if(generation!==this.generation || !host.isConnected) {stream.getTracks().forEach(t=>t.stop());return;}
      this.stream=stream;
      const video=document.createElement('video');
      video.autoplay=true;video.muted=true;video.playsInline=true;video.setAttribute('aria-label','Camera preview');
      video.srcObject=stream;
      host.replaceChildren(video);
      this.video=video;
      try {await video.play();} catch {this.stop();throw new Error('Camera playback failed. Choose a photo instead.');}
    }
    capture(): string {
      const v=this.video;
      if(!v||v.readyState<2||v.videoWidth===0) throw new Error('Camera is not ready. Wait for the preview or choose a photo.');
      return fromPixels(v,v.videoWidth,v.videoHeight);
    }
    stop(): void {
      this.generation++;
      this.stream?.getTracks().forEach(t=>t.stop());
      this.stream=null;
      if(this.video) this.video.srcObject=null;
      this.video=null;
    }
  }
  function fromPixels(image: CanvasImageSource,width:number,height:number):string {
    if(width*height>12_000_000) throw new Error('Choose a photo smaller than 12 megapixels.');
    const scale=Math.min(1,1280/Math.max(width,height));
    const canvas=document.createElement('canvas');
    canvas.width=Math.round(width*scale);canvas.height=Math.round(height*scale);
    const ctx=canvas.getContext('2d');
    if(!ctx) throw new Error('Image processing is not supported in this browser.');
    ctx.fillStyle='#ffffff';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(image,0,0,canvas.width,canvas.height);
    const data=canvas.toDataURL('image/jpeg',0.85);
    if(data.length>2_700_000) throw new Error('Photo is too detailed. Move closer to a single target and try again.');
    return data;
  }
  export async function normalizePhoto(file:File):Promise<string> {
    if(!['image/jpeg','image/png','image/webp'].includes(file.type)) throw new Error('Choose a JPEG, PNG or WebP photo. HEIC and SVG are not supported; export a JPEG first.');
    if(file.size>8_000_000) throw new Error('Choose a photo smaller than 8 MB.');
    const url=URL.createObjectURL(file);
    try {
      const image=new Image();image.src=url;await image.decode();
      if(image.width<64||image.height<64) throw new Error('Photo must be at least 64 × 64 pixels.');
      return fromPixels(image,image.width,image.height);
    } finally {URL.revokeObjectURL(url);}
  }
}
