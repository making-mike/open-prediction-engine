# Domain Setup

Status: implemented as schema-bound generated setup records for one reference setup and one candidate private setup.

The domain setup contract is the first OPE-standard record for helping agents set up a private prediction engine without treating OPE as a universal oracle. A setup states the forecast question templates, output types, horizons, source roles, required fields, entity and alias expectations, resolution policy, scoring policy, baseline policy, method policy, recalculation rules, local implementation status, and claim boundary.

## Current Records

Generated setup records live under:

```text
spec/fixtures/generated/domain-setups/
```

The current fixtures are:

- `weather-logistics-domain-setup.generated.json`: fixture-ready reference setup that can run through the local weather-logistics forecast-run path.
- `seaport-berth-availability-domain-setup.generated.json`: candidate private setup that proves the contract can describe a non-weather operational domain without claiming a runnable model.

## Commands

Inspect all setup summaries:

```bash
python3 scripts/ope.py domain-setups
```

Inspect one full setup:

```bash
python3 scripts/ope.py domain-setups --setup weather-logistics
python3 scripts/ope.py domain-setups --setup seaport-berth-availability
```

Check generated setup drift and semantic boundaries:

```bash
python3 scripts/generate_domain_setups.py --check
python3 scripts/check_domain_setups.py
python3 scripts/ope.py domain-setups --check
```

## Maturity Labels

- `candidate`: shape is explicit, but the setup is not yet runnable and cannot claim forecast quality.
- `fixture_ready`: generated local fixture records exist and can be checked deterministically.
- `benchmarked`: comparable benchmark evidence exists for at least one enabled non-baseline method.
- `live_provisional`: live evidence can be captured under explicit source policy, but calibration remains provisional.
- `calibrated`: enough comparable resolved outcomes exist for the declared setup, horizon, output type, source policy, and method.

## Guardrails

Candidate private setups must not claim calibration, benchmarked quality, production readiness, state-of-the-art performance, or universal domain coverage. They may only claim that the source roles, required fields, question templates, method policy, and resolution rules are explicit enough for an agent or developer to inspect before connecting data.

Fixture-ready reference setups still cannot claim live calibration or production readiness unless resolved outcome counts and release checks support those claims.
