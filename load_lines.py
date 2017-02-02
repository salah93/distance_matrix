def load_unique_lines(source_path):
    if not source_path:
        return []
    with open(source_path, 'r') as f:
        lines = set((x.strip(', ;') for x in f))
    return sorted(filter(lambda x: x, lines))
