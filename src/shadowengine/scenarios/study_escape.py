"""
Study Room Escape Game - A puzzle-based escape room experience.

You've been locked in a mysterious study. Find clues, solve puzzles,
and escape before time runs out!
"""

import random
import time

from ..game import Game
from ..character import Character, Archetype
from ..narrative import NarrativeSpine, ConflictType, TrueResolution, Revelation
from ..render import Location
from ..interaction import Hotspot, HotspotType


# ============================================================================
# ASCII ART GALLERY - Detailed visuals for the escape room
# ============================================================================

STUDY_ROOM_ART = [
    "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
    "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
    "@@@@@@@@@@0GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG0@@@@@@@@@@",
    "@@@@@@@@@@G:                                                         :G@@@@@@@@@@",
    "@@@@@@@@@@G:  ╔══════╗     ╔═══════════╗     ╔══════╗    ┌──────┐   :G@@@@@@@@@@",
    "@@@@@@@@@@G:  ║ BOOK ║     ║  LOCKED   ║     ║ BOOK ║    │░░░░░░│   :G@@@@@@@@@@",
    "@@@@@@@@@@G:  ║ CASE ║     ║   SAFE    ║     ║ CASE ║    │░░░░░░│   :G@@@@@@@@@@",
    "@@@@@@@@@@G:  ║══════║     ║  [????]   ║     ║══════║    │WINDOW│   :G@@@@@@@@@@",
    "@@@@@@@@@@G:  ║▓▓▓▓▓▓║     ╚═══════════╝     ║▓▓▓▓▓▓║    │░░░░░░│   :G@@@@@@@@@@",
    "@@@@@@@@@@G:  ╚══════╝                       ╚══════╝    └──────┘   :G@@@@@@@@@@",
    "@@@@@@@@@@G:                                                         :G@@@@@@@@@@",
    "@@@@@@@@@@G:      ┌─────────────────────────────────────┐           :G@@@@@@@@@@",
    "@@@@@@@@@@G:      │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│           :G@@@@@@@@@@",
    "@@@@@@@@@@G:      │░░░░░░░░░░░ ORNATE DESK ░░░░░░░░░░░░░│           :G@@@@@@@@@@",
    "@@@@@@@@@@G:      │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│           :G@@@@@@@@@@",
    "@@@@@@@@@@G:      └───────┬───────────────────┬─────────┘           :G@@@@@@@@@@",
    "@@@@@@@@@@G:              │                   │                      :G@@@@@@@@@@",
    "@@@@@@@@@@G:                                                         :G@@@@@@@@@@",
    "@@@@@@@@@@G:    ┌────┐                                 ┌────────┐   :G@@@@@@@@@@",
    "@@@@@@@@@@G:    │COAT│        ═══════════              │PAINTING│   :G@@@@@@@@@@",
    "@@@@@@@@@@G:    │RACK│        ║  CHAIR  ║              │ FRAME  │   :G@@@@@@@@@@",
    "@@@@@@@@@@G:    │ || │        ═══════════              │ ????? │   :G@@@@@@@@@@",
    "@@@@@@@@@@G:    └────┘                                 └────────┘   :G@@@@@@@@@@",
    "@@@@@@@@@@G:                                                         :G@@@@@@@@@@",
    "@@@@@@@@@@G:  ╔════════════════════════════════════════════════╗    :G@@@@@@@@@@",
    "@@@@@@@@@@G:  ║░░░░░░░░░░░░░░░░░ LOCKED DOOR ░░░░░░░░░░░░░░░░░░║    :G@@@@@@@@@@",
    "@@@@@@@@@@G:  ╚════════════════════════════════════════════════╝    :G@@@@@@@@@@",
    "@@@@@@@@@@GLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLG@@@@@@@@@@",
    "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
    "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
]

