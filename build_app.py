import sys

code = """
const KEY='twostones.v1',uid=()=>Math.random().toString(36).slice(2,9),N=v=>parseFloat(v)||0,today=()=>new Date().toISOString().slice(0,10),mon=d=>(d||'').slice(0,7);
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let S={settings:{},clients:[],orders:[],payments:[],materials:[],usage:[],expenses:[],products:[]},V='dash',ID=null,M=today().slice(0,7);
let user = null;

async function initApp() {
  try {
    const { data: { session }, error } = await window.supabase.auth.getSession();
    if (error) throw error;
    user = session?.user;
    if (!user) {
      document.getElementById('app').innerHTML = `<div style="max-width:300px;margin:100px auto;text-align:center;"><h2>Login</h2>
      <input id="em" type="email" placeholder="Email" style="margin:10px 0"><input id="pw" type="password" placeholder="Password" style="margin:10px 0">
      <button class="btn pri" onclick="doLogin()">Log in / Sign up</button></div>`;
      return;
    }
    await loadCloudData();
    R();
  } catch (err) {
    console.error(err);
    document.getElementById('app').innerHTML = `<div style="max-width:400px;margin:100px auto;text-align:center;"><h2>Connection Error</h2><p>${esc(err.message||err)}</p><button class="btn" onclick="location.reload()">Retry</button></div>`;
  }
}
window.onload = initApp;

async function doLogin() {
  const email = document.getElementById('em').value, password = document.getElementById('pw').value;
  let { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error && error.message.includes('Invalid login')) {
    const res = await supabase.auth.signUp({ email, password });
    error = res.error;
    if(!error) toast('Account created. Please log in again or check email.');
  }
  if (error) return toast(error.message);
  location.reload();
}

async function doLogout() {
  await supabase.auth.signOut();
  location.reload();
}

async function loadCloudData() {
  const [set, cl, pr, ord, itm, pay, mat, usg, exp] = await Promise.all([
    supabase.from('pricing_settings').select('*').maybeSingle(),
    supabase.from('clients').select('*'),
    supabase.from('products').select('*'),
    supabase.from('orders').select('*'),
    supabase.from('order_items').select('*'),
    supabase.from('payments').select('*'),
    supabase.from('materials').select('*'),
    supabase.from('material_usage').select('*'),
    supabase.from('expenses').select('*')
  ]);
  
  S.settings = set.data || {name:'Twostones',cur:'KES',labour:500,oh:215,margin:30,markup:30,wm:40,rm:50,mode:'margin',opening_cash_balance:0};
  S.clients = (cl.data||[]).map(r=>({id:r.id, name:r.name, phone:r.phone, email:r.email, notes:r.notes}));
  S.products = (pr.data||[]).map(r=>({id:r.id, name:r.name, fabQty:r.fab_qty, fabCost:r.fab_cost, hours:r.hours, trims:r.trims, pack:r.pack}));
  S.orders = (ord.data||[]).map(o=>{
    const i = (itm.data||[]).find(x=>x.order_id===o.id) || {};
    return {id:o.id, no:o.no, date:o.date, clientId:o.client_id, type:o.type, due:o.due, status:o.status, notes:o.notes,
      priority:o.priority||'Normal', prod_start:o.prod_start, prod_end:o.prod_end, delivered_date:o.delivered_date,
      name:i.name, qty:i.qty, price:i.price, hours:i.hours, estMat:i.est_mat, estOther:i.est_other,
      actHours:i.act_hours, actLabOverride:i.act_lab_override, actMat:i.act_mat, actOther:i.act_other,
      design:i.design, fabric:i.fabric, fabQty:i.fab_qty, measure:i.measure};
  });
  S.payments = (pay.data||[]).map(r=>({id:r.id, orderId:r.order_id, date:r.date, amt:r.amt, method:r.method, ref:r.ref}));
  S.materials = (mat.data||[]).map(r=>({id:r.id, date:r.date, supplier:r.supplier, name:r.name, cat:r.category, qty:r.qty, unit:r.unit, cpu:r.cost_per_unit, notes:r.notes}));
  S.usage = (usg.data||[]).map(r=>({id:r.id, matId:r.mat_id, orderId:r.order_id, qty:r.qty}));
  S.expenses = (exp.data||[]).map(r=>({id:r.id, date:r.date, desc:r.desc_text, cat:r.cat, amt:r.amt, method:r.method, payee:r.payee, orderId:r.order_id, notes:r.notes}));
}

async function syncSave(coll, r) {
  const u = {user_id: user.id};
  if(coll==='clients') await supabase.from('clients').upsert([{...u, id:r.id, name:r.name, phone:r.phone, email:r.email, notes:r.notes}]);
  if(coll==='products') await supabase.from('products').upsert([{...u, id:r.id, name:r.name, fab_qty:N(r.fabQty), fab_cost:N(r.fabCost), hours:N(r.hours), trims:N(r.trims), pack:N(r.pack)}]);
  if(coll==='payments') await supabase.from('payments').upsert([{...u, id:r.id, order_id:r.orderId, date:r.date, amt:N(r.amt), method:r.method, ref:r.ref}]);
  if(coll==='materials') await supabase.from('materials').upsert([{...u, id:r.id, date:r.date, supplier:r.supplier, name:r.name, category:r.cat, qty:N(r.qty), unit:r.unit, cost_per_unit:N(r.cpu), notes:r.notes}]);
  if(coll==='usage') await supabase.from('material_usage').upsert([{...u, id:r.id, mat_id:r.matId, order_id:r.orderId, qty:N(r.qty)}]);
  if(coll==='expenses') await supabase.from('expenses').upsert([{...u, id:r.id, date:r.date, desc_text:r.desc, cat:r.cat, amt:N(r.amt), method:r.method, payee:r.payee, order_id:r.orderId||null, notes:r.notes}]);
  if(coll==='orders') {
    await supabase.from('orders').upsert([{...u, id:r.id, no:r.no, date:r.date, client_id:r.clientId, type:r.type, due:r.due||null, status:r.status, notes:r.notes, priority:r.priority||'Normal', prod_start:r.prod_start||null, prod_end:r.prod_end||null, delivered_date:r.delivered_date||null}]);
    await supabase.from('order_items').upsert([{...u, id:r.id, order_id:r.id, name:r.name, qty:N(r.qty), price:N(r.price), hours:N(r.hours), est_mat:N(r.estMat), est_other:N(r.estOther), act_hours:r.actHours?N(r.actHours):null, act_lab_override:r.actLabOverride?N(r.actLabOverride):null, act_mat:N(r.actMat), act_other:N(r.actOther), design:r.design, fabric:r.fabric, fab_qty:N(r.fabQty), measure:r.measure}]);
  }
}

async function syncDel(coll, id) {
  if(coll==='orders') await supabase.from('order_items').delete().eq('order_id', id);
  await supabase.from(coll==='usage'?'material_usage':coll).delete().eq('id', id);
}

const K=n=>S.settings.cur+' '+Math.round(n||0).toLocaleString('en-US'),P=n=>(isFinite(n)?n:0).toFixed(1)+'%',rp=x=>Math.round(x/50)*50;
const price=(c,p,m)=>m==='margin'?(p>=100?NaN:c/(1-p/100)):c*(1+p/100);
const sum=(a,f)=>a.reduce((x,y)=>x+f(y),0),cl=id=>S.clients.find(c=>c.id===id),cn=id=>cl(id)?.name||'—';
const cls=n=>n<0?'bad':'good';
function toast(t){const e=document.getElementById('toast');e.textContent=t;e.style.display='block';setTimeout(()=>e.style.display='none',2200)}

function ocalc(o){const st=S.settings,q=N(o.qty)||1,total=N(o.price)*q,paid=sum(S.payments.filter(p=>p.orderId===o.id),p=>N(p.amt));
const used=sum(S.usage.filter(u=>u.orderId===o.id),u=>{const m=S.materials.find(m=>m.id===u.matId);return N(u.qty)*(m?N(m.cpu):0)});
const linked=sum(S.expenses.filter(e=>e.orderId===o.id),e=>N(e.amt)),h=N(o.hours);
const eMat=N(o.estMat),eLab=h*st.labour,eOh=h*st.oh,eOth=N(o.estOther),est=eMat+eLab+eOh+eOth;
const actH = o.actHours!==undefined && o.actHours!=='' && o.actHours!==null ? N(o.actHours) : h;
const aLabCalc = actH * st.labour;
const aLab = o.actLabOverride!==undefined && o.actLabOverride!=='' && o.actLabOverride!==null ? N(o.actLabOverride) : aLabCalc;
const aMat=used+N(o.actMat),aOth=N(o.actOther)+linked;
const has=aMat>0||aLab!==eLab||aOth>0||used>0;
const act=aMat+aLab+eOh+aOth,cost=has?act:est;
return{total,paid,bal:total-paid,est,act,has,cost,profit:total-cost,margin:total?(total-cost)/total*100:0,mat:has?aMat:eMat,lab:has?aLab:eLab,oh:eOh,oth:has?aOth:eOth,used,linked}}

const pstat=r=>r.paid<=0?'Unpaid':r.paid>=r.total?'Fully paid':r.paid<r.total/2?'Deposit paid':'Partially paid';
function mstat(m){const os=S.orders.filter(o=>mon(o.date)===m&&o.status!=='Cancelled').map(o=>({o,...ocalc(o)}));
const sales=sum(os,r=>r.total),cost=sum(os,r=>r.cost),coll=sum(S.payments.filter(p=>mon(p.date)===m),p=>N(p.amt)),exps=S.expenses.filter(e=>mon(e.date)===m),
matSp=sum(S.materials.filter(x=>mon(x.date)===m),x=>N(x.qty)*N(x.cpu)),expT=sum(exps,e=>N(e.amt));
const owed=sum(S.orders.filter(o=>o.status!=='Cancelled').map(ocalc),r=>Math.max(0,r.bal));
return{os,sales,cost,coll,matSp,expT,out:matSp+expT,gp:sales-cost,owed,lab:sum(os,r=>r.lab),oh:sum(os,r=>r.oh),exps}}
function flow(m){const pIn=S.payments.filter(p=>mon(p.date)<m),pre=sum(pIn,p=>N(p.amt))-sum(S.expenses.filter(e=>mon(e.date)<m),e=>N(e.amt))-sum(S.materials.filter(x=>mon(x.date)<m),x=>N(x.qty)*N(x.cpu));return N(S.settings.opening_cash_balance)+pre}

/* forms */
const opt=o=>Array.isArray(o)?o:[o,o];
function fld([k,l,t,o],v){const val=v[k]??'',a=`<label>${l}`;
if(t==='header')return `<h4 style="grid-column:1/-1;margin:16px 0 4px;padding-top:12px;border-top:1px solid var(--line);color:var(--ink)">${l}</h4>`;
if(t==='clientSelect')return `<div style="margin-top:8px"><div style="font-size:13px;color:var(--mut);margin-bottom:2px">${l} <a class="l" style="float:right;text-decoration:none" onclick="inlineClient()">+ New Client</a></div><select id="f_${k}">${o.map(x=>{x=opt(x);return`<option value="${esc(x[0])}"${x[0]==val?' selected':''}>${esc(x[1])}</option>`}).join('')}</select><div id="ic_container"></div></div>`;
if(t==='select')return a+`<select id="f_${k}">${o.map(x=>{x=opt(x);return`<option value="${esc(x[0])}"${x[0]==val?' selected':''}>${esc(x[1])}</option>`}).join('')}</select></label>`;
if(t==='area')return a+`<textarea id="f_${k}" rows="2">${esc(val)}</textarea></label>`;
return a+`<input id="f_${k}" type="${t||'text'}" ${t==='number'?'step="any" inputmode="decimal"':''} value="${esc(val)}"></label>`}

function inlineClient() {
  const c = document.getElementById('ic_container');
  if (c.innerHTML !== '') return;
  c.innerHTML = `<div style="background:var(--bg);padding:10px;border:1px solid var(--line);border-radius:8px;margin-top:8px;grid-column:1/-1">
    <h4 style="margin:0 0 8px;color:var(--ink)">New Client</h4>
    <input id="ic_n" placeholder="Name (required)" style="margin-bottom:6px">
    <input id="ic_p" placeholder="Phone" style="margin-bottom:6px">
    <input id="ic_e" placeholder="Email" style="margin-bottom:6px">
    <textarea id="ic_x" placeholder="Notes" rows="2" style="margin-bottom:6px"></textarea>
    <div class="row"><button type="button" class="btn sm" onclick="document.getElementById('ic_container').innerHTML=''">Cancel</button><button type="button" class="btn sm pri" id="ic_btn" onclick="saveInlineClient()">Save Client</button></div>
  </div>`;
}

async function saveInlineClient() {
  const n = document.getElementById('ic_n').value.trim();
  if (!n) return toast('Client name required');
  const btn = document.getElementById('ic_btn');
  btn.disabled = true;
  btn.textContent = 'Saving...';
  
  const c = { id: uid(), name: n, phone: document.getElementById('ic_p').value, email: document.getElementById('ic_e').value, notes: document.getElementById('ic_x').value };
  
  try {
    await syncSave('clients', c);
    S.clients.push(c);
    
    const sel = document.getElementById('f_clientId');
    const opt = document.createElement('option');
    opt.value = c.id;
    opt.textContent = c.name;
    sel.appendChild(opt);
    sel.value = c.id;
    
    document.getElementById('ic_container').innerHTML = '';
    toast('Client created successfully');
  } catch(e) {
    console.error(e);
    toast('Error saving client');
    btn.disabled = false;
    btn.textContent = 'Save Client';
  }
}

function form(title,fields,v,cb){const d=document.getElementById('modal');d.innerHTML=`<div class="sheet"><h3>${title}</h3><div class="two" oninput="if(window.formOnInp)window.formOnInp()">${fields.map(f=>fld(f,v)).join('')}</div><div id="f_preview"></div><div class="row"><button class="btn" onclick="closeM()">Cancel</button><button class="btn pri" id="ok">Save</button></div></div>`;d.classList.add('on');
document.getElementById('ok').onclick=()=>{const r={...v};fields.forEach(f=>{if(f[2]!=='header')r[f[0]]=document.getElementById('f_'+f[0]).value});closeM();cb(r)}}
const closeM=()=>document.getElementById('modal').classList.remove('on');

window.orderPreview = () => {
  const due = document.getElementById('f_due')?.value;
  const hrs = N(document.getElementById('f_hours')?.value);
  const status = document.getElementById('f_status')?.value;
  const el = document.getElementById('f_preview');
  if(!el) return;
  if(!due || !hrs || ['Delivered','Cancelled','Inquiry','Ready'].includes(status)) {
    el.innerHTML = ''; return;
  }
  const st = S.settings;
  const wd = N(st.work_days) || 5;
  const wh = N(st.work_hours) || 8;
  const cb = N(st.cap_buffer) || 0;
  let d = new Date(); d.setHours(0,0,0,0);
  let target = new Date(due); target.setHours(0,0,0,0);
  if(target < d) { el.innerHTML=''; return; }
  let avail = 0;
  let curr = new Date(d);
  while(curr <= target) {
    let day = curr.getDay();
    if(day !== 0 && day <= Math.min(6, Math.max(1, wd))) avail += wh * (1 - cb/100);
    curr.setDate(curr.getDate()+1);
  }
  const existing = sum(S.orders.filter(o => !['Delivered','Cancelled','Inquiry','Ready'].includes(o.status) && o.due && new Date(o.due) <= target && o.id !== window.currEditId), o => N(o.hours));
  const capBefore = avail - existing;
  const capAfter = capBefore - hrs;
  const stat = capAfter >= 0 ? '<span class="good">✓ Fits current capacity</span>' : `<span class="bad">⚠️ This order exceeds available capacity by approximately ${Math.abs(capAfter).toFixed(1)} hours.</span>`;
  el.innerHTML = `<div class="card" style="margin-top:10px;background:var(--bg)">
    <small class="mut">NEW ORDER CAPACITY</small>
    <div class="row sp" style="margin:4px 0"><span>Available before due date:</span><b>${capBefore.toFixed(1)} hours</b></div>
    <div class="row sp" style="margin:4px 0"><span>After adding this order:</span><b>${capAfter.toFixed(1)} / ${avail.toFixed(1)} hours</b></div>
    <div style="margin-top:6px">${stat}</div>
  </div>`;
};

async function edit(coll,title,fields,v,after){
  window.currEditId = v.id;
  window.formOnInp = coll === 'orders' ? () => window.orderPreview() : null;
  form(title,fields,v,async r=>{
    const b = document.getElementById('toast'); toast('Saving...');
    try {
      if(!r.id) r.id=uid();
      await syncSave(coll, r);
      const idx=S[coll].findIndex(x=>x.id===r.id);
      if(idx>=0) S[coll][idx]=r; else S[coll].push(r);
      if(after) after(r);
      R();
      toast('Saved');
    } catch(e) { toast('Error saving'); console.error(e); }
  });
  if (coll === 'orders') window.orderPreview();
}

async function del(coll,id,b){
  if(b.dataset.s!=='1'){b.dataset.s='1';b.textContent='Sure?';return}
  if(coll==='clients'&&S.orders.some(o=>o.clientId===id))return toast('Delete this client\\'s orders first');
  toast('Deleting...');
  try {
    await syncDel(coll, id);
    S[coll]=S[coll].filter(x=>x.id!==id);
    if(coll==='orders'){S.payments=S.payments.filter(p=>p.orderId!==id);S.usage=S.usage.filter(u=>u.orderId!==id);V='orders'}
    if(coll==='materials')S.usage=S.usage.filter(u=>u.matId!==id);
    R();
    toast('Deleted');
  } catch(e) { toast('Error deleting'); console.error(e); }
}

const delb=(c,id)=>`<button class="btn sm" onclick="del('${c}','${id}',this)">Delete</button>`;
const TYPES=['RTW','Custom','Bridal','Other'],STAT=['Inquiry','Confirmed','In production','Cutting','Sewing','Fitting','Alterations','Ready','Delivered','Cancelled'],METH=['M-Pesa','Cash','Bank','Card','Other'];
const MCAT=['Main fabric','Lining','Interfacing','Zippers','Buttons','Thread','Trims','Lace','Packaging','Other'];
const ECAT=['Trims','Packaging','Laundry/dry cleaning','Delivery','Outsourced labour','Repairs','Rent','Electricity/tokens','Water','Internet','Cleaning','Equipment','Maintenance','Marketing','Photography','Software/subscriptions','Transport','Professional services','Bank/M-Pesa charges','Other'];
const DIRECT=['Trims','Packaging','Laundry/dry cleaning','Delivery','Outsourced labour','Repairs'];

const clientF=()=>[['name','Client name'],['phone','Phone'],['email','Email (optional)'],['notes','Notes','area']];
const orderF=()=>[['no','Order number'],['date','Date','date'],['clientId','Client','clientSelect',S.clients.map(c=>[c.id,c.name])],['type','Order type','select',TYPES],['name','Garment / product'],['qty','Quantity','number'],['price','Selling price (each)','number'],['hours','Estimated labour hours (whole order)','number'],['estMat','Estimated materials (whole order)','number'],['estOther','Estimated other costs','number'],['actHours','ACTUAL labour hours (blank = est. hours)','number'],['actLabOverride','ACTUAL labour cost override (blank = hours x rate)','number'],['actMat','ACTUAL extra materials (not in Materials tab)','number'],['actOther','ACTUAL other costs','number'],['design','Design description','area'],['measure','Measurements','area'],['fabric','Fabric'],['fabQty','Fabric quantity','number'],['notes','Notes / trims / client materials','area'],['head_prod','PRODUCTION DETAILS','header'],['due','Due date','date'],['priority','Priority','select',['Normal','Urgent']],['status','Production status','select',STAT],['prod_start','Production start date','date'],['prod_end','Completion date','date'],['delivered_date','Delivery date','date']];
const payF=()=>[['date','Date','date'],['amt','Amount','number'],['method','Method','select',METH],['ref','Reference / transaction no.']];
const newOrder=()=>({no:'TS-'+String(S.orders.length+1).padStart(3,'0'),date:today(),type:'Custom',qty:1,status:'Confirmed',clientId:S.clients[0]?.id||''});

/* views */
const bar=(l,v,mx,c)=>`<div class="row sp" style="margin:6px 0 0"><span>${l}</span><b>${K(v)}</b></div><div class="bar"><i style="width:${mx?Math.max(0,v)/mx*100:0}%;background:${c}"></i></div>`;
const card=(l,v,c='')=>`<div class="card"><small>${l}</small><strong class="${c}">${v}</strong></div>`;

const views={
dash(){const s=mstat(mon(today())),n=s.os.length,cu=s.os.filter(r=>r.o.type!=='RTW').length,mx=Math.max(s.sales,s.coll,s.out,1);
return`<h2>This month</h2><div class="grid">${card('Total sales',K(s.sales))}${card('Money collected',K(s.coll))}${card('Clients who still owe you',K(s.owed),'bad')}${card('Money spent',K(s.out))}${card('Cost of making the garments',K(s.cost))}${card('Profit',K(s.gp),cls(s.gp))}${card('Cash in minus cash out',K(s.coll-s.out),cls(s.coll-s.out))}${card('Profit margin',s.sales?P(s.gp/s.sales*100):'—',cls(s.gp))}</div>
<h3>At a glance</h3><div class="card">${bar('Sales',s.sales,mx,'var(--acc)')}${bar('Collected',s.coll,mx,'var(--good)')}${bar('Spent',s.out,mx,'var(--bad)')}</div>
<div class="grid" style="margin-top:10px">${card('Orders',n)}${card('Custom / bridal / other',cu)}${card('Ready-to-wear',n-cu)}${card('Average order',K(n?s.sales/n:0))}${card('Fabric & materials bought',K(s.matSp))}${card('Labour',K(s.lab))}${card('Overhead share',K(s.oh))}</div>
<div class="note"><b>Revenue is not profit.</b> Profit = what you charged − what the garment cost to make (materials + labour + overhead). Money collected only tells you what has arrived so far.</div>`},
prod(){
  const todayDate = new Date();
  todayDate.setHours(0,0,0,0);
  const isOverdue = d => d && new Date(d) < todayDate;
  const isDueSoon = d => {
    if(!d) return false;
    const diff = (new Date(d) - todayDate) / (1000 * 60 * 60 * 24);
    return diff >= 0 && diff <= 3;
  };

  const active = S.orders.filter(o => !['Delivered', 'Cancelled'].includes(o.status));
  const cOverdue = active.filter(o => isOverdue(o.due)).length;
  const cSoon = active.filter(o => isDueSoon(o.due)).length;
  const cUrgent = active.filter(o => o.priority === 'Urgent').length;
  const cReady = active.filter(o => o.status === 'Ready').length;
  const cProd = active.filter(o => !['Inquiry', 'Confirmed', 'Ready'].includes(o.status)).length;
  
  const st = S.settings;
  const wd = N(st.work_days) || 5;
  const wh = N(st.work_hours) || 8;
  const cb = N(st.cap_buffer) || 0;
  
  const avail = wd * wh;
  const capAfterBuffer = avail * (1 - cb / 100);
  
  const committedOrders = active.filter(o => !['Inquiry', 'Ready'].includes(o.status));
  const commHours = sum(committedOrders, o => N(o.hours));
  const noEstOrders = committedOrders.filter(o => !(N(o.hours) > 0));
  
  const rem = capAfterBuffer - commHours;
  const util = capAfterBuffer ? (commHours / capAfterBuffer) * 100 : 0;
  
  let capState = 'Normal workload';
  if (util >= 70 && util < 90) capState = 'High workload';
  else if (util >= 90 && util <= 100) capState = 'Near capacity';
  else if (util > 100) capState = 'Over capacity';

  const daysRem = (d) => {
    if (!d) return '—';
    const diff = Math.ceil((new Date(d) - todayDate) / (1000 * 60 * 60 * 24));
    return diff < 0 ? `${-diff}d ago` : `${diff}d`;
  };

  const sorted = active.slice().sort((a,b) => {
    const scoreA = isOverdue(a.due) ? 4 : (a.priority === 'Urgent' ? 3 : (isDueSoon(a.due) ? 2 : 1));
    const scoreB = isOverdue(b.due) ? 4 : (b.priority === 'Urgent' ? 3 : (isDueSoon(b.due) ? 2 : 1));
    if (scoreA !== scoreB) return scoreB - scoreA;
    if (a.due && b.due) return new Date(a.due) - new Date(b.due);
    if (a.due) return -1;
    if (b.due) return 1;
    return 0;
  });

  const getDayCap = (d) => {
    const day = d.getDay();
    return (day !== 0 && day <= Math.min(6, Math.max(1, wd))) ? wh * (1 - cb / 100) : 0;
  };

  let simDate = new Date(todayDate);
  let calendar = {};
  let conflicts = [];
  const schedOrders = committedOrders.filter(o => N(o.hours) > 0).sort((a, b) => {
    if (a.due && b.due) return new Date(a.due) - new Date(b.due);
    if (a.due) return -1;
    if (b.due) return 1;
    return 0;
  });

  for (const o of schedOrders) {
    let hrs = N(o.hours);
    let orderDue = o.due ? new Date(o.due) : null;
    if (orderDue) orderDue.setHours(0,0,0,0);
    while (hrs > 0) {
      let ds = simDate.toISOString().slice(0,10);
      if (calendar[ds] === undefined) calendar[ds] = getDayCap(simDate);
      if (calendar[ds] > 0) {
        let take = Math.min(hrs, calendar[ds]);
        calendar[ds] -= take;
        hrs -= take;
      }
      if (hrs > 0) simDate.setDate(simDate.getDate() + 1);
    }
    if (orderDue && simDate > orderDue) conflicts.push(o);
  }

  let nextFree = new Date(simDate);
  while (true) {
    let ds = nextFree.toISOString().slice(0,10);
    if (calendar[ds] === undefined) calendar[ds] = getDayCap(nextFree);
    if (calendar[ds] > 0) break;
    nextFree.setDate(nextFree.getDate() + 1);
  }
  const nextFreeStr = nextFree.toLocaleDateString('en-GB', {day:'numeric', month:'short', year:'numeric'});

  return `<div class="row sp"><h2>Production Dashboard</h2></div>
  <h3>Overview</h3>
  <div class="grid">
    ${card('Overdue', cOverdue, cOverdue ? 'bad' : '')}
    ${card('Due ≤ 3 days', cSoon, cSoon ? 'bad' : '')}
    ${card('Urgent', cUrgent, cUrgent ? 'bad' : '')}
    ${card('In Production', cProd)}
    ${card('Ready', cReady, cReady ? 'good' : '')}
    ${card('Active Orders', active.length)}
  </div>
  
  <div class="grid" style="margin-top:16px">
    <div class="card">
      <small class="mut">CAPACITY (THIS WEEK)</small>
      <p style="margin:8px 0"><b>${commHours.toFixed(1)} / ${capAfterBuffer.toFixed(1)} hours</b> committed</p>
      <p style="margin:8px 0"><b>${util.toFixed(1)}%</b> utilised</p>
      <p style="margin:8px 0"><b>${rem.toFixed(1)} hours</b> available</p>
      <p style="margin:0" class="${util > 100 ? 'bad' : ''}">Status: <b>${capState}</b></p>
    </div>
    <div class="card">
      <small class="mut">WHEN CAN I TAKE ANOTHER ORDER?</small>
      ${noEstOrders.length > 0 ? 
        `<p class="mut">Add labour estimates to active orders to calculate the next available slot. (${noEstOrders.length} missing)</p>` :
        `<p style="margin:8px 0">Next available slot: <b>${commHours === 0 ? 'Available now' : nextFreeStr}</b></p>
         <p style="margin:8px 0">Current workload: <b>${commHours.toFixed(1)} hours</b></p>
         <p style="margin:8px 0">Usable capacity: <b>${capAfterBuffer.toFixed(1)} hours/week</b></p>
         <p style="margin:8px 0">Available: <b>${rem.toFixed(1)} hours</b></p>
         ${conflicts.length > 0 ? `<p class="bad" style="margin:0">⚠️ Current production workload may exceed available capacity (${conflicts.map(c=>esc(c.no)).join(', ')}).</p>` : ''}`
      }
    </div>
  </div>
  
  <h3 style="margin-top:16px">Active Orders</h3>
  <div class="card wrap">
    <table>
      <tr><th>Order</th><th>Client</th><th>Garment</th><th>Due Date</th><th>Priority</th><th>Status</th><th class="r">Est. Hours</th><th class="r">Act. Hours</th><th>Days Rem.</th></tr>
      ${sorted.map(o => {
        let tag = '';
        if (isOverdue(o.due)) tag = '<span class="pill" style="background:var(--bad);color:#fff">OVERDUE</span> ';
        else if (o.priority === 'Urgent') tag = '<span class="pill" style="background:#d9906f;color:#fff">URGENT</span> ';
        else if (isDueSoon(o.due)) tag = '<span class="pill" style="background:#d9906f;color:#fff">DUE SOON</span> ';
        else tag = '<span class="pill">ON TRACK</span> ';
        return `<tr>
          <td><a class="l" onclick="ID='${o.id}';V='order';R()">${esc(o.no)}</a><br>${tag}</td>
          <td>${esc(cn(o.clientId))}</td>
          <td>${esc(o.name)}</td>
          <td>${o.due || '<span class="mut">Not set</span>'}</td>
          <td>${o.priority || 'Normal'}</td>
          <td>${o.status}</td>
          <td class="r">${o.hours ? o.hours : '<span class="mut" title="Labour estimate missing">⚠️ Not set</span>'}</td>
          <td class="r">${o.actHours ? o.actHours : '—'}</td>
          <td>${daysRem(o.due)}</td>
        </tr>`;
      }).join('') || '<tr><td colspan="9" class="mut">No active production orders.</td></tr>'}
    </table>
  </div>`;
},
orders(){return`<div class="row sp"><h2>Orders</h2><button class="btn pri" onclick="edit('orders','New order',orderF(),newOrder())">+ Add order</button></div><div class="card wrap"><table><tr><th>No.</th><th>Client</th><th>Garment</th><th class="r">Price</th><th class="r">Paid</th><th class="r">Balance</th><th>Payment</th><th>Status</th></tr>${S.orders.slice().reverse().map(o=>{const r=ocalc(o);return`<tr><td><a class="l" onclick="ID='${o.id}';V='order';R()">${esc(o.no)}</a></td><td>${esc(cn(o.clientId))}</td><td>${esc(o.name)}</td><td class="r">${K(r.total)}</td><td class="r">${K(r.paid)}</td><td class="r ${r.bal>0?'bad':''}">${K(r.bal)}</td><td>${pstat(r)}</td><td><span class="pill">${o.status}</span></td></tr>`}).join('')}</table></div>`},
order(){const o=S.orders.find(x=>x.id===ID);if(!o)return'';const r=ocalc(o),d=r.act-r.est;
return`<a class="l" onclick="V='orders';R()">← Orders</a><div class="row sp"><h2>${esc(o.no)} · ${esc(o.name)}</h2><div class="row"><button class="btn" onclick="edit('orders','Edit order',orderF(),S.orders.find(x=>x.id==='${o.id}'))">Edit</button>${delb('orders',o.id)}</div></div><p class="mut">${esc(cn(o.clientId))} · ${o.type} · ${o.status} · due ${o.due||'—'} · Priority: ${o.priority||'Normal'}</p>
<div class="grid">${card('Selling price',K(r.total))}${card('Paid so far',K(r.paid))}${card('Balance',K(r.bal),r.bal>0?'bad':'good')}${card('Cost of making it'+(r.has?' (actual)':' (estimate)'),K(r.cost))}${card('Profit',K(r.profit),cls(r.profit))}${card('Profit margin',P(r.margin),cls(r.profit))}</div>
<div class="note">Estimated cost <b>${K(r.est)}</b> · Actual cost <b>${r.has?K(r.act):'not entered yet'}</b>${r.has?` · Difference <b class="${d>0?'bad':'good'}">${d>0?'+':''}${K(d)}</b>`:''}<br>Cost = materials ${K(r.mat)} + labour ${K(r.lab)} + overhead ${K(r.oh)} + other ${K(r.oth)}</div>
<h3>Turnaround</h3>
<div class="card">${(() => {
  const diffDays = (d1, d2) => Math.ceil((new Date(d2) - new Date(d1)) / (1000 * 60 * 60 * 24));
  if (['Delivered', 'Cancelled'].includes(o.status)) {
    const endD = o.delivered_date || o.prod_end;
    const tCal = (o.date && endD) ? diffDays(o.date, endD) : 'Not recorded';
    const tProd = (o.prod_start && o.prod_end) ? diffDays(o.prod_start, o.prod_end) : 'Not recorded';
    const tLab = (N(o.actHours) && N(o.hours)) ? (N(o.actHours) - N(o.hours)) : 'Not recorded';
    return `<p style="margin:0">Calendar turnaround: <b>${tCal !== 'Not recorded' ? tCal + ' days' : 'Not recorded'}</b><br>
    Production duration: <b>${tProd !== 'Not recorded' ? tProd + ' days' : 'Not recorded'}</b><br>
    Labour variance: <b class="${tLab > 0 ? 'bad' : 'good'}">${tLab !== 'Not recorded' ? (tLab > 0 ? '+' : '') + tLab + ' hours' : 'Not recorded'}</b></p>`;
  } else {
    const tSince = o.date ? diffDays(o.date, today()) : 'Not recorded';
    const tProd = (o.prod_start && o.prod_end) ? diffDays(o.prod_start, o.prod_end) : 'Not recorded';
    const tDue = o.due ? diffDays(today(), o.due) : 'Not recorded';
    return `<p style="margin:0">Days since order: <b>${tSince}</b><br>
    Days in production: <b>${tProd}</b><br>
    Days until due: <b>${tDue}</b></p>`;
  }
})()}</div>
<div class="row sp"><h3>Payments</h3><button class="btn pri" onclick="edit('payments','Record payment',payF(),{orderId:'${o.id}',date:today(),method:'M-Pesa'})">+ Payment</button></div><div class="card wrap"><table>${S.payments.filter(p=>p.orderId===o.id).map(p=>`<tr><td>${p.date}</td><td class="r">${K(N(p.amt))}</td><td>${p.method}</td><td>${esc(p.ref)}</td><td><button class="btn sm" onclick="edit('payments','Edit payment',payF(),S.payments.find(x=>x.id==='${p.id}'))">Edit</button> ${delb('payments',p.id)}</td></tr>`).join('')||'<tr><td class="mut">No payments yet</td></tr>'}</table></div>
<div class="row sp"><h3>Materials used</h3><button class="btn pri" onclick="useMat('${o.id}')">+ Assign material</button></div><div class="card wrap"><table>${S.usage.filter(u=>u.orderId===o.id).map(u=>{const m=S.materials.find(x=>x.id===u.matId)||{};return`<tr><td>${esc(m.name)}</td><td>${u.qty} ${esc(m.unit)} × ${K(N(m.cpu))}</td><td class="r">${K(N(u.qty)*N(m.cpu))}</td><td>${delb('usage',u.id)}</td></tr>`}).join('')||'<tr><td class="mut">None assigned</td></tr>'}</table></div>
${o.design||o.measure||o.notes?`<h3>Details</h3><div class="card">${[o.design,o.measure&&'Measurements: '+o.measure,o.fabric&&'Fabric: '+o.fabric+' ('+(o.fabQty||'?')+')',o.notes].filter(Boolean).map(x=>`<p>${esc(x)}</p>`).join('')}</div>`:''}`},
clients(){return`<div class="row sp"><h2>Clients</h2><button class="btn pri" onclick="edit('clients','New client',clientF(),{})">+ Add client</button></div><div class="card wrap"><table><tr><th>Name</th><th>Phone</th><th class="r">Invoiced</th><th class="r">Paid</th><th class="r">Still owes</th></tr>${S.clients.map(c=>{const rs=S.orders.filter(o=>o.clientId===c.id&&o.status!=='Cancelled').map(ocalc);return`<tr><td><a class="l" onclick="ID='${c.id}';V='client';R()">${esc(c.name)}</a></td><td>${esc(c.phone)}</td><td class="r">${K(sum(rs,r=>r.total))}</td><td class="r">${K(sum(rs,r=>r.paid))}</td><td class="r bad">${K(sum(rs,r=>r.bal))}</td></tr>`}).join('')}</table></div>`},
client(){const c=cl(ID);if(!c)return'';const os=S.orders.filter(o=>o.clientId===c.id);return`<a class="l" onclick="V='clients';R()">← Clients</a><div class="row sp"><h2>${esc(c.name)}</h2><div class="row"><button class="btn" onclick="edit('clients','Edit client',clientF(),cl('${c.id}'))">Edit</button>${delb('clients',c.id)}</div></div><p class="mut">${esc(c.phone)} ${esc(c.email)}<br>${esc(c.notes)}</p><div class="row"><button class="btn pri" onclick="edit('orders','New order',orderF(),{...newOrder(),clientId:'${c.id}'})">+ Order for ${esc(c.name)}</button></div>
<h3>Orders & payments</h3>${os.map(o=>{const r=ocalc(o);return`<div class="card" style="margin-bottom:8px"><a class="l" onclick="ID='${o.id}';V='order';R()">${esc(o.no)} · ${esc(o.name)}</a> <span class="pill">${o.status}</span><br>Price ${K(r.total)} · Paid ${K(r.paid)} · <span class="${r.bal>0?'bad':''}">Owes ${K(r.bal)}</span><br><small class="mut">${S.payments.filter(p=>p.orderId===o.id).map(p=>p.date+' '+K(N(p.amt))+' '+p.method).join(' · ')||'No payments'}</small></div>`}).join('')||'<p class="mut">No orders yet</p>'}`},
mat(){const mf=()=>[['date','Date','date'],['supplier','Supplier'],['name','Material / fabric'],['cat','Category','select',MCAT],['qty','Quantity bought','number'],['unit','Unit (yards, pcs…)'],['cpu','Cost per unit','number'],['notes','Notes']];window.mf=mf;
return`<div class="row sp"><h2>Fabric & materials</h2><button class="btn pri" onclick="edit('materials','Record purchase',mf(),{date:today(),unit:'yards',cat:'Main fabric'})">+ Purchase</button></div><div class="note">Record fabric and trim purchases here (not in Expenses) so they are not counted twice. Assign them to a garment to see the cost used.</div><div class="card wrap"><table><tr><th>Date</th><th>Material</th><th>Supplier</th><th class="r">Bought</th><th class="r">Total cost</th><th class="r">Used</th><th class="r">Left</th><th></th></tr>${S.materials.slice().reverse().map(m=>{const u=sum(S.usage.filter(x=>x.matId===m.id),x=>N(x.qty));return`<tr><td>${m.date}</td><td>${esc(m.name)}<br><small class="mut">${m.cat}</small></td><td>${esc(m.supplier)}</td><td class="r">${m.qty} ${esc(m.unit)} @ ${K(N(m.cpu))}</td><td class="r">${K(N(m.qty)*N(m.cpu))}</td><td class="r">${u}</td><td class="r">${N(m.qty)-u}</td><td><button class="btn sm" onclick="useMat(null,'${m.id}')">Use</button> <button class="btn sm" onclick="edit('materials','Edit',mf(),S.materials.find(x=>x.id==='${m.id}'))">Edit</button> ${delb('materials',m.id)}</td></tr>`}).join('')}</table></div>`},
exp(){const ef=()=>[['date','Date','date'],['desc','What was it for'],['cat','Category','select',ECAT],['amt','Amount','number'],['method','Paid by','select',METH],['payee','Supplier / payee'],['orderId','Related order (optional)','select',[['','— none —'],...S.orders.map(o=>[o.id,o.no+' · '+o.name])]],['notes','Notes']];window.ef=ef;
const dir=S.expenses.filter(e=>DIRECT.includes(e.cat)||e.orderId);return`<div class="row sp"><h2>Expenses</h2><button class="btn pri" onclick="edit('expenses','Record expense',ef(),{date:today(),method:'M-Pesa',cat:'Other'})">+ Expense</button></div><div class="grid">${card('Spent on making garments',K(sum(dir,e=>N(e.amt))))}${card('Studio & business running costs',K(sum(S.expenses,e=>N(e.amt))-sum(dir,e=>N(e.amt))))}</div><div class="card wrap" style="margin-top:10px"><table>${S.expenses.slice().reverse().map(e=>`<tr><td>${e.date}</td><td>${esc(e.desc)}<br><small class="mut">${e.cat}${e.payee?' · '+esc(e.payee):''}</small></td><td>${DIRECT.includes(e.cat)||e.orderId?'<span class="pill">garment</span>':'<span class="pill">studio/business</span>'}</td><td class="r">${K(N(e.amt))}</td><td><button class="btn sm" onclick="edit('expenses','Edit',ef(),S.expenses.find(x=>x.id==='${e.id}'))">Edit</button> ${delb('expenses',e.id)}</td></tr>`).join('')}</table></div>`},
calc(){const g=(k,l,t='number')=>`<label>${l}<input id="c_${k}" type="${t}" step="any" inputmode="${t==='number'?'decimal':'text'}" value="${esc(C[k])}"></label>`;
return`<h2>Price it</h2><div oninput="cin()" onchange="cin()"><div class="two">${g('name','Garment','text')}<label>Type<select id="c_type">${['Custom','RTW','Bridal'].map(t=>`<option${C.type===t?' selected':''}>${t}</option>`).join('')}</select></label>${g('qty','Quantity')}${g('hours','Labour hours (add hours for complexity)')}${g('fabQty','Fabric quantity')}${g('fabUnit','Fabric cost per unit')}${g('trims','Trimmings')}${g('lining','Lining')}${g('interf','Interfacing')}${g('other','Other materials / finishing / delivery')}${g('pack','Packaging')}${g('lab','Labour rate / hour')}${g('oh','Overhead rate / hour')}
<label>Target profit<select id="c_pct">${[10,15,20,25,30,35,40,50].map(p=>`<option value="${p}"${N(C.pct)===p?' selected':''}>${p}%</option>`).join('')}</select></label><label>Calculated as<select id="c_mode"><option value="margin"${C.mode==='margin'?' selected':''}>Profit margin (recommended)</option><option value="markup"${C.mode==='markup'?' selected':''}>Markup on cost</option></select></label></div></div><div id="out"></div>`},
cat(){const pf=()=>[['name','Product name'],['fabQty','Fabric quantity','number'],['fabCost','Fabric cost per unit','number'],['hours','Labour hours','number'],['trims','Trims & other materials','number'],['pack','Packaging','number']];window.pf=pf;const st=S.settings;
return`<div class="row sp"><h2>RTW catalogue</h2><button class="btn pri" onclick="edit('products','New product',pf(),{})">+ Product</button></div><p class="mut">Wholesale ${st.wm}% / retail ${st.rm}% (${st.mode}). Change in Settings.</p><div class="card wrap"><table><tr><th>Product</th><th class="r">Cost to make</th><th class="r">Wholesale</th><th class="r">Retail</th><th></th></tr>${S.products.map(p=>{const c=N(p.fabQty)*N(p.fabCost)+N(p.trims)+N(p.pack)+N(p.hours)*(st.labour+st.oh);return`<tr><td>${esc(p.name)}</td><td class="r">${K(c)}</td><td class="r">${K(rp(price(c,st.wm,st.mode)))}</td><td class="r">${K(rp(price(c,st.rm,st.mode)))}</td><td><button class="btn sm" onclick="edit('products','Edit',pf(),S.products.find(x=>x.id==='${p.id}'))">Edit</button> ${delb('products',p.id)}</td></tr>`}).join('')}</table></div>`},
rep(){const s=mstat(M),f=flow(M),by={},ty={};s.os.forEach(r=>{(by[r.o.name]??={s:0,c:0}).s+=r.total;by[r.o.name].c+=r.cost;(ty[r.o.type]??={s:0,c:0}).s+=r.total;ty[r.o.type].c+=r.cost});
const tb=(h,m)=>`<div class="card wrap"><table><tr><th>${h}</th><th class="r">Sales</th><th class="r">Cost</th><th class="r">Profit</th></tr>${Object.entries(m).sort((a,b)=>b[1].s-a[1].s).map(([k,v])=>`<tr><td>${esc(k)}</td><td class="r">${K(v.s)}</td><td class="r">${K(v.c)}</td><td class="r ${cls(v.s-v.c)}">${K(v.s-v.c)}</td></tr>`).join('')||'<tr><td class="mut">No orders this month</td></tr>'}</table></div>`;
return`<div class="row sp"><h2>Reports</h2><input type="month" value="${M}" style="width:auto" onchange="M=this.value;R()"></div>
<h3>Sales</h3><div class="grid">${card('Total sales',K(s.sales))}${card('Collected',K(s.coll))}${card('Still owed (all time)',K(s.owed),'bad')}</div>
<h3>Where the money went</h3><div class="grid">${card('Fabric & materials bought',K(s.matSp))}${card('Labour (on orders)',K(s.lab))}${card('Overhead share (on orders)',K(s.oh))}${card('Expenses recorded',K(s.expT))}</div>
<h3>Profit</h3><div class="grid">${card('Revenue',K(s.sales))}${card('Cost of making',K(s.cost))}${card('Profit (after labour & overhead share)',K(s.gp),cls(s.gp))}${card('Margin',s.sales?P(s.gp/s.sales*100):'—')}</div><p class="mut">Cost of making already includes your overhead share, so studio expenses above are not subtracted again. Compare them with the overhead share to check your KES ${S.settings.oh}/hr is realistic.</p>
<h3>By garment</h3>${tb('Garment',by)}<h3>Custom vs RTW</h3>${tb('Type',ty)}
<h3>Cash</h3><div class="card">Opening ${K(f)}<br>+ Received ${K(s.coll)}<br>− Spent ${K(s.out)}<br><b>Closing ${K(f+s.coll-s.out)}</b></div>`},
set(){const st=S.settings,g=(k,l,t='number')=>`<label>${l}<input id="s_${k}" type="${t}" step="any" value="${esc(st[k])}"></label>`;
return`<h2>Settings</h2><div class="two">${g('name','Business name','text')}${g('cur','Currency','text')}${g('labour','Labour rate / hour')}${g('oh','Overhead rate / hour')}${g('margin','Default profit margin %')}${g('markup','Default markup %')}${g('wm','Wholesale margin/markup %')}${g('rm','Retail margin/markup %')}${g('opening_cash_balance','Opening cash balance')}<label>Wholesale/retail use<select id="s_mode"><option value="margin"${st.mode==='margin'?' selected':''}>Margin</option><option value="markup"${st.mode==='markup'?' selected':''}>Markup</option></select></label></div><p>Hourly production cost: <b>${K(st.labour+st.oh)}</b></p>
<h3>Production Capacity</h3><div class="two">${g('work_days','Working days per week')}${g('work_hours','Working hours per day')}${g('cap_buffer','Capacity buffer %')}</div>
<div class="row"><button class="btn pri" onclick="saveSet()">Save settings</button><button class="btn" onclick="doLogout()">Log out</button></div>
<h3>Export (CSV)</h3><div class="row">${['orders','payments','expenses','materials','clients','products'].map(x=>`<button class="btn" onclick="exp_('${x}')">${x}</button>`).join('')}</div>
<h3>Migrate Local Data</h3><div class="note">Push your old browser data to Supabase. This will not overwrite existing cloud data, but will create new rows.</div><button class="btn" onclick="migrateLocal()">Migrate local data to cloud</button>`}};

function useMat(oid,mid){const f=[['matId','Material','select',S.materials.map(m=>[m.id,m.name+' ('+(N(m.qty)-sum(S.usage.filter(u=>u.matId===m.id),u=>N(u.qty)))+' '+m.unit+' left)'])],['orderId','Used for order','select',S.orders.map(o=>[o.id,o.no+' · '+o.name])],['qty','Quantity used','number']];edit('usage','Assign material to garment',f,{orderId:oid||S.orders[0]?.id,matId:mid||S.materials[0]?.id})}
async function saveSet(){const st=S.settings;['name','cur','mode'].forEach(k=>st[k]=document.getElementById('s_'+k).value);['labour','oh','margin','markup','wm','rm','opening_cash_balance','work_days','work_hours','cap_buffer'].forEach(k=>st[k]=N(document.getElementById('s_'+k).value));
  toast('Saving settings...');
  await window.supabase.from('pricing_settings').upsert([{user_id: user.id, ...st}]);
  toast('Saved'); R();
}

let isMigrating = false;
async function migrateLocal() {
  if (isMigrating) return;
  if (localStorage.getItem('twostones.migrated')) return toast('Data already migrated from this device.');
  
  toast('Migrating...');
  isMigrating = true;
  try {
    const s=localStorage.getItem('twostones.v1');
    if(!s) { isMigrating=false; return toast('No local data found'); }
    const old = JSON.parse(s);
    if(old.settings) { S.settings = old.settings; await supabase.from('pricing_settings').upsert([{user_id: user.id, ...S.settings}]); }
    for(const c of old.clients||[]) await syncSave('clients', c);
    for(const p of old.products||[]) await syncSave('products', p);
    for(const o of old.orders||[]) await syncSave('orders', o);
    for(const p of old.payments||[]) await syncSave('payments', p);
    for(const m of old.materials||[]) await syncSave('materials', m);
    for(const u of old.usage||[]) await syncSave('usage', u);
    for(const e of old.expenses||[]) await syncSave('expenses', e);
    
    localStorage.setItem('twostones.migrated', '1');
    toast('Migration complete!');
    await loadCloudData(); R();
  } catch(e) { toast('Migration failed'); console.error(e); }
  isMigrating = false;
}

async function exp_(k){let rows=S[k];if(k==='orders')rows=S.orders.map(o=>{const r=ocalc(o);return{no:o.no,date:o.date,client:cn(o.clientId),type:o.type,garment:o.name,price:r.total,paid:r.paid,balance:r.bal,cost:r.cost,profit:r.profit,status:o.status}});if(!rows.length)return toast('Nothing to export');
const ks=Object.keys(rows[0]),t=[ks.join(','),...rows.map(r=>ks.map(c=>'"'+String(r[c]??'').replace(/"/g,'""')+'"').join(','))].join('\\n');try{const b=new Blob(['\\ufeff'+t],{type:'text/csv;charset=utf-8'}),a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='twostones-'+k+'.csv';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}catch(e){toast('Export failed')}}

/* calculator */
let C={name:'Custom dress',type:'Custom',qty:1,fabQty:4,fabUnit:1500,trims:500,lining:0,interf:0,other:0,pack:0,hours:5,lab:500,oh:215,pct:30,mode:'margin',try:''};
function cin(){const el=document.getElementById('out');if(!el)return;['name','type','qty','fabQty','fabUnit','trims','lining','interf','other','pack','hours','lab','oh','pct','mode'].forEach(k=>{const e=document.getElementById('c_'+k);if(e)C[k]=e.value});
const t=document.getElementById('c_try');if(t)C.try=t.value;
const q=N(C.qty)||1,mat=N(C.fabQty)*N(C.fabUnit)+N(C.trims)+N(C.lining)+N(C.interf)+N(C.other)+N(C.pack),lab=N(C.hours)*N(C.lab),oh=N(C.hours)*N(C.oh),cost=mat+lab+oh,p=N(C.pct),m=C.mode;
const ex=price(cost,p,m),sp=rp(ex),prof=sp-cost,mg=sp?prof/sp*100:0,mk=cost?prof/cost*100:0,pm=rp(price(cost,p,'margin')),pk=rp(price(cost,p,'markup')),tp=N(C.try);
const w=(v)=>sp?Math.max(0,v)/sp*100:0,lbl=m==='margin'?'margin':'markup';
el.innerHTML=`<h3>Price breakdown</h3><div class="card"><div class="row sp"><span>Selling price (each)</span><b style="font-size:22px">${K(sp)}</b></div><div class="bar"><i style="width:${w(mat)}%;background:#c9a27a"></i><i style="width:${w(lab)}%;background:#8c4a32"></i><i style="width:${w(oh)}%;background:#b9a99b"></i><i style="width:${w(prof)}%;background:var(--good)"></i></div>
<div class="row sp"><span>Fabric / materials</span><span>${K(mat)}</span></div><div class="row sp"><span>Labour (${C.hours||0} h)</span><span>${K(lab)}</span></div><div class="row sp"><span>Overhead</span><span>${K(oh)}</span></div><div class="row sp"><b>Total cost to make</b><b>${K(cost)}</b></div><div class="row sp"><b class="${cls(prof)}">Profit</b><b class="${cls(prof)}">${K(prof)}</b></div><div class="row sp"><span>Profit margin (share of the price)</span><b>${P(mg)}</b></div><div class="row sp"><span>Markup (profit ÷ cost)</span><span>${P(mk)}</span></div>${q>1?`<div class="row sp"><span>For ${q} pieces</span><b>${K(sp*q)} (profit ${K(prof*q)})</b></div>`:''}<small class="mut">Exact price ${ex.toFixed(2)}, shown rounded to the nearest 50.</small></div>
<div class="note"><b>Margin vs markup at ${p}%:</b> a ${p}% <b>margin</b> means ${p}% of the price is profit → ${K(pm)}. A ${p}% <b>markup</b> just adds ${p}% to the cost → ${K(pk)}, which is only a ${P((pk-cost)/pk*100)} margin. Margin shows your real profitability.</div>
<h3>All price options (${lbl})</h3><div class="card wrap"><table><tr><th>${lbl}</th><th class="r">Price</th><th class="r">Profit</th><th class="r">Margin</th></tr><tr><td>Cost</td><td class="r">${K(cost)}</td><td class="r">—</td><td></td></tr>${[10,15,20,25,30,35,40,50].map(x=>{const v=rp(price(cost,x,m));return`<tr class="${x===p?'hl':''}"><td>${x}%</td><td class="r">${K(v)}</td><td class="r">${K(v-cost)}</td><td class="r">${P(v?(v-cost)/v*100:0)}</td></tr>`}).join('')}</table></div>
<h3>What if…?</h3><div class="card"><label>If I charge / the customer will only pay<input id="c_try" type="number" inputmode="decimal" value="${esc(C.try)}" placeholder="e.g. ${rp(sp*0.9)}"></label>${tp>0?`<p>Profit: <b class="${cls(tp-cost)}">${K(tp-cost)}</b> · Profit margin: <b>${P((tp-cost)/tp*100)}</b></p><p>${tp<cost?`<b class="bad">Below cost: you lose ${K(cost-tp)}</b> (labour and overhead are included in cost).`:tp-cost<lab*0.3?'<b>Barely above cost</b>: you cover everything but make almost nothing.':'<b class="good">Still making money</b> after materials, labour and overhead.'}</p><p>Compared with ${K(sp)}: margin sacrificed <b>${P(mg-(tp-cost)/tp*100)}</b> points · profit given up <b>${K(sp-tp)}</b></p>`:'<p class="mut">Type a price to see your real profit and how much margin you give up. Change hours or fabric above to see the effect immediately.</p>'}</div>
<div class="row"><button class="btn" onclick="toCat()">Save to RTW catalogue</button></div>`}
function toCat(){S.products.push({id:uid(),name:C.name,fabQty:N(C.fabQty),fabCost:N(C.fabUnit),hours:N(C.hours),trims:N(C.trims)+N(C.lining)+N(C.interf)+N(C.other),pack:N(C.pack)});edit('products',null,[],S.products[S.products.length-1],()=>toast('Saved to catalogue'))}

const NAV=[['dash','Home'],['orders','Orders'],['prod','Production'],['clients','Clients'],['calc','Price it'],['mat','Materials'],['exp','Expenses'],['cat','Catalogue'],['rep','Reports'],['set','Settings']];
function R(){
  if(!user) return;
  const on=V==='order'?'orders':V==='client'?'clients':V;document.getElementById('app').innerHTML=`<nav><b>${esc(S.settings.name)}</b>${NAV.map(([k,l])=>`<a class="${k===on?'on':''}" onclick="V='${k}';R();scrollTo(0,0)">${l}</a>`).join('')}</nav><main>${views[V]()}</main>`;
  if(V==='calc'){C.lab=S.settings.labour;C.oh=S.settings.oh;C.pct=S.settings.margin;C.mode=S.settings.mode;cin();}
}
"""

with open('js/app.js', 'w', encoding='utf-8') as f:
    f.write(code)