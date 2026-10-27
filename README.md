# Agdapm
A small package manager for Agda that generates defaults and libraries files.

This was made out of my personal frustration so it's only tested on my Windows machine. 

Run ```py .\meta.py init```, then ``` py .\meta.py install ``` followed by a Git repository. 

Example usage: ``` py .\meta.py install https://github.com/agda/agda-categories ```

It should then rebuild your defaults and config.
