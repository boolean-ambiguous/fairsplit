# Digital Stewardship study — Google Forms import

This directory contains the two respondent-segment questionnaires (senior;
adult-child) for the Digital Stewardship study, as Google Apps Script files
that build the actual Google Form for you.

- `senior_survey.gs` — senior segment (account holder aged 55+)
- `adult_child_survey.gs` — adult-child segment (aged 40-65, parent in scope)

## Why a script instead of a plain import file

Google Forms has no built-in "import from text/CSV" feature. The most
reliable way to reproduce a structured instrument like this one in Forms is
a short Apps Script that calls the Forms API (`FormApp`) to build the form
programmatically — no add-ons, no manual retyping of ~50 items.

## How to generate a form

1. Go to [script.google.com](https://script.google.com) and create a new
   project.
2. Paste the full contents of one `.gs` file in, replacing the default
   `Code.gs` boilerplate.
3. At the top of the file, set `var FRAME = 'A';` or `'B'` (see below).
4. In the toolbar, select the function `createSeniorSurveyForm` (or
   `createAdultChildSurveyForm`) and click **Run**. Authorize the script
   the first time you run it.
5. Open **View > Logs** (or **Executions**) for the edit and live URLs of
   the form that was created in your Google Drive.
6. Re-run with the other `FRAME` value to generate the second framing copy.

Each run creates one new Google Form; nothing is modified in place.

## Design limitations of Google Forms for this study

The research notes already flag that a platform without native
randomisation is not adequate for this design (Qualtrics or SurveyMonkey is
the right tool for a fielded study). These scripts are provided for piloting
or review in Google Forms, with the gaps handled as follows:

- **Framing (between subjects).** Google Forms cannot randomly assign a
  respondent to a condition when the form loads. `FRAME` is fixed per
  generated copy instead: run each script twice (`FRAME = 'A'` and
  `FRAME = 'B'`) and split recruitment links roughly 50/50 between the two
  copies. This approximates random assignment at the recruitment level, not
  true per-respondent server-side randomisation.
- **Scenario order (within subjects).** The six scenarios are laid out in a
  fixed order (1 through 6) in the script. Forms cannot randomise item order
  across sections. If order effects matter, duplicate a copy with the
  `scenarios` array manually reordered and split traffic across those
  copies as well.
- **Segment quotas and compound screening.** The original design closes a
  segment at ~100-130 responses and requires age (S1) AND self-reported
  segment (S2) to agree. Forms can only branch navigation on a single
  answer at a time, so each script's `S2` branch enforces only the segment
  match for its own file; watch response counts manually and exclude
  age/segment mismatches during cleaning.

## What each script builds

Both scripts implement the full flow from the brief: welcome/consent with
an exit branch, screening with a segment-match exit branch, the base
service description, the six scenarios (each with the assigned framing
sentence prepended, followed by BI1, BI2, and WTP), the manipulation check,
the UTAUT2 batteries (PE, EE, SI, PV), the independence/identity-threat
items (IT1-IT3), background and controls (including `C1b` and `D1`, shown
only in the adult-child script, and the conditional `C2b` follow-up shown
only when `C2 = Yes`), and the debrief screen.

Item codes (S1, PE1, BI1, …) appear only as comments in the script source
for analysis/appendix purposes — they are not shown to respondents, per the
brief.

Before fielding, replace `RESEARCHER_CONTACT` near the top of each script
with the actual researcher name and email.
