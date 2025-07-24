//! Agent Name: rust-cli
//!
//! Part of the scjson project.
//! Developed by Softoboros Technology Inc.
//! Licensed under the BSD 1-Clause License.
//!
//! Command line interface for scjson conversions.

use clap::{Parser, Subcommand};
use scjson::{json_to_xml, xml_to_json};
use std::fs;
use std::path::{Path, PathBuf};

/// CLI arguments.
#[derive(Parser)]
#[command(name = "scjson", about = "SCXML <-> scjson converter and validator")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

/// Sub-commands supported by the CLI.
#[derive(Subcommand)]
enum Commands {
    /// Convert SCXML to scjson.
    Json {
        /// Input file or directory.
        path: PathBuf,
        /// Output file or directory.
        #[arg(short, long)]
        output: Option<PathBuf>,
        /// Recurse into directories.
        #[arg(short, long)]
        recursive: bool,
        /// Verify conversion without writing output.
        #[arg(short, long)]
        verify: bool,
        /// Keep null or empty items when producing JSON.
        #[arg(long)]
        keep_empty: bool,
    },
    /// Convert scjson to SCXML.
    Xml {
        /// Input file or directory.
        path: PathBuf,
        #[arg(short, long)]
        output: Option<PathBuf>,
        #[arg(short, long)]
        recursive: bool,
        #[arg(short, long)]
        verify: bool,
        #[arg(long)]
        keep_empty: bool,
    },
    /// Validate files by round-tripping them.
    Validate {
        /// File or directory path.
        path: PathBuf,
        /// Recurse into directories.
        #[arg(short, long)]
        recursive: bool,
    },
}

fn convert_scxml_file(src: &Path, dest: Option<&Path>, verify: bool, keep_empty: bool) {
    let xml = fs::read_to_string(src).expect("read xml");
    match xml_to_json(&xml, !keep_empty) {
        Ok(json) => {
            if verify {
                if json_to_xml(&json, true).is_ok() {
                    println!("Verified {}", src.display());
                } else {
                    eprintln!("Failed to verify {}", src.display());
                }
            } else if let Some(d) = dest {
                if let Some(parent) = d.parent() {
                    fs::create_dir_all(parent).ok();
                }
                fs::write(d, json).expect("write json");
                println!("Wrote {}", d.display());
            }
        }
        Err(e) => eprintln!("Failed to convert {}: {}", src.display(), e),
    }
}

/// Convert a scjson file to SCXML.
///
/// # Parameters
/// - `src`: Source JSON file path.
/// - `dest`: Optional output file path.
/// - `verify`: When `true`, only validate the round trip.
/// - `keep_empty`: Preserve empty fields when `true`.
fn convert_scjson_file(src: &Path, dest: Option<&Path>, verify: bool, keep_empty: bool) {
    let json = fs::read_to_string(src).expect("read json");
    match json_to_xml(&json, !keep_empty) {
        Ok(xml) => {
            if verify {
                if xml_to_json(&xml, true).is_ok() {
                    println!("Verified {}", src.display());
                } else {
                    eprintln!("Failed to verify {}", src.display());
                }
            } else if let Some(d) = dest {
                if let Some(parent) = d.parent() {
                    fs::create_dir_all(parent).ok();
                }
                fs::write(d, xml).expect("write xml");
                println!("Wrote {}", d.display());
            }
        }
        Err(e) => eprintln!("Failed to convert {}: {}", src.display(), e),
    }
}

fn convert_directory<F>(dir: &Path, output: &Path, pattern: &str, recursive: bool, func: F)
where
    F: Fn(&Path, Option<&Path>, bool, bool),
{
    let glob_pattern = if recursive {
        format!("**/{}", pattern)
    } else {
        pattern.to_string()
    };
    for entry in glob::glob(&format!("{}/{}", dir.display(), glob_pattern))
        .unwrap()
        .filter_map(Result::ok)
    {
        if entry.is_file() {
            let rel = entry.strip_prefix(dir).unwrap();
            let dest = output
                .join(rel)
                .with_extension(if pattern.ends_with("scxml") {
                    "scjson"
                } else {
                    "scxml"
                });
            func(&entry, Some(&dest), false, false);
        }
    }
}

fn validate_file(path: &Path) -> bool {
    let data = fs::read_to_string(path).expect("read file");
    let res = if path.extension().and_then(|s| s.to_str()) == Some("scxml") {
        xml_to_json(&data, true).and_then(|j| json_to_xml(&j, true))
    } else if path.extension().and_then(|s| s.to_str()) == Some("scjson") {
        json_to_xml(&data, true).and_then(|x| xml_to_json(&x, true))
    } else {
        return true;
    };
    if res.is_err() {
        eprintln!("Validation failed for {}", path.display());
        false
    } else {
        true
    }
}

fn main() {
    let cli = Cli::parse();
    match cli.command {
        Commands::Json {
            path,
            output,
            recursive,
            verify,
            keep_empty,
        } => {
            if path.is_dir() {
                let out = output.as_deref().unwrap_or(&path);
                convert_directory(&path, out, "*.scxml", recursive, |s, d, _, _| {
                    convert_scxml_file(s, d, verify, keep_empty)
                });
            } else {
                let dest = output
                    .clone()
                    .unwrap_or_else(|| path.with_extension("scjson"));
                convert_scxml_file(&path, Some(&dest), verify, keep_empty);
            }
        }
        Commands::Xml {
            path,
            output,
            recursive,
            verify,
            keep_empty,
        } => {
            if path.is_dir() {
                let out = output.as_deref().unwrap_or(&path);
                convert_directory(&path, out, "*.scjson", recursive, |s, d, _, _| {
                    convert_scjson_file(s, d, verify, keep_empty)
                });
            } else {
                let dest = output
                    .clone()
                    .unwrap_or_else(|| path.with_extension("scxml"));
                convert_scjson_file(&path, Some(&dest), verify, keep_empty);
            }
        }
        Commands::Validate { path, recursive } => {
            let mut success = true;
            if path.is_dir() {
                let pattern = if recursive { "**/*" } else { "*" };
                for entry in glob::glob(&format!("{}/{}", path.display(), pattern))
                    .unwrap()
                    .filter_map(Result::ok)
                {
                    if entry.is_file() {
                        if !validate_file(&entry) {
                            success = false;
                        }
                    }
                }
            } else {
                success = validate_file(&path);
            }
            if !success {
                std::process::exit(1);
            }
        }
    }
}
