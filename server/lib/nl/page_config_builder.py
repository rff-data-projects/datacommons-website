# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from typing import Dict, List

from server.config.subject_page_pb2 import Block
from server.config.subject_page_pb2 import RankingTileSpec
from server.config.subject_page_pb2 import StatVarSpec
from server.config.subject_page_pb2 import SubjectPageConfig
from server.config.subject_page_pb2 import Tile
from server.lib.nl import utils
import server.lib.nl.constants as constants
import server.lib.nl.descriptions as lib_desc
from server.lib.nl.detection import EventType
from server.lib.nl.detection import Place
from server.lib.nl.detection import RankingType
from server.lib.nl.utterance import ChartOriginType
from server.lib.nl.utterance import ChartSpec
from server.lib.nl.utterance import ChartType
from server.lib.nl.utterance import QueryType
from server.lib.nl.utterance import Utterance


class PageConfigBuilder:

  def __init__(self, uttr):
    self.uttr = uttr
    self.page_config = SubjectPageConfig()

    metadata = self.page_config.metadata
    first_chart = uttr.rankedCharts[0]
    main_place = first_chart.places[0]
    metadata.place_dcid.append(main_place.dcid)
    if (first_chart.chart_type == ChartType.MAP_CHART or
        first_chart.chart_type == ChartType.RANKING_CHART or
        first_chart.chart_type == ChartType.SCATTER_CHART):
      metadata.contained_place_types[main_place.place_type] = \
        first_chart.attr['place_type']

    self.category = self.page_config.categories.add()
    self.block = None
    self.column = None
    self.prev_block_id = -1

    self.ignore_block_id_check = False
    if uttr.query_type == QueryType.RANKING_ACROSS_PLACES:
      self.ignore_block_id_check = True

  # Returns a Block and a Column
  def new_chart(self, attr: Dict) -> any:
    block_id = attr['block_id']
    if block_id != self.prev_block_id or self.ignore_block_id_check:
      if self.block:
        self.category.blocks.append(self.block)
      self.block = Block()
      if attr['title']:
        self.block.title = _decorate_block_title(title=attr['title'],
                                                 chart_origin=attr.get(
                                                     'class', None))
      if attr['description']:
        self.block.description = attr['description']
      self.column = self.block.columns.add()
      self.prev_block_id = block_id
    return self.block, self.column

  def update_sv_spec(self, stat_var_spec_map):
    for sv_key, spec in stat_var_spec_map.items():
      self.category.stat_var_spec[sv_key].CopyFrom(spec)

  def finalize(self) -> SubjectPageConfig:
    if self.block:
      self.category.blocks.append(self.block)
      self.block = None


