# RepoBuddy

RepoBuddy is a local, read-only AI reviewer for code repositories. It asks Gemma 4 through Ollama for a concise review, explains suggestions in everyday language, and runs Ruff on Python files for additional static findings. It supports common source and documentation formats across several languages; it does not modify the repository or guarantee that every defect will be found.

## Requirements

- Windows, macOS, or Linux
- Python 3.10 or newer
- [Ollama](https://ollama.com/download) running locally
- Gemma 4 pulled in Ollama (`ollama pull gemma4:e4b`)

## Setup on Windows (PowerShell)

From this `RepoBuddy` folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
ollama pull gemma4:e4b
streamlit run app.py
```

If PowerShell blocks virtual-environment activation:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Ollama Desktop normally runs the local service in the background. If needed, start `ollama serve` in a separate terminal. In the app, enter the absolute path to the repository and click **Review repository**.

## Supported files

RepoBuddy reviews common files with these extensions: Python, JavaScript, TypeScript, JSX/TSX, Java, Kotlin, C/C++, C#, Go, Rust, PHP, Ruby, Swift, HTML, CSS/SCSS, Vue, Svelte, SQL, GraphQL, XML, JSON, YAML, TOML, shell scripts, and Markdown.

For responsiveness, each review includes up to 15 files, 75 KB per file, and 16,000 characters total. Hidden files/folders, symlinks, common dependency/build directories, lockfiles, minified files, likely credential files, and files matching secret-assignment, private-key, or common provider-token patterns are skipped. Before sending anything to Gemma, the interface shows the included file list and asks you to confirm it.

Ruff is run only on Python files. Other supported formats are reviewed by the model.

## Privacy and limitations

The app sends selected source and Ruff results to the local Ollama service at `http://localhost:11434`; it does not use a cloud model API. Secret detection is heuristic and cannot guarantee that all secrets are excluded. It errs on the side of caution by excluding a whole file when a likely secret is detected, but new or unusually formatted credentials may go unnoticed. Review the included-file list and confirm before starting, especially when working with private or sensitive repositories. Model suggestions may be incorrect or incomplete; verify them yourself.

RepoBuddy does not execute repository code, apply fixes, authenticate users, or provide a security guarantee.

## Tests

```powershell
python -m unittest -v
```

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
