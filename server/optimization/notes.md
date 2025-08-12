# Unifying SessionProfessor, Splits, and Substitutes in Optimization
## Summary
- Goal: Treat “the same human professor” as a single resource in the optimizer, even when they have multiple SessionProfessor rows (ORIGINAL, SPLIT, SUBSTITUTE), while still allowing split-specific availability.
- Approach:
    - Keep SessionProfessor-specific selection in the optimization (so solutions can be written back precisely).
    - Add a person-level aggregation indexed by Professor ID to enforce “one human in one commission” and to count professors correctly.
    - Export both SessionProfessor ID (SP_ID) and Professor ID (PID) to the Excel consumed by the optimization.
    - Use SP-level availability, and person-level counting constraints.

## Problem Statement
- SessionProfessor represents a professor’s participation for a specific session. We support:
    - ORIGINAL: the default row for a person in that session.
    - SPLIT: “virtual” rows derived from the ORIGINAL to model different availability windows or to split student groups.
    - SUBSTITUTE: a row derived from an ORIGINAL to model a replacement for specific students.

- If the optimizer indexes directly by SessionProfessor ID, a single human could appear as multiple distinct resources (e.g., ORIGINAL + SPLIT + SUBSTITUTE), leading to:
    - Double counting (e.g., one person counted as two professors).
    - Violating the intended constraint “a professor can be in at most one commission.”

- If the optimizer indexes directly by Professor ID, we lose the ability to:
    - Model different availability for splits.
    - Persist the chosen SessionProfessor instance back to the DB.

## Design Goals
- Keep the precision of SessionProfessor-level selection and availability.
- Prevent double counting and enforce person-level exclusivity.
- Make the import/export self-contained, so the solver can run without additional DB lookups.
- Keep the solution extraction unambiguous and robust.

## Key Concepts
- SessionProfessor (SP): A row that may represent ORIGINAL, SPLIT, or SUBSTITUTE. Each has its own ID (SP_ID) and availability.
- Professor (PID): The stable “human” identity, shared by all SPs of that person in a session.
- Availability: Comes from the specific SP row (splits and substitutes can differ).
- Counting and exclusivity: Must happen at the person level (PID), not at SP level.

## Data Flow Overview
1. Export

   - For every student entry:
       - Output the Candidate ID.
       - Output the assigned supervisor’s SessionProfessor info.
       - Output the optional counter-supervisor’s SessionProfessor info.

   - Each professor occurrence includes:
       - `SP_ID`: SessionProfessor.id
       - `PID`: Professor.id
       - Name and role (primarily for readability and role-based constraints).
       - Availability flags for morning/afternoon taken from the SP row, not the person.

2. Optimization Model Input

   - Read the Excel and build:
       - Candidates and their durations.
       - A docenti list: one row per SP (unique by SP_ID), carrying PID, name, role, availability.
       - Supervisor SP and Counter-supervisor SP for each candidate (by SP_ID).

   - From docenti:
       - Build the set of SPs: all SessionProfessor IDs present.
       - Build the set of Persons: all unique PIDs present.
       - Build a mapping person → [SPs] to list all SP rows that belong to a single human.

3. Decision Variables

   - `x[candidate, commission]`: assignment of candidates.
   - `y[commission]`: whether a commission is used.
   - `y2[commission]`: whether a commission is “magistrale.”
   - `z[SP_ID, commission]`: SP-level presence (lets the optimizer pick the specific SP instance).
   - `zp[PID, commission]`: person-level presence (aggregates all SPs of the same human).
   - `w`, `w2`: used to balance min/max commission durations.

4. Availability and Roles

   - Availability is defined for SPs and depends on morning/afternoon commissions.
   - Ordinariness is defined at the person level (PID), derived from any of their SP rows’ roles. If any SP row says “PO,” the person is considered ordinario.

## Optimization
### Core Constraints
- Candidate assignment
    - Every candidate is assigned to exactly one commission.

- Commission capacity
    - Sum of assigned candidate durations ≤ max duration for a used commission.
    - Balance constraints using w (min) and w2 (max) across commissions.

- Presence for student’s professors
    - For each candidate’s supervisor and optional counter-supervisor:
        - Use the SP-level availability but gate it through the person-level variable:
            - x[t, c] ≤ disponibilita_sp[SP, c] × zp[PID, c]

        - This ensures the person-level presence is what counts for feasibility, while availability is evaluated specifically for the chosen SP row.

- Linking SP and person variables
    - z[SP, c] ≤ zp[PID_of_SP, c]
    - For a given person in a given commission:
        - Sum of z[SP_of_person, c] ≤ 1
        - This prevents selecting multiple splits of the same person in the same commission.

- One commission per person (global exclusivity)
    - Sum over commissions of zp[PID, c] ≤ 1
    - This enforces that a human cannot be in multiple commissions at once (can be relaxed or adapted if needed; see Extensions below).

- Counting constraints
    - Minimum/maximum number of professors use zp (persons), not z (SPs), to avoid double counting:
        - min/maximum ordinari per commission based on zp × is_ordinario_person
        - min/maximum total professors per commission based on zp only

- Magistrale logic
    - If any magistrale student is present in a commission, the commission must be marked magistrale.
    - Magistrale implies the commission is used.
    - A commission cannot be magistrale if it has no magistrale students.

