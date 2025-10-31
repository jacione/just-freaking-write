import asyncio
import shutil
import argparse
from pathlib import Path

try:
    import pyperclip
except ImportError:
    pyperclip = None

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, Window
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.styles import Style
from prompt_toolkit.layout.processors import Processor, Transformation


class LockHighlighter(Processor):
    """Highlight or hide locked vs erasable text based on lock_point."""
    def __init__(self, lock_point_ref, mask_locked=False, mask_locked_all=False):
        self.lock_point_ref = lock_point_ref
        self.mask_locked = mask_locked
        self.mask_locked_all = mask_locked_all

    def apply_transformation(self, ti):
        lock_point = self.lock_point_ref[0]
        doc = ti.document
        line_start = doc.translate_row_col_to_index(ti.lineno, 0)
        pos = line_start

        # For soft masking, find last ". " that is still within locked region
        mask_cutoff = None
        if self.mask_locked and not self.mask_locked_all:
            idx = doc.text.rfind(". ", 0, lock_point)
            if idx != -1:
                mask_cutoff = idx + 2  # include the ". "

        def mask_text(segment: str) -> str:
            """Mask segment but preserve trailing whitespace."""
            if not segment:
                return segment
            # Split into non-space prefix and trailing whitespace
            stripped = segment.rstrip()
            trail_len = len(segment) - len(stripped)
            return "█" * len(stripped) + (" " * trail_len)

        new_fragments = []
        for style, text in ti.fragments:
            if not text:
                new_fragments.append((style, text))
                continue

            frag_len = len(text)

            # Entire fragment is locked
            if pos + frag_len <= lock_point:
                if self.mask_locked_all:
                    new_fragments.append(("class:locked", mask_text(text)))
                elif self.mask_locked and mask_cutoff is not None and pos < mask_cutoff:
                    cutoff_in_frag = min(frag_len, max(0, mask_cutoff - pos))
                    masked = mask_text(text[:cutoff_in_frag])
                    remainder = text[cutoff_in_frag:]
                    if masked:
                        new_fragments.append(("class:locked", masked))
                    if remainder:
                        new_fragments.append(("class:locked", remainder))
                else:
                    new_fragments.append(("class:locked", text))

            # Entire fragment is erasable
            elif pos >= lock_point:
                new_fragments.append(("class:erasable", text))

            # Fragment straddles lock_point
            else:
                split_at = lock_point - pos
                before, after = text[:split_at], text[split_at:]
                if before:
                    if self.mask_locked_all:
                        new_fragments.append(("class:locked", mask_text(before)))
                    elif self.mask_locked and mask_cutoff is not None and pos < mask_cutoff:
                        cutoff_in_before = min(len(before), max(0, mask_cutoff - pos))
                        masked = mask_text(before[:cutoff_in_before])
                        remainder = before[cutoff_in_before:]
                        if masked:
                            new_fragments.append(("class:locked", masked))
                        if remainder:
                            new_fragments.append(("class:locked", remainder))
                    else:
                        new_fragments.append(("class:locked", before))
                if after:
                    new_fragments.append(("class:erasable", after))

            pos += frag_len

        return Transformation(new_fragments)


