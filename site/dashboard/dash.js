const fmt = n => (n||0).toLocaleString();
const COL={live:'#22c55e',sandbox:'#f59e0b',pending:'#3b82f6',off:'#9ca3af'};
const ORD={live:0,sandbox:1,pending:2,off:3};
const EMO={Blog:'📝',Facebook:'👥',Instagram:'📸',YouTube:'🔔',Blogger:'✍️',Tumblr:'🌀',Telegraph:'📄',
  Bluesky:'🦋',Mastodon:'🐘',Threads:'🧵',Telegram:'✈️','GitHub Pages':'🐙',Pinterest:'📌',Email:'📧',
  LinkedIn:'💼',TikTok:'🎵','Google Business':'📍'};
// fallback grouping when data.json predates the `group` field
const CONTENT_CH=new Set(['Blog','Podcast','Blogger','Tumblr','Telegraph','GitHub Pages','Email']);
const isContent=c=>c.group?c.group==='content':CONTENT_CH.has(c.name);
function $(id){return document.getElementById(id);}
function sortCh(ch){return [...ch].sort((a,b)=>(ORD[a.status]??9)-(ORD[b.status]??9));}

function renderScoreboard(d){
  const el=$('scoreboard'); if(!el||!d.channels) return;
  const chs=sortCh(d.channels);
  const val=v=>(v==null?'—':fmt(v));
  const shell=(c,body,extra='')=>`<div class="ccard ${extra}" style="--st:${COL[c.status]||'#9ca3af'}">
      <div class="cc-top"><span class="cc-emo">${EMO[c.name]||'•'}</span><span class="cc-grade gcolor-${c.grade||'F'}">${c.grade||'—'}</span></div>
      ${body}</div>`;
  const contentCard=c=>{
    const sub=c.status==='pending'?'Pending':(c.unit+' · '+c.status);
    return shell(c,`<div class="cc-val">${fmt(c.count)}</div><div class="cc-lab">${c.name}</div><div class="cc-sub">${sub}</div>`);
  };
  const socialCard=c=>{
    const sub=c.status==='pending'?'Pending':c.status;
    // only render metrics the platform actually reports — null means "not a thing here"
    // (e.g. Bluesky/Mastodon have no views; Telegram channels have no likes), so we skip
    // the tile instead of showing a bare "—".
    const m=[['Posts',c.count],['Views',c.views],['Likes',c.likes],['Followers',c.followers]].filter(([k,v])=>v!=null);
    const grid=m.map(([k,v])=>`<div class="sm"><span class="smv">${fmt(v)}</span><span class="smk">${k}</span></div>`).join('');
    return shell(c,`<div class="cc-lab">${c.name}</div><div class="cc-sub">${sub}</div><div class="smetrics">${grid}</div>`,'scard');
  };
  el.innerHTML=
    `<div class="sb-group">📚 Content — what we've published</div>`+
    chs.filter(isContent).map(contentCard).join('')+
    `<div class="sb-group">📣 Social — audience &amp; engagement</div>`+
    chs.filter(c=>!isContent(c)).map(socialCard).join('');
}

function renderFunnel(d){
  const el=$('funnel'); if(!el||!d.funnel) return;
  const f=d.funnel,t=d.trends||{};
  const stages=[
    {label:'👀 Reach',val:f.reach,tr:t.reach},
    {label:'🔥 Engagement',val:f.engagement,tr:t.engagement},
    {label:'👥 Audience (followers + email)',val:f.audience,tr:t.audience},
    {label:'🎯 Consent Resolve clicks',val:f.cr_clicks,tr:null}];
  const max=Math.max(1,...stages.map(s=>s.val));
  el.innerHTML=stages.map(s=>{
    const w=Math.max(5,Math.round(100*s.val/max));
    const tr=(s.tr!=null&&s.tr!==0)?`<span class="ftr ${s.tr>0?'up':'down'}">${s.tr>0?'▲':'▼'}${fmt(Math.abs(s.tr))}/wk</span>`:'';
    return `<div class="fstage"><div class="fhead"><span>${s.label}</span><span class="fval">${fmt(s.val)}${tr}</span></div><div class="fbar"><div class="ffill" style="width:${w}%"></div></div></div>`;
  }).join('');
  const tj=$('trajectory'); if(tj){const up=(t.audience||0)>0||(t.engagement||0)>0;tj.textContent=up?'📈 building':'— warming up';tj.className='traj '+(up?'up':'flat');}
}

