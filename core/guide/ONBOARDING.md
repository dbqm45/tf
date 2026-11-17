# Onboarding: the first installation of the factory

This file takes you from zero to a working factory in a project. Daily work: `GUIDE.md`, frequent questions:
`FAQ.md` (both go to `.tf/factory/` in the project at installation).

## 1. Once per computer: the `tf` command
You need Python 3 and git.

```bash
git clone <adres repozytorium fabryki> ~/tools/tf
python3 ~/tools/tf/core/factory/tf.py --install-launcher
```

- The script copies `tf` to `~/.local/bin` (another directory: `--bin <katalog>`; on Windows `tf.cmd` is also created).
- It records the repository address in `tf`: from `--repo <url>`, from the `TF_REPO` variable or from the clone's `origin`.
- `~/.local/bin` must be in `PATH`.
- `tf` runs code from that repository, so point it only at one you trust.

## 2. In the project: installation
```bash
cd ~/projects/moja-aplikacja
tf
```

Without the factory in the project, `tf` installs the latest release (the highest `vX.Y.Z` tag). At the first
installation it asks about packs (`pack-*`) and modes (`mode-*`). It does not ask about the language: agents answer in
the language you write in and write documents for you in it; commits follow the language of the repository's history
(in a new repository, English). Do you write in Polish? Add `pack-editorial-pl` (correctness and style of Polish).

Required packs are added automatically. At the end the installer builds
the agents (`.tf/factory/build.py`).

Without questions, for example in a script:

```bash
tf install --packs pack-it,pack-docs,pack-editorial-pl --yes
```

A preview without changes: `python3 ~/tools/tf/core/factory/install.py --dry-run`.

## 3. Private or team
| | Private (default) | Team (`tf install --shared`) |
|---|---|---|
| Settings and hooks | `.claude/settings.local.json` | `.claude/settings.json` |
| Rules | `CLAUDE.local.md` | `CLAUDE.md` |
| Git | nothing goes into the repository; the factory's paths in `.git/info/exclude` (`--gitignore`: in `.gitignore`) | the factory committed with the project, plus a CI workflow |

Private — when the factory is only your tool. Team — when it is to work for everyone and in CI.

## 4. The first run
1. In the project directory run `claude` and accept trust in the folder. Without that, hooks and permissions do not
   work.
2. Check the installation: `tf doctor` (repair: `tf doctor --fix`), the list of packs and modes: `tf list`.
3. Choose a persona from `.claude/catalog.md` and run it: `claude --agent <nazwa>`. Next: `.tf/factory/GUIDE.md`.

## 5. Cloud sessions (claude.ai/code)
- The factory's hooks work only in a session started in the project repository's directory.
- The factory must be in the repository (`--shared`) or installed in the environment's setup script.
- A session with several repositories or from a parent directory does not load the hooks (there are no start messages).
  You then run tests and gates by hand.

## 6. Later
| Command | What it does |
|---|---|
| `tf` | an update (`tf update --check` — what will change, without changes) |
| `tf add <id>` / `tf remove <id>` | adding or removing a pack or a mode |
| `python3 .tf/factory/update.py --rollback` | going back to the previous version |

An update overwrites the factory's files (like `node_modules`) — you make changes in the factory repo; your files and
settings in `.tf/config/config.yaml` stay. All
options: `python3 ~/tools/tf/core/factory/install.py --help` and `tf --help`.
