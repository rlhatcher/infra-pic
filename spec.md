---
id: spec
title: Spec
tags: [spec]
pinned: true
created: "2026-02-26T15:44:38.345Z"
task:
  status: not_started
---

## Goal

A Python CLI tool called `awsdiagram` that takes a YAML file describing AWS infrastructure and renders it as an architecture diagram. Like PlantUML — declare what exists and how it connects, the tool handles drawing.

## Implementation Approach

Uses the Python **`diagrams`** library (mingrammer) as the rendering engine. The tool parses a simplified YAML DSL and programmatically builds `Diagram`, `Cluster`, and node objects, then renders to PNG via Graphviz.

**Why this approach:**
- `diagrams` library produces clean, professional diagrams with official AWS icons
- 200+ AWS node types across 20+ categories already available
- Graphviz handles layout automatically
- Pure Python — no external CLI tools beyond Graphviz

**Prerequisites:** Python 3.10+, Graphviz (`brew install graphviz`)

## YAML DSL

```yaml
diagram:
  name: "Web Application"

  services:
    lb:
      type: network.ELB
      label: "Load Balancer"
    web1:
      type: compute.EC2
      label: "Web Server 1"
    web2:
      type: compute.EC2
      label: "Web Server 2"
    db:
      type: database.RDS
      label: "User DB"
    cache:
      type: database.ElastiCache
      label: "Session Cache"

  groups:
    - name: "AWS Cloud"
      children:
        - name: "VPC"
          children:
            - name: "Public Subnet"
              services: [lb, web1, web2]
            - name: "Private Subnet"
              services: [db, cache]

  connections:
    - from: lb
      to: [web1, web2]
    - from: web1
      to: [db, cache]
    - from: web2
      to: [db, cache]
```

### DSL design principles

- **`services`** — flat map of service ID → type + label. Type uses category shorthand: `compute.EC2`, `network.ELB`, `database.RDS`, etc. (maps to `diagrams.aws.{category}.{Class}`)
- **`groups`** — ordered list of nested clusters. Each has a `name`, optional `children` (sub-groups), and `services` (list of service IDs placed in this group)
- **`connections`** — list of `from`/`to` pairs. `to` can be a single ID or list. Optional `label` for the connection.
- No layout directives, no positioning, no styling — the tool handles it all

### Supported type categories

`analytics`, `compute`, `database`, `devtools`, `engagement`, `general`, `integration`, `iot`, `management`, `media`, `migration`, `ml`, `mobile`, `network`, `security`, `storage` — and all others from `diagrams.aws.*`

## Tasks

- [ ] [Project scaffolding and CLI](intent://local/task/edeaa7e4-5440-4cef-8e66-d458bb0e5e23)

- [ ] [YAML parser and schema validation](intent://local/task/629e9cb5-7210-4365-a173-735cbdf4f9bb)

- [ ] [Diagram renderer](intent://local/task/3dee16d8-54da-4198-b03e-be1ccd6d6704)

- [ ] [Example YAML files and end-to-end testing](intent://local/task/2af61e9d-b551-4fa1-8f5e-f41280fce5bb)

- [ ] [Unit tests](intent://local/task/36cf895e-a1be-4f65-8b17-6990470f22bb)

## Acceptance Criteria

- [ ] `awsdiagram render <file.yaml>` produces a PNG from YAML
- [ ] YAML DSL uses `services`, `groups`, `connections` — no layout directives
- [ ] Service types use category shorthand: `compute.EC2`, `network.ELB`, etc.
- [ ] Groups nest naturally as clusters in the diagram
- [ ] Connections declared with `from`/`to` — layout is automatic
- [ ] Clear error messages for invalid YAML, missing references, unknown types, missing Graphviz
- [ ] `awsdiagram validate` checks YAML without rendering
- [ ] 3 working example files included
- [ ] All tests pass with `pytest`
- [ ] `awsdiagram import terraform <plan.json>` generates valid YAML DSL from Terraform JSON
- [ ] Generated YAML renders to a diagram with `awsdiagram render`
- [ ] At least 30 common AWS Terraform resource types mapped

## Terraform Integration

**Command:** `awsdiagram import terraform <plan.json> [-o infra.yaml]`

**Flow:** `terraform show -json > plan.json` → `awsdiagram import terraform plan.json` → `infra.yaml` → `awsdiagram render infra.yaml` → `diagram.png`

The import reads Terraform's JSON output format, maps `aws_*` resource types to `diagrams` node types, infers groups from VPCs/subnets/modules, and outputs editable YAML DSL.

- [ ] [Terraform import command](intent://local/task/3d22e488-822b-40dd-a3f3-aa0fc9e78da9)

## Non-goals

- Web UI or GUI
- Non-AWS providers (Azure, GCP) — can be added later
- Custom icons
- SVG/PDF output (PNG only for now)
- README or documentation files

## Assumptions

- Python 3.10+
- Graphviz installed (`brew install graphviz`)
- PNG output only

## Verification Plan

1. `pip install -e .` — installs successfully
2. `awsdiagram --help` — CLI works
3. `awsdiagram validate examples/web-app.yaml` — validation passes
4. `awsdiagram render examples/web-app.yaml -o test.png` — renders PNG
5. `pytest -v` — all tests pass
6. `awsdiagram import terraform examples/terraform-plan.json -o imported.yaml` — generates YAML
7. `awsdiagram render imported.yaml -o imported.png` — renders imported diagram