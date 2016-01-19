#!/usr/local/bin/python3.5

import csv
import glob
import sys
import os
import re
import operator
import json
import argparse
import hashlib
import numpy
from datetime import datetime
#from colorpy.ciexyz import xyz_from_wavelength
#from colorpy.colormodels import irgb_string_from_xyz
from copy import deepcopy
from random import shuffle, seed
from collections import OrderedDict
from bokeh.io import hplot, vplot, gridplot, vform
from bokeh.plotting import Figure, show, save, reset_output
from bokeh.models import HoverTool, CustomJS, Slider, ColumnDataSource, HBox, VBox, VBoxForm
from bokeh.resources import CDN, INLINE
from bokeh.embed import file_html
from palettable import cubehelix

parser = argparse.ArgumentParser(description='Generate a catalog JSON file and plot HTML files from SNE data.')
parser.add_argument('--no-write-catalog', '-wc', dest='writecatalog', help='Don\'t write catalog file',    default=True, action='store_false')
parser.add_argument('--no-write-html', '-wh',    dest='writehtml',    help='Don\'t write html plot files', default=True, action='store_false')
parser.add_argument('--force-html', '-fh',       dest='forcehtml',    help='Force write html plot files',  default=False, action='store_true')
parser.add_argument('--event-list', '-el',       dest='eventlist',    help='Process a list of events',     default=[], type=str, nargs='+')
parser.add_argument('--test', '-t',              dest='test',         help='Test this script',             default=False, action='store_true')
args = parser.parse_args()

outdir = "../"

testsuffix = '.test' if args.test else ''

mycolors = cubehelix.perceptual_rainbow_16.hex_colors[:14]

columnkey = [
    "check",
    "name",
    "aliases",
    "discoverdate",
    "maxdate",
    "maxappmag",
    "maxabsmag",
    "host",
    "instruments",
    "redshift",
    "hvel",
    "lumdist",
    "claimedtype",
    "photolink",
    "spectralink",
    "download",
    "responsive"
]

header = [
    "",
    "Name",
    "Aliases",
    "Disc. Date",
    "Max Date",
    r"<em>m</em><sub>max</sub>",
    r"<em>M</em><sub>max</sub>",
    "Host Name",
    "Instruments/Bands",
    r"<em>z</em>",
    r"<em>v</em><sub>&#9737;</sub> (km/s)",
    r"<em>d</em><sub>L</sub> (Mpc)",
    "Claimed Type",
    "Phot.",
    "Spec.",
    "",
    ""
]

photokeys = [
    'timeunit',
    'time',
    'band',
    'instrument',
    'abmag',
    'aberr',
    'upperlimit',
    'source'
]

sourcekeys = [
    'name',
    'alias',
    'secondary'
]

with open('rep-folders.txt', 'r') as f:
    repfolders = f.read().splitlines()

repyears = [int(repfolders[x][-4:]) for x in range(len(repfolders))]

if len(columnkey) != len(header):
    print('Error: Header not same length as key list.')
    sys.exit(0)

dataavaillink = "<a href='https://bitbucket.org/Guillochon/sne'>Y</a>"

header = OrderedDict(list(zip(columnkey,header)))

bandcodes = [
    "u",
    "g",
    "r",
    "i",
    "z",
    "u'",
    "g'",
    "r'",
    "i'",
    "z'",
    "u_SDSS",
    "g_SDSS",
    "r_SDSS",
    "i_SDSS",
    "z_SDSS",
    "U",
    "B",
    "V",
    "R",
    "I",
    "G",
    "Y",
    "J",
    "H",
    "K",
    "C",
    "CR",
    "CV"
]

bandaliases = {
    "u_SDSS" : "u (SDSS)",
    "g_SDSS" : "g (SDSS)",
    "r_SDSS" : "r (SDSS)",
    "i_SDSS" : "i (SDSS)",
    "z_SDSS" : "z (SDSS)"
}

bandshortaliases = {
    "u_SDSS" : "u",
    "g_SDSS" : "g",
    "r_SDSS" : "r",
    "i_SDSS" : "i",
    "z_SDSS" : "z",
    "G" : ""
}

