import fs from 'node:fs/promises';
import path from 'node:path';
import {PresentationFile,FileBlob} from '@oai/artifact-tool';
import {finalizePresentation} from '/Users/lzy/.codex/plugins/cache/openai-primary-runtime/presentations/26.1026.10807/skills/presentations/container_tools/artifact_tool_utils.mjs';
const root='/Users/lzy/Desktop/毕设',build=root+'/汇报/.ppt_results_build',results=root+'/汇报/结果/SS_vs_baseline_ep20_20261104';
const P=await PresentationFile.importPptx(await FileBlob.load(root+'/汇报/PPT/2026-11-05_组会汇报_SEATrack空间自相似性.pptx'));
const original=P.slides.items.slice();
const oldIds=(await P.inspect({select:'$.slides[*]',include:['id']})).records.map(r=>r.id);
const F='Hiragino Sans GB',C={ink:'#142C3E',teal:'#007F82',muted:'#546876'};
function text(s,t,x,y,w,h,size=25,color=C.ink,bold=false){const a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});a.text=t;a.text.style={fontSize:size,typeface:F,color,bold,wrap:'square',autoFit:'none',insets:0,verticalAlignment:'top'};return a;}
function newSlide(title,sub,notes){const s=P.slides.add();s.background.fill='#FFFFFF';text(s,title,58,42,1164,65,40,C.ink,true);text(s,sub,60,113,1155,43,21,C.muted);text(s,'00',1170,676,50,24,17,C.muted);s.speakerNotes.text=notes;return s;}
function foot(s,t){text(s,t,60,635,1110,36,16,C.muted);}
function replace(s,from,to){for(const sh of s.shapes.items){if(sh.text.toString()===from)sh.text=to;}}
async function img(s,file){const b=await fs.readFile(file);s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:'image/jpeg',alt:path.basename(file),fit:'contain',position:{left:60,top:174,width:1160,height:410}});}
const summary=newSlide('近期成果：基线评测与第20轮对比','SEATrack空间自相似性约束   李子彦   2026年11月5日',`本次直接汇报已经做出的成果。第一，完成完整两两SS损失实现，真实GPU试跑通过，正式训练已进入第22轮。第二，整理了旧基线在LasHeR和RGBT234上的完整评测。第三，用旧基线和SS同为第20轮的权重完成三个固定序列、750帧的连续跟踪，生成可视化和分层特征诊断。所检查的60组配对诊断中58组SS差异更小，但最终跟踪增益尚待完整评测。研究目的是检验在SEATrack既有响应交互基础上增加训练期特征关系约束的实际作用。依据师兄建议先做完整SS，具体方法和文献放在备份页。\n来源：复现日志.md、基线指标报告、第20轮manifest.json及diagnostics.json。`);
text(summary,'完整SS实现与训练',60,190,600,46,32,C.teal,true);
text(summary,'8项CPU测试通过，真实GPU试跑完成\n正式训练进入第22/60轮',60,246,1120,86,27);
text(summary,'两套基线评测结果',60,354,650,46,32,C.teal,true);
text(summary,'LasHeR：245序列     RGBT234：234序列',60,408,1120,54,27);
text(summary,'第20轮同轮次可视化',60,496,750,46,32,C.teal,true);
text(summary,'3个固定序列，750帧连续跟踪，60组配对特征诊断',60,552,1130,55,27);
foot(summary,'研究问题：附加空间关系约束能否改善定位？当前已观察到结构变化，最终性能仍需验证。');
const left=newSlide('跟踪结果：leftuphand，第300帧','旧基线ep20与SS ep20，绿色真实框，蓝色基线，红色SS',`这个序列完整长度1981帧，本次按事先确定的预算连续运行前300帧，展示的是固定选定的第300帧。首帧用真实框初始化，此后两组使用各自预测继续跟踪。该帧两组都定位到目标，框的边缘略有差别，没有明显一致的优势。不能将单帧视觉差异视为完整序列指标。\n来源：leftuphand/frame_0300.jpg、frames.json、Baseline.txt和SS.txt；固定seed20261104抽取序列。`);
await img(left,results+'/leftuphand/frame_0300.jpg');foot(left,'观察：两组均定位到目标，框边缘略有差异。右侧热红外只展示场景，不套用可见光预测框。');
const black=newSlide('跟踪结果：blackboy，第300帧','同样的训练轮次与连续跟踪设置，保留相近结果',`blackboy序列完整长度432帧，本次连续运行前300帧。该图同样是预先确定的末帧，不按效果筛选。可以看到两组预测框接近。目前这些固定案例尚未显示明显一致的定位优势。其价值在于把真实中间结果展示出来，和后面的SS结构诊断一起分析，下一步通过完整评测检验是否转化成收益。\n来源：blackboy/frame_0300.jpg、frames.json；权重来源见manifest.json。`);
await img(black,results+'/blackboy/frame_0300.jpg');foot(black,'观察：两组框总体接近。已有结果支持继续诊断，但不能据此声称跟踪性能提升。');
const allIds=(await P.inspect({select:'$.slides[*]',include:['id']})).records.map(r=>r.id);
const newIds=allIds.slice(16);
// Ten main slides, three backup slides; original evidence objects remain editable.
const order=[newIds[0],oldIds[5],oldIds[6],oldIds[8],newIds[1],newIds[2],oldIds[10],oldIds[11],oldIds[12],oldIds[13],oldIds[4],oldIds[3],oldIds[15]];
P.slides.keep(order);P.slides.reorder(order);
replace(original[5],'已完成结果：第60轮基线完整评测','成果一：基线完整评测结果');
replace(original[6],'训练中期记录：SS约束参与了优化','成果二：SS实现完成，正式训练持续推进');
replace(original[8],'跟踪案例：redboygoright，第150帧','跟踪结果：redboygoright，第150帧');
replace(original[10],'特征诊断：两模态空间关系的差异','特征结果：同一输入的跨模态结构差异减小');
replace(original[11],'多数固定诊断项的结构差异更小','量化结果：58/60组配对诊断的差异更小');
replace(original[12],'目前能得出的结论与待解决问题','当前结论：结构发生变化，定位增益待验证');
replace(original[13],'后续实验计划：先完成主线，再扩大消融','下一步：完整评测与针对性消融');
replace(original[4],'对照设置与已完成验证','备份：实验设置与验证');
replace(original[3],'当前实现：完整两两空间自相似性','备份：完整两两SS的计算方法');
replace(original[15],'参考文献与结果来源','备份：方法依据与结果来源');
// Keep the rationale and budget in notes without consuming main-deck space.
original[13].speakerNotes.text += '\n预算补充：按照已观察吞吐7.9—22.4样本/秒和59968样本/轮，20轮单组纯训练约15—42 GPU小时，不含验证、保存和I/O停顿。先完成主结果，再决定新增实验。';
for(let i=0;i<P.slides.items.length;i++){const s=P.slides.items[i];for(const sh of s.shapes.items){if(sh.position.left>1150 && sh.position.top>660)sh.text=String(i+1).padStart(2,'0');}}
await fs.mkdir(build+'/renders',{recursive:true});
for(let i=0;i<P.slides.items.length;i++){const b=await P.export({slide:P.slides.items[i],format:'png',scale:1});await fs.writeFile(build+'/renders/slide-'+String(i+1).padStart(2,'0')+'.png',new Uint8Array(await b.arrayBuffer()));}
await (await PresentationFile.exportPptx(P)).save(build+'/candidate.pptx');
const tables=[2,3,10,11,12],sk='/Users/lzy/.codex/plugins/cache/openai-primary-runtime/presentations/26.1026.10807/skills/presentations';
const result=await finalizePresentation({workspaceDir:root,candidatePath:build+'/candidate.pptx',finalPath:root+'/汇报/PPT/2026-11-05_组会汇报_成果重点版.pptx',pythonExecutable:'/Users/lzy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',integrityValidatorPath:sk+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:sk+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...tables.flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:tables,requiredNativeChartOwnerSlides:[8],materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[F]},verifyArtifactToolImport:true,receiptPath:build+'/validation.json'});
console.log(result.finalPath);
