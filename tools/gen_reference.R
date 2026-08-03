#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
only <- "ppois"
if (length(args) >= 2 && args[[1]] == "--only") only <- args[[2]]
if (only != "ppois") stop("M1 reference generator only supports ppois")

script_arg <- commandArgs(trailingOnly = FALSE)
script_path <- sub("^--file=", "", script_arg[grepl("^--file=", script_arg)])
root <- normalizePath(file.path(dirname(script_path), ".."))
output <- file.path(root, "tests", "data", "ppois.jsonl")

q_values <- c(
  -1, 0, 1e-12, 0.499999999, 0.5, 0.500000001, 1, 2, 5, 10,
  20, 50, 100, 200, 500, 900, 1000, 10000, 100000, 1000000
)
lambda_values <- c(-1, 1e-10, 0.1, 10, 1e10)

hex_double <- function(value) {
  bytes <- writeBin(as.double(value), raw(), size = 8, endian = "big")
  paste0("0x", paste(sprintf("%02x", as.integer(bytes)), collapse = ""))
}

number <- function(value) sprintf("%.17g", value)
lines <- c(sprintf('{"meta":{"r_version":"%s","function":"ppois"}}', getRversion()))
for (q in q_values) {
  for (lambda in lambda_values) {
    for (lower_tail in c(FALSE, TRUE)) {
      for (log_p in c(FALSE, TRUE)) {
        value <- suppressWarnings(ppois(q, lambda, lower.tail = lower_tail, log.p = log_p))
        lines <- c(
          lines,
          sprintf(
            '{"args":[%s,%s],"lower_tail":%d,"log":%d,"hex":"%s"}',
            number(q), number(lambda), as.integer(lower_tail), as.integer(log_p),
            hex_double(value)
          )
        )
      }
    }
  }
}
writeLines(lines, output, useBytes = TRUE)
cat(sprintf("wrote %d ppois vectors to %s\n", length(lines) - 1, output))

