import os
from subprocess import call
from pathlib import Path

os.chdir(Path(__file__).parent)
call("pyinstaller just_freaking_write.spec")