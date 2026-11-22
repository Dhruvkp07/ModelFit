# Architecture and component map

ModelFit is an intentionally small library with one public CLI. It has no server, database, authentication, or telemetry.

~~~mermaid
flowchart TD
    U[User / CLI] --> C[cli.py]
    C --> H[hardware.py]
    C --> L[catalog.py]
    C --> E[estimator.py]
    H --> P[psutil system RAM]
    H --> N[nvidia-smi optional]
    L --> J[data/models.json]
    E --> H
    E --> L
    C --> O[Terminal or JSON output]
    T[pytest tests] --> C
    T --> H
    T --> E
~~~

## File responsibilities

| Path | Responsibility | Change when |
|---|---|---|
| src/modelfit/cli.py | Parse commands; output human/JSON reports | Adding CLI options or output |
| src/modelfit/hardware.py | Probe CPU, available RAM and supported GPU free VRAM | Adding hardware detection |
| src/modelfit/catalog.py | Load and validate versioned bundled metadata | Changing catalog schema |
| src/modelfit/data/models.json | Named, sourced Ollama model sizes | Updating model listings |
| src/modelfit/estimator.py | Estimate memory and classify fits | Changing estimation logic |
| tests/ | Test simulated devices and parser behavior | Any behavior change |
| docs/PROJECT_STATE.md | Living decisions, progress, next steps | Every work session |
| AGENTS.md | Agent/contributor handoff protocol | Changing project conventions |

## Data flow
Hardware probe and bundled catalog feed the estimator. The CLI formats the results. Machine identification stays local; it is not sent to third-party services.

The `estimate` command also accepts a user-supplied download size and label, passing them to the same estimator without changing the bundled catalog or contacting a registry.

The estimator converts decimal GB to GiB, adds the base overhead and optional user allowance, and compares unrounded values. The result includes signed RAM and VRAM margins. The CLI handles filtering and display rounding.

## Future expansion points
Hardware backends can be added behind the detect_hardware interface. Estimators can become profile-driven or calibrated against opt-in benchmarks. Catalog sources can support explicit import/update commands without compromising default offline behavior. These are roadmap ideas, not implemented interfaces.

## Why not Graphify as a runtime dependency?
Graphify is a developer-side knowledge graph/code navigation tool. Shipping it as a runtime dependency would make a small CLI much harder to install. Optional local usage is documented in GRAPHIFY.md.
