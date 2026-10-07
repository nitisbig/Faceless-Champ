'use strict';
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let lessons = [], current = null, observer = null, toastTimer;
const slug = s => s.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
const icons = {python:'Py',bash:'$_',toml:'{}',json:'{}',text:'↳'};
function highlight(source, language) {
  if (language !== 'python') return esc(source);
  const rx = /#[^\n]*|(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')|\b(?:from|import|class|def|self|for|in|with|as|return|lambda|if|else|True|False|None|and|or|not)\b|\b\d+(?:\.\d+)?\b/g;
  let result='', cursor=0;
  for (const m of source.matchAll(rx)) {
    result += esc(source.slice(cursor,m.index));
    const cls = m[0].startsWith('#') ? 'comment' : /^["']/.test(m[0]) ? 'string' : /^\d/.test(m[0]) ? 'number' : 'keyword';
    result += `<span class="tok-${cls}">${esc(m[0])}</span>`;
    cursor=m.index+m[0].length;
  }
  return result+esc(source.slice(cursor));
}
function blockHTML(block, i) {
  if(block.type==='note') return `<div class="note">${esc(block.text)}</div>`;
  if(block.type==='table') return `<div class="table-wrap"><table><thead><tr>${block.headers.map(h=>`<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${block.rows.map(row=>`<tr>${row.map(v=>`<td>${esc(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  if(block.type==='code') return `<div class="code-block"><div class="code-head"><span class="code-icon">${icons[block.language]||'{}'}</span><span>${esc(block.filename||block.language)}</span>${block.filename?`<a href="examples/${encodeURIComponent(block.filename)}" download="${esc(block.filename)}">Download ↓</a>`:''}<button class="copy-button" data-copy="${i}" aria-label="Copy ${esc(block.filename||block.language)} code">▢ Copy</button></div><pre><code>${highlight(block.code,block.language)}</code></pre>${block.command?`<div class="example-run"><div class="run-label">${esc(block.placement||'Run from your scene directory')}</div><div class="run-command"><code>${esc(block.command)}</code><button class="copy-button" data-command="${i}" aria-label="Copy render command for ${esc(block.filename)}">▢ Copy</button></div></div>`:''}</div>`;
  return '';
}
function renderNav() {
  const groups = [...new Set(lessons.map(l=>l.group))];
  $('#chapter-nav').innerHTML=groups.map(group=>`<div class="nav-group"><h2>${esc(group)}</h2>${lessons.filter(l=>l.group===group).map(l=>`<a class="chapter-link" href="#${l.id}" data-chapter="${l.id}"><span class="nav-num">${String(lessons.indexOf(l)+1).padStart(2,'0')}</span>${esc(l.title)}</a>`).join('')}</div>`).join('');
  $('#chapter-count').textContent=`${lessons.length} chapters`;
}
function route() {
  const [rawId,rawSection] = location.hash.slice(1).split('/');
  if(rawId==='main') return;
  const lesson = lessons.find(l=>l.id===rawId) || lessons[0];
  if(rawId&&!lessons.some(l=>l.id===rawId)) history.replaceState(null,'',`#${lesson.id}`);
  if(current?.id!==lesson.id) render(lesson);
  if(rawSection) requestAnimationFrame(()=>document.getElementById(rawSection)?.scrollIntoView());
}
function render(lesson) {
  current=lesson;
  document.title=`${lesson.title} — Faceless Champ Guide`;
  const index=lessons.indexOf(lesson), blocks=[];
  const sections=lesson.sections.map(s=>`<section class="section"><h2 id="${slug(s.title)}">${esc(s.title)}<a class="heading-link" href="#${lesson.id}/${slug(s.title)}" aria-label="Link to ${esc(s.title)}">#</a></h2><p>${esc(s.text)}</p>${s.blocks.map(b=>{const i=blocks.push(b)-1;return blockHTML(b,i)}).join('')}</section>`).join('');
  const preview=lesson.preview?`<figure class="preview-box ${lesson.preview==='kit'?'portrait-preview':''}"><div class="preview-header"><span>OUTPUT PREVIEW</span><span>● Rendered with Faceless Champ</span></div><video controls playsinline preload="none" poster="assets/${lesson.preview}.png" aria-label="${esc(lesson.title)} rendered video preview"><source src="assets/${lesson.preview}.mp4" type="video/mp4"></video></figure><p class="preview-caption"><span>↳</span> Actual Python render · ${lesson.preview==='kit'?'Portrait framework example':'Landscape library example'}</p>`:'';
  $('#article').innerHTML=`<div class="breadcrumb"><a href="#hello-world">Guide</a><span>/</span><span>${esc(lesson.group)}</span></div><div class="eyebrow">${index===0?'YOUR FIRST VIDEO':esc(lesson.group.toUpperCase())}</div><h1>${esc(lesson.title)}</h1><p class="description">${esc(lesson.description)}</p><div class="lesson-meta"><span>CHAPTER ${String(index+1).padStart(2,'0')} / ${lessons.length}</span><span>${lesson.group==='The framework'?'FRAMEWORK':'PYTHON LIBRARY'}</span><span>${lesson.group==='The framework'?'v0.1.0rc1':'v0.1.0'}</span></div>${preview}${sections}<nav class="pagination" aria-label="Chapter navigation">${index>0?`<a class="page-link" href="#${lessons[index-1].id}"><small>← PREVIOUS CHAPTER</small><strong>${esc(lessons[index-1].title)}</strong></a>`:''}${index<lessons.length-1?`<a class="page-link next" href="#${lessons[index+1].id}"><small>NEXT CHAPTER →</small><strong>${esc(lessons[index+1].title)}</strong></a>`:''}</nav><footer class="article-footer"><span>Faceless Champ · Programmatic video, made with Python.</span><a href="https://github.com/nitisbig/Faceless-Champ" target="_blank" rel="noopener noreferrer">Explore the source ↗</a></footer>`;
  $('#toc').innerHTML=lesson.sections.map(s=>`<a href="#${lesson.id}/${slug(s.title)}">${esc(s.title)}</a>`).join('');
  document.querySelectorAll('.chapter-link').forEach(link=>{const active=link.dataset.chapter===lesson.id;link.classList.toggle('active',active);if(active)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current')});
  $('#article').querySelectorAll('[data-copy]').forEach(button=>button.addEventListener('click',()=>copyCode(blocks[Number(button.dataset.copy)].code,button)));
  $('#article').querySelectorAll('[data-command]').forEach(button=>button.addEventListener('click',()=>copyCode(blocks[Number(button.dataset.command)].command+'\n',button)));
  observer?.disconnect();
  observer=new IntersectionObserver(entries=>{const first=entries.filter(e=>e.isIntersecting).sort((a,b)=>a.boundingClientRect.top-b.boundingClientRect.top)[0];if(first)$('#toc').querySelectorAll('a').forEach(a=>a.classList.toggle('current',a.hash.endsWith('/'+first.target.id)))},{rootMargin:'-90px 0px -65% 0px'});
  document.querySelectorAll('.section h2').forEach(el=>observer.observe(el));
  window.scrollTo({top:0,behavior:'instant'});
  if($('#sidebar').classList.contains('open')) $('#main').focus({preventScroll:true});
  closeMobile();
  // Never autoplay media; users control each rendered example.
}
async function copyCode(code,button) {
  try {
    if(navigator.clipboard&&window.isSecureContext) await navigator.clipboard.writeText(code);
    else {const text=document.createElement('textarea');text.value=code;text.style.position='fixed';text.style.opacity='0';document.body.append(text);text.focus();text.select();const ok=document.execCommand('copy');text.remove();button.focus();if(!ok)throw new Error('Clipboard unavailable')}
    button.textContent='✓ Copied';showToast('Code copied to clipboard');setTimeout(()=>{if(button.isConnected)button.textContent='▢ Copy'},1800);
  } catch {showToast('Select the code and copy with Ctrl/Cmd+C. Clipboard access is unavailable.');}
}
function showToast(message){clearTimeout(toastTimer);$('#toast').textContent=message;$('#toast').classList.add('show');toastTimer=setTimeout(()=>$('#toast').classList.remove('show'),3000)}
function closeMobile(){$('#sidebar').classList.remove('open');$('#mobile-backdrop').hidden=true;$('#menu-toggle').setAttribute('aria-expanded','false');$('#menu-toggle').setAttribute('aria-label','Open chapters')}
$('#menu-toggle').addEventListener('click',()=>{const open=!$('#sidebar').classList.contains('open');$('#sidebar').classList.toggle('open',open);$('#mobile-backdrop').hidden=!open;$('#menu-toggle').setAttribute('aria-expanded',String(open));$('#menu-toggle').setAttribute('aria-label',open?'Close chapters':'Open chapters')});
$('#mobile-backdrop').addEventListener('click',closeMobile);
function applyTheme(value){document.documentElement.dataset.theme=value;$('#theme-toggle').setAttribute('aria-label',`Switch to ${value==='dark'?'light':'dark'} theme`)}
let savedTheme;try{savedTheme=localStorage.getItem('fc-guide-theme')}catch{}
applyTheme(savedTheme==='dark'?'dark':'light');
$('#theme-toggle').addEventListener('click',()=>{const value=document.documentElement.dataset.theme==='dark'?'light':'dark';applyTheme(value);try{localStorage.setItem('fc-guide-theme',value)}catch{}});
function search(){const query=$('#search-input').value.trim().toLowerCase();const found=lessons.map(l=>{const searchable=[l.title,l.description,...l.sections.flatMap(s=>[s.title,s.text,...s.blocks.map(b=>b.code||b.text||JSON.stringify(b.rows||[]))])].join(' ').toLowerCase();return {l,score:!query?0:l.title.toLowerCase().includes(query)?3:searchable.includes(query)?1:-1}}).filter(x=>x.score>=0).sort((a,b)=>b.score-a.score);$('#search-results').innerHTML=found.length?found.map(({l})=>`<a role="listitem" class="search-result" href="#${l.id}"><small>${esc(l.group)}</small><strong>${esc(l.title)}</strong><p>${esc(l.description)}</p></a>`).join(''):'<p class="empty-search">No matching chapters. Try “timeline”, “mask”, or “kit”.</p>';$('#search-results').querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{$('#search-dialog').close();if(current?.id===a.hash.slice(1))window.scrollTo({top:0,behavior:'instant'})}))}
function openSearch(){closeMobile();$('#search-dialog').showModal();search();$('#search-input').focus()}
$('#open-search').addEventListener('click',openSearch);$('#search-input').addEventListener('input',search);
document.addEventListener('keydown',event=>{if((event.metaKey||event.ctrlKey)&&event.key.toLowerCase()==='k'){event.preventDefault();if(!$('#search-dialog').open)openSearch()}if(event.key==='Escape')closeMobile()});
$('#search-dialog').addEventListener('click',event=>{if(event.target===$('#search-dialog')){const r=$('#search-dialog').getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)$('#search-dialog').close()}});
window.addEventListener('hashchange',route);
fetch('content.json').then(response=>{if(!response.ok)throw new Error(`HTTP ${response.status}`);return response.json()}).then(data=>{lessons=data.lessons;renderNav();route()}).catch(error=>{$('#article').innerHTML=`<h1>The guide could not load</h1><p>Please reload this page or read the <a href="https://github.com/nitisbig/Faceless-Champ/tree/master/docs">repository documentation</a>.</p>`;console.error(error)});
