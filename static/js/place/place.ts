/**
 * Copyright 2020 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import React from "react";
import ReactDOM from "react-dom";
import axios from "axios";

import { ChildPlace } from "./child_places_menu";
import { MainPane } from "./main";
import { Menu } from "./topic_menu";
import { ParentPlace } from "./parent_breadcrumbs";
import { PlaceHighlight } from "./place_highlight";
import { PageSubtitle } from "./page_subtitle";
import { isPlaceInUsa } from "./util";
import { initSearchAutocomplete } from "./search";

import { PageData } from "./types";

let yScrollLimit = 0; // window scroll position to start fixing the sidebar
let sidebarTopMax = 0; // Max top position for the sidebar, relative to #sidebar-outer.
const Y_SCROLL_WINDOW_BREAKPOINT = 992; // Only trigger fixed sidebar beyond this window width.
const Y_SCROLL_MARGIN = 100; // Margin to apply to the fixed sidebar top.

window.onload = () => {
  const urlParams = new URLSearchParams(window.location.search);
  const dcid = urlParams.get("dcid");
  renderPage(dcid);
  initSearchAutocomplete();
  updatePageLayoutState();
  maybeToggleFixedSidebar();
  window.onresize = maybeToggleFixedSidebar;
};

/**
 *  Make adjustments to sidebar scroll state based on the content.
 */
function updatePageLayoutState(): void {
  yScrollLimit = document.getElementById("main-pane").offsetTop;
  document.getElementById("sidebar-top-spacer").style.height =
    yScrollLimit + "px";
  const sidebarOuterHeight = document.getElementById("sidebar-outer")
    .offsetHeight;
  const sidebarRegionHeight = document.getElementById("sidebar-region")
    .offsetHeight;
  sidebarTopMax = sidebarOuterHeight - sidebarRegionHeight - Y_SCROLL_MARGIN;
}

/**
 *  Toggle fixed sidebar based on window width.
 */
function maybeToggleFixedSidebar() {
  if (window.innerWidth < Y_SCROLL_WINDOW_BREAKPOINT) {
    document.removeEventListener("scroll", adjustMenuPosition);
    return;
  }
  document.addEventListener("scroll", adjustMenuPosition);
}

/**
 * Update fixed sidebar based on the window scroll.
 */
function adjustMenuPosition() {
  const topicsEl = document.getElementById("sidebar-region");
  if (window.scrollY > yScrollLimit) {
    const calcTop = window.scrollY - yScrollLimit - Y_SCROLL_MARGIN;
    if (calcTop > sidebarTopMax) {
      topicsEl.style.top = sidebarTopMax + "px";
      return;
    }
    topicsEl.style.top = calcTop + "px";
  } else {
    topicsEl.style.top = "0";
  }
}

/**
 * Get the geo json info for choropleth charts.
 */
async function getGeoJsonData(dcid: string, placeType: string) {
  if (placeType == "Country" || placeType == "State") {
    return axios.get("/api/chart/geojson/" + dcid).then((resp) => {
      return resp.data;
    });
  } else {
    return new Promise((resolve) => {
      resolve({});
    });
  }
}

/**
 * Get the stat var data for choropleth charts.
 */
async function getChoroplethData(dcid: string, placeType: string) {
  if (placeType == "Country" || placeType == "State") {
    return axios.get("/api/chart/choroplethdata/" + dcid).then((resp) => {
      return resp.data;
    });
  } else {
    return new Promise((resolve) => {
      resolve({});
    });
  }
}

/**
 * Get the landing page data
 */
async function getLandingPageData(dcid: string): Promise<PageData> {
  return axios.get("/api/landingpage/data/" + dcid).then((resp) => {
    return resp.data;
  });
}

function renderPage(dcid: string) {
  const urlParams = new URLSearchParams(window.location.search);
  // Get topic and render menu.
  let topic = urlParams.get("topic") || "Overview";
  const placeName = document.getElementById("place-name").dataset.pn;
  const placeType = document.getElementById("place-type").dataset.pt;
  const landingPagePromise = getLandingPageData(dcid);
  const chartGeoJsonPromise = getGeoJsonData(dcid, placeType);
  const choroplethDataPromise = getChoroplethData(dcid, placeType);

  Promise.all([
    landingPagePromise,
    chartGeoJsonPromise,
    choroplethDataPromise,
  ]).then(([landingPageData, geoJsonData, choroplethData]) => {
    const data: PageData = landingPageData;
    const isUsaPlace = isPlaceInUsa(dcid, data.parentPlaces);
    if (Object.keys(data.pageChart).length == 1) {
      topic = "Overview";
    }
    ReactDOM.render(
      React.createElement(Menu, {
        pageChart: data.pageChart,
        dcid,
        topic,
      }),
      document.getElementById("topics")
    );

    // Earth has no parent places.
    if (data.parentPlaces.length > 0) {
      ReactDOM.render(
        React.createElement(ParentPlace, {
          names: data.names,
          parentPlaces: data.parentPlaces,
          placeType,
        }),
        document.getElementById("place-type")
      );
    }
    ReactDOM.render(
      React.createElement(PlaceHighlight, {
        dcid,
        highlight: data.highlight,
      }),
      document.getElementById("place-highlight")
    );

    // Readjust sidebar based on parent places.
    updatePageLayoutState();

    // Display child places alphabetically
    for (const placeType in data.allChildPlaces) {
      data.allChildPlaces[placeType].sort((a, b) =>
        a.name < b.name ? -1 : a.name > b.name ? 1 : 0
      );
    }
    ReactDOM.render(
      React.createElement(ChildPlace, {
        childPlaces: data.allChildPlaces,
        placeName,
      }),
      document.getElementById("child-place")
    );

    ReactDOM.render(
      React.createElement(PageSubtitle, {
        category: topic,
        dcid,
      }),
      document.getElementById("subtitle")
    );

    ReactDOM.render(
      React.createElement(MainPane, {
        category: topic,
        dcid,
        isUsaPlace,
        names: data.names,
        pageChart: data.pageChart,
        placeName,
        placeType,
        geoJsonData,
        choroplethData,
        childPlacesType: data.childPlacesType,
        parentPlaceDcid:
          data.parentPlaces.length > 0 ? data.parentPlaces[0] : null,
      }),
      document.getElementById("main-pane")
    );
  });
}

export { updatePageLayoutState };
