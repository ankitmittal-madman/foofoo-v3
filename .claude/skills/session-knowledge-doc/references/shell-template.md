# Shell Template for New Knowledge Books

When `KNOWLEDGE.html` does not exist, generate this full file.
Replace `{{PROJECT_NAME}}` and `{{PROJECT_DESC}}` before writing.
All `<!-- *_INJECT -->` comments MUST be preserved — they are how future sessions inject content.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{PROJECT_NAME}} — Build Knowledge</title>
<style>
  :root {
    --bg:#f7f6f3; --surface:#ffffff; --surface2:#f2f1ee;
    --border:#e4e2dc; --border2:#d0cec7;
    --text:#1a1917; --text2:#6b6860; --text3:#9e9b94;
    --blue:#1a56db; --blue-bg:#eff4ff; --blue-border:#c3d4fa;
    --teal:#0e7a5a; --teal-bg:#e8f8f2; --teal-border:#a3dfc9;
    --purple:#5145b8; --purple-bg:#f0effe; --purple-border:#c8c4f4;
    --amber:#92500a; --amber-bg:#fef8ec; --amber-border:#f5d68a;
    --green:#166534; --green-bg:#f0fdf4; --green-border:#86efac;
    --orange:#9a3412; --orange-bg:#fff7ed; --orange-border:#fdba74;
    --sidebar-w:220px; --radius:8px; --radius-sm:5px;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);font-size:14px;display:flex;min-height:100vh}

  #sidebar{width:var(--sidebar-w);flex-shrink:0;background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column;position:sticky;top:0;height:100vh;overflow-y:auto}
  .sidebar-logo{padding:18px 16px 14px;border-bottom:1px solid var(--border)}
  .sidebar-logo .app-name{font-size:15px;font-weight:600}
  .sidebar-logo .app-sub{font-size:11px;color:var(--text3);margin-top:2px}
  .sidebar-section{padding:10px 10px 4px}
  .sidebar-section-label{font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--text3);padding:0 6px;margin-bottom:4px}
  .nav-item{display:flex;align-items:center;gap:8px;padding:7px 10px;border-radius:var(--radius-sm);cursor:pointer;color:var(--text2);font-size:13px;transition:background .12s,color .12s;user-select:none}
  .nav-item:hover{background:var(--surface2);color:var(--text)}
  .nav-item.active{background:var(--blue-bg);color:var(--blue);font-weight:500}
  .nav-item .nav-icon{font-size:14px;flex-shrink:0}
  .nav-item .nav-badge{margin-left:auto;font-size:10px;padding:1px 6px;border-radius:10px;background:var(--surface2);color:var(--text3)}
  .nav-item.active .nav-badge{background:var(--blue-border);color:var(--blue)}
  .sidebar-divider{border:none;border-top:1px solid var(--border);margin:6px 10px}

  #main{flex:1;overflow-y:auto;padding:28px 32px;max-width:860px}
  .page-header{margin-bottom:24px}
  .page-title{font-size:22px;font-weight:600;margin-bottom:4px}
  .page-subtitle{font-size:13px;color:var(--text2);line-height:1.6}

  .session-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:18px 20px;margin-bottom:20px}
  .session-card-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px}
  .session-card-title{font-size:16px;font-weight:600}
  .session-card-meta{font-size:11px;color:var(--text3);text-align:right;line-height:1.7}
  .session-card-desc{font-size:13px;color:var(--text2);line-height:1.6;margin-bottom:14px}
  .stat-row{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
  .stat{background:var(--surface2);border-radius:var(--radius-sm);padding:10px 12px;text-align:center}
  .stat-n{font-size:20px;font-weight:600}
  .stat-l{font-size:11px;color:var(--text3);margin-top:2px}

  .view-tabs{display:flex;gap:2px;margin-bottom:20px;border-bottom:1px solid var(--border)}
  .view-tab{padding:8px 16px;font-size:13px;font-weight:500;color:var(--text2);cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px;transition:color .12s,border-color .12s;user-select:none;white-space:nowrap}
  .view-tab:hover{color:var(--text)}
  .view-tab.active{color:var(--blue);border-bottom-color:var(--blue)}
  .view-pane{display:none}.view-pane.active{display:block}

  .swim-lane{display:flex;margin-bottom:10px}
  .swim-label{width:100px;flex-shrink:0;display:flex;align-items:flex-start;justify-content:flex-end;padding:14px 12px 12px 0}
  .swim-label-inner{text-align:right}
  .swim-label-title{font-size:11px;font-weight:600;color:var(--text2)}
  .swim-label-sub{font-size:10px;color:var(--text3);margin-top:1px}
  .swim-body{flex:1;border-radius:var(--radius);border:1px solid var(--border);padding:10px 12px;display:flex;flex-direction:column;gap:6px}
  .lane-blue .swim-body{background:var(--blue-bg);border-color:var(--blue-border)}
  .lane-teal .swim-body{background:var(--teal-bg);border-color:var(--teal-border)}
  .lane-amber .swim-body{background:var(--amber-bg);border-color:var(--amber-border)}
  .swim-step{display:flex;align-items:flex-start;gap:8px;padding:2px 0}
  .step-num{width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:600;flex-shrink:0;margin-top:1px}
  .num-blue{background:var(--blue-bg);color:var(--blue);border:1px solid var(--blue-border)}
  .num-purple{background:var(--purple-bg);color:var(--purple);border:1px solid var(--purple-border)}
  .num-teal{background:var(--teal-bg);color:var(--teal);border:1px solid var(--teal-border)}
  .num-amber{background:var(--amber-bg);color:var(--amber);border:1px solid var(--amber-border)}
  .step-content{flex:1}
  .step-title-row{display:flex;align-items:center;gap:6px;margin-bottom:2px}
  .step-title{font-size:13px;font-weight:500}
  .step-desc{font-size:12px;color:var(--text2);line-height:1.5}
  .swim-arrow{text-align:center;font-size:11px;color:var(--text3);padding:4px 0;padding-left:112px}

  .tag{font-size:10px;padding:2px 7px;border-radius:10px;font-weight:500;flex-shrink:0}
  .tag-new{background:var(--green-bg);color:var(--green);border:1px solid var(--green-border)}
  .tag-mod{background:var(--orange-bg);color:var(--orange);border:1px solid var(--orange-border)}
  .tag-db{background:var(--purple-bg);color:var(--purple);border:1px solid var(--purple-border)}
  .tag-cfg{background:var(--blue-bg);color:var(--blue);border:1px solid var(--blue-border)}

  .detail-item{margin-bottom:8px}
  .detail-row{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);cursor:pointer;transition:border-color .12s,border-radius .12s;user-select:none}
  .detail-row:hover{border-color:var(--border2)}
  .detail-row.open{border-color:var(--blue-border);border-radius:var(--radius-sm) var(--radius-sm) 0 0}
  .detail-left{display:flex;align-items:center;gap:8px}
  .detail-name{font-size:13px;font-weight:500;font-family:'SF Mono','Fira Code',monospace}
  .detail-name.plain{font-family:inherit}
  .detail-chevron{font-size:12px;color:var(--text3);transition:transform .15s}
  .detail-chevron.open{transform:rotate(180deg)}
  .detail-drawer{display:none;background:var(--surface2);border:1px solid var(--blue-border);border-top:none;border-radius:0 0 var(--radius-sm) var(--radius-sm);padding:12px 14px;margin-bottom:8px}
  .detail-drawer.open{display:block}
  .dd-label{font-size:10px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--text3);margin-bottom:4px;margin-top:12px}
  .dd-label:first-child{margin-top:0}
  .dd-text{font-size:13px;color:var(--text2);line-height:1.6}
  .dd-flow{display:flex;align-items:center;gap:5px;flex-wrap:wrap;margin-top:5px}
  .dd-node{font-size:11px;padding:3px 9px;border-radius:var(--radius-sm);background:var(--surface);border:1px solid var(--border);color:var(--text2);white-space:nowrap}
  .dd-arrow{font-size:11px;color:var(--text3)}
  .dd-code{font-family:'SF Mono','Fira Code',monospace;font-size:12px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);padding:8px 10px;color:var(--text2);line-height:1.8;margin-top:5px}
  .dd-hl{color:#92400e;font-weight:600;background:#fef3c7;padding:1px 3px;border-radius:3px}
  .dd-why{padding:8px 12px;border-left:3px solid var(--teal-border);background:var(--teal-bg);border-radius:0 var(--radius-sm) var(--radius-sm) 0;margin-top:5px}
  .dd-why-q{font-size:11px;font-weight:600;color:var(--teal);margin-bottom:3px}
  .dd-why-a{font-size:12px;color:var(--text2);line-height:1.5}

  .arch-section{margin-bottom:20px}
  .arch-section-title{font-size:12px;font-weight:600;color:var(--text2);margin-bottom:8px;display:flex;align-items:center;gap:6px;padding-bottom:6px;border-bottom:1px solid var(--border)}
  .arch-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));gap:7px}
  .arch-node{position:relative;padding:10px 12px;border-radius:var(--radius-sm);border:1px solid var(--border);background:var(--surface);cursor:default;transition:border-color .12s,background .12s}
  .arch-node[onclick]{cursor:pointer}
  .arch-node[onclick]:hover{border-color:var(--border2);background:var(--surface2)}
  .arch-node[onclick]::after{content:"↗";position:absolute;top:8px;right:10px;color:var(--text3);font-size:11px}
  .arch-node.is-new{border-color:var(--teal-border);background:var(--teal-bg)}
  .arch-node.is-mod{border-color:var(--orange-border);background:var(--orange-bg)}
  .arch-node-name{font-size:12px;font-weight:600;font-family:'SF Mono','Fira Code',monospace;margin-bottom:2px}
  .arch-node-name.plain{font-family:inherit}
  .arch-node-desc{font-size:11px;color:var(--text3);line-height:1.4}
  .arch-legend{display:flex;gap:12px;margin-bottom:12px}
  .legend-item{display:flex;align-items:center;gap:5px;font-size:11px;color:var(--text3)}
  .legend-dot{width:10px;height:10px;border-radius:2px}

  .timeline-row{display:flex;gap:0}
  .tl-date{width:80px;flex-shrink:0;padding:12px 14px 0 0;text-align:right;font-size:11px;color:var(--text3);line-height:1.5}
  .tl-spine{width:1px;background:var(--border);flex-shrink:0;position:relative}
  .tl-dot{position:absolute;top:16px;left:-5px;width:11px;height:11px;border-radius:50%;border:2px solid var(--bg)}
  .tl-content{flex:1;padding:8px 0 24px 18px}
  .tl-badge{font-size:11px;font-weight:600;padding:2px 8px;border-radius:10px;display:inline-block;margin-bottom:5px}
  .tl-title{font-size:14px;font-weight:600;margin-bottom:5px}
  .tl-chips{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:5px}
  .tl-chip{font-size:11px;padding:2px 8px;border-radius:10px;background:var(--surface);border:1px solid var(--border);color:var(--text2);cursor:pointer;transition:border-color .1s}
  .tl-chip:hover{border-color:var(--blue-border);color:var(--blue)}
  .tl-note{font-size:12px;color:var(--text2);line-height:1.5}

  .next-box{margin-top:20px;padding:12px 16px;border:1px dashed var(--border2);border-radius:var(--radius);background:var(--surface)}
  .next-label{font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--text3);margin-bottom:4px}
  .next-text{font-size:13px;color:var(--text2);line-height:1.6}

  .files-table{width:100%;border-collapse:collapse;font-size:13px}
  .files-table th{text-align:left;font-size:10px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--text3);padding:6px 10px;border-bottom:1px solid var(--border)}
  .files-table td{padding:8px 10px;border-bottom:1px solid var(--border);vertical-align:top}
  .fr-file{font-family:'SF Mono','Fira Code',monospace;font-size:12px}
  .fr-session{color:var(--text3);font-size:12px;white-space:nowrap}
  .fr-desc{color:var(--text2);font-size:12px}

  .decision-item{padding:12px 14px;border:1px solid var(--border);border-radius:var(--radius-sm);margin-bottom:8px;background:var(--surface)}
  .decision-q{font-size:13px;font-weight:500;margin-bottom:4px}
  .decision-a{font-size:13px;color:var(--text2);line-height:1.6;margin-bottom:6px}
  .decision-meta{font-size:11px;color:var(--text3)}

  .empty-pane{text-align:center;padding:48px 24px;color:var(--text3)}
  .empty-pane h3{font-size:15px;font-weight:600;color:var(--text2);margin-bottom:6px}
  .empty-pane p{font-size:13px;line-height:1.6}

  /* ── Feature flows tab (per-session) ── */
  .ff-tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}
  .ff-tab{padding:9px 16px;border:1px solid var(--border);border-radius:8px;background:var(--surface);font-size:13px;font-weight:500;color:var(--text);cursor:pointer;transition:border-color .12s,color .12s;user-select:none}
  .ff-tab:hover{border-color:var(--border2)}
  .ff-tab.active{border-color:#1a56db;color:#1a56db}
  .ff-meta{font-size:13px;color:var(--text2);margin-bottom:14px}
  .ff-step{border:1px solid var(--border);border-radius:var(--radius);margin-bottom:10px;background:var(--surface);overflow:hidden}
  .ff-step-header{display:flex;align-items:center;gap:10px;padding:13px 16px;cursor:pointer;user-select:none}
  .ff-step-num{width:24px;height:24px;border-radius:50%;border:1px solid var(--border2);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;color:var(--text2);flex-shrink:0}
  .ff-pill{font-size:11px;font-weight:600;padding:3px 9px;border-radius:10px;flex-shrink:0}
  .ff-step-title{font-size:14px;font-weight:600;color:var(--text);flex:1}
  .ff-chevron{font-size:12px;color:var(--text3);flex-shrink:0}
  .ff-step-body{display:none;padding:0 16px 16px 60px}
  .ff-step.open .ff-step-body{display:block}
  .ff-section-label{font-size:10px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--text3);margin:14px 0 6px}
  .ff-section-label:first-child{margin-top:0}
  .ff-desc{font-size:13px;color:var(--text2);line-height:1.6}
  .ff-codeflow{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
  .ff-code-chip{font-family:'SF Mono','Fira Code',monospace;font-size:11px;background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:5px 10px;color:var(--text)}
  .ff-code-arrow{font-size:12px;color:var(--text3)}
  .ff-files-touched{display:flex;flex-direction:column;gap:7px}
  .ff-file-row{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
  .ff-file-chip{font-family:'SF Mono','Fira Code',monospace;font-size:11px;background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:4px 9px;color:var(--text)}
  .ff-file-desc{font-size:12px;color:var(--text2)}
  .ff-api-row,.ff-db-row{font-size:12px;color:var(--text2);display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}
  .ff-api-name,.ff-db-name{font-family:'SF Mono','Fira Code',monospace;font-weight:600;color:var(--text);flex-shrink:0}
  .ff-deepdive{margin-top:14px;text-align:center}
  .ff-deepdive-btn{padding:10px 18px;border-radius:8px;border:1px solid var(--blue-border);background:var(--blue-bg);color:var(--blue);font-size:13px;font-weight:600;cursor:pointer}
  .ff-deepdive-btn:hover{background:var(--blue-border)}

  @media(max-width:640px){#sidebar{display:none}#main{padding:20px 16px}.stat-row{grid-template-columns:repeat(2,1fr)}}
</style>
</head>
<body>

<script>
function showPage(id){
  document.querySelectorAll('.page-content').forEach(p=>p.style.display='none');
  const pg=document.getElementById('page-'+id);
  if(pg) pg.style.display='block';
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n=>{
    const oc=n.getAttribute('onclick')||'';
    if(oc.includes("'"+id+"'"))n.classList.add('active');
  });
}
function switchView(session,view){
  const pg=document.getElementById('page-'+session);
  if(!pg)return;
  pg.querySelectorAll('.view-pane').forEach(p=>p.classList.remove('active'));
  pg.querySelectorAll('.view-tab').forEach(t=>t.classList.remove('active'));
  const vp=document.getElementById(session+'-'+view);
  if(vp)vp.classList.add('active');
  if(event&&event.target)event.target.classList.add('active');
}
// Jump from swim lane step → detail drawer (F13)
function jumpDetail(session,id){
  switchView(session,'detail',null);
  setTimeout(()=>{
    const dr=document.getElementById('draw-'+session+'-'+id);
    if(dr&&!dr.classList.contains('open'))toggleDetail(session+'-'+id);
    const rw=document.getElementById('row-'+session+'-'+id);
    if(rw)rw.scrollIntoView({behavior:'smooth',block:'start'});
  },60);
}
// Jump from an architecture tile → its Module Reference entry (F24)
function jumpModule(id){
  showPage('modules');
  setTimeout(()=>{
    const dr=document.getElementById('draw-mod-'+id);
    if(dr&&!dr.classList.contains('open'))toggleDetail('mod-'+id);
    const rw=document.getElementById('row-mod-'+id);
    if(rw)rw.scrollIntoView({behavior:'smooth',block:'start'});
  },60);
}
function toggleDetail(id){
  const dr=document.getElementById('draw-'+id);
  const ch=document.getElementById('chev-'+id);
  if(!dr||!ch)return;
  const row=ch.closest('.detail-row');
  const isOpen=dr.classList.contains('open');
  dr.classList.toggle('open',!isOpen);
  row&&row.classList.toggle('open',!isOpen);
  ch.classList.toggle('open',!isOpen);
}

// ── Feature flows tab (per-session) ──
// Renders a flows[] array (see references/session-block-template.md) into rootId.
// Called once per session from that session's own inline <script>, e.g.:
//   renderFeatureFlows('s3-flows', FEATURE_FLOWS_S3);
function renderFeatureFlows(rootId, flows){
  const root=document.getElementById(rootId);
  if(!root||!flows||!flows.length)return;
  const layerMeta={
    'Phone':{bg:'#E6F1FB',color:'#0C447C'},
    'App logic':{bg:'#E1F5EE',color:'#085041'},
    'Middleware':{bg:'#FAEEDA',color:'#633806'},
    'Server':{bg:'#FFF0F0',color:'#791F1F'},
    'Database':{bg:'#EEEDFE',color:'#3C3489'},
    'Service':{bg:'#FAECE7',color:'#712B13'}
  };
  const tagMeta={
    'UI':{bg:'#E6F1FB',color:'#0C447C'},
    'HOOK':{bg:'#E1F5EE',color:'#085041'},
    'API':{bg:'#FAEEDA',color:'#633806'},
    'DB':{bg:'#EEEDFE',color:'#3C3489'},
    'SDK':{bg:'#FAECE7',color:'#712B13'},
    'POLICY':{bg:'#FBEAF0',color:'#72243E'}
  };
  function esc(s){return (s==null?'':String(s)).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function pill(text,meta){
    const m=meta[text]||{bg:'#f2f1ee',color:'#6b6860'};
    return '<span class="ff-pill" style="background:'+m.bg+';color:'+m.color+'">'+esc(text)+'</span>';
  }
  let html='<div class="ff-tabs">';
  flows.forEach((f,i)=>{html+='<div class="ff-tab'+(i===0?' active':'')+'" data-ff-tab="'+i+'">'+esc(f.label)+'</div>';});
  html+='</div>';
  flows.forEach((f,i)=>{
    html+='<div class="ff-panel" data-ff-panel="'+i+'" style="'+(i===0?'':'display:none')+'">';
    html+='<div class="ff-meta">'+esc(f.label)+' · '+f.steps.length+' steps · click any step to see the code files and data flow</div>';
    f.steps.forEach((s,si)=>{
      const uid=rootId+'-f'+i+'-s'+si;
      html+='<div class="ff-step" id="'+uid+'">';
      html+='<div class="ff-step-header" onclick="toggleFeatureStep(\''+uid+'\')">';
      html+='<div class="ff-step-num">'+(si+1)+'</div>';
      html+=pill(s.layer,layerMeta);
      if(s.tag)html+=pill(s.tag,tagMeta);
      html+='<div class="ff-step-title">'+esc(s.title)+'</div>';
      html+='<span class="ff-chevron" id="'+uid+'-chev">▾</span>';
      html+='</div>';
      html+='<div class="ff-step-body" id="'+uid+'-body">';
      html+='<div class="ff-desc">'+esc(s.desc)+'</div>';
      if(s.codeFlow&&s.codeFlow.length){
        html+='<div class="ff-section-label">Code flow</div><div class="ff-codeflow">';
        s.codeFlow.forEach(c=>{
          if(c.chip!=null)html+='<span class="ff-code-chip">'+esc(c.chip)+'</span>';
          else if(c.label!=null)html+='<span class="ff-code-arrow">→ '+esc(c.label)+'</span>';
        });
        html+='</div>';
      }
      if(s.files&&s.files.length){
        html+='<div class="ff-section-label">Files touched</div><div class="ff-files-touched">';
        s.files.forEach(fl=>{
          html+='<div class="ff-file-row"><span class="ff-file-chip">📄 '+esc(fl.path)+'</span><span class="ff-file-desc">'+esc(fl.desc)+'</span></div>';
        });
        html+='</div>';
      }
      if(s.api){
        html+='<div class="ff-section-label">API contract</div><div class="ff-api-row"><span class="ff-api-name">'+esc(s.api.endpoint)+'</span><span>'+esc(s.api.note)+'</span></div>';
      }
      if(s.db){
        html+='<div class="ff-section-label">Database</div><div class="ff-db-row"><span class="ff-db-name">'+esc(s.db.table)+' · '+esc(s.db.op)+'</span><span>'+esc(s.db.note)+'</span></div>';
      }
      html+='</div></div>';
    });
    html+='<div class="ff-deepdive"><button class="ff-deepdive-btn" onclick="deepDiveFeature(\''+esc(f.label).replace(/'/g,"\\'")+'\')">🔎 Deep-dive: error handling &amp; edge cases for '+esc(f.label)+'</button></div>';
    html+='</div>';
  });
  root.innerHTML=html;
  root.querySelectorAll('.ff-tab').forEach(tab=>{
    tab.addEventListener('click',function(){
      const idx=this.getAttribute('data-ff-tab');
      root.querySelectorAll('.ff-tab').forEach(t=>t.classList.remove('active'));
      this.classList.add('active');
      root.querySelectorAll('.ff-panel').forEach(p=>{p.style.display=(p.getAttribute('data-ff-panel')===idx)?'':'none';});
    });
  });
}
function toggleFeatureStep(uid){
  const body=document.getElementById(uid+'-body');
  const chev=document.getElementById(uid+'-chev');
  const step=document.getElementById(uid);
  if(!body||!chev||!step)return;
  const isOpen=step.classList.contains('open');
  step.classList.toggle('open',!isOpen);
  chev.textContent=isOpen?'▾':'▴';
}
function deepDiveFeature(featureLabel){
  const prompt='Go deeper on error handling and edge cases for the "'+featureLabel+'" feature flow documented in KNOWLEDGE.html — what can fail at each step, and how is/should it be handled?';
  if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(prompt).then(()=>{
      alert('Prompt copied to clipboard — paste it into Claude Code to go deeper:\n\n'+prompt);
    }).catch(()=>{alert(prompt);});
  }else{
    alert(prompt);
  }
}
</script>


<nav id="sidebar">
  <div class="sidebar-logo">
    <div class="app-name">{{PROJECT_NAME}}</div>
    <div class="app-sub">Build knowledge base</div>
  </div>

  <div class="sidebar-section">
    <div class="sidebar-section-label">Overview</div>
    <div class="nav-item active" onclick="showPage('arch-full')">
      <span class="nav-icon">🗺</span> App architecture
    </div>
    <div class="nav-item" onclick="showPage('timeline-full')">
      <span class="nav-icon">📅</span> Build timeline
    </div>
    <div class="nav-item" onclick="showPage('flow')">
      <span class="nav-icon">🔀</span> System flow
    </div>
  </div>

  <hr class="sidebar-divider">

  <div class="sidebar-section">
    <div class="sidebar-section-label">Sessions</div>
    <!-- NAV_INJECT -->
  </div>

  <hr class="sidebar-divider">

  <div class="sidebar-section">
    <div class="sidebar-section-label">Reference</div>
    <div class="nav-item" onclick="showPage('modules')">
      <span class="nav-icon">🧩</span> Modules
    </div>
    <div class="nav-item" onclick="showPage('files')">
      <span class="nav-icon">📁</span> Files register
    </div>
    <div class="nav-item" onclick="showPage('db')">
      <span class="nav-icon">🗄</span> Database schema
    </div>
    <div class="nav-item" onclick="showPage('decisions')">
      <span class="nav-icon">💡</span> Key decisions
    </div>
  </div>
</nav>

<main id="main">

  <!-- ── Architecture page ── -->
  <div id="page-arch-full" class="page-content">
    <div class="page-header">
      <div class="page-title">App architecture</div>
      <div class="page-subtitle">{{PROJECT_DESC}} — all components across all sessions. Teal = new this session · Amber = modified.</div>
    </div>
    <div class="arch-legend">
      <div class="legend-item"><div class="legend-dot" style="background:var(--teal-bg);border:1px solid var(--teal-border)"></div> New this session</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--orange-bg);border:1px solid var(--orange-border)"></div> Modified</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--surface);border:1px solid var(--border)"></div> Existing</div>
    </div>
    <div class="arch-section">
      <div class="arch-section-title">📱 Phone — screens</div>
      <div class="arch-grid" id="arch-phone">
        <!-- ARCH_PHONE_INJECT -->
      </div>
    </div>
    <div class="arch-section">
      <div class="arch-section-title">🧠 App Logic — repositories, hooks &amp; config</div>
      <div class="arch-grid" id="arch-applogic">
        <!-- ARCH_APPLOGIC_INJECT -->
      </div>
    </div>
    <div class="arch-section">
      <div class="arch-section-title">🗄 Database — tables</div>
      <div class="arch-grid" id="arch-db">
        <!-- ARCH_DB_INJECT -->
      </div>
    </div>
    <div class="arch-section">
      <div class="arch-section-title">☁️ Server — functions</div>
      <div class="arch-grid" id="arch-server">
        <!-- ARCH_SERVER_INJECT -->
      </div>
    </div>
    <div class="arch-section">
      <div class="arch-section-title">🔌 Services</div>
      <div class="arch-grid" id="arch-services">
        <!-- ARCH_SERVICES_INJECT -->
      </div>
    </div>
  </div>

  <!-- ── System flow page ── -->
  <div id="page-flow" class="page-content" style="display:none">
    <div class="page-header">
      <div class="page-title">System flow</div>
      <div class="page-subtitle">How a request actually travels through the app, step by step — click any step to see its full explanation.</div>
    </div>
    <!-- FLOWS_INJECT -->
  </div>

  <!-- ── Timeline page ── -->
  <div id="page-timeline-full" class="page-content" style="display:none">
    <div class="page-header">
      <div class="page-title">Build timeline</div>
      <div class="page-subtitle">Every session in order. Click any chip to open that session's full doc.</div>
    </div>
    <!-- TIMELINE_INJECT -->
  </div>

  <!-- ── Modules ── -->
  <div id="page-modules" class="page-content" style="display:none">
    <div class="page-header">
      <div class="page-title">Modules</div>
      <div class="page-subtitle">What each piece of code or database table is actually for, in plain English — click an architecture tile to jump straight to its entry here.</div>
    </div>
    <!-- MODULES_INJECT -->
  </div>

  <!-- ── Files register ── -->
  <div id="page-files" class="page-content" style="display:none">
    <div class="page-header">
      <div class="page-title">Files register</div>
      <div class="page-subtitle">Every file Claude has created or modified, with the session it was introduced.</div>
    </div>
    <table class="files-table">
      <thead><tr><th>File</th><th>Type</th><th>Session</th><th>Description</th></tr></thead>
      <tbody>
        <!-- FILES_INJECT -->
      </tbody>
    </table>
  </div>

  <!-- ── DB schema ── -->
  <div id="page-db" class="page-content" style="display:none">
    <div class="page-header">
      <div class="page-title">Database schema</div>
      <div class="page-subtitle">Current state of all tables and columns. Updated whenever a migration runs.</div>
    </div>
    <div class="empty-pane"><h3>Updated each session</h3><p>Claude updates this whenever a migration is added.</p></div>
  </div>

  <!-- ── Decisions log ── -->
  <div id="page-decisions" class="page-content" style="display:none">
    <div class="page-header">
      <div class="page-title">Key decisions log</div>
      <div class="page-subtitle">Every significant architectural decision made, and why.</div>
    </div>
    <!-- DECISIONS_INJECT -->
  </div>

  <!-- ── Session pages injected here ── -->
  <!-- SESSIONS_INJECT -->

</main>

</body>
</html>
```
