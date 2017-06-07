##### functions #####
options(warn=-1)

### read in pwm/bamm file
read_pwm <- function(pwm_file, pwm_order, read_order){
  values = scan(file=pwm_file, what = "numeric",strip.white = TRUE,quiet = TRUE, blank.lines.skip = TRUE)
  range = c(1:(pwm_order+1))
  values_per_position = cumsum(4^range)[pwm_order+1]
  pwm_length = length(values)/values_per_position
  offset = 1
  if(read_order > 0){
    offset = cumsum(4^range)[read_order]+1
  }
  pwm = c()
  for( i in 0:(pwm_length-1)){
    position = rbind(as.numeric(values[(i*values_per_position+1):(i*values_per_position+4^(read_order+1))]))
    pwm = rbind(pwm,position)
  }
  return(pwm)
}

### read in background model
read_bg <- function(bg_file, read_order, len){
  values = scan(file = bg_file, skip = (2+read_order), nlines=1, quiet=TRUE)
  bg = matrix(rep(values,len),ncol = 4^(read_order+1), byrow=TRUE)
  return(bg)
}

### calculate distance between pwm to background
get_min_dist_bg<- function(pwm,bg,pwm_log_pwm,bg_log_bg){
  avg = (pwm + bg ) / 2
  dist = 0.5 * sum(pwm_log_pwm + bg_log_bg - 2* avg * log2(avg))
  return(dist)
}
### calculate distance between pwm to background
get_dist_bg<- function(pwm,bg,pwm_log_pwm,bg_log_bg){
  avg = (pwm + bg ) / 2
  dist = 0.5 * rowSums(pwm_log_pwm + bg_log_bg - 2* avg * log2(avg))
  return(dist)
}

### calculate minimum distance between two pwms
get_min_dist_p_q <- function(p, plogp, q, qlogq, min_overlap){
  min_d = 10e6
  min_W = 0
  min_off_p = 0
  min_off_q = 0

  len_p = dim(p)[1]
  len_q = dim(q)[1]
  max_ol = min(len_p,len_q)
  min_ol = min(len_p,len_q,min_overlap)

  for( off_p in 0:(len_p-min_ol)){
    len_ol = min(max_ol, len_p-off_p)
    distance = calc_pwm_dist(p,q,off_p,0,len_ol, plogp,qlogq)
    if( distance < min_d ){
      min_d = distance
      min_W = len_ol
      min_off_p = off_p
    }
  }
  for( off_q in 0:(len_q-min_ol)){
    len_ol = min(max_ol, len_q-off_q)
    distance = calc_pwm_dist(p,q,0,off_q,len_ol,plogp, qlogq)
    if( distance < min_d ){
      min_d = distance
      min_W = len_ol
      min_off_p = 0
      min_off_q = off_q
    }
  }

  info = c(min_d, min_W, min_off_p, min_off_q)
  names(info)<- c("dist", "W", "off_p","off_q")
  return(info)
}

### calcaulate distance between 2 pwms
calc_pwm_dist <- function(p,q, off_p,off_q,len_ol, plogp, qlogq){
  ol = c(1:len_ol)
  avg = (p[off_p + ol,] + q[off_q + ol,])/2
  distance = sum(plogp[off_p + ol,] + qlogq[off_q+ol,] - 2 * avg * log2(avg))
  return(distance)
}

