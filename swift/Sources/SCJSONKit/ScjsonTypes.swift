// Agent Name: swift-props
//
// Part of the scjson project.
// Developed by Softoboros Technology Inc.
// Licensed under the BSD 1-Clause License.

import Foundation

/// Canonical JSON scalar representation used by generated scjson types.
public enum JSONValue: Codable, Equatable {
    case string(String)
    case integer(Int)
    case number(Double)
    case bool(Bool)
    case array([JSONValue])
    case object(JSONDictionary)
    case null

    public init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() {
            self = .null
        } else if let boolValue = try? container.decode(Bool.self) {
            self = .bool(boolValue)
        } else if let intValue = try? container.decode(Int.self) {
            self = .integer(intValue)
        } else if let doubleValue = try? container.decode(Double.self) {
            self = .number(doubleValue)
        } else if let stringValue = try? container.decode(String.self) {
            self = .string(stringValue)
        } else if let arrayValue = try? container.decode([JSONValue].self) {
            self = .array(arrayValue)
        } else if let objectValue = try? container.decode(JSONDictionary.self) {
            self = .object(objectValue)
        } else {
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Unsupported JSON value")
        }
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let value): try container.encode(value)
        case .integer(let value): try container.encode(value)
        case .number(let value): try container.encode(value)
        case .bool(let value): try container.encode(value)
        case .array(let value): try container.encode(value)
        case .object(let value): try container.encode(value)
        case .null: try container.encodeNil()
        }
    }
}

/// Dictionary alias for JSON object values.
public typealias JSONDictionary = [String: JSONValue]

/// Protocol adopted by generated scjson value types to simplify encoding and decoding.
public protocol ScjsonCodable: Codable {}

public extension ScjsonCodable {
    /// Decode a value of the receiver type from JSON data.
    /// - Parameters:
    ///   - data: JSON payload to decode.
    ///   - decoder: Custom `JSONDecoder` to use. Defaults to `JSONDecoder()`.
    /// - Returns: A fully decoded value of the receiver type.
    static func decode(from data: Data, using decoder: JSONDecoder = JSONDecoder()) throws -> Self {
        try decoder.decode(Self.self, from: data)
    }

    /// Encode the value into JSON data.
    /// - Parameter encoder: Custom `JSONEncoder` to use. Defaults to `JSONEncoder()`.
    /// - Returns: UTF-8 encoded JSON data representing the value.
    func encode(using encoder: JSONEncoder = JSONEncoder()) throws -> Data {
        try encoder.encode(self)
    }
}

// MARK: - Enumerations

/// The assign type that allows for precise manipulation of the datamodel     location.      Types are:     replacechildren (default),     firstchild, lastchild,     previoussibling, nextsibling,     replace, delete,     addattribute
public enum AssignTypeDatatypeProps: String, Codable, CaseIterable {
    case replacechildren = "replacechildren"
    case firstchild = "firstchild"
    case lastchild = "lastchild"
    case previoussibling = "previoussibling"
    case nextsibling = "nextsibling"
    case replace = "replace"
    case delete = "delete"
    case addattribute = "addattribute"

    /// Default enumeration value as defined by the schema.
    public static let defaultValue: AssignTypeDatatypeProps = .replacechildren
}

/// The binding type in use for the SCXML document.
public enum BindingDatatypeProps: String, Codable, CaseIterable {
    case early = "early"
    case late = "late"

    /// Default enumeration value as defined by the schema.
    public static let defaultValue: BindingDatatypeProps = .early
}

/// Boolean: true or false only
public enum BooleanDatatypeProps: String, Codable, CaseIterable {
    case `true` = "true"
    case `false` = "false"

    /// Default enumeration value as defined by the schema.
    public static let defaultValue: BooleanDatatypeProps = .`true`
}

/// Describes the processor execution mode for this document, being either "lax" or     "strict".
public enum ExmodeDatatypeProps: String, Codable, CaseIterable {
    case lax = "lax"
    case strict = "strict"

    /// Default enumeration value as defined by the schema.
    public static let defaultValue: ExmodeDatatypeProps = .lax
}

/// type of `<history>` state: `shallow` or `deep`.
public enum HistoryTypeDatatypeProps: String, Codable, CaseIterable {
    case shallow = "shallow"
    case deep = "deep"

    /// Default enumeration value as defined by the schema.
    public static let defaultValue: HistoryTypeDatatypeProps = .shallow
}

/// The type of the transition i.e. internal or external.
public enum TransitionTypeDatatypeProps: String, Codable, CaseIterable {
    case `internal` = "internal"
    case external = "external"

    /// Default enumeration value as defined by the schema.
    public static let defaultValue: TransitionTypeDatatypeProps = .`internal`
}


// MARK: - Model Structures

/// update a datamodel location with an expression or value.
public struct AssignProps: ScjsonCodable, Equatable {
    /// Location
    public var location: String
    /// Expr
    public var expr: String?
    public var typeValue: AssignTypeDatatypeProps
    /// Attr
    public var attr: String?
    /// Other Attributes
    public var otherAttributes: JSONDictionary
    /// Content
    public var content: [JSONValue]

    /// Create a new AssignProps value with schema defaults applied.
    public init(
        location: String = "",
        expr: String? = nil,
        typeValue: AssignTypeDatatypeProps = AssignTypeDatatypeProps.replacechildren,
        attr: String? = nil,
        otherAttributes: JSONDictionary = [:],
        content: [JSONValue] = []
    ) {
        self.location = location
        self.expr = expr
        self.typeValue = typeValue
        self.attr = attr
        self.otherAttributes = otherAttributes
        self.content = content
    }

