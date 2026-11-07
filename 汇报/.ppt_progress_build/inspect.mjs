import fs from 'node:fs/promises';
import {PresentationFile,FileBlob} from '@oai/artifact-tool';
const root='/Users/lzy/Desktop/毕设/汇报';
const p=await PresentationFile.importPptx(await FileBlob.load(root+'/.ppt_progress_build/source_user_edited.pptx'));
await fs.mkdir(root+'/.ppt_progress_build/source_renders',{recursive:true});
for(let i=0;i<p.slides.items.length;i++){const b=await p.export({slide:p.slides.items[i],format:'png',scale:1});await fs.writeFile(root+'/.ppt_progress_build/source_renders/slide-'+String(i+1).padStart(2,'0')+'.png',new Uint8Array(await b.arrayBuffer()));}
console.log('Rendered final 16 slides');

await fs.writeFile(root+'/.ppt_progress_build/shapes.json',JSON.stringify(p.slides.items.map((s,i)=>({slide:i+1,shapes:s.shapes.items.map((x,j)=>({j,text:x.text.toString(),position:x.position})),tables:s.tables.items.map((t,j)=>({j,rows:t.rows.length,columns:t.columns.length}))})),null,2));
