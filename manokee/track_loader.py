from amio import AudioClip
import os
import soundfile as sf


def track_loader(filename):
    """
    Function that returns a generator that performs loading of the track audio
    data from disk in chunks and report progress, so that application operation
    is not blocked by the loading.
    """
    if os.path.getsize(filename) == 0:
        return None, None

    f = sf.SoundFile(filename)
    audio_clip = AudioClip.zeros(f.frames, f.channels, f.samplerate)
    audio_clip.writeable = True

    def generator():
        read_so_far = 0
        blocksize = 30 * f.samplerate  # load in 30-second chunks
        for block in f.blocks(blocksize=blocksize):
            audio_clip.overwrite(AudioClip(block, f.samplerate), read_so_far)
            read_so_far += blocksize
            yield 100 * read_so_far / f.frames
        audio_clip.writeable = False
        f.close()

    return audio_clip, generator()
