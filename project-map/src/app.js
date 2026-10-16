'use strict';
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
const escapeHTML = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const PATHS = {
  layers:'m12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5M3 16l9 5 9-5',
  grid:'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
  compass:'m16 8-3 5-5 3 3-5 5-3ZM12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Z',
  search:'M21 21l-5-5M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14Z',
  wave:'M2 12h3l3-8 4 16 4-13 3 5h3',
  film:'M3 4h18v16H3zM7 4v16M17 4v16M3 9h4M3 15h4M17 9h4M17 15h4',
  clock:'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 3v6l4 2',
  folder:'M3 6V4h6l2 3h10v13H3V6Z',
  menu:'M3 6h18M3 12h18M3 18h18',
  download:'M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5',
  code:'m8 6-6 6 6 6m8-12 6 6-6 6m-3-14-2 16',
  terminal:'M3 4h18v16H3zM6 8l4 4-4 4m7 0h5',
  cube:'m12 2 10 5v10l-10 5L2 17V7l10-5Zm0 10 10-5M12 12 2 7m10 5v10',
  flow:'M3 3h7v6H3zM14 15h7v6h-7zM6 9v9h8M10 6h8v9',
  chart:'M3 3v18h18M7 17v-5m5 5V7m5 10V3',
  globe:'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm0 0c-6 6-6 14 0 20m0-20c6 6 6 14 0 20M2 12h20',
  type:'M4 4h16M12 4v16M8 20h8',
  image:'M3 3h18v18H3zM3 16l5-5 5 5 4-4 4 4M16 6h1v1h-1z',
  audio:'M3 9h4l5-5v16l-5-5H3V9Zm13-2c4 3 4 7 0 10m3-13c6 4 6 12 0 16',
  move:'M12 2v20M2 12h20m-23-3 3 3-3 3m18-6 3 3-3 3M9 5l3-3 3 3M9 19l3 3 3-3',
  mask:'M3 3h18v18H3zM3 21 21 3M8 3l-5 5m0 7L15 3',
  browser:'M2 3h20v18H2zM2 8h20M5 5h1m2 0h1m2 0h1',
  window:'M3 3h18v18H3zM3 8h18M8 8v13',
  chess:'M7 21h10M8 18h8l-1-9h-6l-1 9ZM8 9h8V5h-3V2h-2v3H8v4Z',
  palette:'M12 3C0 3 0 21 11 21c4 0 1-5 4-5h3C26 16 21 3 12 3ZM7 9h.1m5-3h.1m5 4h.1M7 15h.1',
  gradient:'M3 3h18v18H3zM7 3v18M12 3v18M17 3v18',
  blocks:'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zm11 0h7v7h-7z',
  recipe:'M6 2h12v20l-6-3-6 3V2Zm3 5h6M9 11h6',
  spark:'m12 2 3 7 7 3-7 3-3 7-3-7-7-3 7-3 3-7Z',
  book:'M12 5C9 2 4 3 2 4v16c3-1 7-1 10 1m0-16c3-3 8-2 10-1v16c-3-1-7-1-10 1V5Z',
  check:'m5 12 4 4L19 6'
};
const icon = (name, cls = '') => `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${PATHS[name] || PATHS.layers}"/></svg>`;
const sourceURL = path => '../' + path.split('/').map(encodeURIComponent).join('/');
const sourceLink = (path, label = 'Read guide') => `<a class="source-link" href="${sourceURL(path)}" target="_blank" rel="noopener">${escapeHTML(label)}</a>`;
const apiTags = names => `<div class="api-list">${names.map(x => `<span class="api-tag">${escapeHTML(x)}</span>`).join('')}</div>`;
const featureById = id => FEATURES.find(f => f.id === id);
const prettyDate = day => new Date(day + 'T12:00:00').toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'});
const intro = (kicker, title, description, stamp = '') => `<div class="intro"><div><div class="eyebrow">${kicker}</div><h1>${title}</h1><p>${description}</p></div>${stamp ? `<div class="intro-stamp">${stamp}</div>` : ''}</div>`;
const sectionHead = (title, subtitle = '', link = '') => `<div class="section-head"><div><h2>${title}</h2>${subtitle ? `<p>${subtitle}</p>` : ''}</div>${link}</div>`;
const pill = (text, cls = '') => `<span class="pill ${cls}">${escapeHTML(text)}</span>`;
const openFeature = id => {
  const f = featureById(id);
  if (!f) return;
  $('#detail-content').innerHTML = `<div class="detail-top"><span>${escapeHTML(f.group)} / ${escapeHTML(f.layer)}</span><button type="button" class="dialog-close" data-close="detail-dialog" aria-label="Close feature details">Close ×</button></div><div class="detail-body"><div class="feature-icon">${icon(f.icon)}</div><h2 id="detail-title">${escapeHTML(f.name)}</h2><div class="detail-tagline">${escapeHTML(f.tagline)}</div><p>${escapeHTML(f.description)}</p><h4>What you’ve built</h4><ul>${f.items.map(x => `<li>${escapeHTML(x)}</li>`).join('')}</ul><h4>Public API entrypoints</h4>${apiTags(f.apis)}${f.limit ? `<div class="callout">${escapeHTML(f.limit)}</div>` : ''}<div class="detail-links">${sourceLink(f.docs,'Open the documentation')}${sourceLink(f.source, 'Inspect the implementation')}<span class="source-path">${escapeHTML(f.source)}</span></div></div>`;
  if (!$('#detail-dialog').open) $('#detail-dialog').showModal();
  $('#detail-dialog').scrollTop = 0;
};