class ScratchpadEditor:
    def __init__(self, temp_file: Path = Path("temp.txt"), erasable_depth: int = 2,
                 mask_locked=False, mask_locked_all=False):
        self.temp_file = temp_file
        self.lock_point = [0]
        self.word_boundaries = []
        self.erasable_depth = max(1, erasable_depth)
        self.mask_locked = mask_locked
        self.mask_locked_all = mask_locked_all

        self._prev_len = 0

        if self.temp_file.exists():
            self.temp_file.unlink()

        self.default_status = (
            "Scratchpad | Ctrl+Q Quit | Ctrl+C Copy all | Ctrl+R Reset"
        )
        self._status_message = self.default_status

        self.text_area = TextArea(
            text="",
            multiline=True,
            wrap_lines=True,
            input_processors=[LockHighlighter(
                self.lock_point,
                mask_locked=self.mask_locked,
                mask_locked_all=self.mask_locked_all
            )],
        )

        self.text_area.buffer.on_text_changed += self._on_text_changed

        initial_width = shutil.get_terminal_size((80, 20)).columns
        self.status_bar = TextArea(
            text=self._format_status(self._status_message, initial_width - 1),
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
            after_render=self.update_status_bar,
        )

    # ---------- Status helpers ----------
    def set_status(self, message: str, temporary: bool = True):
        self._status_message = message
        if temporary:
            async def reset():
                await asyncio.sleep(2)
                if not self.app.is_running:
                    return
                self._status_message = self.default_status
                self.app.invalidate()
            self.app.create_background_task(reset())

    def _format_status(self, left_text: str, width: int) -> str:
        text = self.text_area.text
        words = len(text.split())
        chars = len(text)
        right = f"Words: {words}  Chars: {chars}"
        available = max(0, width - len(right) - 1)
        return f"{left_text[:available].ljust(available)} {right}"

    def update_status_bar(self, app):
        width = app.output.get_size().columns
        self.status_bar.text = self._format_status(self._status_message, width)

    # ---------- Core helpers ----------
    def save_file(self, text: str):
        self.temp_file.write_text(text, encoding="utf-8")

    def _on_text_changed(self, buf):
        text = buf.text
        cur = buf.cursor_position

        if len(text) > self._prev_len:
            idx = cur - 1
            if idx >= 0:
                ch = text[idx]
                prev_ch = text[idx - 1] if idx - 1 >= 0 else " "
                if not ch.isspace() and prev_ch.isspace():
                    self.word_boundaries.append(idx)
                    if len(self.word_boundaries) >= self.erasable_depth:
                        self.lock_point[0] = self.word_boundaries.pop(0)
                    self.save_file(text)
        elif len(text) < self._prev_len:
            while self.word_boundaries and self.word_boundaries[-1] >= len(text):
                self.word_boundaries.pop()
            self.save_file(text)

        self._prev_len = len(text)

    # ---------- Key bindings ----------
    def _bind_keys(self):
        @self.kb.add("backspace")
        def _(event):
            buf = event.app.current_buffer
            if buf.cursor_position > self.lock_point[0]:
                buf.delete_before_cursor(count=1)
                while self.word_boundaries and self.word_boundaries[-1] >= len(buf.text):
                    self.word_boundaries.pop()

        @self.kb.add(" ")
        def _(event):
            event.app.current_buffer.insert_text(" ")

        @self.kb.add("enter")
        def _(event):
            event.app.current_buffer.newline()

        @self.kb.add("c-q")
        def _(event):
            if self.temp_file.exists():
                self.temp_file.unlink()
            for task in list(self.app._background_tasks):
                task.cancel()
            event.app.exit()

        @self.kb.add("c-c")
        def _(event):
            if pyperclip:
                try:
                    pyperclip.copy(self.text_area.text)
                    self.set_status("[Copied ALL text]")
                except Exception:
                    self.set_status("[Clipboard error]")

        @self.kb.add("c-r")
        def _(event):
            self.text_area.text = ""
            self.lock_point[0] = 0
            self.word_boundaries.clear()
            self._prev_len = 0
            self.save_file("")
            self.set_status("[Editor reset]")

    # ---------- Run ----------
    async def run(self):
        await self.app.run_async()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Minimal scratchpad editor.")
    parser.add_argument(
        "-e", "--erasable-depth",
        type=int,
        default=2,
        help="Total number of editable words including the current one (default: 2).",
    )
    parser.add_argument(
        "-m", "--mask-locked",
        action="store_true",
        help="Mask locked text up to the last locked '. ' (soft masking).",
    )
    parser.add_argument(
        "-M", "--mask-locked-all",
        action="store_true",
        help="Mask all locked text (aggressive masking).",
    )
    args = parser.parse_args()

    asyncio.run(ScratchpadEditor(
        erasable_depth=args.erasable_depth,
        mask_locked=args.mask_locked,
        mask_locked_all=args.mask_locked_all
    ).run())