function renderGoals(d){
  if(!$('goals')||!d.goals) return;
  $('goalLabel').textContent=d.goals.label;
  $('countdown').textContent=d.goals.days_left+' days left';
  $('goals').innerHTML=d.goals.items.map(g=>{
    const cls=g.on_track?'ok':'behind';
    return `<div class="goal"><div class="gtop"><span class="gname">${g.icon} ${g.label}</span>
      <span class="gnum"><b>${fmt(g.current)}</b> / ${fmt(g.target)}</span></div>
      <div class="track"><div class="fill ${cls}" data-w="${g.pct}"></div></div>
      <div class="gfoot"><span class="gtag ${cls}">${g.on_track?'● On track':'● Behind pace'}</span><span class="gpct">${g.pct}%</span></div></div>`;}).join('');
  setTimeout(()=>document.querySelectorAll('#goals .fill').forEach(f=>f.style.width=f.dataset.w+'%'),120);
  if($('goalRationale')) $('goalRationale').textContent=d.goals.rationale||'';
}

function renderStrategist(d){
  if(!$('coachHead')||!d.strategist||!d.strategist.headline) return;
  const s=d.strategist;
  $('coachHead').textContent=s.headline;
  $('coachUpd').textContent='Updated '+(s.updated||'')+(s.next_review?(' · next review '+s.next_review):'');
  $('coachRead').textContent=s.read||'';
  $('coachNext').textContent=s.next_move||'';
}

function renderAgents(d){
  if(!$('agents')||!d.agents) return;
  const order=['Publishing','Visual formats','Engagement','Funnel','Ops','Other'];
  const byCat={}; d.agents.forEach(a=>{(byCat[a.cat||'Other']=byCat[a.cat||'Other']||[]).push(a)});
  let html='';
  order.forEach(cat=>{ if(!byCat[cat])return;
    html+=`<div class="agcat">${cat} · ${byCat[cat].length}</div>`;
    html+=byCat[cat].map(ag=>`<div class="agent"><div><div class="n">${ag.name}</div><div class="s">${ag.schedule}</div></div><div class="badge"><span class="dot"></span>LIVE</div></div>`).join('');
  });
  $('agents').innerHTML=html;
}

function renderChannels(d){
  if(!$('channels')||!d.channels) return;
  const lab={live:'Live',sandbox:'Sandbox',pending:'Pending',off:'Not connected'};
  $('channels').innerHTML=sortCh(d.channels).map(c=>{
    let right;
    if(c.status==='off') right=lab.off;
    else if(c.status==='pending') right=`Pending — ${c.unit}`;
    else { const extra=c.stat?`${c.stat} · `:((c.followers!=null)?`${c.followers} followers · `:''); right=`${extra}${c.count} ${c.unit} · ${lab[c.status]}`; }
    return `<div class="chan"><div><div class="n"><span class="sdot" style="background:${COL[c.status]||'#9ca3af'}"></span>${EMO[c.name]||''} ${c.name}</div></div><div class="c">${right}</div></div>`;
  }).join('');
}

function renderQueue(d){
  if(!$('pr')||!d.content) return;
  const c=d.content;
  const pTot=(c.posts_published-1+c.posts_remaining)||1, rTot=(c.reels_published+c.reels_remaining)||1;
  $('pr').textContent=c.posts_remaining+' left'; $('rr').textContent=c.reels_remaining+' left';
  setTimeout(()=>{$('prf').style.width=(100*c.posts_remaining/pTot)+'%';$('rrf').style.width=(100*c.reels_remaining/rTot)+'%';},100);
}

