const DEFAULTS={"placeHi": "मुंस्यारी", "placeEn": "MUNSIYARI · UTTARAKHAND", "showAltitude": true, "altitude": 2200, "countUp": true, "showDate": true, "date": "26 जून 2026", "showTime": true, "time": "09:58 AM", "weather": "sun", "temperature": "14°C", "position": "bottom-left", "scale": 1.0, "outAt": 0, "accentColor": "#f4b03e", "rolling": true};
const DURATION=8;
const CHOICES={"weather": ["none", "sun", "part-cloud", "cloud", "rain", "snow", "fog", "night"], "position": ["bottom-left", "bottom-right", "top-left", "top-right"]};
const CSS=`
.card{position:absolute;display:flex;gap:calc(var(--u)*20);padding:calc(var(--u)*22) calc(var(--u)*32) calc(var(--u)*22) calc(var(--u)*22);background:rgba(7,18,43,.62);border-radius:calc(var(--u)*18);box-shadow:0 calc(var(--u)*10) calc(var(--u)*40) rgba(0,0,0,.35)}
.bar{width:calc(var(--u)*6);border-radius:calc(var(--u)*3);background:var(--accent);transform-origin:50% 0}
.top{display:flex;align-items:center;gap:calc(var(--u)*18)}
.wx{width:calc(var(--u)*66);height:calc(var(--u)*66);flex:none} .wx svg{width:100%;height:100%;overflow:visible}
.hi{font-size:calc(var(--u)*60);font-weight:800;color:var(--snow);line-height:1.22;white-space:nowrap;text-shadow:0 calc(var(--u)*2) calc(var(--u)*10) rgba(0,0,0,.35)}
.en{font-size:calc(var(--u)*17);font-weight:700;color:var(--accent);white-space:nowrap;margin-top:calc(var(--u)*2)}
.meta{display:flex;flex-wrap:nowrap;gap:calc(var(--u)*28);margin-top:calc(var(--u)*16);font-size:calc(var(--u)*22);font-weight:500;color:rgba(245,248,252,.92)}
.m{display:inline-flex;align-items:center;gap:calc(var(--u)*9);white-space:nowrap} .m svg{width:calc(var(--u)*22);height:calc(var(--u)*22)}
.m b{font-weight:700}`;

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
.rs{display:flex;flex-direction:column}
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
  _ch(k){const v=String(this._state[k]??"").trim().toLowerCase(),L=CHOICES[k]||[];if(/^\d+(\.\d+)?$/.test(v))return clamp(Math.round(+v),0,Math.max(0,L.length-1));
    const n=x=>x.toLowerCase().replace(/[^a-z0-9\u0900-\u097f]/g,"").replace("center","centre");const q=n(v);if(!q)return 0;
    let i=L.findIndex(o=>n(o)===q);if(i<0)i=L.findIndex(o=>n(o).startsWith(q));if(i<0)i=L.findIndex(o=>n(o).includes(q));
    if(i<0){const d=DEFAULTS[k];i=Math.max(0,L.findIndex(o=>o===d));}return i;}
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

