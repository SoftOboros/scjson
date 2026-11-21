/**
 * scjsonProps.d.ts : Properties definition file for scjson types
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */

/**
 * update a datamodel location with an expression or value.
*/
export interface AssignProps {
    location: string;
    expr: string | null;
    typeValue: typeof AssignTypeDatatypeProps;
    attr: string | null;
    otherAttributes: Record<string, object>;
    helpText: string[];
    content: Record<string, object>[];
}

/** Instantiate a default object of type AssignProps */
export declare const defaultAssign: () => AssignProps;

/**
 * update a datamodel location with an expression or value.
*/
/** Type for an array of of AssignProps */
export type AssignArray = AssignProps[];

/**
 * The assign type that allows for precise manipulation of the datamodel
 * location.
 * Types are:
 * replacechildren (default),
 * firstchild, lastchild,
 * previoussibling, nextsibling,
 * replace, delete,
 * addattribute
*/
export type AssignTypeDatatypePropsType =
    | "addattribute"
    | "delete"
    | "firstchild"
    | "lastchild"
    | "nextsibling"
    | "previoussibling"
    | "replace"
    | "replacechildren"
;

export declare const AssignTypeDatatypeProps: {
    readonly Addattribute: "addattribute",
    readonly Delete: "delete",
    readonly Firstchild: "firstchild",
    readonly Lastchild: "lastchild",
    readonly Nextsibling: "nextsibling",
    readonly Previoussibling: "previoussibling",
    readonly Replace: "replace",
    readonly Replacechildren: "replacechildren",
};

/**
 * The binding type in use for the SCXML document.
*/
export type BindingDatatypePropsType =
    | "early"
    | "late"
;

export declare const BindingDatatypeProps: {
    readonly Early: "early",
    readonly Late: "late",
};

/**
 * Boolean: true or false only
*/
export type BooleanDatatypePropsType =
    | "false"
    | "true"
;

export declare const BooleanDatatypeProps: {
    readonly False: "false",
    readonly True: "true",
};

/**
 * cancel a pending `<send>` operation.
*/
export interface CancelProps {
    otherElement: Record<string, object>[];
    sendid: string | null;
    sendidexpr: string | null;
    otherAttributes: Record<string, object>;
    helpText: string[];
}

/** Instantiate a default object of type CancelProps */
export declare const defaultCancel: () => CancelProps;

/**
 * cancel a pending `<send>` operation.
*/
/** Type for an array of of CancelProps */
export type CancelArray = CancelProps[];

/**
 * inline payload used by `<send>` and `<invoke>`.
*/
export interface ContentProps {
    content: (string | XmlPayloadElementProps | ScxmlProps)[] | null;
    expr: string | null;
    otherAttributes: Record<string, object>;
    helpText: string[];
}

/** Instantiate a default object of type ContentProps */
export declare const defaultContent: () => ContentProps;

/**
 * inline payload used by `<send>` and `<invoke>`.
*/
/** Type for an array of of ContentProps */
export type ContentArray = ContentProps[];

/**
 * represents a single datamodel variable.
*/
export interface DataProps {
    id: string;
    src: string | null;
    expr: string | null;
    otherAttributes: Record<string, object>;
    helpText: string[];
    content: Record<string, object>[];
}

/** Instantiate a default object of type DataProps */
export declare const defaultData: () => DataProps;

/**
 * represents a single datamodel variable.
*/
/** Type for an array of of DataProps */
export type DataArray = DataProps[];

/**
 * container for one or more `<data>` elements.
*/
export interface DatamodelProps {
    data: DataProps[];
    otherElement: Record<string, object>[];
    otherAttributes: Record<string, object>;
    helpText: string[];
}

/** Instantiate a default object of type DatamodelProps */
export declare const defaultDatamodel: () => DatamodelProps;

/**
 * container for one or more `<data>` elements.
*/
/** Type for an array of of DatamodelProps */
export type DatamodelArray = DatamodelProps[];

/**
 * payload returned when a `<final>` state is reached.
*/
export interface DonedataProps {
    content: ContentProps | null;
    param: ParamProps[];
    otherAttributes: Record<string, object>;
    helpText: string[];
}

/** Instantiate a default object of type DonedataProps */
export declare const defaultDonedata: () => DonedataProps;

/**
 * payload returned when a `<final>` state is reached.
*/
/** Type for an array of of DonedataProps */
export type DonedataArray = DonedataProps[];

