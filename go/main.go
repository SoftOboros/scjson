/*
Agent Name: go-cli

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
*/

package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	cli "github.com/urfave/cli/v2"
)

// collectFiles gathers files with the provided extension under the root path.
//
// @param root string - directory to scan.
// @param extension string - file extension to match (including the dot).
// @param recursive bool - traverse subdirectories when true.
// @returns []string and error - matching file paths and failures.
func collectFiles(root, extension string, recursive bool) ([]string, error) {
	var files []string
	if recursive {
		err := filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return err
			}
			if info.IsDir() {
				return nil
			}
			if strings.EqualFold(filepath.Ext(path), extension) {
				files = append(files, path)
			}
			return nil
		})
		return files, err
	}
	entries, err := os.ReadDir(root)
	if err != nil {
		return nil, err
	}
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		if strings.EqualFold(filepath.Ext(entry.Name()), extension) {
			files = append(files, filepath.Join(root, entry.Name()))
		}
	}
	return files, nil
}

// convertScxmlFile converts a single SCXML file to scjson.
//
// @param src string - path to SCXML file.
// @param dest string - destination path.
// @param verify bool - verify only.
// @param keepEmpty bool - keep empty fields.
// @returns error - failure if any.
func convertScxmlFile(src, dest string, verify, keepEmpty bool) error {
	data, err := os.ReadFile(src)
	if err != nil {
		return err
	}
	jsonStr, err := xmlToJSON(string(data), !keepEmpty)
	if err != nil {
		return err
	}
	if verify {
		if _, err := jsonToXML(jsonStr); err != nil {
			return err
		}
		fmt.Printf("Verified %s\n", src)
		return nil
	}
	if dest == "" {
		dest = filepath.Join(filepath.Dir(src), filepath.Base(src[:len(src)-len(filepath.Ext(src))])+".scjson")
	}
	return writeFile(dest, jsonStr)
}

// convertScjsonFile converts a single scjson file to SCXML.
//
// @param src string - path to scjson file.
// @param dest string - destination path.
// @param verify bool - verify only.
// @returns error - failure if any.
func convertScjsonFile(src, dest string, verify bool) error {
	data, err := os.ReadFile(src)
	if err != nil {
		return err
	}
	xmlStr, err := jsonToXML(string(data))
	if err != nil {
		return err
	}
	if verify {
		if _, err := xmlToJSON(xmlStr, true); err != nil {
			return err
		}
		fmt.Printf("Verified %s\n", src)
		return nil
	}
	if dest == "" {
		dest = filepath.Join(filepath.Dir(src), filepath.Base(src[:len(src)-len(filepath.Ext(src))])+".scxml")
	}
	return writeFile(dest, xmlStr)
}

