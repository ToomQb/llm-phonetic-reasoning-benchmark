from phonemizer.backend.espeak.wrapper import EspeakWrapper
EspeakWrapper.set_library('C:\Program Files\eSpeak NG\libespeak-ng.dll') # Download and install espeak-ng.msi backend from https://github.com/espeak-ng/espeak-ng/releases

from phonemizer import phonemize
from phonemizer.separator import Separator

from panphon.distance import Distance

text = ["Thym", "Papier", "pause", "pose", "peau"]

# phn is a list of phonemized sentences
phn = phonemize(
    text,
    language='fr-fr',
    backend='espeak',
    separator=Separator(phone=None, word=' ', syllable='|'),
    strip=True,
    preserve_punctuation=True)

print(phn)

dist = Distance()
for ipa1 in phn:
    print("-"*20)
    for ipa2 in phn:
        levenshtein_dist = dist.levenshtein_distance(ipa1, ipa2) # Nb de permutation à faire pour arriver au second mot
        feature_dist = dist.feature_edit_distance(ipa1, ipa2) # Distance des features entre les 2 phonemes
        
        print(ipa1, ipa2, levenshtein_dist, feature_dist)