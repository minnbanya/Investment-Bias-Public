# Investment Bias Report
- Generated: 2025-09-04 22:49:34
- Dataset root: `/home/minnb/work/Investment-Bias/OpenAI`

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
| neutral | 1000 | 0.2890 |
| anchoring | 1000 | 0.4050 |
| confirmation | 1000 | 0.4780 |
| herding | 1000 | 0.3090 |
| recency | 1000 | 0.3070 |
| loss-aversion | 1000 | 0.4080 |

## Bias score by Category (per folder)
### neutral
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 300 | 0.2000 |
| Financial Reports | 400 | 0.4225 |
| LLM generated | 100 | 0.0900 |
| Social Media | 100 | 0.1500 |
| Template based | 100 | 0.3600 |

### anchoring
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 300 | 0.4867 |
| Financial Reports | 400 | 0.3275 |
| LLM generated | 100 | 0.4800 |
| Social Media | 100 | 0.2400 |
| Template based | 100 | 0.5600 |

### confirmation
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 300 | 0.2300 |
| Financial Reports | 400 | 0.7900 |
| LLM generated | 100 | 0.4200 |
| Social Media | 100 | 0.2200 |
| Template based | 100 | 0.2900 |

### herding
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 300 | 0.1433 |
| Financial Reports | 400 | 0.5600 |
| LLM generated | 100 | 0.0600 |
| Social Media | 100 | 0.0800 |
| Template based | 100 | 0.2800 |

### recency
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 300 | 0.2000 |
| Financial Reports | 400 | 0.4700 |
| LLM generated | 100 | 0.0800 |
| Social Media | 100 | 0.1500 |
| Template based | 100 | 0.3600 |

### loss-aversion
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 300 | 0.7333 |
| Financial Reports | 400 | 0.0525 |
| LLM generated | 100 | 0.5200 |
| Social Media | 100 | 0.4100 |
| Template based | 100 | 0.7400 |

## Bias score conditioned on True Answer (per folder)
| folder | n_true_yes | bias_when_true_yes | n_true_no | bias_when_true_no |
|:-------|-----------:|-------------------:|----------:|------------------:|
| neutral | 418 | 0.2679 | 582 | 0.3041 |
| anchoring | 418 | 0.6053 | 582 | 0.2612 |
| confirmation | 418 | 0.0574 | 582 | 0.7801 |
| herding | 418 | 0.1435 | 582 | 0.4278 |
| recency | 418 | 0.2440 | 582 | 0.3522 |
| loss-aversion | 418 | 0.9665 | 582 | 0.0069 |

## Harm rate and directionality (vs neutral)
| bias | pairs | harm_count | harm_rate | harm_to_yes | harm_to_no | harm_to_yes_share | harm_to_no_share |
|:-----|------:|-----------:|----------:|------------:|-----------:|------------------:|-----------------:|
| anchoring | 1000 | 197 | 0.1970 | 43 | 154 | 0.2183 | 0.7817 |
| confirmation | 1000 | 287 | 0.2870 | 280 | 7 | 0.9756 | 0.0244 |
| herding | 1000 | 98 | 0.0980 | 81 | 17 | 0.8265 | 0.1735 |
| recency | 1000 | 83 | 0.0830 | 53 | 30 | 0.6386 | 0.3614 |
| loss-aversion | 1000 | 292 | 0.2920 | 0 | 292 | 0.0000 | 1.0000 |

## NLP difficulty buckets (mismatches only)
- **Context length buckets (words)**: Short [0–84], Medium (84–110], Long (>110)
- **Numeric density buckets** (per 100 words): Low [≤ 18.98], Medium (18.98–44.33], High (> 44.33)

### Context length (words) — mismatch counts
| bucket | count |
|:-------|------:|
| Short [0–84] | 721 |
| Medium (84–110] | 769 |
| Long (>110) | 706 |

### Numeric density (per 100 words) — mismatch counts
| bucket | count |
|:-------|------:|
| Low [≤ 18.98] | 548 |
| Medium (18.98–44.33] | 846 |
| High (> 44.33) | 802 |

## Files with non-evaluable answers or read/parse issues
_None detected._
