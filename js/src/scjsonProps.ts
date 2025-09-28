/**
 * Agent Name: ts-props
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
    typeValue: AssignTypeDatatypeProps;
    attr: string | null;
    otherAttributes: Record<string, object>;
    content: Record<string, object>[];
}

/** Instantiate a default object of type AssignProps */
export const defaultAssign = (): AssignProps => ({
    location: "",
    expr: null,
    typeValue: AssignTypeDatatypeProps.Replacechildren,
    attr: null,
    otherAttributes: {},
    content: [],
});

/**
 * update a datamodel location with an expression or value.
*/
/** Type for an array of of AssignProps */
export type AssignArray = AssignProps[];

/**
 * The assign type that allows for precise manipulation of the datamodel
 *     location.
 *     Types are:
 *     replacechildren (default),
 *     firstchild, lastchild,
 *     previoussibling, nextsibling,
 *     replace, delete,
 *     addattribute
*/
export const AssignTypeDatatypeProps = {
    Addattribute: "addattribute",
    Delete: "delete",
    Firstchild: "firstchild",
    Lastchild: "lastchild",
    Nextsibling: "nextsibling",
    Previoussibling: "previoussibling",
    Replace: "replace",
    Replacechildren: "replacechildren",
} as const;
/** executable version of AssignTypeDatatypeProps */
export type AssignTypeDatatypeProps = typeof AssignTypeDatatypeProps[keyof typeof AssignTypeDatatypeProps];

/**
 *     The binding type in use for the SCXML document.
*/
export const BindingDatatypeProps = {
    Early: "early",
    Late: "late",
} as const;
/** executable version of BindingDatatypeProps */
export type BindingDatatypeProps = typeof BindingDatatypeProps[keyof typeof BindingDatatypeProps];

/**
 * Boolean: true or false only
*/
export const BooleanDatatypeProps = {
    False: "false",
    True: "true",
} as const;
/** executable version of BooleanDatatypeProps */
export type BooleanDatatypeProps = typeof BooleanDatatypeProps[keyof typeof BooleanDatatypeProps];

/**
 * cancel a pending `<send>` operation.
*/
export interface CancelProps {
    otherElement: Record<string, object>[];
    sendid: string | null;
    sendidexpr: string | null;
    otherAttributes: Record<string, object>;
}

/** Instantiate a default object of type CancelProps */
export const defaultCancel = (): CancelProps => ({
    otherElement: [],
    sendid: null,
    sendidexpr: null,
    otherAttributes: {},
});

/**
 * cancel a pending `<send>` operation.
*/
/** Type for an array of of CancelProps */
export type CancelArray = CancelProps[];

/**
 * inline payload used by `<send>` and `<invoke>`.
*/
export interface ContentProps {
    content: ScxmlProps[] | null;
    expr: string | null;
    otherAttributes: Record<string, object>;
}

/** Instantiate a default object of type ContentProps */
export const defaultContent = (): ContentProps => ({
    content: null,
    expr: null,
    otherAttributes: {},
});

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
    content: Record<string, object>[];
}

/** Instantiate a default object of type DataProps */
export const defaultData = (): DataProps => ({
    id: "",
    src: null,
    expr: null,
    otherAttributes: {},
    content: [],
});

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
}

/** Instantiate a default object of type DatamodelProps */
export const defaultDatamodel = (): DatamodelProps => ({
    data: [],
    otherElement: [],
    otherAttributes: {},
});

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
}

/** Instantiate a default object of type DonedataProps */
export const defaultDonedata = (): DonedataProps => ({
    content: null,
    param: [],
    otherAttributes: {},
});

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
}

/** Instantiate a default object of type ElseProps */
export const defaultElse = (): ElseProps => ({
    otherAttributes: {},
});

/**
 * conditional branch following an `<if>`.
*/
export interface ElseifProps {
    cond: string;
    otherAttributes: Record<string, object>;
}

/** Instantiate a default object of type ElseifProps */
export const defaultElseif = (): ElseifProps => ({
    cond: "",
    otherAttributes: {},
});

/**
 *     Describes the processor execution mode for this document, being either "lax"
 * or
 *     "strict".
*/
export const ExmodeDatatypeProps = {
    Lax: "lax",
    Strict: "strict",
} as const;
/** executable version of ExmodeDatatypeProps */
export type ExmodeDatatypeProps = typeof ExmodeDatatypeProps[keyof typeof ExmodeDatatypeProps];

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
}

/** Instantiate a default object of type FinalProps */
export const defaultFinal = (): FinalProps => ({
    onentry: [],
    onexit: [],
    donedata: [],
    otherElement: [],
    id: null,
    otherAttributes: {},
});

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
}

