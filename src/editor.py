import asyncio
from pathlib import Path

try:
    import pyperclip
except Exception:
    pyperclip = None

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, Window
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.styles import Style
from prompt_toolkit.layout.processors import Processor, Transformation


class LockHighlighter(Processor):
    """Highlight locked vs erasable text based on lock_point."""
    def __init__(self, lock_point_ref):
        self.lock_point_ref = lock_point_ref

    def apply_transformation(self, ti):
        lock_point = self.lock_point_ref[0]
        doc = ti.document
        line_start = doc.translate_row_col_to_index(ti.lineno, 0)
        pos = line_start

        new_fragments = []
        for style, text in ti.fragments:
            if not text:
                new_fragments.append((style, text))
                continue

            frag_len = len(text)
            if pos + frag_len <= lock_point:
                new_fragments.append(("class:locked", text))
            elif pos >= lock_point:
                new_fragments.append(("class:erasable", text))
            else:
                split_at = lock_point - pos
                before, after = text[:split_at], text[split_at:]
                if before:
                    new_fragments.append(("class:locked", before))
                if after:
                    new_fragments.append(("class:erasable", after))
            pos += frag_len

        return Transformation(new_fragments)


class ScratchpadEditor:
    def __init__(self, temp_file: Path = Path("temp.txt")):
        self.temp_file = temp_file
        self.lock_point = [0]
        self.word_boundaries = []

        if self.temp_file.exists():
            self.temp_file.unlink()

        self.text_area = TextArea(
            text="",
            multiline=True,
            wrap_lines=True,
            input_processors=[LockHighlighter(self.lock_point)],
        )

        self.status_bar = TextArea(
            text="Scratchpad | Ctrl+Q Quit | Ctrl+X Copy all | Ctrl+C Copy last paragraph | Ctrl+R Reset",
            height=1,
            style="class:status",
            focusable=False,
        )

        self.kb = KeyBindings()
        self._bind_keys()

        self.style = Style.from_dict({
            "status": "reverse",
            "locked": "fg:ansiblue",
            "erasable": "fg:ansired bold",
        })

        root_container = HSplit([
            self.text_area,
            Window(height=1, char="-", style="class:line"),
            self.status_bar,
        ])
        self.layout = Layout(root_container)

        self.app = Application(
            layout=self.layout,
            key_bindings=self.kb,
            full_screen=True,
            style=self.style,
        )

    # ---------- Core helpers ----------
    def save_file(self, text: str):
        self.temp_file.write_text(text, encoding="utf-8")

    def commit_word(self):
        buf = self.text_area.buffer
        self.word_boundaries.append(len(buf.text))
        if len(self.word_boundaries) > 2:
            self.lock_point[0] = self.word_boundaries.pop(0)
        self.save_file(buf.text)
        self.status_bar.text = "[Autosaved] | Ctrl+Q Quit | Ctrl+X Copy all | Ctrl+C Copy last paragraph | Ctrl+R Reset"

    # ---------- Key bindings ----------
    def _bind_keys(self):
        @self.kb.add("backspace")
        def _(event):
            buf = event.app.current_buffer
            if buf.cursor_position > self.lock_point[0]:
                buf.delete_before_cursor(count=1)
                while self.word_boundaries and self.word_boundaries[-1] > len(buf.text):
                    self.word_boundaries.pop()

        @self.kb.add(" ")
        def _(event):
            event.app.current_buffer.insert_text(" ")
            self.commit_word()

        @self.kb.add("enter")
        def _(event):
            event.app.current_buffer.newline()
            self.commit_word()

        @self.kb.add("c-q")
        def _(event):
            if self.temp_file.exists():
                self.temp_file.unlink()
            event.app.exit()

        @self.kb.add("c-x")
        def _(event):
            if pyperclip:
                try:
                    pyperclip.copy(self.text_area.text)
                    self.status_bar.text = "[Copied ALL text]"
                except Exception:
                    self.status_bar.text = "[Clipboard error]"

        @self.kb.add("c-c")
        def _(event):
            text = self.text_area.text.rstrip()
            last_para = text.split("\n\n")[-1] if "\n\n" in text else text
            if pyperclip:
                try:
                    pyperclip.copy(last_para)
                    self.status_bar.text = "[Copied LAST paragraph]"
                except Exception:
                    self.status_bar.text = "[Clipboard error]"

        @self.kb.add("c-r")
        def _(event):
            self.text_area.text = ""
            self.lock_point[0] = 0
            self.word_boundaries.clear()
            self.save_file("")  # overwrite with empty file
            self.status_bar.text = "[Editor reset]"

    # ---------- Run ----------
    async def run(self):
        await self.app.run_async()


if __name__ == "__main__":
    asyncio.run(ScratchpadEditor().run())