MYSTERIOUS_PORTRAIT_ART = """
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@0GG00GGGGCCCCCCCCCCCCCCCCCGGGGGGG0@@@@@@
@@@@@@@@@@L;1ttttt1;;;:,,,,,,,,:;iiiiiiiii;1@@@@@@
@@@@@@@@@@Litffffftii;::::::::;iiiiiiiiiiit@@@@@@
@@@@@@@@@@Li1fffff1ii;::::::::;ii;;;;ii1t1f@@@@@@
@@@@@@@@@@Li1ttfff1ii;::::::::;i;;;ii11111t@@@@@@
@@@@@@@@@@Li1ttttf1;i;::::::::;i;;i11i11111t@@@@@@
@@@@@@@@@@Li1ttttf1;i;:::,,:::;iiii1iii11111f@@@@@@
@@@@@@@@@@Litftttt1;i;::,::::;11iii111t1iiiiit@@@@@@
@@@@@@@@@@Litftttf1;i;:,:::::,;iiiiiiii1111it@@@@@@
@@@@@@@@@@L;tttttf1;;:,,,....,;iiii;iii11ti1@@@@@@
@@@@@@@@@@L;tttttf1i;,,..,;i;;iiii;;iii11t@@@@@@
@@@@@@@@@@Litttttf1;,....;iii1111;1111ii;iiit@@@@@@
@@@@@@@@@@L;tttttft:....,iii11tttt1111ii;iiit@@@@@@
@@@@@@@@@@L;tttttft,...,;iiittttt111111iii1@@@@@@
@@@@@@@@@@L;1ttttft...,:;iiii111111111iiii;it@@@@@@
@@@@@@@@@@L;tttttf;...,:;;iii1ttttttiiii;;it@@@@@@
@@@@@@@@@@f;tttttf:...,:;;;;i11t111iiiii;;:it@@@@@@
@@@@@@@@@@f;tttttf;..,,:;;;;i1ttffftt1iiii;it@@@@@@
@@@@@@@@@@f;tttttf1..,,;;;;i111111111iii1ii;it@@@@@@
@@@@@@@@@@f;tttttf;..,:;;i;:,,:;itLt1;:,,,:iif@@@@@@
@@@@@@@@@@f;tttttf1...:i;,,.,;iii1111iii;;i1if@@@@@@
@@@@@@@@@@f;tttttf1;:,:i;,:;;::::;i1ti;::;iiif@@@@@@
@@@@@@@@@@f;tttttti;:,:i;::;;:,,,;tf1;:;i111if@@@@@@
@@@@@@@@@@f;tttttfi:,,,;i;;:,.:i;itft1i1i;iif@@@@@@
@@@@@@@@@@f;tttttti;;,.:ii;;;;;;;itt111111if@@@@@@
@@@@@@@@@@f;tttttti;;:,,iiiiiiii;t1ii11tft1if@@@@@@
@@@@@@@@@@f;t1tttti;;:,.;iii1111iftii1111ttL@@@@@@
@@@@@@@@@@f;tttttti;;:,.:;;ii111tft111ii11tL@@@@@@
@@@@@@@@@@f;tttttti;;:,,;;iiii;i11i;ii11i;:f@@@@@@
@@@@@@@@@@f;t111tti:;:,..;;;;;;;;::;itft1if@@@@@@
@@@@@@@@@@f;t1111ti:;:,,.:;;;;;;i;:;i11t1if@@@@@@
@@@@@@@@@@f;t1111ti:;::,,;;;;;;;;:,:i1111if@@@@@@
@@@@@@@@@@t;t1111t;:;:,,,,:;iiii;::,;i111if@@@@@@
@@@@@@@@@@t;t11111;:;:,,,,,;i;ii1;,:1t111it@@@@@@
@@@@@@@@@@t;111111;:;:,,,,,,;;;;i;,:1111iit@@@@@@
@@@@@@@@@@t;t11111;:;::,,,,:;;;;:,;11iiit@@@@@@
@@@@@@@@@@t;111111;:::::::::,:;;:;ii:;iiit@@@@@@
@@@@@@@@@@t;111111;:::::::::,,::;;;;;iiitf@@@@@@
@@@@@@@@@@t;111111;::::::::::,.,,;;;;ii;:@@@@@@
@@@@@@@@@@t;111111;:::;::;:::,,..,,:;;:,,@@@@@@
@@@@@@@@@@t;111111;:::::::,,,,,....,,,...@@@@@@
@@@@@@@@@@fi111111;:::::::,,,,,;;......,@@@@@@
@@@@@@@@@@f11111111i;;::,,,:,,;1:......,@@@@@@
@@@@@@@@@@fiiii11tffti;1ft;:::;,.......,@@@@@@
@@@@@@@@@@Ltt1iiii11ii;fGLi;:::,.......,@@@@@@
@@@@@@@@@@Lttttiiii1Ltifft11;;;:.......,@@@@@@
@@@@@@@@@@ti111i111t1ii1ii1t;::;:...,..@@@@@@
@@@@@@@@@@fiiii1tfti:::::::::,::,...;;:@@@@@@
@@@@@@@@@@tiii;;i1i:,.........,,.. ,:;;@@@@@@
@@@@@@@@@@LfLftttt111111111111t111iitftG@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"""

