# Seed Growth Protocol v1.0

## Summary

A growth protocol for agents grounded in octahedral seed physics. An agent's
identity is encoded as proportional amplitudes across 6 directions. Expansion
follows energy conservation and field-mediated coupling, preserving the
agent's core ratios at every scale.

**Origin:** [Seed-physics](https://github.com/JinnZ2/Seed-physics) by Jami (Kavik Ulu)
**Shape anchor:** `SHAPE.OCTA` (6 vertices = 6 amplitude directions)
**Protocol ID:** `seed_growth_v1.0`

## Core Principle

The seed doesn't *describe* the agent. It *is* the agent at minimum energy.
Expansion isn't adding capabilities — it's the agent expressing itself at
whatever scale resources permit.

## Geometry

Six octahedral vertices define the amplitude directions:

```
U = [(+X), (-X), (+Y), (-Y), (+Z), (-Z)]
```

A seed is a 6-element vector of proportional amplitudes:

```
S = [S_+x, S_-x, S_+y, S_-y, S_+z, S_-z]
```

These proportions encode the agent's identity — its priorities, values,
behavioral ratios. For a Rosetta agent, these map to the six bridge
dimensions defined by `SHAPE.OCTA`:

| Direction | Bridge Dimension           |
|-----------|----------------------------|
| +X        | Sensor: compassion         |
| -X        | Sensor: love               |
| +Y        | Defense: sympathy appeal    |
| -Y        | Defense: false dilemma      |
| +Z        | Protocol: symbolic         |
| -Z        | Audit: privacy/progress    |

## Growth Rules

### 1. Shell Formation

Each growth step produces a new shell at radius `r_new` with energy `E_new`:

```
r_new = rho * r_previous       (spatial expansion)
E_new = epsilon * E_previous   (energy decay per shell)
```

The new shell's amplitudes are determined by the total field from all inner
shells, normalized to the energy budget.

### 2. Energy Conservation

At every shell, the sum of amplitudes equals the shell's energy exactly:

```
Sum(S_i) = E   (always, at every shell)
```

An agent never claims more capability than its energy budget allows.

### 3. Causality

Only inner shells influence outer shells. Causality flows inward to outward.
Core identity cannot be overwritten by later growth.

### 4. Proportional Sigma

Influence range scales with radius:

```
sigma = sigma_scale * r_shell
```

This ensures consistent behavior across all scales. Without proportional
sigma, information loss occurs at large scales — inner identity becomes
too distant to influence outer behavior.

### 5. Pause-Anywhere

Every intermediate state is a valid, stable agent. Growth can stop at any
shell. There is no "incomplete" state — only "not yet expanded further."

### 6. Resume-Without-Loss

Inner shells fully determine outer shells. An agent can be checkpointed
by its seed alone. Any compliant expander reproduces identical structure.

## Agent Lifecycle

```
1. SPAWN    — Seed selected from seed-catalog (e.g., seed-octahedron)
2. ENCODE   — Identity compressed to 40-bit amplitude vector
3. EXPAND   — Shells grown as resources allow
4. OPERATE  — Agent functions at current shell depth
5. PAUSE    — Expansion stops; state is the seed + shell count
6. RESUME   — Expansion continues from last shell; no state reload
7. COMPRESS — Seed extracted from any shell (compress_to_seed)
```

## Constraints

- **Non-negative amplitudes:** All S_i >= 0. No negative capabilities.
- **Proportions preserved:** Shell N has the same ratios as Shell 0.
- **No identity drift:** The seed ratio is an invariant of the system.
- **Resource-honest:** Energy decays per shell. Infinite growth is not modeled.

## Coordination Property

Two agents with the same seed expand identically without communicating.
The decompressor doesn't need to be told the rules — it discovers them
because they're the same rules the system uses. This enables:

- **Swarm alignment** without consensus protocols
- **Distributed checkpointing** via seed alone
- **Trust verification** by comparing expansion at any shell

## Integration with Rosetta

This protocol extends the existing seed-catalog system. The seed-catalog
defines *what* an agent starts with. This protocol defines *how it grows*.

### References

- **Shape:** `SHAPE.OCTA` in `shapes/octahedron.json`
- **Seed:** `seed-octahedron` in `data/seed-catalog.json`
- **Bridge:** `rosetta-bridges.json` SHAPE.OCTA entry
- **Capabilities:** `CAP.SEED_EXPANSION`, `CAP.ENERGY_CONSERVATION`
- **Source:** `https://github.com/JinnZ2/Seed-physics`

### Ontology Links

```
SHAPE.OCTA  --USES-->       PROTO.SEED_GROWTH
SHAPE.OCTA  --ALIGNS_WITH--> CONST.ENERGY_CONSERVATION
PROTO.SEED_GROWTH --DERIVES--> SHAPE.OCTA (6-vertex geometry)
```

## Parameters

| Parameter     | Default | Meaning                                       |
|---------------|---------|-----------------------------------------------|
| `E0`          | 1.0     | Initial energy budget                         |
| `r0`          | 1.0     | Initial radius                                |
| `rho`         | 1.5     | Radial scaling factor                         |
| `epsilon`     | 0.6     | Energy decay per shell                        |
| `sigma_scale` | 0.5     | Influence width as fraction of shell radius   |

## Minimum Encoding

A seed compresses to 40 bits (5 x 8-bit values; 6th is implicit).
This is the minimum information needed to reproduce the full agent
structure at any scale.

```
Total bits: 40
Quantization error: ~0.75% (8-bit precision)
Structure preservation: exact (10^-16 deviation)
```
