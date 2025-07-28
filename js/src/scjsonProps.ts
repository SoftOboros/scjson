/**
 * Agent Name: ts-props
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
*/

export interface AssignProps {
    location: string;
    expr: string | null;
    typeValue: AssignTypeDatatypeProps;
    attr: string | null;
    otherAttributes: Record<string, object>;
    content: Record<string, object>[];
}

export const defaultAssign = (): AssignProps => ({
    location: "",
    expr: null,
    typeValue: AssignTypeDatatypeProps.Replacechildren,
    attr: null,
    otherAttributes: {},
    content: [],
});

export type AssignArray = AssignProps[];

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

export type AssignTypeDatatypeProps = typeof AssignTypeDatatypeProps[keyof typeof AssignTypeDatatypeProps];

export const BindingDatatypeProps = {
    Early: "early",
    Late: "late",
} as const;

export type BindingDatatypeProps = typeof BindingDatatypeProps[keyof typeof BindingDatatypeProps];

export const BooleanDatatypeProps = {
    False: "false",
    True: "true",
} as const;

export type BooleanDatatypeProps = typeof BooleanDatatypeProps[keyof typeof BooleanDatatypeProps];

export interface CancelProps {
    otherElement: Record<string, object>[];
    sendid: string | null;
    sendidexpr: string | null;
    otherAttributes: Record<string, object>;
}

export const defaultCancel = (): CancelProps => ({
    otherElement: [],
    sendid: null,
    sendidexpr: null,
    otherAttributes: {},
});

export type CancelArray = CancelProps[];

export interface ContentProps {
    content: ScxmlProps[] | null;
    expr: string | null;
    otherAttributes: Record<string, object>;
}

export const defaultContent = (): ContentProps => ({
    content: null,
    expr: null,
    otherAttributes: {},
});

export type ContentArray = ContentProps[];

export interface DataProps {
    id: string;
    src: string | null;
    expr: string | null;
    otherAttributes: Record<string, object>;
    content: Record<string, object>[];
}

export const defaultData = (): DataProps => ({
    id: "",
    src: null,
    expr: null,
    otherAttributes: {},
    content: [],
});

export type DataArray = DataProps[];

export interface DatamodelProps {
    data: DataProps[];
    otherElement: Record<string, object>[];
    otherAttributes: Record<string, object>;
}

export const defaultDatamodel = (): DatamodelProps => ({
    data: [],
    otherElement: [],
    otherAttributes: {},
});

export type DatamodelArray = DatamodelProps[];

export interface DonedataProps {
    content: ContentProps | null;
    param: ParamProps[];
    otherAttributes: Record<string, object>;
}

export const defaultDonedata = (): DonedataProps => ({
    content: null,
    param: [],
    otherAttributes: {},
});

export type DonedataArray = DonedataProps[];

export interface ElseProps {
    otherAttributes: Record<string, object>;
}

export const defaultElse = (): ElseProps => ({
    otherAttributes: {},
});

export interface ElseifProps {
    cond: string;
    otherAttributes: Record<string, object>;
}

export const defaultElseif = (): ElseifProps => ({
    cond: "",
    otherAttributes: {},
});

export const ExmodeDatatypeProps = {
    Lax: "lax",
    Strict: "strict",
} as const;

export type ExmodeDatatypeProps = typeof ExmodeDatatypeProps[keyof typeof ExmodeDatatypeProps];

export interface FinalProps {
    onentry: OnentryProps[];
    onexit: OnexitProps[];
    donedata: DonedataProps[];
    otherElement: Record<string, object>[];
    id: string | null;
    otherAttributes: Record<string, object>;
}

export const defaultFinal = (): FinalProps => ({
    onentry: [],
    onexit: [],
    donedata: [],
    otherElement: [],
    id: null,
    otherAttributes: {},
});

export type FinalArray = FinalProps[];

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

export type FinalizeArray = FinalizeProps[];

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

export type ForeachArray = ForeachProps[];

export interface HistoryProps {
    otherElement: Record<string, object>[];
    transition: TransitionProps;
    id: string | null;
    typeValue: HistoryTypeDatatypeProps | null;
    otherAttributes: Record<string, object>;
}

export const defaultHistory = (): HistoryProps => ({
    otherElement: [],
    transition: defaultTransition(),
    id: null,
    typeValue: null,
    otherAttributes: {},
});

export type HistoryArray = HistoryProps[];

export const HistoryTypeDatatypeProps = {
    Deep: "deep",
    Shallow: "shallow",
} as const;

export type HistoryTypeDatatypeProps = typeof HistoryTypeDatatypeProps[keyof typeof HistoryTypeDatatypeProps];

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

export type IfArray = IfProps[];

export interface InitialProps {
    otherElement: Record<string, object>[];
    transition: TransitionProps;
    otherAttributes: Record<string, object>;
}

export const defaultInitial = (): InitialProps => ({
    otherElement: [],
    transition: defaultTransition(),
    otherAttributes: {},
});

export type InitialArray = InitialProps[];

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

export type InvokeArray = InvokeProps[];

export interface LogProps {
    otherElement: Record<string, object>[];
    label: string | null;
    expr: string | null;
    otherAttributes: Record<string, object>;
}

export const defaultLog = (): LogProps => ({
    otherElement: [],
    label: null,
    expr: null,
    otherAttributes: {},
});

export type LogArray = LogProps[];

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

export type OnentryArray = OnentryProps[];

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

export type OnexitArray = OnexitProps[];

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

export type ParallelArray = ParallelProps[];

export interface ParamProps {
    otherElement: Record<string, object>[];
    name: string;
    expr: string | null;
    location: string | null;
    otherAttributes: Record<string, object>;
}

export const defaultParam = (): ParamProps => ({
    otherElement: [],
    name: "",
    expr: null,
    location: null,
    otherAttributes: {},
});

export type ParamArray = ParamProps[];

export interface RaiseProps {
    event: string;
    otherAttributes: Record<string, object>;
}

export const defaultRaise = (): RaiseProps => ({
    event: "",
    otherAttributes: {},
});

export type RaiseArray = RaiseProps[];

export interface ScriptProps {
    src: string | null;
    otherAttributes: Record<string, object>;
    content: Record<string, object>[];
}

export const defaultScript = (): ScriptProps => ({
    src: null,
    otherAttributes: {},
    content: [],
});

export type ScriptArray = ScriptProps[];

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

export type SendArray = SendProps[];

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

export type StateArray = StateProps[];

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

export type TransitionArray = TransitionProps[];

export const TransitionTypeDatatypeProps = {
    External: "external",
    Internal: "internal",
} as const;

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

