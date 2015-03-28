var map;
google.maps.event.addDomListener(window, 'load', initialize);
var circles = [];
var fbAccessToken;

/*
// ############
//    Search Events
// ############
*/ 
// If the element with id 'searchVenue' is clicked
$('#loginAndSearchEvent').on('click',function(e){
	var location = $('#location').val();
    var startdate = $('#start').val();
    var enddate = $('#end').val();
    $.blockUI({ message: '<h2>Facebook data and external events are being fatched. This may take several minutes, depending on the number of selected days...</h2>' });
    $.ajax({
    	   url: '/search_events',
    	   data: {'location': location, 'startdate': startdate, 'enddate': enddate, 'fbToken': fbAccessToken},
    	   timeout: 1200000, //in milliseconds
    	   success: function(data, textStatus, jqXHR){
    		    $.unblockUI();
    			// If successful, add the data to the DOM tree under the 'searchResults' element.
    	        var obj = jQuery.parseJSON(data);
    	   
    	        //set map central to search area
    	        var mapOptions = {
    	            zoom: 12,
    	            center: new google.maps.LatLng(obj.location.lat, obj.location.lon)
    	        };
    	        map.setOptions(mapOptions);
    	        
    	        //remove previous circles
    	        for(circle in circles){
    	        	circles[circle].setMap(null);
    	        }
    	        	
    	        var events = obj.events;
    	        for(var event_idx in events){
    	        	var event = events[event_idx];
    	        	
    	        	var color = '#000000';
        	        if( !event.hasOwnProperty('cluster') ){
            	        color = '#0000FF';
        	        }else if( event.cluster == 0 ){
        	        	color = '#FF0000';
        	        }else if( event.cluster == 1 ){
        	        	color = '#298A08';
        	        }else if( event.cluster == 2 ){
        	        	color = '#0000FF';
        	        }
        	        
    	        	var populationOptions = {
    	        	  //draw circle
    			      strokeColor: color, 
    			      strokeOpacity: 0.8,
    			      strokeWeight: 2, 
    			      fillColor: color,
    			      fillOpacity: 0.35,
    			      map: map,
    			      center: new google.maps.LatLng(event.lat_original, event.lon_original),
    			      radius: event.number_attendants+50,
    			      clickable: true
    			    };
    			    circle = new google.maps.Circle(populationOptions);
    	            circles.push(circle);

    	            setInfoWindow(event, circle)
    	        }
    	   },
    	   error: function(jqXHR, textStatus, errorThrown){
    		   $.unblockUI();
    		   alert( "We are sorry! An error occured. Please try again. (Status Code:"+textStatus+", "+errorThrown+")" );
    	   }
    	});
});

//This is called with the results from from FB.getLoginStatus().
function fbLoginStatusChanged(response) {
  if (response.status === 'connected') {
	  fbAccessToken =   FB.getAuthResponse()['accessToken'];
	  FB.api('/me', function(response) {
		 document.getElementById('loginStatus').innerHTML =
		   'Thanks for logging in, ' + response.name + '! Enter your current location and the time-range you want to search for';
	  });
  } else if (response.status === 'not_authorized') {
	  console.log('Please log into this app.');
  } else {
	  console.log('Please log into Facebook.');
  }
}


/////////////////////////////////////////////////////////////////
//Google Maps Stuff///////////////////////////////////////////
/////////////////////////////////////////////////////////////////

function initialize() {
    var mapOptions = {
        zoom: 12,
        center: new google.maps.LatLng(52.370197, 4.890444)
    };
    map = new google.maps.Map(document.getElementById('searchResults'),mapOptions);    
}

function setInfoWindow(event, circle){
	// Create the data table.
	event.previous_attendants
    var data = new google.visualization.DataTable();
    data.addColumn('string', 'Event');
    data.addColumn('number', 'Number of Attendees');
    for(var previous_event in event.previous_attendants){
    	data.addRow([previous_event,event.previous_attendants[previous_event]]);
    }
    

    // Set chart options
    var options = {'title': 'People who visited this event also visited / will visit',
                   'width':600,
                   'height':200,
                   legend: { position: "none" },
                   hAxis: {slantedText:true, slantedTextAngle:340} };

    var content = document.createElement('div');
    var title = document.createElement('h4');
    var textnode = document.createTextNode(event.name+' at '+event.venue+' ( '+event.start+' ) ');
    title.appendChild(textnode);
    var linknode = document.createElement('a');
    linknode.setAttribute('href','http://www.facebook.com/'+event.id);
    linknode.setAttribute('target','blank');
    linknode.innerHTML = 'go to Facebook!';
    title.appendChild(linknode);
    content.appendChild(title);
    var chartnode = document.createElement('div');
    content.appendChild(chartnode)
    var clustercontent = document.createElement('h6');
    var clustertext = document.createTextNode('Cluster terms: '+(event.hasOwnProperty('cluster_terms') ? event.cluster_terms : ''));
    clustercontent.appendChild(clustertext);
    content.appendChild(clustercontent)

    var infowindow = new google.maps.InfoWindow();
    var chart = new google.visualization.ColumnChart(chartnode);
    
    chart.draw(data, options);
    infowindow.setContent(content);
        
    google.maps.event.addListener(circle, 'click', function() {
    	infowindow.setPosition(circle.getCenter());
    	infowindow.open(circle.get('map'));
    });
}

/////////////////////////////////////////////////////////////////
//Facebook Login Stuff///////////////////////////////////////////
/////////////////////////////////////////////////////////////////

// This function is called when someone finishes with the Login
// Button.  See the onlogin handler attached to it in the sample
// code below.
function checkLoginState() {
  FB.getLoginStatus(function(response) {
	  fbLoginStatusChanged(response);
  });
}

window.fbAsyncInit = function() {
  FB.init({
    appId      : '798360973552447',
    cookie     : true,  // enable cookies to allow the server to access 
                        // the session
    xfbml      : true,  // parse social plugins on this page
    version    : 'v2.2' // use version 2.2
  });
	  
  FB.getLoginStatus(function(response) {
	  fbLoginStatusChanged(response);
  });
};
  
//Load the Facebook SDK asynchronously
  (function(d, s, id) {
    var js, fjs = d.getElementsByTagName(s)[0];
    if (d.getElementById(id)) return;
    js = d.createElement(s); js.id = id;
    js.src = "//connect.facebook.net/en_US/sdk.js";
    fjs.parentNode.insertBefore(js, fjs);
  }(document, 'script', 'facebook-jssdk'));

/////////////////////////////////////////////////////////////////
//Google Visualizations Stuff////////////////////////////////////
/////////////////////////////////////////////////////////////////
//Load the Visualization API and the piechart package.
google.load('visualization', '1.0', {'packages':['corechart']});