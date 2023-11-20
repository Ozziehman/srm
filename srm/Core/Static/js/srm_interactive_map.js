const startPointInput = document.getElementById('start_point');
const endPointInput = document.getElementById('end_point');
const contextMenu = document.getElementById('context-menu');
var lastClickedPosition = null;

/**
 * Initialize the interactive Leaflet map in the 'map' div.
 * Should focus on the user's location by default, unable to do 
 * this in this prototype due to Geolocation API only working over HTTPS.
 * 
 * Attribution to Leaflet and OpenStreetMap is required, otherwise the map will not work.
 */
var map = L.map('map', { zoomControl: false, minZoom: 4 }).setView([50.881401, 5.956668], 13);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

/**
 * When a user right-clicks the map, save the position in the lastClickedPosition variable.
 * Setting the start and endpoint of the route is controlled by the custom context menu.
 */
map.on('contextmenu', function(event) {
    var coordinates = event.latlng;
    let lat = coordinates.lat;
    let lng = coordinates.lng;
    lastClickedPosition = `${lat}, ${lng}`
})

/**
 * Function that sets the start or endpoint of the route.
 */
function setPosition(type)
{
    if(!['start', 'end'].includes(type)) return;

    type === 'start' ? startPointInput.value = lastClickedPosition : endPointInput.value = lastClickedPosition;

    contextMenu.classList.remove('visible');
}