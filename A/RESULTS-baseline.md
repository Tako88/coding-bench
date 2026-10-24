# Results: run baseline (benchmark A)

| model                                                                     | c1_csv_line     | c2_eval_expr    | c3_tokenize    | c4_schedule     | c5_shortest_match | score | out    |
|---------------------------------------------------------------------------|-----------------|-----------------|----------------|-----------------|-------------------|-------|--------|
| Qwen3.8-27B (ASCII-Condensed) UD-IQ4_XS + MTP (kv-stream fork, 98304 ctx) | P 147s 6.1k     | P 1733s 61.6k   | P 722s 29.9k   | P 791s 32.0k    | P 671s 27.7k      | 5/5   | 157.4k |
| Qwen3.8-Flash-Next GSQ-RCO Coder IQ1_M (PolyStrata, 98304 ctx)            | P 592s 23.6k    | P 316s 12.7k    | P 485s 18.3k   | P 350s 13.0k    | P 738s 26.7k      | 5/5   | 94.4k  |
| Qwen3.8-27B IQ3_XXS + MTP (llama.cpp router, 65536 ctx)                   | P 223s 6.7k     | F* 1800s 40.2k+ | P 1715s 40.2k  | F* 1800s 45+    | P 1588s 37.9k     | 3/5   | 125.1k |
| Swift-1.5-Qwen3.8-27B GSQ-RCO IQ3_XXS + MTP (llama.cpp router, 98304 ctx) | P 360s 10.9k    | P 441s 13.6k    | P* 1800s 39.1k | P 1095s 31.8k   | P 1292s 30.1k     | 5/5   | 125.4k |
| Qwen3.6-35B-A3B REAP-48 v2 Q4_K_M + DFlash (llama.cpp router, 131072 ctx) | P 276s 10.8k    | P 358s 15.5k    | P 532s 22.1k   | F 453s 22.4k    | F 1076s 44.3k     | 3/5   | 115.2k |
| Qwen3.6-35B-A3B UD-Q4_K_M (PolyStrata, 131072 ctx)                        | P 903s 35.7k    | F 542s 26.1k    | P 135s 5.7k    | F 1090s 42.8k   | F* 1800s 78+      | 2/5   | 110.4k |
| Ornith-1.5-35B Q4_K_M (PolyStrata, 131072 ctx)                            | P 59s 3.7k      | P 84s 5.5k      | P 193s 11.1k   | P 723s 34.5k    | P 299s 17.4k      | 5/5   | 72.3k  |
| Mellum2.1-12B-A2.5B-Thinking Q6_K (llama.cpp router, 131072 ctx)          | F 706s 45.4k    | P 209s 15.8k    | F 302s 22.2k   | F 274s 20.3k    | F 395s 27.9k      | 1/5   | 131.6k |
| LFM2.5-24B-A2B Q6_K (PolyStrata, 131072 ctx)                              | F* 1800s 61.6k+ | P 979s 39.3k    | F 1114s 42.1k+ | F 489s 22.9k    | F* 1800s 57.6k+   | 1/5   | 223.5k |
| Nemotron-3.5-Bolt-74B-A9B IQ2_XXS (PolyStrata, 131072 ctx)                | P 1170s 22.4k   | P 837s 13.2k    | P 1474s 21.6k  | F* 1800s 47.1k+ | P 893s 22.1k      | 4/5   | 126.3k |
| Flint Preview UD-Q4_K_XL (PolyStrata, 131072 ctx)                         | P 274s 11.8k    | P 163s 7.0k     | P 243s 7.6k    | P 589s 24.9k    | F 412s 16.6k      | 4/5   | 67.9k  |
| Ling-3.0-tiny Q8_0 (llama.cpp, 131072 ctx)                                | F 423s 33.4k    | F 466s 33.1k    | F 411s 32.8k   | F 410s 32.8k    | F 414s 32.8k      | 0/5   | 165.0k |

`*` = killed at the 1800s cap, file on disk graded afterwards

### samplers