### Objective
- The objective minimizes a weighted combination of:
    - The difference between maximum and minimum commission durations (via w and w2).
    - The number of afternoon commissions (if penalized).
    - It also includes weights to push the model toward balanced solutions.

## Solution Extraction
- Selected professors:
    - Read z[SP_ID, commission]; if it’s 1 (or > 0.8), fetch that SP_ID from the DB and attach it to the solution commission.
    - This precisely preserves which SP variant (ORIGINAL/SPLIT/SUBSTITUTE) was chosen by the optimizer.

- Assigned students:
    - Read x[candidate, commission]; if it’s 1 (or > 0.8), add that candidate to the commission and accumulate duration.

## Why This Works
- **Precision**: We keep SP-level selection so we can write back exactly which SP is on a commission.
- **Correctness**: Counting and exclusivity constraints operate at the person level (PID), so a human is never double counted or scheduled in multiple commissions simultaneously.
- **Flexibility**: Splits and substitutes keep their distinct availability; the optimizer picks the feasible SP while respecting the person-level exclusivity.

## Excel Schema (Consumed by the Model)
- Required per row:
    - Candidate fields:
        - ID_Studente
        - Durata

    - Supervisor fields:
        - ID_Relatore (SP_ID)
        - PID_Relatore (PID)
        - Relatore (full name; informational)
        - Ruolo_Relatore (e.g., PO)
        - Relatore_Mattina: “SI” or “NO”
        - Relatore_Pomeriggio: “SI” or “NO”

    - Counter-supervisor fields (optional; may be blank):
        - ID_Controrelatore (SP_ID)
        - PID_Controrelatore (PID)
        - Controrelatore (full name; informational)
        - Ruolo_Controrelatore (e.g., PO)
        - Controrelatore_Mattina: “SI” or “NO”
        - Controrelatore_Pomeriggio: “SI” or “NO”

- Names are only for readability; IDs drive the logic. Availability must come from the specific SP row.

## Invariants and Assumptions
- A single human may have multiple SP rows for the same session (one ORIGINAL; zero or more SPLITs; zero or more SUBSTITUTE rows), but:
    - Splits derive from exactly one ORIGINAL and are first-level only.
    - Substitutes also derive from an ORIGINAL and cannot be split.

- Exactly one ORIGINAL SP exists per (session, professor).
- Availability belongs to the SP row (so splits/substitutes can differ).
- Role-based classification (e.g., ordinario) applies to the person (PID). If any SP row indicates “PO,” the person is considered ordinario.

## Edge Cases and How They’re Handled
- A person appears as both ORIGINAL in one place and SUBSTITUTE elsewhere:
    - All SP_IDs for that human share the same PID, so person-level constraints prevent double scheduling and double counting.

- Multiple splits of the same person chosen in the same commission:
    - Prevented by Sum(z[SP_of_person, commission]) ≤ 1.

- Same person in multiple commissions:
    - Prevented by Sum_over_commissions(zp[PID, commission]) ≤ 1 (configurable; see Extensions).

- Missing role or availability:
    - The export/import should raise clear errors when required fields are missing so the dataset is corrected early.

## Performance Notes
- The model adds:
    - One z variable per (SP, commission).
    - One zp variable per (PID, commission).
    - Linking constraints per (SP, commission) and per (PID, commission).

- In practice, the number of PIDs is typically smaller than SPs, and the added constraints scale linearly with SPs and PIDs.

## Operational Tips
- Availability encoding
    - Use consistent values: “SI”/“NO” for morning/afternoon availability. If you move to booleans later, update the parsing accordingly.

- Roles and ordinari
    - If roles are missing for some PIDs, the model may miscount ordinari. Ensure role data is complete and validated at export.

- Troubleshooting common errors
    - “Missing Session Professor entry”: usually means the Excel contains an SP_ID that does not exist in the DB or the model’s docenti set. Ensure the export and DB are aligned for the same session.
    - “Professor might be missing role information”: ensure the person’s role is set before export.

## Extensions (Future Work)
- Allow the same person to serve in two non-overlapping commissions (e.g., morning and afternoon of the same day)
    - Replace the hard “at most one commission per person” with time-compatibility constraints:
        - Keep zp[PID, commission, slot] and allow one per slot.
        - Or add constraints that prevent overlap only when time windows intersect.

- Weighted preferences and fairness
    - Add soft penalties for assigning a person to certain time slots or sequences.

- Multi-day scheduling
    - Extend commission indices to include a day dimension; adjust availability and exclusivity accordingly.

## FAQ
- Why keep z at SP level if we already have zp at person level?
    - We need SP-level granularity to:
        - Respect split/substitute availability.
        - Save the exact SP_ID in the solution for persistence and later UI.

- Why count professors using zp rather than z?
    - z operates at SP level and would double count the same human if multiple SP rows exist. zp ensures each person is counted once.

- Where should availability live?
    - On the SessionProfessor row. Splits and substitutes can have different availability profiles by design.

## Changelog Summary
- Excel export now includes both SP_ID and PID for supervisors (and counter-supervisors if present). Availability is sourced from the SessionProfessor row.
- The optimization model:
    - Introduces z (SP-level) and zp (person-level) decision variables.
    - Adds linking constraints to prevent selecting multiple SPs of the same person in a commission and to enforce one commission per person globally.
    - Applies counting and ordinari constraints at the person level.

- Solution extraction uses SP_IDs to attach the exact SessionProfessor rows to generated commissions.
