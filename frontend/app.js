const base = (window.API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
const $ = id => document.getElementById(id);
const fragment = new URLSearchParams(location.hash.slice(1));
const incomingKey = fragment.get('access');
if (incomingKey) {
  sessionStorage.setItem('siteAccessKey', incomingKey);
  history.replaceState(null, '', location.pathname + location.search);
}
const accessKey = sessionStorage.getItem('siteAccessKey');
document.querySelector('main').hidden = !accessKey;
$('access-gate').hidden = !!accessKey;
let activeId = null, rows = [], editingId = null;
async function request(path, options={}) {
  const response = await fetch(base + path, {...options, headers:{"Content-Type":"application/json","X-Access-Key":accessKey,...options.headers}});
  const body = await response.json().catch(()=>({}));
  if (!response.ok) throw new Error(body.detail || `HTTP ${response.status}`);
  return body;
}
const won = n => Number(n).toLocaleString("ko-KR") + "원";
function notice(message) {$('notice').textContent = message;}
function renderMessages(messages) {
  $('messages').replaceChildren();
  if (!messages.length) {$('messages').innerHTML='<div class="empty">최근 주가의 흐름이나 최고·최저 종가를 물어보세요.</div>';return;}
  for (const message of messages) {const el=document.createElement('div');el.className='bubble '+message.role;el.textContent=message.content;$('messages').append(el);}
  $('messages').scrollTop=$('messages').scrollHeight;
}
async function loadConversations() {
  const items=await request('/api/conversations');$('conversations').replaceChildren();
  for(const item of items){const row=document.createElement('div');row.className='conversation-row';const open=document.createElement('button');open.className='conversation'+(item.id===activeId?' active':'');open.textContent=item.title;open.onclick=async()=>{const detail=await request('/api/conversations/'+encodeURIComponent(item.id));activeId=item.id;renderMessages(detail.messages);loadConversations();};const del=document.createElement('button');del.className='delete';del.textContent='×';del.title='대화 삭제';del.onclick=async()=>{if(!confirm('이 대화를 삭제할까요?'))return;await request('/api/conversations/'+encodeURIComponent(item.id),{method:'DELETE'});if(activeId===item.id){activeId=null;renderMessages([]);}loadConversations();};row.append(open,del);$('conversations').append(row);}
}
async function loadData(){rows=await request('/api/data');$('data-rows').replaceChildren();for(const item of [...rows].reverse()){const tr=document.createElement('tr');const d=document.createElement('td');d.textContent=item.date;const v=document.createElement('td');v.textContent=won(item.value);const actions=document.createElement('td');const edit=document.createElement('button');edit.textContent='수정';edit.onclick=()=>{editingId=item.id;$('date').value=item.date;$('value').value=item.value;$('memo').value=item.memo;$('save-data').textContent='수정 저장';$('cancel-edit').hidden=false;};const del=document.createElement('button');del.textContent='삭제';del.onclick=async()=>{if(!confirm(item.date+' 데이터를 삭제할까요?'))return;try{await request('/api/data/'+encodeURIComponent(item.id),{method:'DELETE'});notice('삭제되었습니다.');await refresh();}catch(e){notice(e.message);}};actions.append(edit,del);tr.append(d,v,actions);$('data-rows').append(tr);}}
async function loadSummary(){const s=await request('/api/data/summary');const box=$('summary');box.replaceChildren();if(!s.count){box.textContent='등록된 데이터가 없습니다.';return;}const items=[['기간',s.period.start+' ~ '+s.period.end],['데이터',s.count+'거래일'],['최근 종가',won(s.metrics.latest)],['평균 종가',won(s.metrics.average)],['최고',won(s.metrics.max)+' ('+s.metrics.max_date+')'],['최저',won(s.metrics.min)+' ('+s.metrics.min_date+')'],['최근 추세',s.trend]];for(const [label,value] of items){const row=document.createElement('div');row.className='metric';const a=document.createElement('span');a.textContent=label;const b=document.createElement('strong');b.textContent=value;row.append(a,b);box.append(row);}}
async function refresh(){await Promise.all([loadData(),loadSummary()]);}
$('data-form').onsubmit=async e=>{e.preventDefault();const payload={date:$('date').value,value:Number($('value').value),memo:$('memo').value};try{await request(editingId?'/api/data/'+encodeURIComponent(editingId):'/api/data',{method:editingId?'PUT':'POST',body:JSON.stringify(payload)});notice(editingId?'수정되었습니다.':'추가되었습니다.');$('data-form').reset();editingId=null;$('save-data').textContent='데이터 추가';$('cancel-edit').hidden=true;await refresh();}catch(error){notice(error.message);}};
$('cancel-edit').onclick=()=>{editingId=null;$('data-form').reset();$('save-data').textContent='데이터 추가';$('cancel-edit').hidden=true;};
$('new-chat').onclick=()=>{activeId=null;renderMessages([]);loadConversations();};
$('refresh').onclick=()=>refresh().catch(e=>notice(e.message));
$('chat-form').onsubmit=async e=>{e.preventDefault();const input=$('chat-input');const message=input.value.trim();if(!message)return;input.value='';const current=[...$('messages').querySelectorAll('.bubble')].map(el=>({role:el.classList.contains('user')?'user':'assistant',content:el.textContent}));renderMessages([...current,{role:'user',content:message}]);$('chat-loading').hidden=false;input.disabled=true;try{const result=await request('/api/chat',{method:'POST',body:JSON.stringify({message,conversation_id:activeId})});activeId=result.conversation_id;renderMessages([...current,{role:'user',content:message},{role:'assistant',content:result.answer}]);await loadConversations();}catch(error){renderMessages(current);alert(error.message);}finally{$('chat-loading').hidden=true;input.disabled=false;input.focus();}};
if (accessKey) Promise.all([refresh(),loadConversations()]).then(()=>$('status').textContent='API 연결됨').catch(e=>{$('status').textContent='API 연결 실패';notice(e.message);});
else $('status').textContent='접속 제한';
