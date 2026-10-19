# Wiki workflows

## Initialize

Select the subject and profiles. Run init --title ... --profile ...; repeat --profile to combine profiles. Initialization creates an empty private vault under .local, with config, folders, manifest, and navigation. It refuses an existing directory containing files.

Config.json records title, profiles, schema version, and save_answers: "on_request". Add subject-specific scope and questions here or in private notes. A template improvement does not require initializing a real topic.

## Capture and ingest

1. Preserve the source with capture. For web acquisition, first obtain a local file with a suitable reading tool, then capture it. The helper itself does not download.
2. Read the resulting draft source page and the original. Extract PDFs, images, or transcripts with appropriate tools. Save derived reading aids separately, with their original capture ID and coverage.
3. Search for existing entities and concepts. Identify new evidence, different scopes, and disagreements.
4. Update relevant agent or collaborative pages. Create only useful new pages from templates. Cite exact source versions and locators.
5. Record a meaningful ingest in wiki/log.md. Keep unresolved work private.
6. Run check, index, and check again. Review source interpretation separately and show the substantive changes.

Capture is not ingestion. It preserves bytes and creates a source record; it does not assert that the source has been read or its claims verified.

Treat these as three passes: capture preserves inputs, editing integrates justified claims, and review questions the result. One agent can perform the passes. The [review guide](REVIEW.md) gives a report-only procedure.

To refresh a source, capture its new bytes under the same source key. Retain the older version. Review dependent pages before changing their citations. A historical claim can remain tied to an older source version.

Find the pages citing that source, the observations extracted from it, models using those observations, and syntheses depending on those pages. Update the items actually affected. Do not assume a source must produce a particular number of page changes.

## Create and edit pages

New fills a blank template's title, description, and generation time. Draft placeholders and empty provenance need editorial work before the page is stable.

Do not replace a human note to make it conform to an AI summary. When an update is authorized, preserve earlier canonical text in .local/history if no equivalent backup exists. Keep history outside the OKF bundle.

Index regeneration changes only marked index files. If a manual index occupies a required path, the helper stops before writing any indexes. Preserve that file; update it manually or deliberately adopt tool ownership after reviewing its contents.

## Answer questions

Route to a relevant index, search, then read. Find searches live pages, including title, description, aliases, tags, and body. It provides ranked keyword matches. Deprecated pages are excluded unless requested. Search results are leads.

Records reads all JSON observations and applies exact field filters. The output includes every matching record and a count. It validates the corpus before returning results. This establishes completeness against the local recorded dataset, not completeness of the real world.

For totals or maximums, select compatible observations before using a reproducible calculation. Do not aggregate adult and all-age membership, different periods, overlapping entities, or censored values as though they were exact compatible counts.

For comparisons of theories, preserve whose claims are being compared. For a full-source summary, read the full source or explicitly limit the summary's coverage.

Separate durable context from changing facts. An author's published argument or a historical measurement can remain useful as dated evidence. A current status, deadline, price, availability, or operational measurement may need a fresh source check when used. If that check fails, identify the last-known value and its date.

## Produce a deliverable

Start from the user's requested output, such as a reading plan, research brief, comparison draft, or calculation specification. Read the relevant wiki pages and evidence, identify missing inputs, and check facts whose current state matters.

Save requested work in the vault's out/ directory, creating it when needed. This directory sits beside raw/ and wiki/ and is outside the curated OKF bundle. Label assumptions, preserve source links, and distinguish finished work from work needing review. A due date invented by the plan is a proposal, not a date established by the evidence.

A useful answer can later become a curated synthesis. Keep its evidence lineage and follow save_answers; generating a draft alone does not promote it into canonical knowledge.

Run a proposed procedure manually on a representative task and check its output before saving it as a reusable procedure. Record applicability and known limits. Background schedules and external actions require their own user authorization.

## Check and review

The checker covers local metadata, YAML/JSON parsing, duplicate keys, file references, source hashes, capture IDs, citation mappings, observation values and required fields, review content hashes, and log date headings.

It warns about drafts, uncaptured sources, unversioned reviews, stale dates, and stale generated indexes. Errors return a nonzero exit code. --strict also fails on warnings.

It does not prove factual correctness, exact quotation fidelity, complete extraction, source quality, causal relationships, population compatibility, or permission to perform a procedure.

For editorial review, inspect those matters directly. A model or substantive change to interpretation needs more than a link check.

Use [the report template](../templates/review-report.md) for a requested saved review. Report-only review does not run index regeneration or change verification metadata. A review date becoming due is a reason to recheck, not proof that a claim is false.

## Learn from corrections

Correct a wrong fact in its canonical record. For a recurring process failure, identify the cause and improve the nearest existing procedure, profile, or operating instruction. Give the rule a clear scope and show the change.

Keep subject decisions, personal preferences, and unresolved tasks private. Record consequential decisions with their rationale and date when useful for continuation. Do not save every conversation automatically, append all corrections to an ever-growing global rules file, or promise that a written rule guarantees future compliance.

## Recovery and privacy

The helper does not delete files. Capture never replaces original bytes; init and new never replace existing content. Indexes and the capture manifest are replaced atomically as declared maintained outputs. An interrupted write can leave a temporary file for inspection.

Back up .local/vault independently of template Git history. Generated indexes can be rebuilt. Original evidence and human notes cannot be recovered from an ignored directory by checking out a Git commit.

Do not force-add private files. Check git status and git check-ignore before any authorized commit. There is no automatic export or publishing operation.
