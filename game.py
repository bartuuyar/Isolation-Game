import itertools
import math

BOARD_SIZE = 8

EMPTY   = 0
PLAYER1 = 1   # human 
PLAYER2 = 2   # AI 
BLACKOUT = 3


def opposite(player):
    return PLAYER1 if player == PLAYER2 else PLAYER2


class Game:
    def __init__(self, mode='vs AI', first_player=1, blackout_mode='legal'):
        self.mode = mode
        self.first_player = first_player
        self.current_player = first_player

        
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        # Default starting positions:
        self.board[2][0] = PLAYER1
        self.board[5][7] = PLAYER2

        # legal (adjacent empty cells only) or distant (up to two squares away)
        self.blackout_mode = blackout_mode

    def get_pawn_position(self, player):
        
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                if self.board[y][x] == player:
                    return (x, y)
        return None

    def get_legal_moves(self, player):
        
        pos = self.get_pawn_position(player)
        if pos is None:
            return []

        x0, y0 = pos
        moves = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                x, y = x0 + dx, y0 + dy
                if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and self.board[y][x] == EMPTY:
                    moves.append((x, y))
        return moves

    def get_distant_moves(self, player):
        
        pos = self.get_pawn_position(player)
        if pos is None:
            return []

        x0, y0 = pos
        moves = []
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx == 0 and dy == 0:
                    continue
                x, y = x0 + dx, y0 + dy
                if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and self.board[y][x] == EMPTY:
                    moves.append((x, y))
        return moves

    def apply_move(self, move, player):
        
        x_new, y_new = move
        pos = self.get_pawn_position(player)
        if pos is None:
            return
        x_old, y_old = pos
        self.board[y_old][x_old] = EMPTY
        self.board[y_new][x_new] = player

    def apply_blackouts(self, cells):
        
        for (x, y) in cells:
            if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
                self.board[y][x] = BLACKOUT

    def is_terminal(self):
        
        return not self.get_legal_moves(self.current_player)

    def evaluate(self):
        
        if self.is_terminal():
            
            if self.current_player == PLAYER2:
                return -math.inf
            
            else:
                return math.inf

        
        return len(self.get_legal_moves(PLAYER2)) - len(self.get_legal_moves(PLAYER1))

    def minimax(self, depth, alpha, beta, maximizing):
        
        # Leaf‐node either depth0 or current player has no moves
        if depth == 0 or self.is_terminal():
            return None, self.evaluate()

        best_action = None

        if maximizing:
            # AI’s turn (PLAYER2)
            max_eval = -math.inf
           
            moves = self.get_legal_moves(PLAYER2)
            
            for move in moves:
                
                board_backup = [row[:] for row in self.board]
                cp_backup = self.current_player

               
                self.apply_move(move, PLAYER2)
                

                
                opponent = PLAYER1
                if self.blackout_mode == 'legal':
                    human_moves = self.get_legal_moves(opponent)
                else:  
                    human_moves = self.get_distant_moves(opponent)
               
                if len(human_moves) >= 2:
                    combos = list(itertools.combinations(human_moves, 2))
                else:
                    combos = [tuple(human_moves)]  #blackout all remaining moves 0, 1 or 2

                
                for blacks in combos:
                   
                    board2_backup = [row[:] for row in self.board]
                  
                    self.apply_blackouts(blacks)
                   
                    self.current_player = PLAYER1
                    
                    _, score = self.minimax(depth - 1, alpha, beta, False)

                    self.board = [row[:] for row in board2_backup]
                    self.current_player = PLAYER2                                  
                    
                    if score > max_eval or best_action is None:
                        max_eval = score
                        best_action = (move, blacks)

                    
                    alpha = max(alpha, max_eval)
                    if beta <= alpha:
                        break  

                
                self.board = [row[:] for row in board_backup]
                self.current_player = cp_backup
                if beta <= alpha:
                    break  

            return best_action, max_eval

        else:
            # humans turn (PLAYER1)
            min_eval = math.inf

            
            moves = self.get_legal_moves(PLAYER1)

            
            for move in moves:
                
                board_backup = [row[:] for row in self.board]
                cp_backup = self.current_player
               
                self.apply_move(move, PLAYER1)
                
                
                opponent = PLAYER2
                if self.blackout_mode == 'legal':
                    ai_moves = self.get_legal_moves(opponent)
                else:
                    ai_moves = self.get_distant_moves(opponent)             

                if len(ai_moves) >= 2:                   
                    combos = list(itertools.combinations(ai_moves, 2))
                else:
                    combos = [tuple(ai_moves)]  #blackout all remaining moves 0, 1 or 2

                
                for blacks in combos:
                    board2_backup = [row[:] for row in self.board]
                   
                    self.apply_blackouts(blacks)
                  
                    self.current_player = PLAYER2
                    
                    _, score = self.minimax(depth - 1, alpha, beta, True)
                    
                    self.board = [row[:] for row in board2_backup]
                    self.current_player = PLAYER1
                  
                    if score < min_eval or best_action is None:
                        min_eval = score
                        best_action = (move, blacks)

                   
                    beta = min(beta, min_eval)
                    if beta <= alpha:
                        break  

                
                self.board = [row[:] for row in board_backup]
                self.current_player = cp_backup
                if beta <= alpha:
                    break  

            return best_action, min_eval

    def best_action_for(self, player, depth):
        
        self.current_player = player
        maximizing = (player == PLAYER2)
        action, _ = self.minimax(depth, -math.inf, math.inf, maximizing)
        return action
