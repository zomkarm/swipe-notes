#!/usr/bin/env python3

"""
SwipeNotes — A lightweight swipe-based card app for quick notes, revision, and prompts.
Run: python main.py
"""

import json
import os
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, simpledialog

# ── Config ──────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "bg":         "#0f1117",
    "surface":    "#1a1d27",
    "card":       "#20243a",
    "card_hover": "#262b42",
    "accent":     "#4f7cff",
    "accent2":    "#7c4fff",
    "text":       "#e8eaf6",
    "sub":        "#8b90b0",
    "danger":     "#ff4f6e",
    "success":    "#4fff9a",
    "border":     "#2e3350",
}

# ── Persistence ──────────────────────────────────────────────────────────────
# load_data():
def load_data():
    data = {}
    for fname in os.listdir(DATA_DIR):
        if fname.endswith(".json"):
            topic = fname[:-5]  # strip .json
            try:
                with open(os.path.join(DATA_DIR, fname), "r", encoding="utf-8") as f:
                    data[topic] = json.load(f)
            except Exception:
                data[topic] = []
    return data

#  save_data():
def save_data(data):
    for topic, cards in data.items():
        with open(os.path.join(DATA_DIR, f"{topic}.json"), "w", encoding="utf-8") as f:
            json.dump(cards, f, indent=2, ensure_ascii=False)
        
# delete_topic_file:
def delete_topic_file(topic):
    path = os.path.join(DATA_DIR, f"{topic}.json")
    if os.path.exists(path):
        print("removing",path)
        os.remove(path)

