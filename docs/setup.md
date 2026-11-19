# Installing the `tf` command

The factory is not a program installed once per computer. It is a set of files that goes into every project
(`.claude/` and `.tf/`). One thing is installed on the computer: the `tf` command. In a project directory, `tf install`
downloads the latest factory release and installs it, and `tf` (or `tf update`) updates it later.

Requirements: **Python 3.9+** and **git**. The script checks both and tells you how to install what is missing.

## One line

The `dbqm45/tf` repository is private, so downloading the script and the factory itself requires access to it. The
simplest way is the [GitHub CLI](https://cli.github.com/) (`gh auth login` once per computer; git uses the same login).

**macOS, Linux:**

```sh
gh api repos/dbqm45/tf/contents/scripts/install.sh -H "Accept: application/vnd.github.raw" | sh
```

**Windows (PowerShell):**

```powershell
gh api repos/dbqm45/tf/contents/scripts/install.ps1 -H "Accept: application/vnd.github.raw" | Out-String | iex
```

Without `gh`, with a GitHub token (read access to the repository) in the `GITHUB_TOKEN` variable:

```sh
curl -fsSL -H "Authorization: Bearer $GITHUB_TOKEN" https://raw.githubusercontent.com/dbqm45/tf/main/scripts/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/dbqm45/tf/main/scripts/install.ps1 -Headers @{Authorization = "Bearer $env:GITHUB_TOKEN"} | iex
```

Once the repository is public, this is enough:
`curl -fsSL https://raw.githubusercontent.com/dbqm45/tf/main/scripts/install.sh | sh`
(Windows: `irm https://raw.githubusercontent.com/dbqm45/tf/main/scripts/install.ps1 | iex`).

## What the script does

1. Checks for Python 3.9+ (`python3`, `python`; on Windows `py` first) and git.
2. Downloads the factory (`git clone --depth 1`) into a temporary directory.
3. Installs the `tf` command in `~/.local/bin` (`core/factory/tf.py --install-launcher`) with the repository address
   stored inside; on Windows also `tf.cmd`.
   The launcher is a copy of `tf.py` from the time of installation: after a successful `tf` (update) in a project it is
   replaced with the `tf.py` of the updated engine, and a command it does not know yet is passed on to the project's
   `.tf/factory/tf.py`. You refresh a launcher from before this change once, by hand:
   `python3 .tf/factory/tf.py --install-launcher`.
4. Removes the temporary directory. If `~/.local/bin` is not in PATH, it tells you what to add (on Windows it asks
   whether to add it to the user's PATH).

The script messages are in English and ASCII only, because Windows PowerShell 5.1 reads `irm … | iex` in an encoding
other than UTF-8 and garbles non-ASCII letters and symbols.

Apart from the `tf` file (and `tf.cmd`), the script installs nothing and does not change the shell profile. Read a
script downloaded from the network before running it: `scripts/install.sh`, `scripts/install.ps1`.

## Settings

| Variable | Default | Purpose |
|---|---|---|
| `TF_REPO` | `https://github.com/dbqm45/tf.git` | another repository (e.g. a fork) or SSH: `git@github.com:dbqm45/tf.git` |
| `TF_BIN` | `~/.local/bin` | another directory for the `tf` command |
| `TF_PYTHON` | `python3 python` (Windows: `py python3 python`) | a specific Python |
| `TF_GIT` | `git` | a specific git |
| `TF_NO_PATH` | — | Windows: do not ask about PATH |

Example: `curl … | TF_BIN=~/bin sh`.

## Next

```sh
cd ~/projects/my-app
tf install            # choose overlays and language; writes the factory to .claude/ and .tf/
tf                    # later: update to the latest release
```

Guide to the factory in a project: `.tf/factory/GUIDE.md`; frequently asked questions: `.tf/factory/FAQ.md`.
From a repository clone, `sh scripts/install.sh` or `python3 core/factory/tf.py --install-launcher` also works.