    private enum CodingKeys: String, CodingKey {
        case location = "location"
        case expr = "expr"
        case typeValue = "type_value"
        case attr = "attr"
        case otherAttributes = "other_attributes"
        case content = "content"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> AssignProps {
        AssignProps()
    }
}

/// Convenience alias representing a collection of AssignProps values.
public typealias AssignArray = [AssignProps]

/// cancel a pending `<send>` operation.
public struct CancelProps: ScjsonCodable, Equatable {
    /// Other Element
    public var otherElement: [JSONValue]
    /// Sendid
    public var sendid: String?
    /// Sendidexpr
    public var sendidexpr: String?
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new CancelProps value with schema defaults applied.
    public init(
        otherElement: [JSONValue] = [],
        sendid: String? = nil,
        sendidexpr: String? = nil,
        otherAttributes: JSONDictionary = [:]
    ) {
        self.otherElement = otherElement
        self.sendid = sendid
        self.sendidexpr = sendidexpr
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case otherElement = "other_element"
        case sendid = "sendid"
        case sendidexpr = "sendidexpr"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> CancelProps {
        CancelProps()
    }
}

/// Convenience alias representing a collection of CancelProps values.
public typealias CancelArray = [CancelProps]

public struct ContentProps: ScjsonCodable, Equatable {
    /// Content
    public var content: [ScxmlProps]?
    /// Expr
    public var expr: String?
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new ContentProps value with schema defaults applied.
    public init(
        content: [ScxmlProps]? = nil,
        expr: String? = nil,
        otherAttributes: JSONDictionary = [:]
    ) {
        self.content = content
        self.expr = expr
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case content = "content"
        case expr = "expr"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> ContentProps {
        ContentProps()
    }
}

/// Convenience alias representing a collection of ContentProps values.
public typealias ContentArray = [ContentProps]

/// represents a single datamodel variable.
public struct DataProps: ScjsonCodable, Equatable {
    /// Id
    public var id: String
    /// Src
    public var src: String?
    /// Expr
    public var expr: String?
    /// Other Attributes
    public var otherAttributes: JSONDictionary
    /// Content
    public var content: [JSONValue]

    /// Create a new DataProps value with schema defaults applied.
    public init(
        id: String = "",
        src: String? = nil,
        expr: String? = nil,
        otherAttributes: JSONDictionary = [:],
        content: [JSONValue] = []
    ) {
        self.id = id
        self.src = src
        self.expr = expr
        self.otherAttributes = otherAttributes
        self.content = content
    }