#
# Given an Utterance, build the final Chart config proto.
#
def build_page_config(
    uttr: Utterance,
    event_config: SubjectPageConfig = None) -> SubjectPageConfig:

  builder = PageConfigBuilder(uttr)

  # Get names of all SVs
  all_svs = set()
  for cspec in uttr.rankedCharts:
    all_svs.update(cspec.svs)
  all_svs = list(all_svs)
  sv2name = utils.get_sv_name(all_svs)
  # TODO: use this when setting sv spec for map and ranking charts
  sv2unit = utils.get_sv_unit(all_svs)

  # Get footnotes of all SVs
  sv2footnote = utils.get_sv_footnote(all_svs)

  # Add a human answer to the query
  # try:
  #   desc = lib_desc.build_category_description(uttr, sv2name)
  #   if desc:
  #     builder.category.description = desc
  # except Exception as err:
  #   utils.update_counter(uttr.counters, 'failed_category_description_build',
  #                        str(err))
  #   logging.warning("Error building category description: %s", str(err))

  # Build chart blocks
  for cspec in uttr.rankedCharts:
    if not cspec.places:
      continue
    stat_var_spec_map = {}

    # Call per-chart handlers.
    if cspec.chart_type == ChartType.PLACE_OVERVIEW:
      place = cspec.places[0]
      block, column = builder.new_chart(cspec.attr)
      block.title = place.name
      _place_overview_block(column)

    elif cspec.chart_type == ChartType.TIMELINE_CHART:
      _, column = builder.new_chart(cspec.attr)
      if len(cspec.svs) > 1:
        stat_var_spec_map = _single_place_multiple_var_timeline_block(
            column, cspec.places[0], cspec.svs, sv2name, sv2unit, cspec.attr)
      else:
        stat_var_spec_map = _single_place_single_var_timeline_block(
            column, cspec.places[0], cspec.svs[0], sv2name, sv2unit, cspec.attr)

    elif cspec.chart_type == ChartType.BAR_CHART:
      _, column = builder.new_chart(cspec.attr)
      stat_var_spec_map = _multiple_place_bar_block(column, cspec.places,
                                                    cspec.svs, sv2name, sv2unit,
                                                    cspec.attr)

    elif cspec.chart_type == ChartType.MAP_CHART:
      if not _is_map_or_ranking_compatible(cspec):
        continue
      for sv in cspec.svs:
        _, column = builder.new_chart(cspec.attr)
        stat_var_spec_map.update(
            _map_chart_block(column, cspec.places[0], sv, sv2name, cspec.attr))

    elif cspec.chart_type == ChartType.RANKING_CHART:
      if not _is_map_or_ranking_compatible(cspec):
        continue
      pri_place = cspec.places[0]

      if cspec.attr['source_topic'] == 'dc/topic/ProjectedClimateExtremes':
        stat_var_spec_map.update(
            _ranking_chart_block_climate_extremes(builder, pri_place, cspec.svs,
                                                  sv2name, sv2footnote,
                                                  cspec.attr))
      else:

        for idx, sv in enumerate(cspec.svs):
          block, column = builder.new_chart(cspec.attr)
          block.footnote = sv2footnote[sv]

          if idx > 0 and cspec.attr['source_topic']:
            # For a peer-group of SVs, set the title and description only once.
            builder.block.title = ''
            builder.block.description = ''
          elif not builder.block.title and builder.ignore_block_id_check:
            # For the first SV, if title weren't already set, set it to
            # the SV name.
            builder.block.title = sv2name[sv]
            # TODO: Maybe insert sv description here.

          main_title = builder.block.title
          chart_origin = cspec.attr.get('class', None)
          builder.block.title = _decorate_block_title(title=main_title,
                                                      chart_origin=chart_origin)
          stat_var_spec_map.update(
              _ranking_chart_block_nopc(column, pri_place, sv, sv2name,
                                        cspec.attr))
          if cspec.attr['include_percapita'] and _should_add_percapita(sv):
            if not 'skip_map_for_ranking' in cspec.attr:
              main_title = builder.block.title
              block, column = builder.new_chart(cspec.attr)
              if main_title:
                builder.block.title = _decorate_block_title(
                    title=main_title, chart_origin=chart_origin, do_pc=True)
            stat_var_spec_map.update(
                _ranking_chart_block_pc(column, pri_place, sv, sv2name,
                                        cspec.attr))
    elif cspec.chart_type == ChartType.SCATTER_CHART:
      _, column = builder.new_chart(cspec.attr)
      stat_var_spec_map = _scatter_chart_block(column, cspec.places[0],
                                               cspec.svs, sv2name, cspec.attr)

    elif cspec.chart_type == ChartType.EVENT_CHART and event_config:
      block, column = builder.new_chart(cspec.attr)
      _event_chart_block(builder.page_config.metadata, block, column,
                         cspec.places[0], cspec.event, cspec.attr, event_config)

    builder.update_sv_spec(stat_var_spec_map)

  builder.finalize()
  logging.info(builder.page_config)
  return builder.page_config


