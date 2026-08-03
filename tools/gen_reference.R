#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
only <- ""
if (length(args) >= 2 && args[[1]] == "--only") only <- args[[2]]

script_arg <- commandArgs(trailingOnly = FALSE)
script_path <- sub("^--file=", "", script_arg[grepl("^--file=", script_arg)])
root <- normalizePath(file.path(dirname(script_path), ".."))
python <- Sys.which("python3")
if (!nzchar(python)) stop("python3 is required to read functions.toml")

plan <- tempfile(fileext = ".tsv")
plan_args <- file.path(root, "tools", "reference_plan.py")
if (nzchar(only)) plan_args <- c(plan_args, "--only", only)
status <- system2(
  python,
  plan_args,
  stdout = plan
)
if (status != 0) stop("reference plan generation failed")

bridge_dir <- tempfile(pattern = "accudist-reference-")
dir.create(bridge_dir)
bridge_source <- file.path(bridge_dir, "reference_bridge.c")
file.copy(file.path(root, "tools", "reference_bridge.c"), bridge_source)
bridge <- file.path(bridge_dir, paste0("reference_bridge", .Platform$dynlib.ext))
compile <- system2(
  file.path(R.home("bin"), "R"),
  c("CMD", "SHLIB", "-o", bridge, bridge_source),
  stdout = TRUE,
  stderr = TRUE
)
if (!file.exists(bridge)) stop(paste(compile, collapse = "\n"))
dyn.load(bridge)
on.exit(dyn.unload(bridge), add = TRUE)

hex_double <- function(value) {
  bytes <- writeBin(as.double(value), raw(), size = 8, endian = "big")
  paste0("0x", paste(sprintf("%02x", as.integer(bytes)), collapse = ""))
}

rows <- readLines(plan, warn = FALSE)
groups <- split(rows, vapply(strsplit(rows, "\t", fixed = TRUE), `[[`, "", 1))
dir.create(file.path(root, "tests", "data"), recursive = TRUE, showWarnings = FALSE)
for (name in names(groups)) {
  output <- file.path(root, "tests", "data", paste0(name, ".jsonl"))
  lines <- sprintf('{"meta":{"r_version":"%s","function":"%s"}}', getRversion(), name)
  for (row in groups[[name]]) {
    fields <- strsplit(row, "\t", fixed = TRUE)[[1]]
    value <- suppressWarnings(eval(parse(text = fields[[4]]), envir = globalenv()))
    lines <- c(lines, sprintf('{"args":%s,"kwargs":%s,"hex":"%s"}',
                              fields[[2]], fields[[3]], hex_double(value)))
  }
  writeLines(lines, output, useBytes = TRUE)
  cat(sprintf("wrote %d %s vectors to %s\n", length(lines) - 1, name, output))
}
