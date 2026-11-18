# Observed epoch averages from one search-only training run, seed 0.
# No smoothing, resampling, uncertainty intervals, or baseline comparison.
args <- commandArgs(trailingOnly=TRUE)
out <- if(length(args)) args[1] else '.'
d <- read.csv(file.path(out,'epoch_metrics.csv'),check.names=FALSE)
t <- d[d$split=='train',]; v <- d[d$split=='val',]
stopifnot(nrow(t)==60,nrow(v)==12,all(is.finite(d$IoU)))
d$tracking <- d[['Loss/total']] - d[['Loss/ss_weighted']]
d$ratio <- 100*d[['Loss/ss_weighted']]/d[['Loss/total']]
t <- d[d$split=='train',]; v <- d[d$split=='val',]
cols <- c('#356E73','#B36B43')
lcols <- c('#356E73','#557CA5','#9071A8','#B58A46','#616A73')
# Separate single-panel figures: panel alignment is not applicable.
# 9 x 5.5 inch slide/report output; ordinary text at least 10 pt.
setup <- function(title,yl,ylim){
 par(mar=c(4.5,5.2,4.7,1.3),mgp=c(3.1,.8,0),family='Arial',cex=1,
     cex.axis=.9,cex.lab=1,lwd=1,bty='l',las=1)
 plot(NA,xlim=c(1,60),ylim=ylim,xlab='Epoch',ylab=yl,xaxt='n')
 axis(1,at=c(1,10,20,30,40,50,60))
 abline(h=axTicks(2),col='#E8ECEE',lwd=.6)
 title(main=title,adj=0,line=2.8,cex.main=1.2)
 mtext('Search-only SS ; seed 0; epoch averages; no smoothing',side=3,line=1.2,adj=0,cex=.8,col='#626C70')
}
range_pad <- function(x){r<-range(x);p<-diff(r)*.12;if(p==0)p<-.01;c(max(0,r[1]-p),r[2]+p)}
pair <- function(key,title,yl,percent=FALSE){
 a<-t[[key]];b<-v[[key]];if(percent){a<-a*100;b<-b*100}
 setup(title,yl,range_pad(c(a,b)))
 lines(t$epoch,a,col=cols[1],lwd=2)
 lines(v$epoch,b,col=cols[2],lwd=2,lty=2)
 points(v$epoch,b,col=cols[2],pch=16,cex=.6)
 legend('topright',legend=c('Training (every epoch)','Validation (every 5 epochs)'),col=cols,lty=c(1,2),lwd=2,bty='n',cex=.85)
}
layerplot <- function(z,title){
 keys<-paste0('Loss/ss_search_layer_',c(3,5,7,9,11))
 setup(title,'Unweighted search SS (MSE)',c(0,max(unlist(z[keys]))*1.2))
 for(i in seq_along(keys)) {lines(z$epoch,z[[keys[i]]],col=lcols[i],lwd=1.8,lty=i);if(z$split[1]=='val')points(z$epoch,z[[keys[i]]],col=lcols[i],pch=15+i,cex=.5)}
 legend('topright',legend=paste('Before layer',c(4,6,8,10,12)),col=lcols,lty=1:5,lwd=1.8,bty='n',cex=.8,ncol=2)
}
plots<-list(
 '01_search_ss'=function()pair('Loss/ss_search','Search SS: training and validation','Unweighted search SS (MSE)'),
 '02_tracking_loss'=function()pair('tracking','Tracking objective during training','Tracking loss (total minus weighted SS)'),
 '03_iou'=function()pair('IoU','IoU during training and validation','Sampled crop IoU (%)',TRUE),
 '04_ss_contribution'=function()pair('ratio','Numerical contribution of SS to total loss','Weighted SS / total loss (%)'),
 '05_layers_train'=function()layerplot(t,'Layer-wise search SS: training'),
 '06_layers_val'=function()layerplot(v,'Layer-wise search SS: validation'),
 '07_giou'=function()pair('Loss/giou','GIoU loss during training','GIoU loss (before coefficient 2)'),
 '08_l1'=function()pair('Loss/l1','Box L1 loss during training','L1 loss (before coefficient 5)'),
 '09_location'=function()pair('Loss/location','Location loss during training','Location loss'),
 '10_weighted_ss'=function()pair('Loss/ss_weighted','Weighted SS during training','Weighted SS loss'))
for(n in names(plots)){
 cairo_pdf(file.path(out,paste0(n,'.pdf')),width=9,height=5.5,pointsize=12,family='Arial');plots[[n]]();dev.off()
 if(requireNamespace('svglite',quietly=TRUE)){svglite::svglite(file.path(out,paste0(n,'.svg')),width=9,height=5.5,pointsize=12);plots[[n]]();dev.off()}
 png(file.path(out,paste0(n,'.png')),width=2700,height=1650,res=300,type='cairo',pointsize=12);plots[[n]]();dev.off()
}
cairo_pdf(file.path(out,'SS_search_dynamics.pdf'),width=9,height=5.5,pointsize=12)
for(f in plots) f()
dev.off()
