# Lspy-Chat
A Chat Application Based on Tepy-Chat. High performance, High concurrence. And Secure protocols.

## Features

+ Server speak
+ Online list
+ Set nickname
+ Kick user (or IP)
+ Ban user (or IP)
+ Channels

## Licence

It uses the GPLv3 license, So you can:

+ Free to use
+ Modify
+ Share freely

## Usage

### Server

In server command line, it hasn't help message. So I wrote at it :\)

+ **Commands**

| Commands | Comments | Usage |
| --- | --- | --- |
| exit | Stop the server | None |
| say | Broadcast the message (From server) | say \<message\> |
| list | List the online user | list \<channel\> |
| listchan | List channels | None |
| kick | Kick the online user from server | kick \<nickname\> |
| kickip | Kick the connect by IP from server (Even if the name is not set)| kickip \<IP Address\> |
| ban | Ban the user from server | ban \<nickname\> |
| unban | Unban the user from server | unban \<nickname\> |
| banip | Ban the IP Address from server | banip \<IP Address\> |
| unbanip | Unban the IP Address from server | unbanip \<IP Address\> |
| chanper | Change the channel permission (black or white list) | chanper \<chan\>  b/w |
| userper | Change the name permission (add or remove from permission list) | userper \<nickname\> add/del \<channel\> |

When not connected, the ban still work. 
And pay attention to capitalization!

### Clients

+ **Commandline**
It has help message, so you can read it (I won't write it again once)

+ **GUI**
I will take you step by step to use it
<pre>
First:
    Type the Server IP Address to the "IP" Entry, and click the "Connect" Button

Second:
    Type your nickname to "Nickname" Entry, and click "Set" Button (after you connected)

Third:
    Click the "Channels" on the toolbar and choose your channel to join

Last:
    Start your chat

It has some Chinese, use the translator
</pre>

## Some things

I will update more things in the future, Stay tuned :\)