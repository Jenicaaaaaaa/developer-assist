import requests
from devassist.indexer import query_codebase

OLLAMA_URL = "http://localhost:11434/api/generate"


def query_ollama(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]


def ask(question):
    results = query_codebase(question, n_results=8)
    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]

    context = ""
    for chunk, meta in zip(chunks, metadatas):
        context += f"\n--- {meta['filepath']} (lines {meta['start_line']}-{meta['end_line']}) ---\n"
        context += chunk + "\n"

    prompt = (
        "You are an expert code assistant analyzing a developer codebase.\n\n"
        "Here are the most relevant parts of their code:\n\n"
        + context +
        "\nAnswer this question about the codebase: " + question + "\n\n"
        "Rules:\n"
        "- Quote exact variable names, function names, and values from the code above\n"
        "- Reference exact file names and line numbers\n"
        "- Include specific technical terms from the code\n"
        "- Do not give generic answers\n"
        "- Do not ask for more information"
    )

    answer = query_ollama(prompt)

    # Build citations from retrieved chunks
    citations = "\n\n---\n📚 **Sources:**\n"
    seen = set()
    for meta in metadatas:
        key = f"{meta['filepath']}:{meta['start_line']}"
        if key not in seen:
            citations += f"  📄 `{meta['filepath']}` (lines {meta['start_line']}-{meta['end_line']})\n"
            seen.add(key)

    return answer + citations

def debug(error):
    results = query_codebase(error, n_results=8)
    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]

    context = ""
    for chunk, meta in zip(chunks, metadatas):
        context += f"\n--- {meta['filepath']} (lines {meta['start_line']}-{meta['end_line']}) ---\n"
        context += chunk + "\n"

    prompt = (
        "You are an expert software engineer helping debug a code error.\n\n"
        "Here are the most relevant parts of the codebase:\n\n"
        + context +
        "\nError or stack trace:\n" + error + "\n\n"
        "Please:\n"
        "1. Explain what is causing this error in plain English\n"
        "2. Point to the exact file and line number where the issue likely is\n"
        "3. Give the exact fix with corrected code\n"
        "4. Explain why your fix works"
    )

    return query_ollama(prompt)


def summarize(repo_path="."):
    results = query_codebase("main purpose architecture modules", n_results=8)
    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]

    context = ""
    for chunk, meta in zip(chunks, metadatas):
        context += f"\n--- {meta['filepath']} ---\n"
        context += chunk + "\n"

    prompt = (
        "You are an expert software engineer. Analyze this codebase and give a concise summary.\n\n"
        "Code samples from the project:\n\n"
        + context +
        "\nPlease provide:\n"
        "1. What this project does in 2-3 sentences\n"
        "2. The main modules/files and what each does\n"
        "3. The key technologies and patterns used\n"
        "4. Any notable architectural decisions"
    )

    return query_ollama(prompt)


def explain_diff(repo_path="."):
    import git

    try:
        repo = git.Repo(repo_path, search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        return "No git repository found at this path."

    staged = repo.git.diff("--cached")
    unstaged = repo.git.diff()

    diff_text = ""
    if staged:
        diff_text += "=== STAGED CHANGES ===\n" + staged + "\n"
    if unstaged:
        diff_text += "=== UNSTAGED CHANGES ===\n" + unstaged + "\n"

    if not diff_text:
        diff_text = repo.git.diff("HEAD~1", "HEAD")

    if not diff_text:
        return "No changes detected in this repository."

    if len(diff_text) > 4000:
        diff_text = diff_text[:4000] + "\n... (truncated)"

    prompt = (
        "You are a senior software engineer reviewing code changes.\n\n"
        "Here is a git diff:\n\n"
        + diff_text +
        "\n\nPlease:\n"
        "1. Summarize what changed in plain English\n"
        "2. Explain WHY these changes were likely made\n"
        "3. Flag any potential bugs or security issues\n"
        "4. Rate the change as: Safe / Review Needed / Risky"
    )

    return query_ollama(prompt)


def generate_commit(repo_path="."):
    import git

    try:
        repo = git.Repo(repo_path, search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        return "No git repository found at this path."

    staged = repo.git.diff("--cached")

    if not staged:
        return "No staged changes found. Run git add first."

    if len(staged) > 4000:
        staged = staged[:4000] + "\n... (truncated)"

    prompt = (
        "You are an expert software engineer. Generate a git commit message.\n\n"
        "Git diff:\n"
        + staged +
        "\n\nRules:\n"
        "- Use conventional commits format: type(scope): description\n"
        "- Types: feat, fix, refactor, docs, chore, test\n"
        "- First line max 72 characters\n"
        "- Add 2-3 bullet points explaining what and why\n"
        "- Generate only the commit message, nothing else"
    )

    return query_ollama(prompt)


def review_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()
    except FileNotFoundError:
        return f"File not found: {filepath}"

    if len(code) > 5000:
        code = code[:5000] + "\n... (truncated)"

    prompt = (
        "You are a senior software engineer doing a thorough code review.\n\n"
        "File: " + filepath + "\n\nCode:\n"
        + code +
        "\n\nPlease review and provide:\n"
        "1. Summary - What this file does\n"
        "2. Bugs - Any logic errors\n"
        "3. Security Issues - Any vulnerabilities\n"
        "4. Code Quality - Bad practices\n"
        "5. Performance - Any inefficiencies\n"
        "6. Suggestions - Top 3 improvements with example code\n"
        "7. Overall Rating - Score out of 10"
    )

    return query_ollama(prompt)