def _single_place_single_var_timeline_block(column, place, sv_dcid, sv2name,
                                            sv2unit, attr):
  """A column with two charts, main stat var and per capita"""
  stat_var_spec_map = {}

  title = _decorate_chart_title(title=sv2name[sv_dcid], place=place)

  # Line chart for the stat var
  sv_key = sv_dcid
  tile = Tile(type=Tile.TileType.LINE, title=title, stat_var_key=[sv_key])
  stat_var_spec_map[sv_key] = StatVarSpec(stat_var=sv_dcid,
                                          name=sv2name[sv_dcid],
                                          unit=sv2unit[sv_dcid])
  if 'set_place_override_for_line' in attr:
    tile.place_dcid_override = place.dcid
  column.tiles.append(tile)

  # Line chart for the stat var per capita
  if attr['include_percapita'] and _should_add_percapita(sv_dcid):
    title = _decorate_chart_title(title=sv2name[sv_dcid],
                                  place=place,
                                  do_pc=True)
    sv_key = sv_dcid + '_pc'
    tile = Tile(type=Tile.TileType.LINE, title=title, stat_var_key=[sv_key])
    stat_var_spec_map[sv_key] = StatVarSpec(stat_var=sv_dcid,
                                            name=sv2name[sv_dcid],
                                            denom="Count_Person",
                                            scaling=100,
                                            unit="%")
    column.tiles.append(tile)
  return stat_var_spec_map


def _single_place_multiple_var_timeline_block(column, place, svs, sv2name,
                                              sv2unit, attr):
  """A column with two chart, all stat vars and per capita"""
  stat_var_spec_map = {}

  orig_title = attr['title'] if attr[
      'title'] else "Compared with Other Variables"
  title = _decorate_chart_title(title=orig_title, place=place)

  # Line chart for the stat var
  tile = Tile(type=Tile.TileType.LINE, title=title, stat_var_key=[])
  for sv in svs:
    sv_key = sv
    tile.stat_var_key.append(sv_key)
    stat_var_spec_map[sv_key] = StatVarSpec(stat_var=sv,
                                            name=sv2name[sv],
                                            unit=sv2unit[sv])
  column.tiles.append(tile)

  # Line chart for the stat var per capita
  svs_pc = list(filter(lambda x: _should_add_percapita(x), svs))
  if attr['include_percapita'] and len(svs_pc) > 0:
    title = _decorate_chart_title(title=orig_title, place=place, do_pc=True)
    tile = Tile(type=Tile.TileType.LINE, title=title)
    for sv in svs_pc:
      sv_key = sv + '_pc'
      tile.stat_var_key.append(sv_key)
      stat_var_spec_map[sv_key] = StatVarSpec(stat_var=sv,
                                              name=sv2name[sv],
                                              denom="Count_Person",
                                              scaling=100,
                                              unit="%")
    column.tiles.append(tile)

  return stat_var_spec_map


def _multiple_place_bar_block(column, places: List[Place], svs: List[str],
                              sv2name, sv2unit, attr):
  """A column with two charts, main stat var and per capita"""
  stat_var_spec_map = {}

  if attr['title']:
    # This happens in the case of Topics
    orig_title = attr['title']
  elif len(svs) > 1:
    # This suggests we are comparing against SV peers from SV extension
    orig_title = 'Compared with Other Variables'
  else:
    # This is the case of multiple places for a single SV
    orig_title = sv2name[svs[0]]

  if len(places) == 1:
    title = _decorate_chart_title(title=orig_title, place=places[0])
    pc_title = _decorate_chart_title(title=orig_title,
                                     place=places[0],
                                     do_pc=True)
  else:
    title = orig_title
    pc_title = _decorate_chart_title(title=orig_title, place=None, do_pc=True)

  # Total
  tile = Tile(type=Tile.TileType.BAR,
              title=title,
              comparison_places=[x.dcid for x in places])
  for sv in svs:
    sv_key = sv + "_multiple_place_bar_block"
    tile.stat_var_key.append(sv_key)
    stat_var_spec_map[sv_key] = StatVarSpec(stat_var=sv,
                                            name=sv2name[sv],
                                            unit=sv2unit[sv])

  column.tiles.append(tile)
  # Per Capita
  svs_pc = list(filter(lambda x: _should_add_percapita(x), svs))
  if attr['include_percapita'] and len(svs_pc) > 0:
    tile = Tile(type=Tile.TileType.BAR,
                title=pc_title,
                comparison_places=[x.dcid for x in places])
    for sv in svs_pc:
      sv_key = sv + "_multiple_place_bar_block_pc"
      tile.stat_var_key.append(sv_key)
      stat_var_spec_map[sv_key] = StatVarSpec(stat_var=sv,
                                              denom="Count_Person",
                                              name=sv2name[sv],
                                              scaling=100,
                                              unit="%")

    column.tiles.append(tile)
  return stat_var_spec_map


