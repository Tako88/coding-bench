# Results: run flint-q4kxl (benchmark A)

| model                                                                     | c1_csv_line | c2_eval_expr | c3_tokenize | c4_schedule | c5_shortest_match | score | out |
|---------------------------------------------------------------------------|-------------|--------------|-------------|-------------|-------------------|-------|-----|
| Qwen3.8-27B (ASCII-Condensed) UD-IQ4_XS + MTP (kv-stream fork, 98304 ctx) | -           | -            | -           | -           | -                 | 0/5   | 0   |
| Qwen3.8-Flash-Next GSQ-RCO Coder IQ1_M (PolyStrata, 98304 ctx)            | -           | -            | -           | -           | -                 | 0/5   | 0   |
| Ornith-1.5-35B Q4_K_M (PolyStrata, 131072 ctx)                            | -           | -            | -           | -           | -                 | 0/5   | 0   |
| Flint Preview UD-Q4_K_XL (PolyStrata, 131072 ctx)                         | -           | -            | -           | -           | -                 | 0/5   | 0   |



### samplers

| model                                                                     | sampling from | temperature | top_p | top_k | min_p | presence | repeat | thinking | cap   |
|---------------------------------------------------------------------------|---------------|-------------|-------|-------|-------|----------|--------|----------|-------|
| Qwen3.8-27B (ASCII-Condensed) UD-IQ4_XS + MTP (kv-stream fork, 98304 ctx) | request       | 1.0         | 0.95  | 20    | 0.0   | 0.0      | 1.0    | xhigh    | 1800s |
| Qwen3.8-Flash-Next GSQ-RCO Coder IQ1_M (PolyStrata, 98304 ctx)            | request       | 1.0         | 0.95  | 20    | 0.0   | 0.0      | 1.0    | xhigh    | 1800s |
| Ornith-1.5-35B Q4_K_M (PolyStrata, 131072 ctx)                            | request       | 0.6         | 0.95  | 20    | 0.0   | 0.0      | 1.0    | medium   | 1800s |
| Flint Preview UD-Q4_K_XL (PolyStrata, 131072 ctx)                         | request       | 1.0         | 0.95  | 20    | 0.0   | 0.0      | 1.0    | xhigh    | 1800s |

### models

| model                            | params | quant      | GiB   | drafter    | arch (blocks / experts)               | ctx    | served by      |
|----------------------------------|--------|------------|-------|------------|---------------------------------------|--------|----------------|
| Qwen3.8-27B (ASCII-Condensed)    | 27B    | UD-IQ4_XS  | 12.63 | MTP inline | qwen35 65 blk                         | 98304  | kv-stream fork |
| Qwen3.8-Flash-Next GSQ-RCO Coder | -      | IQ1_M      | 54.40 | -          | qwen4exp 48 blk / 256 exp (10 active) | 98304  | PolyStrata     |
| Ornith-1.5-35B                   | 35B    | Q4_K_M     | 20.22 | -          | qwen35moe 41 blk / 256 exp (8 active) | 131072 | PolyStrata     |
| Flint Preview                    | -      | UD-Q4_K_XL | 23.33 | -          | flint 49 blk / 256 exp (6 active)     | 131072 | PolyStrata     |
