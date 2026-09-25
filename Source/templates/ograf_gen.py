"""Generate Safar Pahad Parivar OGraf title templates for DaVinci Resolve."""
import json, os, shutil
from pathlib import Path as _P
SRC = str(_P(__file__).resolve().parents[1])      # <kit>/Source
KIT = str(_P(__file__).resolve().parents[2])      # <kit>
S = SRC
OUT = os.path.join(KIT, "Resolve", "Templates", "Edit", "Titles", "Safar Pahad Parivar")
os.makedirs(OUT, exist_ok=True)

def U(n):  # size in "design units" (1u = 1px at 1080-short-side)
    return f"calc(var(--u)*{n})"

BASE = r"""
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
"""

def weather_icons():
    s = 'stroke="#f5f8fc" stroke-width="3.2" fill="none" stroke-linecap="round" stroke-linejoin="round"'
    sun = '<circle cx="32" cy="32" r="11" fill="var(--accent)"/><g stroke="var(--accent)" stroke-width="3.2" stroke-linecap="round">' + "".join(
        f'<line x1="{32+17*c:.1f}" y1="{32+17*s_:.1f}" x2="{32+24*c:.1f}" y2="{32+24*s_:.1f}"/>'
        for c, s_ in [(1,0),(0.707,0.707),(0,1),(-0.707,0.707),(-1,0),(-0.707,-0.707),(0,-1),(0.707,-0.707)]) + '</g>'
    cloud = f'<path d="M18 46 h28 a10 10 0 0 0 0-20 a14 14 0 0 0-27-3 a10 10 0 0 0-1 23z" {s}/>'
    return {
        1: sun,
        2: '<circle cx="24" cy="24" r="9" fill="var(--accent)"/>' + f'<path d="M22 50 h26 a9 9 0 0 0 0-18 a13 13 0 0 0-25-3 a9 9 0 0 0-1 21z" {s} fill="rgba(7,18,43,.55)"/>',
        3: cloud,
        4: cloud + f'<g {s}><line x1="24" y1="52" x2="21" y2="60"/><line x1="33" y1="52" x2="30" y2="60"/><line x1="42" y1="52" x2="39" y2="60"/></g>',
        5: cloud + '<g fill="#f5f8fc"><circle cx="23" cy="56" r="2.4"/><circle cx="32" cy="59" r="2.4"/><circle cx="41" cy="56" r="2.4"/></g>',
        6: f'<g {s}><line x1="12" y1="24" x2="52" y2="24"/><line x1="8" y1="33" x2="48" y2="33"/><line x1="14" y1="42" x2="54" y2="42"/><line x1="10" y1="51" x2="44" y2="51"/></g>',
        7: '<path d="M40 14 a20 20 0 1 0 12 30 a16 16 0 0 1-12-30z" fill="var(--accent)"/>',
    }

ICONS = {
    "alt": '<svg viewBox="0 0 24 24"><path d="M2 20 L9 8 L13 14 L16 10 L22 20 Z" fill="var(--accent)"/></svg>',
    "date": '<svg viewBox="0 0 24 24" fill="none" stroke="#f5f8fc" stroke-width="2"><rect x="3" y="5" width="18" height="16" rx="2"/><line x1="3" y1="10" x2="21" y2="10"/><line x1="8" y1="3" x2="8" y2="7"/><line x1="16" y1="3" x2="16" y2="7"/></svg>',
    "time": '<svg viewBox="0 0 24 24" fill="none" stroke="#f5f8fc" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7 V12 L15.5 14"/></svg>',
}

def select_prop(title, labels, default=0):
    """Dropdown in Resolve's Inspector. Values are "0","1",... so template code can use (s.x|0)."""
    keys = [str(i) for i in range(len(labels))]
    return {"type": "string", "title": title, "enum": keys, "gddType": "select",
            "gddOptions": {"labels": dict(zip(keys, labels))}, "default": str(default)}

def color_prop(title, default="#f4b03e"):
    return {"type": "string", "title": title, "gddType": "color-rrggbb", "pattern": "^#[0-9a-f]{6}$", "default": default}

SAMPLE_SRT = '1\n00:00:01,000 --> 00:00:04,000\nसाल की सबसे यादगार ट्रिप\n\n2\n00:00:04,300 --> 00:00:07,800\nफ़रीदाबाद से सीधे कुमाऊँ की आख़िरी सरहद तक\n\n3\n00:00:08,100 --> 00:00:11,500\nदारचूला, पंचाचूली और मुंस्यारी\n\n4\n00:00:11,800 --> 00:00:14,500\nचलिए, साथ चलते हैं\n'
TEMPLATES = []