    private enum CodingKeys: String, CodingKey {
        case id = "id"
        case src = "src"
        case expr = "expr"
        case otherAttributes = "other_attributes"
        case content = "content"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> DataProps {
        DataProps()
    }
}

/// Convenience alias representing a collection of DataProps values.
public typealias DataArray = [DataProps]

/// container for one or more `<data>` elements.
public struct DatamodelProps: ScjsonCodable, Equatable {
    /// Data
    public var data: [DataProps]
    /// Other Element
    public var otherElement: [JSONValue]
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new DatamodelProps value with schema defaults applied.
    public init(
        data: [DataProps] = [],
        otherElement: [JSONValue] = [],
        otherAttributes: JSONDictionary = [:]
    ) {
        self.data = data
        self.otherElement = otherElement
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case data = "data"
        case otherElement = "other_element"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> DatamodelProps {
        DatamodelProps()
    }
}

/// Convenience alias representing a collection of DatamodelProps values.
public typealias DatamodelArray = [DatamodelProps]

public struct DonedataProps: ScjsonCodable, Equatable {
    public var content: ContentProps?
    /// Param
    public var param: [ParamProps]
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new DonedataProps value with schema defaults applied.
    public init(
        content: ContentProps? = nil,
        param: [ParamProps] = [],
        otherAttributes: JSONDictionary = [:]
    ) {
        self.content = content
        self.param = param
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case content = "content"
        case param = "param"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> DonedataProps {
        DonedataProps()
    }
}

/// Convenience alias representing a collection of DonedataProps values.
public typealias DonedataArray = [DonedataProps]

/// fallback branch for `<if>` conditions.
public struct ElseProps: ScjsonCodable, Equatable {
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new ElseProps value with schema defaults applied.
    public init(
        otherAttributes: JSONDictionary = [:]
    ) {
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> ElseProps {
        ElseProps()
    }
}

/// conditional branch following an `<if>`.
public struct ElseifProps: ScjsonCodable, Equatable {
    /// Cond
    public var cond: String
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new ElseifProps value with schema defaults applied.
    public init(
        cond: String = "",
        otherAttributes: JSONDictionary = [:]
    ) {
        self.cond = cond
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case cond = "cond"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> ElseifProps {
        ElseifProps()
    }
}

public struct FinalProps: ScjsonCodable, Equatable {
    /// Onentry
    public var onentry: [OnentryProps]
    /// Onexit
    public var onexit: [OnexitProps]
    /// Donedata
    public var donedata: [DonedataProps]
    /// Other Element
    public var otherElement: [JSONValue]
    /// Id
    public var id: String?
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new FinalProps value with schema defaults applied.
    public init(
        onentry: [OnentryProps] = [],
        onexit: [OnexitProps] = [],
        donedata: [DonedataProps] = [],
        otherElement: [JSONValue] = [],
        id: String? = nil,
        otherAttributes: JSONDictionary = [:]
    ) {
        self.onentry = onentry
        self.onexit = onexit
        self.donedata = donedata
        self.otherElement = otherElement
        self.id = id
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case onentry = "onentry"
        case onexit = "onexit"
        case donedata = "donedata"
        case otherElement = "other_element"
        case id = "id"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> FinalProps {
        FinalProps()
    }
}

/// Convenience alias representing a collection of FinalProps values.
public typealias FinalArray = [FinalProps]

public struct FinalizeProps: ScjsonCodable, Equatable {
    /// Other Element
    public var otherElement: [JSONValue]
    /// Raise Value
    public var raiseValue: [RaiseProps]
    /// If Value
    public var ifValue: [IfProps]
    /// Foreach
    public var foreach: [ForeachProps]
    /// Send
    public var send: [SendProps]
    /// Script
    public var script: [ScriptProps]
    /// Assign
    public var assign: [AssignProps]
    /// Log
    public var log: [LogProps]
    /// Cancel
    public var cancel: [CancelProps]
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new FinalizeProps value with schema defaults applied.
    public init(
        otherElement: [JSONValue] = [],
        raiseValue: [RaiseProps] = [],
        ifValue: [IfProps] = [],
        foreach: [ForeachProps] = [],
        send: [SendProps] = [],
        script: [ScriptProps] = [],
        assign: [AssignProps] = [],
        log: [LogProps] = [],
        cancel: [CancelProps] = [],
        otherAttributes: JSONDictionary = [:]
    ) {
        self.otherElement = otherElement
        self.raiseValue = raiseValue
        self.ifValue = ifValue
        self.foreach = foreach
        self.send = send
        self.script = script
        self.assign = assign
        self.log = log
        self.cancel = cancel
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case otherElement = "other_element"
        case raiseValue = "raise_value"
        case ifValue = "if_value"
        case foreach = "foreach"
        case send = "send"
        case script = "script"
        case assign = "assign"
        case log = "log"
        case cancel = "cancel"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> FinalizeProps {
        FinalizeProps()
    }
}

/// Convenience alias representing a collection of FinalizeProps values.
public typealias FinalizeArray = [FinalizeProps]

public struct ForeachProps: ScjsonCodable, Equatable {
    /// Other Element
    public var otherElement: [JSONValue]
    /// Raise Value
    public var raiseValue: [RaiseProps]
    /// If Value
    public var ifValue: [IfProps]
    /// Foreach
    public var foreach: [ForeachProps]
    /// Send
    public var send: [SendProps]
    /// Script
    public var script: [ScriptProps]
    /// Assign
    public var assign: [AssignProps]
    /// Log
    public var log: [LogProps]
    /// Cancel
    public var cancel: [CancelProps]
    /// Array
    public var array: String
    /// Item
    public var item: String
    /// Index
    public var index: String?
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new ForeachProps value with schema defaults applied.
    public init(
        otherElement: [JSONValue] = [],
        raiseValue: [RaiseProps] = [],
        ifValue: [IfProps] = [],
        foreach: [ForeachProps] = [],
        send: [SendProps] = [],
        script: [ScriptProps] = [],
        assign: [AssignProps] = [],
        log: [LogProps] = [],
        cancel: [CancelProps] = [],
        array: String = "",
        item: String = "",
        index: String? = nil,
        otherAttributes: JSONDictionary = [:]
    ) {
        self.otherElement = otherElement
        self.raiseValue = raiseValue
        self.ifValue = ifValue
        self.foreach = foreach
        self.send = send
        self.script = script
        self.assign = assign
        self.log = log
        self.cancel = cancel
        self.array = array
        self.item = item
        self.index = index
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case otherElement = "other_element"
        case raiseValue = "raise_value"
        case ifValue = "if_value"
        case foreach = "foreach"
        case send = "send"
        case script = "script"
        case assign = "assign"
        case log = "log"
        case cancel = "cancel"
        case array = "array"
        case item = "item"
        case index = "index"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> ForeachProps {
        ForeachProps()
    }
}

/// Convenience alias representing a collection of ForeachProps values.
public typealias ForeachArray = [ForeachProps]

public struct HistoryProps: ScjsonCodable, Equatable {
    /// Other Element
    public var otherElement: [JSONValue]
    public var transition: TransitionProps
    /// Id
    public var id: String?
    public var typeValue: HistoryTypeDatatypeProps?
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new HistoryProps value with schema defaults applied.
    public init(
        otherElement: [JSONValue] = [],
        transition: TransitionProps = TransitionProps(),
        id: String? = nil,
        typeValue: HistoryTypeDatatypeProps? = nil,
        otherAttributes: JSONDictionary = [:]
    ) {
        self.otherElement = otherElement
        self.transition = transition
        self.id = id
        self.typeValue = typeValue
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case otherElement = "other_element"
        case transition = "transition"
        case id = "id"
        case typeValue = "type_value"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> HistoryProps {
        HistoryProps()
    }
}

/// Convenience alias representing a collection of HistoryProps values.
public typealias HistoryArray = [HistoryProps]

public struct IfProps: ScjsonCodable, Equatable {
    /// Other Element
    public var otherElement: [JSONValue]
    /// Raise Value
    public var raiseValue: [RaiseProps]
    /// If Value
    public var ifValue: [IfProps]
    /// Foreach
    public var foreach: [ForeachProps]
    /// Send
    public var send: [SendProps]
    /// Script
    public var script: [ScriptProps]
    /// Assign
    public var assign: [AssignProps]
    /// Log
    public var log: [LogProps]
    /// Cancel
    public var cancel: [CancelProps]
    public var elseif: ElseifProps?
    public var elseValue: ElseProps?
    /// Cond
    public var cond: String
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new IfProps value with schema defaults applied.
    public init(
        otherElement: [JSONValue] = [],
        raiseValue: [RaiseProps] = [],
        ifValue: [IfProps] = [],
        foreach: [ForeachProps] = [],
        send: [SendProps] = [],
        script: [ScriptProps] = [],
        assign: [AssignProps] = [],
        log: [LogProps] = [],
        cancel: [CancelProps] = [],
        elseif: ElseifProps? = nil,
        elseValue: ElseProps? = nil,
        cond: String = "",
        otherAttributes: JSONDictionary = [:]
    ) {
        self.otherElement = otherElement
        self.raiseValue = raiseValue
        self.ifValue = ifValue
        self.foreach = foreach
        self.send = send
        self.script = script
        self.assign = assign
        self.log = log
        self.cancel = cancel
        self.elseif = elseif
        self.elseValue = elseValue
        self.cond = cond
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case otherElement = "other_element"
        case raiseValue = "raise_value"
        case ifValue = "if_value"
        case foreach = "foreach"
        case send = "send"
        case script = "script"
        case assign = "assign"
        case log = "log"
        case cancel = "cancel"
        case elseif = "elseif"
        case elseValue = "else_value"
        case cond = "cond"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> IfProps {
        IfProps()
    }
}

/// Convenience alias representing a collection of IfProps values.
public typealias IfArray = [IfProps]

public struct InitialProps: ScjsonCodable, Equatable {
    /// Other Element
    public var otherElement: [JSONValue]
    public var transition: TransitionProps
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new InitialProps value with schema defaults applied.
    public init(
        otherElement: [JSONValue] = [],
        transition: TransitionProps = TransitionProps(),
        otherAttributes: JSONDictionary = [:]
    ) {
        self.otherElement = otherElement
        self.transition = transition
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case otherElement = "other_element"
        case transition = "transition"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> InitialProps {
        InitialProps()
    }
}

/// Convenience alias representing a collection of InitialProps values.
public typealias InitialArray = [InitialProps]

public struct InvokeProps: ScjsonCodable, Equatable {
    /// Content
    public var content: [ContentProps]
    /// Param
    public var param: [ParamProps]
    /// Finalize
    public var finalize: [FinalizeProps]
    /// Other Element
    public var otherElement: [JSONValue]
    /// Type Value
    public var typeValue: String
    /// Typeexpr
    public var typeexpr: String?
    /// Src
    public var src: String?
    /// Srcexpr
    public var srcexpr: String?
    /// Id
    public var id: String?
    /// Idlocation
    public var idlocation: String?
    /// Namelist
    public var namelist: String?
    public var autoforward: BooleanDatatypeProps
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new InvokeProps value with schema defaults applied.
    public init(
        content: [ContentProps] = [],
        param: [ParamProps] = [],
        finalize: [FinalizeProps] = [],
        otherElement: [JSONValue] = [],
        typeValue: String = "scxml",
        typeexpr: String? = nil,
        src: String? = nil,
        srcexpr: String? = nil,
        id: String? = nil,
        idlocation: String? = nil,
        namelist: String? = nil,
        autoforward: BooleanDatatypeProps = BooleanDatatypeProps.`false`,
        otherAttributes: JSONDictionary = [:]
    ) {
        self.content = content
        self.param = param
        self.finalize = finalize
        self.otherElement = otherElement
        self.typeValue = typeValue
        self.typeexpr = typeexpr
        self.src = src
        self.srcexpr = srcexpr
        self.id = id
        self.idlocation = idlocation
        self.namelist = namelist
        self.autoforward = autoforward
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case content = "content"
        case param = "param"
        case finalize = "finalize"
        case otherElement = "other_element"
        case typeValue = "type_value"
        case typeexpr = "typeexpr"
        case src = "src"
        case srcexpr = "srcexpr"
        case id = "id"
        case idlocation = "idlocation"
        case namelist = "namelist"
        case autoforward = "autoforward"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> InvokeProps {
        InvokeProps()
    }
}

/// Convenience alias representing a collection of InvokeProps values.
public typealias InvokeArray = [InvokeProps]

/// diagnostic output statement.
public struct LogProps: ScjsonCodable, Equatable {
    /// Other Element
    public var otherElement: [JSONValue]
    /// Label
    public var label: String?
    /// Expr
    public var expr: String?
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new LogProps value with schema defaults applied.
    public init(
        otherElement: [JSONValue] = [],
        label: String? = nil,
        expr: String? = nil,
        otherAttributes: JSONDictionary = [:]
    ) {
        self.otherElement = otherElement
        self.label = label
        self.expr = expr
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case otherElement = "other_element"
        case label = "label"
        case expr = "expr"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> LogProps {
        LogProps()
    }
}

/// Convenience alias representing a collection of LogProps values.
public typealias LogArray = [LogProps]

public struct OnentryProps: ScjsonCodable, Equatable {
    /// Other Element
    public var otherElement: [JSONValue]
    /// Raise Value
    public var raiseValue: [RaiseProps]
    /// If Value
    public var ifValue: [IfProps]
    /// Foreach
    public var foreach: [ForeachProps]
    /// Send
    public var send: [SendProps]
    /// Script
    public var script: [ScriptProps]
    /// Assign
    public var assign: [AssignProps]
    /// Log
    public var log: [LogProps]
    /// Cancel
    public var cancel: [CancelProps]
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new OnentryProps value with schema defaults applied.
    public init(
        otherElement: [JSONValue] = [],
        raiseValue: [RaiseProps] = [],
        ifValue: [IfProps] = [],
        foreach: [ForeachProps] = [],
        send: [SendProps] = [],
        script: [ScriptProps] = [],
        assign: [AssignProps] = [],
        log: [LogProps] = [],
        cancel: [CancelProps] = [],
        otherAttributes: JSONDictionary = [:]
    ) {
        self.otherElement = otherElement
        self.raiseValue = raiseValue
        self.ifValue = ifValue
        self.foreach = foreach
        self.send = send
        self.script = script
        self.assign = assign
        self.log = log
        self.cancel = cancel
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case otherElement = "other_element"
        case raiseValue = "raise_value"
        case ifValue = "if_value"
        case foreach = "foreach"
        case send = "send"
        case script = "script"
        case assign = "assign"
        case log = "log"
        case cancel = "cancel"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> OnentryProps {
        OnentryProps()
    }
}

/// Convenience alias representing a collection of OnentryProps values.
public typealias OnentryArray = [OnentryProps]

public struct OnexitProps: ScjsonCodable, Equatable {
    /// Other Element
    public var otherElement: [JSONValue]
    /// Raise Value
    public var raiseValue: [RaiseProps]
    /// If Value
    public var ifValue: [IfProps]
    /// Foreach
    public var foreach: [ForeachProps]
    /// Send
    public var send: [SendProps]
    /// Script
    public var script: [ScriptProps]
    /// Assign
    public var assign: [AssignProps]
    /// Log
    public var log: [LogProps]
    /// Cancel
    public var cancel: [CancelProps]
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new OnexitProps value with schema defaults applied.
    public init(
        otherElement: [JSONValue] = [],
        raiseValue: [RaiseProps] = [],
        ifValue: [IfProps] = [],
        foreach: [ForeachProps] = [],
        send: [SendProps] = [],
        script: [ScriptProps] = [],
        assign: [AssignProps] = [],
        log: [LogProps] = [],
        cancel: [CancelProps] = [],
        otherAttributes: JSONDictionary = [:]
    ) {
        self.otherElement = otherElement
        self.raiseValue = raiseValue
        self.ifValue = ifValue
        self.foreach = foreach
        self.send = send
        self.script = script
        self.assign = assign
        self.log = log
        self.cancel = cancel
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case otherElement = "other_element"
        case raiseValue = "raise_value"
        case ifValue = "if_value"
        case foreach = "foreach"
        case send = "send"
        case script = "script"
        case assign = "assign"
        case log = "log"
        case cancel = "cancel"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> OnexitProps {
        OnexitProps()
    }
}

/// Convenience alias representing a collection of OnexitProps values.
public typealias OnexitArray = [OnexitProps]

public struct ParallelProps: ScjsonCodable, Equatable {
    /// Onentry
    public var onentry: [OnentryProps]
    /// Onexit
    public var onexit: [OnexitProps]
    /// Transition
    public var transition: [TransitionProps]
    /// State
    public var state: [StateProps]
    /// Parallel
    public var parallel: [ParallelProps]
    /// History
    public var history: [HistoryProps]
    /// Datamodel
    public var datamodel: [DatamodelProps]
    /// Invoke
    public var invoke: [InvokeProps]
    /// Other Element
    public var otherElement: [JSONValue]
    /// Id
    public var id: String?
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new ParallelProps value with schema defaults applied.
    public init(
        onentry: [OnentryProps] = [],
        onexit: [OnexitProps] = [],
        transition: [TransitionProps] = [],
        state: [StateProps] = [],
        parallel: [ParallelProps] = [],
        history: [HistoryProps] = [],
        datamodel: [DatamodelProps] = [],
        invoke: [InvokeProps] = [],
        otherElement: [JSONValue] = [],
        id: String? = nil,
        otherAttributes: JSONDictionary = [:]
    ) {
        self.onentry = onentry
        self.onexit = onexit
        self.transition = transition
        self.state = state
        self.parallel = parallel
        self.history = history
        self.datamodel = datamodel
        self.invoke = invoke
        self.otherElement = otherElement
        self.id = id
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case onentry = "onentry"
        case onexit = "onexit"
        case transition = "transition"
        case state = "state"
        case parallel = "parallel"
        case history = "history"
        case datamodel = "datamodel"
        case invoke = "invoke"
        case otherElement = "other_element"
        case id = "id"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> ParallelProps {
        ParallelProps()
    }
}

/// Convenience alias representing a collection of ParallelProps values.
public typealias ParallelArray = [ParallelProps]

/// parameter passed to `<invoke>` or `<send>`.
public struct ParamProps: ScjsonCodable, Equatable {
    /// Other Element
    public var otherElement: [JSONValue]
    /// Name
    public var name: String
    /// Expr
    public var expr: String?
    /// Location
    public var location: String?
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new ParamProps value with schema defaults applied.
    public init(
        otherElement: [JSONValue] = [],
        name: String = "",
        expr: String? = nil,
        location: String? = nil,
        otherAttributes: JSONDictionary = [:]
    ) {
        self.otherElement = otherElement
        self.name = name
        self.expr = expr
        self.location = location
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case otherElement = "other_element"
        case name = "name"
        case expr = "expr"
        case location = "location"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> ParamProps {
        ParamProps()
    }
}

/// Convenience alias representing a collection of ParamProps values.
public typealias ParamArray = [ParamProps]

/// raise an internal event.
public struct RaiseProps: ScjsonCodable, Equatable {
    /// Event
    public var event: String
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new RaiseProps value with schema defaults applied.
    public init(
        event: String = "",
        otherAttributes: JSONDictionary = [:]
    ) {
        self.event = event
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case event = "event"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> RaiseProps {
        RaiseProps()
    }
}

/// Convenience alias representing a collection of RaiseProps values.
public typealias RaiseArray = [RaiseProps]

/// inline executable script.
public struct ScriptProps: ScjsonCodable, Equatable {
    /// Src
    public var src: String?
    /// Other Attributes
    public var otherAttributes: JSONDictionary
    /// Content
    public var content: [JSONValue]

