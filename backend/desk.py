"""Adviser desk: a browser page (desktop/laptop) for reading leads and downloading the CRM file.
Served by the backend so it keeps working after Publish (the app's own web build isn't hosted)."""
from html import escape

_PAGE = r"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>__APP__ · Adviser desk</title><style>
*{box-sizing:border-box}body{margin:0;font-family:Arial,Helvetica,sans-serif;background:#F5F3EE;color:#2C2A28}
header{background:#223342;color:#fff;padding:14px 24px;display:flex;align-items:center;gap:16px}
header img{height:40px}header .sp{flex:1}header .who{font-size:14px;color:#D9D4C7}
button,.btn{font:inherit;cursor:pointer;border-radius:10px;border:0;padding:10px 16px;font-weight:700;text-decoration:none;display:inline-block}
.gold{background:#BF9B30;color:#fff}.gold:hover{background:#A8862A}.ghost{background:transparent;color:#fff;border:1px solid #6B7C8C}
.sec{background:#fff;color:#223342;border:1px solid #223342}
main{max-width:980px;margin:0 auto;padding:24px}
.card{background:#fff;border-radius:14px;padding:24px;box-shadow:0 1px 3px rgba(0,0,0,.06);margin-bottom:16px}
h1{color:#223342;margin:0 0 8px;font-size:26px}h2{color:#223342;font-size:18px;margin:0 0 12px}
.muted{color:#7D7973;font-size:14px}label{display:block;font-size:14px;font-weight:700;margin:14px 0 6px}
input{width:100%;padding:12px;border:1px solid #CFCAC0;border-radius:10px;font:inherit}
.err{color:#B3261E;margin-top:12px;font-size:14px}.ok{color:#2E7D32}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:10px 8px;border-bottom:1px solid #EEE9DF;font-size:14px}
th{color:#7D7973;font-weight:700}td.n,th.n{text-align:right}tr.row{cursor:pointer}tr.row:hover{background:#FBF8F1}
.pill{display:inline-block;padding:3px 10px;border-radius:99px;font-size:12px;font-weight:700}
.p-new{background:#FFF4D6;color:#8A6A10}.p-contacted{background:#E3EEF9;color:#1D4F80}.p-closed{background:#E8E8E8;color:#555}
.bar{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:16px}.bar .sp{flex:1}
.notice{background:#FFF4D6;border-left:4px solid #BF9B30;padding:10px 14px;border-radius:8px;font-size:14px;margin:12px 0}
.gap{color:#B3261E;font-weight:700}.nogap{color:#2E7D32;font-weight:700}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
a.link{color:#223342;font-weight:700}ul{margin:6px 0;padding-left:20px}li{margin:4px 0;font-size:14px}
.login{max-width:420px;margin:48px auto}
</style></head><body>
<header><img src="/api/static/logos/logo_dark_transparent.png" alt="__APP__"><div class="sp"></div>
<span class="who" id="who"></span><button class="ghost" id="logout" hidden>Log out</button></header>
<main id="app"><p class="muted">Loading…</p></main>
<script>
(function(){
var IDLE_MS=30*60*1000, REFRESH_MS=10*60*1000, K="sfs_desk";
var app=document.getElementById("app");
function h(tag,attrs){var e=document.createElement(tag);attrs=attrs||{};for(var k in attrs){if(k==="text")e.textContent=attrs[k];else if(k.slice(0,2)==="on")e.addEventListener(k.slice(2),attrs[k]);else e.setAttribute(k,attrs[k]);}
  for(var i=2;i<arguments.length;i++){var c=arguments[i];if(c==null||c===false)continue;e.appendChild(typeof c==="string"?document.createTextNode(c):c);}return e;}
function gbp(v){return "£"+Math.round(Number(v)||0).toLocaleString("en-GB");}
function when(s){if(!s)return "";var d=new Date(s);return d.toLocaleDateString("en-GB",{day:"numeric",month:"short",year:"numeric"})+" "+d.toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit"});}
var LABEL={"new":"New","contacted":"Contacted","closed":"Closed"};
function pill(s){return h("span",{"class":"pill p-"+s,text:LABEL[s]||s});}
function sess(){try{return JSON.parse(sessionStorage.getItem(K)||"null");}catch(e){return null;}}
function save(s){sessionStorage.setItem(K,JSON.stringify(s));}
function logout(msg){sessionStorage.removeItem(K);document.getElementById("who").textContent="";document.getElementById("logout").hidden=true;showLogin(msg);}
document.getElementById("logout").onclick=function(){logout("You've been logged out.");};
function touch(){var s=sess();if(!s)return;s.last=Date.now();save(s);}
["mousemove","keydown","click","scroll","touchstart"].forEach(function(ev){window.addEventListener(ev,touch,{passive:true});});
setInterval(function(){var s=sess();if(!s)return;var now=Date.now();
  if(now-s.last>IDLE_MS){logout("You were logged out after 30 minutes without activity.");return;}
  if(now-s.issued>REFRESH_MS&&now-s.last<REFRESH_MS){api("POST","/api/desk/refresh").then(function(r){var t=sess();if(t&&r){t.token=r.token;t.issued=Date.now();save(t);}}).catch(function(){});}
},30000);
function api(method,path){var s=sess();return fetch(path,{method:method,headers:s?{"Authorization":"Bearer "+s.token}:{}}).then(function(r){
  if(r.status===401){logout("Your session has ended. Please log in again.");throw new Error("401");}
  if(!r.ok)return r.json().catch(function(){return {};}).then(function(j){throw new Error(j.detail||"Something went wrong");});
  return r;}).then(function(r){return (r.headers.get("content-type")||"").indexOf("json")>=0?r.json():r;});}
function wantedLead(){var m=/lead=([a-f0-9]{24})/i.exec(location.hash);return m?m[1]:null;}

function showLogin(msg){
  document.getElementById("logout").hidden=true;document.getElementById("who").textContent="";
  app.innerHTML="";var err=h("div",{"class":"err",id:"login-error"});if(msg){err.textContent=msg;err.className="muted";}
  var email=h("input",{type:"email",id:"login-email",autocomplete:"username",required:""});
  var pw=h("input",{type:"password",id:"login-password",autocomplete:"current-password",required:""});
  var btn=h("button",{"class":"gold",type:"submit",id:"login-submit",style:"width:100%;margin-top:20px",text:"Log in"});
  var f=h("form",{},h("label",{"for":"login-email",text:"Email"}),email,h("label",{"for":"login-password",text:"Password"}),pw,btn,err);
  f.onsubmit=function(e){e.preventDefault();btn.disabled=true;btn.textContent="Logging in…";err.className="err";err.textContent="";
    fetch("/api/desk/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:email.value.trim(),password:pw.value})})
    .then(function(r){return r.json().then(function(j){if(!r.ok)throw new Error(j.detail||"Couldn't log in");return j;});})
    .then(function(j){save({token:j.token,name:j.user.name,issued:Date.now(),last:Date.now()});route();})
    .catch(function(x){err.textContent=x.message;btn.disabled=false;btn.textContent="Log in";});};
  app.appendChild(h("div",{"class":"card login",id:"login-card"},h("h1",{text:"Adviser desk"}),
    h("p",{"class":"muted",text:wantedLead()?"Log in to view this lead.":"Log in to see your leads and download them for your CRM."}),f));
  email.focus();}

function download(){var b=document.getElementById("download-crm");b.disabled=true;b.textContent="Preparing…";
  api("GET","/api/adviser/leads/export").then(function(r){return r.blob().then(function(blob){
    var name=((r.headers.get("content-disposition")||"").match(/filename="([^"]+)"/)||[])[1]||"leads.csv";
    var a=h("a",{href:URL.createObjectURL(blob),download:name});document.body.appendChild(a);a.click();a.remove();});})
  .catch(function(e){alert(e.message);}).finally(function(){b.disabled=false;b.textContent="Download for CRM";});}

function showList(){
  app.innerHTML="";app.appendChild(h("p",{"class":"muted",text:"Loading leads…"}));
  api("GET","/api/adviser/leads").then(function(leads){app.innerHTML="";
    var bar=h("div",{"class":"bar"},h("h1",{text:"Your leads"}),h("div",{"class":"sp"}),
      h("button",{"class":"gold",id:"download-crm",onclick:download,text:"Download for CRM"}));
    var card=h("div",{"class":"card"});
    if(!leads.length){card.appendChild(h("p",{"class":"muted",id:"no-leads",text:"No leads yet. New call-back requests will appear here."}));}
    else{var tb=h("tbody");leads.forEach(function(l){
      tb.appendChild(h("tr",{"class":"row","data-testid":"lead-row",onclick:function(){location.hash="lead="+l.id;}},
        h("td",{},h("a",{"class":"link",href:"#lead="+l.id,text:l.name})),h("td",{text:when(l.created_at)}),h("td",{},pill(l.status)),
        h("td",{text:l.source_label||""}),h("td",{"class":"n",text:l.summary&&l.summary.life_gap!=null?gbp(l.summary.life_gap):"–"})));});
      card.appendChild(h("table",{id:"lead-table"},h("thead",{},h("tr",{},h("th",{text:"Name"}),h("th",{text:"Received"}),h("th",{text:"Status"}),h("th",{text:"Came from"}),h("th",{"class":"n",text:"Life cover gap"}))),tb));}
    app.appendChild(bar);app.appendChild(card);
    app.appendChild(h("p",{"class":"muted",text:"The CRM file has contact details and consent only, ready to import into Greenlight."}));
  }).catch(function(e){if(e.message!=="401"){app.innerHTML="";app.appendChild(h("p",{"class":"err",text:e.message}));}});}

function showLead(id){
  app.innerHTML="";app.appendChild(h("p",{"class":"muted",text:"Loading lead…"}));
  api("GET","/api/adviser/leads/"+id).then(function(l){app.innerHTML="";
    var back=h("a",{"class":"link",href:"#",id:"back-to-list",text:"← All leads"});
    var top=h("div",{"class":"card",id:"lead-detail"},
      h("div",{"class":"bar"},h("h1",{id:"lead-name",text:l.name}),pill(l.status)),
      h("p",{"class":"muted",text:"Requested "+when(l.created_at)+(l.preferred_time?" · Prefers "+l.preferred_time.toLowerCase():"")}),
      h("p",{"class":"muted",text:"Came from: "+l.source_label+(l.source_code?" (code "+l.source_code+")":"")+(l.heard_from?" · Heard via "+l.heard_from:"")}),
      h("div",{"class":"grid"},
        h("div",{},h("div",{"class":"muted",text:"Phone"}),h("a",{"class":"link",id:"lead-phone",href:"tel:"+(l.phone||"").replace(/[^0-9+]/g,""),text:l.phone})),
        h("div",{},h("div",{"class":"muted",text:"Email"}),h("a",{"class":"link",id:"lead-email",href:"mailto:"+l.email,text:l.email}))),
      l.message?h("div",{},h("label",{text:"Their message"}),h("p",{id:"lead-message",text:l.message})):null);
    app.appendChild(h("p",{},back));app.appendChild(top);
    var a=l.assessment,card=h("div",{"class":"card",id:"lead-family"});
    if(!a){card.appendChild(h("p",{"class":"muted",text:"This family hadn't completed a check when they asked for a call."}));}
    else{var r=a.results||{},g=r.gaps||{},i=a.inputs||{};
      card.appendChild(h("h2",{text:"Their family check"}));
      card.appendChild(h("div",{"class":"notice",id:"lead-unverified",text:"Client-entered, not yet verified. Confirm at fact-find."}));
      if(r.headline)card.appendChild(h("p",{},h("strong",{text:r.headline})));
      var tb=h("tbody");[["Life cover",g.life,""],["Income protection",g.income,"/mo"],["Critical illness",g.critical,""]].forEach(function(x){if(!x[1])return;
        tb.appendChild(h("tr",{},h("td",{text:x[0]}),h("td",{"class":"n",text:gbp(x[1].need)+x[2]}),h("td",{"class":"n",text:gbp(x[1].have)+x[2]}),
          h("td",{"class":"n "+(x[1].gap>0?"gap":"nogap"),text:gbp(x[1].gap)+x[2]})));});
      card.appendChild(h("table",{id:"lead-cover-table"},h("thead",{},h("tr",{},h("th",{text:""}),h("th",{"class":"n",text:"Needs"}),h("th",{"class":"n",text:"Has"}),h("th",{"class":"n",text:"Gap"}))),tb));
      var n=function(v){return Number(v)||0;};var ul=h("ul",{id:"lead-existing-cover"});
      ["Life insurance: "+(n(i.life_cover)?gbp(i.life_cover):"none"),
       "Death in service: "+(n(i.death_in_service)?i.death_in_service+"× salary ("+gbp(n(i.death_in_service)*n(i.annual_income))+")":"none"),
       "Income protection: "+(n(i.income_protection)?gbp(i.income_protection)+"/mo":"none"),
       "Critical illness: "+(n(i.critical_illness)?gbp(i.critical_illness):"none"),
       "Employer sick pay: "+(n(i.sick_pay_months)?i.sick_pay_months+" month"+(n(i.sick_pay_months)===1?"":"s"):"statutory only"),
       "Savings: "+gbp(i.savings)].forEach(function(t){ul.appendChild(h("li",{text:t}));});
      card.appendChild(h("label",{text:"What they have now"}));card.appendChild(ul);
      card.appendChild(h("p",{"class":"muted",text:"“Has” for life cover includes life insurance, death in service and savings."}));
      if(i.worry)card.appendChild(h("p",{"class":"muted",text:"Biggest worry: "+i.worry}));}
    app.appendChild(card);
    app.appendChild(h("p",{"class":"muted",text:"To update the status or action a data-deletion request, open this lead in the app."}));
  }).catch(function(e){if(e.message!=="401"){app.innerHTML="";app.appendChild(h("p",{},h("a",{"class":"link",href:"#",text:"← All leads"})));
    app.appendChild(h("div",{"class":"card"},h("p",{"class":"err",id:"lead-error",text:e.message==="Lead not found"?"We couldn't find that lead on your account.":e.message})));}});}

function route(){var s=sess();if(!s||Date.now()-s.last>IDLE_MS){if(s)sessionStorage.removeItem(K);showLogin();return;}
  document.getElementById("who").textContent=s.name;document.getElementById("logout").hidden=false;
  var id=wantedLead();if(id)showLead(id);else showList();window.scrollTo(0,0);}
window.addEventListener("hashchange",route);route();
})();
</script></body></html>"""


def desk_page(*, app_name: str) -> str:
    return _PAGE.replace("__APP__", escape(app_name))