# ------------------------------------------------------------------ 1. INFO CARD
wx = weather_icons()
TEMPLATES.append(dict(
    id="spp-info-card", name="SPP Info Card", file="SPP-Info-Card", duration=8,
    desc="Location card: Hindi + English place, date, time, altitude, weather. Each item can be shown or hidden.",
    props={
        "placeHi": {"type": "string", "title": "Place (Hindi)", "default": "मुंस्यारी"},
        "placeEn": {"type": "string", "title": "Place (English)", "default": "MUNSIYARI · UTTARAKHAND"},
        "showAltitude": {"type": "boolean", "title": "Show Altitude", "default": True},
        "altitude": {"type": "integer", "title": "Altitude (m)", "minimum": 0, "maximum": 9000, "default": 2200},
        "countUp": {"type": "boolean", "title": "Count Altitude Up", "default": True},
        "showDate": {"type": "boolean", "title": "Show Date", "default": True},
        "date": {"type": "string", "title": "Date", "default": "26 जून 2026"},
        "showTime": {"type": "boolean", "title": "Show Time", "default": True},
        "time": {"type": "string", "title": "Time", "default": "09:58 AM"},
        "weather": select_prop("Weather", ["None", "Sunny", "Partly cloudy", "Cloudy", "Rain", "Snow", "Fog", "Night"], 1),
        "temperature": {"type": "string", "title": "Temperature (blank = hide)", "default": "14°C"},
        "position": select_prop("Position", ["Bottom left", "Bottom right", "Top left", "Top right"], 0),
        "scale": {"type": "number", "title": "Size", "minimum": 0.5, "maximum": 2.0, "default": 1.0},
        "outAt": {"type": "number", "title": "Animate Out At (s, 0 = end)", "minimum": 0, "maximum": 8, "default": 0},
        "accentColor": color_prop("Accent Colour"),
        "rolling": {"type": "boolean", "title": "Rolling-dial numbers", "default": True},
    },
    css=f"""
.card{{position:absolute;display:flex;gap:{U(20)};padding:{U(22)} {U(32)} {U(22)} {U(22)};background:rgba(7,18,43,.62);border-radius:{U(18)};box-shadow:0 {U(10)} {U(40)} rgba(0,0,0,.35)}}
.bar{{width:{U(6)};border-radius:{U(3)};background:var(--accent);transform-origin:50% 0}}
.top{{display:flex;align-items:center;gap:{U(18)}}}
.wx{{width:{U(66)};height:{U(66)};flex:none}} .wx svg{{width:100%;height:100%;overflow:visible}}
.hi{{font-size:{U(60)};font-weight:800;color:var(--snow);line-height:1.22;white-space:nowrap;text-shadow:0 {U(2)} {U(10)} rgba(0,0,0,.35)}}
.en{{font-size:{U(17)};font-weight:700;color:var(--accent);white-space:nowrap;margin-top:{U(2)}}}
.meta{{display:flex;flex-wrap:nowrap;gap:{U(28)};margin-top:{U(16)};font-size:{U(22)};font-weight:500;color:rgba(245,248,252,.92)}}
.m{{display:inline-flex;align-items:center;gap:{U(9)};white-space:nowrap}} .m svg{{width:{U(22)};height:{U(22)}}}
.m b{{font-weight:700}}""",
    build=f"""
this.$.card=el("div","card",scene); this.$.bar=el("div","bar",this.$.card);
const body=el("div","body",this.$.card); const top=el("div","top",body);
this.$.wx=el("div","wx",top); const ti=el("div","",top);
this.$.hi=el("div","hi deva",ti); this.$.en=el("div","en pop",ti);
this.$.meta=el("div","meta mix",body);
this.$.alt=el("span","m",this.$.meta,{json.dumps(ICONS['alt'])}+'<span><b class="av">0</b> m</span>');
this.$.date=el("span","m",this.$.meta,{json.dumps(ICONS['date'])}+'<span class="dv"></span>');
this.$.time=el("span","m",this.$.meta,{json.dumps(ICONS['time'])}+'<span class="tv"></span>');
this.$.temp=el("span","m",this.$.meta,'<span class="pv"></span>');
this.WX={json.dumps(wx, ensure_ascii=False)};""",
    apply="""
const s=this._state; this.style.setProperty("--accent",s.accentColor||"#f4b03e");
setT(this.$.hi,s.placeHi||""); setT(this.$.en,s.placeEn||""); this.$.en.style.display=s.placeEn?"block":"none";
this.$.alt.style.display=s.showAltitude?"inline-flex":"none"; this.$.date.style.display=(s.showDate&&s.date)?"inline-flex":"none";
this.$.time.style.display=(s.showTime&&s.time)?"inline-flex":"none"; this.$.temp.style.display=s.temperature?"inline-flex":"none";


const w=this.WX[s.weather]; this.$.wx.style.display=w?"block":"none"; if(w&&this._wxk!==s.weather){this.$.wx.innerHTML=`<svg viewBox="0 0 64 64">${w}</svg>`;this._wxk=s.weather;}
const anyMeta=s.showAltitude||(s.showDate&&s.date)||(s.showTime&&s.time)||s.temperature; this.$.meta.style.display=anyMeta?"flex":"none";
this._side=this._corner(this.$.card,s.position|0,90,84,60,560,250);
this.$.card.style.transformOrigin=(this._side==="right"?"100% ":"0% ")+((s.position|0)>=2?"0%":"100%");""",
    frame="""
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
  setT(av,fmtM((s.altitude||0)*a));setT(dv,s.date||"");setT(tv,s.time||"");setT(pv,s.temperature||"");}""",
))

