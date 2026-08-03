#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
only <- ""
if (length(args) >= 2 && args[[1]] == "--only") only <- args[[2]]

script_arg <- commandArgs(trailingOnly = FALSE)
script_path <- sub("^--file=", "", script_arg[grepl("^--file=", script_arg)])
root <- normalizePath(file.path(dirname(script_path), ".."), winslash = "/", mustWork = TRUE)
system_name <- unname(Sys.info()[["sysname"]])
machine_name <- tolower(unname(Sys.info()[["machine"]]))
system_key <- switch(system_name, Darwin = "macos", Linux = "linux", Windows = "windows",
                     tolower(system_name))
machine_key <- gsub("x86-64", "x86_64", machine_name, fixed = TRUE)
if (machine_key %in% c("arm64", "aarch64")) machine_key <- "arm64"
if (system_key == "windows" && machine_key %in% c("amd64", "x86_64")) machine_key <- "amd64"
platform_key <- Sys.getenv("ACCUDIST_ORACLE_PLATFORM", paste(system_key, machine_key, sep = "-"))
python <- Sys.which("python3")
if (!nzchar(python)) python <- Sys.which("python")
if (!nzchar(python)) stop("Python is required to read functions.toml")

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
bridge_dir <- normalizePath(bridge_dir, winslash = "/", mustWork = TRUE)
bridge_source <- file.path(bridge_dir, "reference_bridge.c", fsep = "/")
bridge_template <- file.path(root, "tools", "reference_bridge.c", fsep = "/")
if (!file.copy(bridge_template, bridge_source)) stop("failed to copy reference bridge")
bridge_source <- normalizePath(bridge_source, winslash = "/", mustWork = TRUE)
bridge <- file.path(
  bridge_dir,
  paste0("reference_bridge", .Platform$dynlib.ext),
  fsep = "/"
)
compile <- system2(
  file.path(R.home("bin"), "R"),
  c("CMD", "SHLIB", "-o", shQuote(bridge), shQuote(bridge_source)),
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
data_dir <- file.path(root, "tests", "data", platform_key)
dir.create(data_dir, recursive = TRUE, showWarnings = FALSE)
for (name in names(groups)) {
  output <- file.path(data_dir, paste0(name, ".jsonl"))
  lines <- sprintf('{"meta":{"r_version":"%s","platform":"%s","function":"%s"}}',
                   getRversion(), platform_key, name)
  for (row in groups[[name]]) {
    fields <- strsplit(row, "\t", fixed = TRUE)[[1]]
    value <- suppressWarnings(eval(parse(text = fields[[4]]), envir = globalenv()))
    encoded_hex <- if (length(value) == 1) {
      sprintf('"%s"', hex_double(value))
    } else {
      paste0('[', paste(sprintf('"%s"', vapply(value, hex_double, "")), collapse = ','), ']')
    }
    lines <- c(lines, sprintf('{"args":%s,"kwargs":%s,"hex":%s}',
                              fields[[2]], fields[[3]], encoded_hex))
  }
  writeLines(lines, output, useBytes = TRUE)
  cat(sprintf("wrote %d %s vectors to %s\n", length(lines) - 1, name, output))
}
