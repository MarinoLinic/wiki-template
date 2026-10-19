---
type: model
title: All-age membership change
description: A formula using compatible fictional records from two periods.
status: stable
ownership: collaborative
claim_kind: interpretation
inputs:
  - ../observations/membership-2024.json
  - ../observations/membership-2025.json
sources:
  - id: report
    resource: ../sources/fictional-report.md
    locator: Section B, lines 8-9
---

# All-age membership change

Inputs are the [2024 record](../observations/membership-2024.json) and the [2025 record](../observations/membership-2025.json). Both cover Harbor Association's all-age membership.[^report]

~~~text
net_change = membership_2025 - membership_2024
percentage_change = net_change / membership_2024 * 100
~~~

This is a formula specification. Use a deterministic calculation to obtain an output. Do not substitute the overlapping adult membership record or call the result a birth rate.

[^report]: [Demonstration report](../sources/fictional-report.md), Section B, lines 8-9.
