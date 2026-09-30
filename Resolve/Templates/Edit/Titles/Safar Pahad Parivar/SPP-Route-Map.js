const DEFAULTS={"routeFile": "", "titleHi": "हमारा सफ़र", "titleEn": "OUR ROUTE", "drawStart": 1.2, "drawEnd": 12, "pause": 1.0, "camera": "whole", "zoom": 2.0, "showTimes": true, "showClock": true, "keepLabels": true, "dim": 0.1, "outAt": 0, "accentColor": "#f4b03e", "cinemaBars": false, "fromStop": "", "toStop": ""};
const DURATION=40;
const CHOICES={"camera": ["whole", "follow"]};
const CSS=`
.cam{position:absolute;inset:0;transform-origin:0 0;will-change:transform}
.cam img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.cam svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}
.dim{position:absolute;inset:0;background:#07122b}
.lab{position:absolute;transform-origin:0 0}
.card{position:absolute;left:calc(var(--u)*26);top:calc(var(--u)*-40);background:rgba(7,18,43,.86);border:calc(var(--u)*2) solid rgba(245,248,252,.16);
  border-left:calc(var(--u)*6) solid var(--accent);border-radius:calc(var(--u)*14);padding:calc(var(--u)*10) calc(var(--u)*18) calc(var(--u)*12);white-space:nowrap;
  box-shadow:0 calc(var(--u)*10) calc(var(--u)*30) rgba(0,0,0,.35);transform-origin:0 50%}
.lab.left .card{left:auto;right:calc(var(--u)*26);border-left:calc(var(--u)*2) solid rgba(245,248,252,.16);border-right:calc(var(--u)*6) solid var(--accent);transform-origin:100% 50%}
.lab.below .card{top:calc(var(--u)*14)}
.card .hi{font-weight:800;font-size:calc(var(--u)*40);color:#f5f8fc;line-height:1.15}
.card .en{font:700 calc(var(--u)*16)/1.2 "SPP Pop","Poppins",sans-serif;letter-spacing:.14em;color:var(--accent);margin-top:calc(var(--u)*2)}
.card .tm{font:500 calc(var(--u)*19)/1.35 "SPP Pop","SPP Deva","Nirmala UI",sans-serif;color:rgba(245,248,252,.86);margin-top:calc(var(--u)*6)}
.card .tm b{color:var(--accent);font-weight:700}
.lab.small .card{padding:calc(var(--u)*6) calc(var(--u)*12);border-width:calc(var(--u)*1)}
.lab.small .en,.lab.small .tm{display:none}
.lab.small .hi{font-size:calc(var(--u)*28)}
.ttl{position:absolute;left:calc(var(--u)*70);top:calc(var(--u)*56)}
.ttl .hi{font-weight:800;font-size:calc(var(--u)*66);color:#f5f8fc;line-height:1.1;text-shadow:0 calc(var(--u)*3) calc(var(--u)*18) rgba(7,18,43,.9)}
.ttl .en{font:700 calc(var(--u)*20)/1.4 "SPP Pop","Poppins",sans-serif;letter-spacing:.2em;color:var(--accent);margin-top:calc(var(--u)*4);text-shadow:0 calc(var(--u)*2) calc(var(--u)*10) rgba(7,18,43,.9)}
.clock{position:absolute;left:calc(var(--u)*70);top:calc(var(--u)*186);display:flex;align-items:center;gap:calc(var(--u)*12);background:rgba(7,18,43,.8);
  border-radius:calc(var(--u)*40);padding:calc(var(--u)*8) calc(var(--u)*22) calc(var(--u)*8) calc(var(--u)*14);font:600 calc(var(--u)*26)/1 "SPP Pop","SPP Deva","Nirmala UI",sans-serif;color:#f5f8fc}
.clock svg{width:calc(var(--u)*30);height:calc(var(--u)*30)}
.credit{position:absolute;right:calc(var(--u)*24);bottom:calc(var(--u)*16);font:500 calc(var(--u)*13)/1 "SPP Pop","Poppins",sans-serif;color:rgba(245,248,252,.6)}
.msg{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);background:rgba(7,18,43,.9);color:#f5f8fc;
  padding:calc(var(--u)*24) calc(var(--u)*34);border-radius:calc(var(--u)*16);font:600 calc(var(--u)*28)/1.5 "SPP Pop","SPP Deva","Nirmala UI",sans-serif;text-align:center;border:calc(var(--u)*2) solid var(--accent)}`;

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

