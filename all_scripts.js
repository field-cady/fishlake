var mymap = null;
var markerLayer = null;   // holds only the currently-visible cluster/point markers
var superIndex = null;    // supercluster spatial index over the filtered points
var allLakes = [];        // every lake that has coordinates

// Default icon for Leaflet
var defaultIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [20, 32],
  iconAnchor: [10, 32],
  popupAnchor: [1, -28],
  shadowSize: [32, 32]
});

// Functions for populating the map

var initializeMap = function() {
  // Center on the continental US so all states are visible on load
  mymap = L.map('mapid').setView([39.5, -96.0], 4);
  
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
  }).addTo(mymap);
  
  markerLayer = L.layerGroup().addTo(mymap);
  // Re-render only the markers in view whenever the map moves/zooms.
  mymap.on('moveend', renderClusters);
}

var downloadDataAndRender = function(url) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.responseType = 'json';
    xhr.onload = function() {
      if (xhr.status === 200) {
        var data = xhr.response;
        renderData(data);
      } else {
        console.error("Failed to load data from " + url);
        hideLoading();
      }
    };
    xhr.onerror = function() {
      console.error("Error loading data from " + url);
      hideLoading();
    };
    xhr.send();
};

var hideLoading = function() {
  var overlay = document.getElementById('loading-overlay');
  if (overlay) overlay.classList.add('hidden');
};

var renderData = function(dat) {
  if (dat["timestamp"]) {
    showTimestamp(dat["timestamp"]);
  }
  allLakes = (dat["lakes"] || []).filter(function(lk) {
    return lk.lat != null && lk.lon != null;
  });
  populateFilters(allLakes);
  updateMarkers();
  hideLoading();
}

// --- Species -> filter category mapping (FRONTEND ONLY; not stored in data) ---
// Display order for the filter checkboxes; "Other" always last.
var SPECIES_CATEGORIES = ["Trout", "Bass", "Panfish", "Catfish", "Walleye & Perch",
  "Crappie", "Pike & Muskie", "Carp & Rough Fish", "Salmon", "Other"];

var speciesCategory = function(name) {
  var n = (name || '').toLowerCase();
  var has = function(keys) {
    for (var i = 0; i < keys.length; i++) { if (n.indexOf(keys[i]) !== -1) return true; }
    return false;
  };
  // Order matters: more specific buckets first.
  if (n.indexOf('crappie') !== -1 || n.indexOf('wcr') !== -1) return 'Crappie';
  if (has(['salmon', 'kokanee', 'chinook', 'coho', 'sockeye', 'chum'])) return 'Salmon';
  if (has(['trout', 'char', 'splake', 'steelhead', 'redband', 'grayling',
           'cutthroat', 'rbt', 'goldbow', 'brownbow', 'cutbow'])) return 'Trout';
  if (has(['catfish', 'bullhead', 'madtom', 'stonecat'])) return 'Catfish';
  if (has(['pike', 'muskellunge', 'musky', 'muskie', 'pickerel'])) return 'Pike & Muskie';
  if (has(['walleye', 'sauger', 'saugeye', 'perch'])) return 'Walleye & Perch';
  if (has(['bass', 'wiper', 'largemouth', 'smallmouth', 'striped', 'stb'])) return 'Bass';
  if (has(['bluegill', 'sunfish', 'pumpkinseed', 'redear', 'warmouth', 'bream',
           'longear', 'shellcracker', 'panfish', 'gsf', 'blg'])) return 'Panfish';
  if (has(['carp', 'buffalo', 'sucker', 'drum', 'bowfin', 'gar', 'burbot', 'whitefish',
           'cisco', 'chub', 'sturgeon', 'paddlefish', 'tench', 'goldfish', 'shad',
           'herring', 'minnow', 'dace', 'sculpin', 'goldeye', 'quillback',
           'shiner', 'smelt', 'stickleback', 'lamprey'])) return 'Carp & Rough Fish';
  return 'Other';
};

// Set of filter categories present at a lake (cached on the lake object).
var lakeCategories = function(lk) {
  if (lk._cats) return lk._cats;
  var set = {};
  var sp = lk.species || [];
  for (var i = 0; i < sp.length; i++) { set[speciesCategory(sp[i])] = true; }
  lk._cats = set;
  return set;
};