| model                                                                     | sampling from | temperature | top_p | top_k | min_p | presence | repeat | thinking | cap   |
|---------------------------------------------------------------------------|---------------|-------------|-------|-------|-------|----------|--------|----------|-------|
| Qwen3.8-27B (ASCII-Condensed) UD-IQ4_XS + MTP (kv-stream fork, 98304 ctx) | request       | 1.0         | 0.95  | 20    | 0.0   | 0.0      | 1.0    | xhigh    | 1800s |
| Qwen3.8-Flash-Next GSQ-RCO Coder IQ1_M (PolyStrata, 98304 ctx)            | request       | 1.0         | 0.95  | 20    | 0.0   | 0.0      | 1.0    | xhigh    | 1800s |
| Qwen3.8-27B IQ3_XXS + MTP (llama.cpp router, 65536 ctx)                   | request       | 1.0         | 0.95  | 20    | 0.0   | 0.0      | 1.0    | xhigh    | 1800s |
| Swift-1.5-Qwen3.8-27B GSQ-RCO IQ3_XXS + MTP (llama.cpp router, 98304 ctx) | request       | 1.0         | 0.95  | 20    | 0.0   | 0.0      | 1.0    | xhigh    | 1800s |
| Qwen3.6-35B-A3B REAP-48 v2 Q4_K_M + DFlash (llama.cpp router, 131072 ctx) | request       | 0.6         | 0.95  | 20    | 0.0   | 0.0      | 1.0    | medium   | 1800s |
| Qwen3.6-35B-A3B UD-Q4_K_M (PolyStrata, 131072 ctx)                        | request       | 0.6         | 0.95  | 20    | 0.0   | 0.0      | 1.0    | medium   | 1800s |
| Ornith-1.5-35B Q4_K_M (PolyStrata, 131072 ctx)                            | request       | 0.6         | 0.95  | 20    | 0.0   | 0.0      | 1.0    | medium   | 1800s |
| Mellum2.1-12B-A2.5B-Thinking Q6_K (llama.cpp router, 131072 ctx)          | request       | 1.0         | 0.95  | 20    | 0.0   | 0.0      | 1.0    | medium   | 1800s |
| LFM2.5-24B-A2B Q6_K (PolyStrata, 131072 ctx)                              | request       | 0.6         | 0.95  | 50    | 0.0   | 0.0      | 1.05   | medium   | 1800s |
| Nemotron-3.5-Bolt-74B-A9B IQ2_XXS (PolyStrata, 131072 ctx)                | request       | 1.0         | 0.95  | -     | 0.0   | 0.0      | 1.0    | medium   | 1800s |
| Flint Preview UD-Q4_K_XL (PolyStrata, 131072 ctx)                         | request       | 1.0         | 0.95  | 20    | 0.0   | 0.0      | 1.0    | xhigh    | 1800s |
| Ling-3.0-tiny Q8_0 (llama.cpp, 131072 ctx)                                | request       | 1.0         | 0.95  | 20    | 0.0   | 0.0      | 1.0    | high     | 1800s |

### models

| model                            | params    | quant      | GiB   | drafter              | arch (blocks / experts)                    | ctx    | served by        |
|----------------------------------|-----------|------------|-------|----------------------|--------------------------------------------|--------|------------------|
| Qwen3.8-27B (ASCII-Condensed)    | 27B       | UD-IQ4_XS  | 12.63 | MTP inline           | qwen35 65 blk                              | 98304  | kv-stream fork   |
| Qwen3.8-Flash-Next GSQ-RCO Coder | -         | IQ1_M      | 54.40 | -                    | qwen4exp 48 blk / 256 exp (10 active)      | 98304  | PolyStrata       |
| Qwen3.8-27B                      | 27B       | IQ3_XXS    | 10.18 | MTP Q4_K_S 1.28 GiB  | qwen35 65 blk                              | 65536  | llama.cpp router |
| Swift-1.5-Qwen3.8-27B GSQ-RCO    | 27B       | IQ3_XXS    | 9.73  | MTP inline           | qwen35 65 blk                              | 98304  | llama.cpp router |
| Qwen3.6-35B-A3B REAP-48 v2       | 35B-A3B   | Q4_K_M     | 8.78  | DFlash Q6_K 0.31 GiB | qwen35moe 40 blk / 133 exp (8 active)      | 131072 | llama.cpp router |
| Qwen3.6-35B-A3B                  | 35B-A3B   | UD-Q4_K_M  | 20.61 | -                    | qwen35moe 40 blk / 256 exp (8 active)      | 131072 | PolyStrata       |
| Ornith-1.5-35B                   | 35B       | Q4_K_M     | 20.22 | -                    | qwen35moe 41 blk / 256 exp (8 active)      | 131072 | PolyStrata       |
| Mellum2.1-12B-A2.5B-Thinking     | 12B-A2.5B | Q6_K       | 10.13 | -                    | mellum 28 blk / 64 exp (8 active)          | 131072 | llama.cpp router |
| LFM2.5-24B-A2B                   | 24B-A2B   | Q6_K       | 18.34 | -                    | lfm2moe 40 blk / 64 exp (4 active)         | 131072 | PolyStrata       |
| Nemotron-3.5-Bolt-74B-A9B        | 74B-A9B   | IQ2_XXS    | 20.51 | -                    | nemotron_h_moe 88 blk / 496 exp (9 active) | 131072 | PolyStrata       |
| Flint Preview                    | -         | UD-Q4_K_XL | 23.33 | -                    | flint 49 blk / 256 exp (6 active)          | 131072 | PolyStrata       |
| Ling-3.0-tiny                    | -         | Q8_0       | 7.83  | -                    | bailingmoe3 24 blk / 128 exp (8 active)    | 131072 | llama.cpp        |
