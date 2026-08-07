def reconstruct_abstract(inverted_index: dict | None) -> str:
    """
    Reconstruct an abstract from OpenAlex's inverted index format.
    
    OpenAlex stores abstracts as a dictionary where keys are words 
    and values are lists of positions (indices) in the original text.
    """
    if not inverted_index:
        return ""
        
    max_pos = 0
    for positions in inverted_index.values():
        if positions:
            max_pos = max(max_pos, max(positions))
            
    words = [""] * (max_pos + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            if pos < len(words):
                words[pos] = word
                
    return " ".join(words).strip()