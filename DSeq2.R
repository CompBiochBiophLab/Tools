#BiocManager::install("pasilla")
library("pasilla")



#browseVignettes("pasilla")
dataFilesDir = system.file("/Users/mariagiovanna/BarcellonaUviC", package = "pasilla", mustWork=TRUE)
pasillaSampleAnno = read.csv(file.path(dataFilesDir, "pasilla_sample_annotation.csv"))
pasillaSampleAnno

dataFilesDir = system.file("/Users/mariagiovanna/BarcellonaUviC", package = "pasilla", mustWork=TRUE)
pasillaSampleAnno = read.csv(file.path(dataFilesDir, "GSE160306_human_retina_DR_totalRNA_counts.txt"))
pasillaSampleAnno

pasCts <- system.file("./",
                      "GSE160306_human_retina_DR_totalRNA_counts.txt",
                      package="pasilla", mustWork=TRUE)
pasAnno <- system.file("extdata",
                       "/Users/mariagiovanna/BarcellonaUviC/gruppoexperimet2.csv",
                       package="pasilla", mustWork=TRUE)
cts <- as.matrix(read.csv(pasCts,sep="\t",row.names="gene_id"))
coldata <- read.csv(pasAnno, row.names=1)
coldata <- coldata[,c("condition","type")]
coldata$condition <- factor(coldata$condition)
coldata$type <- factor(coldata$type)

cron_rscript("~/my_cron_jobs/foo.R"
             system.file(system.file(package = "cronR", "extdata", "helloworld.R")
                        
             