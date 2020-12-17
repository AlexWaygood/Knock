# Knock
Multiplayer game of the card game Knock, also known as "Diminishing Contract Whist", or "Oh Hell!"

Main game script developed entirely by Alex Waygood; the code for the fireworks display has been adapted from code by Adam Binks: https://github.com/adam-binks/Fireworks

This game accepts between 2 and 6 players.

# Running this code
In order to play this game:
* KnockServer.py (the server script) must be run on a computer.
* Simultaneously, each player must run Knock.py (the client script).
* The client script can be run either on Python or as a .exe file. The server script can only be run on Python.
* All scripts require Python 3.8. Run pip install requirements.txt on the command line to install the necessary dependencies.
* All players must have an internet connection.
* The router for the wifi network that the server-script is using must have port forwarding set up (see below).
* You will need to set a password length, if you wish to use a password, in PasswordChecker.py.
* If the person running the server script wishes to pre-screen attempted connections before allowing them to join the game, you will need to create an account at https://ipinfo.io/, and insert your account access token in Network.py.
* Users running either the client or the server script may need to disable their firewall settings for Python.

# Setting up port forwarding for the server script.
For more information on setting up port-forwarding for the server-script, see the following two websites:
* https://www.howtogeek.com/66214/how-to-forward-ports-on-your-router/
* https://portforward.com/networking/static-ip-windows-10.htm (Windows 10 only).

The computer running the server script must have a static IP address, in addition to having port forwarding set up on their router.
Once port forwarding is set up, the port being used should be entered into KnockServer.py.

In choosing your port number, you may wish to consult https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers.
If the port number is listed in the article, it is a bad idea to use it if the process using it is one that is used by your machine.
It is essential to choose a port number >5000.

If you wish for players to be able to connect via hostname instead of IP address, you will have to create an account with a service like Dynu: https://dynu.com.

# Requirements in brief
* pygame (essential)
* pyinputplus (essential)
* Pillow (essential)
* pycryptodome (if you want to set up a password for a game)
* ipinfo (if you want to be able to screen the users who are trying to connect to the server)

For a full list of requirements, see requirements.txt

# Rules of the game
Knock is a simple whist-derived game, also known as 'Diminishing Whist', 'Diminishing Contract Whist' and 'Oh Hell!'.
It is played with a standard pack of cards, excluding jokers.
Aces > Queens > Jacks > 10 > ... > 2.

Players compete individually in this game.
Each round, a player states how many tricks he believes he can win with his hand before play begins.

At the end of the round, the player receives one point for each trick he has won, with an additional 10-point bonus if he has won the precise number that he bid (no more, no less).
There is therefore often a great benefit to deliberately losing tricks.

The winner at the end of the game is the player with the most points.
The number of cards decreases by one each round.

The trumpsuit is determined by randomly choosing a card from the pack at the beginning of each round.
Once this card has been chosen, it is laid face-up on the table, so that all players know that it is no longer in the pack.

The game can theoretically start with any number of cards, providing:
* Only one pack is used.
* At least one card remains in the pack, to be used as a trumpcard.
* All players have the same number of cards.

However, due to screen-size limitations, this implementation of Knock has an upper limit of 13 cards to start.

Some variations of this game have players bid sequentially, such that each player except the first has some information about what the other players will be bidding in this round.

However, this version of the game implements the variant in which no player knows what any other player will be bidding until all bidding is complete.

Play occurs clockwise.
The person starting the round rotates each round.

For more information on the rules (though describing slightly different variants described to this one), you can consult:
* https://www.fgbradleys.com/rules/rules4/Contract%20Whist%20-%20rules.pdf
* https://en.wikipedia.org/wiki/Whist#:~:text=Diminishing%20contract%20whist%20(a%20British,10%20for%20matching%20their%20contract.
* https://www.theguardian.com/lifeandstyle/2008/nov/22/rules-card-games-oh-hell

# Client script (Knock.py)
This script is run by each player in this game. 
The script will only work if the Server script is running at the same time as this script.

The window for this script may open up in the background after the necessary inputs have been entered.

A version of the client script that has been packaged as a .exe file is also included in this repo, for users who may not have Python installed.

Icon for this game taken from https://www.flaticon.com/authors/dinosoftlabs

Fireworks display in this code was adapted from code by Adam Binks: https://github.com/adam-binks/Fireworks

# Server script (KnockServer.py)
This script runs the server for the game, which communicates with the clients through the threading and socket modules. 
There is an option to set up a password for each session, which is communicated securely between server and client using pycryptodome and the Diffie-Hellman algorithm.

Most of the code for the gameplay is in Game.py and the Knock.py. 
As a result, this file is fairly thin on content, acting as a lightweight coordinator between the clients and classes.