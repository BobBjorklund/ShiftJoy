import json
from channels.generic.websocket import AsyncWebsocketConsumer

class BingoGameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = f'bingo_game_{self.game_id}'
        
        # Join game room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        print(f"WebSocket connected to game {self.game_id}")
    
    async def disconnect(self, close_code):
        # Leave game room
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"WebSocket disconnected from game {self.game_id}")
    
    async def receive(self, text_data):
        # This method handles messages FROM clients
        # We don't need it for now since clients only listen
        pass
    
    # Handler for phrase_called events
    async def phrase_called(self, event):
        # Send phrase to WebSocket client
        await self.send(text_data=json.dumps({
            'type': 'phrase_called',
            'phrase': event['phrase'],
            'total_called': event['total_called']
        }))
    
    # Handler for player_joined events
    async def player_joined(self, event):
        # Send player info to WebSocket client
        await self.send(text_data=json.dumps({
            'type': 'player_joined',
            'board_uuid': event['board_uuid'],
            'player_name': event['player_name'],
            'player_email': event['player_email']
        }))