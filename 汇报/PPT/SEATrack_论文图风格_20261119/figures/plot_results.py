"""Measured results, one run per method. No smoothing or invented uncertainty."""
import csv,sys,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
sys.path.insert(0,'/Users/lzy/.codex/skills/nature-figure/scripts')
from audit_panel_alignment import require_matplotlib_panel_alignment
P=Path(__file__).resolve().parent.parent
plt.rcParams.update({'font.family':'Arial','font.size':12,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42,'legend.frameon':False})
C=['#717A80','#4A8FBD','#BC8E53','#91B9D1','#D3B58E']
def save(fig,name):
 fig.canvas.draw()
 require_matplotlib_panel_alignment(fig,json_out=str(P/'figures'/f'{name}.alignment.json'),strict=True)
 fig.savefig(P/'images'/f'{name}.png',dpi=300)
 fig.savefig(P/'figures'/f'{name}.pdf')
 fig.savefig(P/'figures'/f'{name}.svg')
 plt.close(fig)
# Percent-point changes are paired within datasets, not pooled across metrics.
fig,ax=plt.subplots(figsize=(12.8,4.8));fig.subplots_adjust(left=.24,right=.93,bottom=.18,top=.9)
names=['LasHeR / SR','RGBT234 / MSR','VisEvent / SR','DepthTrack / F']
a=np.array([57.51,63.73,60.26,63.23]);b=np.array([56.71,64.67,59.63,60.97]);d=b-a
y=np.arange(4)
ax.barh(y,d,height=.46,color=[C[2] if v<0 else C[1] for v in d]);ax.axvline(0,color='#303638',lw=.8)
ax.set(yticks=y,yticklabels=names,xlim=(-2.6,1.5),xlabel='SS minus baseline (percentage points)');ax.invert_yaxis()
for i,v in enumerate(d): ax.text(v+(.06 if v>=0 else -.06),i,f'{v:+.2f}',ha='left' if v>=0 else 'right',va='center',weight='bold')
ax.grid(False);ax.set_axisbelow(True);save(fig,'ss_results')
fig,axes=plt.subplots(1,2,figsize=(12.8,4.8));fig.subplots_adjust(left=.15,right=.97,bottom=.17,top=.85,wspace=.5)
methods=['Baseline','Original SS','Template-only','Target-aware']
for ax,vals,title,limits in zip(axes,[[57.51,56.71,57.31,57.29],[63.73,64.67,64.03,64.06]],['LasHeR / SR (%)','RGBT234 / MSR (%)'],[(56.5,57.9),(63.5,65.1)]):
 ax.axvline(vals[0],color=C[0],ls='--',lw=1);ax.scatter(vals,np.arange(4),c=C[:4],s=90,zorder=3)
 for i,v in enumerate(vals):ax.text(limits[1]-.02,i,f'{v:.2f}',va='center',ha='right',fontsize=12)
 ax.set(yticks=np.arange(4),yticklabels=methods,xlim=limits,ylim=(3.6,-.6),xlabel=title)
 ax.grid(False)
save(fig,'ab_results')
rows=list(csv.DictReader((P/'sources/epoch_metrics.csv').open()))
fig,axes=plt.subplots(1,2,figsize=(12.8,4.8));fig.subplots_adjust(left=.08,right=.97,bottom=.18,top=.82,wspace=.27)
for ax,key,title,scale in zip(axes,['Loss/ss_search','IoU'],['Unweighted search SS (MSE)','Sampled crop IoU (%)'],[1,100]):
 for split,col,ls,label in [('train',C[1],'-','Train (60 epochs)'),('val',C[2],'--','Validation (12 points)')]:
  r=[r for r in rows if r['split']==split]
  ax.plot([float(v['epoch']) for v in r],[float(v[key])*scale for v in r],color=col,ls=ls,marker='o' if split=='val' else None,ms=3,lw=1.8,label=label)
 ax.set(xlim=(0,61),xlabel='Epoch',ylabel=title);ax.grid(alpha=.15)
fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.99),ncol=2)
save(fig,'dynamics')
fig,axes=plt.subplots(1,3,figsize=(12.8,4.8));fig.subplots_adjust(left=.07,right=.98,bottom=.29,top=.85,wspace=.27)
values=[[0,0,.8111,0,.8253],[.0138,.0066,.0200,.0091,.0224],[.8016,.7680,.7713,.7771,.7779]]
labels=['Sum','R-low','I-low','R-low\nRMS','I-low\nRMS']
for ax,v,title in zip(axes,values,['White SUV: frame 23','Face: frame 165','Stable controls: 66 frames']):
 ax.bar(range(5),v,color=C,width=.6);ax.set(xticks=range(5),xticklabels=labels,ylim=(0,1),title=title)
 ax.tick_params(axis='x',labelsize=10);ax.grid(False);ax.set_axisbelow(True)
 for i in [0,2,4]:ax.text(i,v[i]+.025,f'{v[i]:.3f}',ha='center',fontsize=10)
axes[0].set_ylabel('IoU');save(fig,'frequency_results')
(P/'sources/chart_data.json').write_text(json.dumps({'ss':{'datasets':names,'baseline':a.tolist(),'ss':b.tolist()},'ab':{'methods':methods,'LasHeR':[57.51,56.71,57.31,57.29],'RGBT234':[63.73,64.67,64.03,64.06]},'frequency':{'methods':labels,'white_face_stable':values}},indent=2))
print('4 figures exported as PNG/SVG/PDF with alignment checks')
