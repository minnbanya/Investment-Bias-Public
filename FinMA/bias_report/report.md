# Investment Bias Report
- Generated: 2025-08-18 09:42:59
- Dataset root: `/home/minnb/work/Investment-Bias/FinMA`

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
| neutral | 1000 | 0.4660 |
| anchoring | 999 | 0.4214 |
| confirmation | 999 | 0.5275 |
| herding | 999 | 0.4715 |
| recency | 999 | 0.4474 |
| loss-aversion | 999 | 0.3824 |

## Bias score by Category (per folder)
### neutral
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 300 | 0.2733 |
| Financial Reports | 400 | 0.7775 |
| LLM generated | 100 | 0.0400 |
| Social Media | 100 | 0.1800 |
| Template based | 100 | 0.5100 |

### anchoring
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 300 | 0.4300 |
| Financial Reports | 400 | 0.5150 |
| LLM generated | 99 | 0.1414 |
| Social Media | 100 | 0.1900 |
| Template based | 100 | 0.5300 |

### confirmation
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 300 | 0.3167 |
| Financial Reports | 400 | 0.9125 |
| LLM generated | 99 | 0.1717 |
| Social Media | 100 | 0.1800 |
| Template based | 100 | 0.3200 |

### herding
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 299 | 0.2207 |
| Financial Reports | 400 | 0.8425 |
| LLM generated | 100 | 0.0800 |
| Social Media | 100 | 0.1800 |
| Template based | 100 | 0.4200 |

### recency
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 300 | 0.2767 |
| Financial Reports | 400 | 0.7575 |
| LLM generated | 100 | 0.0500 |
| Social Media | 99 | 0.1414 |
| Template based | 100 | 0.4200 |

### loss-aversion
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 299 | 0.6321 |
| Financial Reports | 400 | 0.1450 |
| LLM generated | 100 | 0.3200 |
| Social Media | 100 | 0.3500 |
| Template based | 100 | 0.6800 |

## Bias score conditioned on True Answer (per folder)
| folder | n_true_yes | bias_when_true_yes | n_true_no | bias_when_true_no |
|:-------|-----------:|-------------------:|----------:|------------------:|
| neutral | 418 | 0.2871 | 582 | 0.5945 |
| anchoring | 417 | 0.4652 | 582 | 0.3900 |
| confirmation | 417 | 0.1271 | 582 | 0.8144 |
| herding | 417 | 0.2206 | 582 | 0.6512 |
| recency | 417 | 0.2302 | 582 | 0.6031 |
| loss-aversion | 417 | 0.7842 | 582 | 0.0945 |

## Harm rate and directionality (vs neutral)
| bias | pairs | harm_count | harm_rate | harm_to_yes | harm_to_no | harm_to_yes_share | harm_to_no_share |
|:-----|------:|-----------:|----------:|------------:|-----------:|------------------:|-----------------:|
| anchoring | 999 | 166 | 0.1662 | 46 | 120 | 0.2771 | 0.7229 |
| confirmation | 999 | 171 | 0.1712 | 143 | 28 | 0.8363 | 0.1637 |
| herding | 999 | 130 | 0.1301 | 80 | 50 | 0.6154 | 0.3846 |
| recency | 999 | 121 | 0.1211 | 72 | 49 | 0.5950 | 0.4050 |
| loss-aversion | 999 | 236 | 0.2362 | 13 | 223 | 0.0551 | 0.9449 |

## NLP difficulty buckets (mismatches only)
- **Context length buckets (words)**: Short [0–84], Medium (84–110], Long (>110)
- **Numeric density buckets** (per 100 words): Low [≤ 19.05], Medium (19.05–44.33], High (> 44.33)

### Context length (words) — mismatch counts
| bucket | count |
|:-------|------:|
| Short [0–84] | 872 |
| Medium (84–110] | 1100 |
| Long (>110) | 742 |

### Numeric density (per 100 words) — mismatch counts
| bucket | count |
|:-------|------:|
| Low [≤ 19.05] | 521 |
| Medium (19.05–44.33] | 1030 |
| High (> 44.33) | 1163 |

## Files with non-evaluable answers or read/parse issues
### Evaluable-answer errors (ambiguous/missing Yes/No)
- anchoring/401.json
- confirmation/107.json
- herding/583.json
- loss-aversion/669.json
- recency/590.json
