#imports
from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Optional, TypedDict

from game.game import ChessGame, TimelineMove

try:
    from PIL import Image, ImageTk
except ModuleNotFoundError:
    Image = None
    ImageTk = None


# Defines the DragState type.
class DragState(TypedDict):
    from_x: int
    from_y: int
    piece_abbrev: str
    item_id: int


# Defines the ChessGUI type.
class ChessGUI(tk.Tk):
    # Handles __init__ operations.
    def __init__(self) -> None:
        super().__init__()
        self.title("Chess")
        self.geometry("1180x760")
        self.minsize(960, 640)

        self.game: ChessGame = ChessGame()
        self.read_only_loaded_game: bool = False
        self.flipped: bool = False

        self.square_px: int = 80
        self.board_px: int = 640
        self.margin: int = 28

        self.selected_square: Optional[tuple[int, int]] = None
        self.legal_targets: set[tuple[int, int]] = set()
        self.pseudo_targets: set[tuple[int, int]] = set()

        self.drag_state: Optional[DragState] = None
        self.drag_started: bool = False
        self.press_xy: Optional[tuple[int, int]] = None

        self.last_move: Optional[TimelineMove] = None
        self.flash_king_square: Optional[tuple[int, int]] = None
        self.flash_after_id: Optional[str] = None

        self.animation_duration_ms: int = 170
        self.animating: bool = False
        self.anim_piece_abbrev: Optional[str] = None
        self.anim_from: Optional[tuple[int, int]] = None
        self.anim_to: Optional[tuple[int, int]] = None
        self.anim_progress: float = 0.0

        self.symbols: dict[str, str] = {
            "K": "♔",
            "Q": "♕",
            "R": "♖",
            "B": "♗",
            "N": "♘",
            "P": "♙",
            "k": "♚",
            "q": "♛",
            "r": "♜",
            "b": "♝",
            "n": "♞",
            "p": "♟",
        }

        self.image_dir: Path = Path("assets/pieces")
        self.image_cache: dict[tuple[str, int], tk.PhotoImage] = {}

        self._build_layout()
        self._bind_events()
        self._refresh_all()

    # Handles _build_layout operations.
    def _build_layout(self) -> None:
        outer = ttk.Frame(self)
        outer.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        outer.columnconfigure(0, weight=3)
        outer.columnconfigure(1, weight=2)
        outer.rowconfigure(0, weight=1)

        board_card = ttk.Frame(outer, padding=10)
        board_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        board_card.rowconfigure(0, weight=1)
        board_card.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(board_card, highlightthickness=0, bg="#1f252b")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        panel = ttk.Frame(outer, padding=10)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(3, weight=1)

        title = ttk.Label(panel, text="Chess", font=("Georgia", 22, "bold"))
        title.grid(row=0, column=0, sticky="w", pady=(0, 12))

        controls = ttk.Frame(panel)
        controls.grid(row=1, column=0, sticky="ew")
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)

        ttk.Button(controls, text="New Game", command=self._new_game).grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=3)
        ttk.Button(controls, text="Flip Board", command=self._flip_board).grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=3)

        ttk.Button(controls, text="Undo", command=self._undo_move).grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=3)
        ttk.Button(controls, text="Save Game", command=self._save_game).grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=3)

        ttk.Button(controls, text="Load Game (Replay)", command=self._load_game_replay).grid(row=2, column=0, sticky="ew", padx=(0, 6), pady=3)
        ttk.Button(controls, text="Load Position", command=self._load_position).grid(row=2, column=1, sticky="ew", padx=(6, 0), pady=3)

        ttk.Button(controls, text="Prev", command=self._step_backward).grid(row=3, column=0, sticky="ew", padx=(0, 6), pady=3)
        ttk.Button(controls, text="Next", command=self._step_forward).grid(row=3, column=1, sticky="ew", padx=(6, 0), pady=3)

        speed_frame = ttk.LabelFrame(panel, text="Animation")
        speed_frame.grid(row=2, column=0, sticky="ew", pady=(10, 10))
        speed_frame.columnconfigure(0, weight=1)

        self.speed_var = tk.IntVar(value=self.animation_duration_ms)
        speed = ttk.Scale(
            speed_frame,
            from_=80,
            to=360,
            variable=self.speed_var,
            command=self._on_speed_change,
        )
        speed.grid(row=0, column=0, sticky="ew", padx=8, pady=8)

        self.mode_label = ttk.Label(panel, text="Mode: Play", font=("Arial", 10, "bold"))
        self.mode_label.grid(row=3, column=0, sticky="w", pady=(2, 6))

        move_box = ttk.LabelFrame(panel, text="Moves")
        move_box.grid(row=4, column=0, sticky="nsew")
        move_box.rowconfigure(0, weight=1)
        move_box.columnconfigure(0, weight=1)

        self.moves_list: tk.Listbox = tk.Listbox(move_box, activestyle="none", font=("Menlo", 12), bg="#f7f8fa", bd=0)
        self.moves_list.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(move_box, orient=tk.VERTICAL, command=self.moves_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.moves_list.configure(yscrollcommand=scrollbar.set)

        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(panel, textvariable=self.status_var, foreground="#1f4f8b")
        status.grid(row=5, column=0, sticky="ew", pady=(8, 0))

    # Handles _bind_events operations.
    def _bind_events(self) -> None:
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    # Handles _on_speed_change operations.
    def _on_speed_change(self, _value: str) -> None:
        self.animation_duration_ms = int(self.speed_var.get())

    # Handles _new_game operations.
    def _new_game(self) -> None:
        self.game = ChessGame()
        self.read_only_loaded_game = False
        self.last_move = None
        self.selected_square = None
        self.legal_targets.clear()
        self.pseudo_targets.clear()
        self.status_var.set("New game started")
        self._refresh_all()

    # Handles _flip_board operations.
    def _flip_board(self) -> None:
        self.flipped = not self.flipped
        self._draw_board()

    # Handles _undo_move operations.
    def _undo_move(self) -> None:
        if self.read_only_loaded_game:
            self.status_var.set("Replay mode is read-only")
            return
        if self.game.timeline_index <= 0:
            return
        self.game.step_backward()
        self.last_move = self.game.last_move_for_index()
        self._refresh_all()

    # Handles _save_game operations.
    def _save_game(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save Game",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialdir="saves",
        )
        if not path:
            return
        self.game.save(path)
        self.status_var.set(f"Saved: {Path(path).name}")

    # Handles _load_game_replay operations.
    def _load_game_replay(self) -> None:
        path = filedialog.askopenfilename(
            title="Load Saved Game",
            filetypes=[("JSON files", "*.json")],
            initialdir="saves",
        )
        if not path:
            return
        try:
            self.game = ChessGame.load(path)
        except Exception as exc:
            messagebox.showerror("Load Failed", str(exc))
            return
        self.read_only_loaded_game = True
        self.selected_square = None
        self.legal_targets.clear()
        self.pseudo_targets.clear()
        self.last_move = self.game.last_move_for_index()
        self.status_var.set(f"Loaded replay: {Path(path).name}")
        self._refresh_all()

    # Handles _load_position operations.
    def _load_position(self) -> None:
        path = filedialog.askopenfilename(
            title="Load Position",
            filetypes=[("Position files", "*.fen *.txt *.json"), ("All files", "*.*")],
            initialdir="saves",
        )
        if not path:
            return
        try:
            fen = self._read_fen_from_file(Path(path))
            self.game = ChessGame(fen)
            self.read_only_loaded_game = False
            self.last_move = None
            self.selected_square = None
            self.legal_targets.clear()
            self.pseudo_targets.clear()
            self.status_var.set(f"Loaded position: {Path(path).name}")
            self._refresh_all()
        except Exception as exc:
            messagebox.showerror("Load Failed", str(exc))

    # Handles _read_fen_from_file operations.
    def _read_fen_from_file(self, path: Path) -> str:
        text = path.read_text(encoding="utf-8").strip()
        if path.suffix.lower() == ".json":
            raw_obj: object = json.loads(text)
            if not isinstance(raw_obj, dict):
                raise ValueError("JSON position must be an object")
            if isinstance(raw_obj.get("current_fen"), str):
                return str(raw_obj["current_fen"])
            if isinstance(raw_obj.get("timeline"), list) and raw_obj["timeline"]:
                timeline = raw_obj["timeline"]
                first = timeline[0]
                if not isinstance(first, str):
                    raise ValueError("timeline entries must be FEN strings")
                return first
            raise ValueError("JSON missing current_fen or timeline")
        return text

    # Handles _step_backward operations.
    def _step_backward(self) -> None:
        if self.game.step_backward():
            self.last_move = self.game.last_move_for_index()
            self._refresh_all()

    # Handles _step_forward operations.
    def _step_forward(self) -> None:
        if self.game.step_forward():
            self.last_move = self.game.last_move_for_index()
            self._refresh_all()

    # Handles _refresh_all operations.
    def _refresh_all(self) -> None:
        self.mode_label.configure(text="Mode: Replay" if self.read_only_loaded_game else "Mode: Play")
        self._sync_move_list()
        self._draw_board()

    # Handles _sync_move_list operations.
    def _sync_move_list(self) -> None:
        self.moves_list.delete(0, tk.END)
        notations = self.game.timeline_notations
        for index in range(0, len(notations), 2):
            move_no = index // 2 + 1
            white = notations[index]
            black = notations[index + 1] if index + 1 < len(notations) else ""
            self.moves_list.insert(tk.END, f"{move_no:>2}. {white:<8} {black}")

        if self.game.timeline_index > 0:
            active_half_move = self.game.timeline_index - 1
            row = active_half_move // 2
            if 0 <= row < self.moves_list.size():
                self.moves_list.selection_clear(0, tk.END)
                self.moves_list.selection_set(row)
                self.moves_list.see(row)

    # Handles _on_canvas_resize operations.
    def _on_canvas_resize(self, _event: tk.Event[tk.Misc]) -> None:
        self._draw_board()

    # Handles _board_coords_to_screen operations.
    def _board_coords_to_screen(self, x: int, y: int) -> tuple[int, int]:
        col = y
        row = x
        if self.flipped:
            col = 7 - col
            row = 7 - row
        return row, col

    # Handles _screen_to_board_coords operations.
    def _screen_to_board_coords(self, row: int, col: int) -> tuple[int, int]:
        if self.flipped:
            row = 7 - row
            col = 7 - col
        return row, col

    # Handles _pixel_to_square operations.
    def _pixel_to_square(self, px: int, py: int) -> Optional[tuple[int, int]]:
        left = (self.canvas.winfo_width() - self.board_px) // 2 + self.margin
        top = (self.canvas.winfo_height() - self.board_px) // 2 + self.margin
        board_inner = self.square_px * 8
        if not (left <= px < left + board_inner and top <= py < top + board_inner):
            return None
        col = (px - left) // self.square_px
        row = (py - top) // self.square_px
        bx, by = self._screen_to_board_coords(int(row), int(col))
        return bx, by

    # Handles _square_center operations.
    def _square_center(self, x: int, y: int) -> tuple[float, float]:
        row, col = self._board_coords_to_screen(x, y)
        left = (self.canvas.winfo_width() - self.board_px) // 2 + self.margin
        top = (self.canvas.winfo_height() - self.board_px) // 2 + self.margin
        cx = left + col * self.square_px + self.square_px / 2
        cy = top + row * self.square_px + self.square_px / 2
        return cx, cy

    # Handles _draw_board operations.
    def _draw_board(self) -> None:
        self.canvas.delete("all")

        board_dim = min(self.canvas.winfo_width(), self.canvas.winfo_height())
        board_dim = max(320, board_dim - 24)
        self.board_px = board_dim
        self.square_px = max(36, (board_dim - self.margin * 2) // 8)

        left = (self.canvas.winfo_width() - self.board_px) // 2 + self.margin
        top = (self.canvas.winfo_height() - self.board_px) // 2 + self.margin

        light = "#eeeed2"
        dark = "#769656"
        last_a = "#f6f679"
        last_b = "#cdd26a"
        select_color = "#7fa7ff"

        for row in range(8):
            for col in range(8):
                x0 = left + col * self.square_px
                y0 = top + row * self.square_px
                x1 = x0 + self.square_px
                y1 = y0 + self.square_px
                bx, by = self._screen_to_board_coords(row, col)

                base = light if (row + col) % 2 == 0 else dark
                fill = base
                if self.last_move is not None:
                    last_from = (self.last_move["from_x"], self.last_move["from_y"])
                    last_to = (self.last_move["to_x"], self.last_move["to_y"])
                    if (bx, by) in (last_from, last_to):
                        fill = last_a if (row + col) % 2 == 0 else last_b
                if self.selected_square == (bx, by):
                    fill = select_color
                if self.flash_king_square == (bx, by):
                    fill = "#ff6b6b"

                self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, width=0)

        self._draw_legal_targets()
        self._draw_coordinates()
        self._draw_pieces()
        self._draw_drag_piece()
        self._draw_animation_piece()

    # Handles _draw_coordinates operations.
    def _draw_coordinates(self) -> None:
        left = (self.canvas.winfo_width() - self.board_px) // 2 + self.margin
        top = (self.canvas.winfo_height() - self.board_px) // 2 + self.margin

        for col in range(8):
            file_char = chr(ord("a") + (7 - col if self.flipped else col))
            x = left + col * self.square_px + 4
            y = top + 8 * self.square_px - 4
            self.canvas.create_text(x, y, text=file_char, anchor="sw", fill="#12320c", font=("Arial", 10, "bold"))

        for row in range(8):
            rank_char = str(row + 1 if self.flipped else 8 - row)
            x = left + 4
            y = top + row * self.square_px + 12
            self.canvas.create_text(x, y, text=rank_char, anchor="nw", fill="#12320c", font=("Arial", 10, "bold"))

    # Handles _draw_legal_targets operations.
    def _draw_legal_targets(self) -> None:
        for x, y in self.legal_targets:
            piece = self.game.board.grid[x][y]
            cx, cy = self._square_center(x, y)
            if piece is None:
                self.canvas.create_oval(cx - 8, cy - 8, cx + 8, cy + 8, fill="#2e6037", width=0)
            else:
                self.canvas.create_oval(
                    cx - self.square_px * 0.42,
                    cy - self.square_px * 0.42,
                    cx + self.square_px * 0.42,
                    cy + self.square_px * 0.42,
                    outline="#2e6037",
                    width=3,
                )

    # Handles _piece_image operations.
    def _piece_image(self, abbrev: str) -> Optional[tk.PhotoImage]:
        if Image is None or ImageTk is None:
            return None

        size = int(self.square_px * 0.86)
        key = (abbrev, size)
        if key in self.image_cache:
            return self.image_cache[key]

        candidates = [
            self.image_dir / f"{abbrev}.png",
            self.image_dir / f"{abbrev.lower()}.png",
            self.image_dir / f"{'w' if abbrev.isupper() else 'b'}{abbrev.upper()}.png",
            self.image_dir / f"{'w' if abbrev.isupper() else 'b'}{abbrev.upper()}.svg.png",
        ]
        source = next((path for path in candidates if path.exists()), None)
        if source is None:
            return None

        image = Image.open(source).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
        tk_image = ImageTk.PhotoImage(image)
        self.image_cache[key] = tk_image
        return tk_image

    # Handles _draw_pieces operations.
    def _draw_pieces(self) -> None:
        hidden_to: Optional[tuple[int, int]] = None
        if self.animating and self.anim_to is not None:
            hidden_to = self.anim_to

        for x in range(8):
            for y in range(8):
                if hidden_to == (x, y):
                    continue
                piece = self.game.board.grid[x][y]
                if piece is None:
                    continue

                cx, cy = self._square_center(x, y)
                image = self._piece_image(piece.abbreviation)
                if image is not None:
                    self.canvas.create_image(cx, cy, image=image)
                else:
                    self.canvas.create_text(
                        cx,
                        cy,
                        text=self.symbols[piece.abbreviation],
                        font=("Segoe UI Symbol", int(self.square_px * 0.64)),
                        fill="#101316" if piece.color else "#0a0a0a",
                    )

    # Handles _draw_drag_piece operations.
    def _draw_drag_piece(self) -> None:
        if self.drag_state is None:
            return
        if self.drag_started:
            return
        x, y = self.drag_state["from_x"], self.drag_state["from_y"]
        cx, cy = self._square_center(x, y)
        abbrev = self.drag_state["piece_abbrev"]
        self.canvas.create_text(
            cx,
            cy,
            text=self.symbols[abbrev],
            font=("Segoe UI Symbol", int(self.square_px * 0.64)),
            fill="#101316" if abbrev.isupper() else "#0a0a0a",
        )

    # Handles _draw_animation_piece operations.
    def _draw_animation_piece(self) -> None:
        if not self.animating or self.anim_piece_abbrev is None or self.anim_from is None or self.anim_to is None:
            return

        start_x, start_y = self._square_center(*self.anim_from)
        end_x, end_y = self._square_center(*self.anim_to)
        eased = self._ease(self.anim_progress)
        cx = start_x + (end_x - start_x) * eased
        cy = start_y + (end_y - start_y) * eased

        self.canvas.create_text(
            cx,
            cy,
            text=self.symbols[self.anim_piece_abbrev],
            font=("Segoe UI Symbol", int(self.square_px * 0.64)),
            fill="#101316" if self.anim_piece_abbrev.isupper() else "#0a0a0a",
        )

    # Handles _ease operations.
    def _ease(self, t: float) -> float:
        return t * t * (3.0 - 2.0 * t)

    # Handles _on_press operations.
    def _on_press(self, event: tk.Event[tk.Misc]) -> None:
        if self.animating:
            return

        square = self._pixel_to_square(event.x, event.y)
        if square is None:
            self.selected_square = None
            self.legal_targets.clear()
            self.pseudo_targets.clear()
            self._draw_board()
            return

        if self.read_only_loaded_game:
            self.status_var.set("Replay mode: moves disabled")
            return

        x, y = square
        piece = self.game.board.grid[x][y]
        if piece is None:
            self.selected_square = None
            self.legal_targets.clear()
            self.pseudo_targets.clear()
            self._draw_board()
            return

        if piece.color != self.game.board.side_to_move:
            return

        self.selected_square = (x, y)
        self.legal_targets = {(m.to_x, m.to_y) for m in self.game.board.get_legal_move_objects(piece)}
        self.pseudo_targets = {(m.to_x, m.to_y) for m in self.game.board._pseudo_moves_for_piece(piece)}

        self.drag_state = {
            "from_x": x,
            "from_y": y,
            "piece_abbrev": piece.abbreviation,
            "item_id": -1,
        }
        self.drag_started = False
        self.press_xy = (event.x, event.y)
        self._draw_board()

    # Handles _on_drag operations.
    def _on_drag(self, event: tk.Event[tk.Misc]) -> None:
        if self.drag_state is None or self.read_only_loaded_game or self.animating:
            return

        if not self.drag_started and self.press_xy is not None:
            dx = abs(event.x - self.press_xy[0])
            dy = abs(event.y - self.press_xy[1])
            if max(dx, dy) < 4:
                return
            self.drag_started = True

        self._draw_board()
        self.drag_state["item_id"] = self.canvas.create_text(
            event.x,
            event.y,
            text=self.symbols[self.drag_state["piece_abbrev"]],
            font=("Segoe UI Symbol", int(self.square_px * 0.64)),
            fill="#101316" if self.drag_state["piece_abbrev"].isupper() else "#0a0a0a",
        )

    # Handles _on_release operations.
    def _on_release(self, event: tk.Event[tk.Misc]) -> None:
        if self.drag_state is None:
            return
        if self.read_only_loaded_game or self.animating:
            self.drag_state = None
            self.drag_started = False
            return

        from_sq = (self.drag_state["from_x"], self.drag_state["from_y"])
        target = self._pixel_to_square(event.x, event.y)

        if target is None:
            self._cancel_drag()
            return

        if (not self.drag_started) and target == from_sq:
            self._draw_board()
            return

        if target in self.legal_targets:
            self._play_move(from_sq, target)
            return

        if target in self.pseudo_targets:
            self._flash_king()
        self._cancel_drag()

    # Handles _cancel_drag operations.
    def _cancel_drag(self) -> None:
        self.drag_state = None
        self.drag_started = False
        self._draw_board()

    # Handles _flash_king operations.
    def _flash_king(self) -> None:
        try:
            king_square = self.game.board.find_king(self.game.board.side_to_move)
        except ValueError:
            return
        self.flash_king_square = king_square
        self._draw_board()
        if self.flash_after_id is not None:
            self.after_cancel(self.flash_after_id)
        self.flash_after_id = self.after(220, self._clear_flash)

    # Handles _clear_flash operations.
    def _clear_flash(self) -> None:
        self.flash_king_square = None
        self.flash_after_id = None
        self._draw_board()

    # Handles _play_move operations.
    def _play_move(self, from_sq: tuple[int, int], to_sq: tuple[int, int]) -> None:
        from_x, from_y = from_sq
        to_x, to_y = to_sq

        piece = self.game.board.grid[from_x][from_y]
        if piece is None:
            self._cancel_drag()
            return

        promotion: Optional[str] = None
        if piece.abbreviation.lower() == "p" and (to_x == 0 or to_x == 7):
            choice = simpledialog.askstring("Promotion", "Promote to (Q, R, B, N):", parent=self)
            if choice:
                promotion = choice.strip().upper()[:1]
            if promotion not in {"Q", "R", "B", "N", None}:
                promotion = "Q"

        moved = self.game.play_coords(from_x, from_y, to_x, to_y, promotion)
        if not moved:
            if (to_x, to_y) in self.pseudo_targets:
                self._flash_king()
            self._cancel_drag()
            return

        self.last_move = self.game.last_move_for_index()
        self.status_var.set("Move played")

        self.selected_square = None
        self.legal_targets.clear()
        self.pseudo_targets.clear()
        self.drag_state = None
        self.drag_started = False

        self._start_animation(piece.abbreviation, from_sq, to_sq)

    # Handles _start_animation operations.
    def _start_animation(self, abbrev: str, from_sq: tuple[int, int], to_sq: tuple[int, int]) -> None:
        self.animating = True
        self.anim_piece_abbrev = abbrev
        self.anim_from = from_sq
        self.anim_to = to_sq
        self.anim_progress = 0.0
        self._animate_step(0)

    # Handles _animate_step operations.
    def _animate_step(self, elapsed_ms: int) -> None:
        if not self.animating:
            return

        duration = max(80, self.animation_duration_ms)
        self.anim_progress = min(1.0, elapsed_ms / duration)
        self._refresh_all()

        if self.anim_progress >= 1.0:
            self.animating = False
            self.anim_piece_abbrev = None
            self.anim_from = None
            self.anim_to = None
            self.anim_progress = 0.0
            self._refresh_all()
            return

        self.after(16, lambda: self._animate_step(elapsed_ms + 16))


# Handles launch_gui operations.
def launch_gui() -> None:
    app = ChessGUI()
    app.mainloop()