### get score for motif - db comparison
get_Scores <- function(pwm,pwm_log_pwm, bg, bg_log_bg, db_folder, db_order, read_order, alpha, min_overlap, p_bg_dist, p_rev_bg_dist, pwm_rev, pwm_rev_log_pwm_rev){
  scores = c()
  names = c()
  db_files = list.files( path = db_folder, full.names=TRUE, pattern = ".ihbcp", recursive = TRUE)
  for(db_file in db_files){
    pwm_db = read_pwm(db_file, db_order, read_order)
    pwm_db_log_pwm_db = pwm_db * log2(pwm_db)
    if(dim(pwm_db)[1] != dim(bg)[1]){
      bg = matrix(rep(bg[1,],dim(pwm_db)[1]),ncol = 4^(read_order+1), byrow=TRUE)
      bg_log_bg = bg * log2(bg)
    }
    q_bg_dist    = get_dist_bg(  pwm_db, bg, pwm_db_log_pwm_db, bg_log_bg)
    p_q_info     = get_min_dist_p_q( pwm, pwm_log_pwm, pwm_db, pwm_db_log_pwm_db, min_overlap)
    p_rev_q_info = get_min_dist_p_q( pwm_rev, pwm_rev_log_pwm_rev, pwm_db, pwm_db_log_pwm_db, min_overlap)

    if(p_q_info["dist"]<p_rev_q_info["dist"]){
      q_bg = sum(q_bg_dist[p_q_info["off_q"]:(p_q_info["off_q"]+p_q_info["W"]-1)])
      p_bg = sum(p_bg_dist[p_q_info["off_p"]:(p_q_info["off_p"]+p_q_info["W"]-1)])
      s_p_q = alpha * (p_bg +q_bg)  - p_q_info["dist"]
      line = c(s_p_q, p_q_info["dist"], p_q_info["W"], q_bg, p_bg )
    }else{
      q_bg = sum(q_bg_dist[p_rev_q_info["off_q"]:(p_rev_q_info["off_q"]+p_rev_q_info["W"]-1)])
      p_bg = sum(p_bg_dist[p_rev_q_info["off_p"]:(p_rev_q_info["off_p"]+p_rev_q_info["W"]-1)])

      s_p_q = alpha * (p_bg + q_bg) - p_rev_q_info["dist"]
      line = c(s_p_q, p_rev_q_info["dist"],p_rev_q_info["W"], q_bg, p_bg )
    }
    names = c(names, "Name"= paste(unlist(strsplit(basename(db_file),"_"))[1], collapse="_"))
    scores = rbind(scores, line)
  }
  row.names(scores)<- names
  colnames(scores)<- c("score", "q_p", "W", "q_bg", "p_bg")
  return(scores)
}

## calculate p- and e-value based on shuffled score distribution
calculate_p_and_e_value <- function(info_real, info_fake, e){

  info_real = cbind(info_real,
                    "FP"=rep(0,dim(info_real)[1]),
                    "Sl_higher"= sapply(info_real[,"score"], FUN = function(x){min(info_fake[info_fake[,"score"]>=x,"score"])}),
                    "Sl_lower" = sapply(info_real[,"score"], FUN = function(x){max(info_fake[info_fake[,"score"]<=x,"score"])}) )
  info_fake = cbind(info_fake, "FP"=rep(1,dim(info_fake)[1]),
                    "Sl_higher" = rep(NA, dim(info_fake)[1]),
                    "Sl_lower"  = rep(NA, dim(info_fake)[1]))
  info_fake = info_fake[order(info_fake[,"score"]),]

  info_all = rbind(info_real,info_fake)
  info_all = info_all[order(info_all[,"score"], decreasing = TRUE),]
  info_all = cbind(info_all, "FPl"=cumsum(info_all[,"FP"]))

  info_all = info_all[info_all[,"FP"] == 0,]
  Nminus = dim(info_fake)[1]
  info_all = cbind(info_all, "p-value"=(info_all[,"FPl"]/Nminus) + (1/Nminus) * (info_all[,"Sl_higher"] - info_all[,"score"] + e) / ( info_all[, "Sl_higher"] - info_all[,"Sl_lower"] + e))

  ntop = min(100, (0.1*Nminus))
  lambda = (1/ntop) * sum (info_fake[1:ntop,"score"] - info_fake[ntop,"score"])
  for(i in c(which(info_all[,"Sl_higher"] == Inf))){
    # Sl_higher not defined
    ### ! the exponent should be negative! the actual formular does not take the abs() --> discuss with johannes!
    info_all[i,"p-value"] = (ntop/Nminus)*exp(-abs((info_all[i,"score"] - info_fake[ntop,"score"])/lambda))
  }
  for(i in c(which(is.na(info_all[,"Sl_lower"])))){
    # Sl_lower is not defined
    info_all[i,"p-value"] = 1
  }

  info_all = cbind(info_all, "e-value"=info_all[,"p-value"]*dim(info_real)[1])

  return(info_all)

}

# shuffle pwm is a localized fashion
shuffle_pwm <- function(pwm){
  j = c(1:dim(pwm)[1])
  Rj = -j +2*rnorm(dim(pwm)[1],0,1)
  return(pwm[order(Rj, decreasing = TRUE),])
}


#######################################################
#### BaMM-compare for finding motif-motif matches
#######################################################

