import {PresentationFile,FileBlob} from '@oai/artifact-tool';
const p=await PresentationFile.importPptx(await FileBlob.load('/Users/lzy/Desktop/毕设/汇报/PPT/2026-11-05_组会汇报_SEATrack空间自相似性.pptx'));
console.log((await p.inspect({select:'$.slides[*]',include:['id']})).ndjson);
console.log(p.slides.items[5].shapes.items.map(x=>({text:x.text.toString(),position:x.position})));
