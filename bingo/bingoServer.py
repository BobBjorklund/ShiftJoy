import uuid
import json
import sys
from .bingoCardGenerator import bingoCardGenerator


def create_game(game_id, num_boards, phrases):
    """
    Generate complete game data structure.
    
    Args:
        game_id: UUID string for the game
        num_boards: Number of boards/players
        phrases: List of 48+ phrase strings
        
    Returns:
        dict: Complete game state including board assignments and player links
    """
    boards = bingoCardGenerator(phrases, num_boards)
    
    board_assignments = {}
    player_links = []
    
    for board_num in range(num_boards):
        board_uuid = str(uuid.uuid4())
        board_assignments[board_uuid] = {
            "board_num": board_num,
            "board_data": boards[board_num],
            "assigned": False,
            "player_id": None
        }
        
        # Domain placeholder - will be replaced by Django settings
        link = f"website.com/bingo/games/{game_id}/{board_uuid}"
        player_links.append(link)
    
    return {
        "game_id": game_id,
        "num_boards": num_boards,
        "board_assignments": board_assignments,
        "player_links": player_links,
        "phrases_called": [],
        "game_state": "waiting",  # waiting, active, completed
        "created_at": None,  # Will be set by Django
        "host_id": None  # Will be set by Django
    }


# CLI interface for testing
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python bingoServer.py <gameId> <numBoards> <phrasesJson>")
        sys.exit(1)
    
    game_id = sys.argv[1]
    num_boards = int(sys.argv[2])
    phrases = json.loads(sys.argv[3])
    
    print(f"Generating {num_boards} boards for game {game_id}...", file=sys.stderr)
    
    output = create_game(game_id, num_boards, phrases)
    
    print(json.dumps(output))