const $=id=>document.getElementById(id);
function element(tag, className, content){const el=document.createElement(tag);if(className)el.className=className;if(content!==undefined)el.textContent=content;return el;}
function render(items){
  $('total').textContent=items.length;
  $('critical').textContent=items.filter(x=>x.severity==='critical').length;
  $('high').textContent=items.filter(x=>x.severity==='high').length;
  $('other').textContent=items.filter(x=>['medium','low'].includes(x.severity)).length;
  const filter=$('filter').value;
  const list=$('incidents');list.replaceChildren();
  const selected=items.filter(x=>!filter||x.severity===filter);
  if(!selected.length){list.append(element('div','empty','No matching incidents found.'));return;}
  for(const item of selected){
    const card=element('article','incident');
    card.append(element('h3','',item.title));
    const meta=element('div','meta');
    meta.append(element('span','tag '+item.severity,item.severity),element('span','',item.service),element('span','',new Date(item.created_at).toLocaleString()));
    card.append(meta,element('p','',item.description),element('p','',item.explanation),element('p','advice','Next step: '+item.recommendation));
    list.append(card);
  }
}
let all=[];
async function load(){
  try{const res=await fetch('/api/incidents');if(!res.ok)throw Error('Unable to fetch incidents');all=(await res.json()).items;render(all);}
  catch(e){$('message').textContent=e.message;}
}
$('filter').addEventListener('change',()=>render(all));
$('incidentForm').addEventListener('submit',async event=>{
  event.preventDefault();$('submit').disabled=true;$('message').textContent='';
  try{
    const payload=Object.fromEntries(new FormData(event.target));
    const res=await fetch('/api/incidents',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const data=await res.json();if(!res.ok)throw Error(data.error||'Unable to save incident');
    event.target.reset();$('message').style.color='#91e5bd';$('message').textContent='Incident analyzed and saved.';await load();
  }catch(e){$('message').style.color='#ffa6ae';$('message').textContent=e.message;}
  finally{$('submit').disabled=false;}
});
load();