# ------------------------------------------------------------------ 2. ALTITUDE COUNTER
TEMPLATES.append(dict(
    id="spp-altitude-counter", name="SPP Altitude Counter", file="SPP-Altitude-Counter", duration=8,
    desc="Altitude counts up in metres while a mountain profile draws itself.",
    props={
        "startAltitude": {"type": "integer", "title": "Start Altitude (m)", "minimum": 0, "maximum": 9000, "default": 1500},
        "endAltitude": {"type": "integer", "title": "End Altitude (m)", "minimum": 0, "maximum": 9000, "default": 2200},
        "countSeconds": {"type": "number", "title": "Count Duration (s)", "minimum": 0.5, "maximum": 6, "default": 3.0},
        "labelHi": {"type": "string", "title": "Label (Hindi)", "default": "ऊँचाई"},
        "labelEn": {"type": "string", "title": "Label (English)", "default": "ALTITUDE"},
        "place": {"type": "string", "title": "Place (optional)", "default": "मुंस्यारी · MUNSIYARI"},
        "showProfile": {"type": "boolean", "title": "Show Mountain Profile", "default": True},
        "position": select_prop("Position", ["Bottom left", "Bottom right", "Top left", "Top right", "Centre"], 3),
        "scale": {"type": "number", "title": "Size", "minimum": 0.5, "maximum": 2.5, "default": 1.0},
        "outAt": {"type": "number", "title": "Animate Out At (s, 0 = end)", "minimum": 0, "maximum": 8, "default": 0},
        "accentColor": color_prop("Accent Colour"),
        "rolling": {"type": "boolean", "title": "Rolling-dial numbers", "default": True},
    },
    css=f"""
.box{{position:absolute;padding:{U(22)} {U(30)};background:rgba(7,18,43,.6);border-radius:{U(18)};box-shadow:0 {U(10)} {U(40)} rgba(0,0,0,.35)}}
.lab{{display:flex;align-items:center;gap:{U(10)};font-size:{U(22)};font-weight:700;color:var(--snow);white-space:nowrap}}
.lab svg{{width:{U(22)};height:{U(22)}}} .lab .le{{font-size:{U(15)};letter-spacing:.3em;color:var(--accent)}}
.num{{display:flex;align-items:baseline;gap:{U(10)};margin-top:{U(2)}}}
.nv{{font-size:{U(104)};font-weight:700;color:var(--snow);line-height:1.05;font-variant-numeric:tabular-nums;text-shadow:0 {U(3)} {U(14)} rgba(0,0,0,.35)}}
.nu{{font-size:{U(40)};font-weight:700;color:var(--accent)}}
.pl{{font-size:{U(21)};font-weight:500;color:rgba(245,248,252,.85);white-space:nowrap}}
.prof{{display:block;width:{U(420)};height:{U(92)};margin-top:{U(12)};overflow:visible}}""",
    build=f"""
this.$.box=el("div","box",scene);
this.$.lab=el("div","lab mix",this.$.box,{json.dumps(ICONS['alt'])}+'<span class="lh"></span><span class="le pop"></span>');
const n=el("div","num pop",this.$.box); this.$.nv=el("span","nv",n,"0"); el("span","nu",n,"m");
this.$.pl=el("div","pl mix",this.$.box);
this.$.prof=svgEl("svg",{{viewBox:"0 0 420 92",class:"prof"}},this.$.box);
const defs=svgEl("defs",{{}},this.$.prof); const g=svgEl("linearGradient",{{id:"pg",x1:"0",y1:"0",x2:"0",y2:"1"}},defs);
svgEl("stop",{{offset:"0","stop-color":"#f5f8fc","stop-opacity":"0.28"}},g); svgEl("stop",{{offset:"1","stop-color":"#f5f8fc","stop-opacity":"0"}},g);
const P=[[0,86],[40,78],[70,82],[105,66],[135,70],[170,52],[200,58],[235,40],[262,46],[295,28],[322,34],[352,18],[380,24],[412,8]];
const d="M"+P.map(p=>p.join(" ")).join(" L");
this._P=P;
this.$.fill=svgEl("path",{{d:"",fill:"url(#pg)"}},this.$.prof);
this.$.line=svgEl("path",{{d:"",fill:"none",stroke:"#f5f8fc","stroke-width":"3","stroke-linejoin":"round","stroke-linecap":"round"}},this.$.prof);
this.$.dot=svgEl("circle",{{r:"6",fill:"var(--accent)"}},this.$.prof);""",
    apply="""
const s=this._state; this.style.setProperty("--accent",s.accentColor||"#f4b03e");
setT(this.$.lab.querySelector(".lh"),s.labelHi||""); setT(this.$.lab.querySelector(".le"),s.labelEn||"");
setT(this.$.pl,s.place||""); this.$.pl.style.display=s.place?"block":"none";
this.$.prof.style.display=s.showProfile?"block":"none";
this._side=this._corner(this.$.box,s.position|0,90,84,60,560,250);
const p=s.position|0; this.$.box.style.transformOrigin=p===4?"50% 50%":((this._side==="right"?"100% ":"0% ")+(p>=2?"0%":"100%"));""",
    frame="""
const s=this._state,sc=s.scale||1,p=s.position|0;
const k=eo(seg(t,0,0.45)); this.$.box.style.opacity=String(k);
const base=p===4?"translate(-50%,-50%) ":""; this.$.box.style.transform=`${base}translateY(${Math.round(24*this._u*(1-k))}px) scale(${sc*(0.96+0.04*k)})`;
const c=eo(seg(t,0.45,0.45+(s.countSeconds||3)));
const a0=s.startAltitude||0,a1=s.endAltitude||0;
if(s.rolling!==false)rollOdo(this.$.nv,a0+(a1-a0)*c,Math.max(a0,a1));else{this.$.nv.classList.remove("roll");this.$.nv._rk=null;setT(this.$.nv,fmtM(a0+(a1-a0)*c));}
const P=this._P,X=412*c,pts=[P[0]];
for(let i=1;i<P.length;i++){const a=P[i-1],b=P[i];if(b[0]<=X){pts.push(b);}else{const f=(X-a[0])/(b[0]-a[0]);if(f>0)pts.push([X,a[1]+(b[1]-a[1])*f]);break;}}
const fx=v=>v.toFixed(2),path="M"+pts.map(q=>fx(q[0])+" "+fx(q[1])).join(" L"),last=pts[pts.length-1];
this.$.line.setAttribute("d",pts.length>1?path:""); this.$.fill.setAttribute("d",pts.length>1?path+` L${fx(last[0])} 92 L0 92 Z`:"");
this.$.dot.setAttribute("cx",fx(last[0])); this.$.dot.setAttribute("cy",fx(last[1]));
this.$.dot.setAttribute("opacity",String(seg(t,0.4,0.6)));""",
))

