# Changelog

## [Unreleased] V 1.0
### Added
General:
- Changelog (Yay!)
- Pip install support
- Semantic Versioning now employed.
- Added folder for Sphinx doc files, for hosting at ReadTheDocs
- Added folder for Unittests; so far only tests for API classes exist

Exchanges:
- Poloniex RESTAPI and interface
- Interfaces for all RESTAPIs currently implemented
- Standardized methods with identical method headers for all interfaces
- Quoine RESTAPI and interface
- QuadrigaCX RESTAPI and interface

Formatters:
- The submodule `bitex.formatters` has been added, which provides formatter functions for exchange interfaces.

### Changed
General:
- Restructured project to store interfaces in `bitex.interfaces` submodule

Exchanges:
- All calls to interface methods now return a tuple consisting of formatted query data, as well as the raw response object
- Bitstamp's `tickers` method hat its surplus `s` removed.

### Deprecated
- btc-e API is no longer supported actively.

### Removed

### Fixed
- Various spelling and code errors which resulted in the code crashing in unexpected situations.
