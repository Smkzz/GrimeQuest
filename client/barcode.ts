namespace GQ {
  export function validGTIN(raw:string):boolean {
    if(!/^(?:[0-9]{8}|[0-9]{12,14})$/.test(raw))return false;
    const body=raw.slice(0,-1).split('').reverse();
    const checksum=body.reduce((sum,ch,i)=>sum+Number(ch)*(i%2===0?3:1),0);
    return (10-checksum%10)%10===Number(raw[raw.length-1]);
  }
  type BarcodeResult={getText():string};
  interface Decoder {
    decodeFromVideoDevice(deviceId:string|null,video:HTMLVideoElement,cb:(r:BarcodeResult|null)=>void):Promise<unknown>;
    decodeFromImageElement(image:HTMLImageElement):Promise<BarcodeResult>;
    reset():void;
  }
  function makeDecoder():Decoder {
    const w=window as unknown as {ZXing?:{BrowserMultiFormatReader:new()=>Decoder}};
    if(!w.ZXing)throw new Error('Barcode scanner not available. Enter the digits printed under the barcode.');
    return new w.ZXing.BrowserMultiFormatReader();
  }
  export class BarcodeScanner {
    private reader:Decoder|null=null;
    private video:HTMLVideoElement|null=null;
    private generation=0;
    stop():void {
      this.generation++;
      try{this.reader?.reset();}catch{}
      this.reader=null;
      const video=this.video;this.video=null;
      if(video){
        const source=video.srcObject;
        if(source&&'getTracks' in source){
          try{(source as MediaStream).getTracks().forEach(t=>t.stop());}catch{}
        }
        video.srcObject=null;
      }
    }
    async start(video:HTMLVideoElement,onFound:(code:string)=>void):Promise<void> {
      this.stop();
      const decoder=makeDecoder(),generation=++this.generation;
      this.reader=decoder;this.video=video;
      try{
        await decoder.decodeFromVideoDevice(null,video,result=>{
          if(generation!==this.generation||!result)return;
          const code=result.getText().trim();
          if(!validGTIN(code))return;
          this.stop();onFound(code);
        });
      }catch{
        if(generation===this.generation)this.stop();
        throw new Error('Camera scan unavailable. Choose a barcode image or enter the printed digits.');
      }
    }
    async fromPhoto(file:File):Promise<string>{
      const jpeg=await normalizePhoto(file);
      const img=new Image();img.src=jpeg;
      const reader=makeDecoder();
      try{
        await img.decode();
        const found=await reader.decodeFromImageElement(img);
        const code=found.getText().trim();
        if(!validGTIN(code))throw new Error('Invalid barcode check digit.');
        return code;
      }catch{
        throw new Error('Barcode not readable. Take a closer picture or type its printed digits.');
      }finally{try{reader.reset();}catch{} img.src='';}
    }
  }
}
