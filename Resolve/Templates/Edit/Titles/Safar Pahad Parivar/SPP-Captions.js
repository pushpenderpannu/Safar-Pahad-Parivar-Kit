const DEFAULTS={"srt": "1\n00:00:01,000 --> 00:00:04,000\nसाल की सबसे यादगार ट्रिप\n\n2\n00:00:04,300 --> 00:00:07,800\nफ़रीदाबाद से सीधे कुमाऊँ की आख़िरी सरहद तक\n\n3\n00:00:08,100 --> 00:00:11,500\nदारचूला, पंचाचूली और मुंस्यारी\n\n4\n00:00:11,800 --> 00:00:14,500\nचलिए, साथ चलते हैं\n", "clipStart": 0, "style": "0", "position": "0", "size": 1.0, "plate": false, "textColor": "#f5f8fc", "highlightColor": "#f4b03e"};
const DURATION=1200;
const CSS=`
.cap{position:absolute;left:50%;display:flex;justify-content:center}
.box{text-align:center;font-weight:800;line-height:1.38;color:var(--txt);padding:calc(var(--u)*6) calc(var(--u)*22) calc(var(--u)*10);border-radius:calc(var(--u)*14)}
.box.plate{background:rgba(7,18,43,.62)}
.w{display:inline-block;white-space:pre;
   text-shadow:0 0 calc(var(--u)*3) rgba(7,18,43,.95),0 calc(var(--u)*2) calc(var(--u)*6) rgba(7,18,43,.85),0 calc(var(--u)*4) calc(var(--u)*18) rgba(0,0,0,.45)}
.box.plate .w{text-shadow:none}
.w.stress{margin:0 .2em;transform-origin:50% 70%}`;

const clamp=(v,a,b)=>Math.max(a,Math.min(v,b));
const seg=(t,a,b)=>clamp((t-a)/(b-a),0,1);
const eo=(t)=>1-Math.pow(1-t,3);
const eb=(t)=>{const c1=1.70158,c3=c1+1;return 1+c3*Math.pow(t-1,3)+c1*Math.pow(t-1,2);};
const DEVA_RANGE="U+0900-097F,U+1CD0-1CF9,U+200C-200D,U+20A8,U+20B9,U+20F0,U+25CC,U+A830-A839,U+A8E0-A8FF";
const LAT_RANGE="U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215";
const FONT_DIR=new URL("./fonts/",import.meta.url);
let _fontsReady=null;
function sppFonts(){
  if(_fontsReady) return _fontsReady;
  const defs=[];
  for(const w of [500,700,800]){defs.push(["SPP Deva",`deva-${w}.woff2`,w,DEVA_RANGE]);defs.push(["SPP Deva",`deva-latin-${w}.woff2`,w,LAT_RANGE]);}
  defs.push(["SPP Pop","pop-500.ttf",500,null]);defs.push(["SPP Pop","pop-700.ttf",700,null]);
  _fontsReady=Promise.all(defs.map(async([fam,file,w,range])=>{try{const o={weight:String(w)};if(range)o.unicodeRange=range;
    const f=new FontFace(fam,`url("${new URL(file,FONT_DIR).href}")`,o);await f.load();document.fonts.add(f);}catch(e){}}));
  return _fontsReady;
}
const DEVA=`"SPP Deva","Noto Sans Devanagari","Noto Sans Devanagari UI","Nirmala UI",sans-serif`;
const POP=`"SPP Pop","Poppins","Segoe UI",sans-serif`;
const MIX=`"SPP Pop","SPP Deva","Poppins","Noto Sans Devanagari","Nirmala UI",sans-serif`;
const fmtM=(n)=>Math.round(n).toLocaleString("en-IN");
const setT=(n,v)=>{v=(v??"")+"";if(n.textContent!==v)n.textContent=v;};
// ---- rolling digit wheels (odometer / slot-machine numbers)
const RH=1.18;
function rollBuild(host,text){if(host._rk===text)return host._rw;host._rk=text;host.textContent="";host.classList.add("roll");const W=[];
  const runs=text.match(/[0-9]|[^0-9]+/g)||[];
  for(const ch of runs){if(ch.length===1&&ch>="0"&&ch<="9"){const w=document.createElement("span");w.className="rw";const st=document.createElement("span");st.className="rs";
      for(let r=0;r<3;r++)for(let d=0;d<10;d++){const c=document.createElement("span");c.textContent=String(d);st.appendChild(c);}
      w.appendChild(st);host.appendChild(w);W.push({w,st,d:+ch});}
    else{const c=document.createElement("span");c.className="rc";c.textContent=ch;host.appendChild(c);W.push({c});}}
  host._rw=W;return W;}