def _map_chart_block(column, place: Place, pri_sv: str, sv2name, attr):
  svs_map = _map_chart_block_nopc(column, place, pri_sv, sv2name, attr)
  if attr['include_percapita'] and _should_add_percapita(pri_sv):
    svs_map.update(_map_chart_block_pc(column, place, pri_sv, sv2name, attr))
  return svs_map


def _map_chart_block_nopc(column, place: Place, pri_sv: str, sv2name: Dict,
                          attr: Dict):
  # The main tile
  tile = column.tiles.add()
  tile.stat_var_key.append(pri_sv)
  tile.type = Tile.TileType.MAP
  tile.title = _decorate_chart_title(title=sv2name[pri_sv],
                                     place=place,
                                     do_pc=False,
                                     child_type=attr.get('place_type', ''))

  stat_var_spec_map = {}
  stat_var_spec_map[pri_sv] = StatVarSpec(stat_var=pri_sv, name=sv2name[pri_sv])
  return stat_var_spec_map


def _map_chart_block_pc(column, place: Place, pri_sv: str, sv2name: Dict,
                        attr: Dict):
  tile = column.tiles.add()
  sv_key = pri_sv + "_pc"
  tile.stat_var_key.append(sv_key)
  tile.type = Tile.TileType.MAP
  tile.title = _decorate_chart_title(title=sv2name[pri_sv],
                                     place=place,
                                     do_pc=True,
                                     child_type=attr.get('place_type', ''))

  stat_var_spec_map = {}
  stat_var_spec_map[sv_key] = StatVarSpec(stat_var=pri_sv,
                                          denom="Count_Person",
                                          name=sv2name[pri_sv],
                                          scaling=100,
                                          unit="%")
  return stat_var_spec_map


def _set_ranking_tile_spec(ranking_types: List[RankingType], pri_sv: str,
                           ranking_tile_spec: RankingTileSpec):
  ranking_tile_spec.ranking_count = 10
  # TODO: Add more robust checks.
  if "CriminalActivities" in pri_sv:
    # first check if "best" or "worst"
    if RankingType.BEST in ranking_types:
      ranking_tile_spec.show_lowest = True
    elif RankingType.WORST in ranking_types:
      ranking_tile_spec.show_highest = True
    else:
      # otherwise, render normally
      if RankingType.HIGH in ranking_types:
        ranking_tile_spec.show_highest = True
      if RankingType.LOW in ranking_types:
        ranking_tile_spec.show_lowest = True
  else:
    if RankingType.HIGH in ranking_types:
      ranking_tile_spec.show_highest = True
    elif RankingType.LOW in ranking_types:
      ranking_tile_spec.show_lowest = True
    elif RankingType.EXTREME in ranking_types:
      if _does_extreme_mean_low(pri_sv):
        ranking_tile_spec.show_lowest = True
      else:
        ranking_tile_spec.show_highest = True


