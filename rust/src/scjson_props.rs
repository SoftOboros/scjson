// scjson_props.rs : Properties file for scjson types
//
// Part of the scjson project.
// Developed by Softoboros Technology Inc.
// Licensed under the BSD 1-Clause License.
use serde::{Serialize, Deserialize};
use serde_json::{Map, Value};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum AssignTypeDatatypeProps {
    #[serde(rename = "replacechildren")]
    Replacechildren,
    #[serde(rename = "firstchild")]
    Firstchild,
    #[serde(rename = "lastchild")]
    Lastchild,
    #[serde(rename = "previoussibling")]
    Previoussibling,
    #[serde(rename = "nextsibling")]
    Nextsibling,
    #[serde(rename = "replace")]
    Replace,
    #[serde(rename = "delete")]
    Delete,
    #[serde(rename = "addattribute")]
    Addattribute,
}

pub fn default_assigntypedatatype() -> AssignTypeDatatypeProps {
    AssignTypeDatatypeProps::Replacechildren
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum BindingDatatypeProps {
    #[serde(rename = "early")]
    Early,
    #[serde(rename = "late")]
    Late,
}

pub fn default_bindingdatatype() -> BindingDatatypeProps {
    BindingDatatypeProps::Early
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum BooleanDatatypeProps {
    #[serde(rename = "true")]
    True,
    #[serde(rename = "false")]
    False,
}

pub fn default_booleandatatype() -> BooleanDatatypeProps {
    BooleanDatatypeProps::True
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum ExmodeDatatypeProps {
    #[serde(rename = "lax")]
    Lax,
    #[serde(rename = "strict")]
    Strict,
}

pub fn default_exmodedatatype() -> ExmodeDatatypeProps {
    ExmodeDatatypeProps::Lax
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum HistoryTypeDatatypeProps {
    #[serde(rename = "shallow")]
    Shallow,
    #[serde(rename = "deep")]
    Deep,
}

pub fn default_historytypedatatype() -> HistoryTypeDatatypeProps {
    HistoryTypeDatatypeProps::Shallow
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum TransitionTypeDatatypeProps {
    #[serde(rename = "internal")]
    Internal,
    #[serde(rename = "external")]
    External,
}

pub fn default_transitiontypedatatype() -> TransitionTypeDatatypeProps {
    TransitionTypeDatatypeProps::Internal
}


#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct AssignProps {
    pub location: String,
    pub expr: Option<String>,
    pub type_value: AssignTypeDatatypeProps,
    pub attr: Option<String>,
    pub other_attributes: Map<String, Value>,
    pub content: Vec<Map<String, Value>>,
}

pub fn default_assign() -> AssignProps {
    AssignProps {
        location: String::new(),
        expr: None,
        type_value: AssignTypeDatatypeProps::Replacechildren,
        attr: None,
        other_attributes: Map::new(),
        content: Vec::new(),
    }
}

pub type AssignArray = Vec<AssignProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CancelProps {
    pub other_element: Vec<Map<String, Value>>,
    pub sendid: Option<String>,
    pub sendidexpr: Option<String>,
    pub other_attributes: Map<String, Value>,
}

pub fn default_cancel() -> CancelProps {
    CancelProps {
        other_element: Vec::new(),
        sendid: None,
        sendidexpr: None,
        other_attributes: Map::new(),
    }
}

pub type CancelArray = Vec<CancelProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ContentProps {
    pub content: Option<Vec<ScxmlProps>>,
    pub expr: Option<String>,
    pub other_attributes: Map<String, Value>,
}

pub fn default_content() -> ContentProps {
    ContentProps {
        content: None,
        expr: None,
        other_attributes: Map::new(),
    }
}

pub type ContentArray = Vec<ContentProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct DataProps {
    pub id: String,
    pub src: Option<String>,
    pub expr: Option<String>,
    pub other_attributes: Map<String, Value>,
    pub content: Vec<Map<String, Value>>,
}

pub fn default_data() -> DataProps {
    DataProps {
        id: String::new(),
        src: None,
        expr: None,
        other_attributes: Map::new(),
        content: Vec::new(),
    }
}

pub type DataArray = Vec<DataProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct DatamodelProps {
    pub data: Vec<DataProps>,
    pub other_element: Vec<Map<String, Value>>,
    pub other_attributes: Map<String, Value>,
}

pub fn default_datamodel() -> DatamodelProps {
    DatamodelProps {
        data: Vec::new(),
        other_element: Vec::new(),
        other_attributes: Map::new(),
    }
}

pub type DatamodelArray = Vec<DatamodelProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct DonedataProps {
    pub content: Option<ContentProps>,
    pub param: Vec<ParamProps>,
    pub other_attributes: Map<String, Value>,
}

pub fn default_donedata() -> DonedataProps {
    DonedataProps {
        content: None,
        param: Vec::new(),
        other_attributes: Map::new(),
    }
}

pub type DonedataArray = Vec<DonedataProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ElseProps {
    pub other_attributes: Map<String, Value>,
}

pub fn default_else() -> ElseProps {
    ElseProps {
        other_attributes: Map::new(),
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ElseifProps {
    pub cond: String,
    pub other_attributes: Map<String, Value>,
}

pub fn default_elseif() -> ElseifProps {
    ElseifProps {
        cond: String::new(),
        other_attributes: Map::new(),
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct FinalProps {
    pub onentry: Vec<OnentryProps>,
    pub onexit: Vec<OnexitProps>,
    pub donedata: Vec<DonedataProps>,
    pub other_element: Vec<Map<String, Value>>,
    pub id: Option<String>,
    pub other_attributes: Map<String, Value>,
}

pub fn default_final() -> FinalProps {
    FinalProps {
        onentry: Vec::new(),
        onexit: Vec::new(),
        donedata: Vec::new(),
        other_element: Vec::new(),
        id: None,
        other_attributes: Map::new(),
    }
}

pub type FinalArray = Vec<FinalProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct FinalizeProps {
    pub other_element: Vec<Map<String, Value>>,
    pub raise_value: Vec<RaiseProps>,
    pub if_value: Vec<IfProps>,
    pub foreach: Vec<ForeachProps>,
    pub send: Vec<SendProps>,
    pub script: Vec<ScriptProps>,
    pub assign: Vec<AssignProps>,
    pub log: Vec<LogProps>,
    pub cancel: Vec<CancelProps>,
    pub other_attributes: Map<String, Value>,
}

pub fn default_finalize() -> FinalizeProps {
    FinalizeProps {
        other_element: Vec::new(),
        raise_value: Vec::new(),
        if_value: Vec::new(),
        foreach: Vec::new(),
        send: Vec::new(),
        script: Vec::new(),
        assign: Vec::new(),
        log: Vec::new(),
        cancel: Vec::new(),
        other_attributes: Map::new(),
    }
}

pub type FinalizeArray = Vec<FinalizeProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ForeachProps {
    pub other_element: Vec<Map<String, Value>>,
    pub raise_value: Vec<RaiseProps>,
    pub if_value: Vec<IfProps>,
    pub foreach: Vec<ForeachProps>,
    pub send: Vec<SendProps>,
    pub script: Vec<ScriptProps>,
    pub assign: Vec<AssignProps>,
    pub log: Vec<LogProps>,
    pub cancel: Vec<CancelProps>,
    pub array: String,
    pub item: String,
    pub index: Option<String>,
    pub other_attributes: Map<String, Value>,
}

pub fn default_foreach() -> ForeachProps {
    ForeachProps {
        other_element: Vec::new(),
        raise_value: Vec::new(),
        if_value: Vec::new(),
        foreach: Vec::new(),
        send: Vec::new(),
        script: Vec::new(),
        assign: Vec::new(),
        log: Vec::new(),
        cancel: Vec::new(),
        array: String::new(),
        item: String::new(),
        index: None,
        other_attributes: Map::new(),
    }
}

pub type ForeachArray = Vec<ForeachProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct HistoryProps {
    pub other_element: Vec<Map<String, Value>>,
    pub transition: TransitionProps,
    pub id: Option<String>,
    pub type_value: Option<HistoryTypeDatatypeProps>,
    pub other_attributes: Map<String, Value>,
}

pub fn default_history() -> HistoryProps {
    HistoryProps {
        other_element: Vec::new(),
        transition: default_transition(),
        id: None,
        type_value: None,
        other_attributes: Map::new(),
    }
}

pub type HistoryArray = Vec<HistoryProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct IfProps {
    pub other_element: Vec<Map<String, Value>>,
    pub raise_value: Vec<RaiseProps>,
    pub if_value: Vec<IfProps>,
    pub foreach: Vec<ForeachProps>,
    pub send: Vec<SendProps>,
    pub script: Vec<ScriptProps>,
    pub assign: Vec<AssignProps>,
    pub log: Vec<LogProps>,
    pub cancel: Vec<CancelProps>,
    pub elseif: Option<ElseifProps>,
    pub else_value: Option<ElseProps>,
    pub cond: String,
    pub other_attributes: Map<String, Value>,
}

pub fn default_if() -> IfProps {
    IfProps {
        other_element: Vec::new(),
        raise_value: Vec::new(),
        if_value: Vec::new(),
        foreach: Vec::new(),
        send: Vec::new(),
        script: Vec::new(),
        assign: Vec::new(),
        log: Vec::new(),
        cancel: Vec::new(),
        elseif: None,
        else_value: None,
        cond: String::new(),
        other_attributes: Map::new(),
    }
}

pub type IfArray = Vec<IfProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct InitialProps {
    pub other_element: Vec<Map<String, Value>>,
    pub transition: TransitionProps,
    pub other_attributes: Map<String, Value>,
}

pub fn default_initial() -> InitialProps {
    InitialProps {
        other_element: Vec::new(),
        transition: default_transition(),
        other_attributes: Map::new(),
    }
}

pub type InitialArray = Vec<InitialProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct InvokeProps {
    pub content: Vec<ContentProps>,
    pub param: Vec<ParamProps>,
    pub finalize: Vec<FinalizeProps>,
    pub other_element: Vec<Map<String, Value>>,
    pub type_value: String,
    pub typeexpr: Option<String>,
    pub src: Option<String>,
    pub srcexpr: Option<String>,
    pub id: Option<String>,
    pub idlocation: Option<String>,
    pub namelist: Option<String>,
    pub autoforward: BooleanDatatypeProps,
    pub other_attributes: Map<String, Value>,
}

pub fn default_invoke() -> InvokeProps {
    InvokeProps {
        content: Vec::new(),
        param: Vec::new(),
        finalize: Vec::new(),
        other_element: Vec::new(),
        type_value: "scxml".to_string(),
        typeexpr: None,
        src: None,
        srcexpr: None,
        id: None,
        idlocation: None,
        namelist: None,
        autoforward: BooleanDatatypeProps::False,
        other_attributes: Map::new(),
    }
}

pub type InvokeArray = Vec<InvokeProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct LogProps {
    pub other_element: Vec<Map<String, Value>>,
    pub label: Option<String>,
    pub expr: Option<String>,
    pub other_attributes: Map<String, Value>,
}

pub fn default_log() -> LogProps {
    LogProps {
        other_element: Vec::new(),
        label: None,
        expr: None,
        other_attributes: Map::new(),
    }
}

pub type LogArray = Vec<LogProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct OnentryProps {
    pub other_element: Vec<Map<String, Value>>,
    pub raise_value: Vec<RaiseProps>,
    pub if_value: Vec<IfProps>,
    pub foreach: Vec<ForeachProps>,
    pub send: Vec<SendProps>,
    pub script: Vec<ScriptProps>,
    pub assign: Vec<AssignProps>,
    pub log: Vec<LogProps>,
    pub cancel: Vec<CancelProps>,
    pub other_attributes: Map<String, Value>,
}

pub fn default_onentry() -> OnentryProps {
    OnentryProps {
        other_element: Vec::new(),
        raise_value: Vec::new(),
        if_value: Vec::new(),
        foreach: Vec::new(),
        send: Vec::new(),
        script: Vec::new(),
        assign: Vec::new(),
        log: Vec::new(),
        cancel: Vec::new(),
        other_attributes: Map::new(),
    }
}

pub type OnentryArray = Vec<OnentryProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct OnexitProps {
    pub other_element: Vec<Map<String, Value>>,
    pub raise_value: Vec<RaiseProps>,
    pub if_value: Vec<IfProps>,
    pub foreach: Vec<ForeachProps>,
    pub send: Vec<SendProps>,
    pub script: Vec<ScriptProps>,
    pub assign: Vec<AssignProps>,
    pub log: Vec<LogProps>,
    pub cancel: Vec<CancelProps>,
    pub other_attributes: Map<String, Value>,
}

pub fn default_onexit() -> OnexitProps {
    OnexitProps {
        other_element: Vec::new(),
        raise_value: Vec::new(),
        if_value: Vec::new(),
        foreach: Vec::new(),
        send: Vec::new(),
        script: Vec::new(),
        assign: Vec::new(),
        log: Vec::new(),
        cancel: Vec::new(),
        other_attributes: Map::new(),
    }
}

pub type OnexitArray = Vec<OnexitProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ParallelProps {
    pub onentry: Vec<OnentryProps>,
    pub onexit: Vec<OnexitProps>,
    pub transition: Vec<TransitionProps>,
    pub state: Vec<StateProps>,
    pub parallel: Vec<ParallelProps>,
    pub history: Vec<HistoryProps>,
    pub datamodel: Vec<DatamodelProps>,
    pub invoke: Vec<InvokeProps>,
    pub other_element: Vec<Map<String, Value>>,
    pub id: Option<String>,
    pub other_attributes: Map<String, Value>,
}

pub fn default_parallel() -> ParallelProps {
    ParallelProps {
        onentry: Vec::new(),
        onexit: Vec::new(),
        transition: Vec::new(),
        state: Vec::new(),
        parallel: Vec::new(),
        history: Vec::new(),
        datamodel: Vec::new(),
        invoke: Vec::new(),
        other_element: Vec::new(),
        id: None,
        other_attributes: Map::new(),
    }
}

pub type ParallelArray = Vec<ParallelProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ParamProps {
    pub other_element: Vec<Map<String, Value>>,
    pub name: String,
    pub expr: Option<String>,
    pub location: Option<String>,
    pub other_attributes: Map<String, Value>,
}

pub fn default_param() -> ParamProps {
    ParamProps {
        other_element: Vec::new(),
        name: String::new(),
        expr: None,
        location: None,
        other_attributes: Map::new(),
    }
}

pub type ParamArray = Vec<ParamProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct RaiseProps {
    pub event: String,
    pub other_attributes: Map<String, Value>,
}

pub fn default_raise() -> RaiseProps {
    RaiseProps {
        event: String::new(),
        other_attributes: Map::new(),
    }
}

pub type RaiseArray = Vec<RaiseProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ScriptProps {
    pub src: Option<String>,
    pub other_attributes: Map<String, Value>,
    pub content: Vec<Map<String, Value>>,
}

pub fn default_script() -> ScriptProps {
    ScriptProps {
        src: None,
        other_attributes: Map::new(),
        content: Vec::new(),
    }
}

pub type ScriptArray = Vec<ScriptProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ScxmlProps {
    pub state: Vec<StateProps>,
    pub parallel: Vec<ParallelProps>,
    pub r#final: Vec<FinalProps>,
    pub datamodel: Vec<DatamodelProps>,
    pub script: Vec<ScriptProps>,
    pub other_element: Vec<Map<String, Value>>,
    pub initial: Vec<String>,
    pub name: Option<String>,
    pub version: Value,
    pub datamodel_attribute: String,
    pub binding: Option<BindingDatatypeProps>,
    pub exmode: Option<ExmodeDatatypeProps>,
    pub other_attributes: Map<String, Value>,
}

pub fn default_scxml() -> ScxmlProps {
    ScxmlProps {
        state: Vec::new(),
        parallel: Vec::new(),
        r#final: Vec::new(),
        datamodel: Vec::new(),
        script: Vec::new(),
        other_element: Vec::new(),
        initial: Vec::new(),
        name: None,
        version: Value::Null,
        datamodel_attribute: "null".to_string(),
        binding: None,
        exmode: None,
        other_attributes: Map::new(),
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SendProps {
    pub content: Vec<ContentProps>,
    pub param: Vec<ParamProps>,
    pub other_element: Vec<Map<String, Value>>,
    pub event: Option<String>,
    pub eventexpr: Option<String>,
    pub target: Option<String>,
    pub targetexpr: Option<String>,
    pub type_value: String,
    pub typeexpr: Option<String>,
    pub id: Option<String>,
    pub idlocation: Option<String>,
    pub delay: String,
    pub delayexpr: Option<String>,
    pub namelist: Option<String>,
    pub other_attributes: Map<String, Value>,
}

pub fn default_send() -> SendProps {
    SendProps {
        content: Vec::new(),
        param: Vec::new(),
        other_element: Vec::new(),
        event: None,
        eventexpr: None,
        target: None,
        targetexpr: None,
        type_value: "scxml".to_string(),
        typeexpr: None,
        id: None,
        idlocation: None,
        delay: "0s".to_string(),
        delayexpr: None,
        namelist: None,
        other_attributes: Map::new(),
    }
}

pub type SendArray = Vec<SendProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct StateProps {
    pub onentry: Vec<OnentryProps>,
    pub onexit: Vec<OnexitProps>,
    pub transition: Vec<TransitionProps>,
    pub initial: Vec<InitialProps>,
    pub state: Vec<StateProps>,
    pub parallel: Vec<ParallelProps>,
    pub r#final: Vec<FinalProps>,
    pub history: Vec<HistoryProps>,
    pub datamodel: Vec<DatamodelProps>,
    pub invoke: Vec<InvokeProps>,
    pub other_element: Vec<Map<String, Value>>,
    pub id: Option<String>,
    pub initial_attribute: Vec<String>,
    pub other_attributes: Map<String, Value>,
}

pub fn default_state() -> StateProps {
    StateProps {
        onentry: Vec::new(),
        onexit: Vec::new(),
        transition: Vec::new(),
        initial: Vec::new(),
        state: Vec::new(),
        parallel: Vec::new(),
        r#final: Vec::new(),
        history: Vec::new(),
        datamodel: Vec::new(),
        invoke: Vec::new(),
        other_element: Vec::new(),
        id: None,
        initial_attribute: Vec::new(),
        other_attributes: Map::new(),
    }
}

pub type StateArray = Vec<StateProps>;
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TransitionProps {
    pub other_element: Vec<Map<String, Value>>,
    pub raise_value: Vec<RaiseProps>,
    pub if_value: Vec<IfProps>,
    pub foreach: Vec<ForeachProps>,
    pub send: Vec<SendProps>,
    pub script: Vec<ScriptProps>,
    pub assign: Vec<AssignProps>,
    pub log: Vec<LogProps>,
    pub cancel: Vec<CancelProps>,
    pub event: Option<String>,
    pub cond: Option<String>,
    pub target: Vec<String>,
    pub type_value: Option<TransitionTypeDatatypeProps>,
    pub other_attributes: Map<String, Value>,
}

pub fn default_transition() -> TransitionProps {
    TransitionProps {
        other_element: Vec::new(),
        raise_value: Vec::new(),
        if_value: Vec::new(),
        foreach: Vec::new(),
        send: Vec::new(),
        script: Vec::new(),
        assign: Vec::new(),
        log: Vec::new(),
        cancel: Vec::new(),
        event: None,
        cond: None,
        target: Vec::new(),
        type_value: None,
        other_attributes: Map::new(),
    }
}

pub type TransitionArray = Vec<TransitionProps>;
