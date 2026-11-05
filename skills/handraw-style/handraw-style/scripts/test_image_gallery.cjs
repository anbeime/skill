// Offline checks of generated JavaScript logic. Does not open/render a browser.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const file=path.join(root,'skills/handdraw-style-prompter/gallery/tutorials.html');
const html=fs.readFileSync(file,'utf8').replace(/\r\n/g,'\n');
for(const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g)) new vm.Script(match[1]);
assert(!html.includes('data-mode="video"'));assert(!html.includes('video-shots.html'));
class Element {
  constructor(){this.value='';this.textContent='';this.hidden=false;this.open=false;this.style={};this.dataset={};this.scrollHeight=58;this.handlers={};this.children=[];this.classList={toggle(){},add(){},remove(){}};}
  addEventListener(name,handler){this.handlers[name]=handler;}
  focus(){} setAttribute(name,value){this[name]=value;} showModal(){this.open=true;} close(){this.open=false;}
  set innerHTML(value){this.markup=value;this.children=[...value.matchAll(/<button\b([^>]+)>/g)].map(match=>{const el=new Element();for(const attr of match[1].matchAll(/data-([\w-]+)="([^"]*)"/g))el.dataset[attr[1].replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=attr[2];return el;});}
  get innerHTML(){return this.markup||'';}
  querySelectorAll(){return this.children;}
  querySelector(selector){return this.children.find(el=>selector===`[data-id="${el.dataset.id}"]`)||this.children[0]||null;}
}
const nodes=new Map();const get=selector=>{if(!nodes.has(selector))nodes.set(selector,new Element());return nodes.get(selector);};
const document={querySelector:selector=>selector.startsWith('#slot-')?null:get(selector),querySelectorAll:()=>[]};
const context=vm.createContext({document,assert,console});const run=source=>vm.runInContext(source,context);
for(const name of ['LAYOUTS_DATA','STYLES_DATA','COLORS_DATA','TONES_DATA','OFFICIAL_ASSETS_DATA']){const match=html.match(new RegExp(`const ${name} = ([^\\n]+);`));assert(match,name);run(match[0]);}
run('let ASSETS_DATA = [...OFFICIAL_ASSETS_DATA];');
run(html.match(/const I18N = \{[\s\S]*?\n\};/)[0]);
run(`
let currentLang='zh',currentMode='pure',currentWhitespace='normal';
let selectedAssets=[],selectedTones=[],selectedLayout=null,selectedStyle=null,selectedColor=null,selectedCharStyle=null,selectedSceneStyle=null;
let isToneActive=false,isFusionActive=false,isBatchActive=false,isMixLayoutsActive=false,currentPickerType=null,currentPickerFilter='all';
const REALISTIC_ITEM={id:'realistic',isRealistic:true,name:'写实'};
const pickerGrid=document.querySelector('#picker-grid'),pickerSearch=document.querySelector('#picker-search'),pickerFilters=document.querySelector('#picker-filters'),pickerTitle=document.querySelector('#picker-title'),pickerDialog=document.querySelector('#picker-dialog');
const modalAssetFooter=document.querySelector('#modal-asset-footer'),modalAssetSummary=document.querySelector('#modal-asset-summary');
const inputTheme=document.querySelector('#input-theme'),themeLabelText=document.querySelector('#theme-label-text');
const inputAudience=document.querySelector('#input-audience'),inputChannel=document.querySelector('#input-channel'),inputRatio=document.querySelector('#input-ratio'),inputMood=document.querySelector('#input-mood'),inputShootType=document.querySelector('#input-shoot-type'),btnClearRatio=document.querySelector('#btn-clear-ratio');
const posterExtraFields=document.querySelector('#poster-extra-fields'),photoExtraFields=document.querySelector('#photo-extra-fields'),assembledText=document.querySelector('#assembled-text');
const updateSlotUI=()=>{},renderLayoutFilters=()=>{},renderAssetFilters=()=>{},updateModalAssetCount=()=>{},renderAssetsTray=()=>{},renderToneFilters=()=>{},updateModalToneCount=()=>{},renderStyleFilters=()=>{},renderColorFilters=()=>{};
`);
for(const name of ['updatePrompt','setMode','autoResizeTheme','openPicker','renderPickerItems']){const match=html.match(new RegExp(`function ${name}\\([^]*?\\n\\}`));assert(match,name);run(match[0]);}
run(`
assert.equal(STYLES_DATA.length,331);assert.equal(LAYOUTS_DATA.length,166);assert.equal(COLORS_DATA.length,36);
for(const [mode,phrase] of [['pure','主题：'],['graphic-text','图文模式'],['poster','请帮我出海报提示词'],['article-illust','文章插图模式'],['article-cover','请设计文章封面'],['photo','摄影写真模式']]){
  inputTheme.value='桌上的断绳';setMode(mode);assert.match(assembledText.textContent,new RegExp(phrase));assert.equal(inputTheme.style.height,'58px');
}
setMode('pure');openPicker('layout');assert.equal(pickerGrid.children.length,166);assert.equal(modalAssetFooter.hidden,true);
pickerGrid.children[0].handlers.click();assert(selectedLayout);assert.equal(pickerDialog.open,false);
pickerSearch.value='IP-007';openPicker('layout');pickerSearch.value='IP-007';renderPickerItems();assert.equal(pickerGrid.children.length,1);pickerGrid.children[0].handlers.click();assert.equal(selectedLayout.id,'IP-007');
pickerSearch.value='';openPicker('style');assert.equal(pickerGrid.children.length,332);
pickerSearch.value='FA-001';renderPickerItems();assert.equal(pickerGrid.children.length,1);pickerGrid.children[0].handlers.click();assert.equal(selectedStyle.id,'FA-001');
for(const id of ['IP-007','EC-001']){selectedLayout=LAYOUTS_DATA.find(item=>item.id===id);assert(selectedLayout);updatePrompt();assert(assembledText.textContent.includes(id));}
isFusionActive=true;selectedCharStyle=STYLES_DATA.find(item=>item.id==='FA-001');selectedSceneStyle=REALISTIC_ITEM;inputRatio.value='3:4';updatePrompt();
assert.match(assembledText.textContent,/角色风格：FA-001/);assert.match(assembledText.textContent,/场景风格：写实/);assert.match(assembledText.textContent,/风格融合设计/);
isToneActive=true;selectedTones=[TONES_DATA[0]];assert(TONES_DATA.length>0);updatePrompt();assert.match(assembledText.textContent,/影调：/);
isBatchActive=true;isMixLayoutsActive=true;updatePrompt();assert.match(assembledText.textContent,/批量出图/);assert.match(assembledText.textContent,/混合多种图型/);
currentLang='en';updatePrompt();assert.match(assembledText.textContent,/Character style: FA-001/);assert.match(assembledText.textContent,/Scene style: Realistic/);assert.match(assembledText.textContent,/Batch Generation/);
`);
console.log(JSON.stringify({passed:true,styles:331,layouts:166,colors:36,scope:'JavaScript syntax; six image modes; style/layout pickers; IP/e-commerce; fusion; tones; batch; bilingual prompts. Not visual UI acceptance.'}));
