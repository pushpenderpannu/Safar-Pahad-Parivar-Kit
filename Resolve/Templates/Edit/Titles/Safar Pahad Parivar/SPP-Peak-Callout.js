const DEFAULTS={"peakHi": "पंचाचूली", "peakEn": "PANCHACHULI", "showHeight": true, "heightM": 6904, "targetX": 50, "targetY": 38, "labelDX": 12, "labelDY": -16, "marker": "0", "scale": 1.0, "outAt": 0, "accentColor": "#f4b03e"};
const DURATION=6;
const CSS=`
.lines{position:absolute;inset:0;width:100%;height:100%;overflow:visible}
.lbl{position:absolute;white-space:nowrap;background:rgba(7,18,43,.55);padding:calc(var(--u)*8) calc(var(--u)*18) calc(var(--u)*10);border-radius:calc(var(--u)*12)}
.ph{font-size:calc(var(--u)*52);font-weight:800;color:var(--snow);line-height:1.2;text-shadow:0 calc(var(--u)*2) calc(var(--u)*12) rgba(0,0,0,.6),0 0 calc(var(--u)*3) rgba(0,0,0,.4)}
.pe{display:flex;gap:calc(var(--u)*14);align-items:baseline;font-size:calc(var(--u)*17);font-weight:700;color:var(--accent);letter-spacing:.28em;text-shadow:0 calc(var(--u)*1) calc(var(--u)*6) rgba(0,0,0,.6)}
.pm{color:var(--snow);letter-spacing:.06em;font-size:calc(var(--u)*20)}`;

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

class PeakCalloutGraphic extends SPPGraphic{
_build(scene){
this.$.svg=svgEl("svg",{class:"lines"},scene);
this.$.ring=svgEl("circle",{fill:"none",stroke:"var(--accent)","stroke-width":"3"},this.$.svg);
this.$.dot=svgEl("circle",{fill:"var(--accent)",stroke:"#07122b","stroke-width":"2"},this.$.svg);
this.$.arrow=svgEl("path",{fill:"var(--accent)"},this.$.svg);
this.$.lead=svgEl("path",{fill:"none",stroke:"#f5f8fc","stroke-width":"3","stroke-linecap":"round","stroke-linejoin":"round"},this.$.svg);
this.$.under=svgEl("line",{stroke:"var(--accent)","stroke-width":"4","stroke-linecap":"round"},this.$.svg);
this.$.lbl=el("div","lbl",scene); this.$.ph=el("div","ph deva",this.$.lbl);
const pe=el("div","pe pop",this.$.lbl); this.$.pe=el("span","",pe); this.$.pm=el("span","pm",pe);
}
_apply(){
const s=this._state; this.style.setProperty("--accent",s.accentColor||"#f4b03e");
setT(this.$.ph,s.peakHi||""); setT(this.$.pe,s.peakEn||"");
setT(this.$.pm,(s.showHeight&&s.heightM)?fmtM(s.heightM)+" m":""); this.$.svg.setAttribute("viewBox",`0 0 ${this._w} ${this._h}`);
}
_frame(t,out){
const s=this._state,W=this._w,H=this._h,u=this._u*(s.scale||1);
const tx=W*(s.targetX??50)/100,ty=H*(s.targetY??38)/100,ax=tx+W*(s.labelDX??12)/100,ay=ty+H*(s.labelDY??-16)/100;
const right=ax>=tx;
// label box
const lw=this.$.lbl.offsetWidth*(s.scale||1)||300*u;
this.$.lbl.style.transformOrigin=right?"0% 100%":"100% 100%";
const lk=eo(seg(t,0.75,1.2)); this.$.lbl.style.opacity=String(lk);
this.$.lbl.style.left=right?Math.round(ax+8*u)+"px":"auto"; this.$.lbl.style.right=right?"auto":Math.round(W-ax+8*u)+"px";
this.$.lbl.style.top=Math.round(ay-this.$.lbl.offsetHeight*(s.scale||1)-6*u)+"px";
this.$.lbl.style.transform=`translateY(${Math.round(14*u*(1-lk))}px) scale(${s.scale||1})`;
this.$.pm.style.opacity=String(eo(seg(t,1.0,1.4)));
// marker
const mk=eb(seg(t,0,0.35));
if((s.marker|0)===0){
  this.$.arrow.setAttribute("opacity","0"); this.$.dot.setAttribute("opacity","1");
  this.$.dot.setAttribute("cx",tx);this.$.dot.setAttribute("cy",ty);this.$.dot.setAttribute("r",String(Math.max(0,9*u*mk)));
  const ph=(t*0.9)%1; this.$.ring.setAttribute("cx",tx);this.$.ring.setAttribute("cy",ty);
  this.$.ring.setAttribute("r",String(9*u+26*u*ph)); this.$.ring.setAttribute("opacity",String((1-ph)*seg(t,0.2,0.4)));
  this.$.ring.setAttribute("stroke-width",String(3*u));
}else{
  this.$.dot.setAttribute("opacity","0"); this.$.ring.setAttribute("opacity","0"); this.$.arrow.setAttribute("opacity",String(clamp(mk,0,1)));
  const ang=Math.atan2(ty-ay,tx-ax),L=26*u*clamp(mk,0,1.2),Wd=13*u*clamp(mk,0,1.2);
  const bx=tx-Math.cos(ang)*L,by=ty-Math.sin(ang)*L,nx=-Math.sin(ang),ny=Math.cos(ang);
  this.$.arrow.setAttribute("d",`M${tx} ${ty} L${bx+nx*Wd} ${by+ny*Wd} L${bx-nx*Wd} ${by-ny*Wd} Z`);
}
// leader line from marker to label anchor, then underline under label
const sx=tx+(ax-tx)*0.0,sy=ty; const ang2=Math.atan2(ay-ty,ax-tx); const off=16*u;
const x0=tx+Math.cos(ang2)*off,y0=ty+Math.sin(ang2)*off;
const lineLen=Math.hypot(ax-x0,ay-y0); const lp=eo(seg(t,0.25,0.8));
this.$.lead.setAttribute("d",`M${x0} ${y0} L${x0+(ax-x0)*lp} ${y0+(ay-y0)*lp}`); this.$.lead.setAttribute("stroke-width",String(3*u));
const up=eo(seg(t,0.7,1.05)),ux=right?ax+lw*up:ax-lw*up;
this.$.under.setAttribute("x1",ax);this.$.under.setAttribute("y1",ay);this.$.under.setAttribute("x2",ux);this.$.under.setAttribute("y2",ay);
this.$.under.setAttribute("stroke-width",String(4*u)); this.$.under.setAttribute("opacity",up>0?"1":"0");
}

}
export default PeakCalloutGraphic;