class InfoCardGraphic extends SPPGraphic{
_build(scene){
this.$.card=el("div","card",scene); this.$.bar=el("div","bar",this.$.card);
const body=el("div","body",this.$.card); const top=el("div","top",body);
this.$.wx=el("div","wx",top); const ti=el("div","",top);
this.$.hi=el("div","hi deva",ti); this.$.en=el("div","en pop",ti);
this.$.meta=el("div","meta mix",body);
this.$.alt=el("span","m",this.$.meta,"<svg viewBox=\"0 0 24 24\"><path d=\"M2 20 L9 8 L13 14 L16 10 L22 20 Z\" fill=\"var(--accent)\"/></svg>"+'<span><b class="av">0</b> m</span>');
this.$.date=el("span","m",this.$.meta,"<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"#f5f8fc\" stroke-width=\"2\"><rect x=\"3\" y=\"5\" width=\"18\" height=\"16\" rx=\"2\"/><line x1=\"3\" y1=\"10\" x2=\"21\" y2=\"10\"/><line x1=\"8\" y1=\"3\" x2=\"8\" y2=\"7\"/><line x1=\"16\" y1=\"3\" x2=\"16\" y2=\"7\"/></svg>"+'<span class="dv"></span>');
this.$.time=el("span","m",this.$.meta,"<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"#f5f8fc\" stroke-width=\"2\"><circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"M12 7 V12 L15.5 14\"/></svg>"+'<span class="tv"></span>');
this.$.temp=el("span","m",this.$.meta,'<span class="pv"></span>');
this.WX={"1": "<circle cx=\"32\" cy=\"32\" r=\"11\" fill=\"var(--accent)\"/><g stroke=\"var(--accent)\" stroke-width=\"3.2\" stroke-linecap=\"round\"><line x1=\"49.0\" y1=\"32.0\" x2=\"56.0\" y2=\"32.0\"/><line x1=\"44.0\" y1=\"44.0\" x2=\"49.0\" y2=\"49.0\"/><line x1=\"32.0\" y1=\"49.0\" x2=\"32.0\" y2=\"56.0\"/><line x1=\"20.0\" y1=\"44.0\" x2=\"15.0\" y2=\"49.0\"/><line x1=\"15.0\" y1=\"32.0\" x2=\"8.0\" y2=\"32.0\"/><line x1=\"20.0\" y1=\"20.0\" x2=\"15.0\" y2=\"15.0\"/><line x1=\"32.0\" y1=\"15.0\" x2=\"32.0\" y2=\"8.0\"/><line x1=\"44.0\" y1=\"20.0\" x2=\"49.0\" y2=\"15.0\"/></g>", "2": "<circle cx=\"24\" cy=\"24\" r=\"9\" fill=\"var(--accent)\"/><path d=\"M22 50 h26 a9 9 0 0 0 0-18 a13 13 0 0 0-25-3 a9 9 0 0 0-1 21z\" stroke=\"#f5f8fc\" stroke-width=\"3.2\" fill=\"none\" stroke-linecap=\"round\" stroke-linejoin=\"round\" fill=\"rgba(7,18,43,.55)\"/>", "3": "<path d=\"M18 46 h28 a10 10 0 0 0 0-20 a14 14 0 0 0-27-3 a10 10 0 0 0-1 23z\" stroke=\"#f5f8fc\" stroke-width=\"3.2\" fill=\"none\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>", "4": "<path d=\"M18 46 h28 a10 10 0 0 0 0-20 a14 14 0 0 0-27-3 a10 10 0 0 0-1 23z\" stroke=\"#f5f8fc\" stroke-width=\"3.2\" fill=\"none\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/><g stroke=\"#f5f8fc\" stroke-width=\"3.2\" fill=\"none\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><line x1=\"24\" y1=\"52\" x2=\"21\" y2=\"60\"/><line x1=\"33\" y1=\"52\" x2=\"30\" y2=\"60\"/><line x1=\"42\" y1=\"52\" x2=\"39\" y2=\"60\"/></g>", "5": "<path d=\"M18 46 h28 a10 10 0 0 0 0-20 a14 14 0 0 0-27-3 a10 10 0 0 0-1 23z\" stroke=\"#f5f8fc\" stroke-width=\"3.2\" fill=\"none\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/><g fill=\"#f5f8fc\"><circle cx=\"23\" cy=\"56\" r=\"2.4\"/><circle cx=\"32\" cy=\"59\" r=\"2.4\"/><circle cx=\"41\" cy=\"56\" r=\"2.4\"/></g>", "6": "<g stroke=\"#f5f8fc\" stroke-width=\"3.2\" fill=\"none\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><line x1=\"12\" y1=\"24\" x2=\"52\" y2=\"24\"/><line x1=\"8\" y1=\"33\" x2=\"48\" y2=\"33\"/><line x1=\"14\" y1=\"42\" x2=\"54\" y2=\"42\"/><line x1=\"10\" y1=\"51\" x2=\"44\" y2=\"51\"/></g>", "7": "<path d=\"M40 14 a20 20 0 1 0 12 30 a16 16 0 0 1-12-30z\" fill=\"var(--accent)\"/>"};
}
_apply(){
const s=this._state; this.style.setProperty("--accent",s.accentColor||"#f4b03e");
setT(this.$.hi,s.placeHi||""); setT(this.$.en,s.placeEn||""); this.$.en.style.display=s.placeEn?"block":"none";
this.$.alt.style.display=s.showAltitude?"inline-flex":"none"; this.$.date.style.display=(s.showDate&&s.date)?"inline-flex":"none";
this.$.time.style.display=(s.showTime&&s.time)?"inline-flex":"none"; this.$.temp.style.display=s.temperature?"inline-flex":"none";


const w=this.WX[this._ch("weather")]; this.$.wx.style.display=w?"block":"none"; if(w&&this._wxk!==s.weather){this.$.wx.innerHTML=`<svg viewBox="0 0 64 64">${w}</svg>`;this._wxk=s.weather;}
const anyMeta=s.showAltitude||(s.showDate&&s.date)||(s.showTime&&s.time)||s.temperature; this.$.meta.style.display=anyMeta?"flex":"none";
this._side=this._corner(this.$.card,this._ch("position"),90,84,60,560,250);
this.$.card.style.transformOrigin=(this._side==="right"?"100% ":"0% ")+((this._ch("position"))>=2?"0%":"100%");
}
_frame(t,out){
const s=this._state,dir=this._side==="right"?1:-1,sc=s.scale||1;
const k=eo(seg(t,0.05,0.5)); this.$.card.style.opacity=String(k);
this.$.card.style.transform=`translateX(${Math.round(dir*40*this._u*(1-k)+dir*30*this._u*(1-out))}px) scale(${sc})`;
this.$.bar.style.transform=`scaleY(${eo(seg(t,0,0.4))})`;
const h=eo(seg(t,0.2,0.65)); this.$.hi.style.opacity=String(h); this.$.hi.style.transform=`translateY(${Math.round(16*this._u*(1-h))}px)`;
const e=eo(seg(t,0.35,0.9)); this.$.en.style.opacity=String(e); this.$.en.style.letterSpacing=(0.62-0.32*e).toFixed(3)+"em";
const wk=eb(seg(t,0.25,0.75)); this.$.wx.style.opacity=String(clamp(wk,0,1)); this.$.wx.style.transform=`scale(${0.4+0.6*wk}) rotate(${(t*6).toFixed(2)}deg)`;
[this.$.alt,this.$.date,this.$.time,this.$.temp].forEach((m,i)=>{const q=eo(seg(t,0.55+0.1*i,0.95+0.1*i));m.style.opacity=String(q);m.style.transform=`translateY(${Math.round(10*this._u*(1-q))}px)`;});
const av=this.$.alt.querySelector(".av"),dv=this.$.date.querySelector(".dv"),tv=this.$.time.querySelector(".tv"),pv=this.$.temp.querySelector(".pv");
if(s.rolling!==false){
  if(s.countUp){const a=eo(seg(t,0.6,2.1));rollOdo(av,(s.altitude||0)*a,s.altitude||0);}else rollSlot(av,fmtM(s.altitude||0),seg(t,0.6,1.8));
  rollSlot(dv,s.date||"",seg(t,0.7,2.0),0.06); rollSlot(tv,s.time||"",seg(t,0.8,2.1)); rollSlot(pv,s.temperature||"",seg(t,0.9,2.0));}
else{const a=s.countUp?eo(seg(t,0.6,1.9)):1;[av,dv,tv,pv].forEach(n=>{n.classList.remove("roll");n._rk=null;});
  setT(av,fmtM((s.altitude||0)*a));setT(dv,s.date||"");setT(tv,s.time||"");setT(pv,s.temperature||"");}
}

}
export default InfoCardGraphic;