/**
 * fallback branch for `<if>` conditions.
*/
export interface ElseProps {
    otherAttributes: Record<string, object>;
    helpText: string[];
}

/** Instantiate a default object of type ElseProps */
export declare const defaultElse: () => ElseProps;

/**
 * conditional branch following an `<if>`.
*/
export interface ElseifProps {
    cond: string;
    otherAttributes: Record<string, object>;
    helpText: string[];
}

/** Instantiate a default object of type ElseifProps */
export declare const defaultElseif: () => ElseifProps;

/**
 * Describes the processor execution mode for this document, being either "lax" or
 * "strict".
*/
export type ExmodeDatatypePropsType =
    | "lax"
    | "strict"
;

export declare const ExmodeDatatypeProps: {
    readonly Lax: "lax",
    readonly Strict: "strict",
};

/**
 * marks a terminal state in the machine.
*/
export interface FinalProps {
    onentry: OnentryProps[];
    onexit: OnexitProps[];
    donedata: DonedataProps[];
    otherElement: Record<string, object>[];
    id: string | null;
    otherAttributes: Record<string, object>;
    helpText: string[];
}

/** Instantiate a default object of type FinalProps */
export declare const defaultFinal: () => FinalProps;

/**
 * marks a terminal state in the machine.
*/
/** Type for an array of of FinalProps */
export type FinalArray = FinalProps[];

/**
 * executed after an `<invoke>` completes.
*/
export interface FinalizeProps {
    otherElement: Record<string, object>[];
    raiseValue: RaiseProps[];
    ifValue: IfProps[];
    foreach: ForeachProps[];
    send: SendProps[];
    script: ScriptProps[];
    assign: AssignProps[];
    log: LogProps[];
    cancel: CancelProps[];
    otherAttributes: Record<string, object>;
    helpText: string[];
    executionOrder?: string[];
}

/** Instantiate a default object of type FinalizeProps */
export declare const defaultFinalize: () => FinalizeProps;

/**
 * executed after an `<invoke>` completes.
*/
/** Type for an array of of FinalizeProps */
export type FinalizeArray = FinalizeProps[];

/**
 * iterate over items within executable content.
*/
export interface ForeachProps {
    otherElement: Record<string, object>[];
    raiseValue: RaiseProps[];
    ifValue: IfProps[];
    foreach: ForeachProps[];
    send: SendProps[];
    script: ScriptProps[];
    assign: AssignProps[];
    log: LogProps[];
    cancel: CancelProps[];
    array: string;
    item: string;
    index: string | null;
    otherAttributes: Record<string, object>;
    helpText: string[];
    executionOrder?: string[];
}

/** Instantiate a default object of type ForeachProps */
export declare const defaultForeach: () => ForeachProps;

/**
 * iterate over items within executable content.
*/
/** Type for an array of of ForeachProps */
export type ForeachArray = ForeachProps[];

/**
 * pseudostate remembering previous active children.
*/
export interface HistoryProps {
    otherElement: Record<string, object>[];
    transition: TransitionProps;
    id: string | null;
    typeValue: typeof HistoryTypeDatatypeProps | null;
    otherAttributes: Record<string, object>;
    helpText: string[];
}

/** Instantiate a default object of type HistoryProps */
export declare const defaultHistory: () => HistoryProps;

/**
 * pseudostate remembering previous active children.
*/
/** Type for an array of of HistoryProps */
export type HistoryArray = HistoryProps[];

/**
 * type of `<history>` state: `shallow` or `deep`.
*/
export type HistoryTypeDatatypePropsType =
    | "deep"
    | "shallow"
;

export declare const HistoryTypeDatatypeProps: {
    readonly Deep: "deep",
    readonly Shallow: "shallow",
};

/**
 * conditional execution block.
*/
export interface IfProps {
    otherElement: Record<string, object>[];
    raiseValue: RaiseProps[];
    ifValue: IfProps[];
    foreach: ForeachProps[];
    send: SendProps[];
    script: ScriptProps[];
    assign: AssignProps[];
    log: LogProps[];
    cancel: CancelProps[];
    elseif: ElseifProps | ElseifProps[] | null;
    elseValue: ElseProps | null;
    cond: string;
    otherAttributes: Record<string, object>;
    helpText: string[];
    executionOrder?: string[];
}

/** Instantiate a default object of type IfProps */
export declare const defaultIf: () => IfProps;

/**
 * conditional execution block.
*/
/** Type for an array of of IfProps */
export type IfArray = IfProps[];