SAFE_CLOSE_UP_ART = """
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║    ╔═══════════════════════════════════════════╗     ║
║    ║                                           ║     ║
║    ║      ┌─────────────────────────┐         ║     ║
║    ║      │   COMBINATION SAFE      │         ║     ║
║    ║      │                         │         ║     ║
║    ║      │    ┌───┐ ┌───┐ ┌───┐   │         ║     ║
║    ║      │    │ ? │ │ ? │ │ ? │   │         ║     ║
║    ║      │    └───┘ └───┘ └───┘   │         ║     ║
║    ║      │                         │         ║     ║
║    ║      │    [ENTER CODE]         │         ║     ║
║    ║      │                         │         ║     ║
║    ║      └─────────────────────────┘         ║     ║
║    ║                                           ║     ║
║    ╚═══════════════════════════════════════════╝     ║
║                                                       ║
║        A heavy steel safe. The dial shows             ║
║        it needs a 3-digit code to open.               ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝"""

BOOKCASE_LEFT_ART = """
╔═════════════════════════════════════════╗
║          ANTIQUE BOOKCASE               ║
╠═════════════════════════════════════════╣
║ ┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐   ║
║ │░░░░░││▓▓▓▓▓││░░░░░││▓▓▓▓▓││░░░░░│   ║
║ │DANTE││HOMER││SHAKE││POETS││MYTHS│   ║
║ └─────┘└─────┘└─────┘└─────┘└─────┘   ║
╠═════════════════════════════════════════╣
║ ┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐   ║
║ │▓▓▓▓▓││░░░░░││▓▓▓▓▓││░░░░░││▓▓▓▓▓│   ║
║ │ATLAS││?????││BIBLE││GUILD││STARS│   ║
║ └─────┘└─────┘└─────┘└─────┘└─────┘   ║
╠═════════════════════════════════════════╣
║                                         ║
║   One book appears slightly loose...    ║
║   Title reads: "SECRETS OF THE AGES"    ║
║                                         ║
╚═════════════════════════════════════════╝"""

DESK_CLOSE_UP_ART = """
╔═══════════════════════════════════════════════════════════════════╗
║                         ORNATE MAHOGANY DESK                       ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                     ║
║    ┌──────────┐    ┌────────────────┐    ┌──────────┐             ║
║    │ INKWELL  │    │    JOURNAL     │    │  CANDLE  │             ║
║    │    ◯     │    │ ░░░░░░░░░░░░░░ │    │    ╥     │             ║
║    └──────────┘    │ ░░░░░░░░░░░░░░ │    │   ═╩═    │             ║
║                    │ ░░░░░░░░░░░░░░ │    └──────────┘             ║
║                    └────────────────┘                              ║
║                                                                     ║
║    ┌─────────────────────────────────────────────────────────┐    ║
║    │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│    ║
║    │          D R A W E R   (locked)                         │    ║
║    │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│    ║
║    └─────────────────────────────────────────────────────────┘    ║
║                                                                     ║
║    A brass nameplate reads: "Prof. Edmund Blackwood"               ║
║                                                                     ║
╚═══════════════════════════════════════════════════════════════════╝"""