bandwavelengths = {
    "u" : 354.,
    "g" : 475.,
    "r" : 622.,
    "i" : 763.,
    "z" : 905.,
    "u'" : 354.,
    "g'" : 475.,
    "r'" : 622.,
    "i'" : 763.,
    "z'" : 905.,
    "u_SDSS" : 354.3,
    "g_SDSS" : 477.0,
    "r_SDSS" : 623.1,
    "i_SDSS" : 762.5,
    "z_SDSS" : 913.4,
    "U" : 365.,
    "B" : 445.,
    "V" : 551.,
    "R" : 658.,
    "I" : 806.,
    "Y" : 1020.,
    "J" : 1220.,
    "H" : 1630.,
    "K" : 2190.
}

wavedict = dict(list(zip(bandcodes,bandwavelengths)))

seed(101)
#bandcolors = ["#%06x" % round(float(x)/float(len(bandcodes))*0xFFFEFF) for x in range(len(bandcodes))]
bandcolors = cubehelix.cubehelix1_16.hex_colors[2:14] + cubehelix.cubehelix2_16.hex_colors[2:14] + cubehelix.cubehelix3_16.hex_colors[2:14]
shuffle(bandcolors)

def event_filename(name):
    return(name.replace('/', '_'))

# Replace bands with real colors, if possible.
#for b, code in enumerate(bandcodes):
#    if (code in bandwavelengths):
#        hexstr = irgb_string_from_xyz(xyz_from_wavelength(bandwavelengths[code]))
#        if (hexstr != "#000000"):
#            bandcolors[b] = hexstr

bandcolordict = dict(list(zip(bandcodes,bandcolors)))

coldict = dict(list(zip(list(range(len(columnkey))),columnkey)))

def bandcolorf(color):
    if (color in bandcolordict):
        return bandcolordict[color]
    return 'black'

def bandaliasf(code):
    if (code in bandaliases):
        return bandaliases[code]
    return code

def bandshortaliasf(code):
    if (code in bandshortaliases):
        return bandshortaliases[code]
    return code

def bandwavef(code):
    if (code in bandwavelengths):
        return bandwavelengths[code]
    return 0.

def utf8(x):
    return str(x, 'utf-8')

def get_rep_folder(entry):
    if 'discoveryear' not in entry:
        return repfolders[0]
    if not is_number(entry['discoveryear']):
        print ('Error, discovery year is not a number!')
        sys.exit()
    for r, repyear in enumerate(repyears):
        if int(entry['discoveryear']) <= repyear:
            return repfolders[r]
    return repfolders[0]

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def label_format(label):
    newlabel = label.replace('Angstrom', 'Å')
    newlabel = newlabel.replace('^2', '²')
    return newlabel

catalog = OrderedDict()
catalogcopy = OrderedDict()
snepages = []
sourcedict = dict()
nophoto = []
nospectra = []
totalphoto = 0
totalspectra = 0

files = []
for rep in repfolders:
    files += glob.glob('../' + rep + "/*.json")

md5s = []
md5 = hashlib.md5
if os.path.isfile(outdir + 'md5s.json'):
    with open(outdir + 'md5s.json', 'r') as f:
        filetext = f.read()
    oldmd5s = json.loads(filetext)
    oldmd5s = [list(i) for i in zip(*oldmd5s)]
    md5dict = dict(list(zip(oldmd5s[0], oldmd5s[1])))
else:
    md5dict = {}

