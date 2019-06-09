# Lagoon (ラグーン) X68000K - English translation patch

This is a translation patch for Lagoon, an action RPG for the Japan-exclusive Sharp X68000 gaming PC. 

While Lagoon was later ported to the SFC/SNES and released in English, significant changes were made to its plot in the port. As far as I know, this is the only extant attempt to translate the original game.

Please note that my Japanese is pretty terrible, so there are likely all kinds of mistakes in the translations contributed by me. I won't object too much if someone better at reading Japanese submits improved translations to this project.

I have also transcribed and translated the plot and item-related sections of the manual, mostly for my own reference. Those are available in the repository [here](doc/manual_translation.txt)&mdash;or, if you downloaded a release, they should be in that archive. The original manual I'm basing this on is scanned online [here](https://archive.org/details/LagoonX68000).

The main repository for this project is on [GitHub](https://github.com/nleseul/lagoon_x68k_trans); any issues you find can be reported there. You can also visit [my personal web portal](http://nleseul.this-life.us/) or [email me directly](mailto:nleseul@this-life.us).

## Applying the patch

The patch is released in BPS format, because that handles floppy images better than IPS. You'll need a patching program capable of applying BPS patches. I used [Floating IPS](https://www.romhacking.net/utilities/1040/) (also available on [GitHub](https://github.com/Alcaro/Flips)) to make them.

The original Lagoon was distributed on five floppies. The versions archived online have various names, but the original disks were labeled "System", "Data 1" through "Data 3", and "User". You can see the original labels scanned in the manual linked above.

Releases of this patch should have two patches, for the "System" and "User" disks. There's also another version of the "System" patch based on a different online distribution of the disks that did not contain a "User" image.

"System" CRC32 (XDF format): `F283C7F6`\
"User" CRC32 (XDF format): `5480B64D`

Alternate "System" CRC32 (DIM format): `684A43EF`

Both of these disks have basically the same data files, so you will need to patch both of them. Flips may complain about the checksum on the user disk, though, if your version happens to have user save data that doesn't match my copy. Hopefully the user disk patch will apply okay regardless, but I can't be sure.

If you can't get the user disk patch to work, though&mdash;or if your download doesn't include a user disk&mdash;that's fine; the game does give you a mechanism for creating a new one using the data on your (patched) system disk.

I'm probably not supposed to link to downloads of the game disks. Just ask Google.

## Creating a new user disk

Like many games released on floppies, Lagoon expects you to make a copy of one of the original disks and use it to store your progress. To do that:
* Boot the game and load into the first area. Just re-insert the system disk when prompted for a user disk.
* Press F1 for the disk menu.
* Select "Make".
* Insert a blank floppy into the second drive. Your emulator should give you a way to make a blank floppy.
* When prompted for a password, it's `XF1` `XF2` `E` `I` `S`. This is in the manual.
* Wait a minute while the disks churn. 
* Put the new user disk in the first drive (drive 0) and the requested data disk in the second drive (drive 1).
* Continue playing, saving your progress as you like.

## Building the patch

This process is only necessary if you want to make your own modifications to the patch&mdash;or I guess if you want to look at unreleased changes if there ever are any. You will need to acquire the source repository via GitHub at the aforementioned link.

Running the script is straightforward enough:

`> python build_patch.py _orig _dest`

Here, `_orig` is a folder containing the contents of the Lagoon system disk (disk 0 in some distributions), and `_dest` is a folder into which the modified files will be placed. Those folders can be whatever, but those names are what I use (and what I've set up the `.gitignore` to ignore).

The hard part is getting the files in question on and off the disk images. I haven't found very good tools for working with X68K disk images, and haven't found any way to automate that process.

There's a tool called [WinXDF](https://zophar.net/utilities/computil/winxdf.html) that works okay to dump the entire contents of an .xdf image to a folder quickly, but I don't believe it has any way to write files back to the image.

[DiskExplorer](https://hp.vector.co.jp/authors/VA013937/editdisk/index_e.html) (also known as editdisk to avoid confusion with a bigger application of the same name) lets you browse disk images interactively and supports writing files to them, but I don't think it handles bulk operations involving subdirectories very well. It also had trouble autodetecting the filesystem on my Lagoon images. Using the "Manual FD" and searching for a Human68K FS worked for the system disk, at least. There might be a better way to configure it, but I haven't found it yet.

Another option that I used is to create a hard drive image in my X68K emulator and open that in DiskExplorer, which doesn't have any problems with hard drive images. You can then copy files from that hard drive to your floppy images at the Human68K prompt within the emulator.

At any rate, to run the patched game, you will need to copy the files produced by the script back to the system disk, and, if you have one, the user disk. (Or you should be able to create a new user disk from in the game based on your patched system disk, if you really want to.) This should include the main LAGOON.X executable, and all the files in the IVENT subfolder.