function renderSignups(d){
  const el=$('signupGoal'); if(!el||!d.signups) return;
  const s=d.signups, pct=Math.min(100, s.pct||0);
  const top=(s.top_sources||[]).slice(0,5).map(x=>`<div class="adrow"><span class="k">${x.page}</span><span>${x.n}</span></div>`).join('')
    ||'<div class="adrow"><span class="k">No signups tracked yet — traffic + capture just went live</span><span>0</span></div>';
  el.innerHTML=`<div class="panel"><div class="eyebrow">📧 Newsletter goal — 1,000 ICP signups in 90 days</div>
    <div style="display:flex;align-items:baseline;gap:10px;margin:6px 0"><div style="font-family:'Bricolage Grotesque', Georgia, serif;font-size:42px;color:#a62d1a">${s.total||0}</div><div style="color:#8b9098">/ ${s.goal||1000} · ${pct}%</div></div>
    <div style="height:10px;background:#23262b;border-radius:6px;overflow:hidden;margin:8px 0 16px"><div style="height:100%;width:${pct}%;background:linear-gradient(90deg,#a62d1a,#c8321b)"></div></div>
    <div class="eyebrow" style="font-size:11px;margin-bottom:6px">Top converting pages</div>${top}</div>`;
}
function renderSearch(d){
  const el=$('searchSeo'); if(!el) return;
  const s=d.search||{};
  if(!s.configured){
    el.innerHTML=`<div class="panel"><div class="eyebrow">🔎 Organic search (SEO)</div>
      <div style="color:#8b9098;font-size:13px;margin-top:6px">Connect Google Search Console + Bing to see real organic clicks, impressions and top queries here. (Creds pending.)</div></div>`;
    return;
  }
  const eng=(name,g)=>{ if(!g||g.error) return `<div class="adrow"><span class="k">${name}</span><span>${g&&g.error?'⚠️ '+g.error:'—'}</span></div>`;
    return `<div class="adrow"><span class="k">${name}</span><span>${g.clicks||0} clicks · ${g.impressions||0} impr · ${g.ctr||0}% CTR${g.position?' · pos '+g.position:''}</span></div>`; };
  const allq=[...(((s.google||{}).top_queries)||[]),...(((s.bing||{}).top_queries)||[])]
    .sort((a,b)=>(b.clicks||0)-(a.clicks||0)).slice(0,8);
  const q=allq.length?allq.map(x=>`<div class="adrow"><span class="k">${x.query}</span><span>${x.clicks||0} clk · ${x.impressions||0} imp${x.position?' · #'+x.position:''}</span></div>`).join('')
    :'<div class="adrow"><span class="k">No query data yet (new domain — impressions land first)</span><span>—</span></div>';
  const cf=s.cloudflare||null;
  const cfRow=(cf&&!cf.error)?`<div class="adrow"><span class="k">Cloudflare pageviews</span><span>${cf.pageviews_daily||0}/day · ${cf.pageviews_weekly||0}/wk · ${cf.pageviews_monthly||0}/mo <span style="color:#8b9098">(zone-level, incl. bots)</span></span></div>`:'';
  // Buffer-routed channels (TikTok / LinkedIn / Pinterest) — engagement reality check
  const buf=d.buffer||null; let bufPanel='';
  if(buf&&!buf.error){
    const rows=Object.entries(buf).map(([svc,m])=>{
      const dead=(m.posts>10&&(m.reactions+m.comments)===0);
      return `<div class="adrow"><span class="k">${svc.charAt(0).toUpperCase()+svc.slice(1)}${dead?' <span style="color:#fca5a5">⚠ flatlined</span>':''}</span><span>${m.posts} posts · ${m.views} views · ${m.reactions+m.comments} eng${m.engagement_rate?' · '+m.engagement_rate+'%':''}</span></div>`;
    }).join('');
    bufPanel=`<div class="panel" style="margin-top:14px"><div class="eyebrow">📣 Buffer channels — last 30 days</div>${rows||'<div class="adrow"><span class="k">No channels</span><span>—</span></div>'}</div>`;
  }
  el.innerHTML=`<div class="panel"><div class="eyebrow">🔎 Organic search (SEO) — last 28 days</div>
    <div style="display:flex;align-items:baseline;gap:10px;margin:6px 0"><div style="font-family:'Bricolage Grotesque', Georgia, serif;font-size:42px;color:#a62d1a">${s.total_clicks||0}</div><div style="color:#8b9098">clicks · ${s.total_impressions||0} impressions</div></div>
    ${eng('Google',s.google)}${eng('Bing',s.bing)}${cfRow}
    <div class="eyebrow" style="font-size:11px;margin:12px 0 6px">Top queries</div>${q}</div>${bufPanel}`;
}
function renderAds(d){
  const a=(d&&d.ads)||null;
  // prominent header badge: ad on/off + total spend, visible on every load
  const badge=$('adBadge');
  if(badge&&a){
    const live=(a.status||'').toUpperCase()==='ACTIVE';
    const spent='$'+(parseFloat(a.spend)||0).toFixed(2);
    badge.style.display='inline-flex';
    badge.style.cssText+=';align-items:center;gap:8px;padding:6px 12px;border-radius:999px;font-weight:700;font-size:13px;'
      +(live?'background:rgba(46,204,113,.15);color:#2ecc71;border:1px solid #2ecc71'
             :'background:rgba(255,106,0,.12);color:#a62d1a;border:1px solid #a62d1a');
    badge.innerHTML=(live?'🟢 Ads ACTIVE':'⏸️ Ads PAUSED')
      +` · 💰 <b>${spent}</b> spent`+(live&&a.daily_budget?` · $${a.daily_budget.toFixed(0)}/day`:'');
  }
  if(!$('ads')||!a) return;
  const a2=a, live=(a2.status||'').toUpperCase()==='ACTIVE';
  $('ads').innerHTML=`<div class="adrow"><span class="k">Status</span><span class="pill ${live?'':'paused'}">${a2.status||'—'}</span></div>
    <div class="adrow"><span class="k">Daily budget</span><span>${a.daily_budget?('$'+a.daily_budget.toFixed(0)+'/day'):'—'}</span></div>
    <div class="adrow"><span class="k">Spent (total)</span><span>$${(parseFloat(a.spend)||0).toFixed(2)}</span></div>
    <div class="adrow"><span class="k">Impressions</span><span>${fmt(a.impressions)}</span></div>
    <div class="adrow"><span class="k">Video views</span><span>${fmt(a.video_views)}</span></div>`;
}

