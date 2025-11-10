# SUMMARIZER -- USING -- REASONING - CRITICAL

## Project Structure

```
ROOT
│
├── Config/
│    ├── config.json
│    └── keys.json
│
├── Data/
│    ├── LongK171
│    │    └── VNexpress
│    └── SurAyush
│         └── News_Summary_Dataset
│
├── Libraries/
│    ├── __init__.py
│    ├── Client_Llama.py
│    ├── Common_*.py
│    ├── Flow_*.py
│    ├── Processor_*.py
│    └── Tools_Json_Parser.py
│
├── Models/
│    ├── microsoft
│    │    └── Phi-3-mini-4k-instruct-gguf
│    └── Qwen
│         └── Qwen2.5-3B-Instruct-GGUF
│
├── Output/
│    ├── Histories-Batch-EN.json
│    └── Histories-Batch-VI.json
│
├── Prompts/
│    ├── EN-*.txt
│    └── VI-*.txt
│
├── Reports/
│
├── .gitignore
├── env.yml
├── llama_run.py
├── Main_Pipeline.ipynb├── Reports/
└── README.md
END
```
