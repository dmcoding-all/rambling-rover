/* ============================================================
   RAMBLING ROVER — World Map (Leaflet.js)
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {
  const mapEl = document.getElementById('leaflet-map');
  if (!mapEl) return;

  // Init map
  const map = L.map('leaflet-map', {
    center: [mapCenter.lat, mapCenter.lng],
    zoom: mapCenter.zoom,
    zoomControl: true,
    scrollWheelZoom: false,
    attributionControl: true,
  });

  // CartoDB light tiles — clean, minimal look
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 20,
  }).addTo(map);

  // Custom icon
  function makeIcon(isHighlighted) {
    return L.divIcon({
      className: '',
      html: `<div class="map-marker-outer" style="${isHighlighted ? 'background:#B35A2A;' : ''}"></div>`,
      iconSize: [14, 14],
      iconAnchor: [7, 7],
      popupAnchor: [0, -10],
    });
  }

  // Add markers from Hugo-injected data
  if (typeof mapLocations !== 'undefined') {
    mapLocations.forEach(function (loc) {
      const marker = L.marker([loc.lat, loc.lng], { icon: makeIcon(false) }).addTo(map);

      // Popup content
      const popupContent = `
        <div style="font-family:'DM Sans',sans-serif;">
          <div style="font-family:'Cormorant Garant',Georgia,serif;font-size:1.05rem;color:#fff;margin-bottom:0.25rem;">${loc.name}</div>
          <div style="font-size:0.72rem;color:rgba(255,255,255,0.55);letter-spacing:0.05em;">${loc.dates}</div>
          <a href="/rambling-rover/locations/${loc.slug}/" style="display:inline-block;margin-top:0.6rem;font-size:0.72rem;letter-spacing:0.1em;text-transform:uppercase;color:#9ec96a;text-decoration:none;">
            Explore →
          </a>
        </div>
      `;

      marker.bindPopup(popupContent, { maxWidth: 220 });

      marker.on('mouseover', function () {
        this.openPopup();
      });

      marker.on('click', function () {
        window.location.href = '/rambling-rover/locations/' + loc.slug + '/';
      });
    });
  }

  // Enable scroll zoom on click
  map.on('click', function () {
    if (!map.scrollWheelZoom.enabled()) {
      map.scrollWheelZoom.enable();
    }
  });

  // Disable scroll zoom when leaving
  map.on('mouseout', function () {
    map.scrollWheelZoom.disable();
  });
});
