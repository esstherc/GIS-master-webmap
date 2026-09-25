// Run with a local HTTP server and Chrome started with --remote-debugging-port=9223.
const endpoint = 'http://127.0.0.1:9223/json/list';
let page;
for (let attempt = 0; attempt < 40; attempt++) {
  try {
    page = (await (await fetch(endpoint)).json()).find(target => target.type === 'page');
    if (page) break;
  } catch {}
  await new Promise(resolve => setTimeout(resolve, 250));
}
if (!page) throw new Error('No Chrome page available');

const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  ws.addEventListener('open', resolve, { once: true });
  ws.addEventListener('error', reject, { once: true });
});
let nextId = 0;
const pending = new Map();
ws.addEventListener('message', event => {
  const message = JSON.parse(event.data);
  if (pending.has(message.id)) {
    pending.get(message.id)(message);
    pending.delete(message.id);
  }
});

async function command(method, params) {
  const id = ++nextId;
  return new Promise(resolve => {
    pending.set(id, resolve);
    ws.send(JSON.stringify({ id, method, params }));
  });
}

async function evaluate(expression) {
  const response = await command('Runtime.evaluate', { expression, returnByValue: true });
  if (response.result?.exceptionDetails) throw new Error(response.result.exceptionDetails.exception?.description || 'Browser evaluation failed');
  return response.result?.result?.value;
}

try {
  let count;
  for (let attempt = 0; attempt < 50; attempt++) {
    try { count = await evaluate('allData.length'); } catch {}
    if (count === 174) break;
    await new Promise(resolve => setTimeout(resolve, 200));
  }
  if (count !== 174) throw new Error(`Expected 174 programs, got ${count}`);
  const cards = await evaluate("document.querySelectorAll('.result-card').length");
  if (cards !== 174) throw new Error(`Expected 174 results, got ${cards}`);

  const combined = await evaluate("document.getElementById('search-filter').value='Pennsylvania State University';document.getElementById('type-filter').value='research';document.getElementById('location-filter').value='online';applyFilters();[matchingPrograms.length,document.getElementById('visible-count').textContent]");
  if (combined[0] !== 0 || combined[1] !== '0') throw new Error(`Combined filter returned ${combined}`);
  const popupMatches = await evaluate("document.getElementById('location-filter').value='on-site';applyFilters();document.querySelector('.result-focus').click();document.querySelectorAll('.leaflet-popup .program-item').length");
  if (popupMatches !== 1) throw new Error(`Popup showed ${popupMatches} programs instead of the one match`);
  const chips = await evaluate("const before=document.querySelectorAll('.filter-chip').length;document.querySelector('[data-filter-id=\"location-filter\"]').click();const after=document.querySelectorAll('.filter-chip').length;const format=document.getElementById('location-filter').value;document.getElementById('clear-active-filters').click();[before,after,format,document.querySelectorAll('.filter-chip').length]");
  if (chips[0] !== 3 || chips[1] !== 2 || chips[2] !== '' || chips[3] !== 0) throw new Error(`Applied filter chips failed: ${chips}`);

  const saved = await evaluate("clearFilters();document.querySelector('.result-card .save-toggle').click();document.querySelector('.saved-card .note-toggle').click();const form=document.querySelector('.saved-card .note-form');form.querySelector('textarea').value='Interested in this program';form.requestSubmit();[savedPrograms.length,savedPrograms[0].note,document.getElementById('saved-count').textContent]");
  if (saved[0] !== 1 || saved[1] !== 'Interested in this program' || saved[2] !== '1') throw new Error(`Save or note failed: ${saved}`);

  const removed = await evaluate("document.querySelector('.saved-card .saved-remove').click();savedPrograms.length");
  if (removed !== 0) throw new Error('Remove failed');
  const popupOpen = await evaluate("document.querySelector('.result-card .result-focus').click();markers.some(marker=>marker.isPopupOpen())");
  if (!popupOpen) throw new Error('Result did not open a map popup');
  const legacy = await evaluate("savedPrograms=[{...allData[0],programId:'old_index_key',note:'Old note',type:'Wishlist + Note'}];reconcileSavedPrograms();const migrated=savedPrograms[0].programId===programKey(allData[0])&&savedPrograms[0].note==='Old note';savedPrograms=[];saveStoredPrograms();migrated");
  if (!legacy) throw new Error('Legacy saved programs did not migrate');
  const compare = await evaluate("(()=>{savedPrograms=allData.slice(0,5).map((program,index)=>({...program,programId:programKey(program),note:index===0?'Candidate A':''}));saveStoredPrograms();const boxes=document.querySelectorAll('.compare-select');boxes[0].click();boxes[1].click();document.getElementById('compare-open').click();return [document.getElementById('compareModal').hidden,document.querySelectorAll('.compare-table tbody tr').length,document.querySelectorAll('.compare-table thead th').length,document.getElementById('compare-content').textContent.includes('Candidate A'),document.querySelectorAll('.compare-table a[href]').length]})()");
  if (compare[0] || compare[1] !== 8 || compare[2] !== 3 || !compare[3] || compare[4] !== 2) throw new Error(`Comparison table failed: ${compare}`);
  const limit = await evaluate("(()=>{document.getElementById('compare-close').click();const boxes=document.querySelectorAll('.compare-select');boxes[2].click();boxes[3].click();const blocked=boxes[4].disabled;document.querySelector('.saved-card .saved-remove').click();const restored=!document.querySelectorAll('.compare-select')[3].disabled;savedPrograms=[];saveStoredPrograms();return [blocked,restored,compareSelection.size]})()");
  if (!limit[0] || !limit[1] || limit[2] !== 0) throw new Error(`Comparison selection limit failed: ${limit}`);
  await command('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  const mobileFilter = await evaluate("syncFilterPanel();const initial=document.getElementById('filter-controls').hidden;document.getElementById('mobile-filter-toggle').click();const open=!document.getElementById('filter-controls').hidden;document.getElementById('state-filter').value='CA';applyFilters();document.getElementById('mobile-filter-toggle').click();const closed=document.getElementById('filter-controls').hidden;document.querySelector('.filter-chip').click();[initial,open,closed,document.querySelectorAll('.filter-chip').length]");
  if (!mobileFilter[0] || !mobileFilter[1] || !mobileFilter[2] || mobileFilter[3] !== 0) throw new Error(`Mobile filter panel failed: ${mobileFilter}`);
  const mobileCompare = await evaluate("(()=>{savedPrograms=allData.slice(0,4).map(program=>({...program,programId:programKey(program)}));saveStoredPrograms();document.querySelectorAll('.compare-select').forEach(input=>input.click());document.getElementById('compare-open').click();const area=document.getElementById('compare-content');const result=[document.getElementById('compareModal').hidden,area.scrollWidth,area.clientWidth];document.getElementById('compare-close').click();savedPrograms=[];saveStoredPrograms();return result})()");
  if (mobileCompare[0] || mobileCompare[1] <= mobileCompare[2]) throw new Error(`Mobile comparison did not scroll sideways: ${mobileCompare}`);
  const widths = await evaluate('[innerWidth,document.documentElement.scrollWidth]');
  if (widths[1] > widths[0]) throw new Error(`Mobile horizontal overflow: ${widths}`);
  console.log('UI browser check OK: filters, chips, mobile panel, saved programs, 2–4 comparison, and mobile width');
} finally {
  ws.close();
}
