#!/usr/bin/env Rscript
# Evaluate one R expression per line of a TSV (id \t expr) and write id \t value.
# Values are %.17g decimals, or "inf", "-inf", "nan"; errors become "ERROR: ...".
# Driven by tools/gen_reference.py; not meant to be run by hand.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) stop("usage: gen_reference.R cases.tsv values.tsv")
lines <- readLines(args[1])
fmt <- function(v) {
  if (!is.numeric(v) || length(v) != 1) return(sprintf("ERROR: unexpected value of class %s length %d", class(v)[1], length(v)))
  if (is.na(v)) return("nan")
  if (is.infinite(v)) return(if (v > 0) "inf" else "-inf")
  sprintf("%.17g", v)
}
out <- character(length(lines) + 1)
out[1] <- paste("#R", R.version$major, R.version$minor, sep = "\t")
for (i in seq_along(lines)) {
  parts <- strsplit(lines[i], "\t", fixed = TRUE)[[1]]
  val <- tryCatch(suppressWarnings(eval(parse(text = parts[2]))),
                  error = function(e) paste("ERROR:", conditionMessage(e)))
  out[i + 1] <- paste(parts[1], if (is.character(val)) val else fmt(val), sep = "\t")
}
writeLines(out, args[2])
