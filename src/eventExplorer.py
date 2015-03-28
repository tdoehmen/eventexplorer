from flask import Flask, render_template, url_for, request, jsonify
from SPARQLWrapper import SPARQLWrapper, RDF, JSON
import requests
import facebook
import json
import time
import sys
import codecs
import datetime
import geopy.distance
import cPickle
import numpy
#from sklearn.feature_extraction.text import TfidfVectorizer
#from sklearn.cluster import KMeans

sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)

app = Flask(__name__)

@app.route('/')
def first_page():
    app.logger.debug('You arrived at ' + url_for('first_page'))
    return render_template('index.html', startmin=time.strftime("%Y-%m-%d"), enddefault=(datetime.datetime.now()+datetime.timedelta(1)).strftime("%Y-%m-%d"))

@app.route('/login')
def login_page():
    app.logger.debug('You arrived at ' + url_for('first_page'))
    return render_template('facebookLogin.html')

@app.route('/search_events',methods=['GET'])
def search_event():
    # Get the message from the GET request, if nothing is found, set a default message.

    location = request.args.get('location', '')
    startdate = request.args.get('startdate', '')
    enddate = request.args.get('enddate', '')
    fbToken = request.args.get('fbToken', '')
    #enddate = datetime.datetime.strptime(startdate,"%Y-%m-%d") + datetime.timedelta(1)
    print startdate
    print enddate

    fbGraph = facebook.GraphAPI(fbToken)
    radius = '10';
    
    
    own_event_id_index = {}
    own_attendant_event_index = {}
    # TODO: Facebook only returns 13?! events why?
    own_events = fbGraph.get_connections('me', 'events', limit=25)['data']
    print(len(own_events))
    for event in own_events:
        print((datetime.datetime.now()-datetime.timedelta(366)))
        print(datetime.datetime.strptime(event['start_time'][:10], '%Y-%m-%d'))
        if (datetime.datetime.now()-datetime.timedelta(366)) > datetime.datetime.strptime(event['start_time'][:10], '%Y-%m-%d'):
            print('old event: '+event['name'])
            continue
        if event['rsvp_status'] != 'attending':
            print('not attending: '+event['name'])
            continue;
        attendings = fbGraph.get_connections(event['id'], 'attending')['data']
        own_event_id_index[event['id']] = event['name']
        for attending in attendings:
            own_attendant_event_index.setdefault(attending['id'],[])
            own_attendant_event_index.get(attending['id']).append(event['id'])
    print(own_attendant_event_index)

    location_lat_long = requests.get('http://maps.googleapis.com/maps/api/geocode/json?address='+location+'&sensor=true').json();
    lat = str(location_lat_long['results'][0]['geometry']['location']['lat']);
    lon = str(location_lat_long['results'][0]['geometry']['location']['lng']);
        
    facebook_events = []
    
    eventful_request = requests.get('http://api.eventful.com/json/events/search?app_key=tsjkqtvVDbT85C6R&where='+lat+','+lon+'&within=10&unit=km&date='+time.strftime("%Y%m%d",time.strptime(startdate,"%Y-%m-%d"))+'00-'+time.strftime("%Y%m%d",time.strptime(enddate,"%Y-%m-%d"))+'00&page_size=100&sort_order=popularity').json()
    print('number of eventful events: '+eventful_request['total_items'])
    for page in xrange(1,int(eventful_request['page_count'])):    
        eventful_request = requests.get('http://api.eventful.com/json/events/search?app_key=tsjkqtvVDbT85C6R&where='+lat+','+lon+'&within=10&unit=km&date='+time.strftime("%Y%m%d",time.strptime(startdate,"%Y-%m-%d"))+'00-'+time.strftime("%Y%m%d",time.strptime(enddate,"%Y-%m-%d"))+'00&page_size=100&sort_order=popularity&page_number='+str(page)).json()
        for event in eventful_request['events']['event']:
            facebook_search_result = fbGraph.request('search', {'q' : event['title'].encode('ascii','ignore'), 'type' : 'event', 'limit' : 1})
            if len(facebook_search_result['data']) > 0:
                print('name: '+facebook_search_result['data'][0]['name'])
                print('id: '+facebook_search_result['data'][0]['id']) 
                fb_event = fbGraph.get_object(facebook_search_result['data'][0]['id'])
                fb_event.setdefault('venue',{})
                fb_event['venue'].setdefault('latitude','0')
                fb_event['venue'].setdefault('longitude','0')
                fb_event.setdefault('end_time','')
                fb_event.setdefault('description','')
                event.setdefault('end_time','')
                event.setdefault('description','')
                event.setdefault('venue_name','')
                event.setdefault('venue_address','')
                facebook_events.append({'id':fb_event['id'],
                                        'name':fb_event['name'], 
                                        'name_original':event['title'], 
                                        'lat':fb_event['venue']['latitude'],
                                        'lat_original':event['latitude'],
                                        'lon':fb_event['venue']['longitude'],
                                        'lon_original':event['longitude'],
                                        'start':fb_event['start_time'],
                                        'start_original':event['start_time'],
                                        'end':fb_event['end_time'],
                                        'end_original':event['end_time'],
                                        'description':fb_event['description'],
                                        'description_original':event['description'],
                                        'venue':('' if event['venue_name'] is None else event['venue_name'].encode('ascii','ignore'))+', '+('' if event['venue_address'] is None else event['venue_address'].encode('ascii','ignore')),
                                        'source':event['url']
                                        })
            else:
                print('event "'+event['title'].encode('ascii','ignore')+'" not found')
    
    eventbrite_request = requests.get('https://www.eventbriteapi.com/v3/events/search/?location.within=10km&location.latitude='+lat+'&location.longitude='+lon+'&start_date.range_start='+startdate+'T00%3A00%3A00Z&start_date.range_end='+enddate+'T00%3A00%3A00Z&token=C7XZQC7QC4CMDR4XRBIZ').json()
    print('number of eventbrite events: '+str(eventbrite_request['pagination']['object_count']))
    for event in eventbrite_request['events']:
        facebook_search_result = fbGraph.request('search', {'q' : event['name']['text'].encode('ascii','ignore'), 'type' : 'event', 'limit' : 1})
        if len(facebook_search_result['data']) > 0:
            print('name: '+facebook_search_result['data'][0]['name'])
            print('id: '+facebook_search_result['data'][0]['id']) 
            fb_event = fbGraph.get_object(facebook_search_result['data'][0]['id'])
            fb_event.setdefault('venue',{})
            fb_event['venue'].setdefault('latitude','0')
            fb_event['venue'].setdefault('longitude','0')
            fb_event.setdefault('end_time','')
            fb_event.setdefault('description','')
            event.setdefault('name',{})
            event['name'].setdefault('text','')
            event.setdefault('venue',{})
            event['venue'].setdefault('latitude','0')
            event['venue'].setdefault('longitude','0')
            event['venue'].setdefault('address',{})
            event['venue']['address'].setdefault('address_1','')
            event['venue'].setdefault('name','')
            event.setdefault('end',{})
            event['end'].setdefault('local','')
            event.setdefault('description',{})
            event['description'].setdefault('text','')
            facebook_events.append({'id':fb_event['id'],
                                    'name':fb_event['name'],
                                    'name_original':event['name']['text'], 
                                    'lat':fb_event['venue']['latitude'],
                                    'lat_original':event['venue']['latitude'],
                                    'lon':fb_event['venue']['longitude'],
                                    'lon_original':event['venue']['longitude'],
                                    'start':fb_event['start_time'],
                                    'start_original':event['start']['local'],
                                    'end':fb_event['end_time'],
                                    'end_original':event['end']['local'],
                                    'description':fb_event['description'],
                                    'description_original':event['description']['text'],
                                    'venue':('' if event['venue']['name'] is None else event['venue']['name'].encode('ascii','ignore'))+', '+('' if event['venue']['address']['address_1'] is None else event['venue']['address']['address_1'].encode('ascii','ignore')),
                                    'source':event['url']
                                    })
        else:
            print('event "'+event['name']['text'].encode('ascii','ignore')+'" not found')
    
    meetup_request = requests.get('https://api.meetup.com/2/open_events?and_text=False&offset=0&format=json&lon='+lon+'&limited_events=True&photo-host=public&time='+str(int(time.mktime(time.strptime(startdate,"%Y-%m-%d"))*1000))+'%2C'+str(int(time.mktime(time.strptime(enddate,"%Y-%m-%d"))*1000))+'&radius=6.2137&lat='+lat+'&desc=False&status=upcoming&key=b3d7b43f71356c3e23a384943735f').json()    
    print('number of meetup events: '+str(meetup_request['meta']['total_count']))
    for event in meetup_request['results']:
        facebook_search_result = fbGraph.request('search', {'q' : event['name'].encode('ascii','ignore'), 'type' : 'event', 'limit' : 1})
        if len(facebook_search_result['data']) > 0:
            print('name: '+facebook_search_result['data'][0]['name'])
            print('id: '+facebook_search_result['data'][0]['id']) 
            fb_event = fbGraph.get_object(facebook_search_result['data'][0]['id'])
            fb_event.setdefault('venue',{})
            fb_event['venue'].setdefault('latitude','0')
            fb_event['venue'].setdefault('longitude','0')
            fb_event.setdefault('end_time','')
            fb_event.setdefault('description','')
            event.setdefault('venue',{})
            event['venue'].setdefault('lat',event['group']['group_lat'])
            event['venue'].setdefault('lon',event['group']['group_lon'])
            event['venue'].setdefault('address_1', '')
            event['venue'].setdefault('name', '')
            event.setdefault('description','')
            event.setdefault('event_url','meetup:'+event['id'])
            facebook_events.append({'id':fb_event['id'],
                                    'name':fb_event['name'],
                                    'name_original':event['name'], 
                                    'lat':fb_event['venue']['latitude'],
                                    'lat_original':event['venue']['lat'],
                                    'lon':fb_event['venue']['longitude'],
                                    'lon_original':event['venue']['lon'],
                                    'start':fb_event['start_time'],
                                    'start_original':event['time'],
                                    'end':fb_event['end_time'],
                                    'end_original':'',
                                    'description':fb_event['description'],
                                    'description_original':event['description'],
                                    'venue':('' if event['venue']['name'] is None else event['venue']['name'].encode('ascii','ignore'))+', '+('' if event['venue']['address_1'] is None else event['venue']['address_1'].encode('ascii','ignore')),
                                    'source':event['event_url']
                                    })
        else:
            print('event "'+event['name'].encode('ascii','ignore')+'" not found')
    
    '''
    f = open("myData.pickle", "wb") # create a file handle for writing (w) in binary mode (b) named myData.pickle, 
    cPickle.dump(facebook_events, f) # write the contents of list 'words' to file 'f'
    f.close()
    
    
    facebook_events=cPickle.load(open("myData.pickle")) 
    '''
            
    for event in facebook_events:
        attendings = fbGraph.get_connections(event['id'], 'attending')['data']
        print('number of people attending event '+str(event['id'])+': '+str(len(attendings)))
        previous_attendants_index = {}
        event['number_attendants']=len(attendings)
        for attending in attendings:
            if own_attendant_event_index.has_key(attending['id']) :
                for own_attendant_event_id in own_attendant_event_index.get(attending['id']):
                    previous_attendants_index.setdefault(own_event_id_index[own_attendant_event_id],0) 
                    previous_attendants_index[own_event_id_index[own_attendant_event_id]] = previous_attendants_index[own_event_id_index[own_attendant_event_id]]+1
        event['previous_attendants'] = previous_attendants_index
        print(previous_attendants_index)    
     
    facebook_events_clean = []
    for event in facebook_events: 
        #filter events which are not at the same location (location differs more than 10km (search radius)
        point_fb = geopy.Point(float(event['lat']),float(event['lon']))
        point_orig = geopy.Point(float(event['lat_original']),float(event['lon_original']))        
        if geopy.distance.distance(point_fb,point_orig).km < 10:
            #filter events which are not at the same location
            replace = False
            add = True
            for event_clean in facebook_events_clean:
                point_event_clean = geopy.Point(float(event_clean['lat_original']),float(event_clean['lon_original']))       
                #if two events are at the same place (<10m distance), check which one has more attendees and take that one
                if geopy.distance.distance(point_orig,point_event_clean).m < 10:
                    if int(event['number_attendants']) > int(event_clean['number_attendants']) :    
                        replace = True
                    else:
                        add = False
                    break;
            #remove smaller event and replace with bigger one        
            if replace == True :                
                facebook_events_clean.remove(event_clean)
            if add == True :
                facebook_events_clean.append(event)
    
    facebook_event_descriptions = []
    for event in facebook_events:
        facebook_event_descriptions.append(event['description'])
    
    
    ''' For compatability reasons with openshift deactivated 
    
    nr_of_cluster = 3     
    nr_of_features = 300     
    vectorizer = TfidfVectorizer(max_df=0.5, max_features=nr_of_features,
                                 min_df=2, stop_words='english',
                                 use_idf=True)
    X = vectorizer.fit_transform(facebook_event_descriptions)
    km = KMeans(n_clusters=nr_of_cluster, init='k-means++', max_iter=100, n_init=1,
                verbose=False)
    km.fit(X)
    
    order_centroids = km.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names()    
    for event in facebook_events:
        max_hits = 0
        for cluster in range(nr_of_cluster) :
            hits = 0
            cluster_terms = ''
            for ind in order_centroids[cluster, :7]:
                cluster_terms += ' ' + str(terms[ind]).encode('ascii','ignore')
                for word in event['description'].split():
                    if word.lower() == terms[ind].lower():
                        hits += 1
            if hits > max_hits:
                event['cluster'] = cluster
                event['cluster_terms'] = cluster_terms
                max_hits = hits
            #print('event: '+str(event['name'])+' cluster: '+str(cluster)+' hits: '+str(hits))   
    
    '''
    terms = [['music',
              'techno',
              'party',
              'loud',
              'dj',
              'electro',
              'club'
              ],
             ['museum',
              'exhibition',
              'foto',
              'photo',
              'art',
              'style',
              'artist'
              ],
             ['technology',
              'conference',
              'startup',
              'meeting',
              'coffee',
              'lunch',
              'business'
              ]]    
    for event in facebook_events:
        max_hits = 0
        for cluster in range(3) :
            hits = 0
            cluster_terms = ''
            for term in terms[cluster]:
                cluster_terms += ' ' + term
                for word in event['description'].split():
                    if word.lower() == term.lower():
                        hits += 1
            if hits > max_hits:
                event['cluster'] = cluster
                event['cluster_terms'] = cluster_terms
                max_hits = hits
            #print('event: '+str(event['name'])+' cluster: '+str(cluster)+' hits: '+str(hits))   
                     
    facebook_events_clean.sort(key=lambda event: int(event['number_attendants']), reverse=True) 
    max_number_of_event = 999;
    
    return json.dumps({'location':{'lat':lat,'lon':lon},'events':facebook_events_clean[0:(len(facebook_events_clean) if len(facebook_events_clean) <= max_number_of_event else max_number_of_event )]})
        
    
if __name__ == '__main__':
    app.debug = True
    app.run()