    /// Create a new ScriptProps value with schema defaults applied.
    public init(
        src: String? = nil,
        otherAttributes: JSONDictionary = [:],
        content: [JSONValue] = []
    ) {
        self.src = src
        self.otherAttributes = otherAttributes
        self.content = content
    }

    private enum CodingKeys: String, CodingKey {
        case src = "src"
        case otherAttributes = "other_attributes"
        case content = "content"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> ScriptProps {
        ScriptProps()
    }
}

/// Convenience alias representing a collection of ScriptProps values.
public typealias ScriptArray = [ScriptProps]

public struct ScxmlProps: ScjsonCodable, Equatable {
    /// State
    public var state: [StateProps]
    /// Parallel
    public var parallel: [ParallelProps]
    /// Final
    public var final: [FinalProps]
    /// Datamodel
    public var datamodel: [DatamodelProps]
    /// Script
    public var script: [ScriptProps]
    /// Other Element
    public var otherElement: [JSONValue]
    /// Initial
    public var initial: [String]
    /// Name
    public var name: String?
    /// Version
    public var version: JSONValue?
    /// Datamodel Attribute
    public var datamodelAttribute: String
    public var binding: BindingDatatypeProps?
    public var exmode: ExmodeDatatypeProps?
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new ScxmlProps value with schema defaults applied.
    public init(
        state: [StateProps] = [],
        parallel: [ParallelProps] = [],
        final: [FinalProps] = [],
        datamodel: [DatamodelProps] = [],
        script: [ScriptProps] = [],
        otherElement: [JSONValue] = [],
        initial: [String] = [],
        name: String? = nil,
        version: JSONValue? = JSONValue.string("1.0"),
        datamodelAttribute: String = "null",
        binding: BindingDatatypeProps? = nil,
        exmode: ExmodeDatatypeProps? = nil,
        otherAttributes: JSONDictionary = [:]
    ) {
        self.state = state
        self.parallel = parallel
        self.final = final
        self.datamodel = datamodel
        self.script = script
        self.otherElement = otherElement
        self.initial = initial
        self.name = name
        self.version = version
        self.datamodelAttribute = datamodelAttribute
        self.binding = binding
        self.exmode = exmode
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case state = "state"
        case parallel = "parallel"
        case final = "final"
        case datamodel = "datamodel"
        case script = "script"
        case otherElement = "other_element"
        case initial = "initial"
        case name = "name"
        case version = "version"
        case datamodelAttribute = "datamodel_attribute"
        case binding = "binding"
        case exmode = "exmode"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> ScxmlProps {
        ScxmlProps()
    }
}

public struct SendProps: ScjsonCodable, Equatable {
    /// Content
    public var content: [ContentProps]
    /// Param
    public var param: [ParamProps]
    /// Other Element
    public var otherElement: [JSONValue]
    /// Event
    public var event: String?
    /// Eventexpr
    public var eventexpr: String?
    /// Target
    public var target: String?
    /// Targetexpr
    public var targetexpr: String?
    /// Type Value
    public var typeValue: String
    /// Typeexpr
    public var typeexpr: String?
    /// Id
    public var id: String?
    /// Idlocation
    public var idlocation: String?
    /// Delay
    public var delay: String
    /// Delayexpr
    public var delayexpr: String?
    /// Namelist
    public var namelist: String?
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new SendProps value with schema defaults applied.
    public init(
        content: [ContentProps] = [],
        param: [ParamProps] = [],
        otherElement: [JSONValue] = [],
        event: String? = nil,
        eventexpr: String? = nil,
        target: String? = nil,
        targetexpr: String? = nil,
        typeValue: String = "scxml",
        typeexpr: String? = nil,
        id: String? = nil,
        idlocation: String? = nil,
        delay: String = "0s",
        delayexpr: String? = nil,
        namelist: String? = nil,
        otherAttributes: JSONDictionary = [:]
    ) {
        self.content = content
        self.param = param
        self.otherElement = otherElement
        self.event = event
        self.eventexpr = eventexpr
        self.target = target
        self.targetexpr = targetexpr
        self.typeValue = typeValue
        self.typeexpr = typeexpr
        self.id = id
        self.idlocation = idlocation
        self.delay = delay
        self.delayexpr = delayexpr
        self.namelist = namelist
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case content = "content"
        case param = "param"
        case otherElement = "other_element"
        case event = "event"
        case eventexpr = "eventexpr"
        case target = "target"
        case targetexpr = "targetexpr"
        case typeValue = "type_value"
        case typeexpr = "typeexpr"
        case id = "id"
        case idlocation = "idlocation"
        case delay = "delay"
        case delayexpr = "delayexpr"
        case namelist = "namelist"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> SendProps {
        SendProps()
    }
}

/// Convenience alias representing a collection of SendProps values.
public typealias SendArray = [SendProps]

public struct StateProps: ScjsonCodable, Equatable {
    /// Onentry
    public var onentry: [OnentryProps]
    /// Onexit
    public var onexit: [OnexitProps]
    /// Transition
    public var transition: [TransitionProps]
    /// Initial
    public var initial: [InitialProps]
    /// State
    public var state: [StateProps]
    /// Parallel
    public var parallel: [ParallelProps]
    /// Final
    public var final: [FinalProps]
    /// History
    public var history: [HistoryProps]
    /// Datamodel
    public var datamodel: [DatamodelProps]
    /// Invoke
    public var invoke: [InvokeProps]
    /// Other Element
    public var otherElement: [JSONValue]
    /// Id
    public var id: String?
    /// Initial Attribute
    public var initialAttribute: [String]
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new StateProps value with schema defaults applied.
    public init(
        onentry: [OnentryProps] = [],
        onexit: [OnexitProps] = [],
        transition: [TransitionProps] = [],
        initial: [InitialProps] = [],
        state: [StateProps] = [],
        parallel: [ParallelProps] = [],
        final: [FinalProps] = [],
        history: [HistoryProps] = [],
        datamodel: [DatamodelProps] = [],
        invoke: [InvokeProps] = [],
        otherElement: [JSONValue] = [],
        id: String? = nil,
        initialAttribute: [String] = [],
        otherAttributes: JSONDictionary = [:]
    ) {
        self.onentry = onentry
        self.onexit = onexit
        self.transition = transition
        self.initial = initial
        self.state = state
        self.parallel = parallel
        self.final = final
        self.history = history
        self.datamodel = datamodel
        self.invoke = invoke
        self.otherElement = otherElement
        self.id = id
        self.initialAttribute = initialAttribute
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case onentry = "onentry"
        case onexit = "onexit"
        case transition = "transition"
        case initial = "initial"
        case state = "state"
        case parallel = "parallel"
        case final = "final"
        case history = "history"
        case datamodel = "datamodel"
        case invoke = "invoke"
        case otherElement = "other_element"
        case id = "id"
        case initialAttribute = "initial_attribute"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> StateProps {
        StateProps()
    }
}

/// Convenience alias representing a collection of StateProps values.
public typealias StateArray = [StateProps]

public struct TransitionProps: ScjsonCodable, Equatable {
    /// Other Element
    public var otherElement: [JSONValue]
    /// Raise Value
    public var raiseValue: [RaiseProps]
    /// If Value
    public var ifValue: [IfProps]
    /// Foreach
    public var foreach: [ForeachProps]
    /// Send
    public var send: [SendProps]
    /// Script
    public var script: [ScriptProps]
    /// Assign
    public var assign: [AssignProps]
    /// Log
    public var log: [LogProps]
    /// Cancel
    public var cancel: [CancelProps]
    /// Event
    public var event: String?
    /// Cond
    public var cond: String?
    /// Target
    public var target: [String]
    public var typeValue: TransitionTypeDatatypeProps?
    /// Other Attributes
    public var otherAttributes: JSONDictionary

