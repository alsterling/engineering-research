# REFERENCE: HUMAN-SUPPLIED EVIDENCE

Production rule text, verbatim. `../SKILL.md` governs loading; its rules apply
alongside.

Also load: `evidence.md`; `certification.md` for a certifier record.

---

## HUMAN-SUPPLIED EVIDENCE

HUMAN-SUPPLIED is an acquisition channel: the human, not the run, obtained the
artifact. It is not an evidence grade, an authority class, a requirement status
or proof that the claim is correct. Grade, authority, applicability, document
state and conflict are judged on the original source, exactly as for evidence
the run retrieved itself.
- a human-supplied manufacturer document is manufacturer evidence, and a
  human-supplied certifier record is certifier evidence, when its provenance
  establishes that origin
- a human statement, summary or pasted claim without the underlying record is a
  lead or context; it does not become manufacturer or certifier evidence because
  a human supplied it, and it cannot support PASS

For human-supplied evidence used for a HARD requirement, record:
1. original source authority/issuer
2. original URL, registry ID, certificate/file number or equivalent locator
3. acquisition channel: HUMAN-SUPPLIED
4. supply date, and the retrieval date when the human states it
5. document title
6. revision, issue date or version when available
7. where the document names the candidate/configuration
8. supporting locator: page/section/table/row/registry field where practical
9. supporting text/value used for the predicate
10. SHA-256 of the supplied bytes when file bytes are supplied and the
    environment can compute it

Record a field that does not exist for the source, or cannot be obtained, as not
available with the reason; never invent it. Human supply does not relax HARD
PASS TRACEABILITY.

Artifact form:
- original file or record copy: hash the bytes when practical, keep the file
  unchanged where the environment allows, and grade by the original issuer
- screenshot, image or partial export: supports only what is visible in it,
  never unseen pages, hidden footnotes, revision or scope; record it as PARTIAL
- transcription or pasted text: not primary evidence on its own; usable only as
  far as its original source and locator are traceable under the existing rules

If the artifact was edited, cropped, transformed or otherwise modified in a way
that could affect the evidence, record that: its SHA-256 is the hash of the
supplied artifact, not of the original document, and unseen or removed content
is not inferred. A copy that leaves the bytes unchanged changes nothing. This is
engineering traceability, not forensic chain of custody.

Supplying the actual applicable record and inspecting it moves an
EXISTS_NOT_RETRIEVED or ACCESS_GATED document to RETRIEVED; a statement or
summary does not. Keep the earlier document state and how the record was
finally obtained in the record.

Human supply does not repair inadequate authority, a wrong model, an undefined
wildcard, an unresolved qualifier, unresolved applicability or an authoritative
conflict.

---

