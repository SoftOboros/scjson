<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>
"""
Agent Name: dev-env-plan

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""

# Unified Development Environment Plan

This note captures the package requirements and conflict strategy for building a
single Docker image that supports every language implementation in the project.
The goal is a deterministic install that succeeds with a minimal, compatible
package set and fails with a clear explanation whenever mutually exclusive
options are requested.

## Baseline Packages (Ubuntu 24.04)

These packages have no mutual conflicts and cover all required toolchains.

| Purpose | Packages |
|---|---|
| Core tooling | `build-essential`, `curl`, `wget`, `git`, `nano`, `zstd`, `pkg-config` |
| Python | `python3`, `python3-venv`, `python3-pip` |
| Ruby | `ruby-full` |
| Java | `openjdk-21-jdk`, `maven` |
| .NET | `dotnet-sdk-8.0` |
| Go | `golang-go` |
| Rust (bootstrap) | `clang`, `cmake`, `llvm-dev`, `libssl-dev`, `libgtk-3-dev`, `libx11-dev`, `libxext-dev`, `libxrender1`, plus Rustup curl installer |
| Swift (runtime deps)| `libicu-dev`, `libxml2`, `libcurl4`, `libsqlite3-0`, `libpthread-stubs0-dev`, `libedit-dev` |
| Lua | `lua5.4`, `luarocks` |

Additional project build steps install Node.js, Swift, and Rust via official
tarballs/installers to avoid conflicting distro packages.

## Reference Installation Flow

1. `apt-get update`
2. Install the baseline packages listed above with `--no-install-recommends`.
3. Install AWS CLI v2 using the official AWS zip installer (no apt package is
available on 24.04).
4. Install Node.js, Swift, and Rust from their official tarballs as already done
in the project Dockerfile.

## Known Conflict Families & Resolutions

| Family | Conflict | Resolution |
|---|---|---|
| Lua JIT | `luajit` vs `luajit2` | Neither is required; stick with plain `lua5.4` + `luarocks`. |
| Databases | `mysql-*` vs `mariadb-*` | No language component depends on either; omit both. |
| NVIDIA Drivers | multiple `nvidia-*` variants | Not needed for build/test; omit entirely. |
| Mail/Print servers | packages such as `postfix`, `sendmail`, `magicfilter` | Out of scope; omit. |
| `rustup` vs distro `cargo` | `rustup` conflicts with `cargo` meta-package | Install Rust via rustup; do **not** install the distro `cargo`. |

By removing these optional/irrelevant packages the dependency resolver no
longer encounters conflicts.

## Optional Feature Flags

If a future contributor needs an optional stack that conflicts with the
baseline, guard the install behind an environment variable and fail with a clear
message when incompatible selections are made. Example pseudo-logic:

```bash
if [ "$INSTALL_DATABASE" = "mysql" ] && [ "$INSTALL_DATABASE" = "mariadb" ]; then
  echo "Conflicting database selections (mysql vs mariadb). Choose one." >&2
  exit 1
fi
```

Document any such options in this file so the matrix stays up to date.

## Next Steps

1. Update the Dockerfile to use the baseline package list and AWS CLI installer.
2. Remove the legacy `apt` installs for conflicting packages.
3. Add optional feature flags only when we have a concrete need, following the
failure pattern described above.