var toggleSpeciesMenu = function() {
  var menu = document.getElementById('species_menu');
  if (menu) menu.classList.toggle('open');
};

var updateSpeciesToggleLabel = function() {
  var typeSel = document.getElementById('type_filter');
  var type = typeSel ? typeSel.value : 'any';
  var checked = document.querySelectorAll('#species_menu input[type=checkbox]:checked');
  var label = document.getElementById('species_toggle_label');
  if (!label) return;
  if (type === 'any')          label.textContent = 'Any Species';
  else if (checked.length === 0) label.textContent = 'All ' + type;
  else                          label.textContent = checked.length + ' selected';
};

// Lake counts per category, and the distinct species (with lake counts) inside
// each category. Built once from the data; drives both dropdowns.
var categoryCounts = {};
var speciesByCategory = {};

var populateFilters = function(lakes) {
  categoryCounts = {};
  for (var c = 0; c < SPECIES_CATEGORIES.length; c++) { categoryCounts[SPECIES_CATEGORIES[c]] = 0; }

  var speciesInfo = {};   // species name -> { count, cat }
  for (var i = 0; i < lakes.length; i++) {
    var cats = lakeCategories(lakes[i]);
    for (var k in cats) { if (categoryCounts[k] !== undefined) categoryCounts[k]++; }
    var sp = lakes[i].species || [];
    var seen = {};
    for (var s = 0; s < sp.length; s++) {
      var name = sp[s];
      if (seen[name]) continue;   // count each species at most once per lake
      seen[name] = true;
      if (!speciesInfo[name]) speciesInfo[name] = { count: 0, cat: speciesCategory(name) };
      speciesInfo[name].count++;
    }
  }

  speciesByCategory = {};
  for (var nm in speciesInfo) {
    var cat = speciesInfo[nm].cat;
    (speciesByCategory[cat] = speciesByCategory[cat] || []).push({ name: nm, count: speciesInfo[nm].count });
  }
  for (var cc in speciesByCategory) {
    speciesByCategory[cc].sort(function(a, b) { return b.count - a.count; });
  }

  // Fish Types dropdown (single-select): "Any Type" + each non-empty category.
  var typeSel = document.getElementById('type_filter');
  if (typeSel) {
    typeSel.innerHTML = '<option value="any">Any Type</option>';
    for (var c2 = 0; c2 < SPECIES_CATEGORIES.length; c2++) {
      var t = SPECIES_CATEGORIES[c2];
      if (!categoryCounts[t]) continue;   // skip empty categories
      var opt = document.createElement('option');
      opt.value = t;
      opt.textContent = t + ' (' + categoryCounts[t] + ')';
      typeSel.appendChild(opt);
    }
  }
  populateSpecificSpecies();
}

// Fill the "Specific Species" dropdown with the species inside the selected
// type. Disabled while "Any Type" is selected.
var populateSpecificSpecies = function() {
  var typeSel = document.getElementById('type_filter');
  var type = typeSel ? typeSel.value : 'any';
  var menu = document.getElementById('species_menu');
  var toggle = document.getElementById('species_toggle');
  if (!menu || !toggle) return;
  menu.innerHTML = '';
  menu.classList.remove('open');

  if (type === 'any') {
    toggle.disabled = true;
    updateSpeciesToggleLabel();
    return;
  }
  toggle.disabled = false;
  var list = speciesByCategory[type] || [];
  for (var i = 0; i < list.length; i++) {
    var row = document.createElement('label');
    row.className = 'dropdown-item';
    row.innerHTML = '<input type="checkbox" value="' + list[i].name + '" onchange="updateMarkers()"> ' +
      '<span>' + list[i].name + '</span><span class="cat-count">' + list[i].count + '</span>';
    menu.appendChild(row);
  }
  updateSpeciesToggleLabel();
}

// Changing the type resets the specific-species picker, then re-filters.
var onTypeChange = function() {
  populateSpecificSpecies();
  updateMarkers();
}

var featureFor = function(lk) {
  return { type: 'Feature', properties: lk,
           geometry: { type: 'Point', coordinates: [lk.lon, lk.lat] } };
};

