from threading import Thread
import threading
lock = threading.Lock()
import glob
import os.path
import cookielib
import re
import time
import datetime
from datetime import date
import socket
import requests
global run_length
global i_controller
global matches_id_controller
#from requests.adapters import HTTPAdapter
# timeout in seconds
timeout = 6
socket.setdefaulttimeout(timeout)
# timeout in seconds
# set header
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
# set header
#print "Started hon scanner at "+str(datetime.datetime.now())
# configurable options
run_length = 30000 #30000
threads_to_start = 8 #8
#mmr_threshold = 1750 #1750
min_kills = 15 #20
max_deaths = 6 #8
today = str(date.today())
gpm_threshold = 750
#logger = open("log_"+today+".txt", 'a')
#logger.write("Started at "+str(datetime.datetime.now())+"\n")
#logger.close()
# configurable options
def refresh():
    try:
        global i_controller
        global matches_id_controller
        i_controller = 1
        request = requests.get("http://api.honbot.com/latestMatches", headers=hdr)
        geturl_readable = request.text
        matches_id_controller = re.findall("\"id\":(\d+)", geturl_readable)[-1]
        #print matches_id_controller
    except:
        matches_id_controller = 150134119 # switch to manual

refresh()

def doWork():
    while True:
        try:
            global run_length
            take_new_match = 1
            started_at = time.time()
            while (time.time() - started_at) < 86400: #run for 24 hours (86400 sec)
                ##print (time.time() - started_at) #timer, dont #print this
                with lock:
                    if take_new_match == 1:
                        #thread controller
                        global i_controller
                        i = i_controller
                        i_controller = int(i_controller) + 1 #change for other threads
                        global matches_id_controller
                        matches_id = matches_id_controller
                        matches_id_controller = int(matches_id_controller) - 1 #change for other threads
                        #thread controller
                        take_new_match = 0
                if i_controller > run_length:
                    refresh()
                today = str(date.today())
                try:
                    request2 = requests.get('https://www.heroesofnewerth.com/matchstats/'+str(matches_id)+'/', headers=hdr)
                    geturl_new_readable = request2.text
                    geturl_new_readable_filter = re.findall('[\t\r\n]+.*kills"\>(\d{1,2})\<\/span\>\s\/\s\<span class=\"deaths\"\>(\d{1,2})', geturl_new_readable)
                    gpms = re.findall('\<td\>([\d\.]+)<\/td\>[\r\n\t]+\<td>[\d]+\<\/td\>[\r\n\t]+\<td\>[\r\n\t]+\<div', geturl_new_readable)
                    ##print "gpms"+str(gpms)
                    #exclusive filters
                    geturl_new_readable_filter2 = re.search("[\t\r\n]+.*(TMM Match)", geturl_new_readable)
                    matched_ranked = geturl_new_readable_filter2.group(1)
                    #geturl_new_readable_filter3 = re.search("[\t\r\n]+.*(Forests of Caldavar)", geturl_new_readable)
                    #matched_map = geturl_new_readable_filter3.group(1) 
                    #exclusive filters             
                except:
                    ##print str(matches_id)+": wrong type of match"
                    take_new_match = 1
                else:            
                    list_kd = []
                    p = -1 #for comparing kd to heroes
                    for tuple in geturl_new_readable_filter:
                            p = p+1
                            if int(tuple[0]) >= min_kills and int(tuple[1]) <= max_deaths:
                                    kills_legion = []
                                    kills_hellbourne = []
                                    #print "Starting testing of "+str(matches_id)
                                    #kdi
                                    #print "Match KD pairs:"+ str(len(geturl_new_readable_filter))
                                    kills_legion = int(geturl_new_readable_filter[0][0])+int(geturl_new_readable_filter[1][0])+int(geturl_new_readable_filter[2][0])+int(geturl_new_readable_filter[3][0])+int(geturl_new_readable_filter[4][0])
                                    kills_hellbourne = int(geturl_new_readable_filter[5][0])+int(geturl_new_readable_filter[6][0])+int(geturl_new_readable_filter[7][0])+int(geturl_new_readable_filter[8][0])+int(geturl_new_readable_filter[9][0])
                                    #print "Legion kills:"+str(kills_legion)
                                    #print "Hellbourne kills:"+str(kills_hellbourne)
                                    kdi = abs(kills_legion - kills_hellbourne)
                                    #print "KDi: "+str(kdi)
                                    qkdi = kdi*100 / (kills_legion + kills_hellbourne)
                                    #print "KDi ratio: "+str(qkdi)
                                    #kdi
                                    hero_icons = re.findall ('[\t\r\n]+.*\/(\d*)\/icon_\d*.jpg', geturl_new_readable)
                                    request4 = requests.get("https://www.heroesofnewerth.com/heroes/view/"+str(hero_icons[p]), headers=hdr)
                                    geturl_readable3 = request4.text
                                    hero_matched = re.search ("[\t\r\n]+.*Hero - ([\w\s]+)", geturl_readable3)
                                    gpm = gpms[p]
                                    #print "GPM: "+str(gpm)
                                    try:
                                        hero_matched_readable = hero_matched.group(1)
                                    except:
                                        hero_matched_readable = "unknown"
                                    #print hero_matched_readable                                
                                    matched_kills = tuple[0]
                                    matched_deaths = tuple[1]
                                    version = []
                                    version = re.findall('[\t\r\n]+([\d\.]+)[\t\r\n]+\<\/div\>[\t\r\n]+\<div\sstyle\=\"clear',geturl_new_readable)
                                    #print "Version: "+str(version[0])
                                    player_list = re.findall('[\t\r\n]+.*\/playerstats\/ranked\/(.*)\"\>', geturl_new_readable)
                                    #print player_list
                                    win_percentage_list = []
                                    for x in player_list:
                                        request3 = requests.get("https://www.heroesofnewerth.com/playerstats/ranked/"+x, headers=hdr)    
                                        geturl_readable2 = request3.text
                                        win_percentage = re.findall('[\t\r\n+]([\d\.]+)\%[\t\r\n]+\<\/div\>[\t\r\n]+\<\/div\>[\t\r\n]+\<\!\-\-\sTHE', geturl_readable2)
                                        #print "Win%: "+str(win_percentage[0])
                                        win_percentage_list.append(win_percentage[0])

                                    today = str(date.today())
                                    #print "GPM: "+str(gpms[p])+" "+str(gpm_threshold)
                                    if float(gpms[p]) > float(gpm_threshold):
                                        today = str(date.today())
                                        fake_deaths = False
                                        if float(matched_deaths) == 0:
                                                matched_deaths = 1 #prevent division by 0
                                                fake_deaths = True
                                        kdr = (float(matched_kills)/float(matched_deaths))
                                        if fake_deaths == True:
                                                matched_deaths = str(0) #revert prevention after dividing
                                                fake_deaths = False
                                        #print "matched"
                                        isduplicate = 0
                                        filenames = glob.glob("matches*.txt")
                                        for fname in filenames:
                                            with open(fname) as infile:
                                                for line in infile:
                                                    if str(matches_id) in line:
                                                        isduplicate = 1
                                        #print isduplicate
                                        with lock:
                                            if isduplicate == 0:
                                                f = open("matches_"+today+".txt", 'a')
                                                print "saving data for "+str(matches_id)
                                                f.write("https://www.heroesofnewerth.com/matchstats/"+str(matches_id)+"	" +str(player_list[p])+ "	" +str(hero_matched_readable)+ "	"+matched_kills+"/"+matched_deaths+"	"+str(round(kdr,2))+"	"+str(gpm)+"	"  +str(win_percentage_list[p])+ "	" +str(qkdi)+ "	" +str(version[0])+"\n")
                                                f.close()
                                        if isduplicate == 1:
                                            #print "duplicate, skipping"
                                            take_new_match = 1
                                    else:
                                        #print "gpm threshold not met"
                                        today = str(date.today())
                                        take_new_match = 1
                    else:
                        today = str(date.today())
                        take_new_match = 1
        except:
            pass
for q in range(threads_to_start):
    t = Thread(target=doWork)
    #print "thread "+str(t)+ " started"
    t.start()