def _does_extreme_mean_low(sv: str) -> bool:
  _MIN_SV_PATTERNS = ['ProjectedMin', 'Min_Temperature']
  for p in _MIN_SV_PATTERNS:
    if p in sv:
      return True
  return False


def _ranking_chart_block_climate_extremes(builder, pri_place: Place,
                                          pri_svs: List[str], sv2name: Dict,
                                          sv2footnote: Dict, attr: Dict):
  footnotes = []
  stat_var_spec_map = {}

  # Add the main ranking tile
  ranking_block, ranking_column = builder.new_chart(attr)
  ranking_tile = ranking_column.tiles.add()
  ranking_tile.type = Tile.TileType.RANKING

  for _, sv in enumerate(pri_svs):
    _set_ranking_tile_spec(attr['ranking_types'], '',
                           ranking_tile.ranking_tile_spec)
    sv_key = "ranking-" + sv
    ranking_tile.stat_var_key.append(sv_key)
    stat_var_spec_map[sv_key] = StatVarSpec(
        stat_var=sv, name=utils.SV_DISPLAY_SHORT_NAME[sv])
    footnotes.append(sv2footnote[sv])

  ranking_tile.title = ranking_block.title
  ranking_tile.ranking_tile_spec.show_multi_column = True

  # Add the map block
  map_block, map_column = builder.new_chart(attr)

  for _, sv in enumerate(pri_svs):
    if len(map_column.tiles):
      map_column = map_block.columns.add()
    stat_var_spec_map.update(
        _map_chart_block_nopc(map_column, pri_place, sv, sv2name, attr))
    map_column.tiles[0].title = sv2name[
        sv]  # override decorated title (too long).

  map_block.title = ''
  map_block.description = ''
  map_block.footnote = '\n\n'.join(footnotes)

  return stat_var_spec_map


def _ranking_chart_block_nopc(column, pri_place: Place, pri_sv: str,
                              sv2name: Dict, attr: Dict):
  # The main tile
  tile = column.tiles.add()
  tile.stat_var_key.append(pri_sv)
  tile.type = Tile.TileType.RANKING
  _set_ranking_tile_spec(attr['ranking_types'], '', tile.ranking_tile_spec)
  tile.title = _decorate_chart_title(title=sv2name[pri_sv],
                                     place=pri_place,
                                     do_pc=False,
                                     child_type=attr.get('place_type', ''))

  stat_var_spec_map = {}
  stat_var_spec_map[pri_sv] = StatVarSpec(stat_var=pri_sv, name=sv2name[pri_sv])

  if not 'skip_map_for_ranking' in attr:
    # Also add a map chart.
    stat_var_spec_map.update(
        _map_chart_block_nopc(column, pri_place, pri_sv, sv2name, attr))

  return stat_var_spec_map


def _ranking_chart_block_pc(column, pri_place: Place, pri_sv: str,
                            sv2name: Dict, attr: Dict):
  # The per capita tile
  tile = column.tiles.add()
  sv_key = pri_sv + "_pc"
  tile.stat_var_key.append(sv_key)
  tile.type = Tile.TileType.RANKING
  _set_ranking_tile_spec(attr['ranking_types'], pri_sv, tile.ranking_tile_spec)
  tile.title = _decorate_chart_title(title=sv2name[pri_sv],
                                     place=pri_place,
                                     do_pc=True,
                                     child_type=attr.get('place_type', ''))

  stat_var_spec_map = {}
  stat_var_spec_map[sv_key] = StatVarSpec(stat_var=pri_sv,
                                          denom="Count_Person",
                                          name=sv2name[pri_sv],
                                          scaling=100,
                                          unit="%")

  if pri_sv in constants.ADDITIONAL_DENOMINATOR_VARS:
    denom_sv, name_suffix = constants.ADDITIONAL_DENOMINATOR_VARS[pri_sv]
    tile = column.tiles.add()
    sv_key = pri_sv + "_" + denom_sv
    tile.stat_var_key.append(sv_key)
    tile.type = Tile.TileType.RANKING
    _set_ranking_tile_spec(attr['ranking_types'], pri_sv,
                           tile.ranking_tile_spec)
    sv_title = sv2name[pri_sv] + " " + name_suffix
    tile.title = _decorate_chart_title(title=sv_title,
                                       place=pri_place,
                                       do_pc=False,
                                       child_type=attr.get('place_type', ''))

    stat_var_spec_map[sv_key] = StatVarSpec(stat_var=pri_sv,
                                            denom=denom_sv,
                                            name=sv_title)

  # TODO: Maybe add ADDITIONAL_DENOMINATOR_VARS to map too
  if not 'skip_map_for_ranking' in attr:
    # Also add a map chart.
    stat_var_spec_map.update(
        _map_chart_block_pc(column, pri_place, pri_sv, sv2name, attr))

  return stat_var_spec_map