# example parameter settings
pwm_order            = 4
db_order             = 4
read_order           = 0
shuffle_times        = 10
p_val_limit          = 0.01
db_folder = '/home/kiesel/Desktop/TomTomTool/Results'
pwm_file = '/home/kiesel/Desktop/TomTomTool/Results/wgEncodeUwTfbsHcmCtcfStdAlnRep0_summits125/wgEncodeUwTfbsHcmCtcfStdAlnRep0_summits125_motif_1.ihbcp'


args <- commandArgs(trailingOnly = TRUE)
splits <- strsplit(args,split='=')
for(split in splits) {
       if(split[1] == '--p_val_limit'  ){p_val_limit_in   <- split[2]}
  else if(split[1] == '--shuffle_times'){shuffle_times_in <- split[2]}
  else if(split[1] == '--read_order'   ){read_order_in    <- split[2]}
  else if(split[1] == '--db_order'     ){db_order_in      <- split[2]}
  else if(split[1] == '--order'        ){order_in         <- split[2]}
  else if(split[1] == '--query'        ){query_in         <- split[2]}
  else if(split[1] == '--bg'           ){bg_in            <- split[2]}
  else if(split[1] == '--db_folder'    ){db_folder        <- split[2]}
}

  p_val_limit   = as.numeric(p_val_limit_in)
  shuffle_times = as.numeric(shuffle_times_in)
  read_order    = as.numeric(read_order_in)
  db_order      = as.numeric(db_order_in)
  pwm_order     = as.numeric(order_in)
  pwm_file      = query_in
  bg_file       = bg_in

  alpha        = 0.6
  min_overlap  = 4
  e            = 1e-5

  # get real scores (inclusive reverseComplement)

  pwm                 = read_pwm(pwm_file, pwm_order, read_order)
  pwm_log_pwm         = pwm *log2(pwm)
  bg                  = read_bg(bg_file, read_order, dim(pwm)[1])
  bg_log_bg           = bg *log2(bg)
  p_bg_dist           = get_dist_bg( pwm, bg, pwm_log_pwm, bg_log_bg)
  pwm_rev             = pwm[dim(pwm)[1]:1,dim(pwm)[2]:1]
  pwm_rev_log_pwm_rev = pwm_rev * log2(pwm_rev)
  p_rev_bg_dist       = get_dist_bg( pwm_rev, bg, pwm_rev_log_pwm_rev, bg_log_bg)

  info_real = get_Scores(pwm,pwm_log_pwm,bg, bg_log_bg, db_folder, db_order, read_order, alpha, min_overlap, p_bg_dist, p_rev_bg_dist, pwm_rev, pwm_rev_log_pwm_rev)

  # get background scores on shuffled pwms (inclusive reverseComplement)

  info_fake = c()
  info_mean = matrix(0, nrow=dim(info_real)[1], ncol=dim(info_real)[2])
  for( x in 1:shuffle_times ){
    shuff                   = shuffle_pwm(pwm) #pwm[sample(1:dim(pwm)[1]),]
    shuff_log_shuff         = shuff * log2( shuff )
    shuff_rev               = shuff[dim(shuff)[1]:1,dim(shuff)[2]:1]
    shuff_rev_log_shuff_rev = shuff_rev * log2(shuff_rev)

    info_shuffle = get_Scores(shuff,shuff_log_shuff,bg, bg_log_bg, db_folder, db_order, read_order, alpha, min_overlap, p_bg_dist, p_rev_bg_dist, shuff_rev, shuff_rev_log_shuff_rev)
    info_fake    = rbind(info_fake, info_shuffle)
    info_mean    = info_mean + info_shuffle
  }
  info_mean = info_mean / shuffle_times

  # calculate p_value and e_value and extrac matches above p-val limit

  info_real    = calculate_p_and_e_value(info_real, info_fake , e)
  best_matches = info_real[which(info_real[,"p-value"]<= p_val_limit),]

  # output results
  if(dim(best_matches)[1] == 0){
    message('no matches!')
  }else{
    for(i in c(1:dim(best_matches)[1])){
      message(rownames(best_matches)[i] , ' ' , best_matches[i,"p-value"] , ' ' , best_matches[i,"e-value"] , ' ' , best_matches[i,"score"] , ' ' , best_matches[i,"W"])
    }
  }