function renderAgenda(d){
  if(!$('agenda')||!d.upcoming) return;
  const mo=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
  $('agenda').innerHTML=d.upcoming.length?d.upcoming.map(u=>{const dt=new Date(u.date+'T12:00');
    return `<div class="ag"><div class="date"><div class="d">${dt.getDate()}</div><div class="m">${mo[dt.getMonth()]}</div></div>
      <span class="em">${u.icon}</span><div><div class="t">${u.title}</div><div class="s">${u.sub}</div></div>
      <span class="tag ${u.type}">${u.type==='reel'?'REEL':'POST'}</span></div>`;}).join('')
    :'<p style="color:var(--muted);font-size:13px">Queue empty — refill coming.</p>';
}

function renderActivity(cl){
  if(!$('feed')) return;
  $('feed').innerHTML=(cl.entries||[]).slice(0,30).map(e=>`<div class="ev"><div class="em">${e.icon}</div><div class="body">
    <div class="tx">${e.text}</div><div class="tm">${new Date(e.ts).toLocaleString([],{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'})}</div></div></div>`).join('');
}

function renderRecent(r){
  if(!$('recent')) return;
  const posts=(r.posts||[]);
  const ic={facebook:'📘',instagram:'📸',ig:'📸',youtube:'▶️',tiktok:'🎵',linkedin:'💼',bluesky:'🦋',telegram:'✈️',tumblr:'🌀',mastodon:'🐘',pinterest:'📌',threads:'🧵',blogger:'📝',blog:'📝'};
  if($('recentsum')) $('recentsum').textContent = posts.length ? `${posts.length} posts · ${new Set(posts.map(p=>p.channel)).size} channels` : 'none yet';
  $('recent').innerHTML = posts.slice(0,24).map(p=>{
    const t=new Date(p.ts).toLocaleString([],{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});
    const link=p.url?`<a class="rp-l" href="${p.url}" target="_blank" rel="noopener">↗</a>`:'';
    return `<div class="rp"><span class="rp-c">${ic[p.channel]||'•'} ${p.channel}</span><span class="rp-i">${p.item}</span><span class="rp-t">${t}</span>${link}</div>`;
  }).join('') || '<div class="muted" style="padding:8px 4px">No posts logged yet — first automated run will populate this.</div>';
}