def _scatter_chart_block(column, pri_place: Place, sv_pair: List[str], sv2name,
                         attr: Dict):
  assert len(sv_pair) == 2

  sv_names = [sv2name[sv_pair[0]], sv2name[sv_pair[1]]]
  sv_key_pair = [sv_pair[0] + '_scatter', sv_pair[1] + '_scatter']

  change_to_pc = [False, False]
  if _is_sv_percapita(sv_names[0]):
    if not _is_sv_percapita(sv_names[1]):
      change_to_pc[1] = True
      sv_names[1] += " Per Capita"
  if _is_sv_percapita(sv_names[1]):
    if not _is_sv_percapita(sv_names[0]):
      change_to_pc[0] = True
      sv_names[0] += " Per Capita"

  stat_var_spec_map = {}
  for i in range(2):
    if change_to_pc[i]:
      stat_var_spec_map[sv_key_pair[i]] = StatVarSpec(stat_var=sv_pair[i],
                                                      name=sv_names[i],
                                                      denom='Count_Person',
                                                      unit='%',
                                                      scaling=100)
    else:
      stat_var_spec_map[sv_key_pair[i]] = StatVarSpec(stat_var=sv_pair[i],
                                                      name=sv_names[i])

  # add a scatter config
  tile = column.tiles.add()
  tile.stat_var_key.extend(sv_key_pair)
  tile.type = Tile.TileType.SCATTER
  tile.title = _decorate_chart_title(title=f"{sv_names[0]} vs. {sv_names[1]}",
                                     place=pri_place,
                                     do_pc=False,
                                     child_type=attr.get('place_type', ''))
  tile.scatter_tile_spec.highlight_top_right = True

  return stat_var_spec_map


def _place_overview_block(column):
  tile = column.tiles.add()
  tile.type = Tile.TileType.PLACE_OVERVIEW


def _event_chart_block(metadata, block, column, place: Place,
                       event_type: EventType, attr, event_config):

  # Map EventType to config key.
  event_id = constants.EVENT_TYPE_TO_CONFIG_KEY[event_type]

  if event_id == 'earthquake':
    eq_val = metadata.event_type_spec[event_id]
    eq_val.id = event_id
    eq_val.name = 'Earthquake'
    eq_val.event_type_dcids.append('EarthquakeEvent')
    eq_val.color = '#930000'
    sev_filter = eq_val.default_severity_filter
    sev_filter.prop = 'magnitude'
    sev_filter.display_name = 'Magnitude'
    sev_filter.upper_limit = 10
    sev_filter.lower_limit = 6
  elif event_id in event_config.metadata.event_type_spec:
    metadata.event_type_spec[event_id].CopyFrom(
        event_config.metadata.event_type_spec[event_id])
  else:
    logging.error('ID not found in event_type_spec: %s', event_id)
    return

  if not place.place_type in metadata.contained_place_types:
    metadata.contained_place_types[
        place.place_type] = constants.CHILD_PLACES_TYPES.get(
            place.place_type, "Place")
  event_name = metadata.event_type_spec[event_id].name
  if event_type in constants.EVENT_TYPE_TO_DISPLAY_NAME:
    event_name = constants.EVENT_TYPE_TO_DISPLAY_NAME[event_type]
  event_title = _decorate_chart_title(title=event_name, place=place)
  block.title = event_title
  block.type = Block.DISASTER_EVENT

  if (RankingType.HIGH in attr['ranking_types'] or
      RankingType.EXTREME in attr['ranking_types']):
    tile = column.tiles.add()
    # TODO: Handle top event for earthquakes
    if not _maybe_copy_top_event(event_id, block, tile, event_config):
      tile.type = Tile.TOP_EVENT
      tile.title = event_title
      top_event = tile.top_event_tile_spec
      top_event.event_type_key = event_id
      top_event.display_prop.append('name')
      top_event.show_start_date = True
      top_event.show_end_date = True
    else:
      tile.title = _decorate_chart_title(title=tile.title, place=place)
    tile = block.columns.add().tiles.add()
  else:
    tile = column.tiles.add()

  tile.type = Tile.DISASTER_EVENT_MAP
  tile.disaster_event_map_tile_spec.point_event_type_key.append(event_id)
  tile.title = event_title