/**
 * starting state within a compound state.
*/
export interface InitialProps {
    otherElement: Record<string, object>[];
    transition: TransitionProps;
    otherAttributes: Record<string, object>;
    helpText: string[];
}

/** Instantiate a default object of type InitialProps */
export declare const defaultInitial: () => InitialProps;

/**
 * starting state within a compound state.
*/
/** Type for an array of of InitialProps */
export type InitialArray = InitialProps[];

/**
 * run an external process or machine.
*/
export interface InvokeProps {
    content: ContentProps[];
    param: ParamProps[];
    finalize: FinalizeProps[];
    otherElement: Record<string, object>[];
    typeValue: string;
    typeexpr: string | null;
    src: string | null;
    srcexpr: string | null;
    id: string | null;
    idlocation: string | null;
    namelist: string | null;
    autoforward: typeof BooleanDatatypeProps;
    otherAttributes: Record<string, object>;
    helpText: string[];
}

/** Instantiate a default object of type InvokeProps */
export declare const defaultInvoke: () => InvokeProps;

/**
 * run an external process or machine.
*/
/** Type for an array of of InvokeProps */
export type InvokeArray = InvokeProps[];

/**
 * diagnostic output statement.
*/
export interface LogProps {
    otherElement: Record<string, object>[];
    label: string | null;
    expr: string | null;
    otherAttributes: Record<string, object>;
    helpText: string[];
}

/** Instantiate a default object of type LogProps */
export declare const defaultLog: () => LogProps;

/**
 * diagnostic output statement.
*/
/** Type for an array of of LogProps */
export type LogArray = LogProps[];

/**
 * actions performed when entering a state.
*/
export interface OnentryProps {
    otherElement: Record<string, object>[];
    raiseValue: RaiseProps[];
    ifValue: IfProps[];
    foreach: ForeachProps[];
    send: SendProps[];
    script: ScriptProps[];
    assign: AssignProps[];
    log: LogProps[];
    cancel: CancelProps[];
    otherAttributes: Record<string, object>;
    helpText: string[];
    executionOrder?: string[];
}

/** Instantiate a default object of type OnentryProps */
export declare const defaultOnentry: () => OnentryProps;

/**
 * actions performed when entering a state.
*/
/** Type for an array of of OnentryProps */
export type OnentryArray = OnentryProps[];

/**
 * actions performed when leaving a state.
*/
export interface OnexitProps {
    otherElement: Record<string, object>[];
    raiseValue: RaiseProps[];
    ifValue: IfProps[];
    foreach: ForeachProps[];
    send: SendProps[];
    script: ScriptProps[];
    assign: AssignProps[];
    log: LogProps[];
    cancel: CancelProps[];
    otherAttributes: Record<string, object>;
    helpText: string[];
    executionOrder?: string[];
}

/** Instantiate a default object of type OnexitProps */
export declare const defaultOnexit: () => OnexitProps;

/**
 * actions performed when leaving a state.
*/
/** Type for an array of of OnexitProps */
export type OnexitArray = OnexitProps[];

/**
 * coordinates concurrent regions.
*/
export interface ParallelProps {
    onentry: OnentryProps[];
    onexit: OnexitProps[];
    transition: TransitionProps[];
    state: StateProps[];
    parallel: ParallelProps[];
    history: HistoryProps[];
    datamodel: DatamodelProps[];
    invoke: InvokeProps[];
    otherElement: Record<string, object>[];
    id: string | null;
    otherAttributes: Record<string, object>;
    helpText: string[];
}

/** Instantiate a default object of type ParallelProps */
export declare const defaultParallel: () => ParallelProps;

/**
 * coordinates concurrent regions.
*/
/** Type for an array of of ParallelProps */
export type ParallelArray = ParallelProps[];

/**
 * parameter passed to `<invoke>` or `<send>`.
*/
export interface ParamProps {
    otherElement: Record<string, object>[];
    name: string;
    expr: string | null;
    location: string | null;
    otherAttributes: Record<string, object>;
    helpText: string[];
}

/** Instantiate a default object of type ParamProps */
export declare const defaultParam: () => ParamProps;

/**
 * parameter passed to `<invoke>` or `<send>`.
*/
/** Type for an array of of ParamProps */
export type ParamArray = ParamProps[];

/**
 * raise an internal event.
*/
export interface RaiseProps {
    event: string;
    otherAttributes: Record<string, object>;
    helpText: string[];
}