function overview() {
  const count = SNAPSHOT.packages[0].exports.length;
  return intro('Your project, connected', 'Everything you’ve built.<br><em>One connected system.</em>', 'A source-grounded map of Faceless Champ: the Python video engine, the authoring framework, and the production tools around them.', '<strong>PROJECT SNAPSHOT</strong>' + prettyDate(SNAPSHOT.date)) +
  `<div class="stat-grid">${[
    ['Independent packages','3','core · kit · agent','layers'],
    ['Core root exports',count,'public names','code'],
    ['Project starters',SNAPSHOT.templates.length,`${SNAPSHOT.recipes.length} recipes`,'blocks'],
    ['Training projects',SNAPSHOT.projects.length,'authored examples','film']
  ].map(([label,value,small,i]) => `<div class="stat"><div class="stat-top"><span>${label}</span>${icon(i)}</div><div class="stat-value">${value}<small>${small}</small></div></div>`).join('')}</div>` +
  sectionHead('The ecosystem at a glance', 'Three layers. One underlying rendering engine.', '<a class="text-button" href="#architecture">Explore architecture</a>') +
  `<div class="canvas"><div class="canvas-top"><span class="canvas-label">FACELESS CHAMP / SYSTEM MAP</span><div class="canvas-legend"><span><i class="legend-dot" style="background:var(--green)"></i>Plan</span><span><i class="legend-dot" style="background:var(--blue)"></i>Compose</span><span><i class="legend-dot" style="background:var(--orange)"></i>Render</span></div></div><div class="eco-canvas"><div class="flow-caption">Your video project / external AI author → public Python APIs</div><div class="package-flow">${[
    ['agent','AGENT WORKFLOW','Agent',SNAPSHOT.packages[2].version,'Plan, discover capabilities, review and track production evidence.','facelesschamp-agent / fc-agent'],
    ['kit','AUTHORING FRAMEWORK','Kit',SNAPSHOT.packages[1].version,'Arrange segments, blocks, assets, themes and explanation recipes.','facelesschamp-kit / fc-kit'],
    ['scenes','RENDERING ENGINE','Core',SNAPSHOT.packages[0].version,'Evaluate time, draw components, compose frames and export video.','faceless-champ / Python API']
  ].map(([id,tag,name,ver,body,code],i) => `${i ? '<div class="connector" aria-hidden="true">→</div>' : ''}<button class="package-node ${name.toLowerCase()}" data-feature="${id}"><div class="node-header"><span>${tag}</span><span>v${ver}</span></div><div class="node-name">Faceless<span>Champ</span> ${name}</div><p>${body}</p><span class="node-code">${code} ↗</span></button>`).join('')}</div><div class="domain-label">Visual systems powered by the core</div><div class="domain-grid">${['typography','charts','maps','coding','playground','flow','arch','web','os','chess'].map(id => {const f=featureById(id);return `<button class="domain-chip" data-feature="${id}">${icon(f.icon)}${({typography:'Text & equations',charts:'Charts',maps:'Maps & flags',coding:'CodingChamp',playground:'Playgrounds',flow:'FlowChamp',arch:'ArchChamp',web:'HTML capture',os:'Virtual OS',chess:'ChessChamp'})[id]}</button>`;}).join('')}</div></div><div class="canvas-bottom"><span><strong>Output pipeline</strong> &nbsp; Timeline → Pillow / VTK viewport → FFmpeg → MP4</span><span>Click any module to look inside ↗</span></div></div>` +
  `<div class="overview-bottom"><div class="recent-panel"><div class="mini-heading">${icon('clock')}LATEST DEVELOPMENTS</div>${[
    ['gradients','Gradient surfaces & shadows','Oct 16 · Premium effects, Phase 2A'],
    ['spring','Analytical Spring motion','Oct 15 · Transform safety and deterministic seeking'],
    ['clean-flow','Clean-flow across the ecosystem','Oct 15 · Themes, diagrams and coding workspaces']
  ].map(([id,name,desc]) => `<button class="recent-item" data-feature="${id}"><span class="recent-symbol">${icon(featureById(id).icon)}</span><span><strong>${name}</strong><small>${desc}</small></span><span>↗</span></button>`).join('')}</div><div class="insight-panel"><div class="mini-heading">${icon('compass')}THE LARGER PICTURE</div><h3>You’ve built an authoring ecosystem around a deterministic video engine.</h3><p>Core owns pixels and time. Kit turns them into reusable video structures. Agent makes those structures discoverable, plan-driven and reviewable.</p><div class="insight-chips">${pill('Python-first')}${pill('Reusable public APIs')}${pill('Local authoring')}</div></div></div>` +
  `<div class="verification-strip"><span class="feature-icon">${icon('check')}</span><div><h3>Recorded verification, with a clear scope</h3><p>The latest Phase 2A report records 1,645 tests passed, 2 skipped, and four short exports fully decoded. These are recorded results, not tests rerun by this atlas. ${sourceLink('docs/premium-effects-verification.md','Read the evidence')}</p></div></div>`;
}

