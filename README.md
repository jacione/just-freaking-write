# Just Freaking Write
Are you the kind of person that spends hours agonizing over a few sentences? Are you sick of ending a writing session with nothing to show for it? Do you wish you could just write an imperfect (but complete) draft? Well today might be your lucky day!

just-freaking-write is a superminimal text editor that prevents backspacing more than a few words. Since it's not meant for you to write a whole document like this, it doesn't save your work to a file. Instead, you just copy the text to your clipboard, which you can then paste into a real text editor for... y'know... editing. Perhaps you can tell by the rambling nature of this paragraph, that it was written using this tool. In fact, I just realized I shouldn't have used a comma in that last sentence, but I CAN"T CHANGE IT NOW. Maybe this will help me finally write on a deadline. Here's hoping!

# Instructions
## Dependencies
For all operating systems:
```
pip install prompt-toolkit pyinstaller pyperclip
```
If running on Ubuntu/Debian, you will also need tp run:
```
sudo apt install xclip
```
If on another Linux distro... I'll just assume you can figure it out.

## Installation
Clone (or otherwise download) the git repository. From that directory, run
```
python install.py
```
The executable will be compiled as `~/just-freaking-write/dist/jfwedit.exe`. If you add the `dist` directory to your Windows PATH (or equivalent) you will be able to execute it simply by typing
```
jfwedit
```
in your terminal. If you're in Linux, I will once again assume you know what to do.

## Options
There are currently three command-line arguments:

`--erasable-depth <num>` or `-e <num>` sets the number of words that you can type before they start locking into place. Default is 2.

`--mask-locked` or `-m` covers your text up to the last fully locked sentence. This can be useful to prevent yourself from even _reading_ what you've written before it's time to edit.

`--mask-locked-all` or `-M` is a more aggressive masking, that covers ALL text as soon as it's locked in. (In case of masochism, break glass.)

## Just freaking write.
It's as simple as that. Once you have something written, you have three options:

`ctrl-C` copy what you've written

`ctrl-R` reset the editor

`ctrl-Q` close the application