# ── Main App ─────────────────────────────────────────────────────────────────
class SwipeNotesApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Swipe Notes")
        self.geometry("900x620")
        self.minsize(720, 520)
        self.wm_attributes("-zoomed", True)
        try:
            icon = tk.PhotoImage(file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets/icon.png"))
            self.wm_iconphoto(True, icon)
        except Exception:
            pass  # silently skip if icon file missing
        self.configure(fg_color=COLORS["bg"])

        self.data = load_data()          # {topic: [card_text, ...]}
        self.current_topic = None
        self.card_index = 0
        self._drag_start_x = None
        self._flipped = False

        self._build_ui()
        self._refresh_topic_list()
        self.bind("<Right>",  lambda e: self.next_card())
        self.bind("<Left>",   lambda e: self.prev_card())
        self.bind("<Escape>", lambda e: self.focus_set())

    # ── UI Build ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Left sidebar
        self.sidebar = ctk.CTkFrame(self, fg_color=COLORS["surface"],
                                    corner_radius=0, width=230)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Sidebar header
        hdr = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(20, 8))
        ctk.CTkLabel(hdr, text="⚡ TOPICS", font=ctk.CTkFont("Courier", 11, "bold"),
                     text_color=COLORS["accent"]).pack(side="left")

        add_btn = ctk.CTkButton(hdr, text="+", width=28, height=28,
                                fg_color=COLORS["accent"], hover_color=COLORS["accent2"],
                                font=ctk.CTkFont(size=16, weight="bold"),
                                corner_radius=8, command=self.add_topic)
        add_btn.pack(side="right")

        # Topic list scrollable
        self.topic_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent",
                                                    scrollbar_button_color=COLORS["border"])
        self.topic_scroll.pack(fill="both", expand=True, padx=8, pady=4)

        # Delete topic at bottom
        del_topic_btn = ctk.CTkButton(self.sidebar, text="🗑 Delete Topic",
                                      fg_color="transparent", hover_color="#2a0f18",
                                      text_color=COLORS["danger"], border_color=COLORS["danger"],
                                      border_width=1, corner_radius=8, height=32,
                                      command=self.delete_topic)
        del_topic_btn.pack(padx=12, pady=(4, 16), fill="x")

        # ── Right main area ──────────────────────────────────────────────────
        self.main = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        self.main.pack(side="right", fill="both", expand=True)

        # Top bar
        topbar = ctk.CTkFrame(self.main, fg_color=COLORS["surface"],
                              corner_radius=0, height=52)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        self.topic_label = ctk.CTkLabel(topbar, text="Select a topic →",
                                        font=ctk.CTkFont("Georgia", 16, slant="italic"),
                                        text_color=COLORS["sub"])
        self.topic_label.pack(side="left", padx=20, pady=12)

        self.counter_label = ctk.CTkLabel(topbar, text="",
                                          font=ctk.CTkFont("Courier", 12),
                                          text_color=COLORS["sub"])
        self.counter_label.pack(side="right", padx=20)

        # Card area
        card_area = ctk.CTkFrame(self.main, fg_color="transparent")
        card_area.pack(fill="both", expand=True, padx=40, pady=30)

        # The card itself
        self.card_frame = ctk.CTkFrame(card_area, fg_color=COLORS["card"],
                                       corner_radius=20,
                                       border_width=1, border_color=COLORS["border"])
        self.card_frame.pack(fill="both", expand=True)

        # Decorative accent line at top of card
        accent_bar = tk.Frame(self.card_frame, bg=COLORS["accent"], height=3)
        accent_bar.pack(fill="x")

        self.card_text = ctk.CTkTextbox(self.card_frame, fg_color="transparent",
                                        font=ctk.CTkFont("Georgia", 18),
                                        text_color=COLORS["text"],
                                        wrap="word", state="disabled",
                                        border_width=0, scrollbar_button_color=COLORS["border"])
        self.card_text.pack(fill="both", expand=True, padx=32, pady=28)

        # Swipe hint
        self.hint = ctk.CTkLabel(card_area, text="← → arrow keys or buttons to navigate",
                                 font=ctk.CTkFont(size=11), text_color=COLORS["border"])
        self.hint.pack(pady=(6, 0))

        # Bind drag-to-swipe
        self.card_frame.bind("<ButtonPress-1>",   self._drag_start)
        self.card_frame.bind("<ButtonRelease-1>", self._drag_end)
        self.card_text.bind("<ButtonPress-1>",    self._drag_start)
        self.card_text.bind("<ButtonRelease-1>",  self._drag_end)

        # Bottom controls
        controls = ctk.CTkFrame(self.main, fg_color=COLORS["surface"],
                                corner_radius=0, height=64)
        controls.pack(fill="x", side="bottom")
        controls.pack_propagate(False)

        inner = ctk.CTkFrame(controls, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        btn_cfg = dict(width=110, height=38, corner_radius=10,
                       font=ctk.CTkFont(size=13, weight="bold"))

        self.prev_btn = ctk.CTkButton(inner, text="◀  Prev",
                                      fg_color=COLORS["card"],
                                      hover_color=COLORS["card_hover"],
                                      border_width=1, border_color=COLORS["border"],
                                      command=self.prev_card, **btn_cfg)
        self.prev_btn.pack(side="left", padx=6)

        self.add_card_btn = ctk.CTkButton(inner, text="＋ Add Card",
                                          fg_color=COLORS["accent"],
                                          hover_color=COLORS["accent2"],
                                          command=self.add_card, **btn_cfg)
        self.add_card_btn.pack(side="left", padx=6)

        self.edit_btn = ctk.CTkButton(inner, text="✎ Edit",
                                      fg_color=COLORS["card"],
                                      hover_color=COLORS["card_hover"],
                                      border_width=1, border_color=COLORS["border"],
                                      command=self.edit_card, **btn_cfg)
        self.edit_btn.pack(side="left", padx=6)

        self.del_btn = ctk.CTkButton(inner, text="✕ Delete",
                                     fg_color="transparent",
                                     hover_color="#2a0f18",
                                     text_color=COLORS["danger"],
                                     border_color=COLORS["danger"], border_width=1,
                                     command=self.delete_card, **btn_cfg)
        self.del_btn.pack(side="left", padx=6)

        self.next_btn = ctk.CTkButton(inner, text="Next  ▶",
                                      fg_color=COLORS["card"],
                                      hover_color=COLORS["card_hover"],
                                      border_width=1, border_color=COLORS["border"],
                                      command=self.next_card, **btn_cfg)
        self.next_btn.pack(side="left", padx=6)

    # ── Topic list render ────────────────────────────────────────────────────
    def _refresh_topic_list(self):
        for w in self.topic_scroll.winfo_children():
            w.destroy()
        for topic in self.data:
            self._make_topic_btn(topic)
        if not self.data:
            ctk.CTkLabel(self.topic_scroll, text="No topics yet.\nClick + to add one.",
                         font=ctk.CTkFont(size=12), text_color=COLORS["sub"],
                         justify="center").pack(pady=20)

    def _make_topic_btn(self, topic):
        is_sel = (topic == self.current_topic)
        btn = ctk.CTkButton(
            self.topic_scroll,
            text=f"{'▶ ' if is_sel else '  '}{topic}",
            anchor="w",
            fg_color=COLORS["accent"] if is_sel else "transparent",
            hover_color=COLORS["card_hover"],
            text_color=COLORS["text"] if is_sel else COLORS["sub"],
            font=ctk.CTkFont(size=13, weight="bold" if is_sel else "normal"),
            corner_radius=8, height=38,
            command=lambda t=topic: self.select_topic(t)
        )
        btn.pack(fill="x", pady=2, padx=4)

    # ── Topic logic ──────────────────────────────────────────────────────────
    def add_topic(self):
        name = simpledialog.askstring("New Topic", "Topic name:", parent=self)
        if not name or not name.strip():
            return
        name = name.strip()
        if name in self.data:
            messagebox.showwarning("Exists", f'Topic "{name}" already exists.', parent=self)
            return
        self.data[name] = []
        save_data(self.data)
        self._refresh_topic_list()
        self.select_topic(name)

    def delete_topic(self):
        if not self.current_topic:
            messagebox.showinfo("Tip", "Select a topic first.", parent=self)
            return
        if not messagebox.askyesno("Delete Topic",
                                f'Delete "{self.current_topic}" and all its cards?',
                                parent=self):
            return
        # delete the file from disk first, before clearing current_topic
        topic_file = os.path.join(DATA_DIR, f"{self.current_topic}.json")
        if os.path.exists(topic_file):
            os.remove(topic_file)
        del self.data[self.current_topic]
        self.current_topic = None
        self.card_index = 0
        self._refresh_topic_list()
        self._render_card()

    def select_topic(self, topic):
        self.current_topic = topic
        self.card_index = 0
        self._refresh_topic_list()
        self._render_card()

    # ── Card logic ───────────────────────────────────────────────────────────
    def _cards(self):
        if self.current_topic and self.current_topic in self.data:
            return self.data[self.current_topic]
        return []

    def _render_card(self):
        cards = self._cards()
        topic = self.current_topic or "Select a topic →"
        self.topic_label.configure(text=topic)

        self.card_text.configure(state="normal")
        self.card_text.delete("1.0", "end")

        if not self.current_topic:
            self.card_text.insert("1.0", "👈  Select or create a topic to begin.")
            self.counter_label.configure(text="")
        elif not cards:
            self.card_text.insert("1.0", "No cards yet.\nClick ＋ Add Card to create one.")
            self.counter_label.configure(text="0 / 0")
        else:
            self.card_index = max(0, min(self.card_index, len(cards) - 1))
            self.card_text.insert("1.0", cards[self.card_index])
            self.counter_label.configure(
                text=f"Card  {self.card_index + 1} / {len(cards)}")

        self.card_text.configure(state="disabled")

    def next_card(self):
        cards = self._cards()
        if not cards:
            return
        self.card_index = (self.card_index + 1) % len(cards)
        self._animate_slide("left")
        self._render_card()

    def prev_card(self):
        cards = self._cards()
        if not cards:
            return
        self.card_index = (self.card_index - 1) % len(cards)
        self._animate_slide("right")
        self._render_card()

    def add_card(self):
        if not self.current_topic:
            messagebox.showinfo("Tip", "Select a topic first.", parent=self)
            return
        dlg = CardDialog(self, title="Add Card")
        text = dlg.result
        if text and text.strip():
            self.data[self.current_topic].append(text.strip())
            self.card_index = len(self.data[self.current_topic]) - 1
            save_data(self.data)
            self._render_card()

    def edit_card(self):
        cards = self._cards()
        if not cards:
            messagebox.showinfo("Tip", "No card to edit.", parent=self)
            return
        dlg = CardDialog(self, title="Edit Card", initial=cards[self.card_index])
        text = dlg.result
        if text and text.strip():
            self.data[self.current_topic][self.card_index] = text.strip()
            save_data(self.data)
            self._render_card()

    def delete_card(self):
        cards = self._cards()
        if not cards:
            return
        if not messagebox.askyesno("Delete Card", "Delete this card?", parent=self):
            return
        cards.pop(self.card_index)
        self.card_index = max(0, self.card_index - 1)
        save_data(self.data)
        self._render_card()

    # ── Swipe gesture ─────────────────────────────────────────────────────────
    def _drag_start(self, e):
        self._drag_start_x = e.x_root

    def _drag_end(self, e):
        if self._drag_start_x is None:
            return
        delta = e.x_root - self._drag_start_x
        self._drag_start_x = None
        if delta < -60:
            self.next_card()
        elif delta > 60:
            self.prev_card()

    # ── Slide animation ───────────────────────────────────────────────────────
    def _animate_slide(self, direction):
        # Lightweight flash effect
        orig = COLORS["card"]
        flash = COLORS["card_hover"]
        self.card_frame.configure(fg_color=flash)
        self.after(80, lambda: self.card_frame.configure(fg_color=orig))


# ── Card Text Dialog ──────────────────────────────────────────────────────────
class CardDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="Card", initial=""):
        super().__init__(parent)
        self.title(title)
        self.update_idletasks()
        w, h = 560, 380
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.resizable(True, True)
        self.configure(fg_color=COLORS["bg"])
        self.result = None
        self.after(100, self.grab_set)

        ctk.CTkLabel(self, text=title, font=ctk.CTkFont("Georgia", 17, "bold"),
                     text_color=COLORS["text"]).pack(padx=24, pady=(20, 8), anchor="w")

        ctk.CTkLabel(self, text="Enter card content below:",
                     font=ctk.CTkFont(size=12), text_color=COLORS["sub"]).pack(
            padx=24, anchor="w")

        self.textbox = ctk.CTkTextbox(self, fg_color=COLORS["card"],
                                      font=ctk.CTkFont("Georgia", 15),
                                      text_color=COLORS["text"],
                                      border_width=1, border_color=COLORS["border"],
                                      corner_radius=12, wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=24, pady=12)
        if initial:
            self.textbox.insert("1.0", initial)
        self.textbox.focus()

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(padx=24, pady=(0, 20), fill="x")

        ctk.CTkButton(btns, text="Cancel", width=100,
                      fg_color="transparent", border_width=1,
                      border_color=COLORS["border"], text_color=COLORS["sub"],
                      hover_color=COLORS["card"], corner_radius=8,
                      command=self.destroy).pack(side="right", padx=(8, 0))

        ctk.CTkButton(btns, text="Save", width=100,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent2"],
                      corner_radius=8, font=ctk.CTkFont(weight="bold"),
                      command=self._save).pack(side="right")

        self.bind("<Control-Return>", lambda e: self._save())
        self.bind("<Escape>",         lambda e: self.destroy())
        self.wait_window()

    def _save(self):
        self.result = self.textbox.get("1.0", "end").strip()
        self.destroy()


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        import customtkinter  # noqa
    except ImportError:
        import subprocess, sys
        print("Installing customtkinter...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
    app = SwipeNotesApp()
    app.mainloop()