    /// Create a new TransitionProps value with schema defaults applied.
    public init(
        otherElement: [JSONValue] = [],
        raiseValue: [RaiseProps] = [],
        ifValue: [IfProps] = [],
        foreach: [ForeachProps] = [],
        send: [SendProps] = [],
        script: [ScriptProps] = [],
        assign: [AssignProps] = [],
        log: [LogProps] = [],
        cancel: [CancelProps] = [],
        event: String? = nil,
        cond: String? = nil,
        target: [String] = [],
        typeValue: TransitionTypeDatatypeProps? = nil,
        otherAttributes: JSONDictionary = [:]
    ) {
        self.otherElement = otherElement
        self.raiseValue = raiseValue
        self.ifValue = ifValue
        self.foreach = foreach
        self.send = send
        self.script = script
        self.assign = assign
        self.log = log
        self.cancel = cancel
        self.event = event
        self.cond = cond
        self.target = target
        self.typeValue = typeValue
        self.otherAttributes = otherAttributes
    }

    private enum CodingKeys: String, CodingKey {
        case otherElement = "other_element"
        case raiseValue = "raise_value"
        case ifValue = "if_value"
        case foreach = "foreach"
        case send = "send"
        case script = "script"
        case assign = "assign"
        case log = "log"
        case cancel = "cancel"
        case event = "event"
        case cond = "cond"
        case target = "target"
        case typeValue = "type_value"
        case otherAttributes = "other_attributes"
    }

