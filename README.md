# Wiki Template

A starter for private knowledge bases that a person and an AI can use together. Keep original sources, build linked explanations, and add structured observations when a subject needs exact comparisons or calculations.

The same foundation supports theory, numerical research, hobby reference, personal observations, and agent procedures. Open the files in Obsidian or a Markdown editor. An AI with file access can maintain the collection using [AGENTS.md](AGENTS.md).

## Start a wiki

Copy or clone this repository into a new project directory. Then give your AI this instruction:

> Read AGENTS.md. Create an empty private wiki about [subject]. Choose the appropriate profiles, explain the scope briefly, and initialize it in .local/vault. Do not populate it with unsourced facts.

That is the normal way to use the template. You can combine profiles, for example theory with quantitative, or reference with observations.

For manual setup, the optional helper needs Python 3.10+ and PyYAML:

~~~powershell
py -3 -m pip install -r requirements.txt
py -3 scripts/wiki.py init --title "My topic" --profile theory
~~~

On macOS or Linux, substitute python3 for py -3. If PyYAML is already available, skip installation. The tools make no network requests.

Open .local/vault as an Obsidian vault. Start at wiki/index.md. Use source mode for nested YAML metadata. The curated pages use ordinary Markdown links and footnotes.

## Work with the wiki

Give the AI a file and a clear instruction:

> Ingest this source into the wiki. Preserve the original, identify what it adds to existing pages, keep disagreements visible, and show me the substantive changes.

For a question:

> Using this wiki, explain [question]. Cite the evidence and distinguish reported claims from interpretation. Check the originals if the question needs an exact quote or detail.

For maintenance:

> Check this wiki for broken references, stale source dependencies, missing attribution, and conflicting definitions. Separate mechanical problems from editorial questions.

The AI should preserve human-owned notes and create useful pages rather than a fixed number of notes per source. Answers are saved when requested or when the local configuration explicitly enables that workflow.

The workflow separates capture, editing, and review. A review can identify affected pages, unresolved disagreements, stale claims, and weak navigation without rewriting the wiki. See [the review guide](docs/REVIEW.md).

To turn knowledge into a deliverable:

> Using this wiki, draft [a reading plan, brief, comparison, or other output]. Check any facts that need to be current, link the supporting evidence, and mark assumptions. Save the draft in the vault's out directory.

## What lives where

| Path | Purpose |
| --- | --- |
| AGENTS.md | Agent instructions and routing |
| CLAUDE.md | Entry pointer for agents using that filename |
| docs/FORMAT.md | Page and record contract |
| docs/WORKFLOWS.md | Setup, ingestion, answering, review, and recovery |
| docs/REVIEW.md | Report-only review, source impact, contradictions, and freshness |
| docs/profiles/ | Optional rules for each kind of knowledge |
| templates/ | Blank page and observation templates |
| examples/vault/ | A small, entirely fictional worked example |
| scripts/wiki.py | Setup, page creation, source capture, checks, indexing, search, and exact record filtering |
| tests/ | Behavioral checks for the helper and example corpus |
| .local/vault/ | Your private configuration, originals, pages, and records |
| .local/vault/out/ | Requested drafts and review reports, outside the curated wiki |
| .local/history/ | Private backups of edited material, when needed |

The private vault contains config.json, raw/, and wiki/. Only wiki/ is the curated OKF bundle. Raw transcripts, PDFs, and datasets retain their original format.

## Helper commands

~~~powershell
# Create a blank page. It starts as a draft and never replaces a page.
py -3 scripts/wiki.py new concept --title "Example concept" --description "What this page explains."

# Preserve a local source and create its draft source page.
py -3 scripts/wiki.py capture "C:\path\paper.pdf" --source-id paper --title "Paper title" --resource "https://example.org/paper"

# Check metadata, references, source hashes, and structured records.
py -3 scripts/wiki.py check

# Rebuild only tool-owned directory indexes.
py -3 scripts/wiki.py index

# Search current pages, including aliases. This is keyword search.
py -3 scripts/wiki.py find "example concept"

# Return all structured observations matching exact filters.
py -3 scripts/wiki.py records --metric population --period 2025 --unit people
~~~

--vault selects another vault and comes before the command. For example:

~~~powershell
py -3 scripts/wiki.py --vault examples/vault check
py -3 scripts/wiki.py --vault examples/vault find "institutional continuity"
py -3 scripts/wiki.py --vault examples/vault records --metric membership --period 2025
py -3 -m unittest discover -s tests -v
~~~

The example command does not initialize a personal wiki. Tests keep their generated fixtures in ignored .local/test-runs/.

The helper does not parse PDFs, infer concepts, evaluate models, or decide whether claims are true. Those tasks belong to source-reading tools, reproducible domain-specific calculations, and editorial review. See [the workflows](docs/WORKFLOWS.md) for what checks establish.

## Privacy and backups

Personal knowledge, settings, originals, and working notes belong in .local. It is excluded from Git. Keep committed examples fictional and do not force-add ignored files.

Git exclusion is not encryption, a backup, or an AI access restriction. File synchronization can still include this directory. A hosted model receives the material supplied to it for processing. Keep a separate backup of the private vault if it matters to you.

Public guides can be selected exports later. This starter has no publishing, background ingestion, or hosted service.

## Format and extension

The curated folder targets [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md), with a stricter local profile for useful metadata and references. Its maintenance workflow draws on [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

Add a profile when a domain needs different records or review rules. Add semantic search, a derived database, or typed relationship queries when actual questions demonstrate the need. Canonical knowledge remains in files; generated views should be reproducible.