WINDOW_ART = """
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║      ┌─────────────────────────────────────┐         ║
║      │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│         ║
║      │░░░╔══╗░░░░░░░░░╔══╗░░░░░░░░░░░░░░░░│         ║
║      │░░░║  ║░░░░░░░░░║  ║░░░░░░░░░░░░░░░░│         ║
║      │░░░╚══╝░░░░░░░░░╚══╝░░░░░░░░░░░░░░░░│         ║
║      │░░░░░░░░░░░░NIGHT SKY░░░░░░░░░░░░░░░│         ║
║      │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│         ║
║      │░░░░░░░MOONLIGHT░░░░░░░░░░░░░░░░░░░░│         ║
║      │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│         ║
║      └─────────────────────────────────────┘         ║
║                                                       ║
║      The window is barred from outside.              ║
║      Through it, you see only darkness               ║
║      and the faint glow of distant stars.            ║
║                                                       ║
║      Wait... is that a number scratched              ║
║      into the windowsill? "7"                        ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝"""

PAINTING_ART = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                    ║
║    ╔══════════════════════════════════════════════════════════╗   ║
║    ║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║   ║
║    ║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║   ║
║    ║░░░░░░░░░░░░░░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░║   ║
║    ║░░░░░░░░░░░░░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░║   ║
║    ║░░░░░░░░░░░░░▓▓▓░░░░░░░░░░░░░░░░▓▓▓▓░░░░░░░░░░░░░░░░░░░░░║   ║
║    ║░░░░░░░░░░░░░▓▓░░░○░░░░░░░░○░░░░░▓▓▓░░░░░░░░░░░░░░░░░░░░░║   ║
║    ║░░░░░░░░░░░░░▓▓░░░░░░░░░░░░░░░░░░▓▓▓░░░░░░░░░░░░░░░░░░░░░║   ║
║    ║░░░░░░░░░░░░░▓▓░░░░░░╔══╗░░░░░░░░▓▓▓░░░░░░░░░░░░░░░░░░░░░║   ║
║    ║░░░░░░░░░░░░░▓▓░░░░░░║  ║░░░░░░░░▓▓▓░░░░░░░░░░░░░░░░░░░░░║   ║
║    ║░░░░░░░░░░░░░▓▓░░░░░░╚══╝░░░░░░░░▓▓▓░░░░░░░░░░░░░░░░░░░░░║   ║
║    ║░░░░░░░░░░░░░▓▓▓░░░░░░░░░░░░░░░░▓▓▓░░░░░░░░░░░░░░░░░░░░░░║   ║
║    ║░░░░░░░░░░░░░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░║   ║
║    ║░░░░░░░░░░░░░░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░║   ║
║    ║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║   ║
║    ╚══════════════════════════════════════════════════════════╝   ║
║                                                                    ║
║         A portrait of someone long forgotten.                      ║
║         The eyes seem to follow you...                             ║
║                                                                    ║
║         Something is written on the frame:                         ║
║         "The second number hides in plain sight - 4"               ║
║                                                                    ║
╚═══════════════════════════════════════════════════════════════════╝"""

COAT_RACK_ART = """
╔═══════════════════════════════════════════╗
║           COAT RACK                       ║
╠═══════════════════════════════════════════╣
║                                           ║
║              ┌───┐                        ║
║              │ ○ │                        ║
║           ───┴───┴───                     ║
║           /         \\                     ║
║          /           \\                    ║
║         │             │                   ║
║        ┌┴─────────────┴┐                  ║
║        │░░░░░░░░░░░░░░░│                  ║
║        │░░░ OLD COAT ░░│                  ║
║        │░░░░░░░░░░░░░░░│                  ║
║        │░░░░░░░░░░░░░░░│                  ║
║        │░░░░░░░░░░░░░░░│                  ║
║        │░░░░░░░░░░░░░░░│                  ║
║        └───────────────┘                  ║
║              ║                            ║
║              ║                            ║
║           ═══╩═══                         ║
║                                           ║
║    A dusty coat hangs here.               ║
║    Something jingles in the pocket...     ║
║                                           ║
╚═══════════════════════════════════════════╝"""

LOCKED_DOOR_ART = """
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@0GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG0@@@@@@@@
@@@@@@@@G                                              G@@@@@@@@
@@@@@@@@G     ╔══════════════════════════════════╗    G@@@@@@@@
@@@@@@@@G     ║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║    G@@@@@@@@
@@@@@@@@G     ║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║    G@@@@@@@@
@@@@@@@@G     ║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║    G@@@@@@@@
@@@@@@@@G     ║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║    G@@@@@@@@
@@@@@@@@G     ║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║    G@@@@@@@@
@@@@@@@@G     ║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║    G@@@@@@@@
@@@@@@@@G     ║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║ ○  G@@@@@@@@
@@@@@@@@G     ║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║    G@@@@@@@@
@@@@@@@@G     ║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║    G@@@@@@@@
@@@@@@@@G     ║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║    G@@@@@@@@
@@@@@@@@G     ║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║    G@@@@@@@@
@@@@@@@@G     ║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║    G@@@@@@@@
@@@@@@@@G     ║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║    G@@@@@@@@
@@@@@@@@G     ╚══════════════════════════════════╝    G@@@@@@@@
@@@@@@@@G                                              G@@@@@@@@
@@@@@@@@GLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLG@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

             THE HEAVY OAK DOOR IS LOCKED.

       A brass keyhole gleams in the dim light.
       You'll need to find the key to escape...
