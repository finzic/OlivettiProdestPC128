/* ol_music.c - NOTE helpers */
#include <olivetti.h>

void ol_sound_setup(ol_byte tempo, ol_byte timbre)
{
    OL_POKEW(OL_TEMPO, tempo);
    OL_POKE(OL_TIMBRE, timbre);
}

void ol_play_note(ol_byte note, ol_byte octave, ol_byte duration)
{
    static const ol_byte octaves[5] = { 16, 8, 4, 2, 1 };
    if (octave < 1)
        octave = 1;
    if (octave > 5)
        octave = 5;
    OL_POKEW(OL_OCTAVE, octaves[octave - 1]);
    OL_POKEW(OL_DUREE, duration);
    if (OL_PEEKW(OL_TEMPO) == 0)
        OL_POKEW(OL_TEMPO, 5);
    ol_note(note);
}