// odometer: value x counts, digits spin and carry like a car's odometer; layout fixed to the final number
function rollOdo(host,x,final,fmt){fmt=fmt||(v=>Math.round(v).toLocaleString("en-IN"));
  const W=rollBuild(host,fmt(final)),ds=W.filter(q=>q.st);const n=ds.length;x=Math.max(0,x);
  ds.forEach((q,i)=>{const k=n-1-i,P=Math.pow(10,k),r=x%P;let pos=Math.floor(x/P)%10+(k===0?(x%1):Math.max(0,r-(P-1)));
    q.st.style.transform=`translateY(${(-(pos+10)*RH).toFixed(4)}em)`;q.w.style.opacity=(k>0&&x<P-0.5)?"0.28":"1";});}
// slot: each digit spins in (two turns) and lands on its value, left to right; other characters fade in
function rollSlot(host,text,prog,stag){stag=stag??0.08;const W=rollBuild(host,text);
  W.forEach((q,i)=>{const e=eo(seg(prog,i*stag,i*stag+0.62));
    if(q.st)q.st.style.transform=`translateY(${(-(q.d+20*(1-e))*RH).toFixed(4)}em)`;else q.c.style.opacity=String(e);});}
function rollPlain(host,text){const W=rollBuild(host,text);W.forEach(q=>{if(q.st)q.st.style.transform=`translateY(${(-(q.d+10)*RH).toFixed(4)}em)`;else q.c.style.opacity="1";});}

function parseSRT(txt){const out=[];const j=(txt||"").trim();if(j[0]==="{"){try{const d=JSON.parse(j);return (d.cues||[]).map(c=>({a:+c.a,b:+c.b,text:String(c.text||""),w:Array.isArray(c.w)?c.w:null})).sort((x,y)=>x.a-y.a);}catch(e){return out;}}const re=/(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)/;const blocks=txt.replace(/\r/g,"").split(/\n\s*\n/);for(const b of blocks){const lines=b.split("\n");const i=lines.findIndex(l=>re.test(l));if(i<0)continue;const m=lines[i].match(re);const tt=(h,mi,se,ms)=>(+h)*3600+(+mi)*60+(+se)+(+ms)/1000;const text=lines.slice(i+1).join("\n").replace(/<[^>]*>/g,"").replace(/\{\\[^}]*\}/g,"").replace(/&nbsp;/g," ").replace(/&amp;/g,"&").trim();if(text)out.push({a:tt(m[1],m[2],m[3],m[4]),b:tt(m[5],m[6],m[7],m[8]),text});}out.sort((x,y)=>x.a-y.a);return out;}
const BASE_CSS=`:host{position:absolute;inset:0;display:block;pointer-events:none;--u:1px;--accent:#f4b03e;--navy:#07122b;--snow:#f5f8fc}
*{box-sizing:border-box;margin:0;padding:0}
.scene{position:absolute;inset:0;opacity:0}
.deva{font-family:${DEVA}} .pop{font-family:${POP}} .mix{font-family:${MIX}}
.roll{display:inline-flex;align-items:flex-end;white-space:pre;vertical-align:bottom;line-height:1.18em}
.rw{display:inline-block;position:relative;height:1.18em;overflow:hidden;width:.64em;text-align:center;
  -webkit-mask-image:linear-gradient(transparent,#000 14%,#000 86%,transparent);mask-image:linear-gradient(transparent,#000 14%,#000 86%,transparent)}
.rs{display:flex;flex-direction:column;will-change:transform}
.rs span{display:block;height:1.18em;line-height:1.18em;font-variant-numeric:tabular-nums}
.rc{display:inline-block;height:1.18em;line-height:1.18em}`;
function fileURL(p){p=(p||"").trim().replace(/^"|"$/g,"");if(!p)return "";if(/^(https?|file):/i.test(p))return p;
  const parts=p.replace(/\\/g,"/").split("/");return "file:///"+parts.map((x,i)=>i===0&&/^[A-Za-z]:$/.test(x)?x:encodeURIComponent(x)).join("/");}
