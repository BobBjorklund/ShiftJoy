import uuid
import json
import sys
from .bingoCardGenerator import bingoCardGenerator


def create_game(game_id, num_boards, phrases):
    """
    Generate complete game data structure.
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
            "player_id": None,
        }
        
        link = f"website.com/bingo/games/{game_id}/{board_uuid}"
        player_links.append(link)
    
    # Win patterns (positions in row-major order: 0-24)
    win_patterns = {
        "traditional": {
            "rows": [[0,1,2,3,4], [5,6,7,8,9], [10,11,12,13,14], [15,16,17,18,19], [20,21,22,23,24]],
            "cols": [[0,5,10,15,20], [1,6,11,16,21], [2,7,12,17,22], [3,8,13,18,23], [4,9,14,19,24]],
            "diags": [[0,6,12,18,24], [4,8,12,16,20]]
        },
        "four_corners": [[0, 4, 20, 24]],
        "x": [[0,6,12,18,24,4,8,16,20]],
        "around_the_world": [[0,1,2,3,4,9,14,19,24,23,22,21,20,15,10,5]],
        "full_board": [[i for i in range(25)]]
    }
    
    return {
        "game_id": game_id,
        "num_boards": num_boards,
        "board_assignments": board_assignments,
        "player_links": player_links,
        "phrases_called": [],
        "game_state": "waiting",
        "created_at": None,
        "host_id": None,
        "win_patterns": win_patterns,
        "winners": []  # List of {board_uuid, player_name, pattern, timestamp}
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