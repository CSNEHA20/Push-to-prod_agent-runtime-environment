# Changelog

All notable changes to `arc-sdk` are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial public SDK **structure**: the `ARC` facade exposing `wrap`, `run`,
  `trace`, `recover`, `verify`, `replay`, `inspect`, `middleware`, `plugin`,
  and `event`.
- Typed data contracts (`Session`, `TraceStep`, `Checkpoint`,
  `VerificationResult`, `ReplayTimeline`, `RecoveryPlan`, `Event`) and
  structural extension-point interfaces (`Middleware`, `Plugin`,
  `EventHandler`).
- Modular runtime engine interfaces (`scheduler`, `recovery`, `verifier`,
  `firewall`, `recorder`, `plugins`, `middleware`, `events`).
- Provider/framework integration and MCP router interfaces.
- `arc` console-script entrypoint, packaging (`pyproject.toml`), PEP 561 typing
  marker, examples, and documentation.

### Notes
- This release is **structure only** — runtime engine internals are not yet
  implemented; execution methods raise `NotImplementedError`.

## [0.1.0]
- Scaffolding baseline.