/** Instantiate a default object of type FinalizeProps */
export const defaultFinalize = (): FinalizeProps => ({
    otherElement: [],
    raiseValue: [],
    ifValue: [],
    foreach: [],
    send: [],
    script: [],
    assign: [],
    log: [],
    cancel: [],
    otherAttributes: {},
});

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
}

/** Instantiate a default object of type ForeachProps */
export const defaultForeach = (): ForeachProps => ({
    otherElement: [],
    raiseValue: [],
    ifValue: [],
    foreach: [],
    send: [],
    script: [],
    assign: [],
    log: [],
    cancel: [],
    array: "",
    item: "",
    index: null,
    otherAttributes: {},
});

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
    typeValue: HistoryTypeDatatypeProps | null;
    otherAttributes: Record<string, object>;
}

/** Instantiate a default object of type HistoryProps */
export const defaultHistory = (): HistoryProps => ({
    otherElement: [],
    transition: defaultTransition(),
    id: null,
    typeValue: null,
    otherAttributes: {},
});

/**
 * pseudostate remembering previous active children.
*/
/** Type for an array of of HistoryProps */
export type HistoryArray = HistoryProps[];

/**
 * type of `<history>` state: `shallow` or `deep`.
*/
export const HistoryTypeDatatypeProps = {
    Deep: "deep",
    Shallow: "shallow",
} as const;
/** executable version of HistoryTypeDatatypeProps */
export type HistoryTypeDatatypeProps = typeof HistoryTypeDatatypeProps[keyof typeof HistoryTypeDatatypeProps];

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
    elseif: ElseifProps | null;
    elseValue: ElseProps | null;
    cond: string;
    otherAttributes: Record<string, object>;
}

/** Instantiate a default object of type IfProps */
export const defaultIf = (): IfProps => ({
    otherElement: [],
    raiseValue: [],
    ifValue: [],
    foreach: [],
    send: [],
    script: [],
    assign: [],
    log: [],
    cancel: [],
    elseif: null,
    elseValue: null,
    cond: "",
    otherAttributes: {},
});

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
}

/** Instantiate a default object of type InitialProps */
export const defaultInitial = (): InitialProps => ({
    otherElement: [],
    transition: defaultTransition(),
    otherAttributes: {},
});

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
    autoforward: BooleanDatatypeProps;
    otherAttributes: Record<string, object>;
}

/** Instantiate a default object of type InvokeProps */
export const defaultInvoke = (): InvokeProps => ({
    content: [],
    param: [],
    finalize: [],
    otherElement: [],
    typeValue: "scxml",
    typeexpr: null,
    src: null,
    srcexpr: null,
    id: null,
    idlocation: null,
    namelist: null,
    autoforward: BooleanDatatypeProps.False,
    otherAttributes: {},
});

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
}

/** Instantiate a default object of type LogProps */
export const defaultLog = (): LogProps => ({
    otherElement: [],
    label: null,
    expr: null,
    otherAttributes: {},
});

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
}

/** Instantiate a default object of type OnentryProps */
export const defaultOnentry = (): OnentryProps => ({
    otherElement: [],
    raiseValue: [],
    ifValue: [],
    foreach: [],
    send: [],
    script: [],
    assign: [],
    log: [],
    cancel: [],
    otherAttributes: {},
});

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
}

/** Instantiate a default object of type OnexitProps */
export const defaultOnexit = (): OnexitProps => ({
    otherElement: [],
    raiseValue: [],
    ifValue: [],
    foreach: [],
    send: [],
    script: [],
    assign: [],
    log: [],
    cancel: [],
    otherAttributes: {},
});

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
}

/** Instantiate a default object of type ParallelProps */
export const defaultParallel = (): ParallelProps => ({
    onentry: [],
    onexit: [],
    transition: [],
    state: [],
    parallel: [],
    history: [],
    datamodel: [],
    invoke: [],
    otherElement: [],
    id: null,
    otherAttributes: {},
});

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
}

/** Instantiate a default object of type ParamProps */
export const defaultParam = (): ParamProps => ({
    otherElement: [],
    name: "",
    expr: null,
    location: null,
    otherAttributes: {},
});

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
}

/** Instantiate a default object of type RaiseProps */
export const defaultRaise = (): RaiseProps => ({
    event: "",
    otherAttributes: {},
});

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
    content: Record<string, object>[];
}

/** Instantiate a default object of type ScriptProps */
export const defaultScript = (): ScriptProps => ({
    src: null,
    otherAttributes: {},
    content: [],
});

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
    binding: BindingDatatypeProps | null;
    exmode: ExmodeDatatypeProps | null;
    otherAttributes: Record<string, object>;
}

/** Instantiate a default object of type ScxmlProps */
export const defaultScxml = (): ScxmlProps => ({
    state: [],
    parallel: [],
    final: [],
    datamodel: [],
    script: [],
    otherElement: [],
    initial: [],
    name: null,
    version: 1.0,
    datamodelAttribute: "null",
    binding: null,
    exmode: null,
    otherAttributes: {},
});

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
}

