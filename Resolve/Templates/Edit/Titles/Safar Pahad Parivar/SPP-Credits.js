const DEFAULTS={"heading": "आभार · CREDITS", "line1": "कहानी और आवाज़ / Story & Voice | Pushpender Pannu", "line2": "कैमरा / Camera | Pushpender Pannu", "line3": "एडिट / Edit | Pushpender Pannu", "line4": "साथ में / Featuring | परिवार / Family", "line5": "संगीत / Music | Epidemic Sound", "line6": "", "line7": "", "showLogo": true, "handle": "@safar.pahad.parivar", "backdrop": true, "outAt": 0, "accentColor": "#f4b03e"};
const DURATION=10;
const CSS=`
.bd{position:absolute;inset:0;background:rgba(7,18,43,.86)}
.wrap{position:absolute;left:50%;top:50%;display:flex;flex-direction:column;align-items:center;transform:translate(-50%,-50%)}
.hd{font-size:calc(var(--u)*26);font-weight:700;color:var(--accent);letter-spacing:.3em;margin-bottom:calc(var(--u)*34);white-space:nowrap}
.rows{display:grid;grid-template-columns:auto calc(var(--u)*40) auto;row-gap:calc(var(--u)*18);align-items:baseline}
.r{font-size:calc(var(--u)*29);font-weight:500;color:rgba(245,248,252,.66);text-align:right;white-space:nowrap}
.sep{text-align:center;color:var(--accent);font-size:calc(var(--u)*26)}
.n{font-size:calc(var(--u)*38);font-weight:800;color:var(--snow);white-space:nowrap}
.brand{display:flex;flex-direction:column;align-items:center;margin-top:calc(var(--u)*54)}
.brand svg{width:calc(var(--u)*130);height:auto} .hn{font-size:calc(var(--u)*26);font-weight:700;color:var(--snow);margin-top:calc(var(--u)*8)}`;

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
function parseSRT(txt){const out=[];const re=/(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)/;const blocks=txt.replace(/\r/g,"").split(/\n\s*\n/);for(const b of blocks){const lines=b.split("\n");const i=lines.findIndex(l=>re.test(l));if(i<0)continue;const m=lines[i].match(re);const tt=(h,mi,se,ms)=>(+h)*3600+(+mi)*60+(+se)+(+ms)/1000;const text=lines.slice(i+1).join("\n").replace(/<[^>]*>/g,"").replace(/\{\\[^}]*\}/g,"").replace(/&nbsp;/g," ").replace(/&amp;/g,"&").trim();if(text)out.push({a:tt(m[1],m[2],m[3],m[4]),b:tt(m[5],m[6],m[7],m[8]),text});}out.sort((x,y)=>x.a-y.a);return out;}
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

class CreditsGraphic extends SPPGraphic{
_build(scene){
this.$.bd=el("div","bd",scene); this.$.wrap=el("div","wrap",scene);
this.$.hd=el("div","hd mix",this.$.wrap); this.$.rows=el("div","rows mix",this.$.wrap); this.$.cells=[];
for(let i=0;i<7;i++){const r=el("div","r",this.$.rows),sp=el("div","sep",this.$.rows,"·"),n=el("div","n",this.$.rows);this.$.cells.push([r,sp,n]);}
this.$.brand=el("div","brand",this.$.wrap,MARK_SVG); this.$.hn=el("div","hn pop",this.$.brand);
}
_apply(){
const s=this._state; this.style.setProperty("--accent",s.accentColor||"#f4b03e");
setT(this.$.hd,s.heading||""); this.$.hd.style.display=s.heading?"block":"none";
this.$.bd.style.display=s.backdrop?"block":"none";
this._vis=[];
for(let i=0;i<7;i++){const v=(s["line"+(i+1)]||"").trim(); const [r,sp,n]=this.$.cells[i];
  const show=!!v; [r,sp,n].forEach(x=>x.style.display=show?"block":"none");
  if(show){const parts=v.split("|"); setT(r,(parts[0]||"").trim()); setT(n,(parts.slice(1).join("|")||"").trim()); this._vis.push(i);}}
this.$.brand.style.display=s.showLogo?"flex":"none"; setT(this.$.hn,s.handle||"");
this.$.wrap.style.transform=`translate(-50%,-50%) scale(${this._vertical?0.8:1})`;
}
_frame(t,out){
this.$.bd.style.opacity=String(eo(seg(t,0,0.6)));
const h=eo(seg(t,0.2,0.8)); this.$.hd.style.opacity=String(h); this.$.hd.style.letterSpacing=(0.6-0.3*h).toFixed(3)+"em";
this._vis.forEach((i,j)=>{const q=eo(seg(t,0.5+0.16*j,1.0+0.16*j));this.$.cells[i].forEach(x=>{x.style.opacity=String(q);x.style.transform=`translateY(${Math.round(14*this._u*(1-q))}px)`;});});
const b=eo(seg(t,0.8+0.16*this._vis.length,1.4+0.16*this._vis.length)); this.$.brand.style.opacity=String(b); this.$.brand.style.transform=`translateY(${Math.round(12*this._u*(1-b))}px)`;
}
}
export default CreditsGraphic;
