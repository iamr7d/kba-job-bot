def score(title, search_roles):
    import difflib
    if not title or not search_roles:
        return 0
    title = title.lower()
    best = 0
    for role in search_roles:
        if not isinstance(role, str):
            continue
        role = role.lower()
        ratio = difflib.SequenceMatcher(None, title, role).ratio()
        best = max(best, int(ratio * 100))
    return best

def summarize(job):
    # Placeholder for future summarization logic
    return job.get('description', '')[:500]

def get_desc(url):
    # Placeholder for scraping job descriptions from URLs
    return ""