var clusterIcon = function(count) {
  var size = count < 100 ? 34 : (count < 1000 ? 42 : 52);
  var label = count < 1000 ? count : (Math.round(count / 100) / 10) + 'k';
  // Color by cluster size (green -> yellow -> orange -> red), like the old
  // markercluster palette; dark text on the light tiers for readability.
  var bg, fg = '#1f2937';
  if (count < 50)        { bg = 'rgba(110, 204, 57, 0.85)'; }
  else if (count < 250)  { bg = 'rgba(240, 194, 12, 0.85)'; }
  else if (count < 1000) { bg = 'rgba(241, 128, 23, 0.90)'; fg = '#fff'; }
  else                   { bg = 'rgba(224, 68, 47, 0.90)';  fg = '#fff'; }
  return L.divIcon({
    html: '<div class="cluster-icon" style="background:' + bg + ';color:' + fg + '">' +
          '<span>' + label + '</span></div>',
    className: '', iconSize: [size, size]
  });
};

// Render only the clusters/markers within the current viewport + zoom.
// Supercluster returns a few hundred features at most, so this stays fast
// no matter how many total lakes there are.
var renderClusters = function() {
  if (!superIndex || !markerLayer) return;
  var b = mymap.getBounds();
  var bbox = [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()];
  var clusters = superIndex.getClusters(bbox, Math.round(mymap.getZoom()));
  markerLayer.clearLayers();

  for (var i = 0; i < clusters.length; i++) {
    var c = clusters[i];
    var lat = c.geometry.coordinates[1], lon = c.geometry.coordinates[0];

    if (c.properties.cluster) {
      (function(cid, clat, clon, count) {
        var m = L.marker([clat, clon], { icon: clusterIcon(count) });
        m.on('click', function() {
          var z = superIndex.getClusterExpansionZoom(cid);
          mymap.setView([clat, clon], Math.min(z, 16));
        });
        markerLayer.addLayer(m);
      })(c.properties.cluster_id, lat, lon, c.properties.point_count);
    } else {
      (function(lk, plat, plon) {
        var m = L.marker([plat, plon], { icon: defaultIcon });
        // Open the popup on the MAP, not bound to this marker. On moveend
        // (e.g. Leaflet auto-panning a big popup into view) renderClusters
        // rebuilds the marker layer; a marker-bound popup would be destroyed
        // and vanish. A map-owned popup survives the re-render. maxHeight
        // keeps long popups scrollable instead of overflowing the map.
        m.on('click', function() {
          L.popup({ maxHeight: 260, autoPanPadding: [30, 40] })
            .setLatLng([plat, plon])
            .setContent(lake2marker_html(lk))
            .openOn(mymap);
        });
        markerLayer.addLayer(m);
      })(c.properties, lat, lon);
    }
  }
}

var lake2marker_html = function(lk) {
  var html = '<div class="popup-custom">';
  
  if (lk['url']) {
      html += '<a target="_blank" href="'+lk['url']+'" class="popup-title">'+lk['name']+'</a>';
  } else {
      html += '<div class="popup-title">'+lk['name']+'</div>';
  }
  
  html += '<div class="popup-row"><span class="popup-label">State</span><span class="popup-value">'+lk['state']+'</span></div>';
  
  if (lk['county']) {
      html += '<div class="popup-row"><span class="popup-label">County</span><span class="popup-value">'+lk['county']+'</span></div>';
  }
  if (lk['elevation']) {
      html += '<div class="popup-row"><span class="popup-label">Elevation</span><span class="popup-value">'+String(Math.round(lk['elevation']))+' ft</span></div>';
  }
  if (lk['area']) {
      html += '<div class="popup-row"><span class="popup-label">Size</span><span class="popup-value">'+String(lk['area'])+'</span></div>';
  }
  if (lk['description']) {
      html += '<div style="margin-top: 8px; font-size: 0.85rem; color: #64748b; line-height: 1.4; border-top: 1px solid #e2e8f0; padding-top: 8px;">'+lk['description']+'</div>';
  }
  
  if (lk['species'] && lk['species'].length > 0) {
    html += '<div class="popup-species">';
    html += '<div class="popup-label" style="margin-bottom: 4px;">Species:</div>';
    for (var i = 0; i < lk['species'].length; i++) {
      html += '<span class="species-tag">' + lk['species'][i] + '</span>';
    }
    html += '</div>';
  }
  
  html += '</div>';
  return html;
}