function renderMafia(d){
  if(!$('mafiaMetrics')||!d.mafia) return;
  const m=d.mafia;
  const g=$('mafiaGrade'); g.textContent=m.overall; g.className='mafia-grade gcolor-'+m.overall;
  $('mafiaSummary').textContent=m.summary;
  $('mafiaMetrics').innerHTML=m.metrics.map(x=>
    `<div class="mcard"><div class="ml">${x.label}</div><div class="mv">${fmt(x.value)}</div><div class="mg gcolor-${x.grade}">${x.grade}</div></div>`).join('');
}

function setMafia(on){
  const mv=$('mafiaView'), nv=$('normalView'); if(!mv||!nv) return;
  mv.style.display=on?'':'none'; nv.style.display=on?'none':'';
  try{ localStorage.setItem('mafia',on?'1':'0'); }catch(e){}
}
function initMafia(){
  const t=$('mafiaToggle'); if(!t) return;
  let on=false; try{ on=localStorage.getItem('mafia')==='1'; }catch(e){}
  if(location.search.indexOf('mafia=1')>=0) on=true;
  t.checked=on; setMafia(on);
  t.addEventListener('change',()=>setMafia(t.checked));
}

async function load(){
  let d,cl,rec;
  try{ d=await (await fetch('data.json?'+Date.now())).json(); }catch(e){ return; }
  try{ cl=await (await fetch('changelog.json?'+Date.now())).json(); }catch(e){ cl={entries:[]}; }
  try{ rec=await (await fetch('recent.json?'+Date.now())).json(); }catch(e){ rec={posts:[]}; }
  if($('updated')) $('updated').textContent=new Date(d.updated).toLocaleString([],{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});
  renderScoreboard(d); renderRunway(d); renderCoverage(d); renderMafia(d); renderFunnel(d); renderGoals(d); renderStrategist(d);
  renderAgents(d); renderChannels(d); renderQueue(d); renderAds(d); renderSignups(d); renderSearch(d); renderAgenda(d); renderActivity(cl); renderRecent(rec);
}

function renderRunway(d){
  const el=$('runway'); if(!el||!d.runway) return;
  el.innerHTML=d.runway.map(r=>{
    const val=r.days!=null?`${r.days}d`:'evergreen';
    const w=r.days!=null?Math.max(4,Math.min(100,Math.round(r.days/14*100))):100;
    return `<div class="rwrow rw-${r.status}"><div class="rwlab">${r.label}</div>
      <div class="rwbar"><div class="rwfill" style="width:${w}%"></div></div>
      <div class="rwval">${fmt(r.remaining)} left · <b>${val}</b></div></div>`;
  }).join('');
  const a=$('runwayAlert'); if(!a) return;
  const low=d.runway.filter(r=>r.status!=='green').sort((x,y)=>(x.days??99)-(y.days??99));
  if(low.length){const w=low[0];
    a.textContent=`⚠ ${low.length} low — ${w.label}: ${w.days!=null?w.days+' days':'thin rotation'} left`;
    a.className='rwalert warn';
  } else { a.textContent='✓ all queues healthy'; a.className='rwalert ok'; }
}