for fcnt, eventfile in enumerate(sorted(files, key=lambda s: s.lower())):
    checksum = md5(open(eventfile, 'rb').read()).hexdigest()
    md5s.append([eventfile, checksum])
    filehead, ext = os.path.splitext(eventfile)

    if args.eventlist and os.path.splitext(os.path.basename(eventfile))[0] not in args.eventlist:
        continue

    f = open(eventfile, 'r')
    filetext = f.read()
    f.close()

    catalog.update(json.loads(filetext, object_pairs_hook=OrderedDict))
    entry = next(reversed(catalog))

    eventname = entry

    if args.eventlist and eventname not in args.eventlist:
        continue

    print(eventfile + ' [' + checksum + ']')

    repfolder = get_rep_folder(catalog[entry])
    catalog[entry]['download'] = "<a class='dci' href='https://cdn.rawgit.com/astrotransients/" + repfolder + "/master/" + eventname + ".json' download></a>"
    photoavail = 'photometry' in catalog[entry]
    catalog[entry]['numphoto'] = len(catalog[entry]['photometry']) if photoavail else 0
    if photoavail:
        plotlink = "sne/" + eventname + ".html"
        catalog[entry]['photoplot'] = plotlink
        plotlink = "<a class='lci' href='" + plotlink + "' target='_blank'></a> "
        catalog[entry]['photolink'] = plotlink + str(len(catalog[entry]['photometry']))
    spectraavail = 'spectra' in catalog[entry]
    catalog[entry]['numspectra'] = len(catalog[entry]['spectra']) if spectraavail else 0
    if spectraavail:
        plotlink = "sne/" + eventname + ".html"
        catalog[entry]['spectraplot'] = plotlink
        plotlink = "<a class='sci' href='" + plotlink + "' target='_blank'></a> "
        catalog[entry]['spectralink'] = plotlink + str(len(catalog[entry]['spectra']))
    
    prange = list(range(catalog[entry]['numphoto']))
    instrulist = sorted([_f for _f in list({catalog[entry]['photometry'][x]['instrument'] if 'instrument' in catalog[entry]['photometry'][x] else None for x in prange}) if _f])
    if len(instrulist) > 0:
        instruments = ''
        for i, instru in enumerate(instrulist):
            instruments += instru
            bandlist = sorted([_f for _f in list({bandshortaliasf(catalog[entry]['photometry'][x]['band'])
                if 'instrument' in catalog[entry]['photometry'][x] and catalog[entry]['photometry'][x]['instrument'] == instru else "" for x in prange}) if _f], key=lambda y: bandwavef(y))
            if bandlist:
                instruments += ' (' + ", ".join(bandlist) + ')'
            if i < len(instrulist) - 1:
                instruments += ', '

        catalog[entry]['instruments'] = instruments
    else:
        bandlist = sorted([_f for _f in list({bandshortaliasf(catalog[entry]['photometry'][x]['band']) for x in prange}) if _f], key=lambda y: bandwavef(y))
        if len(bandlist) > 0:
            catalog[entry]['instruments'] = ", ".join(bandlist)

    tools = "pan,wheel_zoom,box_zoom,save,crosshair,reset,resize"

    # Construct the date
    discoverdatestr = ''
    if 'discoveryear' in catalog[entry]:
        discoverdatestr += str(catalog[entry]['discoveryear'])
        if 'discovermonth' in catalog[entry]:
            discoverdatestr += '-' + str(catalog[entry]['discovermonth']).zfill(2)
            if 'discoverday' in catalog[entry]:
                discoverdatestr += '-' + str(catalog[entry]['discoverday']).zfill(2)
    catalog[entry]['discoverdate'] = discoverdatestr

    maxdatestr = ''
    if 'maxyear' in catalog[entry]:
        maxdatestr += str(catalog[entry]['maxyear'])
        if 'maxmonth' in catalog[entry]:
            maxdatestr += '-' + str(catalog[entry]['maxmonth']).zfill(2)
            if 'maxday' in catalog[entry]:
                maxdatestr += '-' + str(catalog[entry]['maxday']).zfill(2)

    catalog[entry]['maxdate'] = maxdatestr

    # Check file modification times before constructing .html files, which is expensive
    dohtml = True
    if not args.forcehtml:
        if (photoavail or spectraavail) and os.path.isfile(outdir + eventname + ".html"):
            if eventfile in md5dict and checksum == md5dict[eventfile]:
                dohtml = False

    if photoavail and dohtml and args.writehtml:
        phototime = [float(catalog[entry]['photometry'][x]['time']) for x in prange]
        photoAB = [float(catalog[entry]['photometry'][x]['abmag']) for x in prange]
        photoerrs = [float(catalog[entry]['photometry'][x]['aberr']) if 'aberr' in catalog[entry]['photometry'][x] else 0. for x in prange]
        photoband = [catalog[entry]['photometry'][x]['band'] for x in prange]
        photoinstru = [catalog[entry]['photometry'][x]['instrument'] if 'instrument' in catalog[entry]['photometry'][x] else '' for x in prange]
        photosource = [', '.join(str(j) for j in sorted(int(i) for i in catalog[entry]['photometry'][x]['source'].split(','))) for x in prange]
        phototype = [bool(catalog[entry]['photometry'][x]['upperlimit']) if 'upperlimit' in catalog[entry]['photometry'][x] else False for x in prange]

        x_buffer = 0.1*(max(phototime) - min(phototime)) if len(phototime) > 1 else 1.0
        x_range = [-x_buffer + min(phototime), x_buffer + max(phototime)]

        tt = [  
                ("Source ID", "@src"),
                ("Epoch (" + catalog[entry]['photometry'][0]['timeunit'] + ")", "@x{1.11}"),
                ("Magnitude", "@y{1.111}"),
                ("Error", "@err{1.111}"),
                ("Band", "@desc")
             ]
        if len(list(filter(None, photoinstru))):
            tt += [("Instrument", "@instr")]
        hover = HoverTool(tooltips = tt)

        p1 = Figure(title='Photometry for ' + eventname, x_axis_label='Time (' + catalog[entry]['photometry'][0]['timeunit'] + ')',
            y_axis_label='AB Magnitude', x_range = x_range, tools = tools, 
            y_range = (0.5 + max([x + y for x, y in list(zip(photoAB, photoerrs))]), -0.5 + min([x - y for x, y in list(zip(photoAB, photoerrs))])))
        p1.add_tools(hover)

        err_xs = []
        err_ys = []

        for x, y, yerr in list(zip(phototime, photoAB, photoerrs)):
            err_xs.append((x, x))
            err_ys.append((y - yerr, y + yerr))

        bandset = set(photoband)
        bandset = [i for (j, i) in sorted(list(zip(list(map(bandaliasf, bandset)), bandset)))]

        for band in bandset:
            bandname = bandaliasf(band)
            indb = [i for i, j in enumerate(photoband) if j == band]
            indt = [i for i, j in enumerate(phototype) if j == 0]
            ind = set(indb).intersection(indt)

            source = ColumnDataSource(
                data = dict(
                    x = [phototime[i] for i in ind],
                    y = [photoAB[i] for i in ind],
                    err = [photoerrs[i] for i in ind],
                    desc = [photoband[i] for i in ind],
                    instr = [photoinstru[i] for i in ind],
                    src = [photosource[i] for i in ind]
                )
            )
            p1.circle('x', 'y', source = source, color=bandcolorf(band), legend=bandname, size=4)
            p1.multi_line([err_xs[x] for x in ind], [err_ys[x] for x in ind], color=bandcolorf(band))

            upplimlegend = bandname if len(ind) == 0 else ''

            indt = [i for i, j in enumerate(phototype) if j == 1]
            ind = set(indb).intersection(indt)
            p1.inverted_triangle([phototime[x] for x in ind], [photoAB[x] for x in ind],
                color=bandcolorf(band), legend=upplimlegend, size=7)

    if spectraavail and dohtml and args.writehtml:
        spectrumwave = []
        spectrumflux = []
        spectrumerrs = []
        for spectrum in catalog[entry]['spectra']:
            specrange = range(len(spectrum['data']))
            spectrumwave.append([float(spectrum['data'][x][0]) for x in specrange])
            spectrumflux.append([float(spectrum['data'][x][1]) for x in specrange])
            if 'errorunit' in spectrum:
                spectrumerrs.append([float(spectrum['data'][x][2]) for x in specrange])
        nspec = len(catalog[entry]['spectra'])
        
        spectrumscaled = spectrumflux
        for f, flux in enumerate(spectrumflux):
            mean = numpy.std(flux)
            spectrumscaled[f] = [x/mean for x in flux]

        y_height = 0.
        y_offsets = [0. for x in range(nspec)]
        for i in reversed(range(nspec)):
            y_offsets[i] = y_height
            ydiff = max(spectrumscaled[i]) - min(spectrumscaled[i])
            spectrumscaled[i] = [j + y_height for j in spectrumscaled[i]]
            y_height += ydiff

        maxsw = max(map(max, spectrumwave))
        minsw = min(map(min, spectrumwave))
        maxfl = max(map(max, spectrumscaled))
        minfl = min(map(min, spectrumscaled))
        maxfldiff = max(map(operator.sub, list(map(max, spectrumscaled)), list(map(min, spectrumscaled))))
        x_buffer = 0.0 #0.1*(maxsw - minsw)
        x_range = [-x_buffer + minsw, x_buffer + maxsw]
        y_buffer = 0.1*maxfldiff
        y_range = [-y_buffer + minfl, y_buffer + maxfl]

        for f, flux in enumerate(spectrumscaled):
            spectrumscaled[f] = [x - y_offsets[f] for x in flux]

        tt2 = [  
                ("λ", "@x{1.1}"),
                ("Flux", "@yorig @fluxunit")
              ]
        if 'timeunit' in spectrum and 'time' in spectrum:
            tt2 += [ ("Epoch (" + spectrum['timeunit'] + ")", "@epoch{1.11}") ]
        tt2 += [ ("Source", "@src") ]
        hover2 = HoverTool(tooltips = tt2)

        p2 = Figure(title='Spectra for ' + eventname, x_axis_label=label_format('Wavelength (' + catalog[entry]['spectra'][0]['waveunit'] + ')'),
            y_axis_label=label_format('Flux (scaled)' + (' + offset'
            if (nspec > 1) else '')), x_range = x_range, tools = tools, 
            y_range = y_range)
        p2.add_tools(hover2)

        sources = []
        for i in range(len(spectrumwave)):
            data = dict(
                x0 = spectrumwave[i],
                y0 = spectrumscaled[i],
                yorig = spectrumflux[i],
                fluxunit = [label_format(catalog[entry]['spectra'][i]['fluxunit'])]*len(spectrumscaled[i]),
                x = spectrumwave[i],
                y = [y_offsets[i] + j for j in spectrumscaled[i]],
                yoff = [y_offsets[i]],
                binsize = [1.0],
                spacing = [1.0],
                src = [catalog[entry]['spectra'][i]['source']]*len(spectrumscaled[i])
            )
            if 'timeunit' in spectrum and 'time' in spectrum:
                data['epoch'] = [catalog[entry]['spectra'][i]['time'] for j in spectrumscaled[i]]
            sources.append(ColumnDataSource(data))
            p2.line('x', 'y', source=sources[i], color=mycolors[i % len(mycolors)], line_width=2)

        sdicts = dict(zip(['s'+str(x) for x in range(len(sources))], sources))
        callback = CustomJS(args=sdicts, code="""
            for (s = 0; s < """ + str(len(sources)) + """; s++) {
                var data = eval('s'+s).get('data');
                if (cb_obj.get('title') == 'Spacing') {
                    data['spacing'][0] = cb_obj.get('value');
                } else {
                    data['binsize'][0] = cb_obj.get('value');
                }
                var f = data['binsize'][0]
                var space = data['spacing'][0]
                var x0 = data['x0'];
                var y0 = data['y0'];
                var dx0 = x0[1] - x0[0];
                var yoff = space*data['yoff'][0];
                data['x'] = [x0[0] - 0.5*Math.max(0., f - dx0)];
                data['y'] = [y0[0] + yoff];
                var xaccum = 0.;
                var yaccum = 0.;
                for (i = 0; i < x0.length; i++) {
                    var dx;
                    if (i == 0) {
                        dx = x0[i+1] - x0[i];
                    } else {
                        dx = x0[i] - x0[i-1];
                    }
                    xaccum += dx;
                    yaccum += y0[i]*dx;
                    if (xaccum >= f) {
                        data['x'].push(data['x'][data['x'].length-1] + xaccum);
                        data['y'].push(yaccum/xaccum + yoff);
                        xaccum = 0.;
                        yaccum = 0.;
                    }
                }
                eval('s'+s).trigger('change');
            }
        """)

        binslider = Slider(start=0, end=20, value=1, step=0.5, title=label_format("Bin size (Angstrom)"), callback=callback)
        spacingslider = Slider(start=0, end=2, value=1, step=0.02, title=label_format("Spacing"), callback=callback)

    if (photoavail or spectraavail) and dohtml and args.writehtml:
    #if (photoavail and spectraavail) and dohtml and args.writehtml:
        if photoavail and spectraavail:
            p = vplot(hplot(p1),hplot(p2,vform(binslider,spacingslider)), width=900)
        elif photoavail:
            p = p1
        else:
            p = vplot(hplot(p2,vform(binslider,spacingslider)), width=900)

        html = file_html(p, INLINE, eventname)
        returnlink = r'<br><a href="https://sne.space"><< Return to supernova catalog</a>'
        repfolder = get_rep_folder(catalog[entry])
        html = re.sub(r'(\<\/body\>)', r'<a href="https://cdn.rawgit.com/astrotransients/' + repfolder + '/master/' + eventname + r'.json" download>Download datafile</a><br><br>\n\1', html)
        if len(catalog[entry]['sources']):
            html = re.sub(r'(\<\/body\>)', r'<em>Sources of data:</em><br><table><tr><th width=30px>ID</th><th>Source</th></tr>\n\1', html)
            for source in catalog[entry]['sources']:
                html = re.sub(r'(\<\/body\>)', r'<tr><td>' + source['alias'] +
                    r'</td><td>' + (('<a href="' + source['url'] + '">') if 'url' in source else '') +
                    source['name'].encode('ascii', 'xmlcharrefreplace').decode("utf-8") +
                    (r'</a>' if 'url' in source else '') +
                    r'</td></tr>\n\1', html)
            html = re.sub(r'(\<\/body\>)', r'</table>\n\1', html)
        html = re.sub(r'(\<\/body\>)', returnlink+r'\n\1', html)
        print(outdir + eventname + ".html")
        with open(outdir + eventname + ".html", "w") as fff:
            fff.write(html)

    # Necessary to clear Bokeh state
    reset_output()

    #if spectraavail and dohtml:
    #    sys.exit()

    #if fcnt > 100:
    #    sys.exit()

    # Save this stuff because next line will delete it.
    if args.writecatalog:
        if 'photoplot' in catalog[entry]:
            snepages.append(catalog[entry]['aliases'] + ['https://sne.space/' + catalog[entry]['photoplot']])

        if 'sources' in catalog[entry]:
            for sourcerow in catalog[entry]['sources']:
                strippedname = re.sub('<[^<]+?>', '', sourcerow['name'].encode('ascii','xmlcharrefreplace').decode("utf-8"))
                if strippedname in sourcedict:
                    sourcedict[strippedname] += 1
                else:
                    sourcedict[strippedname] = 1

        nophoto.append(catalog[entry]['numphoto'] < 3)

        nospectra.append(catalog[entry]['numspectra'] == 0)

        totalphoto += catalog[entry]['numphoto']
        totalspectra += catalog[entry]['numspectra']

        # Delete unneeded data from catalog, add blank entries when data missing.
        catalogcopy[entry] = OrderedDict()
        for col in columnkey:
            if col in catalog[entry]:
                catalogcopy[entry][col] = catalog[entry][col]
            else:
                catalogcopy[entry][col] = None

        del catalog[entry]

    if args.test and spectraavail and photoavail:
        break

