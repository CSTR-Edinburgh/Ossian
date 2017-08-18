

'''
[dyatlov]owatts: python scripts/util/make_corpus_with_clickable_audio.py ./train/sw/speakers/pm_balanced/naive_01_nn/utt/ ./train/sw/speakers/pm_balanced/naive_01_nn/clickable_audio



[dyatlov]owatts:
[dyatlov]owatts: pwd
/afs/inf.ed.ac.uk/user/o/owatts/sim2/oliver/ossian_test/Ossian2
[dyatlov]owatts: python scripts/util/make_corpus_with_clickable_audio.py ./train/sw/speakers/pm_balanced/naive_01_nn/utt/ ./train/sw/speakers/pm_balanced/naive_01_nn/clickable_audio

'''
import os
import sys
import glob
from lxml import etree
import multiprocessing

uttdir = sys.argv[1]
outdir = sys.argv[2]


outdir = os.path.abspath(outdir)


assert not os.path.isdir(outdir), '%s already exists'%(outdir)

audiodir = os.path.join(outdir, 'audio')
os.makedirs(outdir)
os.makedirs(audiodir)



max_cores = '30'


html_lines = []






# Using all available CPU cores unless defined otherwise
if max_cores is not None and max_cores.isdigit():
    n_cores = int(max_cores)
else:
    n_cores = multiprocessing.cpu_count()



def proc_utt(uttfile):

    path, base = os.path.split(uttfile)
    base = base.replace('.utt', '')
    print base
    utt = etree.parse(uttfile)
    wavfile = utt.getroot().attrib['waveform']
    i = 1
    html_line = ''
    os.makedirs(audiodir + '/clickable_%s/'%(base))
    for token in utt.xpath('//token'):
        text = token.attrib['text']
        if 'start' in token.attrib:

            

            start_sec =  float(token.attrib['start']) / 1000.0
            end_sec = float(token.attrib['end']) / 1000.0
            dur_sec = end_sec - start_sec



            ## chop wav extract:
            outwave = audiodir + '/clickable_%s/clickable_%s_%s.ogg'%(base, base, i)
            comm = 'sox %s %s trim %s %s'%(wavfile, outwave, start_sec, dur_sec)
            os.system(comm)
            #print comm

            #html_line += '<audio>%s<source src="%s" type="audio/wav"></audio>'%(text, outwave)
            #html_line += '<a href="%s">%s</a>'%(outwave, text)
            html_line += '<a href="%s" onclick="playItHere(event, this)">%s</a>'%(outwave, text)



            #html_line += '<audio src="%s" hidden> Sorry, your browser does not support the <audio> element. </audio>'%(outwave)

            #html_line += '<a href="#">%s</a>'%(text)
            #html_line += '<audio hidden><source src="%s" type="audio/wav">If you are reading this, audio is not supported. </audio>'%(outwave)
            i += 1
        else:
            html_line += text

    if html_line != '':
        html_line = '<p> %s: %s <p>\n'%(base, html_line)
    return (base, html_line)


uttlist = sorted(glob.glob(uttdir + '/*.utt')) # [:10]

if n_cores == 1:
    for uttfile in uttlist:
        html_lines.append(proc_utt(uttfile))
else:
    pool = multiprocessing.Manager().Pool(n_cores) 
    html_lines = pool.map(proc_utt, uttlist)

                              




html_lines.sort()
html_lines = [line for (base, line) in html_lines]

f = open(outdir + '/text.html', 'w')

f.write('''
<script>
function playItHere(e, link) {
  var audio = document.createElement("audio");
  var src = document.createElement("source");
  src.src = link.href;
  audio.appendChild(src);
  audio.play();
  e.preventDefault();
}
</script>
\n\n\n\n''' )

for html_line in html_lines:
        f.write(html_line)
f.close()


print 
print 
print 'Please view ' + outdir + '/text.html in chrome -- safari does not support a script it uses'
print 
print 