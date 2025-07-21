/**
 * scjsonProps.d.ts : Properties definition file for scjson types
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */

export interface AssignProps {
    location: string;
    expr: string | null;
    typeValue: typeof AssignTypeDatatypeProps;
    attr: string | null;
    otherAttributes: Record<string, object>;
    content: Record<string, object>[];
}

export declare const defaultAssign: () => AssignProps;

export type AssignArray = AssignProps[];

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

export type BindingDatatypePropsType =
    | "early"
    | "late"
;

export declare const BindingDatatypeProps: {
    readonly Early: "early",
    readonly Late: "late",
};

export type BooleanDatatypePropsType =
    | "false"
    | "true"
;

export declare const BooleanDatatypeProps: {
    readonly False: "false",
    readonly True: "true",
};

export interface CancelProps {
    otherElement: Record<string, object>[];
    sendid: string | null;
    sendidexpr: string | null;
    otherAttributes: Record<string, object>;
}

export declare const defaultCancel: () => CancelProps;

export type CancelArray = CancelProps[];

export interface ContentProps {
    otherAttributes: Record<string, object>;
    expr: string | null;
    content: Record<string, object>[];
}

export declare const defaultContent: () => ContentProps;

export type ContentArray = ContentProps[];

export interface DataProps {
    id: string;
    src: string | null;
    expr: string | null;
    otherAttributes: Record<string, object>;
    content: Record<string, object>[];
}

export declare const defaultData: () => DataProps;

export type DataArray = DataProps[];

export interface DatamodelProps {
    data: DataProps[];
    otherElement: Record<string, object>[];
    otherAttributes: Record<string, object>;
}

export declare const defaultDatamodel: () => DatamodelProps;

export type DatamodelArray = DatamodelProps[];

export interface DonedataProps {
    content: ContentProps | null;
    param: ParamProps[];
    otherAttributes: Record<string, object>;
}

export declare const defaultDonedata: () => DonedataProps;

export type DonedataArray = DonedataProps[];

export interface ElseProps {
    otherAttributes: Record<string, object>;
}

export declare const defaultElse: () => ElseProps;

export interface ElseifProps {
    cond: string;
    otherAttributes: Record<string, object>;
}

export declare const defaultElseif: () => ElseifProps;

export type ExmodeDatatypePropsType =
    | "lax"
    | "strict"
;

export declare const ExmodeDatatypeProps: {
    readonly Lax: "lax",
    readonly Strict: "strict",
};

export interface FinalProps {
    onentry: OnentryProps[];
    onexit: OnexitProps[];
    donedata: DonedataProps[];
    otherElement: Record<string, object>[];
    id: string | null;
    otherAttributes: Record<string, object>;
}

export declare const defaultFinal: () => FinalProps;

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

export declare const defaultFinalize: () => FinalizeProps;

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

export declare const defaultForeach: () => ForeachProps;

export type ForeachArray = ForeachProps[];

export interface HistoryProps {
    otherElement: Record<string, object>[];
    transition: TransitionProps;
    id: string | null;
    typeValue: typeof HistoryTypeDatatypeProps | null;
    otherAttributes: Record<string, object>;
}

export declare const defaultHistory: () => HistoryProps;

export type HistoryArray = HistoryProps[];

export type HistoryTypeDatatypePropsType =
    | "deep"
    | "shallow"
;

export declare const HistoryTypeDatatypeProps: {
    readonly Deep: "deep",
    readonly Shallow: "shallow",
};

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

export declare const defaultIf: () => IfProps;

export type IfArray = IfProps[];

export interface InitialProps {
    otherElement: Record<string, object>[];
    transition: TransitionProps;
    otherAttributes: Record<string, object>;
}

export declare const defaultInitial: () => InitialProps;

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
    autoforward: typeof BooleanDatatypeProps;
    otherAttributes: Record<string, object>;
}

export declare const defaultInvoke: () => InvokeProps;

export type InvokeArray = InvokeProps[];

export interface LogProps {
    otherElement: Record<string, object>[];
    label: string | null;
    expr: string | null;
    otherAttributes: Record<string, object>;
}

export declare const defaultLog: () => LogProps;

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

export declare const defaultOnentry: () => OnentryProps;

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

export declare const defaultOnexit: () => OnexitProps;

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

export declare const defaultParallel: () => ParallelProps;

export type ParallelArray = ParallelProps[];

export interface ParamProps {
    otherElement: Record<string, object>[];
    name: string;
    expr: string | null;
    location: string | null;
    otherAttributes: Record<string, object>;
}

export declare const defaultParam: () => ParamProps;

export type ParamArray = ParamProps[];

export interface RaiseProps {
    event: string;
    otherAttributes: Record<string, object>;
}

export declare const defaultRaise: () => RaiseProps;

export type RaiseArray = RaiseProps[];

export interface ScriptProps {
    src: string | null;
    otherAttributes: Record<string, object>;
    content: Record<string, object>[];
}

export declare const defaultScript: () => ScriptProps;

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
    binding: typeof BindingDatatypeProps | null;
    exmode: typeof ExmodeDatatypeProps | null;
    otherAttributes: Record<string, object>;
}

export declare const defaultScxml: () => ScxmlProps;

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

export declare const defaultSend: () => SendProps;

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

export declare const defaultState: () => StateProps;

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
    typeValue: typeof TransitionTypeDatatypeProps | null;
    otherAttributes: Record<string, object>;
}

export declare const defaultTransition: () => TransitionProps;

export type TransitionArray = TransitionProps[];

export type TransitionTypeDatatypePropsType =
    | "external"
    | "internal"
;

export declare const TransitionTypeDatatypeProps: {
    readonly External: "external",
    readonly Internal: "internal",
};

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
                         | Record<string, object>[] | AssignProps | typeof AssignTypeDatatypeProps | typeof BindingDatatypeProps
                         | typeof BooleanDatatypeProps | CancelProps | ContentProps | DataProps | DatamodelProps | DonedataProps
                         | ElseProps | ElseifProps | typeof ExmodeDatatypeProps | FinalProps | FinalizeProps
                         | ForeachProps | HistoryProps | typeof HistoryTypeDatatypeProps | IfProps | InitialProps
                         | InvokeProps | LogProps | OnentryProps | OnexitProps | ParallelProps | ParamProps
                         | RaiseProps | ScriptProps | ScxmlProps | SendProps | StateProps | TransitionProps
                         | typeof TransitionTypeDatatypeProps | AssignArray | CancelArray | ContentArray | DataArray | DatamodelArray
                         | DonedataArray | FinalArray | FinalizeArray | ForeachArray | HistoryArray | IfArray
                         | InitialArray | InvokeArray | LogArray | OnentryArray | OnexitArray | ParallelArray
                         | ParamArray | RaiseArray | ScriptArray | SendArray | StateArray | TransitionArray;

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
}

