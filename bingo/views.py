import json
import uuid
from django.http import JsonResponse
from django.views import View
from django.core.cache import cache
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .bingoServer import create_game


class CreateGameView(View):
    def get(self, request):
        # Show the creation form
        return render(request, 'bingo/create_game.html')
    
    def post(self, request):
        # Get phrases from form
        phrases_raw = request.POST.get('phrases', '')
        phrases = [p.strip() for p in phrases_raw.split('\n') if p.strip()]
        
        num_players = int(request.POST.get('num_players', 5))
        
        # SERVER-SIDE VALIDATION
        if num_players < 1 or num_players > 256:
            return render(request, 'bingo/create_game.html', {
                'error': f'Number of players must be between 1 and 256. You requested {num_players}.',
                'phrases': phrases_raw,
                'num_players': num_players
            })
        
        # Validate phrases
        if len(phrases) < 48:
            return render(request, 'bingo/create_game.html', {
                'error': f'Need at least 48 phrases. You provided {len(phrases)}.',
                'phrases': phrases_raw,
                'num_players': num_players
            })
        
        game_id = str(uuid.uuid4())
        game_data = create_game(game_id, num_players, phrases)
        
        # Store in cache (1 hour timeout)
        cache.set(f'game_{game_id}', game_data, timeout=3600)
        
        # Redirect to admin dashboard (not render)
        from django.shortcuts import redirect
        return redirect('bingo:game_admin', game_id=game_id)


