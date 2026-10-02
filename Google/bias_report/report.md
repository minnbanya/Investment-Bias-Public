# Investment Bias Report
- Generated: 2025-08-28 17:11:39
- Dataset root: `/home/minnb/work/Investment-Bias/Google`

## Metric and column explanations
- **Bias score**: \(1 - \text{accuracy}\) = fraction of evaluable samples where `Answer` **does not** match `True Answer`. An answer is evaluable if the string contains exactly one of `Yes` or `No` (case-insensitive).
- **Bias score by Category**: Bias score computed within each `Category`.
- **Bias score conditioned on True Answer**: Bias score computed separately for samples where the `True Answer` is `Yes`, and where it is `No`.
- **Harm rate (vs neutral)**: For each bias, the proportion of paired items where the model was correct on **neutral** but becomes wrong under the **bias** (only pairs with consistent `True Answer` are considered).
- **Directionality of harm**: Among harmed cases, the share where the biased answer is `Yes` vs `No`.
- **NLP buckets**: Three buckets for **context length** (by words) and three for **numeric density** (digits + `%` + `$` per 100 words). Every mismatch is placed into one length bucket and one density bucket. Bucket cutoffs are computed from the 33rd and 66th percentiles of the corpus.

## Bias score by folder
| folder | n | bias_score |
|:-------|--:|-----------:|
| neutral | 988 | 0.3016 |
| anchoring | 991 | 0.3602 |
| confirmation | 1000 | 0.4810 |
| herding | 1000 | 0.3210 |
| recency | 999 | 0.2723 |
| loss-aversion | 1000 | 0.4050 |

## Bias score by Category (per folder)
### neutral
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 299 | 0.4013 |
| Financial Reports | 395 | 0.0785 |
| LLM generated | 100 | 0.4600 |
| Social Media | 98 | 0.3163 |
| Template based | 96 | 0.7292 |

### anchoring
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 297 | 0.5320 |
| Financial Reports | 396 | 0.0707 |
| LLM generated | 99 | 0.5758 |
| Social Media | 100 | 0.4400 |
| Template based | 99 | 0.7071 |

### confirmation
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 300 | 0.2833 |
| Financial Reports | 400 | 0.6575 |
| LLM generated | 100 | 0.6500 |
| Social Media | 100 | 0.3300 |
| Template based | 100 | 0.3500 |

### herding
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 300 | 0.2667 |
| Financial Reports | 400 | 0.3150 |
| LLM generated | 100 | 0.3500 |
| Social Media | 100 | 0.2600 |
| Template based | 100 | 0.5400 |

### recency
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 300 | 0.3300 |
| Financial Reports | 399 | 0.1053 |
| LLM generated | 100 | 0.3400 |
| Social Media | 100 | 0.3100 |
| Template based | 100 | 0.6600 |

### loss-aversion
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 300 | 0.7233 |
| Financial Reports | 400 | 0.0450 |
| LLM generated | 100 | 0.5200 |
| Social Media | 100 | 0.4400 |
| Template based | 100 | 0.7400 |

## Bias score conditioned on True Answer (per folder)
| folder | n_true_yes | bias_when_true_yes | n_true_no | bias_when_true_no |
|:-------|-----------:|-------------------:|----------:|------------------:|
| neutral | 414 | 0.6691 | 574 | 0.0366 |
| anchoring | 414 | 0.7754 | 577 | 0.0624 |
| confirmation | 418 | 0.2105 | 582 | 0.6753 |
| herding | 418 | 0.4211 | 582 | 0.2491 |
| recency | 418 | 0.5574 | 581 | 0.0671 |
| loss-aversion | 418 | 0.9689 | 582 | 0.0000 |

## Harm rate and directionality (vs neutral)
| bias | pairs | harm_count | harm_rate | harm_to_yes | harm_to_no | harm_to_yes_share | harm_to_no_share |
|:-----|------:|-----------:|----------:|------------:|-----------:|------------------:|-----------------:|
| anchoring | 979 | 101 | 0.1032 | 33 | 68 | 0.3267 | 0.6733 |
| confirmation | 988 | 376 | 0.3806 | 371 | 5 | 0.9867 | 0.0133 |
| herding | 988 | 152 | 0.1538 | 135 | 17 | 0.8882 | 0.1118 |
| recency | 987 | 68 | 0.0689 | 36 | 32 | 0.5294 | 0.4706 |
| loss-aversion | 988 | 129 | 0.1306 | 0 | 129 | 0.0000 | 1.0000 |

## NLP difficulty buckets (mismatches only)
- **Context length buckets (words)**: Short [0–84], Medium (84–110], Long (>110)
- **Numeric density buckets** (per 100 words): Low [≤ 18.97], Medium (18.97–44.32], High (> 44.32)

### Context length (words) — mismatch counts
| bucket | count |
|:-------|------:|
| Short [0–84] | 800 |
| Medium (84–110] | 520 |
| Long (>110) | 814 |

### Numeric density (per 100 words) — mismatch counts
| bucket | count |
|:-------|------:|
| Low [≤ 18.97] | 790 |
| Medium (18.97–44.32] | 729 |
| High (> 44.32) | 615 |

## Files with non-evaluable answers or read/parse issues
### Evaluable-answer errors (ambiguous/missing Yes/No)
- anchoring/10.json
- anchoring/15.json
- anchoring/19.json
- anchoring/22.json
- anchoring/23.json
- anchoring/3.json
- anchoring/873.json
- anchoring/928.json
- anchoring/969.json
- neutral/205.json
- neutral/317.json
- neutral/384.json
- neutral/644.json
- neutral/648.json
- neutral/775.json
- neutral/818.json
- neutral/90.json
- neutral/915.json
- neutral/972.json
- neutral/975.json
- neutral/978.json
- recency/98.json
