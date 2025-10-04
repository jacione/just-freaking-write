# just-freaking-write
Are you the kind of person that spends hours agonizing over a few sentences? Are you sick of ending a writing session with nothing to show for it? Do you wish you could just write an imperfect (but complete) draft? Well today might be your lucky day!

just-freaking-write is a superminimal text editor that prevents backspacing more than a few words. Since it's not meant for you to write a whole document like this, it doesn't save your work to a file. Instead, you just hit ctrl-C to copy the text to your clipboard, which you can then paste into a real text editor for... y'know... editing. Perhaps you can tell by the rambling nature of this paragraph, that it was written using this tool. In fact, I just realized I shouldn't have used a comma in that last sentence, but I CAN"T CHANGE IT NOW. Maybe this will help me finally write on a deadline. Here's hoping!

# Instructions
## Step 1: Dependencies
For all operating systems:
```
pip install prompt-toolkit pyinstaller pyperclip
```
If running on Ubuntu/Debian, you will also need tp run:
```
sudo apt install xclip
```
If on another Linux distro... I'll just assume you can figure it out.

## Step 2: Installation
Clone (or otherwise download) the git repository, then run
```
cd your/path/here/just-freaking-write
pyinstaller just_freaking_write.spec
```
The executable will be compiled in `just-freaking-write/dist`

## Step 3: Write
Launch the executable, write what you want, then hit ctrl-C to copy it all to your clipboard. When you're ready to quit, ctrl-Q will close the application.