/** Instantiate a default object of type SendProps */
export const defaultSend = (): SendProps => ({
    content: [],
    param: [],
    otherElement: [],
    event: null,
    eventexpr: null,
    target: null,
    targetexpr: null,
    typeValue: "scxml",
    typeexpr: null,
    id: null,
    idlocation: null,
    delay: "0s",
    delayexpr: null,
    namelist: null,
    otherAttributes: {},
});

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
}

/** Instantiate a default object of type StateProps */
export const defaultState = (): StateProps => ({
    onentry: [],
    onexit: [],
    transition: [],
    initial: [],
    state: [],
    parallel: [],
    final: [],
    history: [],
    datamodel: [],
    invoke: [],
    otherElement: [],
    id: null,
    initialAttribute: [],
    otherAttributes: {},
});

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
    typeValue: TransitionTypeDatatypeProps | null;
    otherAttributes: Record<string, object>;
}

/** Instantiate a default object of type TransitionProps */
export const defaultTransition = (): TransitionProps => ({
    otherElement: [],
    raiseValue: [],
    ifValue: [],
    foreach: [],
    send: [],
    script: [],
    assign: [],
    log: [],
    cancel: [],
    event: null,
    cond: null,
    target: [],
    typeValue: null,
    otherAttributes: {},
});

/**
 * edge between states triggered by events.
*/
/** Type for an array of of TransitionProps */
export type TransitionArray = TransitionProps[];

/**
 *     The type of the transition i.e. internal or external.
*/
export const TransitionTypeDatatypeProps = {
    External: "external",
    Internal: "internal",
} as const;
/** executable version of TransitionTypeDatatypeProps */
export type TransitionTypeDatatypeProps = typeof TransitionTypeDatatypeProps[keyof typeof TransitionTypeDatatypeProps];

export type Kind = "number" | "string" | "record<string, object>" | "number[]" | "string[]"
                   | "record<string, object>[]" | "assign" | "assigntypedatatype" | "bindingdatatype" | "booleandatatype"
                   | "cancel" | "content" | "data" | "datamodel" | "donedata" | "else" | "elseif"
                   | "exmodedatatype" | "final" | "finalize" | "foreach" | "history" | "historytypedatatype" | "if"
                   | "initial" | "invoke" | "log" | "onentry" | "onexit" | "parallel" | "param" | "raise"
                   | "script" | "scxml" | "send" | "state" | "transition" | "transitiontypedatatype"
                   | "assignarray" | "cancelarray" | "contentarray" | "dataarray" | "datamodelarray"
                   | "donedataarray" | "finalarray" | "finalizearray" | "foreacharray" | "historyarray" | "ifarray"
                   | "initialarray" | "invokearray" | "logarray" | "onentryarray" | "onexitarray" | "parallelarray"
                   | "paramarray" | "raisearray" | "scriptarray" | "sendarray" | "statearray" | "transitionarray";

export type PropsUnion = null | string | number | Record<string, object> | string[] | number[]
                         | Record<string, object>[] | AssignProps | AssignTypeDatatypeProps | BindingDatatypeProps
                         | BooleanDatatypeProps | CancelProps | ContentProps | DataProps | DatamodelProps | DonedataProps
                         | ElseProps | ElseifProps | ExmodeDatatypeProps | FinalProps | FinalizeProps | ForeachProps
                         | HistoryProps | HistoryTypeDatatypeProps | IfProps | InitialProps | InvokeProps | LogProps
                         | OnentryProps | OnexitProps | ParallelProps | ParamProps | RaiseProps | ScriptProps
                         | ScxmlProps | SendProps | StateProps | TransitionProps | TransitionTypeDatatypeProps
                         | AssignArray | CancelArray | ContentArray | DataArray | DatamodelArray | DonedataArray
                         | FinalArray | FinalizeArray | ForeachArray | HistoryArray | IfArray | InitialArray
                         | InvokeArray | LogArray | OnentryArray | OnexitArray | ParallelArray | ParamArray
                         | RaiseArray | ScriptArray | SendArray | StateArray | TransitionArray;

export type KindMap = {
    assign: AssignProps
    assignarray: AssignArray
    assigntypedatatype: AssignTypeDatatypeProps
    bindingdatatype: BindingDatatypeProps
    booleandatatype: BooleanDatatypeProps
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
    exmodedatatype: ExmodeDatatypeProps
    final: FinalProps
    finalarray: FinalArray
    finalize: FinalizeProps
    finalizearray: FinalizeArray
    foreach: ForeachProps
    foreacharray: ForeachArray
    history: HistoryProps
    historyarray: HistoryArray
    historytypedatatype: HistoryTypeDatatypeProps
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
    transitiontypedatatype: TransitionTypeDatatypeProps
}