# ------------------------------------------------------------------ 3. PEAK CALLOUT
TEMPLATES.append(dict(
    id="spp-peak-callout", name="SPP Peak Callout", file="SPP-Peak-Callout", duration=6,
    desc="Point at a mountain: dot or arrow on the peak, leader line and a name label with height.",
    props={
        "peakHi": {"type": "string", "title": "Peak Name (Hindi)", "default": "पंचाचूली"},
        "peakEn": {"type": "string", "title": "Peak Name (English)", "default": "PANCHACHULI"},
        "showHeight": {"type": "boolean", "title": "Show Height", "default": True},
        "heightM": {"type": "integer", "title": "Height (m)", "minimum": 0, "maximum": 9000, "default": 6904},
        "targetX": {"type": "number", "title": "Peak X (% of width)", "minimum": 0, "maximum": 100, "default": 50},
        "targetY": {"type": "number", "title": "Peak Y (% of height)", "minimum": 0, "maximum": 100, "default": 38},
        "labelDX": {"type": "number", "title": "Label Offset X (%)", "minimum": -60, "maximum": 60, "default": 12},
        "labelDY": {"type": "number", "title": "Label Offset Y (%)", "minimum": -60, "maximum": 60, "default": -16},
        "marker": select_prop("Marker", ["Dot + line", "Arrow"], 0),
        "scale": {"type": "number", "title": "Size", "minimum": 0.5, "maximum": 2.0, "default": 1.0},
        "outAt": {"type": "number", "title": "Animate Out At (s, 0 = end)", "minimum": 0, "maximum": 6, "default": 0},
        "accentColor": color_prop("Accent Colour"),
    },
    css=f"""
.lines{{position:absolute;inset:0;width:100%;height:100%;overflow:visible}}
.lbl{{position:absolute;white-space:nowrap;background:rgba(7,18,43,.55);padding:{U(8)} {U(18)} {U(10)};border-radius:{U(12)}}}
.ph{{font-size:{U(52)};font-weight:800;color:var(--snow);line-height:1.2;text-shadow:0 {U(2)} {U(12)} rgba(0,0,0,.6),0 0 {U(3)} rgba(0,0,0,.4)}}
.pe{{display:flex;gap:{U(14)};align-items:baseline;font-size:{U(17)};font-weight:700;color:var(--accent);letter-spacing:.28em;text-shadow:0 {U(1)} {U(6)} rgba(0,0,0,.6)}}
.pm{{color:var(--snow);letter-spacing:.06em;font-size:{U(20)}}}""",
    build="""
this.$.svg=svgEl("svg",{class:"lines"},scene);
this.$.ring=svgEl("circle",{fill:"none",stroke:"var(--accent)","stroke-width":"3"},this.$.svg);
this.$.dot=svgEl("circle",{fill:"var(--accent)",stroke:"#07122b","stroke-width":"2"},this.$.svg);
this.$.arrow=svgEl("path",{fill:"var(--accent)"},this.$.svg);
this.$.lead=svgEl("path",{fill:"none",stroke:"#f5f8fc","stroke-width":"3","stroke-linecap":"round","stroke-linejoin":"round"},this.$.svg);
this.$.under=svgEl("line",{stroke:"var(--accent)","stroke-width":"4","stroke-linecap":"round"},this.$.svg);
this.$.lbl=el("div","lbl",scene); this.$.ph=el("div","ph deva",this.$.lbl);
const pe=el("div","pe pop",this.$.lbl); this.$.pe=el("span","",pe); this.$.pm=el("span","pm",pe);""",
    apply="""
const s=this._state; this.style.setProperty("--accent",s.accentColor||"#f4b03e");
setT(this.$.ph,s.peakHi||""); setT(this.$.pe,s.peakEn||"");
setT(this.$.pm,(s.showHeight&&s.heightM)?fmtM(s.heightM)+" m":""); this.$.svg.setAttribute("viewBox",`0 0 ${this._w} ${this._h}`);""",
    frame="""
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
this.$.under.setAttribute("stroke-width",String(4*u)); this.$.under.setAttribute("opacity",up>0?"1":"0");""",
))

# ------------------------------------------------------------------ 4. POP-UP TITLE
TEMPLATES.append(dict(
    id="spp-popup-title", name="SPP Pop-up Title", file="SPP-Popup-Title", duration=5,
    desc="Chapter / pop-up text: kicker, Hindi headline and English line with a wipe-in.",
    props={
        "kicker": {"type": "string", "title": "Kicker (small line, blank = hide)", "default": "अध्याय 2 · CHAPTER 2"},
        "titleHi": {"type": "string", "title": "Headline (Hindi)", "default": "दारमा वैली"},
        "titleEn": {"type": "string", "title": "English Line (blank = hide)", "default": "INTO THE DARMA VALLEY"},
        "position": select_prop("Position", ["Bottom left", "Bottom right", "Top left", "Top right", "Centre"], 4),
        "backdrop": {"type": "boolean", "title": "Darken Background", "default": True},
        "scale": {"type": "number", "title": "Size", "minimum": 0.5, "maximum": 2.0, "default": 1.0},
        "outAt": {"type": "number", "title": "Animate Out At (s, 0 = end)", "minimum": 0, "maximum": 5, "default": 0},
        "accentColor": color_prop("Accent Colour"),
    },
    css=f"""
.bd{{position:absolute;inset:0;background:radial-gradient(80% 70% at 50% 50%, rgba(7,18,43,.55), rgba(7,18,43,0) 75%)}}
.wrap{{position:absolute;display:flex;flex-direction:column}}
.kick{{display:flex;align-items:center;gap:{U(14)};font-size:{U(22)};font-weight:700;color:var(--accent);white-space:nowrap;text-shadow:0 {U(2)} {U(8)} rgba(0,0,0,.5)}}
.kb{{display:inline-block;width:{U(44)};height:{U(3)};background:var(--accent);border-radius:{U(2)};transform-origin:50% 50%}}
.clip{{overflow:hidden;padding:{U(6)} {U(4)} {U(4)}}}
.th{{font-size:{U(104)};font-weight:800;color:var(--snow);line-height:1.22;white-space:nowrap;text-shadow:0 {U(4)} {U(24)} rgba(0,0,0,.5)}}
.te{{font-size:{U(22)};font-weight:500;color:var(--snow);opacity:.9;white-space:nowrap;text-shadow:0 {U(2)} {U(10)} rgba(0,0,0,.5)}}""",
    build="""
this.$.bd=el("div","bd",scene); this.$.wrap=el("div","wrap",scene);
this.$.kick=el("div","kick mix",this.$.wrap); this.$.kb1=el("span","kb",this.$.kick); this.$.kt=el("span","",this.$.kick); this.$.kb2=el("span","kb",this.$.kick);
const c=el("div","clip",this.$.wrap); this.$.th=el("div","th deva",c); this.$.te=el("div","te pop",this.$.wrap);""",
    apply="""
const s=this._state; this.style.setProperty("--accent",s.accentColor||"#f4b03e");
setT(this.$.kt,s.kicker||""); this.$.kick.style.display=s.kicker?"flex":"none";
setT(this.$.th,s.titleHi||""); setT(this.$.te,s.titleEn||""); this.$.te.style.display=s.titleEn?"block":"none";
this.$.bd.style.display=s.backdrop?"block":"none";
const p=s.position|0; this._side=this._corner(this.$.wrap,p,110,110,70,560,280);
const al=p===4?"center":(this._side==="right"?"flex-end":"flex-start"); this.$.wrap.style.alignItems=al; this.$.wrap.style.textAlign=p===4?"center":this._side;
this.$.kb2.style.display=p===4?"inline-block":"none";
this.$.wrap.style.transformOrigin=p===4?"50% 50%":((this._side==="right"?"100% ":"0% ")+(p>=2?"0%":"100%"));
this.$.bd.style.background=p===4?"":`linear-gradient(${p>=2?"180deg":"0deg"}, rgba(7,18,43,.6), rgba(7,18,43,0) 45%)`;""",
    frame="""
const s=this._state,p=s.position|0,sc=s.scale||1;
this.$.bd.style.opacity=String(eo(seg(t,0,0.5)));
this.$.wrap.style.transform=(p===4?"translate(-50%,-50%) ":"")+`scale(${sc})`;
const kb=eo(seg(t,0.05,0.45)); this.$.kb1.style.transform=this.$.kb2.style.transform=`scaleX(${kb})`;
const kt=eo(seg(t,0.15,0.5)); this.$.kt.style.opacity=String(kt); this.$.kt.style.letterSpacing=(0.5-0.28*kt).toFixed(3)+"em";
const h=eo(seg(t,0.2,0.8)); this.$.th.style.transform=`translateY(${Math.round(110*this._u*(1-h))}px)`;
const e=eo(seg(t,0.55,1.1)); this.$.te.style.opacity=String(e*0.92); this.$.te.style.letterSpacing=(0.6-0.3*e).toFixed(3)+"em";""",
))

