import os, asyncio, pyperclip
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, Window
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.styles import Style
from prompt_toolkit.layout.processors import Processor, Transformation

TEMP_FILE = "temp.txt"

class LockHighlighter(Processor):
    """Highlight locked vs erasable text based on lock_point."""
    def __init__(self, lock_point_ref):
        self.lock_point_ref = lock_point_ref

    def apply_transformation(self, ti):
        fragments = []
        text = ti.document.text
        lock_point = self.lock_point_ref[0]
        for i, ch in enumerate(text):
            if i < lock_point:
                fragments.append(("class:locked", ch))
            else:
                fragments.append(("class:erasable", ch))
        return Transformation(fragments)

async def editor():
    # Always start with a clean slate
    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)

    def save_file(text):
        with open(TEMP_FILE, "w") as f:
            f.write(text)

    lock_point = [0]
    word_boundaries = []

    text_area = TextArea(
        text="",
        multiline=True,
        wrap_lines=True,
        input_processors=[LockHighlighter(lock_point)]
    )

    status_bar = TextArea(
        text="Scratchpad | Ctrl+Q = Quit | Ctrl+C = Copy to clipboard",
        height=1,
        style="class:status",
        focusable=False
    )

    kb = KeyBindings()

    def commit_word():
        buf = text_area.buffer
        word_boundaries.append(len(buf.text))
        while word_boundaries and word_boundaries[-1] > len(buf.text):
            word_boundaries.pop()
        if len(word_boundaries) > 2:
            lock_point[0] = word_boundaries.pop(0)
        save_file(buf.text)
        status_bar.text = "[Autosaved] | Ctrl+Q = Quit | Ctrl+C = Copy"

    @kb.add("backspace")
    def limited_backspace(event):
        buf = event.app.current_buffer
        if buf.cursor_position > lock_point[0]:
            buf.delete_before_cursor(count=1)
            while word_boundaries and word_boundaries[-1] > len(buf.text):
                word_boundaries.pop()

    @kb.add(" ")
    def on_space(event):
        event.app.current_buffer.insert_text(" ")
        commit_word()

    @kb.add("enter")
    def on_enter(event):
        event.app.current_buffer.newline()
        commit_word()

    # for char in [".", ",", "!", "?", ";", ":"]:
    #     @kb.add(char)
    #     def _(event, c=char):
    #         event.app.current_buffer.insert_text(c)
    #         commit_word()

    @kb.add("c-q")
    def on_quit(event):
        if os.path.exists(TEMP_FILE):
            os.remove(TEMP_FILE)
        event.app.exit()

    @kb.add("c-c")
    def on_copy(event):
        pyperclip.copy(text_area.text)
        status_bar.text = "[Copied to clipboard] | Ctrl+Q = Quit | Ctrl+C = Copy"

    style = Style.from_dict({
        "status": "reverse",
        "locked": "fg:ansiblue",
        "erasable": "fg:ansired bold",
    })

    root_container = HSplit([
        text_area,
        Window(height=1, char="-", style="class:line"),
        status_bar
    ])

    layout = Layout(root_container)

    app = Application(
        layout=layout,
        key_bindings=kb,
        full_screen=True,
        style=style
    )

    await app.run_async()

if __name__ == "__main__":
    asyncio.run(editor())