function architecture() {
  const layers = [
    ['01','Project / external author','Your content and decisions','training project/','Story, research, supplied audio, source cues, custom scene content and artwork choices belong to the project. Authors can use the core directly or build through Kit and Agent.',['render.py','videos/main.py','agent-plan.json','facelesschamp.toml']],
    ['02','Agent','Plan, discover and review','facelesschamp-agent/','Structured plans, a capability registry, portable authoring instructions and evidence fingerprints support an external AI author. CLI outputs are structured JSON. The package delegates authoring to Kit.',['VideoPlan','AgentProject','fc-agent','ReviewSubmission']],
    ['03','Kit','Compose reusable videos','facelesschamp-kit/','Configuration, assets, themes, blocks, recipes and segment windows compile to a complete master Scene using public core methods. The framework has no second frame evaluator.',['Video','Segment','BuildContext','BlockBuild','CompiledVideo']],
    ['04','Core','Own timing and rendering','src/faceless_champ/','Components describe visuals. Scene snapshots and property tracks describe change. The renderer samples arbitrary times, rasterizes/composites frames, and hands them to the exporter.',['Scene','Animation','Spring','Group','PillowRenderer','render']]
  ];
  return intro('Architecture', 'A clear place<br><em>for every responsibility.</em>', 'Dependency direction follows project → agent → kit → core. Direct core and kit authoring remain available; higher layers reuse the engine’s public contracts.') +
    `<div class="architecture-rows">${layers.map(([n,name,role,path,desc,apis])=>`<div class="architecture-row"><span class="layer-num">${n}</span><div><h3>${name}</h3><div class="pill">${role}</div><div class="layer-path" style="margin-top:10px">${path}</div></div><div><p class="layer-description">${desc}</p>${apiTags(apis)}</div></div>`).join('')}</div>` +
    sectionHead('From authored intent to encoded video','The core evaluation and export path.') +
    `<div class="pipeline">${[['Describe','Components, content and static design-pixel properties.'],['Record','Snapshots, lifetimes and property animation tracks.'],['Evaluate','Sample the state at an arbitrary source time.'],['Rasterize','Pillow composition plus native VTK for ArchChamp.'],['Encode','Stream frames and mix audio with FFmpeg.']].map(([name,desc],i)=>`<div class="pipeline-step"><small>0${i+1}</small><h4>${name}</h4><p>${desc}</p></div>`).join('')}</div>` +
    `<div class="two-col"><div class="note-panel"><h3>Preparation is an explicit phase</h3><p>Code checkpoints execute during preparation. HTML interactions run during capture. Prepared outputs and source fingerprints then become replayable inputs.</p><ul><li>Prepare complete code checkpoints and web captures.</li><li>Build and validate from stored results.</li><li>Sample, preview and render without rerunning the lesson.</li></ul>${sourceLink('docs/coding-playgrounds.md','Preparation contract')}</div><div class="note-panel"><h3>One deterministic timeline</h3><p>Scene state is sampled by time, without advancing a frame-step simulation. Nested composition maps global time to child time. Spring and specialist scripts follow the same seekable authoring principle.</p><ul><li>Order-independent frame sampling.</li><li>Source-time ranged previews and cue timing.</li><li>Validation before publishing a completed schedule.</li></ul>${sourceLink('docs/architecture.md','Core renderer contract')}</div></div>` +
    sectionHead('Current boundaries','Implemented scope and reserved future work.') +
    `<div class="boundary-grid"><div class="boundary-card"><h3>Core export</h3><p>Pillow is the default 2D rasterizer; FFmpeg exports video. General scene-camera animation, imported video clips and a GPU video renderer remain future work. ArchChamp’s own 3D camera is implemented.</p></div><div class="boundary-card"><h3>Premium effects</h3><p>Phase 2A delivers static gradient paint and shadows baked into Images. Runtime effect stacks, glow/blur, glass and effect animation are future design reservations.</p></div><div class="boundary-card"><h3>External AI authoring</h3><p>The agent package supplies planning, discovery and evidence tools. The external agent writes Python and inspects results. Built-in model runners, TTS and automatic artwork/research are outside v1.</p></div></div>`;
}

