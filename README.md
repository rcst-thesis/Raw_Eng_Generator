# English Sentence Dataset Generator (v5)

Streams unique, human-like English sentences into chunked `.txt` files
(`id,english_text` per line) for building translation datasets.

v5 adds **topic selection**: choose exactly what the sentences are about.

## Quick start

```bash
python main.py
```

With no flags you get two prompts: a topic menu, then a folder picker.

```bash
python main.py --list-categories              # see every topic and group
python main.py --category school --preview 20 # sample 20 lines, write nothing
python main.py -c animals -c nature --total-rows 50000
python main.py --category travelpack --output-dir ./output
python main.py --category all --total-rows 1000000 --rows-per-chunk 5000
```

## Categories

45 topics, e.g. `school`, `people`, `animals`, `nature`, `conversation`,
`greetings`, `family`, `kids`, `home`, `food`, `shopping`, `clothing`,
`health`, `fitness`, `travel`, `directions`, `transport`, `city`, `work`,
`jobs`, `business`, `money`, `support`, `law`, `technology`, `internet`,
`gaming`, `news`, `culture`, `celebrations`, `arts`, `hobbies`, `sports`,
`farming`, `weather`, `environment`, `science`, `history`, `philosophy`,
`emotions`, `relationships`, `emergencies`, `numbers`, `basics`, `stories`.

Groups expand to several topics at once:

| group | contents |
|---|---|
| `daily` | greetings, conversation, basics, home, food, shopping, directions, transport, numbers, emergencies |
| `travelpack` | greetings, conversation, travel, directions, transport, food, shopping, emergencies, numbers |
| `beginner` | basics, greetings, conversation, numbers, kids, school, home |
| `academic` | school, science, history, philosophy, law, news |
| `worklife` | work, jobs, business, money, support, technology |
| `world` | animals, nature, environment, weather, farming, culture |

Selecting a category also reweights the generation strategies — conversational
topics produce more dialogue and everyday phrasing, `stories` produces
narration, `philosophy` produces reflection, and so on.

## Output files

| selection | file pattern |
|---|---|
| `all` (default) | `eng_L_A_001.txt` |
| one topic | `eng_school_A_001.txt` |
| several topics | `eng_animals-nature_A_001.txt` |

Each prefix keeps its own `A → Z` series, so re-running a topic in the same
folder continues at the next letter instead of overwriting.

Deduplication is shared across the whole output folder via `.seen_hashes.bin`,
so no sentence is ever produced twice in that folder — even across runs and
across categories. The cache is checkpointed every 50,000 rows.

Every run appends its seed and settings to `runs.log`; pass `--seed` to
reproduce a run exactly.

## Files

| file | role |
|---|---|
| `main.py` | entry point, run banner, run log |
| `cli.py` | argument parsing, interactive topic and folder pickers |
| `config.py` | run configuration, file naming, series letters |
| `categories.py` | topic definitions and groups |
| `generator.py` | sentence engine, shared word banks, dedup, safety filter |
| `content_domains.py` | v5 domain packs (subjects/verbs/objects/questions) |
| `content_pools.py` | v5 phrase pools and dialogue sections |
| `streamer.py` | chunked writer, progress bars, preview mode |

## Adding a topic

1. Add sentences to `content_pools.py` (`EXTRA_POOLS` / `EXTRA_DIALOGUE`),
   and/or a domain to `content_domains.py`.
2. Register a `Category` in `categories.py` pointing at those names.

Nothing else needs to change — the CLI menu, validation, and file naming pick
it up automatically.
