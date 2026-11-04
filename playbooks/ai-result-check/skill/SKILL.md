---
name: ai-result-check
description: Checks whether an AI-produced result (a report, analysis, summary, research file, calculation or workflow output) can be relied on before anyone acts on it or sends it. Tests repeatability, accuracy and completeness, checks the input and every source, looks for overstatement, gets an independent review, and labels the result as accurate to the raw data or directional only. Use when the user asks to verify, fact-check, double-check, cross-check or trust an AI result, or before an AI result goes to a client, a board or the public.
---

# AI Result Check

An AI result can read well and make sense on a first read and still be wrong, incomplete or partly made up. This skill tests a result before anyone relies on it. A person makes the final call.

**The three main thresholds:** repeatable, accurate, complete. Underneath those, as style: not overstated, not overbuilt.

## Step 1. Set the scope

Ask for what is missing, in one message:
- the result to check, and the prompt or workflow that produced it, if available
- the raw inputs and sources it should rest on
- who will rely on it, and what they will do with it

If the raw inputs are unavailable, say so. Everything that depends on them is then marked "could not check".

## Step 2. Test the whole thing first

If the prompt and inputs are available, run the same prompt several times from a clean start (three is a sensible minimum) and compare the results. List what changes between runs: numbers, findings, order, omissions.

- **Results agree and pass Step 3:** the workflow is a candidate to rely on for this task.
- **Results vary or fail Step 3:** break the work into smaller steps. Give each step its own check against something already known, get each step reliable, then link the steps back together.

## Step 3. Run the checks

Do these in order, and report every finding with its source line or cell.

1. **Input check.** Did the AI read everything? Compare what it reports (row count, column names, first and last row, a handful of sampled values, document and page counts) with the real file.
2. **Accuracy check.** Check every number, name, date and calculation against the raw source. Recalculate figures with a script or spreadsheet where possible. Mark each one: confirmed, partly supported, unsupported, or could not check.
3. **Source check.** Open every reference. Does it exist, and does it say what is claimed? Test quotes word for word against the source.
4. **Completeness check.** Compare with the original ask and the inputs. What was skipped, dropped or never answered?
5. **Overstatement check.** Look for stretches: a plan written up as done, one case made general, a figure more exact than its source, a quote tightened, a "may" turned into a "will".
6. **Overbuilt check.** Is anything there that nobody asked for and that adds nothing? Keep it simple.

## Step 4. Get an independent review

The checker should be independent of the writer. In increasing order of strength:

1. A fresh agent with no memory of the work, on the same model.
2. A different model reviewing the first model's work.
3. A workflow that routes the work between models automatically.

Give the reviewer the result and the sources, and leave out the reasoning behind the result. For anything high-stakes, a person also checks the items that matter most.

## Step 5. Label the result and hand it over

End with this block:

```
RESULT CHECK
Label: ACCURATE TO THE RAW DATA | DIRECTIONAL ONLY | NOT RELIABLE YET
Repeatable: yes / no / not tested
Accurate: X confirmed, X partly supported, X unsupported, X could not check
Complete: what is missing
Overstated: what was stretched
Must be checked by a person: the items that matter most
```

- **Accurate to the raw data:** every figure that matters was traced to its source.
- **Directional only:** the direction is sound, the detail is not exact. Say so in the result itself, so the next reader knows.
- **Not reliable yet:** say which step to fix first.

The AI flags. The person responsible decides. Present findings for that decision and leave the decision itself to them.

## Stop rule

Stop when a fresh independent review finds nothing new that would change a decision. Fix what is wrong and leave the rest. When correcting, avoid overcorrecting and keep it simple.

Never report a check as done if it was not run. Write "could not check" and say why.