class RouteMapGraphic extends SPPGraphic{
_build(scene){
this.$.cam=el("div","cam",scene); this.$.img=el("img","",this.$.cam); this.$.img.decoding="sync";
this.$.dim=el("div","dim",this.$.cam);
this.$.svg=svgEl("svg",{preserveAspectRatio:"xMidYMid slice"},this.$.cam);
this.$.ghostO=svgEl("path",{fill:"none","stroke-linecap":"round","stroke-linejoin":"round"},this.$.svg);
this.$.ghost=svgEl("path",{fill:"none","stroke-linecap":"round","stroke-linejoin":"round"},this.$.svg);
this.$.trailO=svgEl("path",{fill:"none","stroke-linecap":"round","stroke-linejoin":"round"},this.$.svg);
this.$.trail=svgEl("path",{fill:"none","stroke-linecap":"round","stroke-linejoin":"round"},this.$.svg);
this.$.pins=svgEl("g",{},this.$.svg);
this.$.ring=svgEl("circle",{fill:"none"},this.$.svg); this.$.head=svgEl("circle",{},this.$.svg);
this.$.labs=el("div","",this.$.cam);
this.$.ttl=el("div","ttl",scene,'<div class="hi deva"></div><div class="en"></div>');
this.$.clock=el("div","clock",scene,'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--accent)"><rect x="3" y="5" width="18" height="16" rx="3"/><path d="M3 10h18M8 3v4M16 3v4"/></svg><span></span>');
this.$.credit=el("div","credit",scene); this.$.msg=el("div","msg",scene);
this._route=null; this._routeKey=null; this._err="";
}
_apply(){
const s=this._state; this.style.setProperty("--accent",s.accentColor||"#f4b03e");
setT(this.$.ttl.children[0],s.titleHi||""); setT(this.$.ttl.children[1],s.titleEn||"");
this.$.ttl.style.display=(s.titleHi||s.titleEn)?"block":"none";
this.$.dim.style.opacity=String(clamp(+s.dim||0,0,0.8));
const R=this._route;
this.$.msg.style.display=R?"none":"block";
if(!R){this.$.clock.style.display="none";this.$.credit.style.display="none";this.$.msg.innerHTML=this._err||"SPP Route Map<br>Choose <b>route.json</b> in the Inspector<br><small>(Tools\\spp_gps.py route …)</small>";return;}
if(this._builtFor!==R){this._builtFor=R;this._buildRoute(R);}
this.$.clock.style.display=s.showClock&&R.hasTime?"flex":"none"; this.$.credit.style.display="block";
this._lbx=!!s.cinemaBars; const bar=this._bar(),u=this._u;
this.$.ttl.style.top=Math.round(56*u+bar)+"px"; this.$.clock.style.top=Math.round(186*u+bar)+"px"; this.$.credit.style.bottom=Math.round(16*u+bar)+"px";
}
_frame(t,out){
const s=this._state,R=this._route; if(!R)return;
const u=this._u,v=this._vertical;
// ---- title
const ti=eo(seg(t,0.2,0.9)); this.$.ttl.style.opacity=String(ti); this.$.ttl.style.transform=`translateY(${Math.round((1-ti)*-20*u)}px)`;
// ---- journey schedule -> head fraction
const st=R.stops,n=st.length,a0=+s.drawStart||0,a1=Math.max(a0+1,+s.drawEnd||a0+10),P=Math.max(0,+s.pause||0);
const [i0,i1]=this._range(),F0=st[i0].f,F1=st[i1].f,span=Math.max(1e-6,F1-F0),ns=i1-i0+1;   // chapter = stops i0..i1
const move=Math.max(0.5,(a1-a0)-P*(ns-1)); let f=F0,k=0,arrived=i0,clockT=null;
{let tc=a0+P; if(t<tc){f=F0;arrived=t>=a0?i0+1:i0;clockT=st[i0].leave_t||null;}else{f=F1;arrived=i1+1;clockT=st[i1].arrive_t||null;
  for(let i=i0+1;i<=i1;i++){const df=Math.max(0,st[i].f-st[i-1].f),dur=move*df/span,te=tc+dur;
    if(t<te){const q=(t-tc)/Math.max(dur,1e-6);const e=q<.5?4*q*q*q:1-Math.pow(-2*q+2,3)/2;f=st[i-1].f+df*e;arrived=i;clockT=this._segTime(i-1,i,f);break;}
    tc=te; if(i<i1){if(t<tc+P){f=st[i].f;arrived=i+1;clockT=(t-tc<P*0.5)?(st[i].arrive_t||null):(st[i].leave_t||null);break;} tc+=P;}}}}
const hp=this._at(f);
// ---- camera
const cam=this._ch("camera"),Z=cam===1?clamp(+s.zoom||2,1.2,4):1;
const B=this._fit(i0,i1),zb=B.z;                              // whole view of this chapter's part of the route
const zin=eo(seg(t,a0-0.6,a0+0.8)),zout=eo(seg(t,a1+0.2,a1+1.6)),zk=cam===1?zin*(1-zout):0,z=zb+(Math.max(Z,zb)-zb)*zk;
const sm=this._at(clamp(f-0.02,0,1)),sm2=this._at(clamp(f+0.02,0,1));
let cx=(sm[0]+hp[0]+sm2[0])/3,cy=(sm[1]+hp[1]+sm2[1])/3;
cx=B.cx+(cx-B.cx)*zk; cy=B.cy+(cy-B.cy)*zk;
cx=clamp(cx,0.5/z,1-0.5/z); cy=clamp(cy,0.5/z,1-0.5/z);
this.$.cam.style.transform=`translate(${((0.5-cx*z)*100).toFixed(4)}%,${((0.5-cy*z)*100).toFixed(4)}%) scale(${z.toFixed(5)})`;  // % of the frame: never shows an empty edge
// ---- path
const px=(p)=>(p[0]*R.w).toFixed(1)+","+(p[1]*R.h).toFixed(1);
const pts=R.path,iv=[];
for(let i=0;i<pts.length&&pts[i][2]<=f;i++)if(pts[i][2]>=F0)iv.push(px(pts[i]));
if(f>F0){iv.unshift(px(this._at(F0)));iv.push(px(hp));}
const d=iv.length>1?"M"+iv.join("L"):"";
this.$.trail.setAttribute("d",d); this.$.trailO.setAttribute("d",d);
const gi=eo(seg(t,a0-1,a0)); this.$.ghost.style.opacity=String(0.55*gi); this.$.ghostO.style.opacity=String(0.4*gi);
// head
const hv=t>=a0-0.2&&t<=a1+2.5; this.$.head.style.opacity=this.$.ring.style.opacity=hv?"1":"0";
this.$.head.setAttribute("cx",(hp[0]*R.w).toFixed(1)); this.$.head.setAttribute("cy",(hp[1]*R.h).toFixed(1));
this.$.ring.setAttribute("cx",(hp[0]*R.w).toFixed(1)); this.$.ring.setAttribute("cy",(hp[1]*R.h).toFixed(1));
const ph=((t*1.25)%1); this.$.ring.setAttribute("r",(R.sw*(2.2+5*ph)).toFixed(1)); this.$.ring.style.opacity=hv?String(0.8*(1-ph)):"0";
// ---- stops
for(let i=0;i<n;i++){const L=this._labs[i],p=this._pins[i];
  if(i<i0||i>i1){p.style.opacity="0";L.style.display="none";continue;}   // stops of other chapters
  const ta=(i===i0?a0:this._arriveT(i,a0,move,P,i0,span));
  const k1=eb(seg(t,ta,ta+0.45)),k0=eo(seg(t,ta,ta+0.3));
  p.style.opacity=String(k0); p.setAttribute("transform",`translate(${(st[i].x*R.w).toFixed(1)},${(st[i].y*R.h).toFixed(1)}) scale(${(0.2+0.8*k1).toFixed(3)})`);
  const later=i<arrived-1&&arrived>i+1;
  const old=later&&t>=this._arriveT(i+1,a0,move,P,i0,span)+0.3;
  L.classList.toggle("small",old);
  L.style.display=(old&&!s.keepLabels)?"none":"block";
  L.style.opacity=String(k0*(old?0.85:1));
  L.style.transform=`scale(${(1/z).toFixed(5)})`;
  L.firstChild.style.transform=`scale(${(0.6+0.4*k1).toFixed(3)})`;
  L.querySelector(".tm").style.display=(s.showTimes&&!old)?"block":"none";}
// ---- clock
if(s.showClock&&R.hasTime){const tt=clockT;if(tt){const ci=eo(seg(t,a0-0.3,a0+0.3));this.$.clock.style.opacity=String(ci);
  setT(this.$.clock.lastChild,this._fmtClock(tt));}}
this.$.credit.style.opacity=String(eo(seg(t,0.5,1.2)));
}

async _prepare(){const key=this._state.routeFile||"";if(key===this._routeKey)return;this._routeKey=key;this._route=null;this._err="";this._fitKey=null;
  if(!key)return;
  try{const url=fileURL(key);const r=await fetch(url);if(!r.ok)throw new Error("HTTP "+r.status);const R=await r.json();
    if(!R||!Array.isArray(R.path)||!Array.isArray(R.stops))throw new Error("not a route.json");
    R.hasTime=R.path.some(p=>p[3]);R.sw=Math.max(R.w,R.h)/900;
    const imgURL=new URL(R.map||"map.jpg",url).href;
    await new Promise(res=>{this.$.img.onload=res;this.$.img.onerror=res;this.$.img.src=imgURL;});
    if(this.$.img.decode)await this.$.img.decode().catch(()=>{});
    this._route=R;}
  catch(e){this._err="Could not read the route file<br><small>"+String(e.message||e)+"</small>";}}
_buildRoute(R){
  this.$.svg.setAttribute("viewBox",`0 0 ${R.w} ${R.h}`);
  const sw=R.sw,all="M"+R.path.map(p=>(p[0]*R.w).toFixed(1)+","+(p[1]*R.h).toFixed(1)).join("L");
  const dot=`0.1 ${(sw*3.4).toFixed(1)}`;
  const set=(e,a)=>{for(const k in a)e.setAttribute(k,a[k]);};
  set(this.$.ghostO,{d:all,stroke:"rgba(7,18,43,.9)","stroke-width":(sw*2.6).toFixed(1),"stroke-dasharray":dot});
  set(this.$.ghost,{d:all,stroke:"#f5f8fc","stroke-width":(sw*1.5).toFixed(1),"stroke-dasharray":dot});
  set(this.$.trailO,{stroke:"rgba(7,18,43,.95)","stroke-width":(sw*3.6).toFixed(1),"stroke-dasharray":dot});
  set(this.$.trail,{stroke:"var(--accent)","stroke-width":(sw*2.4).toFixed(1),"stroke-dasharray":dot});
  set(this.$.head,{r:(sw*2.2).toFixed(1),fill:"var(--accent)",stroke:"#07122b","stroke-width":(sw*0.8).toFixed(1)});
  set(this.$.ring,{stroke:"var(--accent)","stroke-width":(sw*0.7).toFixed(1)});
  this.$.pins.innerHTML="";this.$.labs.innerHTML="";this._pins=[];this._labs=[];
  R.stops.forEach((st,i)=>{
    const g=svgEl("g",{},this.$.pins);
    svgEl("circle",{r:(sw*4.2).toFixed(1),fill:"rgba(7,18,43,.55)"},g);
    svgEl("circle",{r:(sw*2.6).toFixed(1),fill:"#f5f8fc",stroke:"var(--accent)","stroke-width":(sw*1.2).toFixed(1)},g);
    this._pins.push(g);
    const L=el("div","lab"+(st.x>0.66?" left":"")+(i%2?" below":""),this.$.labs);
    L.style.left=(st.x*100)+"%";L.style.top=(st.y*100)+"%";
    const alt=st.alt?` · ${fmtM(st.alt)} m`:"";
    const tm=[];if(i>0&&st.arrive)tm.push(`<b>पहुँचे</b> ${st.arrive}`);if(i<R.stops.length-1&&st.leave)tm.push(`<b>निकले</b> ${st.leave}`);
    el("div","card",L,`<div class="hi deva"></div><div class="en"></div><div class="tm">${tm.join("<br>")}</div>`);
    setT(L.querySelector(".hi"),st.hi||st.en||"");setT(L.querySelector(".en"),(st.en||"")+alt);
    this._labs.push(L);});
  setT(this.$.credit,R.credit||"");}
_at(f){const P=this._route.path;if(f<=0)return[P[0][0],P[0][1]];if(f>=1){const q=P[P.length-1];return[q[0],q[1]];}
  let lo=0,hi=P.length-1;while(hi-lo>1){const m=(lo+hi)>>1;if(P[m][2]<=f)lo=m;else hi=m;}
  const a=P[lo],b=P[hi],q=(f-a[2])/Math.max(b[2]-a[2],1e-9);return[a[0]+(b[0]-a[0])*q,a[1]+(b[1]-a[1])*q];}
_arriveT(i,a0,move,P,i0,span){i0=i0||0;span=span||1;const st=this._route.stops;let tc=a0+P;for(let j=i0+1;j<=i;j++){tc+=move*Math.max(0,st[j].f-st[j-1].f)/span;if(j<i)tc+=P;}return tc;}
_stopIdx(q,def){const st=this._route.stops;q=String(q??"").trim();if(!q)return def;
  if(/^\d+$/.test(q))return clamp(parseInt(q,10)-1,0,st.length-1);
  const n=x=>String(x||"").toLowerCase().replace(/[^a-z0-9\u0900-\u097f]/g,"");const k=n(q);
  let i=st.findIndex(x=>n(x.hi)===k||n(x.en)===k);if(i<0)i=st.findIndex(x=>n(x.hi).startsWith(k)||n(x.en).startsWith(k));
  if(i<0)i=st.findIndex(x=>n(x.hi).includes(k)||n(x.en).includes(k));return i<0?def:i;}
_range(){const n=this._route.stops.length;let a=this._stopIdx(this._state.fromStop,0),b=this._stopIdx(this._state.toStop,n-1);
  if(b<a)[a,b]=[b,a];if(b===a){if(b<n-1)b++;else if(a>0)a--;}return[a,b];}
_fit(i0,i1){const key=i0+"/"+i1+"/"+(this._lbx?1:0);if(this._fitKey===key)return this._fitV;
  const R=this._route,st=R.stops,F0=st[i0].f,F1=st[i1].f;let x0=1,x1=0,y0=1,y1=0;
  for(const p of R.path)if(p[2]>=F0-1e-6&&p[2]<=F1+1e-6){x0=Math.min(x0,p[0]);x1=Math.max(x1,p[0]);y0=Math.min(y0,p[1]);y1=Math.max(y1,p[1]);}
  for(let i=i0;i<=i1;i++){x0=Math.min(x0,st[i].x);x1=Math.max(x1,st[i].x);y0=Math.min(y0,st[i].y);y1=Math.max(y1,st[i].y);}
  const band=this._h>0?1-2*this._bar()/this._h:1;
  let z=(i0===0&&i1===st.length-1)?1:Math.min(0.62/Math.max(x1-x0,1e-3),0.55*band/Math.max(y1-y0,1e-3));
  z=clamp(z,1,4);const v={z,cx:clamp((x0+x1)/2,0.5/z,1-0.5/z),cy:clamp((y0+y1)/2,0.5/z,1-0.5/z)};
  this._fitKey=key;this._fitV=v;return v;}
_segTime(i0,i1,f){const st=this._route.stops,A=st[i0],B=st[i1];
  const pts=[[A.f,A.leave_t]];for(const p of this._route.path){if(p[3]&&p[2]>A.f&&p[2]<B.f&&p[3]>=A.leave_t&&p[3]<=B.arrive_t)pts.push([p[2],p[3]]);}
  pts.push([B.f,B.arrive_t]);
  for(let j=1;j<pts.length;j++){if(f<=pts[j][0]){const a=pts[j-1],b=pts[j];return a[1]+(b[1]-a[1])*((f-a[0])/Math.max(b[0]-a[0],1e-9));}}
  return B.arrive_t;}
_timeAt(f){const P=this._route.path;let a=null,b=null;
  for(const p of P){if(!p[3])continue;if(p[2]<=f)a=p;else{b=p;break;}}
  if(a&&b)return a[3]+(b[3]-a[3])*((f-a[2])/Math.max(b[2]-a[2],1e-9));return (a||b)?(a||b)[3]:null;}
_fmtClock(ep){const tz=(this._route.tz??5.5)*3600,d=new Date((ep+tz)*1000);
  const M=["जनवरी","फ़रवरी","मार्च","अप्रैल","मई","जून","जुलाई","अगस्त","सितंबर","अक्टूबर","नवंबर","दिसंबर"];
  let h=d.getUTCHours(),m=d.getUTCMinutes();m=Math.floor(m/5)*5;const ap=h<12?"AM":"PM";h=h%12||12;
  return `${d.getUTCDate()} ${M[d.getUTCMonth()]} · ${h}:${String(m).padStart(2,"0")} ${ap}`;}
}
export default RouteMapGraphic;