function el(tag,cls,parent,html){const e=document.createElement(tag);if(cls)e.className=cls;if(html!=null)e.innerHTML=html;if(parent)parent.appendChild(e);return e;}
function svgEl(tag,attrs,parent){const e=document.createElementNS("http://www.w3.org/2000/svg",tag);for(const k in attrs)e.setAttribute(k,attrs[k]);if(parent)parent.appendChild(e);return e;}
const MARK_SVG=`<svg viewBox="0 0 200 130" xmlns="http://www.w3.org/2000/svg"><circle cx="150" cy="30" r="11" fill="var(--accent)"/>
<path d="M8 118 L58 60 L78 82 L103 26 L133 76 L148 60 L192 118" fill="none" stroke="#f5f8fc" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"/>
<path d="M86 62 L95 70 L103 60 L111 70 L121 62" fill="none" stroke="#f5f8fc" stroke-width="3.6" stroke-linejoin="round" stroke-linecap="round"/>
<path d="M100 124 C 82 112, 120 104, 101 92 C 88 86, 110 82, 103 76" fill="none" stroke="var(--accent)" stroke-width="4.5" stroke-linecap="round" stroke-dasharray="0.1 9.6"/></svg>`;

class SPPGraphic extends HTMLElement{
  constructor(){super();this._state={...DEFAULTS};this._initialData={};this._schedule=[];this._currentStep=0;this.$={};this._u=1;this._w=1920;this._h=1080;
    const root=this.attachShadow({mode:"open"});const st=document.createElement("style");st.textContent=BASE_CSS+CSS;
    const scene=document.createElement("div");scene.className="scene";root.append(st,scene);this.$.scene=scene;this._build(scene);}
  _setUnit(w,h){this._w=w;this._h=h;this._u=Math.min(w,h)/1080;this._vertical=h>w;this.style.setProperty("--u",this._u+"px");}
  px(n){return Math.round(n*this._u)+"px";}
  async load(p){this._initialData=p?.data||{};this._state={...DEFAULTS,...this._initialData};this._schedule=[];
    const r=p?.renderCharacteristics?.resolution;
    this._setUnit(r?.width||this.clientWidth||window.innerWidth||1920,r?.height||this.clientHeight||window.innerHeight||1080);
    await sppFonts();
    if(document.fonts&&document.fonts.load){await Promise.all(['800 60px "SPP Deva"','700 30px "SPP Deva"','500 30px "SPP Deva"','700 20px "SPP Pop"','500 20px "SPP Pop"'].map(f=>document.fonts.load(f))).catch(()=>undefined);}
    if(this._prepare)await this._prepare();
    this._apply();this._currentStep=1;this._setFrame(0);return{statusCode:200};}
  async dispose(){this.$.scene.remove();return{statusCode:200};}
  async playAction(){this._currentStep=1;this._setFrame(1.5);return{statusCode:200,currentStep:1};}
  async stopAction(){this._currentStep=0;this._setFrame(-1);return{statusCode:200};}
  async updateAction(p){const d=p?.data||{};this._state={...this._state,...d};
    if(!this._schedule.some(e=>e.action?.type==="updateAction"))this._initialData={...this._initialData,...d};
    if(this._prepare)await this._prepare();
    this._apply();return{statusCode:200};}
  async customAction(){return{statusCode:200};}
  async setActionsSchedule(p){this._schedule=(p?.schedule||p?.actions||[]).slice().sort((a,b)=>a.timestamp-b.timestamp);return{statusCode:200};}
  async goToTime(p){const ts=p?.timestamp??0;this._state={...DEFAULTS,...this._initialData};
    let lastPlay=null,lastStop=null;
    for(const e of this._schedule){if(e.timestamp>ts)break;const a=e.action||{};
      if(a.type==="updateAction")this._state={...this._state,...(a.params?.data||{})};
      else if(a.type==="playAction"){lastPlay=e.timestamp;lastStop=null;}
      else if(a.type==="stopAction"){lastStop=e.timestamp;lastPlay=null;}}
    if(this._prepare)await this._prepare();
    this._apply();
    if(lastStop!==null){this._currentStep=0;this._setFrame(-1);}
    else{this._currentStep=1;this._setFrame((ts-(lastPlay??0))/1000);}
    return{statusCode:200};}
  _setFrame(t){const sc=this.$.scene,s=this._state;
    if(this._currentStep===0||t<0||t>DURATION){sc.style.opacity="0";return;}
    const outAt=(typeof s.outAt==="number"&&s.outAt>0)?s.outAt:DURATION-0.6;
    const out=1-eo(seg(t,outAt,outAt+0.5));
    sc.style.opacity=String(out);this._frame(t,out);}
  _corner(node,pos,mx,my,mxv,myb,myt){ // place a box in a corner (0 BL,1 BR,2 TL,3 TR,4 centre)
    const v=this._vertical;node.style.left=node.style.right=node.style.top=node.style.bottom="auto";
    const X=this.px(v?mxv:mx),B=this.px(v?myb:my),T=this.px(v?myt:my);
    if(pos===4){node.style.left="50%";node.style.top="50%";return "center";}
    if(pos===0||pos===2)node.style.left=X;else node.style.right=X;
    if(pos===0||pos===1)node.style.bottom=B;else node.style.top=T;
    return (pos===1||pos===3)?"right":"left";}
}

