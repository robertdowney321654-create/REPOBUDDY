import json
from pathlib import Path

import streamlit as st

from reviewer import (
    MAX_FILES,
    MAX_TOTAL_CHARS,
    MODEL,
    OllamaError,
    RepoPathError,
    ask_ollama,
    collect_source_files,
    make_review_prompt,
    parse_review,
    run_ruff,
)

LOGO_PATH = Path(__file__).with_name("logo.svg")
LOGO_SVG = LOGO_PATH.read_text(encoding="utf-8")

st.set_page_config(
    page_title="RepoBuddy · Local code review",
    page_icon=str(LOGO_PATH),
    layout="wide",
)
st.markdown(
    """
    <style>
    :root {
      --ink: #e8edf5; --muted: #9aa8bb; --panel: #151d2b; --line: #273448;
      --mint: #7ce0bb; --blue: #9cbaff;
    }
    .stApp { background: radial-gradient(ellipse at 82% 0%, #1c3043 0%, #101722 48%, #0c111a 100%); color: var(--ink); }
    html, body, [class*="css"] { font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: #111925; border-right: 1px solid var(--line); }
    .block-container { max-width: 1050px; padding-top: 2.4rem; padding-bottom: 3rem; }
    .brand { display:flex; align-items:center; gap:13px; margin-bottom:28px; }
    .brand-mark { width:46px; height:46px; display:grid; place-items:center; flex:0 0 46px; }
    .brand-mark svg { display:block; width:100%; height:100%; }
    .brand-name {
      font-family: "Trebuchet MS", "Segoe UI", sans-serif;
      font-size:20px;
      font-weight:800;
      letter-spacing:-.65px;
      color:var(--ink);
    }
    .brand-caption { font-size:12px; color:var(--muted); margin-top:2px; }
    .eyebrow { color:var(--mint); text-transform:uppercase; letter-spacing:2px; font-size:11px; font-weight:700; }
    .hero-title { font-size:clamp(34px, 5vw, 52px); line-height:1.04; letter-spacing:-2.5px;
      margin:9px 0 12px; font-weight:700; color:#f3f6fb; }
    .hero-copy { max-width:650px; color:#aab7c9; font-size:16px; line-height:1.65; margin-bottom:26px; }
    .section-label { color:#b8c5d6; font-size:13px; font-weight:700; letter-spacing:.2px; margin-bottom:8px; }
    .pill { display:inline-block; padding:5px 9px; margin:4px 4px 0 0; border-radius:20px;
      background:#1b2939; border:1px solid #2b3b50; color:#bdcbe0; font-size:11px; }
    .fine-print { color:#91a0b4; font-size:12px; line-height:1.6; }
    div[data-testid="stForm"] { border:1px solid var(--line); border-radius:18px; padding:20px 22px;
      background:linear-gradient(145deg, rgba(24,34,49,.92), rgba(17,25,37,.9));
      box-shadow:0 18px 50px rgba(0,0,0,.16); margin:14px 0 8px; }
    div[data-testid="stMetric"] { background:#151e2b; border:1px solid var(--line); padding:14px 16px; border-radius:14px; }
    div[data-testid="stMetricLabel"] { color:#9aa8bb; }
    div[data-testid="stMetricValue"] { color:#edf5ff; }
    button[kind="primaryFormSubmit"] { background:#7ce0bb; color:#10251f; border:0;
      border-radius:10px; height:46px; font-weight:700; }
    button[kind="primaryFormSubmit"]:hover { background:#a1f0d2; color:#10251f; }
    code, .stCode { font-family: ui-monospace, Consolas, monospace !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        f'<div class="brand"><div class="brand-mark">{LOGO_SVG}</div>'
        '<div><div class="brand-name">RepoBuddy</div>'
        '<div class="brand-caption">Private, local code review</div></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("#### How it works")
    st.markdown(
        "1. Choose a repository folder\n"
        "2. Review the files selected for analysis\n"
        "3. Get focused suggestions from Gemma 4"
    )
    st.divider()
    st.markdown("#### Supported file types")
    st.markdown(
        '<span class="pill">Python</span><span class="pill">JavaScript / TypeScript</span>'
        '<span class="pill">Java</span><span class="pill">C / C++ / C#</span>'
        '<span class="pill">Go</span><span class="pill">Rust</span><span class="pill">PHP</span>'
        '<span class="pill">Ruby</span><span class="pill">HTML / CSS</span>'
        '<span class="pill">Vue / Svelte</span><span class="pill">SQL</span>'
        '<span class="pill">Markdown / JSON / YAML</span>',
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown("#### Local & read-only")
    st.markdown(
        '<div class="fine-print">Gemma runs through Ollama on your machine. '
        'RepoBuddy does not edit project files. Check the included file list before sending it for review.</div>',
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="eyebrow">Local AI code reviewer</div>'
    '<div class="hero-title">A second pair of eyes<br>for your codebase.</div>'
    '<div class="hero-copy">Find practical improvements across your project with local Gemma 4 '
    'and lightweight static checks. Your code stays on this computer.</div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="section-label">Choose a repository to review</div>', unsafe_allow_html=True)
with st.form("review_form"):
    repo_path = st.text_input(
        "Repository folder",
        placeholder=r"C:\Users\you\projects\my-app",
        label_visibility="collapsed",
        help="Use an absolute path. Supported source and documentation files are scanned; dependencies and hidden folders are skipped.",
    )
    scan_submitted = st.form_submit_button("Scan folder", type="primary", use_container_width=True)
st.markdown(
    f'<div class="fine-print">Read-only scan · Up to {MAX_FILES} files / '
    f'{MAX_TOTAL_CHARS:,} characters · Model: {MODEL}</div>',
    unsafe_allow_html=True,
)

if scan_submitted:
    if not repo_path.strip():
        st.error("Enter the full path to a repository folder.")
        st.stop()
    try:
        scan = collect_source_files(repo_path.strip())
    except RepoPathError as exc:
        st.error(str(exc))
        st.stop()
    st.session_state["scan_path"] = str(Path(repo_path.strip()).resolve())
    st.session_state["scan_files"] = scan.files
    st.session_state["scan_warnings"] = scan.warnings
    st.session_state["confirm_files_reviewed"] = False

scan_files = st.session_state.get("scan_files", [])
scan_warnings = st.session_state.get("scan_warnings", [])
scan_path = st.session_state.get("scan_path")
try:
    current_path = str(Path(repo_path.strip()).resolve()) if repo_path.strip() else None
except OSError:
    current_path = None
path_matches_scan = bool(scan_path and current_path and scan_path.casefold() == current_path.casefold())

if scan_path and not path_matches_scan:
    st.warning("The folder path changed. Scan it again to review the current folder.")

if path_matches_scan:
    for warning in scan_warnings:
        st.warning(warning)
    if not scan_files:
        st.stop()

    st.warning(
        "Before continuing, check the file list below. RepoBuddy skips files that look sensitive, "
        "but automatic secret checks cannot catch everything. Only continue if you are comfortable "
        "sending these listed files to Gemma running locally through Ollama."
    )
    languages = sorted({Path(source.path).suffix.lstrip(".").upper() for source in scan_files})
    metric_columns = st.columns(3)
    metric_columns[0].metric("Files included", len(scan_files))
    metric_columns[1].metric("Languages", len(languages))
    metric_columns[2].metric("Characters reviewed", f"{sum(len(source.content) for source in scan_files):,}")

    with st.expander("Files that will be sent for review", expanded=True):
        for source in scan_files:
            st.code(source.path, language="text")

    reviewed_files = st.checkbox(
        "I checked this file list and want to send these files to my local Gemma model.",
        key="confirm_files_reviewed",
    )
    start_review = st.button(
        "Start plain-language review",
        type="primary",
        disabled=not reviewed_files,
        use_container_width=True,
    )

    if start_review:
        with st.spinner(
            "Gemma 4 is reviewing the selected files. First responses can take longer while the model loads."
        ):
            lint_findings, ruff_error = run_ruff(repo_path.strip(), scan_files)
            try:
                prompt = make_review_prompt(scan_files, lint_findings)
                model_response = ask_ollama(prompt)
            except OllamaError as exc:
                st.error(str(exc))
                st.stop()

        st.markdown("### Review results")
        result_columns = st.columns([1, 1.65], gap="large")
        with result_columns[0]:
            st.markdown("#### Quick checks")
            if ruff_error:
                st.warning(ruff_error)
            elif lint_findings:
                for finding in lint_findings:
                    location = (
                        f"{Path(finding.get('filename', 'unknown')).name}:"
                        f"{finding.get('location', {}).get('row', '?')}"
                    )
                    with st.expander("Small code cleanup suggestion"):
                        st.write(
                            "The automatic checker noticed a small code-style issue. "
                            "Fixing it can make this part of the project easier to read."
                        )
                        st.caption(f"Developer detail: {finding.get('message', '')}")
                        st.caption(f"File location: {location}")
            else:
                st.success("The automatic checks did not find any small code-style problems.")
            if not any(Path(source.path).suffix.casefold() == ".py" for source in scan_files):
                st.caption("These automatic checks cover Python only. Gemma reviews the other supported files.")

        with result_columns[1]:
            st.markdown("#### Suggestions in everyday language")
            review = parse_review(model_response)
            if review is None:
                st.warning("The review could not be organized into simple explanations. Here is Gemma's response:")
                st.markdown(model_response)
            else:
                summary = review.get("summary")
                if isinstance(summary, str) and summary.strip():
                    st.write(summary)
                findings = review["findings"]
                if not findings:
                    st.write(
                        "Gemma did not find a clear improvement to suggest in the files it checked. "
                        "That does not guarantee the project has no problems."
                    )
                for finding in findings:
                    if not isinstance(finding, dict):
                        continue
                    severity = str(finding.get("severity", "low")).casefold()
                    severity_label = {
                        "high": "Worth looking at soon",
                        "medium": "Worth improving",
                        "low": "Small improvement",
                    }.get(severity, "Suggestion")
                    explanation = finding.get("plain_english") or (
                        "Gemma found something that may be worth improving."
                    )
                    impact = finding.get("why_it_matters")
                    next_step = finding.get("next_step")

                    st.markdown(f"**{severity_label}**")
                    st.write(explanation)
                    if isinstance(impact, str) and impact.strip():
                        st.markdown(f"**Why it matters:** {impact}")
                    if isinstance(next_step, str) and next_step.strip():
                        st.markdown(f"**What you can do:** {next_step}")

                    location = finding.get("file")
                    line = finding.get("line")
                    if location or finding.get("technical_title"):
                        details = str(finding.get("technical_title") or "Technical details")
                        if location:
                            details += f" · {location}"
                        if isinstance(line, int):
                            details += f":{line}"
                        with st.expander(details):
                            st.caption("Optional detail for someone familiar with code.")

        with st.expander("Technical details (optional)", expanded=False):
            st.code(json.dumps(review, indent=2) if review is not None else model_response)

st.divider()
st.markdown(
    '<div class="fine-print">RepoBuddy gives suggestions, not guarantees. Verify important findings yourself. '
    'The reviewer never changes your source files.</div>',
    unsafe_allow_html=True,
)