/** Instantiate a default object of type RaiseProps */
export declare const defaultRaise: () => RaiseProps;

/**
 * raise an internal event.
*/
/** Type for an array of of RaiseProps */
export type RaiseArray = RaiseProps[];

/**
 * inline executable script.
*/
export interface ScriptProps {
    src: string | null;
    otherAttributes: Record<string, object>;
    helpText: string[];
    content: Record<string, object>[];
}

/** Instantiate a default object of type ScriptProps */
export declare const defaultScript: () => ScriptProps;

/**
 * inline executable script.
*/
/** Type for an array of of ScriptProps */
export type ScriptArray = ScriptProps[];

/**
 * root element of an SCJSON document.
*/
export interface ScxmlProps {
    state: StateProps[];
    parallel: ParallelProps[];
    final: FinalProps[];
    datamodel: DatamodelProps[];
    script: ScriptProps[];
    otherElement: Record<string, object>[];
    initial: string[];
    name: string | null;
    version: number | string;
    datamodelAttribute: string;
    binding: typeof BindingDatatypeProps | null;
    exmode: typeof ExmodeDatatypeProps | null;
    otherAttributes: Record<string, object>;
    helpText: string[];
}

/** Instantiate a default object of type ScxmlProps */
export declare const defaultScxml: () => ScxmlProps;

/**
 * dispatch an external event.
*/
export interface SendProps {
    content: ContentProps[];
    param: ParamProps[];
    otherElement: Record<string, object>[];
    event: string | null;
    eventexpr: string | null;
    target: string | null;
    targetexpr: string | null;
    typeValue: string;
    typeexpr: string | null;
    id: string | null;
    idlocation: string | null;
    delay: string;
    delayexpr: string | null;
    namelist: string | null;
    otherAttributes: Record<string, object>;
    helpText: string[];
}

/** Instantiate a default object of type SendProps */
export declare const defaultSend: () => SendProps;

/**
 * dispatch an external event.
*/
/** Type for an array of of SendProps */
export type SendArray = SendProps[];

/**
 * basic state node.
*/
export interface StateProps {
    onentry: OnentryProps[];
    onexit: OnexitProps[];
    transition: TransitionProps[];
    initial: InitialProps[];
    state: StateProps[];
    parallel: ParallelProps[];
    final: FinalProps[];
    history: HistoryProps[];
    datamodel: DatamodelProps[];
    invoke: InvokeProps[];
    otherElement: Record<string, object>[];
    id: string | null;
    initialAttribute: string[];
    otherAttributes: Record<string, object>;
    helpText: string[];
}

/** Instantiate a default object of type StateProps */
export declare const defaultState: () => StateProps;

/**
 * basic state node.
*/
/** Type for an array of of StateProps */
export type StateArray = StateProps[];

/**
 * edge between states triggered by events.
*/
export interface TransitionProps {
    otherElement: Record<string, object>[];
    raiseValue: RaiseProps[];
    ifValue: IfProps[];
    foreach: ForeachProps[];
    send: SendProps[];
    script: ScriptProps[];
    assign: AssignProps[];
    log: LogProps[];
    cancel: CancelProps[];
    event: string | null;
    cond: string | null;
    target: string[];
    typeValue: typeof TransitionTypeDatatypeProps | null;
    otherAttributes: Record<string, object>;
    helpText: string[];
    executionOrder?: string[];
}

/** Instantiate a default object of type TransitionProps */
export declare const defaultTransition: () => TransitionProps;

/**
 * edge between states triggered by events.
*/
/** Type for an array of of TransitionProps */
export type TransitionArray = TransitionProps[];

/**
 * The type of the transition i.e. internal or external.
*/
export type TransitionTypeDatatypePropsType =
    | "external"
    | "internal"
;

export declare const TransitionTypeDatatypeProps: {
    readonly External: "external",
    readonly Internal: "internal",
};

/**
 * Preserve an extension element's qualified name, attributes and mixed text.
*/
export interface XmlPayloadElementProps {
    qname: string;
    text: string | null;
    tail: string | null;
    children: XmlPayloadElementProps[];
    attributes: Record<string, string>;
}

/** Instantiate a default object of type XmlPayloadElementProps */
export declare const defaultXmlPayloadElement: () => XmlPayloadElementProps;

/**
 * Preserve an extension element's qualified name, attributes and mixed text.
*/
/** Type for an array of of XmlPayloadElementProps */
export type XmlPayloadElementArray = XmlPayloadElementProps[];

