# Content contract v1

The curated wiki/ folder targets OKF v0.2. Repository docs, templates, raw sources, and configuration are outside that bundle.

Upstream: [OKF v0.2 specification](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md). The specification inspected on 2026-10-12 had SHA-256 26aa5da029278939f914e578107242d9607d4f2dc5fe153272b82f9ed1030101. This hash identifies the reviewed text, not a bundled runtime dependency.

## Pages

Each non-reserved .md file in wiki/ starts with YAML frontmatter. Use UTF-8, forward slashes in paths, and ordinary Markdown links. Prefer stable lowercase filenames. Display titles and aliases can contain normal language.

The local profile requires:

| Field | Meaning |
| --- | --- |
| type | Nonempty string; common values are source, entity, concept, synthesis, procedure, note, and model |
| title | Readable title |
| description | Short discovery summary |
| status | draft, stable, or deprecated |
| ownership | human, collaborative, or agent |
| claim_kind | source-report, sourced-summary, interpretation, hypothesis, personal-observation, or procedure |

Aliases and tags are optional lists of strings. A stable page with sourced content needs provenance. Personal hypotheses and personal observations instead identify their author with an actor such as human:example. A source page identifies its own material with resource and, when captured, capture_id.

Unknown type values and additional metadata are preserved. The local profile is stricter than minimal OKF: missing local fields or broken references fail our checker even where upstream consumers must tolerate them.

## Provenance and footnotes

Use a source entry and an ordinary footnote together:

~~~yaml
sources:
  - id: study
    resource: ../sources/study-version.md
    title: Study title
    locator: Table 2
~~~

~~~markdown
The study reports this finding.[^study]

[^study]: [Study title](../sources/study-version.md), Table 2.
~~~

Footnote labels must match sources[].id. Do not manufacture locators. Use a page/table/section or a real video timestamp where available. A paragraph locator is acceptable when a source has no pagination.

Source IDs are unique within a page. Captured versions have unique capture IDs. A source's publication date, capture time, observation period, and page edit time are separate concepts.

Locator, ownership, claim_kind, author, capture_id, inputs, and relations are local extensions. Generic OKF readers may preserve them without implementing their behavior.

## Links, inputs, and relationships

Internal link destinations resolve relative to the current file. Paths beginning with / resolve from wiki/. Encode spaces in Markdown destinations. Local references may reach preserved evidence in the vault's raw/ directory; paths escaping the vault are rejected.

The checker handles ordinary inline links, images, reference links, source resources, model inputs, and relations[].target. It checks file existence and containment, not the semantic correctness of relationships or every heading anchor. Obsidian-specific wikilinks are flagged so the portable core does not silently depend on them.

Typed relationships are optional:

~~~yaml
relations:
  - kind: developed-by
    target: ../entities/example-author.md
    source_id: study
~~~

Use an evidence source ID or identify a personal hypothesis. An edge is an assertion requiring attribution. It does not automatically mean causation.

## Review and dates

OKF generated identifies who or what made the last substantive content change. Verified records source-level confirmation. Actor examples are human:example, process:wiki-template, and example-agent/v1.

Timestamps in these fields and stale_after use ISO 8601 datetimes with a timezone. Verified can be one mapping or a list. Do not call structural checks content verification.

For content review, add a local review_basis from the helper's review_digest(page) function. It hashes the parsed metadata and LF-normalized Markdown body, excluding generated, verified, and review_basis. The checker warns when reviews have no revision basis and fails when a provided basis no longer matches. This covers changes to provenance as well as prose; it checks revision identity, not review quality. A full evidence review also considers changed sources.

Stale_after produces a warning when due. Do not label historical observations current because a page was edited recently.

## Source captures

Raw manifest.json contains a version number and a captures list. Each record includes ID, source key, title, resource, original filename, vault-relative path, SHA-256, byte count, and capture time.

The helper creates a version ID from a user-supplied source key and the content hash. It copies the bytes into that version's raw/captures subdirectory, retaining the original file extension, and creates a draft source page. Identical bytes under the same key reuse the existing capture. Changed bytes create a new version. Old files and source pages remain.

An ID is not evidence by itself. Check verifies capture paths, byte counts, hashes, and page references, and requires a captured source page's resource to match the manifest. A source change invalidates a capture hash rather than silently updating it.

## Structured observations

Store one JSON object per file under wiki/observations/. Each record requires:

~~~json
{
  "id": "example-observation",
  "metric": "example-metric",
  "label": "What was measured",
  "value": null,
  "unit": "example-unit",
  "period": "2025",
  "scope": "Defined place or setup",
  "universe": "Who or what the value describes",
  "method": "unavailable",
  "source": "../sources/example-source.md",
  "locator": "Relevant source section",
  "notes": "Why the value is unavailable"
}
~~~

Values are finite numbers or null; booleans are not numbers here. Null requires method unavailable and an explanation. Zero is a valid measured value. Methods are reported, observed, derived, modeled, or unavailable.

Optional low and high form an ordered range and must contain a provided central value. A range is usable with null central value when the method is not unavailable. Explain whether a range is reported uncertainty, a modeled sensitivity range, or another bound.

Optional qualifier is eq, lt, lte, gt, or gte. Preserve inequalities. An upper bound is not an exact count. IDs must be unique across observations.

The checker does not infer unit compatibility, overlap, or model validity. The quantitative profile defines the review needed before calculation. The helper only returns complete matching records; it does not aggregate them.

## Navigation and history

Reserved index.md files are generated directory listings. The tool owns only indexes containing <!-- wiki-template:index -->. It refuses to replace unmarked files. The root index includes okf_version: "0.2"; child indexes have no frontmatter. Existing manual indexes can remain, but must be updated manually.

Log.md is manually maintained: ISO date headings, newest first, with concise entries for meaningful ingests and revisions. Check checks date ordering and headings. Neither indexing nor a question silently appends knowledge to the log.

Index entries are derived from current metadata and record descriptions. They are navigation, not an independently editable copy of facts. No search index or database is required by this contract.
