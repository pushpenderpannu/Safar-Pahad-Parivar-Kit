const DEFAULTS={"startAltitude": 1500, "endAltitude": 2200, "countSeconds": 3.0, "labelHi": "ऊँचाई", "labelEn": "ALTITUDE", "place": "मुंस्यारी · MUNSIYARI", "showProfile": true, "position": 3, "scale": 1.0, "outAt": 0, "accentColor": "#f4b03e"};
const DURATION=8;
const CSS=`
.box{position:absolute;padding:calc(var(--u)*22) calc(var(--u)*30);background:rgba(7,18,43,.6);border-radius:calc(var(--u)*18);box-shadow:0 calc(var(--u)*10) calc(var(--u)*40) rgba(0,0,0,.35)}
.lab{display:flex;align-items:center;gap:calc(var(--u)*10);font-size:calc(var(--u)*22);font-weight:700;color:var(--snow);white-space:nowrap}
.lab svg{width:calc(var(--u)*22);height:calc(var(--u)*22)} .lab .le{font-size:calc(var(--u)*15);letter-spacing:.3em;color:var(--accent)}
.num{display:flex;align-items:baseline;gap:calc(var(--u)*10);margin-top:calc(var(--u)*2)}
.nv{font-size:calc(var(--u)*104);font-weight:700;color:var(--snow);line-height:1.05;font-variant-numeric:tabular-nums;text-shadow:0 calc(var(--u)*3) calc(var(--u)*14) rgba(0,0,0,.35)}
.nu{font-size:calc(var(--u)*40);font-weight:700;color:var(--accent)}
.pl{font-size:calc(var(--u)*21);font-weight:500;color:rgba(245,248,252,.85);white-space:nowrap}
.prof{display:block;width:calc(var(--u)*420);height:calc(var(--u)*92);margin-top:calc(var(--u)*12);overflow:visible}`;

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
const BASE_CSS=`:host{position:absolute;inset:0;display:block;pointer-events:none;--u:1px;--accent:#f4b03e;--navy:#07122b;--snow:#f5f8fc}
*{box-sizing:border-box;margin:0;padding:0}
.scene{position:absolute;inset:0;opacity:0}
.deva{font-family:${DEVA}} .pop{font-family:${POP}} .mix{font-family:${MIX}}`;
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
    this._apply();this._currentStep=1;this._setFrame(0);return{statusCode:200};}
  async dispose(){this.$.scene.remove();return{statusCode:200};}
  async playAction(){this._currentStep=1;this._setFrame(1.5);return{statusCode:200,currentStep:1};}
  async stopAction(){this._currentStep=0;this._setFrame(-1);return{statusCode:200};}
  async updateAction(p){const d=p?.data||{};this._state={...this._state,...d};
    if(!this._schedule.some(e=>e.action?.type==="updateAction"))this._initialData={...this._initialData,...d};
    this._apply();return{statusCode:200};}
  async customAction(){return{statusCode:200};}
  async setActionsSchedule(p){this._schedule=(p?.schedule||p?.actions||[]).slice().sort((a,b)=>a.timestamp-b.timestamp);return{statusCode:200};}
  async goToTime(p){const ts=p?.timestamp??0;this._state={...DEFAULTS,...this._initialData};
    let lastPlay=null,lastStop=null;
    for(const e of this._schedule){if(e.timestamp>ts)break;const a=e.action||{};
      if(a.type==="updateAction")this._state={...this._state,...(a.params?.data||{})};
      else if(a.type==="playAction"){lastPlay=e.timestamp;lastStop=null;}
      else if(a.type==="stopAction"){lastStop=e.timestamp;lastPlay=null;}}
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

class AltitudeCounterGraphic extends SPPGraphic{
_build(scene){
this.$.box=el("div","box",scene);
this.$.lab=el("div","lab mix",this.$.box,"<svg viewBox=\"0 0 24 24\"><path d=\"M2 20 L9 8 L13 14 L16 10 L22 20 Z\" fill=\"var(--accent)\"/></svg>"+'<span class="lh"></span><span class="le pop"></span>');
const n=el("div","num pop",this.$.box); this.$.nv=el("span","nv",n,"0"); el("span","nu",n,"m");
this.$.pl=el("div","pl mix",this.$.box);
this.$.prof=svgEl("svg",{viewBox:"0 0 420 92",class:"prof"},this.$.box);
const defs=svgEl("defs",{},this.$.prof); const g=svgEl("linearGradient",{id:"pg",x1:"0",y1:"0",x2:"0",y2:"1"},defs);
svgEl("stop",{offset:"0","stop-color":"#f5f8fc","stop-opacity":"0.28"},g); svgEl("stop",{offset:"1","stop-color":"#f5f8fc","stop-opacity":"0"},g);
const P=[[0,86],[40,78],[70,82],[105,66],[135,70],[170,52],[200,58],[235,40],[262,46],[295,28],[322,34],[352,18],[380,24],[412,8]];
const d="M"+P.map(p=>p.join(" ")).join(" L");
this._P=P;
this.$.fill=svgEl("path",{d:"",fill:"url(#pg)"},this.$.prof);
this.$.line=svgEl("path",{d:"",fill:"none",stroke:"#f5f8fc","stroke-width":"3","stroke-linejoin":"round","stroke-linecap":"round"},this.$.prof);
this.$.dot=svgEl("circle",{r:"6",fill:"var(--accent)"},this.$.prof);
}
_apply(){
const s=this._state; this.style.setProperty("--accent",s.accentColor||"#f4b03e");
setT(this.$.lab.querySelector(".lh"),s.labelHi||""); setT(this.$.lab.querySelector(".le"),s.labelEn||"");
setT(this.$.pl,s.place||""); this.$.pl.style.display=s.place?"block":"none";
this.$.prof.style.display=s.showProfile?"block":"none";
this._side=this._corner(this.$.box,s.position|0,90,84,60,560,250);
const p=s.position|0; this.$.box.style.transformOrigin=p===4?"50% 50%":((this._side==="right"?"100% ":"0% ")+(p>=2?"0%":"100%"));
}
_frame(t,out){
const s=this._state,sc=s.scale||1,p=s.position|0;
const k=eo(seg(t,0,0.45)); this.$.box.style.opacity=String(k);
const base=p===4?"translate(-50%,-50%) ":""; this.$.box.style.transform=`${base}translateY(${Math.round(24*this._u*(1-k))}px) scale(${sc*(0.96+0.04*k)})`;
const c=eo(seg(t,0.45,0.45+(s.countSeconds||3)));
const a0=s.startAltitude||0,a1=s.endAltitude||0; setT(this.$.nv,fmtM(a0+(a1-a0)*c));
const P=this._P,X=412*c,pts=[P[0]];
for(let i=1;i<P.length;i++){const a=P[i-1],b=P[i];if(b[0]<=X){pts.push(b);}else{const f=(X-a[0])/(b[0]-a[0]);if(f>0)pts.push([X,a[1]+(b[1]-a[1])*f]);break;}}
const fx=v=>v.toFixed(2),path="M"+pts.map(q=>fx(q[0])+" "+fx(q[1])).join(" L"),last=pts[pts.length-1];
this.$.line.setAttribute("d",pts.length>1?path:""); this.$.fill.setAttribute("d",pts.length>1?path+` L${fx(last[0])} 92 L0 92 Z`:"");
this.$.dot.setAttribute("cx",fx(last[0])); this.$.dot.setAttribute("cy",fx(last[1]));
this.$.dot.setAttribute("opacity",String(seg(t,0.4,0.6)));
}
}
export default AltitudeCounterGraphic;
