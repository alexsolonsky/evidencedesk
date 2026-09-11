'use strict';
const $ = id => document.getElementById(id);
let state = null, ready = false, busy = false, timer = null;
const editable = ['diff','diff-file','model','import-json','review-file','example','analyze','validate'];
function setBusy(value, message) {
  busy = value;
  editable.forEach(id => $(id).disabled = value);
  $('model').disabled = value || !ready;
  $('review').disabled = value || !ready;
  $('download').disabled = value || !state;
  $('status').textContent = message;
  clearInterval(timer);
  if(value) { const start = Date.now(); timer = setInterval(() => {$('status').textContent = `${message} ${Math.floor((Date.now()-start)/1000)}s`;},1000); }
}
function error(message) { $('error').hidden = false; $('error').textContent = message; }
async function api(path, data) {
  const response = await fetch(path, data ? {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)} : {});
  const result = await response.json();
  if(!response.ok) throw Error(result.error || 'Request failed');
  return result;
}
function text(tag, value, className) { const el=document.createElement(tag); el.textContent=value; if(className)el.className=className; return el; }
function evidenceLine(id, index) {
  const line=index[id];
  if(!line)return text('p',`Unresolved reference: ${id}`);
  const el=document.createElement('div');el.className=`line ${line.kind}`;
  el.append(text('div',`${line.path} · ${line.side} line ${line.line}`, 'line-head'));
  el.append(text('code',`${line.kind==='added'?'+':'−'} ${line.text}`));
  el.append(text('span',id+(line.no_newline_at_eof?' · no newline at EOF':''),'line-id'));return el;
}
function render(result) {
  state=result; $('empty').hidden=true; $('stats').hidden=false;
  const p=result.evidence_pack;
  $('stats').replaceChildren(...[`${p.changed_file_count} files`,`+${p.text_added_count} lines`,`−${p.text_removed_count} lines`].map(s=>text('span',s)));
  $('claims').replaceChildren();$('evidence').replaceChildren();
  Object.keys(result.evidence_index).forEach(id=>$('evidence').append(evidenceLine(id,result.evidence_index)));
  $('all-evidence').hidden=false;
  $('provenance').hidden=!result.provenance;
  if(result.provenance){const v=result.provenance;$('provenance').textContent=v.kind==='live_local_ollama'?`LIVE LOCAL AI · ${v.model} · ${v.elapsed_seconds}s · ${v.created_at}`:'IMPORTED REVIEW · Authorship not verified';}
  $('validation').hidden=!result.validation;
  if(result.validation){const v=result.validation;$('validation').textContent=(v.structurally_valid?'References passed structural validation.':'Review validation failed.')+' Semantic truth is not verified.'+(v.errors.length?'\n'+v.errors.map(x=>`${x.path}: ${x.message}`).join('\n'):'');}
  if(result.review && result.validation?.structurally_valid) {
    if(!result.review.claims.length)$('claims').append(text('p','This review contains no claims.'));
    result.review.claims.forEach(c=>{const card=document.createElement('article');card.className='claim';card.append(text('span',`${c.status} · AI assessment`,'claim-label'),text('h3',c.claim),text('p',c.rationale));c.evidence_ids.forEach(id=>card.append(evidenceLine(id,result.evidence_index)));$('claims').append(card);});
  }
  $('download').disabled=false;
}
async function run(path, progress) {
  if(busy)return;$('error').hidden=true;setBusy(true,progress);
  try {const result=await api(path,{diff:$('diff').value,model:$('model').value,review:$('import-json').value});render(result);setBusy(false,result.validation && !result.validation.structurally_valid?'Review validation failed. Inspect the errors below.':result.review?'Review complete. Inspect the claims and cited lines below.':'Evidence extracted. Run the local AI or import a review.');}
  catch(e){setBusy(false,'The request could not be completed. Your input is preserved.');error(e.message);}
}
$('analyze').onclick=()=>run('/api/analyze','Extracting changed-line evidence…');
$('review').onclick=()=>run('/api/review','Local model reviewing your diff…');
$('validate').onclick=()=>run('/api/validate','Validating imported references…');
$('example').onclick=async()=>{try{const r=await api('/api/example');$('diff').value=r.diff;$('example-note').textContent='Synthetic example loaded. A review run still uses the real local model.';await run('/api/analyze','Extracting the synthetic example…');}catch(e){error(e.message);}};
function changed() {state=null;$('download').disabled=true;$('claims').replaceChildren();$('evidence').replaceChildren();['stats','provenance','validation','all-evidence'].forEach(id=>$(id).hidden=true);$('empty').hidden=false;$('status').textContent='Input changed. Extract evidence or run a new review.';}
$('diff').addEventListener('input',()=>{changed();$('example-note').textContent='';});
for(const [file,target] of [['diff-file','diff'],['review-file','import-json']])$(file).onchange=async()=>{const f=$(file).files[0];if(!f)return;if(f.size>524288){error('File exceeds the 512 KB upload limit.');return;}$(target).value=await f.text();if(target==='diff'){changed();$('example-note').textContent='Loaded '+f.name;} };
$('download').onclick=()=>{if(!state)return;const blob=new Blob([JSON.stringify(state,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='evidencedesk-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
api('/api/status').then(r=>{ready=r.available;$('runtime').textContent=ready?'Available':'Inference unavailable';$('model').replaceChildren(...r.models.map(m=>{const o=document.createElement('option');o.value=m.name;o.textContent=m.name;return o;}));if(r.models.some(m=>m.name==='qwen3.6:35b'))$('model').value='qwen3.6:35b';if(!ready)$('model').append(text('option','No installed local model available'));$('model').disabled=!ready;$('review').disabled=!ready;}).catch(()=>{$('runtime').textContent='Inference unavailable';});
