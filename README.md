# Lagoon (ラグーン) X68000K - English translation patch

This is a translation patch for Lagoon, an action RPG for the Japan-exclusive Sharp X68000 gaming PC. 

While Lagoon was later ported to the SFC/SNES and released in English, significant changes were made to its plot in the port. As far as I know, this is the only extant attempt to translate the original game.

Please note that my Japanese is pretty terrible, so there are likely all kinds of mistakes in the translations contributed by me. I won't object too much if someone better at reading Japanese submits improved translations to this project.

## Building the patch

(I will eventually be releasing this as an IPS or BPS patch or some such, so building it yourself is only necessary if you're making modifications to it yourself, or if you really want to preview the work in progress.)

Running the script is straightforward enough:

`> python build_patch.py _orig _dest`

Here, `_orig` is a folder containing the contents of the Lagoon system disk (disk 0 in some distributions), and `_dest` is a folder into which the modified files will be placed. Those folders can be whatever, but those names are what I use (and what I've set up the `.gitignore` to ignore).

The hard part is getting the files in question on and off the disk images. I haven't found very good tools for working with X68K disk images, and haven't found any way to automate that process.

There's a tool called [WinXDF](https://zophar.net/utilities/computil/winxdf.html) that works okay to dump the entire contents of an .xdf image to a folder quickly, but I don't believe it has any way to write files back to the image.

[DiskExplorer](https://hp.vector.co.jp/authors/VA013937/editdisk/index_e.html) (also known as editdisk to avoid confusion with a bigger application of the same name) lets you browse disk images interactively and supports writing files to them, but I don't think it handles bulk operations involving subdirectories very well. It also had trouble autodetecting the filesystem on my Lagoon images. Using the "Manual FD" and searching for a Human68K FS worked for the system disk, at least. There might be a better way to configure it, but I haven't found it yet.

Another option that I used is to create a hard drive image in my X68K emulator and open that in DiskExplorer, which doesn't have any problems with hard drive images. You can then copy files from that hard drive to your floppy images at the Human68K prompt within the emulator.

At any rate, to run the patched game, you will need to copy the files produced by the script back to the system disk, and, if you have one, the user disk. (Or you should be able to create a new user disk from in the game based on your patched system disk, if you really want to.) This should include the main LAGOON.X executable, and all the files in the IVENT subfolder.