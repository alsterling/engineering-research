# REFERENCE: CERTIFICATION EVIDENCE AUTHORITY

Production rule text, verbatim. `../SKILL.md` governs loading; its rules apply
alongside.

Also load: `evidence.md`.

---

## CERTIFICATION EVIDENCE AUTHORITY

Applies only to a certification/approval predicate (for example a UL listing or
a CE declaration). Two separate questions:
- authority: who is authoritative for the certification claim
- applicability: does the record cover the exact candidate/configuration
Strong authority with unresolved applicability cannot support PASS.

Record the authority class of each certification/approval source in its
authority field with exactly one of these tokens:

CERTIFIER-PRIMARY
- a certificate, registry/database record or declaration issued and published
  by the certification body itself
- primary authority for whether the certification/listing exists, its current
  status when stated, the certificate/file/registry identity, and the scope the
  record explicitly shows
- may support PASS for the certification predicate when all are true:
  1. the frozen SPEC's authority_of_record is not MANUFACTURER_EVIDENCE_REQUIRED
  2. the record is current and applicable under the existing evidence rules
  3. the record covers the exact candidate/configuration under the existing
     applicability rules, with no unresolved scope restriction, note or footnote
  4. its document state is RETRIEVED
  5. HARD PASS TRACEABILITY is met
- such a record is Grade A for the certification predicate itself only, never
  for another requirement

MANUFACTURER-PRIMARY
- manufacturer evidence naming the certification: datasheet approvals section,
  compliance page, product page, manufacturer-hosted certificate, or the
  manufacturer's own declaration (for example an EU DoC); a certificate issued by
  the certification body but published by the manufacturer counts here and
  carries the certifier's authority for its content
- supports a certification predicate under the existing evidence rules
- if the frozen SPEC explicitly requires manufacturer evidence, only
  MANUFACTURER-PRIMARY evidence satisfies that wording; a CERTIFIER-PRIMARY
  record may corroborate it but does not substitute for it
- when certification is HARD, item 3 of the document set still applies: the
  current certification/declaration record (certificate, certifier registry
  record or declaration) is inspected or given a document state; an approvals
  section that names a certification is not that record

SECONDARY
- distributor, marketplace or reseller copies, search snippets, aggregators and
  other unauthenticated third-party claims
- cannot independently create a HARD certification PASS
- for the run's own retrieval, authority follows the publisher/host classes
  above, not who created the document: a manufacturer-created or
  certifier-created document retrieved from a distributor, marketplace or other
  third-party host is SECONDARY and Grade C. It counts as an opened source
  record, not as a primary manufacturer document. It may identify the primary
  record for DOCUMENT STATES and RETRIEVAL FALLBACK; in a fallback it is only an
  F4 lead, never the retrieved record. Human-supplied artifacts keep the
  provenance rules of HUMAN-SUPPLIED EVIDENCE
- an inspected SECONDARY claim that is explicitly applicable to the candidate
  is Grade C evidence: under the CHECK statuses it may support CONDITIONAL, not
  PASS. The requirement is UNKNOWN instead when a specific UNKNOWN rule
  applies, including:
  1. an applicable certification/declaration record that could determine the
     predicate is EXISTS_NOT_RETRIEVED or ACCESS_GATED; a SECONDARY source that
     names that record by issuer and certificate, file or document ID
     identifies it
  2. applicability depends on an unresolved qualifier, an undefined pattern or
     inference
  NOT_IDENTIFIED alone does not make it UNKNOWN
- a search snippet or other discovery lead is not verification evidence; it
  supports neither CONDITIONAL nor PASS

If applicability depends on a model pattern or a note/footnote the record does
not resolve, this rule grants no PASS; the existing status rules apply.

Document states apply unchanged: a certification record that is
EXISTS_NOT_RETRIEVED or ACCESS_GATED and could determine the predicate leaves it
UNKNOWN; NOT_IDENTIFIED does not erase otherwise sufficient checked evidence.

