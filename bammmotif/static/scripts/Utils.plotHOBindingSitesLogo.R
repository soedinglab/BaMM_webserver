#...............................................................................
#
# Documentations
#...............................................................................

# Job
# * Plot higher-order sequence logo(s) from interpolated Markov model
#   (conditional) probabilities and frequencies.
#
# Results
# * Higher-order sequence logo(s) (.pdf)


#...............................................................................
#
# Libraries
#...............................................................................

library( grid )

#...............................................................................
#
# Sources
#...............................................................................
args <- commandArgs(trailingOnly = TRUE)
splits <- strsplit(args,split='=')
for(split in splits) { 
  if(split[1] == '--output_dir') {output_dir_in <- split[2]}
  else if(split[1] == '--file_name'){file_name_in  <- split[2]}
  else if(split[1] == '--order') {order_in<- split[2]}
}

source( "/code/bammmotif/static/scripts/Utils.plotHOLogo.R" )
#source( "/home/kiesel/Desktop/BaMM_webserver/bammmotif/static/scripts/Utils.plotHOLogo.R" )

#...............................................................................
#
# Parameters
#...............................................................................

# interpolated Markov model directory
dir <- output_dir_in

# interpolated Markov model file name without ending
# probabilities (.probs) mandatory
# conditional probabilities (.conds) and background frequencies (.freqs) by
# choice
file.name <- file_name_in

# background sequence logo
bg <- FALSE

# specify higher-order logo(s) (max. order: 5)
order <- order_in
# use background (instead of uniformely distributed) nucleotide frequencies for
# 0th-order 1-mer contributions (unapplicable for background sequence logos)
useFreqs <- FALSE
# logarithm base to use in calculating k-mer contributions
base <- 2

# information content (instead of probability) column scaling
icColumnScale <- TRUE
# information content (instead of probability) letter scaling
icLetterScale <- TRUE
# icLetterScale and not icColumnScale is not implemented

# further logo display parameters
xaxis <- TRUE
yaxis <- TRUE
xfontsize <- 15
yfontsize <- 15
alpha <- .3 # icLetterScale only

# additional plot 0th order revcomp
revComp = TRUE

# add 0th order stamp plots
stamp = TRUE
plot_title = TRUE

# .pdf parameters
#width <- 7

# .png parameters
width <- 1200
height <- 800
#...............................................................................
#
# Plot higher-order sequence logo(s)
#...............................................................................

if( bg ){
    pdf( file.path( dir, paste( file.name, "-bg-logo-order-", paste( order,
         collapse="-" ), ifelse( icColumnScale, "-icColumnScale", "" ), ifelse(
         icLetterScale, "-icLetterScale", "" ), ".pdf", sep="" ) ) )
    hoBgSeqLogo( file.name=file.path( dir, file.name ), order=order, base=base,
                 icColumnScale=icColumnScale, icLetterScale=icLetterScale,
                 xaxis=xaxis, yaxis=yaxis, xfontsize=xfontsize,
                 yfontsize=yfontsize, alpha=alpha )
} else{
  png( file.path( dir, paste( file.name, "-logo-order-", paste( order,
       collapse="-" ), ifelse( useFreqs, "-freqs", "" ), ifelse(
       icColumnScale, "-icColumnScale", "" ), ifelse( icLetterScale,
       "-icLetterScale", "" ), ".png", sep="" ) ), width=width , height=height)

  #pdf( file.path( dir, paste( file.name, "-logo-order-", paste( order,
  #       collapse="-" ), ifelse( useFreqs, "-freqs", "" ), ifelse(
  #       icColumnScale, "-icColumnScale", "" ), ifelse( icLetterScale,
  #       "-icLetterScale", "" ), ".pdf", sep="" ) ), width=width )
    hoSeqLogo( file.name=file.path( dir, file.name ), order=order,
               useFreqs=useFreqs, base=base, icColumnScale=icColumnScale,
               icLetterScale=icLetterScale, xaxis=xaxis, yaxis=yaxis,
               xfontsize=xfontsize, yfontsize=yfontsize, alpha=alpha, cex=4, lwd=4 ,revComp=FALSE, plot_title=plot_title)
}
dev.off()

if(revComp && order == 0){
  png( file.path( dir, paste( file.name, "-logo-order-", paste( order,
       collapse="-" ), ifelse( useFreqs, "-freqs", "" ), ifelse(
       icColumnScale, "-icColumnScale", "" ), ifelse( icLetterScale,
       "-icLetterScale", "" ), "-revComp.png", sep="" ) ), width=width , height=height)
  
  hoSeqLogo( file.name=file.path( dir, file.name ), order=order,
             useFreqs=useFreqs, base=base, icColumnScale=icColumnScale,
             icLetterScale=icLetterScale, xaxis=xaxis, yaxis=yaxis,
             xfontsize=xfontsize, yfontsize=yfontsize, alpha=alpha, cex=4, lwd=4 ,revComp=TRUE, plot_title=plot_title)
  dev.off()
}
if(stamp && order == 0){
   width = 1000
   height = 500
  png( file.path( dir, paste( file.name, "-logo-order-", paste( order,
       collapse="-" ), ifelse( useFreqs, "-freqs", "" ), ifelse(
       icColumnScale, "-icColumnScale", "" ), ifelse( icLetterScale,
       "-icLetterScale", "" ), "_stamp.png", sep="" ) ), width=width , height=height)
  
  hoSeqLogo( file.name=file.path( dir, file.name ), order=order,
             useFreqs=useFreqs, base=base, icColumnScale=icColumnScale,
             icLetterScale=icLetterScale, xaxis=FALSE, yaxis=FALSE,
             xfontsize=xfontsize, yfontsize=yfontsize, alpha=alpha, cex=4, lwd=4 ,revComp=FALSE, plot_title=FALSE)
  dev.off()
             
  if(revComp){
  png( file.path( dir, paste( file.name, "-logo-order-", paste( order,
       collapse="-" ), ifelse( useFreqs, "-freqs", "" ), ifelse(
       icColumnScale, "-icColumnScale", "" ), ifelse( icLetterScale,
       "-icLetterScale", "" ), "-revComp_stamp.png", sep="" ) ), width=width , height=height)
  
  hoSeqLogo( file.name=file.path( dir, file.name ), order=order,
             useFreqs=useFreqs, base=base, icColumnScale=icColumnScale,
             icLetterScale=icLetterScale, xaxis=FALSE, yaxis=FALSE,
             xfontsize=xfontsize, yfontsize=yfontsize, alpha=alpha, cex=4, lwd=4 ,revComp=TRUE, plot_title=FALSE)
  dev.off()
  }
}


