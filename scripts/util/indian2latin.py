# -*- coding: utf-8 -*-
import unicodedata
import codecs
import sys
import re
#
# simple conversion of  indic scripts to latin alphabetic form
# implements vowel drop and change,
#
# usage: python indian2latin.py <utf-8 text file> 
# antti.suni@helsinki.fi
#


# additional thoughts:
# Handle all unicode normalized? 
# Then é, ä and ö would contain two unicode chars,
# letter and modifier. Modifier could then be assigned as a contextual features or combined to form new safetext modelnames
# of the letter. Modifiers have their own unicode categories Mc and Mn, both always modify the preceding letter.
#
# Then Indian languages could be handled without exception rules, since
# vowel signs and such are similar modifiers to the preceding syllable characters
#  i.e.
# LATIN SMALL LETTER A + COMBINING DIAERESIS => LATIN SMALL LETTER A WITH DIAERESIS
# TAMIL LETTER KA + TAMIL VOWEL SIGN EE => TAMIL LETTER KA WITH VOWEL SIGN EE
#
# Still a problem of having many phonemes for one model though, and unless contextual features ares used
#  for modifiers, the vowel identity can not be directly targeted in decision tree questions

# below is my rule-based alpha-syllabic to alphabetic conversion where virama deletes the default vowel and
# vowel sign replaces the default vowel #, also anusvara adds n_feature to the name


## osw: added some lines for handling CANDRABINDU and assamese 'WITH LOWER DIAGONAL' etc.
##      Rearranged code to allow other scripts to call the main function latinise_indian_script_string


def latinise_indian_script_string(l):
    prev_letter = ""
    letters = []
    for i in range(0,len(l)):
        try:
            u_name = unicodedata.name(l[i])
        except:
            continue

        # for latin letters do nothing
        if re.match('.*LATIN.*',u_name):
            if prev_letter:
                letters.append(prev_letter)
            letters.append(l[i])
            continue

        u_name = re.sub(' WITH .+', '', u_name)  ## e.g. for assamese 'WITH LOWER DIAGONAL' etc.

        # syllable and independent vowel characters 
        # skip CANDRA, VOCALIC and such for simplicity
        m = re.match('.*LETTER( .+)? (.+)$', u_name)
        if m:
            letter = m.group(2)
            if prev_letter:
                letters.append(prev_letter)
            # unfortunately syllables and independent vowels are not separated in unicode
            # syllable here: = any sequence ending in A except AA,  (IA,OA if found, will be split)
            if letter != "AA" and re.match(".+A$",  letter):
                prev_letter = ""+letter[:-1]+" "+letter[-1]   # osw: space -> ~
            # vowel
            else:
                prev_letter = ""+letter
            continue
        

        # modifiers:

        # change defaut vowel
        m = re.match('.*VOWEL SIGN( .+)? (.+)$', u_name)
        if m:
            prev_letter = prev_letter[:-1]
            prev_letter+=m.group(2)
            continue

        # remove vowel
        if re.match('.*VIRAMA', u_name):
            prev_letter= prev_letter[:-2]
            continue
       
        # nasalize something
        if re.match('.*ANUSVARA',u_name):
            prev_letter+="m"
            continue

        # nasalize something -- OSW added:  blizzard2014/data/speech/hi/txt/text_01241.txt
        if re.match('.*CANDRABINDU',u_name):  ## 'usually means that the previous vowel is nasalized.'
            prev_letter+="m"
            continue
            
        # else no conversion
        if prev_letter:
            letters.append(prev_letter)
            prev_letter = ""
        letters.append(l[i])

    letters.append(prev_letter)

    ## osw -- return list of single letters
    final_letters = []
    for letter in letters:
        if len(letter) == 1:
            final_letters.append(letter)
        else:
            final_letters.extend(letter.split(' '))
    return final_letters
   


def main_work():

    f = codecs.open(sys.argv[1], "r", encoding='utf-8')
    lines = f.readlines()
    f.close()


    for l in lines:
        letters = latinise_indian_script_string(l)
        print u" ".join(letters).encode('utf-8')
   

if __name__=="__main__":

    main_work()


