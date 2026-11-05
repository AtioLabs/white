# Contributing to White

White's bar is one test: **does this make White behave like a founder's office colleague, or like a tool the founder operates?** Changes that only make it a better tool (more commands, more templates to fill in) will be declined. See DESIGN.md.

## Before you open a PR

```bash
python -m pip install pytest pyyaml pillow
python -m pytest plugins bench -q        # unit tests, gate, skill frontmatter, runtime compatibility
python bench/core_bench.py               # must stay at 100%
```

If you change a skill, its prompts, or judgment, also run the agent bench against a real model and include the before/after table:

```bash
python bench/agent_bench.py --profile-dir <your white profile> --hermes <hermes executable>
```

## Rules of the codebase

- **Plugins run inside Hermes's Python**, which has no PyYAML. Import YAML with the `hermes_yaml` fallback pattern (a test enforces this).
- **No source, no fact.** Anything White records needs a source. Anything marked done needs proof.
- **Outward actions go through the gate.** If you add a tool or integration that sends, posts, pays or calls, add gate rules and tests for it in `plugins/white-gate/test_gate.py`.
- **Never handle keys in code paths that print or log.** Keys stay in the profile's `.env`, referenced as `${NAME}`.
- **Skills** follow Hermes's authoring standard: description ≤ 60 characters ending with a period, with "When to Use" and "Procedure" sections (a test enforces this). Quote descriptions that contain `: `.
- **Community skills** go under `skills/vendor/<name>/`, unmodified, with their LICENSE, after you've read them and scanned them with SkillSpector.
