# Copyright 2021 Google LLC
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
"""Handlers for the OSV web frontend."""

import os

from flask import abort
from flask import Blueprint
from flask import jsonify
from flask import make_response
from flask import render_template
from flask import request

import osv
import rate_limiter
import source_mapper

blueprint = Blueprint('frontend_handlers', __name__)

_BACKEND_ROUTE = '/backend'
_PAGE_SIZE = 16
_PAGE_LOOKAHEAD = 4
_REQUESTS_PER_MIN = 30


def _is_prod():
  return os.getenv('GAE_ENV', '').startswith('standard')


if _is_prod():
  redis_host = os.environ.get('REDISHOST', 'localhost')
  redis_port = int(os.environ.get('REDISPORT', 6379))
  limiter = rate_limiter.RateLimiter(
      redis_host, redis_port, requests_per_min=_REQUESTS_PER_MIN)

  @blueprint.before_request
  def check_rate_limit():
    ip_addr = request.headers.get('X-Appengine-User-Ip', 'unknown')
    if not limiter.check_request(ip_addr):
      abort(429)


@blueprint.before_request
def check_cors_preflight():
  """Handle CORS preflight requests."""
  if request.method != 'OPTIONS':
    return None

  response = make_response()
  response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8080')
  response.headers.add('Access-Control-Allow-Methods', '*')
  response.headers.add('Access-Control-Allow-Headers', '*')
  return response


@blueprint.after_request
def add_cors_headers(response):
  """Add CORS headers."""
  response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8080')
  return response


@blueprint.route('/')
def index():
  """Main page."""
  return render_template('index.html')


@blueprint.route('/v2/')
def index_v2():
  return render_template('home.html')


@blueprint.route('/v2/list')
def list_vulnerabilities():
  """Main page."""
  query = request.args.get('q', '')
  page = int(request.args.get('page', 1))
  ecosystem = request.args.get('ecosystem')
  results = osv_query(query, page, False, ecosystem)

  # Fetch ecosystems by default. As an optimization, skip when rendering page
  # fragments.
  ecosystems = osv_get_ecosystems(
  ) if not request.headers.get('Turbo-Frame') else None

  return render_template(
      'list.html',
      page=page,
      query=query,
      selected_ecosystem=ecosystem,
      ecosystems=ecosystems,
      vulnerabilities=results['items'])


@blueprint.route('/v2/vulnerability/<vuln_id>')
def vulnerability(vuln_id):
  """Vulnerability page."""
  vuln = osv_get_by_id(vuln_id)
  return render_template('vulnerability.html', vulnerability=vuln)


def bug_to_response(bug, detailed=True):
  """Convert a Bug entity to a response object."""
  response = osv.vulnerability_to_dict(bug.to_vulnerability())
  response.update({
      'isFixed': bug.is_fixed,
      'invalid': bug.status == osv.BugStatus.INVALID
  })

  if detailed:
    add_links(response)
    add_source_info(bug, response)
  return response


def add_links(bug):
  """Add VCS links where possible."""

  for entry in bug.get('affected', []):
    for i, affected_range in enumerate(entry.get('ranges', [])):
      affected_range['id'] = i
      if affected_range['type'] != 'GIT':
        continue

      repo_url = affected_range.get('repo')
      if not repo_url:
        continue

      for event in affected_range.get('events', []):
        if event.get('introduced'):
          event['introduced_link'] = _commit_to_link(repo_url,
                                                     event['introduced'])
          continue

        if event.get('fixed'):
          event['fixed_link'] = _commit_to_link(repo_url, event['fixed'])
          continue

        if event.get('limit'):
          event['limit_link'] = _commit_to_link(repo_url, event['limit'])
          continue


def add_source_info(bug, response):
  """Add source information to `response`."""
  if bug.source_of_truth == osv.SourceOfTruth.INTERNAL:
    response['source'] = 'INTERNAL'
    return

  source_repo = osv.get_source_repository(bug.source)
  if not source_repo or not source_repo.link:
    return

  source_path = osv.source_path(source_repo, bug)
  response['source'] = source_repo.link + source_path
  response['source_link'] = response['source']


def _commit_to_link(repo_url, commit):
  """Convert commit to link."""
  vcs = source_mapper.get_vcs_viewer_for_url(repo_url)
  if not vcs:
    return None

  if ':' not in commit:
    return vcs.get_source_url_for_revision(commit)

  commit_parts = commit.split(':')
  if len(commit_parts) != 2:
    return None

  start, end = commit_parts
  if start == 'unknown':
    return None

  return vcs.get_source_url_for_revision_diff(start, end)


def osv_get_ecosystems():
  """Get list of ecosystems."""
  query = osv.Bug.query(projection=[osv.Bug.ecosystem], distinct=True)
  return sorted([bug.ecosystem[0] for bug in query if bug.ecosystem])


def osv_query(search_string, page, affected_only, ecosystem):
  """Run an OSV query."""
  query = osv.Bug.query(osv.Bug.status == osv.BugStatus.PROCESSED,
                        osv.Bug.public == True)  # pylint: disable=singleton-comparison

  if search_string:
    query = query.filter(osv.Bug.search_indices == search_string.lower())

  if affected_only:
    query = query.filter(osv.Bug.has_affected == True)  # pylint: disable=singleton-comparison

  if ecosystem:
    query = query.filter(osv.Bug.ecosystem == ecosystem)

  query = query.order(-osv.Bug.last_modified)
  total = query.count()
  results = {
      'total': total,
      'items': [],
  }

  bugs, _, _ = query.fetch_page(
      page_size=_PAGE_SIZE, offset=(page - 1) * _PAGE_SIZE)
  for bug in bugs:
    results['items'].append(bug_to_response(bug, detailed=False))

  return results


def osv_get_by_id(vuln_id):
  """Gets bug details from its id. If invalid, aborts the request."""
  if not vuln_id:
    abort(400)
    return None

  bug = osv.Bug.get_by_id(vuln_id)
  if not bug:
    abort(404)
    return None

  if bug.status == osv.BugStatus.UNPROCESSED:
    abort(404)
    return None

  if not bug.public:
    abort(403)
    return None

  return bug_to_response(bug)


@blueprint.route(_BACKEND_ROUTE + '/ecosystems')
def ecosystems_handler():
  """Handle query for list of ecosystems."""
  return jsonify(osv_get_ecosystems())


@blueprint.route(_BACKEND_ROUTE + '/query')
def query_handler():
  """Handle a query."""
  search_string = request.args.get('search')
  page = int(request.args.get('page', 1))
  affected_only = request.args.get('affected_only') == 'true'
  ecosystem = request.args.get('ecosystem')
  results = osv_query(search_string, page, affected_only, ecosystem)
  return jsonify(results)


@blueprint.route(_BACKEND_ROUTE + '/vulnerability')
def vulnerability_handler():
  """Handle a vulnerability request."""
  vuln_id = request.args.get('id')
  return jsonify(osv_get_by_id(vuln_id))
