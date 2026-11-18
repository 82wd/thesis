"""Plot observed epoch averages. One seed; no smoothing or error bars."""
import csv
import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
sys.path.insert(0, '/Users/lzy/.codex/skills/nature-figure/scripts')
from audit_panel_alignment import require_matplotlib_panel_alignment
OUT = Path(__file__).resolve().parent
with (OUT/'epoch_metrics.csv').open() as f:
    rows = list(csv.DictReader(f))
for row in rows:
    for key in row:
        if key != 'split': row[key] = float(row[key])
    row['tracking'] = row['Loss/total'] - row['Loss/ss_weighted']
    row['ratio'] = 100 * row['Loss/ss_weighted'] / row['Loss/total']
train = [r for r in rows if r['split']=='train']
val = [r for r in rows if r['split']=='val']
assert len(train)==60 and len(val)==12
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
    'font.size':11,'svg.fonttype':'none','pdf.fonttype':42,
    'axes.spines.top':False,'axes.spines.right':False,'legend.frameon':False})
plots = [
 ('01_search_ss','Search SS: training and validation','Unweighted search SS (MSE)','Loss/ss_search'),
 ('02_tracking_loss','Tracking objective during training','Tracking loss (total minus weighted SS)','tracking'),
 ('03_iou','IoU during training and validation','Sampled crop IoU (%)','IoU'),
 ('04_ss_contribution','Numerical contribution of SS to total loss','Weighted SS / total loss (%)','ratio'),
 ('05_layers_train','Layer-wise search SS: training','Unweighted search SS (MSE)','layers_train'),
 ('06_layers_val','Layer-wise search SS: validation','Unweighted search SS (MSE)','layers_val'),
 ('07_giou','GIoU loss during training','GIoU loss (before coefficient 2)','Loss/giou'),
 ('08_l1','Box L1 loss during training','L1 loss (before coefficient 5)','Loss/l1'),
 ('09_location','Location loss during training','Location loss','Loss/location'),
 ('10_weighted_ss','Weighted SS during training','Weighted SS loss','Loss/ss_weighted')]
with PdfPages(OUT/'SS_search_dynamics_python.pdf') as pdf:
    for name,title,ylabel,key in plots:
        fig, ax = plt.subplots(figsize=(9,5.5))
        fig.subplots_adjust(left=.13,right=.97,bottom=.15,top=.73)
        fig.text(.13,.95,title,fontsize=16,weight='bold',va='top')
        fig.text(.13,.88,'Search-only SS; seed 0; epoch averages; no smoothing',fontsize=10,color='#626C70')
        if key.startswith('layers'):
            data = train if key=='layers_train' else val
            for i,(idx,color,style) in enumerate(zip([3,5,7,9,11],['#356E73','#557CA5','#9071A8','#B58A46','#616A73'],['-','--',':','-.',(0,(5,2))])):
                ax.plot([r['epoch'] for r in data],[r[f'Loss/ss_search_layer_{idx}'] for r in data],
                    color=color,ls=style,lw=1.7,marker='o' if data is val else None,ms=3,label=f'Before layer {idx+1}')
            ax.set_ylim(bottom=0)
            handles,labels=ax.get_legend_handles_labels()
            fig.legend(handles,labels,loc='upper right',bbox_to_anchor=(.98,.83),ncol=3,fontsize=9)
        else:
            for data,color,style,label in [(train,'#356E73','-','Training (every epoch)'),(val,'#B36B43','--','Validation (every 5 epochs)')]:
                scale=100 if key=='IoU' else 1
                ax.plot([r['epoch'] for r in data],[scale*r[key] for r in data],color=color,ls=style,lw=1.8,
                    marker='o' if data is val else None,ms=3,label=label)
            handles,labels=ax.get_legend_handles_labels()
            fig.legend(handles,labels,loc='upper right',bbox_to_anchor=(.98,.82),ncol=2,fontsize=9)
        ax.set(xlabel='Epoch',ylabel=ylabel,xlim=(0,61))
        ax.set_xticks([1,10,20,30,40,50,60])
        ax.ticklabel_format(axis='y',style='plain',useOffset=False)
        fig.canvas.draw()
        require_matplotlib_panel_alignment(fig,json_out=str(OUT/f'{name}.alignment.json'),strict=True)
        fig.savefig(OUT/f'{name}.svg')
        fig.savefig(OUT/f'{name}.pdf')
        fig.savefig(OUT/f'{name}.png',dpi=300)
        fig.savefig(OUT/f'{name}_preview.png',dpi=300)
        pdf.savefig(fig)
        plt.close(fig)
print('Exported 10 plots and combined PDF')