# ------------------------------------------------------------------ 5. CREDITS
lines_default = [
    "कहानी और आवाज़ / Story & Voice | Pushpender Pannu",
    "कैमरा / Camera | Pushpender Pannu",
    "एडिट / Edit | Pushpender Pannu",
    "साथ में / Featuring | परिवार / Family",
    "संगीत / Music | Epidemic Sound",
    "", "",
]
credit_props = {"heading": {"type": "string", "title": "Heading", "default": "आभार · CREDITS"}}
for i, d in enumerate(lines_default, 1):
    credit_props[f"line{i}"] = {"type": "string", "title": f"Line {i}  (Role | Name, blank = hide)", "default": d}
credit_props.update({
    "showLogo": {"type": "boolean", "title": "Show Logo + Handle", "default": True},
    "handle": {"type": "string", "title": "Handle", "default": "@safar.pahad.parivar"},
    "backdrop": {"type": "boolean", "title": "Dark Background", "default": True},
    "outAt": {"type": "number", "title": "Animate Out At (s, 0 = end)", "minimum": 0, "maximum": 10, "default": 0},
    "accentColor": color_prop("Accent Colour"),
})
TEMPLATES.append(dict(
    id="spp-credits", name="SPP Credits", file="SPP-Credits", duration=10,
    desc="Credits page: heading, up to 7 'Role | Name' lines, logo and handle.",
    props=credit_props,
    css=f"""
.bd{{position:absolute;inset:0;background:rgba(7,18,43,.86)}}
.wrap{{position:absolute;left:50%;top:50%;display:flex;flex-direction:column;align-items:center;transform:translate(-50%,-50%)}}
.hd{{font-size:{U(26)};font-weight:700;color:var(--accent);letter-spacing:.3em;margin-bottom:{U(34)};white-space:nowrap}}
.rows{{display:grid;grid-template-columns:auto {U(40)} auto;row-gap:{U(18)};align-items:baseline}}
.r{{font-size:{U(29)};font-weight:500;color:rgba(245,248,252,.66);text-align:right;white-space:nowrap}}
.sep{{text-align:center;color:var(--accent);font-size:{U(26)}}}
.n{{font-size:{U(38)};font-weight:800;color:var(--snow);white-space:nowrap}}
.brand{{display:flex;flex-direction:column;align-items:center;margin-top:{U(54)}}}
.brand svg{{width:{U(130)};height:auto}} .hn{{font-size:{U(26)};font-weight:700;color:var(--snow);margin-top:{U(8)}}}""",
    build="""
this.$.bd=el("div","bd",scene); this.$.wrap=el("div","wrap",scene);
this.$.hd=el("div","hd mix",this.$.wrap); this.$.rows=el("div","rows mix",this.$.wrap); this.$.cells=[];
for(let i=0;i<7;i++){const r=el("div","r",this.$.rows),sp=el("div","sep",this.$.rows,"·"),n=el("div","n",this.$.rows);this.$.cells.push([r,sp,n]);}
this.$.brand=el("div","brand",this.$.wrap,MARK_SVG); this.$.hn=el("div","hn pop",this.$.brand);""",
    apply="""
const s=this._state; this.style.setProperty("--accent",s.accentColor||"#f4b03e");
setT(this.$.hd,s.heading||""); this.$.hd.style.display=s.heading?"block":"none";
this.$.bd.style.display=s.backdrop?"block":"none";
this._vis=[];
for(let i=0;i<7;i++){const v=(s["line"+(i+1)]||"").trim(); const [r,sp,n]=this.$.cells[i];
  const show=!!v; [r,sp,n].forEach(x=>x.style.display=show?"block":"none");
  if(show){const parts=v.split("|"); setT(r,(parts[0]||"").trim()); setT(n,(parts.slice(1).join("|")||"").trim()); this._vis.push(i);}}
this.$.brand.style.display=s.showLogo?"flex":"none"; setT(this.$.hn,s.handle||"");
this.$.wrap.style.transform=`translate(-50%,-50%) scale(${this._vertical?0.8:1})`;""",
    frame="""
this.$.bd.style.opacity=String(eo(seg(t,0,0.6)));
const h=eo(seg(t,0.2,0.8)); this.$.hd.style.opacity=String(h); this.$.hd.style.letterSpacing=(0.6-0.3*h).toFixed(3)+"em";
this._vis.forEach((i,j)=>{const q=eo(seg(t,0.5+0.16*j,1.0+0.16*j));this.$.cells[i].forEach(x=>{x.style.opacity=String(q);x.style.transform=`translateY(${Math.round(14*this._u*(1-q))}px)`;});});
const b=eo(seg(t,0.8+0.16*this._vis.length,1.4+0.16*this._vis.length)); this.$.brand.style.opacity=String(b); this.$.brand.style.transform=`translateY(${Math.round(12*this._u*(1-b))}px)`;""",
))


