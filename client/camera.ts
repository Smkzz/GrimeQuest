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
  // A phone can supply a 12/24/48/50+ MP photograph. These limits apply only
  // to the *re-encoded upload*, never to the source camera's pixel count.
  const MAX_SOURCE_FILE_BYTES=100_000_000; // Prevent enormous/RAW-like files exhausting memory.
  const MAX_UPLOAD_DATA_URL_LENGTH=2_600_000; // <2 MB decoded, below server/schema limits.
  const MAX_UPLOAD_EDGE=1600; // Server already normalizes to 1600 pixels.

  function fromPixels(image: CanvasImageSource,width:number,height:number):string {
    if(!Number.isFinite(width)||!Number.isFinite(height)||width<64||height<64)
      throw new Error('Photo must be at least 64 × 64 pixels.');
    // Keep as much label text detail as permitted by the existing API.
    // If highly textured photos exceed the transport budget, progressively
    // lower JPEG quality and then output dimensions, not the input limit.
    for(const edge of [MAX_UPLOAD_EDGE,1280,960,720,512]){
      const scale=Math.min(1,edge/Math.max(width,height));
      const canvas=document.createElement('canvas');
      canvas.width=Math.max(1,Math.round(width*scale));
      canvas.height=Math.max(1,Math.round(height*scale));
      const ctx=canvas.getContext('2d');
      if(!ctx) throw new Error('Image processing is not supported in this browser.');
      ctx.fillStyle='#ffffff';
      ctx.fillRect(0,0,canvas.width,canvas.height);
      ctx.drawImage(image,0,0,canvas.width,canvas.height);
      for(const quality of [0.85,0.72,0.58]){
        const data=canvas.toDataURL('image/jpeg',quality);
        if(!data.startsWith('data:image/jpeg;base64,'))
          throw new Error('This browser could not encode the photo as JPEG.');
        if(data.length<=MAX_UPLOAD_DATA_URL_LENGTH)return data;
      }
    }
    throw new Error('This photo could not be resized for upload. Try a clearly framed photo of one target.');
  }
  export async function normalizePhoto(file:File):Promise<string> {
    const mime=file.type.toLowerCase();
    // Safari 17+ can decode native iPhone HEIC/HEIF; other browsers fail with
    // a clear JPEG-export fallback. No external WASM decoder or original file
    // is uploaded: all accepted photos are drawn and re-encoded to JPEG.
    const heic=['image/heic','image/heif'].includes(mime) ||
      (mime==='' && /\.(heic|heif)$/i.test(file.name));
    if(!['image/jpeg','image/png','image/webp'].includes(mime) && !heic)
      throw new Error('Choose a JPEG, PNG, WebP or supported HEIC/HEIF photo. SVG is not supported.');
    if(file.size>MAX_SOURCE_FILE_BYTES)
      throw new Error('This image file is over 100 MB. Use a normal JPEG or HEIC photo instead of a RAW export.');
    const url=URL.createObjectURL(file);
    try {
      const image=new Image();image.src=url;
      try {await image.decode();}
      catch {
        throw new Error(heic
          ? 'This browser cannot open this HEIC/HEIF photo. Use Safari 17+ or export the photo as JPEG.'
          : 'This photo could not be decoded. Choose another JPEG, PNG or WebP image.');
      }
      const width=image.naturalWidth||image.width;
      const height=image.naturalHeight||image.height;
      return fromPixels(image,width,height);
    } finally {URL.revokeObjectURL(url);}
  }
}
