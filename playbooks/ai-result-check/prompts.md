# Copy-paste prompts

These work in any AI tool (ChatGPT, Copilot, Gemini, Claude). Run them in a **new chat**, and ideally in a **different model** from the one that produced the result. Attach the result and the raw sources, and replace the text in [brackets].

These prompts catch a lot and still miss things. For anything that matters, a person checks the items that matter most.

## 1. Did it read everything?

```
Read the attached file. Before doing anything else, tell me:
the number of rows (or pages), the column names (or headings), the first and last row (or page), and the exact values of these five rows: [row numbers].
Do no analysis yet. If you could not read part of the file, say which part.
```

Compare the answer with the real file. Start the analysis only once it matches.

## 2. Accuracy

```
You did not write the attached result. Check it against the attached sources.
List every number, name, date, calculation and factual claim. For each one, give:
- the claim as written
- where it appears in the sources (file and line, cell or page), quoted word for word
- a verdict: CONFIRMED, PARTLY SUPPORTED, UNSUPPORTED or COULD NOT CHECK
Recalculate every figure. Do not fix anything. Do not assume a claim is right because it sounds plausible. If you cannot find a claim in the sources, say so.
```

## 3. Sources

```
List every reference, link and quote in the attached result. For each one, open or look up the source and tell me:
does it exist, does it say what the result claims, and does the quote match word for word?
If you cannot open a source, write COULD NOT CHECK. Do not guess.
```

## 4. Completeness

```
Here is what was asked: [paste the original ask].
Compare it with the attached result and the attached sources.
What was asked and not answered? What is in the sources that matters for this question and is missing from the result? Which rows, sections or cases were skipped?
Rank the gaps by how much they could change a decision.
```

## 5. Overstatement

```
Read the attached result against its sources and look only for stretches:
a plan or announcement written up as done, one example made into a general rule, a figure more exact than its source, a quote made sharper than the original, a "may" turned into a "will", and any conclusion stronger than the evidence.
For each one, give the sentence, the source wording and a corrected sentence.
```

## 6. Repeatability

Run the same prompt in three new chats, then paste all three results into a fourth:

```
These are three results from the same prompt and the same inputs. Compare them.
List every difference in numbers, findings and conclusions, and every item that appears in only some of them.
Which parts can I rely on, and which parts changed between runs?
```

If the results differ on anything that matters, break the work into smaller steps and test each step the same way.

## 7. Label it

```
Based on the checks above, end the result with one label and the reason for it:
ACCURATE TO THE RAW DATA: every figure that matters was traced to its source.
DIRECTIONAL ONLY: the direction is sound, the detail is not exact.
NOT RELIABLE YET: say what to fix first.
Then list the items a person must still check before anyone acts on this.
```