func main() {
	app := &cli.App{
		Name:  "scjson",
		Usage: "SCXML <-> scjson converter and validator",
	}

	app.Commands = []*cli.Command{
		{
			Name:  "json",
			Usage: "Convert SCXML to scjson",
			Flags: []cli.Flag{
				&cli.StringFlag{Name: "output", Aliases: []string{"o"}},
				&cli.BoolFlag{Name: "recursive", Aliases: []string{"r"}},
				&cli.BoolFlag{Name: "verify", Aliases: []string{"v"}},
				&cli.BoolFlag{Name: "keep-empty"},
			},
			Action: func(c *cli.Context) error {
				p := c.Args().First()
				if p == "" {
					return cli.Exit("path required", 1)
				}
				src, err := filepath.Abs(p)
				if err != nil {
					return err
				}
				out := c.String("output")
				recursive := c.Bool("recursive")
				verify := c.Bool("verify")
				keepEmpty := c.Bool("keep-empty")
				args := c.Args().Slice()
				for i := 0; i < len(args); i++ {
					arg := args[i]
					if !strings.HasPrefix(arg, "-") {
						continue
					}
					switch arg {
					case "-o", "--output":
						if i+1 < len(args) {
							out = args[i+1]
							i++
						}
					case "-r", "--recursive":
						recursive = true
					case "-v", "--verify":
						verify = true
					case "--keep-empty":
						keepEmpty = true
					}
				}
				info, err := os.Stat(src)
				if err != nil {
					return err
				}
				if info.IsDir() {
					destDir := src
					if out != "" {
						destDir, _ = filepath.Abs(out)
					}
					files, err := collectFiles(src, ".scxml", recursive)
					if err != nil {
						return err
					}
					for _, f := range files {
						rel, _ := filepath.Rel(src, f)
						var dest string
						if verify {
							dest = ""
						} else {
							dest = filepath.Join(destDir, rel[:len(rel)-len(filepath.Ext(rel))]+".scjson")
						}
						if err := convertScxmlFile(f, dest, verify, keepEmpty); err != nil {
							fmt.Fprintf(os.Stderr, "Failed to convert %s: %v\n", f, err)
						}
					}
					return nil
				}
				dest := out
				if !verify && dest == "" {
					dest = src[:len(src)-len(filepath.Ext(src))] + ".scjson"
				}
				return convertScxmlFile(src, dest, verify, keepEmpty)
			},
		},
		{
			Name:  "xml",
			Usage: "Convert scjson to SCXML",
			Flags: []cli.Flag{
				&cli.StringFlag{Name: "output", Aliases: []string{"o"}},
				&cli.BoolFlag{Name: "recursive", Aliases: []string{"r"}},
				&cli.BoolFlag{Name: "verify", Aliases: []string{"v"}},
				&cli.BoolFlag{Name: "keep-empty"},
			},
			Action: func(c *cli.Context) error {
				p := c.Args().First()
				if p == "" {
					return cli.Exit("path required", 1)
				}
				src, err := filepath.Abs(p)
				if err != nil {
					return err
				}
				out := c.String("output")
				recursive := c.Bool("recursive")
				verify := c.Bool("verify")
				args := c.Args().Slice()
				for i := 0; i < len(args); i++ {
					arg := args[i]
					if !strings.HasPrefix(arg, "-") {
						continue
					}
					switch arg {
					case "-o", "--output":
						if i+1 < len(args) {
							out = args[i+1]
							i++
						}
					case "-r", "--recursive":
						recursive = true
					case "-v", "--verify":
						verify = true
					}
				}
				info, err := os.Stat(src)
				if err != nil {
					return err
				}
				if info.IsDir() {
					destDir := src
					if out != "" {
						destDir, _ = filepath.Abs(out)
					}
					files, err := collectFiles(src, ".scjson", recursive)
					if err != nil {
						return err
					}
					for _, f := range files {
						rel, _ := filepath.Rel(src, f)
						var dest string
						if verify {
							dest = ""
						} else {
							dest = filepath.Join(destDir, rel[:len(rel)-len(filepath.Ext(rel))]+".scxml")
						}
						if err := convertScjsonFile(f, dest, verify); err != nil {
							fmt.Fprintf(os.Stderr, "Failed to convert %s: %v\n", f, err)
						}
					}
					return nil
				}
				dest := out
				if !verify && dest == "" {
					dest = src[:len(src)-len(filepath.Ext(src))] + ".scxml"
				}
				return convertScjsonFile(src, dest, verify)
			},
		},
		{
			Name:  "validate",
			Usage: "Validate scjson or SCXML files by round-tripping them",
			Flags: []cli.Flag{
				&cli.BoolFlag{Name: "recursive", Aliases: []string{"r"}},
			},
			Action: func(c *cli.Context) error {
				p := c.Args().First()
				if p == "" {
					return cli.Exit("path required", 1)
				}
				src, err := filepath.Abs(p)
				if err != nil {
					return err
				}
				success := true
				handle := func(f string) {
					data, err := os.ReadFile(f)
					if err != nil {
						fmt.Fprintf(os.Stderr, "Validation failed for %s: %v\n", f, err)
						success = false
						return
					}
					if filepath.Ext(f) == ".scxml" {
						jsonStr, err := xmlToJSON(string(data), true)
						if err != nil {
							fmt.Fprintf(os.Stderr, "Validation failed for %s: %v\n", f, err)
							success = false
							return
						}
						if _, err := jsonToXML(jsonStr); err != nil {
							fmt.Fprintf(os.Stderr, "Validation failed for %s: %v\n", f, err)
							success = false
							return
						}
					} else if filepath.Ext(f) == ".scjson" {
						xmlStr, err := jsonToXML(string(data))
						if err != nil {
							fmt.Fprintf(os.Stderr, "Validation failed for %s: %v\n", f, err)
							success = false
							return
						}
						if _, err := xmlToJSON(xmlStr, true); err != nil {
							fmt.Fprintf(os.Stderr, "Validation failed for %s: %v\n", f, err)
							success = false
							return
						}
					}
				}
				info, err := os.Stat(src)
				if err != nil {
					return err
				}
				if info.IsDir() {
					pattern := "*"
					if c.Bool("recursive") {
						pattern = "**/*"
					}
					matches, _ := filepath.Glob(filepath.Join(src, pattern))
					for _, f := range matches {
						if fi, err := os.Stat(f); err == nil && !fi.IsDir() {
							handle(f)
						}
					}
				} else {
					handle(src)
				}
				if !success {
					return cli.Exit("validation failed", 1)
				}
				return nil
			},
		},
	}

	if err := app.Run(os.Args); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
