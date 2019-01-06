function initMap() {

        // map and pin placement help --> https://github.com/taniarascia/googlemaps/blob/master/script.js
        // diplay map
        var map = new google.maps.Map(document.getElementById('map'), {
            zoom: 4,
            center: new google.maps.LatLng(42.375414, -71.117039),
            mapTypeId: google.maps.MapTypeId.ROADMAP
        });

        // define infowindow
        var infowindow = new google.maps.InfoWindow({});

        var marker, i;

       // loop through the length of the player object and set marker and infowindow info
        for (i = 0; i < Object.keys(player).length; i++) {
            marker = new google.maps.Marker({
                position: new google.maps.LatLng(player[i].lat, player[i].lng),
                map: map
            });
            // concatentated the player name and player info into one string for the content window
            google.maps.event.addListener(marker, 'click', (function (marker, i)  {
                return function() {
                    infowindow.setContent(player[i].name.concat(" -- ").concat(player[i].address))
                    infowindow.open(map, marker);
                }
            })(marker, i));
        }

}