class CaptionsGraphic extends SPPGraphic{
_build(scene){
this.$.cap=el("div","cap",scene); this.$.box=el("div","box deva",this.$.cap);
this._cues=[]; this._srtKey=null; this._cueIdx=-2; this._words=[];
}
_apply(){
const s=this._state; this.style.setProperty("--txt",s.textColor||"#f5f8fc"); this.style.setProperty("--hl",s.highlightColor||"#f4b03e");
if(this._srtKey!==s.srt){this._srtKey=s.srt;this._cues=parseSRT(s.srt||"");this._cueIdx=-2;}
this.$.box.classList.toggle("plate",!!s.plate);
const v=this._vertical,p=s.position|0,sz=(s.size||1)*(v?60:54);
this.$.box.style.fontSize=Math.round(sz*this._u)+"px";
this.$.cap.style.width=(v?88:80)+"%";
this.$.cap.style.top=this.$.cap.style.bottom="auto";
if(p===0)this.$.cap.style.bottom=(v?14:8)+"%"; else if(p===1)this.$.cap.style.bottom=(v?30:20)+"%";
else if(p===3)this.$.cap.style.top=(v?16:7)+"%"; else this.$.cap.style.top="50%";
this._pos=p;
}
_frame(t,out){
const s=this._state,T=t+(s.clipStart||0),cues=this._cues;
let idx=-1; for(let i=0;i<cues.length;i++){if(T>=cues[i].a&&T<cues[i].b+0.2){idx=i;}if(cues[i].a>T)break;}
this.$.cap.style.transform=`translateX(-50%)${this._pos===2?" translateY(-50%)":""}`;
if(idx<0){this.$.box.style.opacity="0";return;}
const c=cues[idx];
if(idx!==this._cueIdx){this._cueIdx=idx;this.$.box.innerHTML="";this._words=[];
  const lines=c.text.split("\n");
  lines.forEach((ln,li)=>{ln.split(/\s+/).filter(Boolean).forEach((w,wi,arr)=>{
     const sp=el("span","w",this.$.box);sp.textContent=w+(wi<arr.length-1?" ":"");this._words.push(sp);});
     if(li<lines.length-1)el("br","",this.$.box);});
  const n=this._words.length,d0=Math.max(0.3,c.b-c.a);
  if(c.w&&c.w.length===n){this._wt=c.w.map(x=>[x[0]-c.a,x[1]-c.a,x[2]?1:0]);}
  else{const L=this._words.map(x=>x.textContent.trim().length||1),tot=L.reduce((a,b)=>a+b,0);let acc=0;
    this._wt=L.map(l=>{const f=acc/tot;acc+=l;return [d0*0.85*f,d0*0.85*acc/tot,0];});}
  this._wt.forEach((x,i)=>{x[3]=i<n-1?Math.max(x[1],this._wt[i+1][0]):x[1]+0.25;});
  this._words.forEach((w,i)=>w.classList.toggle("stress",!!this._wt[i][2]));}
const dur=Math.max(0.3,c.b-c.a),lt=T-c.a,st=s.style|0;
const boxIn=eo(seg(lt,0,0.18)),boxOut=1-eo(seg(lt,dur,dur+0.2));
this.$.box.style.opacity=String(st===2?boxIn*boxOut:(s.plate?boxIn*boxOut:boxOut));
this._words.forEach((w,i)=>{const [ws,we,str,hl]=this._wt[i],cur=lt>=ws&&lt<hl,P=str?1.1:1;
  if(st===0){const ta=ws-0.06,k=eo(seg(lt,ta,ta+0.22)),kb=eb(seg(lt,ta,ta+(str?0.32:0.22)));w.style.opacity=String(k);
     w.style.transform=`translateY(${Math.round(14*this._u*(1-k))}px) scale(${((0.92+0.08*kb)*(str?1+0.1*kb:1)).toFixed(4)})`;
     w.style.color=(cur||(str&&lt>=ws))?"var(--hl)":"";}
  else if(st===1){w.style.opacity=String(boxIn);
     w.style.color=(lt>=ws)?((cur||str)?"var(--hl)":"var(--txt)"):"rgba(245,248,252,.55)";
     w.style.transform=`scale(${(cur?1.06*P:(str&&lt>=ws?P:1)).toFixed(3)})`;}
  else{w.style.opacity="1";w.style.transform=str?"scale(1.1)":"none";w.style.color=str?"var(--hl)":"";}});
}

}
export default CaptionsGraphic;
