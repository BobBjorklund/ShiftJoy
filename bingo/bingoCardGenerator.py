import random

def bingoCardGenerator(phrases, num_boards):
    """
    Generate bingo boards from a list of phrases.
    
    Args:
        phrases: List of phrase strings (MUST be 48+)
        num_boards: Number of boards to generate
        
    Returns:
        dict: {0: [[row0], [row1], ...], 1: [[row0], [row1], ...], ...}
    """
    if len(phrases) < 48:
        raise ValueError(f"MUST provide at least 48 phrases for competitive play. Got {len(phrases)}.")
    
    boards = {}
    
    for board_num in range(num_boards):
        selected_phrases = random.sample(phrases, 24)
        random.shuffle(selected_phrases)
        selected_phrases.insert(12, "Free Space")
        board = [selected_phrases[i*5:(i+1)*5] for i in range(5)]
        boards[board_num] = board
    
    return boards