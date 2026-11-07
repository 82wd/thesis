import fs from 'node:fs/promises';
import {PresentationFile,FileBlob} from '@oai/artifact-tool';
const root='/Users/lzy/Desktop/毕设/汇报';
const p=await PresentationFile.importPptx(await FileBlob.load(root+'/.ppt_progress_build/candidate.pptx'));
await fs.mkdir(root+'/.ppt_progress_build/renders',{recursive:true});
for(let i=0;i<p.slides.items.length;i++){const b=await p.export({slide:p.slides.items[i],format:'png',scale:1});await fs.writeFile(root+'/.ppt_progress_build/renders/slide-'+String(i+1).padStart(2,'0')+'.png',new Uint8Array(await b.arrayBuffer()));}
console.log('Rendered final 16 slides');