def _maybe_copy_top_event(event_id, block, tile, event_config):
  # Find a TOP_EVENT tile with given key, because it has
  # additional curated content.
  for c in event_config.categories:
    for b in c.blocks:
      for col in b.columns:
        for t in col.tiles:
          if t.type == Tile.TOP_EVENT and t.top_event_tile_spec.event_type_key == event_id:
            tile.CopyFrom(t)
            block.title = b.title
            block.description = b.description
            return True

  return False


def _is_map_or_ranking_compatible(cspec: ChartSpec) -> bool:
  if len(cspec.places) > 1:
    logging.error('Incompatible MAP/RANKING: too-many-places ', cspec)
    return False
  if 'place_type' not in cspec.attr or not cspec.attr['place_type']:
    logging.error('Incompatible MAP/RANKING: missing-place-type', cspec)
    return False
  return True


def _decorate_block_title(title: str,
                          do_pc: bool = False,
                          chart_origin: ChartOriginType = None) -> str:
  if not title:
    return ''

  if do_pc:
    title = 'Per Capita ' + title

  if chart_origin == ChartOriginType.SECONDARY_CHART:
    title = 'Related: ' + title

  return title


def _decorate_chart_title(title: str,
                          place: Place,
                          do_pc: bool = False,
                          child_type: str = '') -> str:
  if not title:
    return ''

  # Apply in order: place or place+containment, per-capita, related prefix
  if place and place.name:
    if child_type:
      title = title + ' in ' + utils.pluralize_place_type(
          child_type) + ' of ' + place.name
    else:
      title = title + ' in ' + place.name

  if do_pc:
    title = 'Per Capita ' + title

  return title


#
# Per-capita handling
#

_SV_PARTIAL_DCID_NO_PC = [
    'Temperature', 'Precipitation', "BarometricPressure", "CloudCover",
    "PrecipitableWater", "Rainfall", "Snowfall", "Visibility", "WindSpeed",
    "ConsecutiveDryDays", "Percent", "Area_", "Median_", "LifeExpectancy_",
    "AsFractionOf", "AsAFractionOfCount"
]

_SV_FULL_DCID_NO_PC = ["Count_Person"]


def _should_add_percapita(sv_dcid: str) -> bool:
  for skip_phrase in _SV_PARTIAL_DCID_NO_PC:
    if skip_phrase in sv_dcid:
      return False
  for skip_sv in _SV_FULL_DCID_NO_PC:
    if skip_sv == sv_dcid:
      return False
  return True


def _is_sv_percapita(sv_name: str) -> bool:
  # Use names for these since some old prevalence dcid's do not use the new naming scheme.
  if "Percentage" in sv_name or "Prevalence" in sv_name:
    return True
  return False