function renderCoverage(d){
  const el=$('coverage'); if(!el||!d.coverage) return;
  const order=['Facebook','Instagram','YouTube','TikTok','LinkedIn','Pinterest','Bluesky','Mastodon','Threads','Telegram','Tumblr'];
  let gaps=0;
  el.innerHTML=order.filter(nm=>d.coverage[nm]).map(nm=>{
    const cells=d.coverage[nm].map(c=>{
      if(c.status==='live')  return `<span class="cov cov-live">${c.type} <b>${fmt(c.count)}</b></span>`;
      if(c.status==='soon')  return `<span class="cov cov-soon">${c.type} · soon</span>`;
      gaps++;                return `<span class="cov cov-gap">${c.type} · gap</span>`;
    }).join('');
    return `<div class="covrow"><div class="covnet">${EMO[nm]||''} ${nm}</div><div class="covcells">${cells}</div></div>`;
  }).join('');
  if($('covsum')) $('covsum').textContent=`${gaps} gap${gaps===1?'':'s'} to fill · long-form video is a separate project`;
}
// ===== Daily Tasks page =====
function gradeLetter(p){return p>=90?'A':p>=80?'B':p>=70?'C':p>=60?'D':'F';}
function localDate(){const d=new Date();return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');}
function taskRow(t,done,total,kind){
  const extra=(t.extra||[]).map(e=>`<a class="tlink alt" href="${e.link}" target="_blank" rel="noopener">${e.label} →</a>`).join('');
  return `<div class="task ${done?'done':''}"><label class="chk"><input type="checkbox" ${done?'checked':''} data-id="${t.id}" data-total="${total}" data-kind="${kind}"/><span class="box"></span></label>
    <div class="tbody"><div class="tt">${t.emoji||''} ${t.task} <span class="test">${t.est||''}</span></div>
    <div class="tnote">${t.note||''}</div>
    <div class="tlinks"><a class="tlink" href="${t.link}" target="_blank" rel="noopener">Open →</a>${extra}</div></div></div>`;
}
function updateGrades(doneCount,total,running,days){
  const pct=total?Math.round(100*doneCount/total):0;
  if($('todayGrade')){const L=gradeLetter(pct);$('todayGrade').textContent=total?L:'—';$('todayGrade').className='gbig gcolor-'+(total?L:'F');$('todayPct').textContent=pct+'% · '+doneCount+'/'+total+' done';}
  if($('runGrade')){const L=gradeLetter(running);$('runGrade').textContent=days?L:'—';$('runGrade').className='gbig gcolor-'+(days?L:'F');$('runPct').textContent=days?(running+'% avg · '+days+' day'+(days>1?'s':'')):'no history yet';}
}
function rosterRow(g,done){
  return `<div class="task ${done?'done':''}"><label class="chk"><input type="checkbox" ${done?'checked':''} data-id="${g.id}" data-total="0" data-kind="roster"/><span class="box"></span></label>
    <div class="tbody"><div class="tt"><span class="kchip k-${(g.kind||'').toLowerCase()}">${g.kind||''}</span> ${g.label}</div>
    <div class="tnote">${g.note||''}</div>
    <div class="tlinks"><a class="tlink" href="${g.link}" target="_blank" rel="noopener">Search & join →</a></div></div></div>`;
}
function renderRoster(roster,doneSet){
  if(!$('rosterList')) return;
  if($('rosterCount')){const j=roster.filter(g=>doneSet.has(g.id)).length;$('rosterCount').textContent=j+' / '+roster.length+' joined';}
  $('rosterList').innerHTML=roster.map(g=>rosterRow(g,doneSet.has(g.id))).join('')||'<p style="color:var(--muted)">No roster yet.</p>';
}
function fmtK(n){return n>=1e6?(n/1e6).toFixed(n>=1e7?0:1)+'M':n>=1e3?Math.round(n/1e3)+'k':String(n);}
function discRow(href,title,meta,desc){
  return `<a class="drow" href="${href}" target="_blank" rel="noopener"><div class="dmain"><span class="dt">${title}</span>${meta?`<span class="dm">${meta}</span>`:''}</div>${desc?`<div class="dd">${desc}</div>`:''}</a>`;
}
async function renderDiscovery(){
  if(!$('discReddit')) return;
  let d={};
  try{ d=await (await fetch('discovery.json?'+Date.now())).json(); }catch(e){ return; }
  $('discReddit').innerHTML=(d.reddit||[]).map(r=>discRow(r.link,r.name,fmtK(r.members)+' members',r.desc)).join('')||'<p class="dhint">—</p>';
  $('discBluesky').innerHTML=(d.bluesky||[]).map(b=>discRow(b.link,b.handle,fmtK(b.followers)+' followers',b.desc||b.display)).join('')||'<p class="dhint">—</p>';
  const m=d.mastodon||{};
  if($('discMastoTags')) $('discMastoTags').innerHTML=(m.tags||[]).map(t=>`<a class="tagpill" href="${t.link}" target="_blank" rel="noopener">${t.tag}<span>${fmtK(t.uses)}/wk</span></a>`).join('')||'';
  if($('discMastoAccts')) $('discMastoAccts').innerHTML=(m.accounts||[]).map(a=>discRow(a.link,a.handle,fmtK(a.followers)+' followers','')).join('');
  if($('discUpdated')&&d.updated) $('discUpdated').textContent='Auto-discovered '+d.updated.replace('T',' ').replace('Z',' UTC');
}
async function initTasks(){
  if(!$('tasksList')) return;
  const date=localDate();
  let tasks={daily:[],setup:[]}, state={daily:[],setup:[],running:0,days:0};
  try{ tasks=await (await fetch('tasks.json?'+Date.now())).json(); }catch(e){}
  try{ state=await (await fetch('/tasks/state?date='+date)).json(); }catch(e){}
  const doneD=new Set(state.daily||[]), doneS=new Set(state.setup||[]);
  const total=(tasks.daily||[]).length;
  const byP={}; (tasks.daily||[]).forEach(t=>{(byP[t.platform]=byP[t.platform]||[]).push(t);});
  $('tasksList').innerHTML=Object.entries(byP).map(([plat,ts])=>
    `<div class="panel"><h3>${ts[0].emoji} ${plat}</h3>${ts.map(t=>taskRow(t,doneD.has(t.id),total,'daily')).join('')}</div>`).join('')
    || '<p style="color:var(--muted)">No tasks yet — generating.</p>';
  if($('setupList')) $('setupList').innerHTML=(tasks.setup||[]).map(t=>taskRow(t,doneS.has(t.id),0,'setup')).join('');
  renderRoster(tasks.roster||[],new Set(state.roster||[]));
  renderDiscovery();
  if($('taskDate')) $('taskDate').textContent='List for '+(tasks.date||date);
  let curDays=state.days||0;
  updateGrades(doneD.size,total,state.running||0,curDays);
  document.querySelectorAll('#tasksList input, #setupList input, #rosterList input').forEach(cb=>{
    cb.addEventListener('change',async()=>{
      cb.closest('.task').classList.toggle('done',cb.checked);
      const body={date,id:cb.dataset.id,total:parseInt(cb.dataset.total||'0'),kind:cb.dataset.kind};
      try{ const r=await (await fetch('/tasks/toggle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})).json();
        if(body.kind==='daily'){ curDays=r.days||curDays; updateGrades((r.done||[]).length,total,r.running||0,curDays); }
        if(body.kind==='roster'&&$('rosterCount')){const n=(r.roster||[]).length;$('rosterCount').textContent=n+' / '+(tasks.roster||[]).length+' joined';}
      }catch(e){}
    });
  });
}

initMafia(); initTasks(); load(); setInterval(load, 60000);
