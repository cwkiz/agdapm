# Agdapm
A small package manager for Agda that generates defaults and libraries files.

This was made out of my personal frustration so it's only tested on my Windows machine. 

Run ```py -m agdapm init```, then ``` py -m agdapm install ``` followed by a Git repository. 

Example usage: ``` py -m agdapm install https://github.com/agda/agda-categories ```

It should then rebuild your defaults and config. It'll store the repository content in a default directory the tool will generate (~/.agdapm or AppData\Roaming\agdapm) and link the configs to it.

The install command can also take in ZIP files of a library.