#imports
from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any, Callable, Optional, TypedDict, cast

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
        self.geometry("1320x820")
        self.minsize(1040, 680)
        self.configure(bg="#0f141b")

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

        self.speed_map: dict[str, int] = {
            "Instant": 0,
            "Fast": 120,
            "Medium": 200,
            "Slow": 320,
        }
        self.animation_mode_var = tk.StringVar(value="Medium")
        self.animation_duration_ms: int = self.speed_map[self.animation_mode_var.get()]

        self.animating: bool = False
        self.anim_piece_abbrev: Optional[str] = None
        self.anim_from: Optional[tuple[int, int]] = None
        self.anim_to: Optional[tuple[int, int]] = None
        self.anim_progress: float = 0.0

        self.notation_index_to_timeline: list[int] = []
        self.suppress_notation_select: bool = False

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
        self.image_cache: dict[tuple[str, int], Any] = {}

        self._build_layout()
        self._bind_events()
        self._refresh_all()

    # Handles _build_layout operations.
    def _build_layout(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background="#0f141b", foreground="#d9e1ea")
        style.configure("TFrame", background="#0f141b")
        style.configure("TLabel", background="#0f141b", foreground="#d9e1ea")
        style.configure("TLabelframe", background="#121a23", foreground="#9fb3c8", bordercolor="#24303d")
        style.configure("TLabelframe.Label", background="#121a23", foreground="#9fb3c8")
        style.configure("TScrollbar", background="#1c2734", troughcolor="#0f141b")
        style.configure("TCombobox", fieldbackground="#1a2330", background="#1a2330", foreground="#d9e1ea")
        style.configure(
            "Action.TButton",
            font=("Segoe UI", 13, "bold"),
            padding=(24, 18),
            borderwidth=0,
            relief="flat",
            foreground="#f4f7fb",
            background="#2e3b4b",
            focusthickness=0,
        )
        style.map(
            "Action.TButton",
            background=[("pressed", "#1e2a36"), ("active", "#3e536a")],
            foreground=[("pressed", "#ffffff"), ("active", "#ffffff")],
        )

        outer = ttk.Frame(self)
        outer.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
        outer.columnconfigure(0, weight=7)  # board
        outer.columnconfigure(1, weight=2)  # notation
        outer.columnconfigure(2, weight=2)  # buttons
        outer.rowconfigure(0, weight=1)

        board_card = ttk.Frame(outer, padding=10)
        board_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        board_card.rowconfigure(0, weight=1)
        board_card.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(board_card, highlightthickness=0, bg="#0f141b")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        notation_panel = ttk.Frame(outer, padding=10)
        notation_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        notation_panel.columnconfigure(0, weight=1)
        notation_panel.rowconfigure(1, weight=1)

        ttk.Label(notation_panel, text="Notation", font=("Georgia", 18, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 8))

        move_box = ttk.LabelFrame(notation_panel, text="Moves")
        move_box.grid(row=1, column=0, sticky="nsew")
        move_box.rowconfigure(0, weight=1)
        move_box.columnconfigure(0, weight=1)

        self.moves_list = tk.Listbox(
            move_box,
            activestyle="none",
            font=("Menlo", 13),
            bg="#1a2330",
            fg="#d7e2ee",
            selectbackground="#2f4258",
            selectforeground="#ffffff",
            bd=0,
        )
        self.moves_list.grid(row=0, column=0, sticky="nsew")
        self.moves_scrollbar = ttk.Scrollbar(move_box, orient=tk.VERTICAL, command=self._on_moves_scrollbar)
        self.moves_scrollbar.grid(row=0, column=1, sticky="ns")
        self.moves_list.configure(yscrollcommand=self._on_moves_list_scroll)

        self.mode_label = ttk.Label(notation_panel, text="Mode: Play", font=("Arial", 10, "bold"))
        self.mode_label.grid(row=2, column=0, sticky="w", pady=(4, 2))

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(notation_panel, textvariable=self.status_var, foreground="#84a8cc").grid(row=3, column=0, sticky="ew")

        controls_panel = ttk.Frame(outer, padding=10)
        controls_panel.grid(row=0, column=2, sticky="nsew")
        controls_panel.columnconfigure(0, weight=1)
        controls_panel.columnconfigure(1, minsize=260)

        speed_frame = ttk.LabelFrame(controls_panel, text="Animation")
        speed_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        speed_frame.columnconfigure(0, weight=1)
        self.speed_combo = ttk.Combobox(
            speed_frame,
            state="readonly",
            values=list(self.speed_map.keys()),
            textvariable=self.animation_mode_var,
            font=("Segoe UI", 11, "bold"),
        )
        self.speed_combo.grid(row=0, column=0, sticky="ew", padx=8, pady=8)

        buttons: list[tuple[str, Callable[[], None]]] = [
            ("New Game", self._new_game),
            ("Flip Board", self._flip_board),
            ("Undo", self._undo_move),
            ("Save Game", self._save_game),
            ("Load Replay", self._load_game_replay),
            ("Load Position", self._load_position),
            ("Piece Folder", self._choose_piece_folder),
            ("Prev", self._step_backward),
            ("Next", self._step_forward),
        ]
        for idx, (label, callback) in enumerate(buttons, start=1):
            ttk.Button(controls_panel, text=label, command=callback, style="Action.TButton", width=18).grid(
                row=idx, column=0, sticky="ew", pady=5
            )

        material_box = ttk.LabelFrame(controls_panel, text="Material")
        material_box.grid(row=10, column=0, sticky="ew", pady=(10, 0))
        material_box.columnconfigure(0, weight=1)
        self.material_var = tk.StringVar(value="Even material")
        self.captured_white_var = tk.StringVar(value="White captured: -")
        self.captured_black_var = tk.StringVar(value="Black captured: -")
        ttk.Label(material_box, textvariable=self.material_var, font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 6)
        )
        ttk.Label(material_box, textvariable=self.captured_white_var, font=("Segoe UI Symbol", 24, "bold")).grid(
            row=1, column=0, sticky="w", padx=12, pady=4
        )
        ttk.Label(material_box, textvariable=self.captured_black_var, font=("Segoe UI Symbol", 24, "bold")).grid(
            row=2, column=0, sticky="w", padx=12, pady=(4, 10)
        )

    # Handles _bind_events operations.
    def _bind_events(self) -> None:
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.moves_list.bind("<<ListboxSelect>>", self._on_notation_select)
        self.speed_combo.bind("<<ComboboxSelected>>", self._on_speed_mode_change)

    # Handles _on_moves_scrollbar operations.
    def _on_moves_scrollbar(self, *args: str) -> None:
        cast(Any, self.moves_list.yview)(*args)

    # Handles _on_moves_list_scroll operations.
    def _on_moves_list_scroll(self, first: str, last: str) -> None:
        self.moves_scrollbar.set(first, last)

    # Handles _on_speed_mode_change operations.
    def _on_speed_mode_change(self, _event: tk.Event[tk.Misc]) -> None:
        mode = self.animation_mode_var.get()
        self.animation_duration_ms = self.speed_map.get(mode, 200)

    # Handles _choose_piece_folder operations.
    def _choose_piece_folder(self) -> None:
        selected = filedialog.askdirectory(title="Choose Piece Image Folder", initialdir=str(self.image_dir))
        if not selected:
            return
        self.image_dir = Path(selected)
        self.image_cache.clear()
        self.status_var.set(f"Piece folder: {self.image_dir.name}")
        self._draw_board()

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
            raw: dict[str, object] = cast(dict[str, object], raw_obj)

            current_fen_obj: object = raw.get("current_fen")
            if isinstance(current_fen_obj, str):
                return current_fen_obj

            timeline_obj: object = raw.get("timeline")
            if isinstance(timeline_obj, list) and timeline_obj:
                timeline: list[object] = cast(list[object], timeline_obj)
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

    # Handles _on_notation_select operations.
    def _on_notation_select(self, _event: tk.Event[tk.Misc]) -> None:
        if self.suppress_notation_select:
            return
        selected = self.moves_list.curselection()
        if not selected:
            return
        list_index = int(selected[0])
        if not (0 <= list_index < len(self.notation_index_to_timeline)):
            return
        target_timeline = self.notation_index_to_timeline[list_index]
        if self.game.go_to(target_timeline):
            self.last_move = self.game.last_move_for_index()
            self._refresh_all()

    # Handles _refresh_all operations.
    def _refresh_all(self) -> None:
        self.mode_label.configure(text="Mode: Replay" if self.read_only_loaded_game else "Mode: Play")
        self._sync_move_list()
        self._update_material_panel()
        self._draw_board()

    # Handles _sync_move_list operations.
    def _sync_move_list(self) -> None:
        self.suppress_notation_select = True
        self.moves_list.delete(0, tk.END)
        self.notation_index_to_timeline = []

        notations = self.game.timeline_notations
        for idx in range(0, len(notations), 2):
            move_no = idx // 2 + 1
            white = notations[idx]
            black = notations[idx + 1] if idx + 1 < len(notations) else ""
            self.moves_list.insert(tk.END, f"{move_no:>2}. {white:<8} {black}")
            timeline_idx = idx + 2 if idx + 1 < len(notations) else idx + 1
            self.notation_index_to_timeline.append(timeline_idx)

        if self.game.timeline_index > 0:
            active = (self.game.timeline_index - 1) // 2
            if 0 <= active < self.moves_list.size():
                self.moves_list.selection_clear(0, tk.END)
                self.moves_list.selection_set(active)
                self.moves_list.see(active)
        self.suppress_notation_select = False

    # Handles _format_captured_icons operations.
    def _format_captured_icons(self, counts: dict[str, int], as_white: bool) -> str:
        order = ("q", "r", "b", "n", "p")
        chunks: list[str] = []
        for code in order:
            count = counts.get(code, 0)
            if count <= 0:
                continue
            glyph_key = code.upper() if as_white else code
            glyph = self.symbols[glyph_key]
            chunks.append(glyph if count == 1 else f"{glyph}x{count}")
        return " ".join(chunks) if chunks else "-"

    # Handles _update_material_panel operations.
    def _update_material_panel(self) -> None:
        balance = self.game.board.material_balance()
        if balance > 0:
            self.material_var.set(f"White +{balance}")
        elif balance < 0:
            self.material_var.set(f"Black +{abs(balance)}")
        else:
            self.material_var.set("Even material")

        captured_by_white, captured_by_black = self.game.board.captured_piece_counts()
        self.captured_white_var.set(f"White captured: {self._format_captured_icons(captured_by_white, as_white=False)}")
        self.captured_black_var.set(f"Black captured: {self._format_captured_icons(captured_by_black, as_white=True)}")

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
        board_dim = max(380, board_dim - 18)
        self.board_px = board_dim
        self.square_px = max(42, (board_dim - self.margin * 2) // 8)

        left = (self.canvas.winfo_width() - self.board_px) // 2 + self.margin
        top = (self.canvas.winfo_height() - self.board_px) // 2 + self.margin

        light = "#2a3138"
        dark = "#3b4650"
        last_a = "#586a3d"
        last_b = "#6c8248"
        select_color = "#3b5675"

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
        coord_size = max(12, int(self.square_px * 0.22))

        for col in range(8):
            file_char = chr(ord("a") + (7 - col if self.flipped else col))
            x = left + col * self.square_px + 4
            y = top + 8 * self.square_px - 4
            self.canvas.create_text(x, y, text=file_char, anchor="sw", fill="#9bb6d2", font=("Arial", coord_size, "bold"))

        for row in range(8):
            rank_char = str(row + 1 if self.flipped else 8 - row)
            x = left + 4
            y = top + row * self.square_px + 12
            self.canvas.create_text(x, y, text=rank_char, anchor="nw", fill="#9bb6d2", font=("Arial", coord_size, "bold"))

    # Handles _draw_legal_targets operations.
    def _draw_legal_targets(self) -> None:
        for x, y in self.legal_targets:
            occupant = self.game.board.grid[x][y]
            cx, cy = self._square_center(x, y)
            if occupant is None:
                radius = max(7, int(self.square_px * 0.12))
                self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill="#6f8f52", width=0)
            else:
                ring = self.square_px * 0.42
                self.canvas.create_oval(cx - ring, cy - ring, cx + ring, cy + ring, outline="#8fb16b", width=3)

    # Handles _piece_image operations.
    def _piece_image(self, abbrev: str) -> Optional[Any]:
        if Image is None or ImageTk is None:
            return None

        size = int(self.square_px * 0.88)
        key = (abbrev, size)
        if key in self.image_cache:
            return self.image_cache[key]

        candidates = [
            self.image_dir / f"{abbrev}.png",
            self.image_dir / f"{abbrev.lower()}.png",
            self.image_dir / f"{'w' if abbrev.isupper() else 'b'}{abbrev.upper()}.png",
            self.image_dir / f"{'w' if abbrev.isupper() else 'b'}_{abbrev.upper()}.png",
        ]
        source = next((path for path in candidates if path.exists()), None)
        if source is None:
            return None

        image = Image.open(source).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
        tk_image: Any = ImageTk.PhotoImage(image)
        self.image_cache[key] = tk_image
        return tk_image

    # Handles _draw_pieces operations.
    def _draw_pieces(self) -> None:
        hidden_to: Optional[tuple[int, int]] = self.anim_to if self.animating else None

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
                    cast(Any, self.canvas).create_image(cx, cy, image=image)
                else:
                    self.canvas.create_text(
                        cx,
                        cy,
                        text=self.symbols[piece.abbreviation],
                        font=("DejaVu Sans", int(self.square_px * 0.7), "bold"),
                        fill="#101316" if piece.color else "#0a0a0a",
                    )

    # Handles _draw_drag_piece operations.
    def _draw_drag_piece(self) -> None:
        if self.drag_state is None or self.drag_started:
            return
        x, y = self.drag_state["from_x"], self.drag_state["from_y"]
        cx, cy = self._square_center(x, y)
        abbrev = self.drag_state["piece_abbrev"]
        self.canvas.create_text(
            cx,
            cy,
            text=self.symbols[abbrev],
            font=("DejaVu Sans", int(self.square_px * 0.7), "bold"),
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
            font=("DejaVu Sans", int(self.square_px * 0.7), "bold"),
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
            self.drag_state = None
            self.drag_started = False
            self._draw_board()
            return

        if self.read_only_loaded_game:
            self.status_var.set("Replay mode: moves disabled")
            return

        if self.selected_square is not None:
            from_sq = self.selected_square
            if square in self.legal_targets:
                self._play_move(from_sq, square)
                return
            if square in self.pseudo_targets:
                self._flash_king()
                return

        x, y = square
        piece = self.game.board.grid[x][y]
        if piece is None:
            self.selected_square = None
            self.legal_targets.clear()
            self.pseudo_targets.clear()
            self.drag_state = None
            self.drag_started = False
            self._draw_board()
            return

        if piece.color != self.game.board.side_to_move:
            return

        self.selected_square = (x, y)
        self.legal_targets = {(m.to_x, m.to_y) for m in self.game.board.get_legal_move_objects(piece)}
        self.pseudo_targets = {(m.to_x, m.to_y) for m in self.game.board.pseudo_moves_for_piece(piece)}

        self.drag_state = {"from_x": x, "from_y": y, "piece_abbrev": piece.abbreviation, "item_id": -1}
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
            font=("DejaVu Sans", int(self.square_px * 0.7), "bold"),
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
            self.drag_state = None
            self.drag_started = False
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
        self.flash_after_id = self.after(240, self._clear_flash)

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
        if self.animation_duration_ms <= 0:
            self.animating = False
            self.anim_piece_abbrev = None
            self.anim_from = None
            self.anim_to = None
            self.anim_progress = 0.0
            self._refresh_all()
            return

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