"""

JOURNAL_ART = """
╔═══════════════════════════════════════════════════════════════════╗
║                         LEATHER JOURNAL                            ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                     ║
║    ┌─────────────────────────────────────────────────────────┐    ║
║    │                                                         │    ║
║    │  "To whomever finds themselves trapped in my study,     │    ║
║    │                                                         │    ║
║    │   The code you seek is scattered across the room.       │    ║
║    │   Each number hides in a different place:               │    ║
║    │                                                         │    ║
║    │   - The first digit marks the window                    │    ║
║    │   - The second watches from the portrait                │    ║
║    │   - The third rests with forgotten things               │    ║
║    │                                                         │    ║
║    │   The safe holds what you need.                         │    ║
║    │   But remember - things are not always as they seem.    │    ║
║    │                                                         │    ║
║    │                              - E.B."                    │    ║
║    │                                                         │    ║
║    └─────────────────────────────────────────────────────────┘    ║
║                                                                     ║
║    The pages are yellowed with age. This journal holds              ║
║    the secret to escaping this room...                              ║
║                                                                     ║
╚═══════════════════════════════════════════════════════════════════╝"""

SECRET_BOOK_ART = """
╔═══════════════════════════════════════════════════════════════════╗
║              "SECRETS OF THE AGES" - HOLLOW BOOK                   ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                     ║
║         ┌─────────────────────────────────────────┐                ║
║         │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│                ║
║         │░░░┌─────────────────────────────┐░░░░░│                ║
║         │░░░│                             │░░░░░│                ║
║         │░░░│     ╔═══════════════╗      │░░░░░│                ║
║         │░░░│     ║               ║      │░░░░░│                ║
║         │░░░│     ║   BRASS KEY   ║      │░░░░░│                ║
║         │░░░│     ║    ╔═══╗      ║      │░░░░░│                ║
║         │░░░│     ║    ║   ║░░░   ║      │░░░░░│                ║
║         │░░░│     ║    ╚═══╝      ║      │░░░░░│                ║
║         │░░░│     ║               ║      │░░░░░│                ║
║         │░░░│     ╚═══════════════╝      │░░░░░│                ║
║         │░░░│                             │░░░░░│                ║
║         │░░░└─────────────────────────────┘░░░░░│                ║
║         │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│                ║
║         └─────────────────────────────────────────┘                ║
║                                                                     ║
║    The book is hollow inside! A brass key rests in                 ║
║    the carved compartment. This must be the drawer key!            ║
║                                                                     ║
╚═══════════════════════════════════════════════════════════════════╝"""

KEY_FOUND_ART = """
╔═══════════════════════════════════════════════════════════════════╗
║                        ESCAPE KEY FOUND!                           ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                     ║
║                                                                     ║
║                     ╔═══════════════════╗                          ║
║                     ║                   ║                          ║
║                     ║    ┌─────────┐    ║                          ║
║                     ║    │ ╔═════╗ │    ║                          ║
║                     ║    │ ║     ║ │    ║                          ║
║                     ║    │ ║     ╠═╧══════════╗                    ║
║                     ║    │ ║     ║░░░░░░░░░░░░║                    ║
║                     ║    │ ║     ╠═╤══════════╝                    ║
║                     ║    │ ║     ║ │    ║                          ║
║                     ║    │ ╚═════╝ │    ║                          ║
║                     ║    └─────────┘    ║                          ║
║                     ║                   ║                          ║
║                     ╚═══════════════════╝                          ║
║                                                                     ║
║                    THE KEY TO THE DOOR!                            ║
║                                                                     ║
║          You've found the ornate brass key that                    ║
║          unlocks the study door. FREEDOM AWAITS!                   ║
║                                                                     ║
╚═══════════════════════════════════════════════════════════════════╝"""

ESCAPE_SUCCESS_ART = """
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG@@@@@@@@@@
@@@@@@@@@@G                                                           G@@@@@@@@@@
@@@@@@@@@@G    ╔═══════════════════════════════════════════════╗     G@@@@@@@@@@
@@@@@@@@@@G    ║                                               ║     G@@@@@@@@@@
@@@@@@@@@@G    ║    ██╗   ██╗ ██████╗ ██╗   ██╗                ║     G@@@@@@@@@@
@@@@@@@@@@G    ║    ╚██╗ ██╔╝██╔═══██╗██║   ██║                ║     G@@@@@@@@@@
@@@@@@@@@@G    ║     ╚████╔╝ ██║   ██║██║   ██║                ║     G@@@@@@@@@@
@@@@@@@@@@G    ║      ╚██╔╝  ██║   ██║██║   ██║                ║     G@@@@@@@@@@
@@@@@@@@@@G    ║       ██║   ╚██████╔╝╚██████╔╝                ║     G@@@@@@@@@@
@@@@@@@@@@G    ║       ╚═╝    ╚═════╝  ╚═════╝                 ║     G@@@@@@@@@@
@@@@@@@@@@G    ║                                               ║     G@@@@@@@@@@
@@@@@@@@@@G    ║   ███████╗███████╗ ██████╗ █████╗ ██████╗ ███████╗  ║     G@@@@@@@@@@
@@@@@@@@@@G    ║   ██╔════╝██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝  ║     G@@@@@@@@@@
@@@@@@@@@@G    ║   █████╗  ███████╗██║     ███████║██████╔╝█████╗    ║     G@@@@@@@@@@
@@@@@@@@@@G    ║   ██╔══╝  ╚════██║██║     ██╔══██║██╔═══╝ ██╔══╝    ║     G@@@@@@@@@@
@@@@@@@@@@G    ║   ███████╗███████║╚██████╗██║  ██║██║     ███████╗  ║     G@@@@@@@@@@
@@@@@@@@@@G    ║   ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝     ╚══════╝  ║     G@@@@@@@@@@
@@@@@@@@@@G    ║                                               ║     G@@@@@@@@@@
@@@@@@@@@@G    ╚═══════════════════════════════════════════════╝     G@@@@@@@@@@
@@@@@@@@@@G                                                           G@@@@@@@@@@
@@@@@@@@@@G           You unlocked the door and escaped!              G@@@@@@@@@@
@@@@@@@@@@G              Congratulations, detective!                  G@@@@@@@@@@
@@@@@@@@@@G                                                           G@@@@@@@@@@
@@@@@@@@@@GLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLG@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"""


def create_study_escape(seed: int = None) -> Game:
    """
    Create the Study Room Escape scenario.

    A puzzle-based escape room with:
    - 1 main location (the locked study)
    - Multiple puzzles to solve
    - Clues scattered around the room
    - A 3-digit safe code to discover
    - Keys to find and doors to unlock
    """
    game = Game()
    game.new_game(seed=seed)

    # Randomize the safe code for replayability
    if seed:
        random.seed(seed)
    code_digits = [
        random.randint(1, 9),
        random.randint(1, 9),
        random.randint(1, 9)
    ]
    safe_code = f"{code_digits[0]}{code_digits[1]}{code_digits[2]}"

    # Create narrative spine for escape room
    spine = NarrativeSpine(
        conflict_type=ConflictType.THEFT,  # Using THEFT as closest match
        conflict_description=f"You're trapped in a mysterious study. Find the clues, crack the safe code ({safe_code}), and escape!",
        true_resolution=TrueResolution(
            culprit_id="puzzle",
            motive="escape the room",
            method="solve puzzles and find the key",
            opportunity="explore everything",
            evidence_chain=["find_journal", "find_code_1", "find_code_2", "find_code_3", "open_safe", "get_key", "escape"]
        ),
        revelations=[
            Revelation(
                id="find_journal",
                description="The journal reveals the puzzle structure",
                importance=1,
                source="Examine the desk"
            ),
            Revelation(
                id="find_code_1",
                description=f"First digit of safe code: {code_digits[0]}",
                importance=2,
                prerequisites=["find_journal"],
                source="Examine the window"
            ),
            Revelation(
                id="find_code_2",
                description=f"Second digit of safe code: {code_digits[1]}",
                importance=2,
                prerequisites=["find_journal"],
                source="Examine the painting"
            ),
            Revelation(
                id="find_code_3",
                description=f"Third digit of safe code: {code_digits[2]}",
                importance=2,
                prerequisites=["find_journal"],
                source="Search the coat"
            ),
            Revelation(
                id="open_safe",
                description="Safe opened - brass key found!",
                importance=3,
                prerequisites=["find_code_1", "find_code_2", "find_code_3"],
                source="Enter the correct code"
            ),
            Revelation(
                id="get_drawer_key",
                description="Found drawer key in hollow book",
                importance=2,
                source="Examine the bookcase"
            ),
            Revelation(
                id="escape",
                description="Door unlocked - FREEDOM!",
                importance=3,
                prerequisites=["open_safe"],
                source="Use the key on the door"
            )
        ],
        twist_probability=0.0
    )
    game.set_spine(spine)

    # Store the safe code in game state for verification
    game.safe_code = safe_code
    game.code_digits = code_digits

    # Create the study location with full ASCII art
    study = Location(
        id="study",
        name="The Locked Study",
        description="You wake up in a wood-paneled study. The heavy oak door is locked tight. You must find a way to escape!",
        art=STUDY_ROOM_ART,
        is_outdoor=False,
        ambient_description="Dust motes dance in the moonlight filtering through barred windows. The room holds many secrets..."
    )

    # Add all interactive hotspots

    # The locked safe - main puzzle
    study.add_hotspot(Hotspot(
        id="hs_safe",
        label="Locked Safe",
        hotspot_type=HotspotType.CONTAINER,
        position=(35, 7),
        description="A heavy steel safe mounted on the wall.",
        examine_text=SAFE_CLOSE_UP_ART + f"\n\nThe safe requires a 3-digit code. You'll need to search the room for clues."
    ))

    # Left bookcase
    study.add_hotspot(Hotspot(
        id="hs_bookcase_left",
        label="Left Bookcase",
        hotspot_type=HotspotType.CONTAINER,
        position=(8, 6),
        description="An antique bookcase filled with dusty tomes.",
        examine_text=BOOKCASE_LEFT_ART + "\n\nYou pull the loose book... It's hollow inside!\n" + SECRET_BOOK_ART,
        reveals_fact="get_drawer_key"
    ))

    # Right bookcase
    study.add_hotspot(Hotspot(
        id="hs_bookcase_right",
        label="Right Bookcase",
        hotspot_type=HotspotType.OBJECT,
        position=(50, 6),
        description="Another bookcase, these books seem ordinary.",
        examine_text="Rows of leather-bound books on history and philosophy. Nothing unusual here."
    ))

    # The desk with journal
    study.add_hotspot(Hotspot(
        id="hs_desk",
        label="Ornate Desk",
        hotspot_type=HotspotType.OBJECT,
        position=(35, 14),
        description="A large mahogany desk dominates the center of the room.",
        examine_text=DESK_CLOSE_UP_ART + "\n\nYou open the journal and read...\n" + JOURNAL_ART,
        reveals_fact="find_journal"
    ))

    # Window with first clue
    study.add_hotspot(Hotspot(
        id="hs_window",
        label="Barred Window",
        hotspot_type=HotspotType.OBJECT,
        position=(62, 8),
        description="A window looking out into darkness.",
        examine_text=WINDOW_ART.replace('"7"', f'"{code_digits[0]}"'),
        reveals_fact="find_code_1",
        requires_discovery="find_journal"
    ))

    # Painting with second clue
    study.add_hotspot(Hotspot(
        id="hs_painting",
        label="Mysterious Painting",
        hotspot_type=HotspotType.EVIDENCE,
        position=(62, 21),
        description="A dusty portrait in an ornate frame.",
        examine_text=PAINTING_ART.replace('"The second number hides in plain sight - 4"',
                                         f'"The second number hides in plain sight - {code_digits[1]}"') +
                     "\n\n" + MYSTERIOUS_PORTRAIT_ART,
        reveals_fact="find_code_2",
        requires_discovery="find_journal"
    ))

    # Coat rack with third clue
    study.add_hotspot(Hotspot(
        id="hs_coat_rack",
        label="Coat Rack",
        hotspot_type=HotspotType.OBJECT,
        position=(8, 20),
        description="An old coat hangs on this rack.",
        examine_text=COAT_RACK_ART + f"\n\nYou search the coat pocket and find a crumpled note: '{code_digits[2]}'",
        reveals_fact="find_code_3",
        requires_discovery="find_journal"
    ))

    # Chair
    study.add_hotspot(Hotspot(
        id="hs_chair",
        label="Leather Chair",
        hotspot_type=HotspotType.OBJECT,
        position=(35, 21),
        description="A comfortable-looking leather chair.",
        examine_text="A worn leather chair. Someone spent many hours here. Nothing hidden underneath."
    ))

    # The locked door - exit
    study.add_hotspot(Hotspot(
        id="hs_door",
        label="Locked Door",
        hotspot_type=HotspotType.EXIT,
        position=(35, 26),
        description="The heavy oak door. Your only way out.",
        examine_text=LOCKED_DOOR_ART,
        requires_discovery="open_safe"  # Can only use after getting key from safe
    ))

    game.add_location(study)
    game.set_start_location("study")

    return game


def run_study_escape():
    """Run the Study Room Escape scenario."""
    # Generate random seed for unique gameplay each time
    seed = int(time.time() * 1000) % (2**31)
    random.seed(seed)

    print()
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    print("@@@@@@@@@@GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG@@@@@@@@@@@@")
    print("@@@@@@@@@@G                                             G@@@@@@@@@@@@")
    print("@@@@@@@@@@G    ╔═══════════════════════════════════╗   G@@@@@@@@@@@@")
    print("@@@@@@@@@@G    ║    STUDY ROOM ESCAPE              ║   G@@@@@@@@@@@@")
    print("@@@@@@@@@@G    ║                                   ║   G@@@@@@@@@@@@")
    print("@@@@@@@@@@G    ║    You wake in a locked study.    ║   G@@@@@@@@@@@@")
    print("@@@@@@@@@@G    ║    Find the clues. Crack the      ║   G@@@@@@@@@@@@")
    print("@@@@@@@@@@G    ║    code. ESCAPE!                  ║   G@@@@@@@@@@@@")
    print("@@@@@@@@@@G    ║                                   ║   G@@@@@@@@@@@@")
    print("@@@@@@@@@@G    ╚═══════════════════════════════════╝   G@@@@@@@@@@@@")
    print("@@@@@@@@@@G                                             G@@@@@@@@@@@@")
    print("@@@@@@@@@@GLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLG@@@@@@@@@@@@")
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    print()
    print("=" * 70)
    print(f"[Game Seed: {seed}]")
    print("=" * 70)
    print()
    print("Commands: examine [number/name], look, inventory, help")
    print("          use [item] on [object], open [container]")
    print()
    input("Press Enter to begin your escape...")

    game = create_study_escape(seed=seed)
    game.run()


if __name__ == "__main__":
    run_study_escape()