var getFilterFunction = function() {
  // Name Search
  var search_filter_value = document.getElementById('search_filter') ? document.getElementById('search_filter').value.toLowerCase().trim() : '';
  var text_search_filter = function(lk) {
    if (search_filter_value === '') return true;
    return (lk['name'] && lk['name'].toLowerCase().includes(search_filter_value));
  }
  
  // Fish Type (single-select) + optional Specific Species (multi-select).
  // Any Type            -> no constraint.
  // A type, no species  -> lake must contain that type.
  // A type + species    -> lake must contain one of the checked species.
  var typeSel = document.getElementById('type_filter');
  var selectedType = typeSel ? typeSel.value : 'any';
  var checkedBoxes = document.querySelectorAll('#species_menu input[type=checkbox]:checked');
  var checkedSpecies = {};
  for (var cb = 0; cb < checkedBoxes.length; cb++) { checkedSpecies[checkedBoxes[cb].value] = true; }
  var hasCheckedSpecies = checkedBoxes.length > 0;
  var species_filter;
  if (selectedType === 'any') {
    species_filter = function(lk) { return true; }
  } else if (!hasCheckedSpecies) {
    species_filter = function(lk) { return !!lakeCategories(lk)[selectedType]; }
  } else {
    species_filter = function(lk) {
      var sp = lk.species || [];
      for (var i = 0; i < sp.length; i++) { if (checkedSpecies[sp[i]]) return true; }
      return false;
    }
  }
  
  // Size
  var size_filter_value = document.getElementById('size_filter') ? document.getElementById('size_filter').value : 'any';
  var size_filter;
  if (size_filter_value === 'any') {
    size_filter = function(el){return true;}
  } else if (size_filter_value === '<5') {
    size_filter = function(el){return el && parseFloat(el) < 5;}
  } else if (size_filter_value === '5-10') {
    size_filter = function(el){if (!el) return false; var val = parseFloat(el); return (5 <= val && val <= 10);}
  } else if (size_filter_value === '>10') {
    size_filter = function(el){return el && 10 < parseFloat(el);}
  }
  
  // Elevation
  var elev_filter_value = document.getElementById('elevation_filter') ? document.getElementById('elevation_filter').value : 'any';
  var elev_filter;
  if (elev_filter_value === 'any') {
    elev_filter = function(el){return true;}
  } else if (elev_filter_value === '<3000') {
    elev_filter = function(el){return el && parseFloat(el) < 3000;}
  } else if (elev_filter_value === '3000-5000') {
    elev_filter = function(el){if (!el) return false; var val = parseFloat(el); return (3000 <= val && val <= 5000);}
  } else if (elev_filter_value === '>5000') {
    elev_filter = function(el){return el && 5000 < parseFloat(el);}
  }

  return function(lk) {
    return text_search_filter(lk) && species_filter(lk) && size_filter(lk.area) && elev_filter(lk.elevation);
  }
}

// Rebuild the supercluster index from the filtered lakes, then re-render the
// current view. Called on initial load and whenever a filter changes.
var updateMarkers = function() {
  updateSpeciesToggleLabel();
  var filter_func = getFilterFunction();
  var features = [];
  for (var i = 0; i < allLakes.length; i++) {
    if (filter_func(allLakes[i])) features.push(featureFor(allLakes[i]));
  }
  superIndex = new Supercluster({ radius: 60, maxZoom: 16 }).load(features);
  renderClusters();
}

var showTimestamp = function(timestamp) {
  var timestamp_div = document.getElementById("last_update_timestamp");
  if (timestamp_div) {
    timestamp_div.innerHTML = "The data was last updated at: " + timestamp;
  }
}

// Close the species dropdown when clicking outside of it.
document.addEventListener('click', function(e) {
  var dd = document.getElementById('species_dropdown');
  var menu = document.getElementById('species_menu');
  if (dd && menu && !dd.contains(e.target)) menu.classList.remove('open');
});

initializeMap();
downloadDataAndRender("data/all_states.json");