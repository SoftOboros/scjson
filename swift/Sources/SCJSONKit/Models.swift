/*
Agent Name: swift-lib

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
*/

import Foundation

/// Backwards-compatible alias for the canonical SCJSON document structure.
/// Use ``ScjsonDocument`` when working with legacy code that expects the
/// original name but take advantage of the generated ``ScxmlProps`` APIs.
public typealias ScjsonDocument = ScxmlProps

/// Backwards-compatible alias for the generated assign type enumeration.
/// The underlying type is provided by ``AssignTypeDatatypeProps``.
public typealias AssignType = AssignTypeDatatypeProps
