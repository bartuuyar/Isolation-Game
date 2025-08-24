import tkinter as tk
from game import Game, PLAYER1, PLAYER2, BLACKOUT,EMPTY,BOARD_SIZE,opposite

# GUI layout constants
OFFSET = 30
CELL_SIZE = 60

class GUI:
    def __init__(self, depth_blue=3, depth_red=3, ai_delay=500):
        self.root = tk.Tk()
        self.root.title("Isolation Game")
        
        self.ai_depths = {
            PLAYER1: depth_blue,
            PLAYER2: depth_red
        }
        self.ai_delay = ai_delay
        self.mode = tk.StringVar(value='vs AI')
        self.first = tk.IntVar(value=1)
        self._setup_start_menu()
        self.root.mainloop()

    def _setup_start_menu(self):
        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=20)
        tk.Label(frame, text="Mode:").grid(row=0, column=0)
        tk.Radiobutton(frame, text="1v1", variable=self.mode, value='1v1').grid(row=0, column=1)
        tk.Radiobutton(frame, text="vs AI", variable=self.mode, value='vs AI').grid(row=0, column=2)
        tk.Radiobutton(frame, text="AI vs AI", variable=self.mode, value='AI vs AI').grid(row=0, column=3)
        tk.Label(frame, text="First:").grid(row=1, column=0)
        tk.Radiobutton(frame, text="Blue", variable=self.first, value=1).grid(row=1, column=1)
        tk.Radiobutton(frame, text="Red", variable=self.first, value=2).grid(row=1, column=2)
        tk.Button(frame, text="Start Game", command=lambda: self._start_game(frame)) \
            .grid(row=2, column=0, columnspan=4, pady=10)

    def _start_game(self, frame):
        frame.destroy()
        self.game = Game(self.mode.get(), self.first.get())
        self.current_phase = 'move'
        self.selected_blackouts = []
        self._setup_ui()
        self._draw()
        self._update()
        if self.mode.get() == 'vs AI' and self.game.current_player == PLAYER2:
            self.root.after(self.ai_delay, self._ai_move)
        elif self.mode.get() == 'AI vs AI':
            self.root.after(self.ai_delay, self._auto_play)

    def _setup_ui(self):
        width = OFFSET * 2 + BOARD_SIZE * CELL_SIZE
        self.canvas = tk.Canvas(self.root, width=width, height=width)
        self.canvas.pack()
        self.label = tk.Label(self.root, font=('Arial', 14))
        self.label.pack(pady=5)
        self.canvas.bind('<Button-1>', self._on_click)

    def _update(self):
        if self.game.is_terminal():
            winner = 'Red' if self.game.current_player==PLAYER1 else 'Blue'
            self.label.config(text=f"{winner} wins!")
        else:
            turn = 'Blue' if self.game.current_player==PLAYER1 else 'Red'
            self.label.config(text=f"{turn}'s turn ({self.current_phase})")

    def _draw(self):
        cv = self.canvas
        cv.delete('all')
        # draw coordinates
        for i in range(BOARD_SIZE):
            x = OFFSET + i*CELL_SIZE + CELL_SIZE/2
            y = OFFSET + BOARD_SIZE*CELL_SIZE + 15
            cv.create_text(x, y, text=chr(ord('a')+i))
            xi = OFFSET - 15
            yi = OFFSET + i*CELL_SIZE + CELL_SIZE/2
            cv.create_text(xi, yi, text=str(BOARD_SIZE-i))
        # draw cells
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                x0 = OFFSET + x*CELL_SIZE
                y0 = OFFSET + y*CELL_SIZE
                x1 = x0 + CELL_SIZE
                y1 = y0 + CELL_SIZE
                cv.create_rectangle(x0, y0, x1, y1, fill='white', outline='gray')
                c = self.game.board[y][x]
                if c==PLAYER1:
                    cv.create_oval(x0+5, y0+5, x1-5, y1-5, fill='blue')
                elif c==PLAYER2:
                    cv.create_oval(x0+5, y0+5, x1-5, y1-5, fill='red')
                elif c==BLACKOUT:
                    cv.create_rectangle(x0, y0, x1, y1, fill='black')
        # highlight legal actions
        if not self.game.is_terminal():
            if self.current_phase=='move':
                for mx,my in self.game.get_legal_moves(self.game.current_player):
                    cv.create_rectangle(OFFSET+mx*CELL_SIZE, OFFSET+my*CELL_SIZE,
                                        OFFSET+(mx+1)*CELL_SIZE, OFFSET+(my+1)*CELL_SIZE,
                                        outline='green', width=3)
            else:
                for bx,by in self.selected_blackouts:
                    cv.create_rectangle(OFFSET+bx*CELL_SIZE, OFFSET+by*CELL_SIZE,
                                        OFFSET+(bx+1)*CELL_SIZE, OFFSET+(by+1)*CELL_SIZE,
                                        outline='yellow', width=3)

    def _on_click(self, event):
        gx = (event.x - OFFSET)//CELL_SIZE
        gy = (event.y - OFFSET)//CELL_SIZE
        if not (0<=gx<BOARD_SIZE and 0<=gy<BOARD_SIZE): return
        if self.game.is_terminal(): return
        if self.current_phase=='move' and (gx,gy) in self.game.get_legal_moves(self.game.current_player):
            self.game.apply_move((gx,gy), self.game.current_player)
            self.current_phase='blackout'
            self.selected_blackouts=[]
        elif self.current_phase=='blackout' and self.game.board[gy][gx]==EMPTY:
            if (gx,gy) in self.selected_blackouts:
                self.selected_blackouts.remove((gx,gy))
            elif len(self.selected_blackouts)<2:
                self.selected_blackouts.append((gx,gy))
        self._draw()
        if self.current_phase=='blackout' and (len(self.selected_blackouts)==2 or self.mode.get()=='1v1'):
            self._finish_turn()

    def _finish_turn(self):
        self.game.apply_blackouts(self.selected_blackouts)
        self.selected_blackouts=[]
        self.game.current_player = opposite(self.game.current_player)
        self.current_phase='move'
        self._update()
        self._draw()
        if self.mode.get()=='vs AI' and self.game.current_player==PLAYER2 and not self.game.is_terminal():
            self.root.after(self.ai_delay, self._ai_move)

    def _auto_play(self):
        if self.game.is_terminal():
            self._update()
            return

        player = self.game.current_player
        depth  = self.ai_depths[player]
        action = self.game.best_action_for(player, depth)

        if action:
            move, blacks = action
            self.game.apply_move(move, player)
            if blacks:
                self.game.apply_blackouts(blacks)

        self.game.current_player = opposite(player)
        self._update()
        self._draw()
        self.root.after(self.ai_delay, self._auto_play)

    def _ai_move(self):
        player = self.game.current_player
        depth  = self.ai_depths[player]
        action = self.game.best_action_for(player, depth)

        if action:
            move, blacks = action
            self.game.apply_move(move, player)
            if blacks:
                self.game.apply_blackouts(blacks)

        self.game.current_player = opposite(player)
        self._update()
        self._draw()

        if not self.game.is_terminal() and self.mode.get()=='vs AI' and self.game.current_player==PLAYER2:
            self.root.after(self.ai_delay, self._ai_move)

def main(depth_blue=3, depth_red=3, ai_delay=10):
    GUI(depth_blue=depth_blue, depth_red=depth_red, ai_delay=ai_delay)