# ------------------------------------------------------------------ 6. CAPTIONS (SRT-driven, Devanagari-safe)
TEMPLATES.append(dict(
    id="spp-captions", name="SPP Captions", file="SPP-Captions", duration=1200,
    desc="Animated Hindi captions from pasted SRT text. Words animate whole, so Devanagari shaping stays correct.",
    props={
        "srt": {"type": "string", "gddType": "multi-line", "title": "SRT text (paste subtitles here)", "default": SAMPLE_SRT},
        "clipStart": {"type": "number", "title": "This clip starts at timeline time (s)", "minimum": 0, "maximum": 7200, "default": 0},
        "style": select_prop("Animation", ["Word pop + highlight", "Karaoke (colour sweep)", "Simple fade"], 0),
        "position": select_prop("Position", ["Bottom", "Raised (Shorts)", "Centre", "Top"], 0),
        "size": {"type": "number", "title": "Size", "minimum": 0.5, "maximum": 2.0, "default": 1.0},
        "plate": {"type": "boolean", "title": "Dark plate behind text", "default": False},
        "textColor": color_prop("Text Colour", "#f5f8fc"),
        "highlightColor": color_prop("Highlight Colour", "#f4b03e"),
    },
    css=f"""
.cap{{position:absolute;left:50%;display:flex;justify-content:center}}
.box{{text-align:center;font-weight:800;line-height:1.38;color:var(--txt);padding:{U(6)} {U(22)} {U(10)};border-radius:{U(14)}}}
.box.plate{{background:rgba(7,18,43,.62)}}
.w{{display:inline-block;white-space:pre;
   text-shadow:0 0 {U(3)} rgba(7,18,43,.95),0 {U(2)} {U(6)} rgba(7,18,43,.85),0 {U(4)} {U(18)} rgba(0,0,0,.45)}}
.box.plate .w{{text-shadow:none}}
.w.stress{{margin:0 .2em;transform-origin:50% 70%}}""",
    build=r"""
this.$.cap=el("div","cap",scene); this.$.box=el("div","box deva",this.$.cap);
this._cues=[]; this._srtKey=null; this._cueIdx=-2; this._words=[];""",
    apply=r"""
const s=this._state; this.style.setProperty("--txt",s.textColor||"#f5f8fc"); this.style.setProperty("--hl",s.highlightColor||"#f4b03e");
if(this._srtKey!==s.srt){this._srtKey=s.srt;this._cues=parseSRT(s.srt||"");this._cueIdx=-2;}
this.$.box.classList.toggle("plate",!!s.plate);
const v=this._vertical,p=s.position|0,sz=(s.size||1)*(v?60:54);
this.$.box.style.fontSize=Math.round(sz*this._u)+"px";
this.$.cap.style.width=(v?88:80)+"%";
this.$.cap.style.top=this.$.cap.style.bottom="auto";
if(p===0)this.$.cap.style.bottom=(v?14:8)+"%"; else if(p===1)this.$.cap.style.bottom=(v?30:20)+"%";
else if(p===3)this.$.cap.style.top=(v?16:7)+"%"; else this.$.cap.style.top="50%";
this._pos=p;""",
    frame=r"""
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
  else{w.style.opacity="1";w.style.transform=str?"scale(1.1)":"none";w.style.color=str?"var(--hl)":"";}});""",
))

