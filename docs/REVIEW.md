# Review a wiki

A review asks whether the wiki's current explanations remain supported, useful, and easy to find. The helper's check command establishes structural integrity. Source interpretation and contradictions require a separate reading pass.

## Three passes

| Pass | Responsibility | Output |
| --- | --- | --- |
| Capture | Preserve the original, identity, version, and coverage | Raw bytes and a draft source record |
| Edit | Integrate justified claims while preserving attribution and scope | Scoped page or record changes |
| Review | Question evidence, contradictions, freshness, and navigation | Findings with evidence and proposed next actions |

One agent can perform these passes. A fresh reading pass should check the sources directly rather than accepting the editing pass's summary as proof.

During a report-only review, read and run nonmutating checks. Do not edit wiki pages, rebuild indexes, resolve disagreements, refresh review stamps, or perform external actions. Report findings in chat or save a requested report in the private vault's out/ directory.

## Scope the review

Identify the topic, recent source changes, and decision the review is meant to support. Start from the relevant index and explicit references. Expand as needed; do not load the entire collection by default.

State what was reviewed and what remains unchecked. A sampled review cannot establish that the rest of the wiki is correct.

## Follow a source change through its dependents

1. Compare the new capture with the previous version. Separate a changed value, a changed definition, an added section, and a correction.
2. Find direct citations to the source page or version in page metadata and prose.
3. Follow extracted observations, model inputs, derived results, and dependent syntheses. Ordinary references and exact search can help locate candidates.
4. Record which claims are affected and why. A reference does not mean every statement on the page changed.
5. Propose bounded updates. Preserve historically valid observations and their original versions.

The helper has no automatic transitive impact analysis. Source changes need this explicit agent or human review.

## Keep disagreements inspectable

For each apparent contradiction, record:

- The question or claim, with both page paths.
- Each side's source, version, locator, period, and relevant scope.
- Whether the difference comes from definitions, dates, measurement methods, interpretation, or a genuine unresolved conflict.
- What evidence or decision would resolve it, and the next useful action.

Do not choose the newer or more fluent account automatically. Two dated statements can both be correct; two authors can disagree. If the conflict remains unresolved, preserve both positions and report its consequence for the question being answered.

Resolved findings should record the resolution and reason. Keep source history intact. Review reports can hold open issues until a dedicated review queue is justified.

## Freshness depends on the claim

| Kind of knowledge | Review approach |
| --- | --- |
| Historical quote or published theory | Verify attribution and the cited version; age alone is not a failure |
| Historical measurement | Retain its period and universe; do not relabel it current |
| Current status, deadline, price, or availability | Recheck the authoritative source when the request depends on today's state |
| Changing observation or recommendation | Choose a review date from the subject's rate of change and consequences of staleness |

Use the existing verified, review_basis, and stale_after conventions. Generation time and capture time do not mean a claim was confirmed. When only a particular claim was checked, describe that scope in the report rather than marking the entire page verified.

A fresh source is not required merely to keep an old claim valid. Rechecking the existing authoritative source can be sufficient. An overdue review marks work to do; it does not make the source false, remove a previous review, or establish a contradiction.

If current access fails, say so and date any last-known evidence used. Do not silently reuse cached information as though the check succeeded.

## Navigation and omissions

Look for useful pages with no meaningful incoming links, source references that do not lead back to originals, aliases that fail to find known concepts, and important questions absent from syntheses.

When assessing isolation, ignore links supplied only by generated directory listings. Otherwise every indexed page appears connected. Human notes and source records can legitimately stand alone; propose useful links rather than manufacturing connections or deleting pages.

The helper does not detect semantic contradictions or meaningful orphan pages. Its strict structural pass remains a separate check.

## Report and follow up

Use the [review report template](../templates/review-report.md). Prioritize findings that change an answer, invalidate a calculation, or obscure important disagreement. Distinguish confirmed problems, questions, checks passed, and items not examined.

Propose the smallest useful correction and identify human-owned material requiring the user's direction. Report factual conflicts that affect the current answer immediately; do not wait for a future sweep.

Reviews are on demand in this starter. A user can later authorize a scheduled review after the manual workflow proves useful. Such a schedule needs explicit scope, runtime, resource limits, notification conditions, and access-failure behavior. Routine runs should stay quiet when there is no meaningful change or required action.
