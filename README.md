# Xerus — Disk-First Memory for AI and Software

**Persistent local-first memory and retrieval for the Shmry Software Inc ecosystem.**

Xerus now includes a standalone disk-first memory runtime with an installable Python package and CLI. The runtime persists memory to a local JSONL journal, supports namespace-filtered recall, keeps repeated keys authoritative by latest occurrence, and does not require a network service or database.

> **Migration note:** this repository still contains historical Expo/Node/Firebase social-application files from an earlier Xerus product. They are legacy migration residue and are not part of the canonical Xerus memory runtime. The verified runtime lives under `src/xerus/` with package metadata in `pyproject.toml`.

## Verified runtime

The current standalone runtime has been verified on WSL/Linux with:

- editable package installation
- pytest regression coverage
- CLI `remember`
- CLI `recall`
- CLI `status`
- persistent filesystem journal creation

The canonical backend reported by the runtime is `filesystem-journal` and `status` reports `disk_first: true`.

## Quick install

### Linux / WSL / macOS / compatible Unix

```bash
curl -fsSL https://raw.githubusercontent.com/badrpk/xerus/main/install.sh | bash
```

Then:

```bash
xerus status
xerus remember "persistent local memory" --namespace demo
xerus recall "local memory" --namespace demo
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/badrpk/xerus/main/install.ps1 | iex
```

## Development install

```bash
git clone https://github.com/badrpk/xerus.git
cd xerus
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
pytest -q tests/test_memory.py
```

## Runtime layout

```text
pyproject.toml
src/xerus/__init__.py
src/xerus/memory.py
src/xerus/cli.py
tests/test_memory.py
install.sh
install.ps1
```

Default memory state is stored under:

```text
~/.local/share/xerus/memory.jsonl
```

Override it with `XERUS_HOME`.

## Core behavior

Xerus provides:

- disk-first persistent memory
- append-only JSONL journal storage
- fsync-backed persistence on writes
- deterministic memory keys
- latest-record authority for repeated keys
- namespace filtering
- bounded local term retrieval
- explicit filesystem status reporting
- no mandatory cloud or database dependency

## Shmry Software Inc ecosystem

| Product | Role |
|---|---|
| Shmry | Cloud + email server |
| **Xerus** | **Disk-first memory** |
| VPS | Native TLS/SNI webserver |
| HuobzLang | Highest-level compact language |
| Neuron | Biological intelligence |
| Nifdu | Screenshot-loop harness |
| Sophyane | Multi-option engineering harness |

`ecosystem.json` declares Xerus capabilities for the shared Shmry Software Inc capability-routing contract. Runtime peer-to-peer capability calling across all seven products is a separate integration phase and should not be inferred from the manifest alone.

## Legacy-tree retirement

The historical social-app tree is being retained until the standalone memory runtime and installers are proven across target platforms. A later cleanup will preserve rollback history and remove generated, cached, credential-bearing, and unrelated legacy application content from the canonical runtime tree.

## Security

Do not commit runtime journals, `.env` files, credentials, private keys, generated environments, caches, or machine-specific state.

## Contributing

Contributions to the disk-first runtime should preserve local-first operation, explicit failures, durable writes, and backwards-compatible CLI behavior where practical.

## License

See the repository license files for the applicable terms.
