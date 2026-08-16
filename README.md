# Xerus — Disk-First Memory for AI and Software

**Persistent local-first memory, retrieval, and storage indexing for the Shmry Software Inc ecosystem.**

Xerus is being transitioned from its historical social-app codebase into the canonical **disk-first memory** component used by Sophyane, Nifdu, Neuron, HuobzLang, Shmry, and VPS when durable local memory or retrieval is required.

> **Current repository status:** the ecosystem role is canonical, but this repository still contains legacy Expo/Node social-application files from an earlier Xerus product. Those files are being replaced with the native disk-first-memory implementation. Do not treat the current legacy application tree as the final Xerus runtime.

## Role

Xerus provides:

- disk-first persistent memory
- local retrieval and storage indexing
- native-runtime integration
- memory services for peer software
- explicit capability routing through `ecosystem.json`

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

When a local capability is unavailable, Xerus can request an appropriate peer capability according to the shared ecosystem contract.

## Installation

A universal installer will be published after the native disk-first-memory tree replaces the historical social-app files. Until then, cloning this repository is intended for development and migration work only.

```bash
git clone https://github.com/badrpk/xerus.git
cd xerus
```

## Migration safety

The historical Xerus application is being preserved before replacement. The final native tree will deliberately exclude:

- `node_modules/`
- `.expo/`
- generated builds and caches
- credentials and `.env` files
- model binaries and runtime databases
- machine-specific state

## Ecosystem contract

See [`ecosystem.json`](ecosystem.json).

## Contributing

Contributions are welcome after the native memory API is published. Compatibility work should preserve the shared Shmry ecosystem contract and explicit failure behavior when peer capabilities are unavailable.

## License

See the repository license files for the applicable terms.
