const DEFAULTS={"number": 2, "total": 5, "titleHi": "दारमा घाटी की ओर", "titleEn": "INTO THE DARMA VALLEY", "meta": "दिन 2 · धारचूला → दुग्तू", "labelHi": "अध्याय", "labelEn": "CHAPTER", "hindiDigits": false, "position": "centre", "backdrop": false, "scale": 1.0, "outAt": 0, "accentColor": "#f4b03e", "rolling": true};
const DURATION=5;
const CHOICES={"position": ["centre", "bottom-left", "top-left"]};
const CSS=`
.bd{position:absolute;inset:0}
.wrap{position:absolute;display:flex;flex-direction:column}
.row{display:flex;align-items:center;gap:calc(var(--u)*22)}
.num{font-size:calc(var(--u)*150);font-weight:700;color:var(--accent);line-height:1;text-shadow:0 calc(var(--u)*4) calc(var(--u)*24) rgba(0,0,0,.4)}
.num.deva{font-weight:800;font-size:calc(var(--u)*140)}
.dv{width:calc(var(--u)*4);height:calc(var(--u)*118);background:rgba(245,248,252,.85);border-radius:calc(var(--u)*2);transform-origin:50% 50%}
.lab{display:flex;flex-direction:column;align-items:flex-start}
.lh{font-size:calc(var(--u)*40);font-weight:800;color:var(--snow);line-height:1.2;text-shadow:0 calc(var(--u)*2) calc(var(--u)*10) rgba(0,0,0,.45)}
.le{font-size:calc(var(--u)*17);font-weight:700;color:var(--accent);letter-spacing:.34em;white-space:nowrap}
.clip{overflow:hidden;padding:calc(var(--u)*34) calc(var(--u)*50) calc(var(--u)*30);margin:calc(var(--u)*-16) calc(var(--u)*-44) calc(var(--u)*-26)}
.th{font-size:calc(var(--u)*96);font-weight:800;color:var(--snow);line-height:1.22;white-space:nowrap;text-shadow:0 calc(var(--u)*3) calc(var(--u)*14) rgba(0,0,0,.42)}
.te{font-size:calc(var(--u)*24);font-weight:700;color:var(--snow);opacity:.92;white-space:nowrap;text-shadow:0 calc(var(--u)*2) calc(var(--u)*10) rgba(0,0,0,.5)}
.meta{font-size:calc(var(--u)*24);font-weight:500;color:rgba(245,248,252,.88);white-space:nowrap;margin-top:calc(var(--u)*10);text-shadow:0 calc(var(--u)*2) calc(var(--u)*10) rgba(0,0,0,.5)}
.prog{display:block;height:calc(var(--u)*40);margin-top:calc(var(--u)*24);overflow:visible}`;

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
// odometer: value x counts, digits spin and carry like a car's odometer. Digits the value doesn't reach (the "1" of
// 1,650 when it drops to 900) fold away - with the comma in front of them - so there's never a grey leading 0.
function rollOdo(host,x,final,fmt){fmt=fmt||(v=>Math.round(v).toLocaleString("en-IN"));
  const W=rollBuild(host,fmt(final)),ds=W.filter(q=>q.st);const n=ds.length;x=Math.max(0,x);let left=0;
  W.forEach(q=>{if(q.st){const k=n-1-ds.indexOf(q),P=Math.pow(10,k),r=x%P;let pos=Math.floor(x/P)%10+(k===0?(x%1):Math.max(0,r-(P-1)));
      q.st.style.transform=`translateY(${(-(pos+10)*RH).toFixed(4)}em)`;
      const v=k===0?1:clamp((x-0.98*P)/(0.02*P),0,1);q.w.style.width=(0.64*v).toFixed(4)+"em";q.w.style.opacity=v.toFixed(3);left=Math.max(left,v);}
    else{q.c.style.maxWidth=(0.6*left).toFixed(4)+"em";q.c.style.opacity=left.toFixed(3);}});}
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
.rs{display:flex;flex-direction:column}
.rs span{display:block;height:1.18em;line-height:1.18em;font-variant-numeric:tabular-nums}
.rc{display:inline-block;height:1.18em;line-height:1.18em;overflow:hidden;vertical-align:bottom}`;
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
  _ch(k){const v=String(this._state[k]??"").trim().toLowerCase(),L=CHOICES[k]||[];if(/^\d+(\.\d+)?$/.test(v))return clamp(Math.round(+v),0,Math.max(0,L.length-1));
    const n=x=>x.toLowerCase().replace(/[^a-z0-9\u0900-\u097f]/g,"").replace("center","centre");const q=n(v);if(!q)return 0;
    let i=L.findIndex(o=>n(o)===q);if(i<0)i=L.findIndex(o=>n(o).startsWith(q));if(i<0)i=L.findIndex(o=>n(o).includes(q));
    if(i<0){const d=DEFAULTS[k];i=Math.max(0,L.findIndex(o=>o===d));}return i;}
  async load(p){this._initialData=p?.data||{};this._state={...DEFAULTS,...this._initialData};this._schedule=[];
    const r=p?.renderCharacteristics?.resolution;
    // lay out in the page's own CSS pixels: on a 4K timeline Resolve reports 3840x2160 but the page is 1920x1080 CSS px
    // at 2x - using the reported size made every title 2x too big and put labels at 2x their position.
    const vw=window.innerWidth||this.clientWidth,vh=window.innerHeight||this.clientHeight;
    this._setUnit(vw>0&&vh>0?vw:(r?.width||1920),vw>0&&vh>0?vh:(r?.height||1080));
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
    const vw=window.innerWidth,vh=window.innerHeight;if(vw>0&&vh>0&&(vw!==this._w||vh!==this._h)){this._setUnit(vw,vh);this._apply();}
    if(this._currentStep===0||t<0||t>DURATION){sc.style.opacity="0";return;}
    const outAt=(typeof s.outAt==="number"&&s.outAt>0)?s.outAt:DURATION-0.6;
    const out=1-eo(seg(t,outAt,outAt+0.5));
    sc.style.opacity=String(out);this._frame(t,out);}
  // "bottom-left 2.35" (or "... cinema") = keep the title inside 2.35:1 output blanking bars
  _posLB(k){const raw=String(this._state[k]??""),re=/2[.,]?35|cinema|scope/ig;this._lbx=re.test(raw);
    if(!this._lbx)return this._ch(k);const keep=this._state[k];this._state[k]=raw.replace(re,"").trim()||DEFAULTS[k];
    const i=this._ch(k);this._state[k]=keep;return i;}
  _bar(){return (this._lbx&&!this._vertical)?Math.max(0,(this._h-this._w/2.35)/2):0;}
  _corner(node,pos,mx,my,mxv,myb,myt){ // place a box in a corner (0 BL,1 BR,2 TL,3 TR,4 centre)
    const v=this._vertical;node.style.left=node.style.right=node.style.top=node.style.bottom="auto";
    const bar=this._bar(),X=this.px(v?mxv:mx),B=Math.round((v?myb:my)*this._u+bar)+"px",T=Math.round((v?myt:my)*this._u+bar)+"px";
    if(pos===4){node.style.left="50%";node.style.top="50%";return "center";}
    if(pos===0||pos===2)node.style.left=X;else node.style.right=X;
    if(pos===0||pos===1)node.style.bottom=B;else node.style.top=T;
    return (pos===1||pos===3)?"right":"left";}
}

class ChapterGraphic extends SPPGraphic{
_build(scene){
this.$.bd=el("div","bd",scene); this.$.wrap=el("div","wrap",scene);
const row=el("div","row",this.$.wrap); this.$.num=el("div","num pop",row); this.$.dv=el("div","dv",row);
const lab=el("div","lab",row); this.$.lh=el("div","lh deva",lab); this.$.le=el("div","le pop",lab);
const c=el("div","clip",this.$.wrap); this.$.th=el("div","th deva",c);
this.$.te=el("div","te pop",this.$.wrap); this.$.meta=el("div","meta mix",this.$.wrap);
this.$.prog=svgEl("svg",{class:"prog"},this.$.wrap);
this.$.pLine=svgEl("line",{stroke:"rgba(245,248,252,.55)","stroke-width":"3","stroke-linecap":"round","stroke-dasharray":"0.1 9"},this.$.prog);
this.$.pDone=svgEl("line",{stroke:"var(--accent)","stroke-width":"3.4","stroke-linecap":"round","stroke-dasharray":"0.1 9"},this.$.prog);
this.$.pDots=svgEl("g",{},this.$.prog); this.$.pRing=svgEl("circle",{fill:"none",stroke:"var(--accent)","stroke-width":"2.5"},this.$.prog);
this._dots=[]; this._progKey=null;
}
_apply(){
const s=this._state; this.style.setProperty("--accent",s.accentColor||"#f4b03e");
const HD="०१२३४५६७८९", n=Math.max(0,Math.round(+s.number||0));
let txt=String(n).padStart(2,"0"); if(s.hindiDigits)txt=txt.replace(/[0-9]/g,d=>HD[+d]);
this._numTxt=txt; this.$.num.className="num "+(s.hindiDigits?"deva":"pop");
setT(this.$.lh,s.labelHi||""); setT(this.$.le,s.labelEn||"");
setT(this.$.th,s.titleHi||""); setT(this.$.te,s.titleEn||""); this.$.te.style.display=s.titleEn?"block":"none";
setT(this.$.meta,s.meta||""); this.$.meta.style.display=s.meta?"block":"none";
this.$.bd.style.display=s.backdrop?"block":"none";
const N=Math.max(0,Math.round(+s.total||0)), cur=clamp(n,1,Math.max(1,N));
const key=N+"/"+cur;
if(key!==this._progKey){this._progKey=key; this.$.pDots.innerHTML=""; this._dots=[];
  const gap=62, W=Math.max(1,(N-1)*gap);
  this.$.prog.setAttribute("viewBox",`-14 -17 ${W+28} 34`); this.$.prog.style.width=this.px((W+28)*40/34);
  this.$.pLine.setAttribute("x1","0");this.$.pLine.setAttribute("y1","0");this.$.pLine.setAttribute("x2",String(W));this.$.pLine.setAttribute("y2","0");
  for(let i=0;i<N;i++){const d=svgEl("circle",{cx:String(i*gap),cy:"0",r:"7"},this.$.pDots);this._dots.push(d);}
  this._gap=gap; this._N=N; this._cur=cur;}
this.$.prog.style.display=N>=2?"block":"none";
const p=this._posLB("position"); this._pos=p;
const w=this.$.wrap.style; w.left=w.top=w.bottom="auto";
if(p===0){w.left="50%";w.top="50%";w.alignItems="center";w.textAlign="center";
  this.$.bd.style.background="radial-gradient(75% 65% at 50% 50%, rgba(7,18,43,.6), rgba(7,18,43,.1) 80%)";}
else{w.left=this.px(this._vertical?70:120);w.alignItems="flex-start";w.textAlign="left";
  if(p===1){w.bottom=Math.round((this._vertical?420:110)*this._u+this._bar())+"px";this.$.bd.style.background="linear-gradient(0deg, rgba(7,18,43,.7), rgba(7,18,43,0) 60%)";}
  else{w.top=Math.round((this._vertical?260:100)*this._u+this._bar())+"px";this.$.bd.style.background="linear-gradient(180deg, rgba(7,18,43,.7), rgba(7,18,43,0) 60%)";}}
w.transformOrigin=p===0?"50% 50%":(p===1?"0% 100%":"0% 0%");
}
_frame(t,out){
const s=this._state,p=this._pos,sc=(s.scale||1)*(this._vertical&&p===0?0.8:1);
this.$.bd.style.opacity=String(eo(seg(t,0,0.5)));
this.$.wrap.style.transform=(p===0?"translate(-50%,-50%) ":"")+`scale(${sc.toFixed(4)})`;
const nk=eo(seg(t,0.05,0.5)); this.$.num.style.opacity=String(nk);
if(s.rolling!==false&&!s.hindiDigits)rollSlot(this.$.num,this._numTxt,seg(t,0.05,1.0),0.12);
else{this.$.num.classList.remove("roll");this.$.num._rk=null;setT(this.$.num,this._numTxt);this.$.num.style.transform=`translateY(${Math.round(20*this._u*(1-nk))}px)`;}
this.$.dv.style.transform=`scaleY(${eo(seg(t,0.2,0.6))})`;
const lb=eo(seg(t,0.3,0.8)); this.$.lh.style.opacity=this.$.le.style.opacity=String(lb);
this.$.lh.style.transform=this.$.le.style.transform=`translateX(${Math.round(-14*this._u*(1-lb))}px)`;
const h=eo(seg(t,0.35,0.95)); this.$.th.style.transform=`translateY(${Math.round(150*this._u*(1-h))}px)`;
const e=eo(seg(t,0.7,1.3)); this.$.te.style.opacity=String(e*0.92); this.$.te.style.letterSpacing=(0.6-0.3*e).toFixed(3)+"em";
const m=eo(seg(t,0.9,1.4)); this.$.meta.style.opacity=String(m); this.$.meta.style.transform=`translateY(${Math.round(10*this._u*(1-m))}px)`;
if(this._N>=2){const g=this._gap,cur=this._cur,pk=eo(seg(t,0.9,1.9)),x=(cur-1)*g*pk;
  this.$.prog.style.opacity=String(eo(seg(t,0.8,1.1)));
  this.$.pDone.setAttribute("x1","0");this.$.pDone.setAttribute("y1","0");this.$.pDone.setAttribute("x2",x.toFixed(1));this.$.pDone.setAttribute("y2","0");
  this._dots.forEach((d,i)=>{const reached=i*g<=x+0.5, isCur=i===cur-1;
    d.setAttribute("fill",reached?"var(--accent)":"#07122b"); d.setAttribute("stroke",reached?"var(--accent)":"rgba(245,248,252,.8)"); d.setAttribute("stroke-width","2.5");
    const pop=isCur?eb(seg(t,1.85,2.3)):1; d.setAttribute("r",String(isCur?(7+4*clamp(pop,0,1.2)):7));});
  const ph=(t*0.9)%1, show=seg(t,1.9,2.1); this.$.pRing.setAttribute("cx",String((cur-1)*g)); this.$.pRing.setAttribute("cy","0");
  this.$.pRing.setAttribute("r",String(11+14*ph)); this.$.pRing.setAttribute("opacity",String((1-ph)*show));}
}

}
export default ChapterGraphic;
