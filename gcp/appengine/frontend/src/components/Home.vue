<!--
 Copyright 2021 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
-->

<template>
  <div>
    <b-jumbotron id="container">
       <template #header>
         <img id="hero_logo" src="./hero_logo.png">
       </template>

      <h3>Database for open source vulnerabilities</h3>
      <p>
        OSV.dev is a <router-link to="list">vulnerability database</router-link>
        and triage infrastructure for open source projects aimed at helping
        both open source maintainers and consumers of open source.
      <p>
      <p>
        This infrastructure serves as an aggregator of vulnerabilities from 
        <a href="https://github.com/github/advisory-database">GitHub Security Advisories</a>, 
        <a href="https://github.com/google/oss-fuzz">OSS-Fuzz</a> (mostly C/C++), 
        <a href="https://github.com/pypa/advisory-database">PyPI Advisory Database </a>, 
        <a href="https://github.com/golang/vulndb">Go Vulnerability Database</a>, 
        <a href="https://github.com/RustSec/advisory-db">Rust Advisory Database</a>, and 
        <a href="https://github.com/cloudsecurityalliance/gsd-database">Global Security Database</a>.
      </p>
      <p>
        Together, these include vulnerabilities from:
        <ul>
          <li>npm</li>
          <li>Maven</li>
          <li>Go</li>
          <li>NuGet</li>
          <li>PyPI</li>
          <li>RubyGems</li>
          <li>crates.io</li>
          <li>Packagist</li>
          <li>Linux</li>
          <li>OSS-Fuzz</li>
        </ul>
      </p>
      <p>
        These databases have all adopted the
        <a href="https://ossf.github.io/osv-schema/">OpenSSF Open Source
        Vulnerability format</a>, making common tooling and aggregation very
        simple. More data sources from other popular ecosystems are in the works.
      </p>
      <h4>API</h4>
      <p>
        For open source consumers, OSV provides an <a
        href="https://osv.dev/docs/#section/Getting-Started">API</a> that lets
        users query whether or not their versions are impacted.
      </p>
      <pre>
        curl -X POST -d \
            '{"commit": "6879efc2c1596d11a6a6ad296f80063b558d5e0f"}' \
            "https://api.osv.dev/v1/query"
      </pre>
      <pre>
        curl -X POST -d \
            '{"version": "2.4.1", "package": {"name": "jinja2", "ecosystem": "PyPI"}}' \
            "https://api.osv.dev/v1/query"
      </pre>
      <h4>Triaging vulnerabilities</h4>
      <p>
        For open source and vulnerability database maintainers, OSV's
        <a href="https://github.com/pypa/advisory-database/commit/7afe2510b693ad60a0b95da8a5b2a370a7c48997">automation</a>
        helps reduce the burden of triage.

        Vulnerabilities undergo optional bisection and <a
        href="https://github.com/pypa/advisory-database/commit/e4035d8131324cf207ac9b40eacac79b97b1c6b2">version analysis</a>
        to determine precise affected commit and version ranges.
      </p>
      <h3>Open source</h3>
      <p>
        This is an <a href="https://github.com/google/osv">open source project</a>.
        We welcome contributions!
      </p>
      <h3>More information</h3>
      <p>
        Detailed documentation is available <a
        href="https://osv.dev/docs/">here</a>.
      </p>
      <p>
        Check out our <a href="https://osv.dev/docs/#tag/faq">FAQ</a>,
        <a href="https://github.com/google/osv/issues">report issues</a>
        and discuss on our <a href="https://groups.google.com/g/osv-discuss">mailing list</a>.
      </p>
    </b-jumbotron>
  </div>
</template>

<script>
export default {
  name: 'Home',
  mounted() {
    document.title = 'OSV';
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  #container {
    max-width: 1000px;
    margin: 0 auto;
  }

  #hero_logo {
    display: block;
    max-width: 50%;
    width: auto;
    height: auto;
    margin: 0 auto;
  }

  #splash {
    display: block;
    padding: 1em;
    margin: 0 auto;
    max-width: 100%;
    width: auto;
    height: auto;
  }
</style>
