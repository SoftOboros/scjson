/*
Agent Name: swift-lib

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
*/

import Foundation

/** Root scjson document model.
 - Parameters:
   - version: Schema version.
   - datamodelAttribute: Datamodel handling attribute.
 */
public struct ScjsonDocument: Codable {
    public var version: Int
    public var datamodelAttribute: String

    enum CodingKeys: String, CodingKey {
        case version
        case datamodelAttribute = "datamodel_attribute"
    }

    /** Create a new document.
     - Parameters:
       - version: Schema version.
       - datamodelAttribute: Datamodel handling attribute.
     */
    public init(version: Int = 1, datamodelAttribute: String = "null") {
        self.version = version
        self.datamodelAttribute = datamodelAttribute
    }
}

/** Assign manipulation types for the datamodel location. */
public enum AssignType: String, Codable {
    case replacechildren
    case firstchild
}