    /// Convenience factory returning the canonical default instance.
    public static func makeDefault() -> TransitionProps {
        TransitionProps()
    }
}

/// Convenience alias representing a collection of TransitionProps values.
public typealias TransitionArray = [TransitionProps]


// MARK: - Kind Registry

/// Exhaustive set of union kinds used throughout the scjson schema.
public enum ScjsonKind: String {
    /// Canonical kind identifier for the `assign` element family.
    case assign = "assign"
    /// Canonical kind identifier for arrays of `assign` entries.
    case assignArray = "assignarray"
    /// Canonical kind identifier for the `assigntypedatatype` element family.
    case assignTypeDatatype = "assigntypedatatype"
    /// Canonical kind identifier for the `bindingdatatype` element family.
    case bindingDatatype = "bindingdatatype"
    /// Canonical kind identifier for the `booleandatatype` element family.
    case booleanDatatype = "booleandatatype"
    /// Canonical kind identifier for the `cancel` element family.
    case cancel = "cancel"
    /// Canonical kind identifier for arrays of `cancel` entries.
    case cancelArray = "cancelarray"
    /// Canonical kind identifier for the `content` element family.
    case content = "content"
    /// Canonical kind identifier for arrays of `content` entries.
    case contentArray = "contentarray"
    /// Canonical kind identifier for the `data` element family.
    case data = "data"
    /// Canonical kind identifier for arrays of `data` entries.
    case dataArray = "dataarray"
    /// Canonical kind identifier for the `datamodel` element family.
    case datamodel = "datamodel"
    /// Canonical kind identifier for arrays of `datamodel` entries.
    case datamodelArray = "datamodelarray"
    /// Canonical kind identifier for the `donedata` element family.
    case donedata = "donedata"
    /// Canonical kind identifier for arrays of `donedata` entries.
    case donedataArray = "donedataarray"
    /// Canonical kind identifier for the `else` element family.
    case `else` = "else"
    /// Canonical kind identifier for the `elseif` element family.
    case elseif = "elseif"
    /// Canonical kind identifier for the `exmodedatatype` element family.
    case exmodeDatatype = "exmodedatatype"
    /// Canonical kind identifier for the `final` element family.
    case final = "final"
    /// Canonical kind identifier for arrays of `final` entries.
    case finalArray = "finalarray"
    /// Canonical kind identifier for the `finalize` element family.
    case finalize = "finalize"
    /// Canonical kind identifier for arrays of `finalize` entries.
    case finalizeArray = "finalizearray"
    /// Canonical kind identifier for the `foreach` element family.
    case foreach = "foreach"
    /// Canonical kind identifier for arrays of `foreach` entries.
    case foreachArray = "foreacharray"
    /// Canonical kind identifier for the `history` element family.
    case history = "history"
    /// Canonical kind identifier for arrays of `history` entries.
    case historyArray = "historyarray"
    /// Canonical kind identifier for the `historytypedatatype` element family.
    case historyTypeDatatype = "historytypedatatype"
    /// Canonical kind identifier for the `if` element family.
    case `if` = "if"
    /// Canonical kind identifier for arrays of `if` entries.
    case ifArray = "ifarray"
    /// Canonical kind identifier for the `initial` element family.
    case initial = "initial"
    /// Canonical kind identifier for arrays of `initial` entries.
    case initialArray = "initialarray"
    /// Canonical kind identifier for the `invoke` element family.
    case invoke = "invoke"
    /// Canonical kind identifier for arrays of `invoke` entries.
    case invokeArray = "invokearray"
    /// Canonical kind identifier for the `log` element family.
    case log = "log"
    /// Canonical kind identifier for arrays of `log` entries.
    case logArray = "logarray"
    /// Canonical kind identifier for the `onentry` element family.
    case onentry = "onentry"
    /// Canonical kind identifier for arrays of `onentry` entries.
    case onentryArray = "onentryarray"
    /// Canonical kind identifier for the `onexit` element family.
    case onexit = "onexit"
    /// Canonical kind identifier for arrays of `onexit` entries.
    case onexitArray = "onexitarray"
    /// Canonical kind identifier for the `parallel` element family.
    case parallel = "parallel"
    /// Canonical kind identifier for arrays of `parallel` entries.
    case parallelArray = "parallelarray"
    /// Canonical kind identifier for the `param` element family.
    case param = "param"
    /// Canonical kind identifier for arrays of `param` entries.
    case paramArray = "paramarray"
    /// Canonical kind identifier for the `raise` element family.
    case raise = "raise"
    /// Canonical kind identifier for arrays of `raise` entries.
    case raiseArray = "raisearray"
    /// Canonical kind identifier for the `script` element family.
    case script = "script"
    /// Canonical kind identifier for arrays of `script` entries.
    case scriptArray = "scriptarray"
    /// Canonical kind identifier for the `scxml` element family.
    case scxml = "scxml"
    /// Canonical kind identifier for the `send` element family.
    case send = "send"
    /// Canonical kind identifier for arrays of `send` entries.
    case sendArray = "sendarray"
    /// Canonical kind identifier for the `state` element family.
    case state = "state"
    /// Canonical kind identifier for arrays of `state` entries.
    case stateArray = "statearray"
    /// Canonical kind identifier for the `transition` element family.
    case transition = "transition"
    /// Canonical kind identifier for arrays of `transition` entries.
    case transitionArray = "transitionarray"
    /// Canonical kind identifier for the `transitiontypedatatype` element family.
    case transitionTypeDatatype = "transitiontypedatatype"
}

