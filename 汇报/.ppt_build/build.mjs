import fs from 'node:fs/promises';
import path from 'node:path';
import {Presentation, PresentationFile} from '@oai/artifact-tool';
import {finalizePresentation,applyPresentationChartFont} from '/Users/lzy/.codex/plugins/cache/openai-primary-runtime/presentations/26.1026.10807/skills/presentations/container_tools/artifact_tool_utils.mjs';
const root='/Users/lzy/Desktop/毕设', build=path.join(root,'汇报/.ppt_build'), results=path.join(root,'汇报/结果/SS_vs_baseline_ep20_20261104');
const SK='/Users/lzy/.codex/plugins/cache/openai-primary-runtime/presentations/26.1026.10807/skills/presentations';
const P=Presentation.create({slideSize:{width:1280,height:720}});
const F='Hiragino Sans GB', C={ink:'#142C3E', teal:'#007F82', muted:'#546876', light:'#EDF4F5', blue:'#3C78B5', orange:'#D96C38'};
const refs={seat:'Su et al. SEATrack: Simple, Efficient, and Adaptive Multimodal Tracker. CVPR 2026. https://arxiv.org/abs/2604.12502',ss:'Shechtman & Irani. Matching Local Self-Similarities across Images and Videos. CVPR 2007. https://www.wisdom.weizmann.ac.il/~vision/VideoAnalysis/Demos/SelfSimilarities/SelfSimilarities_ShechtmanIrani07.pdf',sp:'Tung & Mori. Similarity-Preserving Knowledge Distillation. ICCV 2019, 1365–1374. https://openaccess.thecvf.com/content_ICCV_2019/html/Tung_Similarity-Preserving_Knowledge_Distillation_ICCV_2019_paper.html'};
const tables=[],charts=[];
function text(s,t,x,y,w,h,size=25,color=C.ink,bold=false){const a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});a.text=t;a.text.style={fontSize:size,typeface:F,color,bold,wrap:'square',autoFit:'none',insets:0,verticalAlignment:'top'};return a;}
function slide(title,sub='',notes=''){const s=P.slides.add();s.background.fill='#FFFFFF';text(s,title,58,42,1164,65,40,C.ink,true);if(sub)text(s,sub,60,113,1155,43,21,C.muted);text(s,String(P.slides.items.length).padStart(2,'0'),1170,676,50,24,17,C.muted);s.speakerNotes.text=notes;return s;}
function foot(s,t){text(s,t,60,635,1110,36,16,C.muted);}
function para(s,heading,body,y,w=1080){text(s,heading,60,y,w,40,29,C.teal,true);text(s,body,60,y+50,w,86,25);}
async function img(s,file,x,y,w,h){const b=await fs.readFile(file);s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:file.endsWith('.png')?'image/png':'image/jpeg',alt:path.basename(file),fit:'contain',position:{left:x,top:y,width:w,height:h}});}
function table(s,values,x,y,w,h,widths,size=23){const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:widths});t.borders.assign({fill:'#D5E1E5',width:1,style:'solid'});for(let r=0;r<values.length;r++)for(let c=0;c<values[r].length;c++){const cell=t.getCell(r,c);cell.fill=r===0?C.ink:(r%2?'#F0F5F6':'#FFFFFF');cell.text.style={fontSize:size,typeface:F,color:r===0?'#FFFFFF':C.ink,bold:r===0,verticalAlignment:'middle',insets:12};}tables.push(P.slides.items.length);return t;}
function note(s,t){s.speakerNotes.text=t;}
// 1
let s=slide('','','今天汇报的是基于SEATrack的跨模态空间自相似性约束。近期完成了完整两两SS损失实现、真实GPU试跑、基线结果整理，以及第20轮的同轮次跟踪与特征可视化。重点回答为什么要做、目前观察到了什么、下一步怎样验证。最终SS模型仍在训练，因此本次不把中间结果当成最终性能结论。');
s.background.fill=C.ink;
text(s,'SEATrack 跨模态空间自相似性约束',60,76,1150,84,49,'#FFFFFF',true);
text(s,'阶段实验与中间轮次可视化',60,176,1080,58,34,'#9EDADD');
await img(s,path.join(results,'blackboy/frame_0060.jpg'),60,278,1050,300);
text(s,'李子彦   组会汇报   2026年11月5日',60,623,1000,40,23,'#FFFFFF');
//2
s=slide('研究背景：跨模态响应对齐与特征关系','研究范围：RGB-T目标跟踪，保留SEATrack原有结构',`多模态跟踪利用可见光与热红外的互补信息。SEATrack在骨干注意力内部通过AMG调节两模态匹配响应，并用HMoE进行跨模态交互。这里需要准确表述：AMG不是最终预测头后的处理，特征也已经经过跨模态交互。我们的研究假设是，在此基础上加入训练期的空间关系一致性约束，可能进一步改善特征学习。该假设尚需对照实验验证。\n来源：${refs.seat}\n图源：本地SEATrack论文第4页Figure 2，裁取原图。`);
await img(s,path.join(build,'assets/seatrack_fig2.png'),60,177,770,410);
text(s,'基线已做什么',860,184,340,40,28,C.teal,true);
text(s,'AMG：调节匹配注意力\nHMoE：跨模态特征交互',860,236,345,105,24);
text(s,'本次要检验什么',860,369,340,40,28,C.teal,true);
text(s,'额外约束两模态内部的空间关系，能否改善定位？',860,423,345,110,25);
foot(s,'依据：[1] SEATrack，CVPR 2026。特征关系约束的有效性属于本课题待验证假设。');
//3
s=slide('实验依据：关系约束有研究基础','借鉴关系建模思想，具体跨模态损失由本课题实现',`本次设计有三层依据。首先，SEATrack讨论了模态偏差与匹配响应之间的冲突，提供了研究问题和基线。其次，局部自相似性研究说明，可以用图像内部的关系描述跨外观的结构。第三，相似性保持蒸馏通过约束成对关系而不是直接复制特征，提供了关系损失的思路。需要强调，经典局部描述子和教师学生蒸馏都不等同于当前RGB-T patch关系损失。引用说明方法来源，不保证当前迁移有效。师兄进一步建议先做完整pairwise SS，再考虑anchor降低复杂度。\n${Object.values(refs).join('\n')}\n本地依据：师兄的想法与建议.rtfd/TXT.rtf及后续聊天中的完整SS建议。`);
table(s,[['依据','支持本实验的内容','迁移到当前方法的边界'],['SEATrack [1]','模态偏差会影响匹配响应','额外SS约束是否有益仍未知'],['局部自相似性 [2]','内部关系可描述跨外观结构','原文是局部描述子，不是本损失'],['相似性保持蒸馏 [3]','约束成对关系，而非逐维复制','原文是教师—学生，本次是RGB—T']],60,182,1160,330,[250,430,480],23);
text(s,'师兄建议：先验证完整两两SS，再研究anchor近似',60,550,1140,62,29,C.teal,true);
foot(s,'[1] Su et al., 2026   [2] Shechtman & Irani, 2007   [3] Tung & Mori, 2019');
//4
s=slide('当前实现：完整两两空间自相似性','辅助损失只在训练和显式验证时计算，推理沿用原跟踪流程',`对RGB和热红外两路patch特征分别在通道维归一化，再计算每对patch的余弦相似度。两个模态的关系矩阵做均方差，模板和搜索区域各占一半，选中层再取平均，总权重为0.1。代码在零基索引3、5、7、9、11号block输入处计算，矩阵包含对角线和双向pair。该模块没有新增可训练参数，梯度用于更新已有可训练参数。当前方法不采用平均池化或可学习query anchor。\n来源：SEATrack-main/README_SS.md；lib/models/layers/semantic_alignment.py；vit_ci.py。`);
text(s,'S_m = normalize(F_m) · normalize(F_m)ᵀ    m ∈ {RGB, T}',60,185,1150,70,32,C.teal,true);
text(s,'LSS = 各层平均 [ 0.5 MSE(S模板ᴿ, S模板ᵀ) + 0.5 MSE(S搜索ᴿ, S搜索ᵀ) ]',60,285,1160,98,27);
text(s,'L总 = L跟踪 + 0.1 LSS',60,391,1150,52,34,C.ink,true);
table(s,[['约束位置','矩阵尺寸','可训练参数增量'],['block输入 3 / 5 / 7 / 9 / 11','模板 64×64；搜索 256×256','0']],60,475,1160,115,[470,420,270],22);
foot(s,'normalize表示沿通道归一化。m区分RGB/热红外模态，ᵀ表示矩阵转置。');
//5
s=slide('对照设置与已完成验证','同轮次可视化使用旧基线第20轮和SS第20轮',`两组对照采用相同的代码基础、初始化权重、数据划分和主要训练设置，SS开关为研究差异。旧基线已有完整60轮，当前SS训练的最近核验状态是第22轮。本次可视化均选择第20轮，避免训练时长不同造成混淆。两组使用相同的推理实现和测试设置。代码已通过8项本地CPU测试，真实GPU试跑完成32个微批、2次更新和4个验证批。它们证明实现能够运行，不是性能有效性的证明。\n来源：复现日志.md；visualization manifest.json；prepare.py。`);
table(s,[['项目','设置'],['训练数据 / 初始化','LasHeR训练集 / OSTrack预训练权重'],['训练预算','60轮，microbatch 4，累积16，有效batch 64'],['随机种子 / 初始学习率','seed 0 / 0.0004'],['轻量微调','沿用LoRA、MoE、scaling等原可训练参数'],['唯一研究改动','加入完整SS约束，权重0.1'],['可视化对照','旧基线ep20 vs SS ep20，同一序列连续跟踪']],60,176,1160,381,[330,830],23);
text(s,'实现验证：8项CPU测试通过，真实GPU试跑退出码0',60,581,1140,40,26,C.teal,true);
foot(s,'相同seed不自动等于所有训练过程完全确定；当前未开展多随机种子重复实验。');
//6
s=slide('已完成结果：第60轮基线完整评测','以下数据属于旧基线，不属于SS改进模型',`这页是已经完成的基线结果。LasHeR使用245条已有轨迹重新整理指标，完整覆盖220703帧。PR为71.5711，NPR为67.8312，SR为57.5125。RGBT234已有234条序列的评测记录，MPR为86.1419，MSR为63.7332。这里采用当前Python参考协议，尚未与MATLAB工具箱执行结果交叉验证，因此不声称精确复现论文数值。基线的意义是提供后续统一协议的比较对象。\n来源：汇报/结果/LasHeR_旧基线_20261104/lasher_metrics_20261104.json；历史RGBT234 metrics_20261022_002510.json与复现日志。`);
table(s,[['数据集','覆盖范围','已得到指标（%）'],['LasHeR','245序列 / 220703帧','PR 71.5711\nNPR 67.8312\nSR 57.5125'],['RGBT234','234序列 / 116649帧','MPR 86.1419\nMSR 63.7332']],60,182,1160,320,[270,390,500],27);
text(s,'后续使用同一评测流程比较SS最终模型',60,545,1140,50,30,C.teal,true);
foot(s,'当前Python参考协议，尚未与MATLAB执行结果交叉验证；不与不同协议的论文数字混作同一对照。');
//7
s=slide('训练中期记录：SS约束参与了优化','截至11月4日核验：训练进入第22/60轮，最近完成第20轮验证',`这些数值直接来自服务器原始日志。SS第10轮验证IoU为0.74327，第20轮为0.74614，SS损失由0.01814降至0.01585。这里能说的是当前模型训练中的关系损失下降，验证IoU没有出现对应的大幅变化。不能用这两点推断相对基线的收益，也不能将训练验证裁剪上的IoU当成完整视频成功率。当前只有一个随机种子，采样一致性还需控制。\n来源：full_zCqHZl/train.log，第10和20轮末条验证记录，已在复现日志记录原始值。`);
table(s,[['验证指标','第10轮','第20轮'],['IoU','0.74327','0.74614'],['SS损失','0.01814','0.01585'],['加权SS项','0.00181','0.00159'],['总损失','1.16924','1.15410']],60,185,1160,300,[500,330,330],27);
text(s,'关系损失下降 ≠ 最终跟踪性能已经提升',60,533,1160,55,32,C.teal,true);
foot(s,'此处为训练流程内的验证统计，无完整SS测试结果；不同轮次的验证采样也可能产生波动。');
//8
s=slide('中间轮次可视化：固定样本与比较条件','两组均使用第20轮权重，连续跟踪共750帧',`序列在运行前用固定随机种子20261104从排序的测试目录抽取，不根据结果挑选。redboygoright处理完整150帧，另外两个序列只处理前300帧。各序列的六个展示帧均匀选定，首帧初始化后使用各自上一帧预测继续跟踪。特征热力图是另一条诊断路径：固定同一真实框中心裁剪，方便排除裁剪不同带来的影响，但不重置跟踪状态。使用测试子集只做预先固定的定性观察，后续参数筛选必须改用独立验证集。\n来源：visualize_midpoint.py、manifest.json、各序列frames.json。`);
table(s,[['序列','完整序列帧数','本次连续跟踪'],['redboygoright','150','150帧'],['leftuphand','1981','前300帧'],['blackboy','432','前300帧']],60,180,1160,250,[500,330,330],26);
text(s,'跟踪图：首帧初始化后连续预测',60,471,1150,42,29,C.teal,true);
text(s,'热力图：相同GT中心裁剪，仅用于特征诊断',60,530,1150,42,29,C.teal,true);
foot(s,'这750帧是定性子集，不替代完整245序列评测。热红外右图仅展示场景，不套用可见光预测框。');
//9
s=slide('跟踪案例：redboygoright，第150帧','绿色真实框，蓝色基线，红色SS',`这个序列共150帧，图中是事先选定的末帧。两组都仍定位到目标，预测框非常接近。这个例子目前主要说明两组在该帧的行为接近，不能据此宣布SS优于基线。展示了原可见光和热红外场景，热红外没有直接套用可见光坐标画预测框。\n来源：redboygoright/frame_0150.jpg；两组同为ep20，从首帧连续跟踪。`);
await img(s,path.join(results,'redboygoright/frame_0150.jpg'),60,174,1160,410);
foot(s,'观察：两组均保持目标定位，框位置接近。单帧只提供定性证据，不能代替序列级评价。');
//10
s=slide('跟踪案例：另外两个固定序列','均展示第300帧，来自同轮次、相同序列的连续跟踪',`这里展示leftuphand和blackboy的第300帧，两者也是在推理前确定的展示帧。当前可见的两组框总体接近，存在位置和尺寸的小差异。不能凭单帧框的视觉差别推断完整序列的精度高低。下一步需要完整视频评测和失败片段分析，确认关系约束是否能转化成定位收益。\n来源：leftuphand/frame_0300.jpg；blackboy/frame_0300.jpg。`);
text(s,'leftuphand',60,177,550,40,28,C.teal,true);text(s,'blackboy',670,177,550,40,28,C.teal,true);
await img(s,path.join(results,'leftuphand/frame_0300.jpg'),60,233,550,210);
await img(s,path.join(results,'blackboy/frame_0300.jpg'),670,233,550,210);
text(s,'框位置和尺寸有小幅差异\n尚无明显一致的单帧优势',60,494,1140,93,31);
foot(s,'所有固定关键帧和视频均已保留，组会可结合离线网页查看完整过程。');
//11
s=slide('特征诊断：两模态空间关系的差异','redboygoright第150帧，block输入索引11，搜索区域',`上排为基线，下排为SS。左两列分别是RGB和热红外内部的两两patch余弦相似矩阵，右列是跨模态的绝对差异。两组的模板相同，当前搜索裁剪也相同，热力图采用统一色标。该帧该层的MSE从0.004981降至0.004439，说明这个固定输入上的结构差异更小。但是这些特征已包含之前层的跨模态交互，并非完全独立的单模态特征。结构差异更小也不保证目标判别性更好。\n来源：redboygoright/ss_f0150_L11_search.png、matrices_0150.npz、diagnostics.json。`);
await img(s,path.join(results,'redboygoright/ss_f0150_L11_search.png'),47,173,860,448);
text(s,'跨模态SS MSE',936,216,300,70,27,C.teal,true);
text(s,'基线  0.004981\nSS     0.004439',936,310,300,130,27);
text(s,'相同输入与色标\n只比较结构差异',936,480,300,90,24,C.muted);
foot(s,'GT中心裁剪仅用于诊断。颜色更接近不自动等于目标定位更准。');
//12
s=slide('多数固定诊断项的结构差异更小','搜索区域：6个固定帧的MSE均值，按block输入层位统计',`这里对三个序列各两个固定帧做统计，一共六个输入。图中只展示搜索区域，每层分别对这六帧求平均。五个层位上SS均低于基线。把模板与搜索区域一起计入，则60组配对诊断中58组SS更低。需要强调，这不是60个独立样本，也没有显著性检验。它支持所检查输入上的结构对齐趋势，不能推出整个数据集的性能增益。下一步在预设独立验证样本上检查定位误差、结构差异和特征方差的联系。\n来源：diagnostics.json；每层每模型仅6个固定帧，算术平均，未按目标难度加权。`);
const data=JSON.parse(await fs.readFile(path.join(build,'chartdata.json'),'utf8'));
const ch=s.charts.add('bar',{position:{left:60,top:180,width:850,height:410},categories:['3','5','7','9','11'],series:[{name:'基线',values:data.Baseline.map(v=>Number(v.toFixed(8))),fill:C.blue},{name:'SS',values:data.SS.map(v=>Number(v.toFixed(8))),fill:C.orange}],barOptions:{direction:'column',grouping:'clustered'},hasLegend:true,legend:{position:'bottom',textStyle:{fontSize:22}},xAxis:{title:'block输入索引',textStyle:{fontSize:20}},yAxis:{min:0,max:.06,numberFormatCode:'0.00',title:'跨模态SS MSE',textStyle:{fontSize:19},majorGridlines:{fill:'#D8E1E5',width:1}},chartFill:'#FFFFFF'});applyPresentationChartFont(ch,{fontFamily:F});charts.push(12);
text(s,'58 / 60',942,232,270,76,52,C.teal,true);
text(s,'配对诊断项中\nSS差异更小',942,322,270,92,26);
text(s,'重复帧、层与区域\n不构成独立样本',942,470,270,90,23,C.muted);
foot(s,'全60项包含模板和搜索区域。图中仅搜索区域；不能以此推断统计显著性或完整跟踪收益。');
//13
s=slide('目前能得出的结论与待解决问题','研究结论停留在实现验证与小样本机制观察',`目前可以确认完整SS约束已经实现，并能参与真实训练。固定样本上的多数结构差异更小。但最终性能是否提升未知，整体定位性能要等完整测试，且当前只做一个随机种子。主要风险包括背景关系主导损失、过强一致性削弱互补性、以及所有patch趋同导致的表征坍缩。已记录非对角相似度均值和标准差，但这些统计不足以排除坍缩。后续应在独立验证集固定裁剪下联合看特征方差、目标背景区分与定位误差。\n依据：当前诊断记录；本科毕业设计任务书中的分组诊断、坍缩监测和主任务验证要求。`);
para(s,'已确认','实现能够运行，关系损失下降；固定输入上多数SS结构差异减小。',180);
para(s,'尚未确认','完整视频跟踪是否提升，以及收益是否能在不同随机种子下保持。',337);
para(s,'下一步诊断','区分目标与背景，联合检查定位误差、特征方差和关系差异。',494);
//14
s=slide('后续实验计划：先完成主线，再扩大消融','日期是安排目标，训练与评测时长受共享GPU和存储速度影响',`计划分阶段推进。11月5到6日优先核对评测协议，并在独立验证集固定样本做分组诊断。现有60轮SS训练继续完成，预计还需数天，完成后用与基线相同的流程评测LasHeR和RGBT234。只有主任务结果清楚后才增加消融。首先考虑一个较小权重0.03，与已有0和0.1的相同20轮结果比较，其他设置保持一致。若预算允许，再对最终选定方案补充随机种子。期望产出是可判断假设的对照证据，而不是预设一定提高若干个百分点。\n依据：任务书的主任务优先、验证集调参、预算核定要求；复现日志中的当前吞吐记录。`);
table(s,[['阶段 / 时间','实验方法','判断标准与产出'],['11月5—6日','固定验证样本，分定位质量组\n核对Python与参考评测口径','检查结构差异是否对应定位变化\n明确指标可比范围'],['现有训练结束后1天内','SS第60轮完整评测\n同协议比较旧基线第60轮','LasHeR PR/NPR/SR\nRGBT234 MPR/MSR与失败案例'],['主结果明确后2—5天','先增加λ=0.03的同预算试验\n与λ=0、0.1的20轮结果比较','验证集选权重，记录实际GPU小时\n收益有限时优先分析原因'],['预算允许时','最终方案补随机种子\n再考虑层位/区域或anchor','报告实际运行次数与均值/波动\n不提前宣称鲁棒提升']],60,176,1160,419,[280,435,445],22);
foot(s,'顺序：主任务完整对照优先。测试集用于最终评估，后续调参只使用独立验证集。');
//15
s=slide('可行性与希望讨论的问题','新增训练前先核定时间预算，避免同时展开多种变量',`当前显存上具备开展推理和诊断的条件，真实试跑峰值分配约2431MiB，但这不代表所有正式训练状态的峰值。时间方面，根据已观察到7.9到22.4样本每秒的吞吐，59968训练样本的一轮纯训练阶段约45到127分钟，20轮约15到42GPU小时，均不含验证和I/O停顿。因此不建议一次开展大量消融。我的优先顺序是先完整评测，再做一个较小权重的对照。希望讨论的是，如果结构差异已经减小而定位收益有限，应优先减小权重，还是限制到目标相关区域。\n时间推算：59968 / 22.4 / 3600与59968 / 7.9 / 3600；吞吐来自历史日志快照，非稳定性能基准。`);
text(s,'20轮单组试验：约15—42 GPU小时',60,190,1140,62,38,C.teal,true);
text(s,'按已观察吞吐推算，仅含训练阶段\n验证、保存及共享存储停顿会额外增加时间',60,275,1150,100,27);
text(s,'若结构更一致，但定位收益有限',60,426,1150,45,31,C.ink,true);
text(s,'优先减小约束权重，还是限制到目标相关区域？',60,495,1150,70,34,C.teal,true);
foot(s,'本次研究目标：验证额外SS约束的实际收益与适用边界，而非仅让辅助损失变小。');
//16
s=slide('参考文献与结果来源','文献提供研究依据，结论以当前实验实际证据为准',`正文中的文献均可通过这里的链接追溯。SEATrack作为基线和问题背景；局部自相似性及相似性保持蒸馏提供关系建模启发，但不是当前损失的直接有效性证明。本地数据包括基线完整指标报告、第20轮权重清单、固定序列的预测与矩阵，以及服务器原始日志。数据与图片均为已执行结果，没有把未来实验的期望写成已有结果。\n${Object.values(refs).join('\n')}\n本地资料：本科毕业设计任务书；师兄的想法与建议；复现日志.md；汇报/结果目录。`);
text(s,'[1] Su J, et al. SEATrack: Simple, Efficient, and Adaptive Multimodal Tracker. CVPR 2026.',60,179,1150,79,25);
text(s,'[2] Shechtman E, Irani M. Matching Local Self-Similarities across Images and Videos. CVPR 2007.',60,280,1150,80,25);
text(s,'[3] Tung F, Mori G. Similarity-Preserving Knowledge Distillation. ICCV 2019: 1365–1374.',60,382,1150,80,25);
text(s,'本地依据：任务书、师兄建议、复现日志\n实验数据：基线指标报告、ep20预测与SS矩阵、权重SHA清单',60,505,1150,95,25,C.teal);
foot(s,'完整文献URL与逐页讲稿位于备注区。');
// Export previews and draft
await fs.mkdir(path.join(build,'renders'),{recursive:true});
for(let i=0;i<P.slides.items.length;i++){const sl=P.slides.items[i]; const blob=await P.export({slide:sl,format:'png',scale:1}); await fs.writeFile(path.join(build,'renders',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));console.log('rendered',i+1);}
await fs.writeFile(path.join(build,'deck.json'),JSON.stringify(P.toProto()));
const candidate=path.join(build,'candidate.pptx');await (await PresentationFile.exportPptx(P)).save(candidate);
const final=path.join(root,'汇报/PPT/2026-11-05_组会汇报_SEATrack空间自相似性.pptx');
const validation=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:final,pythonExecutable:'/Users/lzy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',integrityValidatorPath:path.join(SK,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SK,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...tables.flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:tables,requiredNativeChartOwnerSlides:charts,materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[F]},verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json')});
console.log(JSON.stringify(validation));