# Write it all out at the end
if args.writecatalog and not args.eventlist:
    catalog = catalogcopy

    #Write the MD5 checksums
    jsonstring = json.dumps(md5s, separators=(',',':'))
    f = open(outdir + 'md5s.json' + testsuffix, 'w')
    f.write(jsonstring)
    f.close()

    # Make a few small files for generating charts
    f = open(outdir + 'snepages.csv' + testsuffix, 'w')
    csvout = csv.writer(f, quotechar='"', quoting=csv.QUOTE_ALL)
    for row in snepages:
        csvout.writerow(row)
    f.close()

    f = open(outdir + 'sources.csv' + testsuffix, 'w')
    sortedsources = sorted(list(sourcedict.items()), key=operator.itemgetter(1), reverse=True)
    csvout = csv.writer(f)
    csvout.writerow(['Source','Number'])
    for source in sortedsources:
        csvout.writerow(source)
    f.close()

    nophoto = sum(nophoto)
    hasphoto = len(catalog) - nophoto
    f = open(outdir + 'pie.csv' + testsuffix, 'w')
    csvout = csv.writer(f)
    csvout.writerow(['Category','Number'])
    csvout.writerow(['Has light curve', hasphoto])
    csvout.writerow(['No light curve', nophoto])
    f.close()

    nospectra = sum(nospectra)
    hasspectra = len(catalog) - nospectra
    f = open(outdir + 'spectra-pie.csv' + testsuffix, 'w')
    csvout = csv.writer(f)
    csvout.writerow(['Category','Number'])
    csvout.writerow(['Has spectra', hasspectra])
    csvout.writerow(['No spectra', nospectra])
    f.close()

    with open(outdir + 'hasphoto.html' + testsuffix, 'w') as f:
        f.write("{:,}".format(hasphoto))
    with open(outdir + 'hasspectra.html' + testsuffix, 'w') as f:
        f.write("{:,}".format(hasspectra))
    with open(outdir + 'snecount.html' + testsuffix, 'w') as f:
        f.write("{:,}".format(len(catalog)))
    with open(outdir + 'photocount.html' + testsuffix, 'w') as f:
        f.write("{:,}".format(totalphoto))
    with open(outdir + 'spectracount.html' + testsuffix, 'w') as f:
        f.write("{:,}".format(totalspectra))

    ctypedict = dict()
    for entry in catalog:
        cleanedtype = ''
        if 'claimedtype' in catalog[entry] and catalog[entry]['claimedtype']:
            maxsources = 0
            for ct in catalog[entry]['claimedtype']:
                sourcecount = len(ct['source'].split(','))
                if sourcecount > maxsources:
                    maxsources = sourcecount
                    cleanedtype = ct['value'].strip('?* ')
        if not cleanedtype:
            cleanedtype = 'Unknown'
        if cleanedtype in ctypedict:
            ctypedict[cleanedtype] += 1
        else:
            ctypedict[cleanedtype] = 1
    sortedctypes = sorted(list(ctypedict.items()), key=operator.itemgetter(1), reverse=True)
    f = open(outdir + 'types.csv' + testsuffix, 'w')
    csvout = csv.writer(f)
    csvout.writerow(['Type','Number'])
    for ctype in sortedctypes:
        csvout.writerow(ctype)
    f.close()

    # Convert to array since that's what datatables expects
    catalog = list(catalog.values())

    jsonstring = json.dumps(catalog, separators=(',',':'))
    f = open(outdir + 'sne-catalog.json' + testsuffix, 'w')
    f.write(jsonstring)
    f.close()

    f = open(outdir + 'catalog.html' + testsuffix, 'w')
    f.write('<table id="example" class="display" cellspacing="0" width="100%">\n')
    f.write('\t<thead>\n')
    f.write('\t\t<tr>\n')
    for h in header:
        f.write('\t\t\t<th class="' + h + '">' + header[h] + '</th>\n')
    f.write('\t\t</tr>\n')
    f.write('\t</thead>\n')
    f.write('\t<tfoot>\n')
    f.write('\t\t<tr>\n')
    for h in header:
        f.write('\t\t\t<th class="' + h + '">' + header[h] + '</th>\n')
    f.write('\t\t</tr>\n')
    f.write('\t</thead>\n')
    f.write('</table>\n')
    f.close()
