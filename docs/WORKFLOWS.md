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

To refresh a source, capture its new bytes under the same source key. Retain the older version. Review dependent pages before changing their citations. A historical claim can remain tied to an older source version.

## Create and edit pages

New fills a blank template's title, description, and generation time. Draft placeholders and empty provenance need editorial work before the page is stable.

Do not replace a human note to make it conform to an AI summary. When an update is authorized, preserve earlier canonical text in .local/history if no equivalent backup exists. Keep history outside the OKF bundle.

Index regeneration changes only marked index files. If a manual index occupies a required path, the helper stops before writing any indexes. Preserve that file; update it manually or deliberately adopt tool ownership after reviewing its contents.

## Answer questions

Route to a relevant index, search, then read. Find searches live pages, including title, description, aliases, tags, and body. It provides ranked keyword matches. Deprecated pages are excluded unless requested. Search results are leads.

Records reads all JSON observations and applies exact field filters. The output includes every matching record and a count. It validates the corpus before returning results. This establishes completeness against the local recorded dataset, not completeness of the real world.

For totals or maximums, select compatible observations before using a reproducible calculation. Do not aggregate adult and all-age membership, different periods, overlapping entities, or censored values as though they were exact compatible counts.

For comparisons of theories, preserve whose claims are being compared. For a full-source summary, read the full source or explicitly limit the summary's coverage.

## Check and review

The checker covers local metadata, YAML/JSON parsing, duplicate keys, file references, source hashes, capture IDs, citation mappings, observation values and required fields, review content hashes, and log date headings.

It warns about drafts, uncaptured sources, unversioned reviews, stale dates, and stale generated indexes. Errors return a nonzero exit code. --strict also fails on warnings.

It does not prove factual correctness, exact quotation fidelity, complete extraction, source quality, causal relationships, population compatibility, or permission to perform a procedure.

For editorial review, inspect those matters directly. A model or substantive change to interpretation needs more than a link check.

## Recovery and privacy

The helper does not delete files. Capture never replaces original bytes; init and new never replace existing content. Indexes and the capture manifest are replaced atomically as declared maintained outputs. An interrupted write can leave a temporary file for inspection.

Back up .local/vault independently of template Git history. Generated indexes can be rebuilt. Original evidence and human notes cannot be recovered from an ignored directory by checking out a Git commit.

Do not force-add private files. Check git status and git check-ignore before any authorized commit. There is no automatic export or publishing operation.
