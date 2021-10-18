# Explanations/answers to both the non- & brought- problems

First, let me mention that I've mentioned most of the concerns a real engineer would have when watches this codebase (and would never make those mistakes), but of course, here I'll gather the major ones too.

# Run the tool:
**Python version that was used during the development:** *Python 3.9.5 (tags/v3.9.5:0a7dcbd, May  3 2021, 17:27:52)*

**There is no additional dependencies to be installed.**

First step: `cd data_engineer_exercise`

To get the help menu: `python -m radiology_dataextractor -h`
```Python

```

To process the inputs: `python -m radiology_dataextractor -p samples/pacs.json.csv -r samples/ris.csv -l samples/lims.txt`

It produces the following file: `output.ml.json`. It is not configurable in this version.


# Concerns
Along the way I've realized, that the 3 inputs can be joined not just by the `patient_id` but by the `accession_number` as well.
So instead of concatenating/chaining them only by one element mentioned above from the two, should have been used all the _common_ elements, as one- or the other could be missing, which would cause serious data-leaks.

Also I've realized that the `patient_id` in the LIMS format is proceeded with a string of 3 chars: **MVZ**, which is questionable if is always there.
In the same file what is not handled in a proper way is the other data misses from each _row_.

## Processing
There is a huge risk in this section: every data is joined at once, hence the data is stored in memory, which could lead us to eat up all the memory (that's why we have distributed systems in an environment).
The reasonable & possible solutions that i can think of now:
* if we have enough hardware, use dedicated tools (like Spark -- as it has a python interface as well) to use up as much memory
 as we can
* or, if we have more storage than RAM than the way to go (which slows down, but in theory it has no physical limit) to store in a key:value (or full-text-search) based DB to make the data aggregation there. 

## Output
Some radiology report attributes are missing/incorrect:
* side: None
* not all the dates have been shifted, but could be done easily in the same way just as the others were done

I left the output in an inconsistent state due to the datetime formats, so in this case, let's skip that part.
Another point is relevant here, that the IDs are randomized now, which makes the output almost useless, creating as much
 patients as unique IDs we have in the output. This should be solved (and applied on every ID) based:
* on a table, where we associate a new ID for each patiente
* or, hash their ID to be consistent (**)

For producing the output, while this solution is slower than just using raw jsons troughout the whole process, in the long-term I found to be more beneficial if I use dedicated classes in this case, as because it does matter how easy is for us to follow what attributes do we need, cannot typo them because we're getting help from the IDE, etc.
If it turns out that this slows down the processing with a relevant amount of time, another consideration should be made using somewhat similar approach.
