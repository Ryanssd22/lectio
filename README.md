# lectio

Fetches the daily bible reading

Ideas:
parsebible.cpp is used to parse a bible.txt into a more "efficient" data structure.
I was thinking a parsed file to look as so:

GENESIS<br/>
1:1 In the beginning...<br/>
1:2 But the earth...<br/>
...<br/>
50:26 he died, having completed...<br/>
^<br/>
EXODUS<br/>
1:1 These are the names...<br/>
...<br/>
^<br/>
LEVITICUS<br/>
...<br/>

And so on.
Each chapter will end with the delimiter ^. This will allow us to read just the name of the chapter, and if it is
not the desired chapter, we simply .ignore() until the delimiter '^'.