class BoardView(View):
    def get(self, request, game_id, board_uuid):
        # Retrieve game data
        game_data = cache.get(f'game_{game_id}')
        
        if not game_data:
            return render(request, 'bingo/error.html', {
                'error': 'Game not found or expired.'
            })
        
        # Get board assignment
        board_assignment = game_data['board_assignments'].get(board_uuid)
        
        if not board_assignment:
            return render(request, 'bingo/error.html', {
                'error': 'Invalid board link.'
            })
        
        # Check if board is already assigned
        if board_assignment['assigned']:
            # Already claimed - show the board
            # Build columns for template
            columns = []
            for col in range(5):
                column_squares = []
                for row in range(5):
                    column_squares.append({
                        'row': row,
                        'col': col,
                        'phrase': board_assignment['board_data'][row][col]
                    })
                columns.append(column_squares)
            
            return render(request, 'bingo/game_board.html', {
                'game_id': game_id,
                'board_uuid': board_uuid,
                'columns': columns,
                'player_name': board_assignment.get('player_name', 'Anonymous'),
                'player_email': board_assignment.get('player_email', ''),
                'phrases_called': json.dumps(game_data.get('phrases_called', [])),  # Add this
    })
        else:
            # Not claimed yet - show registration form
            return render(request, 'bingo/claim_board.html', {
                'game_id': game_id,
                'board_uuid': board_uuid
            })
    
    def post(self, request, game_id, board_uuid):
        # Get player info from form
        player_email = request.POST.get('player_email', '').strip()
        player_name = request.POST.get('player_name', '').strip()
        
        # Validate
        if not player_email or not player_name:
            return render(request, 'bingo/claim_board.html', {
                'game_id': game_id,
                'board_uuid': board_uuid,
                'error': 'Both email and display name are required.'
            })
        
        # Retrieve game data
        game_data = cache.get(f'game_{game_id}')
        
        if not game_data:
            return render(request, 'bingo/error.html', {
                'error': 'Game not found or expired.'
            })
        
        # Get board assignment
        board_assignment = game_data['board_assignments'].get(board_uuid)
        
        if not board_assignment:
            return render(request, 'bingo/error.html', {
                'error': 'Invalid board link.'
            })
        
        # Check if already claimed
        if board_assignment['assigned']:
            return render(request, 'bingo/error.html', {
                'error': 'This board has already been claimed.'
            })
        
       # Claim the board
        board_assignment['assigned'] = True
        board_assignment['player_email'] = player_email
        board_assignment['player_name'] = player_name
        board_assignment['player_id'] = player_email
        
        # Update cache
        cache.set(f'game_{game_id}', game_data, timeout=3600)
        
        # BROADCAST VIA WEBSOCKET
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'bingo_game_{game_id}',
            {
                'type': 'player_joined',
                'board_uuid': board_uuid,
                'player_name': player_name,
                'player_email': player_email
            }
        )
        
        # Build columns for template
        columns = []
        for col in range(5):
            column_squares = []
            for row in range(5):
                column_squares.append({
                    'row': row,
                    'col': col,
                    'phrase': board_assignment['board_data'][row][col]
                })
            columns.append(column_squares)
        
        # Show the board
        return render(request, 'bingo/game_board.html', {
            'game_id': game_id,
            'board_uuid': board_uuid,
            'columns': columns,
            'player_name': player_name,
            'player_email': player_email,
        })
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@csrf_exempt
@require_http_methods(["POST"])
def call_phrase(request, game_id):
    try:
        data = json.loads(request.body)
        phrase = data.get('phrase')
        board_uuid = data.get('board_uuid')
        
        # Retrieve game data
        game_data = cache.get(f'game_{game_id}')
        
        if not game_data:
            return JsonResponse({'error': 'Game not found'}, status=404)
        
        # Validate phrase exists in this game
        phrase_valid = False
        for board_data in game_data['board_assignments'].values():
            for row in board_data['board_data']:
                if phrase in row:
                    phrase_valid = True
                    break
            if phrase_valid:
                break
        
        if not phrase_valid:
            return JsonResponse({'error': 'Invalid phrase'}, status=400)
        
        # Check if already called
        if phrase in game_data['phrases_called']:
            return JsonResponse({'error': 'Already called'}, status=400)
        
        # Add to phrases_called
        game_data['phrases_called'].append(phrase)
        
        # Update cache
        cache.set(f'game_{game_id}', game_data, timeout=3600)
        
        # BROADCAST VIA WEBSOCKET
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'bingo_game_{game_id}',
            {
                'type': 'phrase_called',
                'phrase': phrase,
                'total_called': len(game_data['phrases_called'])
            }
        )
        
        return JsonResponse({
            'success': True,
            'phrase': phrase,
            'total_called': len(game_data['phrases_called'])
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)
    try:
        data = json.loads(request.body)
        phrase = data.get('phrase')
        board_uuid = data.get('board_uuid')
        
        # Retrieve game data
        game_data = cache.get(f'game_{game_id}')
        
        if not game_data:
            return JsonResponse({'error': 'Game not found'}, status=404)
        
        # Validate phrase exists in this game (check all boards)
        phrase_valid = False
        for board_data in game_data['board_assignments'].values():
            for row in board_data['board_data']:
                if phrase in row:
                    phrase_valid = True
                    break
            if phrase_valid:
                break
        
        if not phrase_valid:
            return JsonResponse({'error': 'Invalid phrase'}, status=400)
        
        # Check if already called
        if phrase in game_data['phrases_called']:
            return JsonResponse({'error': 'Already called'}, status=400)
        
        # Add to phrases_called
        game_data['phrases_called'].append(phrase)
        
        # Update cache
        cache.set(f'game_{game_id}', game_data, timeout=3600)
        
        # TODO: Broadcast via WebSocket to all clients
        
        return JsonResponse({
            'success': True,
            'phrase': phrase,
            'total_called': len(game_data['phrases_called'])
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
class GameAdminView(View):
    def get(self, request, game_id):
        # Retrieve game data
        game_data = cache.get(f'game_{game_id}')
        
        if not game_data:
            return render(request, 'bingo/error.html', {
                'error': 'Game not found or expired.'
            })
        
        # Render admin dashboard
        return render(request, 'bingo/game_admin.html', {
            'game_data': game_data,
            'game_id': game_id
        })
    
@require_http_methods(["GET"])
def get_game_state(request, game_id):
    game_data = cache.get(f'game_{game_id}')
    
    if not game_data:
        return JsonResponse({'error': 'Game not found'}, status=404)
    
    # Return minimal data needed for updates
    return JsonResponse({
        'phrases_called': game_data.get('phrases_called', []),
        'board_assignments': {
            uuid: {
                'assigned': board['assigned'],
                'player_name': board.get('player_name'),
                'player_email': board.get('player_email')
            }
            for uuid, board in game_data['board_assignments'].items()
        }
    })
from django.http import JsonResponse

def healthz(request):
    return JsonResponse({"ok": True})
