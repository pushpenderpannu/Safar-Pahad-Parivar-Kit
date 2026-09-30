const DEFAULTS={"peak1": "पंचाचूली II | PANCHACHULI II | 6904", "p1X": 50, "p1Y": 45, "peak2": "", "p2X": 65, "p2Y": 50, "peak3": "", "p3X": 35, "p3Y": 50, "peak4": "", "p4X": 80, "p4Y": 55, "showHeight": true, "marker": "dot", "lift": 12, "labelBox": true, "scale": 1.0, "outAt": 0, "accentColor": "#f4b03e"};
const DURATION=6;
const CHOICES={"marker": ["dot", "arrow"]};
const CSS=`
.lines{position:absolute;left:0;top:0;width:100%;height:100%;overflow:visible}
.lbl{position:absolute;left:0;top:0;white-space:nowrap;padding:calc(var(--u)*5) calc(var(--u)*14) calc(var(--u)*7);border-radius:calc(var(--u)*10);transform-origin:0 50%}
.lbl.box{background:rgba(7,18,43,.55)}
.ph{font-size:calc(var(--u)*40);font-weight:800;color:var(--snow);line-height:1.18;text-shadow:0 calc(var(--u)*2) calc(var(--u)*10) rgba(0,0,0,.65),0 0 calc(var(--u)*3) rgba(0,0,0,.45)}
.pe{display:flex;gap:calc(var(--u)*12);align-items:baseline;font-size:calc(var(--u)*15);font-weight:700;color:var(--accent);letter-spacing:.24em;text-shadow:0 calc(var(--u)*1) calc(var(--u)*6) rgba(0,0,0,.7)}
.pe:empty,.pe span:empty{display:none}
.pm{color:var(--snow);letter-spacing:.05em;font-size:calc(var(--u)*18)}`;

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
this.$.svg=svgEl("svg",{class:"lines"},scene); this._pk=[];
for(let i=0;i<4;i++){const g=svgEl("g",{},this.$.svg);
  const P={g,ring:svgEl("circle",{fill:"none",stroke:"var(--accent)"},g),dot:svgEl("circle",{fill:"var(--accent)",stroke:"#07122b"},g),
    arrow:svgEl("path",{fill:"var(--accent)",stroke:"#07122b","stroke-linejoin":"round"},g),
    lead:svgEl("line",{stroke:"#f5f8fc","stroke-linecap":"round"},g),tick:svgEl("line",{stroke:"var(--accent)","stroke-linecap":"round"},g),
    lbl:el("div","lbl",scene)};
  P.ph=el("div","ph deva",P.lbl); const pe=el("div","pe pop",P.lbl); P.pe=el("span","",pe); P.pm=el("span","pm",pe);
  this._pk.push(P);}
}
_apply(){
const s=this._state; this.style.setProperty("--accent",s.accentColor||"#f4b03e");
this.$.svg.setAttribute("viewBox",`0 0 ${this._w} ${this._h}`);
this._vis=[];
this._pk.forEach((P,i)=>{const raw=String(s["peak"+(i+1)]??"").trim(),f=raw.split("|").map(x=>x.trim());
  const on=!!raw; P.g.style.display=on?"":"none"; P.lbl.style.display=on?"block":"none"; if(!on)return;
  const m=parseInt((f[2]||"").replace(/[^0-9]/g,""),10);
  setT(P.ph,f[0]||""); setT(P.pe,f[1]||""); setT(P.pm,(s.showHeight!==false&&m>0)?fmtM(m)+" m":"");
  P.lbl.classList.toggle("box",s.labelBox!==false);
  this._vis.push(i);});
this._lay=null;
}
_frame(t,out){
const s=this._state,W=this._w,H=this._h,sc=s.scale||1,u=this._u*sc;
if(!this._lay){ // place labels once per settings change: straight up from the summit, lifted past any label in the way
  const RL=[],RD=[],M=16*this._u,gap=10*u,stub=22*u,pad=8*u;
  const order=this._vis.slice().sort((a,b)=>(s["p"+(a+1)+"Y"]??50)-(s["p"+(b+1)+"Y"]??50));
  const xs=this._vis.map(i=>+(s["p"+(i+1)+"X"]??50)).sort((a,b)=>a-b),mid=(xs[0]+xs[xs.length-1])/2; // names point outwards
  const L={};
  for(const i of order){const P=this._pk[i];
    const tx=W*clamp(s["p"+(i+1)+"X"]??50,0,100)/100,ty=H*clamp(s["p"+(i+1)+"Y"]??50,0,100)/100;
    const w=P.lbl.offsetWidth*sc,h=P.lbl.offsetHeight*sc;
    const fits=(r)=>r?tx+stub+pad+w<=W-M:tx-stub-pad-w>=M;
    const out=xs.length<2||(s["p"+(i+1)+"X"]??50)>=mid;
    let right=fits(out)?out:(fits(!out)?!out:out);
    let y=ty-H*clamp(s.lift??12,3,60)/100;
    const rect=(yy,r)=>{const x0=r?tx:tx-stub-pad-w,x1=r?tx+stub+pad+w:tx;return[x0,yy-h/2-gap/2,x1,yy+h/2+gap/2];};
    const ov=(q,o)=>q[0]<o[2]&&q[2]>o[0]&&q[1]<o[3]&&q[3]>o[1];
    const ok=(yy,r)=>{const q=rect(yy,r),ld=[tx-2*u,yy,tx+2*u,ty];
      return yy-h/2>=M&&!RL.some(o=>ov(q,o)||ov(ld,o))&&!RD.some(o=>ov(q,o));};
    const y0=y,step=h*0.5+gap; let got=null;
    for(const r of [right,!right]){if(!fits(r))continue;for(let n=0;n<16;n++){const yy=y0-n*step;if(ok(yy,r)){got=[yy,r];break;}}if(got)break;}
    if(got){y=got[0];right=got[1];}
    y=Math.max(y,M+h/2); RL.push(rect(y,right)); RD.push([tx-3*u,y,tx+3*u,ty]); L[i]={tx,ty,y,right,w,h};}
  this._lay=L;}
const mk=this._ch("marker");
this._vis.forEach((i,j)=>{const P=this._pk[i],q=this._lay[i]; if(!q)return; const t0=0.25+0.35*j;
  const {tx,ty,y,right}=q,dir=right?1:-1,stub=22*u,pad=8*u;
  // marker
  const k=eb(seg(t,t0,t0+0.35)),kk=clamp(k,0,1.2);
  let top=ty;
  if(mk===0){P.arrow.setAttribute("opacity","0");P.dot.setAttribute("opacity","1");P.dot.setAttribute("cx",tx);P.dot.setAttribute("cy",ty);
    P.dot.setAttribute("r",String(Math.max(0,7*u*kk)));P.dot.setAttribute("stroke-width",String(2*u));
    const ph=((t-t0)*0.9)%1; P.ring.setAttribute("cx",tx);P.ring.setAttribute("cy",ty);P.ring.setAttribute("r",String(7*u+20*u*Math.max(0,ph)));
    P.ring.setAttribute("stroke-width",String(2.5*u));P.ring.setAttribute("opacity",String(t>t0?(1-ph)*seg(t,t0+0.2,t0+0.4):0));top=ty-9*u;}
  else{P.dot.setAttribute("opacity","0");P.ring.setAttribute("opacity","0");P.arrow.setAttribute("opacity",String(clamp(k,0,1)));
    const a=4*u,L=20*u*kk,Wd=9*u*kk; // small arrow just above the summit, pointing down at it
    P.arrow.setAttribute("d",`M${tx} ${ty-a} L${tx-Wd} ${ty-a-L} L${tx+Wd} ${ty-a-L} Z`);P.arrow.setAttribute("stroke-width",String(1.5*u));top=ty-a-L;}
  // white line up from the marker to the label
  const lp=eo(seg(t,t0+0.15,t0+0.6)),ly=top+(y-top)*lp;
  P.lead.setAttribute("x1",tx);P.lead.setAttribute("y1",top);P.lead.setAttribute("x2",tx);P.lead.setAttribute("y2",ly);
  P.lead.setAttribute("stroke-width",String(2.5*u));P.lead.setAttribute("opacity",lp>0?"0.95":"0");
  // short yellow tick, then the name right beside it
  const tp=eo(seg(t,t0+0.55,t0+0.75));
  P.tick.setAttribute("x1",tx);P.tick.setAttribute("y1",y);P.tick.setAttribute("x2",tx+dir*stub*tp);P.tick.setAttribute("y2",y);
  P.tick.setAttribute("stroke-width",String(4*u));P.tick.setAttribute("opacity",tp>0?"1":"0");
  const lk=eo(seg(t,t0+0.62,t0+1.0));
  const lx=right?tx+stub+pad:tx-stub-pad-q.w;
  P.lbl.style.opacity=String(lk);
  P.lbl.style.transform=`translate(${(lx+dir*(1-lk)*-14*u).toFixed(1)}px,${(y-q.h/2).toFixed(1)}px) scale(${sc})`;
  P.lbl.style.transformOrigin="0 0";
  P.pm.style.opacity=String(eo(seg(t,t0+0.85,t0+1.2)));});
}

}
export default PeakCalloutGraphic;