# ------------------------------------------------------------------ write files
# ------------------------------------------------------------------ 7. ROUTE MAP (route.json from Tools/spp_gps.py)
TEMPLATES.append(dict(
    id="spp-route-map", name="SPP Route Map", file="SPP-Route-Map", duration=40,
    desc="Animated trip route: dotted path drawn over a relief map, stops pop up with arrival / departure times.",
    props={
        "routeFile": {"type": "string", "gddType": "file-path", "gddOptions": {"extensions": [".json"]},
                      "title": "Route file (route.json made by spp_gps.py)", "default": ""},
        "titleHi": {"type": "string", "title": "Title (Hindi)", "default": "हमारा सफ़र"},
        "titleEn": {"type": "string", "title": "Title (English)", "default": "OUR ROUTE"},
        "drawStart": {"type": "number", "title": "Route starts drawing at (s)", "minimum": 0, "maximum": 20, "default": 1.2},
        "drawEnd": {"type": "number", "title": "Route finished at (s)", "minimum": 2, "maximum": 40, "default": 12},
        "pause": {"type": "number", "title": "Pause at each stop (s)", "minimum": 0, "maximum": 4, "default": 1.0},
        "camera": select_prop("Camera", ["Whole route", "Follow the journey"], 1),
        "zoom": {"type": "number", "title": "Follow zoom", "minimum": 1.2, "maximum": 4, "default": 2.0},
        "showTimes": {"type": "boolean", "title": "Show arrival / departure times", "default": True},
        "showClock": {"type": "boolean", "title": "Show running date & time", "default": True},
        "keepLabels": {"type": "boolean", "title": "Keep earlier stop names", "default": True},
        "dim": {"type": "number", "title": "Darken map", "minimum": 0, "maximum": 0.8, "default": 0.1},
        "outAt": {"type": "number", "title": "Animate Out At (s, 0 = end)", "minimum": 0, "maximum": 40, "default": 0},
        "accentColor": color_prop("Accent Colour"),
    },
    css=f"""
.cam{{position:absolute;inset:0;transform-origin:0 0;will-change:transform}}
.cam img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
.cam svg{{position:absolute;inset:0;width:100%;height:100%;overflow:visible}}
.dim{{position:absolute;inset:0;background:#07122b}}
.lab{{position:absolute;transform-origin:0 0}}
.card{{position:absolute;left:{U(26)};top:{U(-40)};background:rgba(7,18,43,.86);border:{U(2)} solid rgba(245,248,252,.16);
  border-left:{U(6)} solid var(--accent);border-radius:{U(14)};padding:{U(10)} {U(18)} {U(12)};white-space:nowrap;
  box-shadow:0 {U(10)} {U(30)} rgba(0,0,0,.35);transform-origin:0 50%}}
.lab.left .card{{left:auto;right:{U(26)};border-left:{U(2)} solid rgba(245,248,252,.16);border-right:{U(6)} solid var(--accent);transform-origin:100% 50%}}
.lab.below .card{{top:{U(14)}}}
.card .hi{{font-weight:800;font-size:{U(40)};color:#f5f8fc;line-height:1.15}}
.card .en{{font:700 {U(16)}/1.2 \"SPP Pop\",\"Poppins\",sans-serif;letter-spacing:.14em;color:var(--accent);margin-top:{U(2)}}}
.card .tm{{font:500 {U(19)}/1.35 \"SPP Pop\",\"SPP Deva\",\"Nirmala UI\",sans-serif;color:rgba(245,248,252,.86);margin-top:{U(6)}}}
.card .tm b{{color:var(--accent);font-weight:700}}
.lab.small .card{{padding:{U(6)} {U(12)};border-width:{U(1)}}}
.lab.small .en,.lab.small .tm{{display:none}}
.lab.small .hi{{font-size:{U(28)}}}
.ttl{{position:absolute;left:{U(70)};top:{U(56)}}}
.ttl .hi{{font-weight:800;font-size:{U(66)};color:#f5f8fc;line-height:1.1;text-shadow:0 {U(3)} {U(18)} rgba(7,18,43,.9)}}
.ttl .en{{font:700 {U(20)}/1.4 \"SPP Pop\",\"Poppins\",sans-serif;letter-spacing:.2em;color:var(--accent);margin-top:{U(4)};text-shadow:0 {U(2)} {U(10)} rgba(7,18,43,.9)}}
.clock{{position:absolute;left:{U(70)};top:{U(186)};display:flex;align-items:center;gap:{U(12)};background:rgba(7,18,43,.8);
  border-radius:{U(40)};padding:{U(8)} {U(22)} {U(8)} {U(14)};font:600 {U(26)}/1 \"SPP Pop\",\"SPP Deva\",\"Nirmala UI\",sans-serif;color:#f5f8fc}}
.clock svg{{width:{U(30)};height:{U(30)}}}
.credit{{position:absolute;right:{U(24)};bottom:{U(16)};font:500 {U(13)}/1 \"SPP Pop\",\"Poppins\",sans-serif;color:rgba(245,248,252,.6)}}
.msg{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);background:rgba(7,18,43,.9);color:#f5f8fc;
  padding:{U(24)} {U(34)};border-radius:{U(16)};font:600 {U(28)}/1.5 \"SPP Pop\",\"SPP Deva\",\"Nirmala UI\",sans-serif;text-align:center;border:{U(2)} solid var(--accent)}}""",
    build=r"""
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
this._route=null; this._routeKey=null; this._err="";""",
    apply=r"""
const s=this._state; this.style.setProperty("--accent",s.accentColor||"#f4b03e");
setT(this.$.ttl.children[0],s.titleHi||""); setT(this.$.ttl.children[1],s.titleEn||"");
this.$.ttl.style.display=(s.titleHi||s.titleEn)?"block":"none";
this.$.dim.style.opacity=String(clamp(+s.dim||0,0,0.8));
const R=this._route;
this.$.msg.style.display=R?"none":"block";
if(!R){this.$.clock.style.display="none";this.$.credit.style.display="none";this.$.msg.innerHTML=this._err||"SPP Route Map<br>Choose <b>route.json</b> in the Inspector<br><small>(Tools\\spp_gps.py route …)</small>";return;}
if(this._builtFor!==R){this._builtFor=R;this._buildRoute(R);}
this.$.clock.style.display=s.showClock&&R.hasTime?"flex":"none"; this.$.credit.style.display="block";""",
    frame=r"""
const s=this._state,R=this._route; if(!R)return;
const u=this._u,v=this._vertical;
// ---- title
const ti=eo(seg(t,0.2,0.9)); this.$.ttl.style.opacity=String(ti); this.$.ttl.style.transform=`translateY(${Math.round((1-ti)*-20*u)}px)`;
// ---- journey schedule -> head fraction
const st=R.stops,n=st.length,a0=+s.drawStart||0,a1=Math.max(a0+1,+s.drawEnd||a0+10),P=Math.max(0,+s.pause||0);
const move=Math.max(0.5,(a1-a0)-P*(n-1)); let f=0,k=0,arrived=0,clockT=null;
{let tc=a0+P; if(t<tc){f=0;arrived=t>=a0?1:0;clockT=st[0].leave_t||null;}else{f=1;arrived=n;clockT=st[n-1].arrive_t||null;
  for(let i=1;i<n;i++){const df=Math.max(0,st[i].f-st[i-1].f),dur=move*df,te=tc+dur;
    if(t<te){const q=(t-tc)/Math.max(dur,1e-6);const e=q<.5?4*q*q*q:1-Math.pow(-2*q+2,3)/2;f=st[i-1].f+df*e;arrived=i;clockT=this._segTime(i-1,i,f);break;}
    tc=te; if(i<n-1){if(t<tc+P){f=st[i].f;arrived=i+1;clockT=(t-tc<P*0.5)?(st[i].arrive_t||null):(st[i].leave_t||null);break;} tc+=P;}}}}
const hp=this._at(f);
// ---- camera
const cam=s.camera|0,Z=cam===1?clamp(+s.zoom||2,1.2,4):1;
const zin=eo(seg(t,a0-0.6,a0+0.8)),zout=eo(seg(t,a1+0.2,a1+1.6)),zk=cam===1?zin*(1-zout):0,z=1+(Z-1)*zk;
const sm=this._at(clamp(f-0.02,0,1)),sm2=this._at(clamp(f+0.02,0,1));
let cx=(sm[0]+hp[0]+sm2[0])/3,cy=(sm[1]+hp[1]+sm2[1])/3;
cx=0.5+(cx-0.5)*zk; cy=0.5+(cy-0.5)*zk;
cx=clamp(cx,0.5/z,1-0.5/z); cy=clamp(cy,0.5/z,1-0.5/z);
const W=this._w,H=this._h,tx=W*(0.5-cx*z),ty=H*(0.5-cy*z);
this.$.cam.style.transform=`translate(${tx.toFixed(2)}px,${ty.toFixed(2)}px) scale(${z.toFixed(5)})`;
// ---- path
const px=(p)=>(p[0]*R.w).toFixed(1)+","+(p[1]*R.h).toFixed(1);
const pts=R.path,iv=[];
for(let i=0;i<pts.length&&pts[i][2]<=f;i++)iv.push(px(pts[i]));
if(f>0)iv.push(px(hp));
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
  const ta=(i===0?a0:this._arriveT(i,a0,move,P));
  const k1=eb(seg(t,ta,ta+0.45)),k0=eo(seg(t,ta,ta+0.3));
  p.style.opacity=String(k0); p.setAttribute("transform",`translate(${(st[i].x*R.w).toFixed(1)},${(st[i].y*R.h).toFixed(1)}) scale(${(0.2+0.8*k1).toFixed(3)})`);
  const later=i<arrived-1&&arrived>i+1;
  const old=later&&t>=this._arriveT(i+1,a0,move,P)+0.3;
  L.classList.toggle("small",old);
  L.style.display=(old&&!s.keepLabels)?"none":"block";
  L.style.opacity=String(k0*(old?0.85:1));
  L.style.transform=`scale(${(1/z).toFixed(5)})`;
  L.firstChild.style.transform=`scale(${(0.6+0.4*k1).toFixed(3)})`;
  L.querySelector(".tm").style.display=(s.showTimes&&!old)?"block":"none";}
// ---- clock
if(s.showClock&&R.hasTime){const tt=clockT;if(tt){const ci=eo(seg(t,a0-0.3,a0+0.3));this.$.clock.style.opacity=String(ci);
  setT(this.$.clock.lastChild,this._fmtClock(tt));}}
this.$.credit.style.opacity=String(eo(seg(t,0.5,1.2)));""",
    extra=r"""
async _prepare(){const key=this._state.routeFile||"";if(key===this._routeKey)return;this._routeKey=key;this._route=null;this._err="";
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
_arriveT(i,a0,move,P){const st=this._route.stops;let tc=a0+P;for(let j=1;j<=i;j++){tc+=move*Math.max(0,st[j].f-st[j-1].f);if(j<i)tc+=P;}return tc;}
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
  return `${d.getUTCDate()} ${M[d.getUTCMonth()]} · ${h}:${String(m).padStart(2,"0")} ${ap}`;}""",
))