export type Kind = "number" | "string" | "record<string, object>" | "number[]" | "string[]"
                   | "record<string, object>[]" | "assign" | "assigntypedatatype" | "bindingdatatype" | "booleandatatype"
                   | "cancel" | "content" | "data" | "datamodel" | "donedata" | "else" | "elseif"
                   | "exmodedatatype" | "final" | "finalize" | "foreach" | "history" | "historytypedatatype" | "if"
                   | "initial" | "invoke" | "log" | "onentry" | "onexit" | "parallel" | "param" | "raise"
                   | "script" | "scxml" | "send" | "state" | "transition" | "transitiontypedatatype"
                   | "xmlpayloadelement" | "assignarray" | "cancelarray" | "contentarray" | "dataarray"
                   | "datamodelarray" | "donedataarray" | "finalarray" | "finalizearray" | "foreacharray"
                   | "historyarray" | "ifarray" | "initialarray" | "invokearray" | "logarray" | "onentryarray"
                   | "onexitarray" | "parallelarray" | "paramarray" | "raisearray" | "scriptarray" | "sendarray"
                   | "statearray" | "transitionarray" | "xmlpayloadelementarray";

export type PropsUnion = null | string | number | Record<string, object> | string[] | number[]
                         | Record<string, object>[] | AssignProps | typeof AssignTypeDatatypeProps | typeof BindingDatatypeProps
                         | typeof BooleanDatatypeProps | CancelProps | ContentProps | DataProps | DatamodelProps | DonedataProps
                         | ElseProps | ElseifProps | typeof ExmodeDatatypeProps | FinalProps | FinalizeProps
                         | ForeachProps | HistoryProps | typeof HistoryTypeDatatypeProps | IfProps | InitialProps
                         | InvokeProps | LogProps | OnentryProps | OnexitProps | ParallelProps | ParamProps
                         | RaiseProps | ScriptProps | ScxmlProps | SendProps | StateProps | TransitionProps
                         | typeof TransitionTypeDatatypeProps | XmlPayloadElementProps | AssignArray | CancelArray | ContentArray | DataArray
                         | DatamodelArray | DonedataArray | FinalArray | FinalizeArray | ForeachArray | HistoryArray
                         | IfArray | InitialArray | InvokeArray | LogArray | OnentryArray | OnexitArray
                         | ParallelArray | ParamArray | RaiseArray | ScriptArray | SendArray | StateArray
                         | TransitionArray | XmlPayloadElementArray;

export type KindMap = {
    assign: AssignProps
    assignarray: AssignArray
    assigntypedatatype: typeof AssignTypeDatatypeProps
    bindingdatatype: typeof BindingDatatypeProps
    booleandatatype: typeof BooleanDatatypeProps
    cancel: CancelProps
    cancelarray: CancelArray
    content: ContentProps
    contentarray: ContentArray
    data: DataProps
    dataarray: DataArray
    datamodel: DatamodelProps
    datamodelarray: DatamodelArray
    donedata: DonedataProps
    donedataarray: DonedataArray
    else: ElseProps
    elseif: ElseifProps
    exmodedatatype: typeof ExmodeDatatypeProps
    final: FinalProps
    finalarray: FinalArray
    finalize: FinalizeProps
    finalizearray: FinalizeArray
    foreach: ForeachProps
    foreacharray: ForeachArray
    history: HistoryProps
    historyarray: HistoryArray
    historytypedatatype: typeof HistoryTypeDatatypeProps
    if: IfProps
    ifarray: IfArray
    initial: InitialProps
    initialarray: InitialArray
    invoke: InvokeProps
    invokearray: InvokeArray
    log: LogProps
    logarray: LogArray
    onentry: OnentryProps
    onentryarray: OnentryArray
    onexit: OnexitProps
    onexitarray: OnexitArray
    parallel: ParallelProps
    parallelarray: ParallelArray
    param: ParamProps
    paramarray: ParamArray
    raise: RaiseProps
    raisearray: RaiseArray
    script: ScriptProps
    scriptarray: ScriptArray
    scxml: ScxmlProps
    send: SendProps
    sendarray: SendArray
    state: StateProps
    statearray: StateArray
    transition: TransitionProps
    transitionarray: TransitionArray
    transitiontypedatatype: typeof TransitionTypeDatatypeProps
    xmlpayloadelement: XmlPayloadElementProps
    xmlpayloadelementarray: XmlPayloadElementArray
}

