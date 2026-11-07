import fs from 'node:fs/promises';
import path from 'node:path';
import {PresentationFile,FileBlob} from '@oai/artifact-tool';
import {finalizePresentation} from '/Users/lzy/.codex/plugins/cache/openai-primary-runtime/presentations/26.1026.10807/skills/presentations/container_tools/artifact_tool_utils.mjs';
const root='/Users/lzy/Desktop/毕设',build=root+'/汇报/.ppt_work_build',results=root+'/汇报/结果/SS_vs_baseline_ep20_20261104';
const P=await PresentationFile.importPptx(await FileBlob.load(root+'/汇报/PPT/2026-11-05_组会汇报_成果重点版.pptx'));
const original=P.slides.items.slice();
const oldIds=(await P.inspect({select:'$.slides[*]',include:['id']})).records.map(r=>r.id);
const F='Hiragino Sans GB',C={ink:'#142C3E',teal:'#007F82',muted:'#546876'};
function text(s,t,x,y,w,h,size=25,color=C.ink,bold=false){const a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});a.text=t;a.text.style={fontSize:size,typeface:F,color,bold,wrap:'square',autoFit:'none',insets:0,verticalAlignment:'top'};return a;}
function newSlide(title,sub,notes){const s=P.slides.add();s.background.fill='#FFFFFF';text(s,title,58,42,1164,65,40,C.ink,true);text(s,sub,60,113,1155,43,21,C.muted);s.speakerNotes.text=notes;return s;}
function foot(s,t){text(s,t,60,635,1110,36,16,C.muted);}
function replace(s,from,to){for(const sh of s.shapes.items){if(sh.text.toString()===from)sh.text=to;}}
async function img(s,file){const b=await fs.readFile(file);s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:'image/jpeg',alt:path.basename(file),fit:'contain',position:{left:60,top:174,width:1160,height:410}});}
function block(s,h,b,y){text(s,h,60,y,1140,44,30,C.teal,true);text(s,b,60,y+53,1140,90,27);}
let s=newSlide('我的工作：实现并验证师兄提出的SS改进','在SEATrack基础上增加训练期的跨模态特征关系约束',`这次工作主要围绕师兄提出的改进展开，而不是重新介绍SEATrack原论文。师兄的想法是在已有匹配响应交互之外，进一步约束特征内部的空间关系。我最近先理解了SS、语义anchor以及损失如何影响特征学习，再把完整两两SS方案落实到代码，最后通过真实训练和中间轮次的可视化检查实际变化。现阶段目标是验证这项附加约束是否有作用，不能预先认定一定提高定位精度。\n依据：师兄的想法与建议.rtfd/TXT.rtf、后续完整pairwise SS建议、本科毕业设计任务书。`);
block(s,'要解决的问题','在保留原有跨模态交互的基础上，额外约束空间关系，\n能否让两模态的表征更一致，并改善目标定位？',180);
block(s,'我的工作内容','理解SS与语义anchor的含义，明确约束如何作用于训练；\n实现损失与训练接入，并设计对照实验。',344);
block(s,'当前阶段','完整SS方案已实现并开始正式训练，\n目前用中间轮次的跟踪与特征结果检查改进是否产生预期变化。',508);
const first=s;
s=newSlide('我对改进思路的理解：约束patch之间的关系','比较关系结构，而不要求RGB与热红外特征逐维相同',`SS描述的是同一模态内部各个patch之间的相似关系。不同模态的外观可以不同，但目标及周围区域的空间关系可能有可比较的部分。我们将两个模态各自得到的关系描述进行比较。语义anchor是另一种更紧凑的关系表示：例如平均池化构建一个代表向量，再计算各patch与它的相似度。可学习query也是师兄提出的备选构建方式，但当前没有实现为主实验。最后，关系差异通过辅助损失反向传播，更新已有可训练参数，并影响之后的特征提取，不是在同一次前向中直接改写特征。\n依据：师兄建议；SEATrack-main/README_SS.md与semantic_alignment.py。关系建模文献见备份页。`);
block(s,'空间自相似性（SS）','先在RGB、热红外各自内部计算patch相似关系，\n再约束两种模态的关系描述保持一致。',180);
block(s,'语义anchor的作用','平均池化或可学习query可构建代表向量，\n用patch与anchor的相似度形成更紧凑的关系描述。',344);
block(s,'辅助损失如何起作用','关系差异通过反向传播更新已有轻量微调参数，\n影响后续提取的特征；推理时不需要辅助损失分支。',508);
const second=s;
s=newSlide('当前方案：先验证完整SS，再考虑anchor简化','师兄明确建议先做两两pair计算，当前不采用平均池化或可学习query',`最初的思路包括用平均池化或可学习query构建语义anchor。师兄之后建议先按标准空间自相似性直接计算两两patch关系，因为anchor主要用于简化计算。当前实验先回答完整SS约束是否有效，避免一开始同时混入anchor近似误差。具体实现选取block输入3、5、7、9、11，分别计算模板和搜索区域关系，区域权重各0.5，总损失权重0.1。这些具体层位和权重是当前实现设置，不应全部说成师兄指定。后续通过验证集消融判断设置是否合适。\n来源：师兄后续消息、README_SS.md、配置rgbt_ss.yaml、vit_ci.py和semantic_alignment.py。`);
const vals=[['层次','本次采用的方案'],['师兄明确提出的方向','完整两两SS作为loss，先检验是否有效'],['当前实现的具体设置','block输入3/5/7/9/11；模板与搜索各0.5；总权重0.1'],['本轮保持不变的部分','AMG、融合方式和预测头；沿用已有轻量微调参数'],['暂缓的方案','平均池化anchor、可学习query，留待完整SS验证之后']];
const t=s.tables.add({rows:5,columns:2,left:60,top:183,width:1160,height:340,values:vals,columnWidths:[340,820]});
t.borders.assign({fill:'#D5E1E5',width:1,style:'solid'});
for(let r=0;r<5;r++)for(let c=0;c<2;c++){const cell=t.getCell(r,c);cell.fill=r===0?C.ink:r%2?'#F0F5F6':'#FFFFFF';cell.text.style={fontSize:24,typeface:F,color:r===0?'#FFFFFF':C.ink,bold:r===0,verticalAlignment:'middle',insets:12};}
text(s,'接下来汇报：方案落地后，已经完成了哪些工作',60,567,1150,50,30,C.teal,true);
foot(s,'层位和权重属于当前实现选择，后续需要实验验证；本次展示的数据均来自完整SS方案。');
const all=(await P.inspect({select:'$.slides[*]',include:['id']})).records.map(r=>r.id);
P.slides.reorder([...all.slice(13),...oldIds]);
replace(original[0],'近期成果：基线评测与第20轮对比','已完成工作：实现、训练与结果分析');
replace(original[0],'SEATrack空间自相似性约束   李子彦   2026年11月5日','以下汇报已完成的实现验证、基线评测和中间轮次结果');
original[0].speakerNotes.text='前面说明了我的工作是什么，这里开始汇报已经完成的内容。完整两两SS已经接入训练，CPU测试与真实GPU试跑通过，正式训练进入第22轮。基线完整结果已经整理，同轮次第20轮的跟踪和特征可视化也已完成。下面分别介绍这些结果。\n来源：复现日志.md及汇报/结果目录。';
for(const sl of P.slides.items)for(const sh of sl.shapes.items){if(sh.position.left>1150&&sh.position.top>660&&/^\d+$/.test(sh.text.toString().trim()))sh.text='';}
await fs.mkdir(build+'/renders',{recursive:true});
for(let i=0;i<P.slides.items.length;i++){const b=await P.export({slide:P.slides.items[i],format:'png',scale:1});await fs.writeFile(build+'/renders/slide-'+String(i+1).padStart(2,'0')+'.png',new Uint8Array(await b.arrayBuffer()));}
await (await PresentationFile.exportPptx(P)).save(build+'/candidate.pptx');
console.log('Authored 16 slides without page numbers');