let featureGroup='All', featureQuery='', projectCategory='All';
function featureCards() {
  const query=featureQuery.trim().toLowerCase();
  const rows=FEATURES.filter(f=>(featureGroup==='All'||f.group===featureGroup)&&[f.name,f.description,f.layer,...f.apis,...f.items].join(' ').toLowerCase().includes(query));
  return rows.map(f=>`<button class="feature-card" data-group="${f.group}" data-feature="${f.id}"><div class="card-top"><span class="feature-icon">${icon(f.icon)}</span>${f.fresh ? pill('Recent','orange') : pill(f.group)}</div><h3>${f.name}</h3><p>${f.tagline}</p><div class="card-foot"><span>${f.layer}</span><span>↗</span></div></button>`).join('') || '<div class="empty-state"><strong>No features match this view.</strong>Try a different category or search term.</div>';
}
function features() {
  return intro('Capability inventory', 'Your feature atlas.<br><em>Explore what the system can do.</em>', 'Open a capability to see its behavior, public APIs, implementation path and documentation. The inventory covers the current source checkout.') +
    `<div class="toolbar"><div class="filter-group" aria-label="Feature category">${['All','Engine','Visual systems','Motion','Authoring','Production'].map(group=>`<button class="filter" data-feature-group="${group}" aria-pressed="${group===featureGroup}">${group}</button>`).join('')}</div><label class="local-search">${icon('search')}<span class="sr-only">Filter features</span><input id="feature-search" placeholder="Search APIs or features" value="${escapeHTML(featureQuery)}"></label><span class="filter-count" id="feature-result-count" role="status"></span></div><div class="feature-grid" id="feature-grid">${featureCards()}</div>`;
}
function updateFeatures() {
  $('#feature-grid').innerHTML=featureCards();
  $$('.filter[data-feature-group]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.featureGroup===featureGroup)));
  const count=$$('.feature-card').length;
  $('#feature-result-count').textContent=`${count} / ${FEATURES.length} capabilities`;
}

function projectArt(feature) {
  let content='';
  if (['coding','web'].includes(feature)) content=`<rect x="52" y="23" width="256" height="102" rx="6" fill="#293122"/><path d="M52 42h256" stroke="#46513a"/><circle cx="65" cy="33" r="2" fill="#d58053"/><circle cx="73" cy="33" r="2" fill="#c4b16a"/><circle cx="81" cy="33" r="2" fill="#8ba773"/><g stroke-width="3" stroke-linecap="round"><path d="M70 60h37m-37 16h67m-55 16h85m-97 16h45" stroke="#c1cfa8"/><path d="M116 60h71m-42 16h27m3 16h43m-96 16h31" stroke="#d88861"/></g>`;
  else if(feature==='arch') content=`<g fill="#f9fbf5" stroke="#78925c" stroke-width="1.4"><path d="m180 18 22 13v23l17 10v25l23 14v20l-62 17-62-17v-20l23-14V64l17-10V31l22-13Z"/><path d="m180 18 1 122M158 31l22 12 22-12m-61 33 39 16 39-16m-101 39 62 20 62-20M158 54l22 11 22-11M141 89l39 16 39-16"/></g><path d="M104 29v94m-4-94h8m-8 94h8" stroke="#d08758" stroke-width="1"/><text x="89" y="80" fill="#a18f67" font-size="8" transform="rotate(-90 89 80)">MODEL DIMENSION</text>`;
  else if(feature==='flow') content=`<g stroke="#a8b798" stroke-width="1.3" fill="none"><path d="M86 75h60m67 0h60M180 42v33m0 0v34"/></g><g fill="#fff" stroke="#d8e1cc"><rect x="32" y="56" width="70" height="38" rx="7"/><rect x="145" y="56" width="70" height="38" rx="7"/><rect x="258" y="56" width="70" height="38" rx="7"/><rect x="155" y="17" width="50" height="25" rx="5"/><rect x="155" y="109" width="50" height="25" rx="5"/></g><g fill="#93a57b" font-size="9" text-anchor="middle"><text x="67" y="79">Client</text><text x="180" y="79">Service</text><text x="293" y="79">Storage</text></g><circle cx="128" cy="75" r="4" fill="#df8154"/><circle cx="244" cy="75" r="4" fill="#df8154"/>`;
  else if(feature==='charts') content=`<path d="M56 22v104h252" stroke="#b2bfa2" fill="none"/><g fill="#e3a17c"><rect x="77" y="83" width="30" height="43" rx="3"/><rect x="128" y="62" width="30" height="64" rx="3"/><rect x="179" y="45" width="30" height="81" rx="3"/><rect x="230" y="25" width="30" height="101" rx="3"/></g><path d="m81 75 50-23 51-15 58-20" fill="none" stroke="#728c56" stroke-width="2"/><g fill="#728c56"><circle cx="81" cy="75" r="3"/><circle cx="131" cy="52" r="3"/><circle cx="182" cy="37" r="3"/><circle cx="240" cy="17" r="3"/></g>`;
  else if(feature==='typography') content=`<text x="180" y="72" fill="#698252" font-family="Georgia,serif" font-size="40" text-anchor="middle">E = mc²</text><path d="M70 105q50-50 100-8t120-33" fill="none" stroke="#d58f66" stroke-width="2"/><path d="M70 126V90m0 36h220" fill="none" stroke="#bdcaae"/>`;
  else if(feature==='clean-flow') content=`<rect x="67" y="28" width="104" height="95" rx="10" fill="#d8dfce"/><rect x="64" y="23" width="104" height="95" rx="10" fill="#fff"/><rect x="196" y="48" width="104" height="64" rx="9" fill="#d8dfce"/><rect x="193" y="43" width="104" height="64" rx="9" fill="#fff"/><rect x="80" y="39" width="51" height="7" rx="3" fill="#a2b78d"/><rect x="80" y="55" width="70" height="4" rx="2" fill="#e6ebdf"/><circle cx="116" cy="88" r="16" fill="#e19369"/><path d="M169 70h23" stroke="#b0bda0"/><rect x="209" y="58" width="64" height="5" rx="2" fill="#b2c39e"/><rect x="209" y="73" width="40" height="17" rx="4" fill="#f5e1d3"/>`;
  else content=`<g fill="#fff" stroke="#dbe3cf"><rect x="45" y="36" width="75" height="75" rx="10"/><rect x="143" y="36" width="75" height="75" rx="10"/><rect x="241" y="36" width="75" height="75" rx="10"/></g><path d="M120 74h23m75 0h23" stroke="#afbe9c"/><circle cx="82" cy="74" r="16" fill="#a8bc90"/><path d="m169 62 22 12-22 12Z" fill="#da916a"/><path d="m267 74 8 8 15-17" stroke="#8eaa71" fill="none" stroke-width="3"/>`;
  return `<svg viewBox="0 0 360 150" aria-hidden="true">${content}</svg>`;
}
function projectCards() {
  const rows=SNAPSHOT.projects.filter(p=>projectCategory==='All'||PROJECT_INFO[p.id]?.category===projectCategory);
  return rows.map(p=>{
    const d=PROJECT_INFO[p.id]||{name:p.id,category:'Other',family:'Authored composition',duration:'Project',note:'Inspect the project README for current authoring details.',feature:'scenes'};
    return `<article class="project-card"><div class="project-art">${projectArt(d.feature)}</div><div class="project-body"><div class="project-meta"><span>${d.category}</span><span>${d.duration}</span></div><h3>${d.name}</h3><p>${d.note}</p><div class="project-family">${d.family}</div><div class="project-links"><a href="${sourceURL(p.readme)}" target="_blank" rel="noopener">Project notes ↗</a><button data-feature="${d.feature}">Related API</button>${p.renderer?`<a href="${sourceURL(p.renderer)}" target="_blank" rel="noopener">render.py ↗</a>`:''}</div></div></article>`;
  }).join('');
}
function projects() {
  return intro('Applied work', 'The ideas you’ve<br><em>already put into practice.</em>', 'Fifteen training projects exercise the reusable APIs through narrated explainers, data stories, coding lessons, system diagrams and technical geometry.') +
    `<div class="toolbar"><div class="filter-group" aria-label="Project category">${['All','Narrated explainers','Math & data','Code & interfaces','Systems & 3D','Design studies'].map(c=>`<button class="filter" data-project-category="${c}" aria-pressed="${c===projectCategory}">${c}</button>`).join('')}</div><span class="filter-count" id="project-result-count" role="status"></span></div><div class="project-grid" id="project-grid">${projectCards()}</div><p class="project-caveat">Durations and story descriptions come from the project notes. These are authored compositions; full-export verification varies by project. Illustrations above are atlas schematics, not screenshots of the rendered videos. Check each project’s verification record for media evidence.</p>` +
    sectionHead('Focused showcases beyond the training gallery','Reusable API demonstrations and tooling.') +
    `<div class="two-col"><div class="note-panel"><h3>Core API demonstrations</h3><p>Chart and map showcases, flags, groups, fitted text, coding workspaces, chess/PGN, OS tutorials, flow diagrams, technical 3D, motion graphics, Spring and premium surfaces.</p>${sourceLink('examples/','Explore examples/')}</div><div class="note-panel"><h3>The library’s own guide video</h3><p>A narrated authoring project demonstrates the broader library, including prepared CodingChamp scenes and source-clock visual timing. Its media evidence is recorded separately from the guide-site previews.</p>${sourceLink('guide video/README.md','Explore the guide video')}</div></div>`;
}

let motionType='spring', springVariant='bouncy', progress=0, playing=false, frameId=0;
function curveSVG() {
  const colors={gentle:'#8b9e79',critical:'#5d7f9d',bouncy:'#db7d51'};
  return `<svg viewBox="0 0 420 145" role="img" aria-label="Analytical Spring progress curves sampled from the current Python kernel"><path d="M30 10v112h375M30 35h375" stroke="#e0e7d6" stroke-width="1" fill="none"/><text x="10" y="39" font-size="8" fill="#99aa87">1</text><text x="10" y="125" font-size="8" fill="#99aa87">0</text><text x="376" y="140" font-size="8" fill="#99aa87">time →</text>${Object.entries(SNAPSHOT.curves).map(([k,v])=>`<path d="${v.filter((_,i)=>i%4===0).map((y,i)=>`${i?'L':'M'}${30+i/250*370},${122-y*87}`).join(' ')}" fill="none" stroke="${colors[k]}" stroke-width="1.7"/>`).join('')}</svg><div class="curve-legend">${Object.entries(colors).map(([label,color])=>`<span><i class="legend-dot" style="background:${color}"></i>${label}</span>`).join('')}</div>`;
}
function motion() {
  return intro('Motion lab', 'Make the movement<br><em>part of the explanation.</em>', 'Scrub or play a small motion study. The Spring study uses samples from your actual Python kernel; other studies illustrate the available animation vocabulary.') +
    `<div class="motion-layout"><div><div class="motion-stage"><div class="stage-header"><span id="stage-effect-label">Spring / bouncy</span>${pill('Interactive study')}</div><div class="stage-area"><div class="stage-track"></div><div class="stage-target"></div><div class="motion-object" id="motion-object">${icon('cube')}</div><div class="stage-badge">NORMALIZED TIMELINE · 0 → 1</div></div><div class="motion-controls"><div class="play-row"><button id="play-motion" class="play-button" aria-label="Play motion study">▶ Play</button><label class="sr-only" for="motion-scrub">Motion progress</label><input id="motion-scrub" type="range" min="0" max="1000" value="0"><output id="motion-time" class="time-label" for="motion-scrub">0.00</output></div><p class="lab-note">Seek any time. Replay the same result. The browser view is an explanation, not a Faceless Champ renderer.</p></div></div><div class="curve-panel"><div class="mini-heading">${icon('wave')}ACTUAL SPRING KERNEL SAMPLES</div>${curveSVG()}</div></div><div class="motion-settings"><h3>Explore the vocabulary</h3><label class="control-label" for="motion-type">Animation study</label><select id="motion-type">${[['spring','Analytical Spring'],['slide','Slide in'],['fade','Fade in'],['pop','Pop in'],['pulse','Pulse emphasis'],['rotate','Rotate / spin'],['wipe','Directional wipe'],['typewriter','Typewriter'],['stagger','Staggered sequence']].map(([id,name])=>`<option value="${id}" ${motionType===id?'selected':''}>${name}</option>`).join('')}</select><div id="spring-settings"><label class="control-label" for="spring-variant">Spring response</label><select id="spring-variant">${[['gentle','Gentle · overdamped (100, 25, 1)'],['critical','Critical (100, 20, 1)'],['bouncy','Bouncy · underdamped (100, 10, 1)']].map(([id,name])=>`<option value="${id}" ${springVariant===id?'selected':''}>${name}</option>`).join('')}</select></div><div id="motion-code" class="motion-code"></div><p class="lab-note">Spring labels here are example configurations, not named public presets. All three studies travel the same distance over 2.6 seconds.</p><button class="source-link" data-feature="spring">Inspect Spring’s API and limits ↗</button></div></div>` +
    sectionHead('The motion toolkit','Preset constructors and the scheduling primitives behind the studies.') +
    `<div class="motion-chip-list">${['FadeIn','FadeOut','Typewriter','Write','Draw','SlideIn','SlideOut','ZoomIn','ZoomOut','PopIn','PopOut','BounceIn','SpinIn','Pulse','Shake','Wiggle','ChartReveal','Stagger','Succession','Repeat','Wipe','Spring'].map(x=>`<button class="motion-chip" data-feature="${x==='Spring'?'spring':['Stagger','Succession','Repeat'].includes(x)?'scheduling':x==='Wipe'?'masks':'transforms'}">${x}</button>`).join('')}</div><div class="callout"><strong>One track model.</strong> Presets, keyframes, relative transforms, schedules and Spring all feed the existing property timeline. A conventional fade can run alongside a Spring transform on the same object.</div>`;
}
const smooth = t => t*t*(3-2*t);
function motionState() {
  const target=$('#motion-object');if(!target)return;
  const t=progress;
  target.className='motion-object';target.style.cssText='';target.innerHTML=icon('cube');
  const width=$('.stage-area').clientWidth*.30;
  let x=0,scale=1,rotation=0,opacity=1;
  if(motionType==='spring')x=SNAPSHOT.curves[springVariant][Math.round(t*1000)]*width;
  if(motionType==='slide'){x=width*smooth(t);opacity=t;}
  if(motionType==='fade'){x=width/2;opacity=t;}
  if(motionType==='pop'){x=width/2;scale=t<.7?.45+(1.14-.45)*smooth(t/.7):1.14-.14*smooth((t-.7)/.3);opacity=Math.min(1,t*3);}
  if(motionType==='pulse'){x=width/2;scale=1+.18*Math.sin(t*Math.PI*4);}
  if(motionType==='rotate'){x=width*smooth(t);rotation=-60*(1-smooth(t));scale=.7+.3*smooth(t);}
  if(motionType==='wipe'){x=width/2;target.style.clipPath=`inset(0 ${(1-t)*100}% 0 0)`;}
  if(motionType==='typewriter'){target.classList.add('type-demo');target.textContent='def build_a_bigger_picture():'.slice(0,Math.floor(t*28));}
  if(motionType==='stagger'){target.style.background='transparent';target.style.boxShadow='none';target.style.width='170px';target.style.left='calc(50% - 85px)';target.innerHTML=[0,1,2].map(i=>{const u=Math.max(0,Math.min(1,(t-i*.2)/.6));return `<span style="position:absolute;left:${i*58}px;width:44px;height:44px;background:#e1946c;border-radius:10px;opacity:${u};transform:translateY(${(1-smooth(u))*30}px)"></span>`;}).join('');}
  target.style.transform=`translateX(${x}px) scale(${scale}) rotate(${rotation}deg)`;target.style.opacity=opacity;
  $('#motion-time').textContent=t.toFixed(2);$('#motion-scrub').value=String(Math.round(t*1000));
  $('#stage-effect-label').textContent=motionType==='spring'?`Spring / ${springVariant}`:motionType.charAt(0).toUpperCase()+motionType.slice(1);
  $('#spring-settings').hidden=motionType!=='spring';
  const damping={gentle:25,critical:20,bouncy:10}[springVariant];
  const code=motionType==='spring'?`scene.play(\n    card.animate.move_to(640, 300),\n    run_time=2.6,\n    rate_func=Spring(\n        stiffness=100, damping=${damping}, mass=1\n    ),\n)`:({slide:'scene.play(SlideIn(card), run_time=2.6)',fade:'scene.play(FadeIn(card), run_time=2.6)',pop:'scene.play(PopIn(card), run_time=2.6)',pulse:'scene.play(Pulse(card), run_time=2.6)',rotate:'scene.play(SpinIn(card), run_time=2.6)',wipe:'scene.play(Wipe(card), run_time=2.6)',typewriter:'scene.play(Typewriter(title), run_time=2.6)',stagger:'scene.play(\n    Stagger(FadeIn(a), FadeIn(b), FadeIn(c))\n)'})[motionType];
  $('#motion-code').textContent=code;
}
function stopMotion(){playing=false;cancelAnimationFrame(frameId);if($('#play-motion')){$('#play-motion').textContent='▶ Play';$('#play-motion').setAttribute('aria-label','Play motion study');}}
function playMotion(){if(playing){stopMotion();return;}if(progress>=1)progress=0;playing=true;$('#play-motion').textContent='Ⅱ Pause';$('#play-motion').setAttribute('aria-label','Pause motion study');const start=performance.now()-progress*2600;const tick=now=>{progress=Math.min(1,(now-start)/2600);motionState();if(progress<1&&playing)frameId=requestAnimationFrame(tick);else stopMotion();};frameId=requestAnimationFrame(tick);}

function timeline() {
  const total=SNAPSHOT.history.length;
  return intro('Development history', 'From an engine<br><em>to an ecosystem.</em>', `Major developments across the current Git history, from October 3 to October 16, 2026. Each milestone points to implemented capabilities; the ${total}-commit source log is included below.`) +
    `<div class="timeline">${MILESTONES.map(m=>{const d=new Date(m.date+'T12:00:00');return `<div class="timeline-row"><div class="timeline-date">OCTOBER<strong>${d.getDate().toString().padStart(2,'0')}</strong>2026</div><article class="timeline-event"><h3>${m.title}</h3><p>${m.body}</p><div class="timeline-tags">${m.ids.map(id=>`<button data-feature="${id}">${featureById(id).name} ↗</button>`).join('')}<code class="commit-tag">${m.commit}</code></div></article></div>`;}).join('')}</div><details class="history-details"><summary>Inspect the complete captured Git log · ${total} commits</summary><div>${SNAPSHOT.history.map(h=>`<div class="history-record"><span>${h.date}</span><code>${h.sha}</code><span>${escapeHTML(h.subject)}</span></div>`).join('')}</div></details><p class="project-caveat">Milestone dates follow local Git commit dates. They describe development in this checkout and do not imply a package-index release or public deployment.</p>`;
}
function repository() {
  return intro('Repository map', 'Know where<br><em>each part belongs.</em>', 'Source ownership, supporting resources and the three package manifests. Expand a directory to see what it contains and why it exists.') +
    `<div class="repo-table">${REPOSITORY.map((r,i)=>`<details class="repo-row" ${i===0?'open':''}><summary>${icon(i<3?'folder':'layers')}<code>${r.path}</code><span>${r.role}</span></summary><div class="repo-detail"><p>${r.detail}</p>${(r.path==='training project/'?SNAPSHOT.projects.map(p=>p.id+'/'):r.children).map(c=>`<div class="repo-child">${escapeHTML(c)}</div>`).join('')}</div></details>`).join('')}</div>` +
    sectionHead('Three independent Python packages','Versions and dependencies read directly from pyproject.toml.') +
    `<div class="manifest-grid">${SNAPSHOT.packages.map(p=>`<article class="manifest"><h3>${p.name}</h3><span class="version">${p.version}</span><p>${p.label}<br>${p.modules} implementation modules · ${p.tests} test modules</p><ul>${p.dependencies.map(d=>`<li>${escapeHTML(d)}</li>`).join('')}</ul>${sourceLink((p.name==='faceless-champ'?'':p.name+'/')+'pyproject.toml','Package manifest')}</article>`).join('')}</div>` +
    `<div class="callout"><strong>Count definitions.</strong> Root exports count names listed in core __all__, including helpers and classes; web/OS submodule names are separate. Implementation modules exclude bundled resource and sample-asset copies. Test-module counts are file counts, not collected or passing test totals.</div>` +
    sectionHead('Registered project starters',`${SNAPSHOT.templates.length} editable starting points from the kit scaffold.`) +
    `<div class="catalog-list">${SNAPSHOT.templates.map(t=>`<div class="catalog-item"><code>${t}</code></div>`).join('')}</div>` +
    sectionHead('Explanation recipes',`${SNAPSHOT.recipes.length} structured patterns from the current recipe catalog.`) +
    `<div class="catalog-list">${SNAPSHOT.recipes.map(r=>`<div class="catalog-item" id="recipe-${r.id}"><code>${r.id}</code><p>${r.purpose}</p></div>`).join('')}</div>` +
    sectionHead('Keep the map current','The page is a portable snapshot with no server or external runtime dependency.') +
    `<div class="note-panel"><h3>Refresh from the repository root</h3><div class="motion-code">python3 project-map/build.py</div><p style="margin-top:14px">This refreshes versions, public export names, module counts, starters, recipes, training-project inventory, Git history and actual Spring samples. Narrative descriptions and milestone summaries are curated in project-map/src/catalog.js and should be reviewed when capabilities change.</p>${sourceLink('project-map/README.md','Usage and refresh notes')}</div>`;
}

const VIEWS={overview:{title:'Overview',render:overview},architecture:{title:'Architecture',render:architecture},features:{title:'Feature atlas',render:features},motion:{title:'Motion lab',render:motion},projects:{title:'Project gallery',render:projects},timeline:{title:'Development timeline',render:timeline},repository:{title:'Repository map',render:repository}};
let currentView='overview';
function renderView(){
  stopMotion();const hash=location.hash.slice(1).split('/')[0];currentView=VIEWS[hash]?hash:'overview';
  $('#main').innerHTML=VIEWS[currentView].render();$('#breadcrumb').textContent=VIEWS[currentView].title;
  document.title=`${VIEWS[currentView].title} — Faceless Champ Project Atlas`;
  $$('[data-view]').forEach(a=>{if(a.dataset.view===currentView)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  $('#sidebar').classList.remove('open');$('#menu-toggle').setAttribute('aria-expanded','false');$('#menu-toggle').setAttribute('aria-label','Open navigation');
  if(currentView==='features')updateFeatures();
  if(currentView==='projects')$('#project-result-count').textContent=`${$$('.project-card').length} projects`;
  if(currentView==='motion'){progress=0;motionState();}
  window.scrollTo(0,0);
}
const SEARCH_RECORDS=[...FEATURES.map(f=>({title:f.name,sub:f.tagline,type:'Feature',icon:f.icon,id:f.id,keywords:[f.description,f.group,f.layer,...f.apis,...f.items].join(' ')})),...SNAPSHOT.projects.map(p=>({title:PROJECT_INFO[p.id]?.name||p.id,sub:PROJECT_INFO[p.id]?.family||'Training project',type:'Project',icon:'film',project:p,keywords:p.id+' '+(PROJECT_INFO[p.id]?.note||'')})),...SNAPSHOT.recipes.map(r=>({title:r.id,sub:r.purpose,type:'Recipe',icon:'recipe',recipe:r.id,keywords:r.purpose}))];
let searchMatches=[];
function search(query=''){
  const q=query.toLowerCase().trim();searchMatches=SEARCH_RECORDS.filter(r=>[r.title,r.sub,r.keywords].join(' ').toLowerCase().includes(q)).slice(0,25);
  $('#search-results').innerHTML=searchMatches.length?searchMatches.map((r,i)=>`<button class="search-result" role="listitem" data-search-result="${i}">${icon(r.icon)}<span><strong>${escapeHTML(r.title)}</strong><small>${escapeHTML(r.sub)}</small></span><span class="result-type">${r.type}</span></button>`).join(''):'<div class="search-empty">No matches. Try “Spring”, “code”, “3D” or “narration”.</div>';
}
function openSearch(){search('');$('#global-search').value='';if(!$('#search-dialog').open)$('#search-dialog').showModal();$('#global-search').focus();}
function selectSearch(index){const r=searchMatches[index];if(!r)return;$('#search-dialog').close();if(r.type==='Feature')openFeature(r.id);else if(r.type==='Project'){projectCategory='All';location.hash='projects';if(currentView==='projects')renderView();requestAnimationFrame(()=>{const cards=$$('.project-card');const i=SNAPSHOT.projects.findIndex(p=>p.id===r.project.id);cards[i]?.scrollIntoView({block:'center',behavior:'smooth'});cards[i]?.animate([{outline:'2px solid #dc6537'},{outline:'2px solid transparent'}],{duration:1800});});}else{location.hash='repository';if(currentView==='repository')renderView();requestAnimationFrame(()=>$('#recipe-'+r.recipe)?.scrollIntoView({block:'center',behavior:'smooth'}));}}

document.addEventListener('click',event=>{
  if(event.target.closest('.skip-link')){event.preventDefault();$('#main').focus();return;}
  const feature=event.target.closest('[data-feature]');if(feature){openFeature(feature.dataset.feature);return;}
  const close=event.target.closest('[data-close]');if(close){$('#'+close.dataset.close).close();return;}
  if(event.target.closest('[data-search]')){openSearch();return;}
  const group=event.target.closest('[data-feature-group]');if(group){featureGroup=group.dataset.featureGroup;updateFeatures();return;}
  const category=event.target.closest('[data-project-category]');if(category){projectCategory=category.dataset.projectCategory;$('#project-grid').innerHTML=projectCards();$$('[data-project-category]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.projectCategory===projectCategory)));$('#project-result-count').textContent=`${$$('.project-card').length} projects`;return;}
  const result=event.target.closest('[data-search-result]');if(result){selectSearch(Number(result.dataset.searchResult));return;}
  if(event.target.closest('#menu-toggle')){const open=$('#sidebar').classList.toggle('open');$('#menu-toggle').setAttribute('aria-expanded',String(open));$('#menu-toggle').setAttribute('aria-label',open?'Close navigation':'Open navigation');return;}
  if(event.target.closest('#print-button')){window.print();return;}
  if(event.target.closest('#play-motion'))playMotion();
  if($('#sidebar').classList.contains('open')&&!event.target.closest('#sidebar')){$('#sidebar').classList.remove('open');$('#menu-toggle').setAttribute('aria-expanded','false');$('#menu-toggle').setAttribute('aria-label','Open navigation');}
});
document.addEventListener('input',event=>{if(event.target.id==='feature-search'){featureQuery=event.target.value;updateFeatures();}if(event.target.id==='global-search')search(event.target.value);if(event.target.id==='motion-scrub'){stopMotion();progress=Number(event.target.value)/1000;motionState();}});
document.addEventListener('change',event=>{if(event.target.id==='motion-type'){stopMotion();motionType=event.target.value;progress=0;motionState();}if(event.target.id==='spring-variant'){stopMotion();springVariant=event.target.value;progress=0;motionState();}});
document.addEventListener('keydown',event=>{
  if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){event.preventDefault();openSearch();return;}
  if(event.key==='Escape'){$('#sidebar').classList.remove('open');$('#menu-toggle').setAttribute('aria-expanded','false');}
  if($('#search-dialog').open&&['ArrowDown','ArrowUp','Enter'].includes(event.key)){const rows=$$('.search-result');if(!rows.length)return;const i=rows.indexOf(document.activeElement);if(event.key==='ArrowDown'){event.preventDefault();rows[(i+1)%rows.length].focus();}if(event.key==='ArrowUp'){event.preventDefault();rows[i<=0?rows.length-1:i-1].focus();}if(event.key==='Enter'&&document.activeElement.id==='global-search'){event.preventDefault();selectSearch(0);}}
});
[$('#search-dialog'),$('#detail-dialog')].forEach(dialog=>dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}}));
$$('[data-icon]').forEach(el=>{el.innerHTML=icon(el.dataset.icon);});
$('#snapshot-date').textContent='Snapshot · '+prettyDate(SNAPSHOT.date);
$('#sidebar-date').textContent=prettyDate(SNAPSHOT.date)+' · '+SNAPSHOT.head;
$('#footer-source').textContent='Source '+SNAPSHOT.head+' · Offline HTML · '+SNAPSHOT.date;
$('#nav-feature-count').textContent=FEATURES.length;
$('#nav-project-count').textContent=SNAPSHOT.projects.length;
window.addEventListener('hashchange',renderView);
renderView();