for T in TEMPLATES:
    defaults = {k: v["default"] for k, v in T["props"].items()}
    cls = "".join(w.capitalize() for w in T["file"].replace("SPP-", "").split("-")) + "Graphic"
    js = (f"const DEFAULTS={json.dumps(defaults, ensure_ascii=False)};\nconst DURATION={T['duration']};\n"
          f"const CSS=`{T['css']}`;\n" + BASE +
          f"\nclass {cls} extends SPPGraphic{{\n_build(scene){{{T['build']}\n}}\n_apply(){{{T['apply']}\n}}\n_frame(t,out){{{T['frame']}\n}}\n{T.get('extra','')}\n}}\nexport default {cls};\n")
    manifest = {
        "$schema": "https://ograf.ebu.io/v1/specification/json-schemas/graphics/schema.json",
        "id": T["id"], "version": "1.0.0", "name": T["name"], "description": T["desc"],
        "author": {"name": "Safar Pahad Parivar"}, "main": T["file"] + ".js",
        "supportsRealTime": False, "supportsNonRealTime": True, "stepCount": 1,
        "schema": {"type": "object", "additionalProperties": False, "properties": T["props"]},
        "renderRequirements": [{"resolution": {"width": {"ideal": 1920}, "height": {"ideal": 1080}},
                                "frameRate": {"ideal": 30}, "accessToPublicInternet": False}],
        "v_bmd": {"duration": T["duration"]},
    }
    open(os.path.join(OUT, T["file"] + ".js"), "w", encoding="utf-8").write(js)
    open(os.path.join(OUT, T["file"] + ".ograf.json"), "w", encoding="utf-8").write(json.dumps(manifest, ensure_ascii=False, indent=2))
    print("wrote", T["file"], len(T["props"]), "props")
shutil.copytree(os.path.join(SRC, "fonts"), os.path.join(OUT, "fonts"), dirs_exist_ok=True)
print("fonts copied")
