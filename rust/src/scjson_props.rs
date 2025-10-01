// scjson_props.rs : Properties file for scjson types
//
// Part of the scjson project.
// Developed by Softoboros Technology Inc.
// Licensed under the BSD 1-Clause License.
use serde::{Serialize, Deserialize};
use serde_json::{Map, Value};

//
// ==== ENUMERATIONS ===
//

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
/// The assign type that allows for precise manipulation of the datamodel
///     location.
///     Types are:
///     replacechildren (default),
///     firstchild, lastchild,
///     previoussibling, nextsibling,
///     replace, delete,
///     addattribute
pub enum AssignTypeDatatypeProps {
    Replacechildren,
    Firstchild,
    Lastchild,
    Previoussibling,
    Nextsibling,
    Replace,
    Delete,
    Addattribute,
}
/// Retrieves the Default AssignTypeDatatypeProps Value
impl Default for AssignTypeDatatypeProps {
    fn default() -> Self {
        Self::Replacechildren
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
///     The binding type in use for the SCXML document.
pub enum BindingDatatypeProps {
    Early,
    Late,
}
/// Retrieves the Default BindingDatatypeProps Value
impl Default for BindingDatatypeProps {
    fn default() -> Self {
        Self::Early
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
/// Boolean: true or false only
pub enum BooleanDatatypeProps {
    True,
    False,
}
/// Retrieves the Default BooleanDatatypeProps Value
impl Default for BooleanDatatypeProps {
    fn default() -> Self {
        Self::True
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
/// Describes the processor execution mode for this document, being either "lax"
/// or "strict".
pub enum ExmodeDatatypeProps {
    Lax,
    Strict,
}
/// Retrieves the Default ExmodeDatatypeProps Value
impl Default for ExmodeDatatypeProps {
    fn default() -> Self {
        Self::Lax
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
/// type of `<history>` state: `shallow` or `deep`.
pub enum HistoryTypeDatatypeProps {
    Shallow,
    Deep,
}
/// Retrieves the Default HistoryTypeDatatypeProps Value
impl Default for HistoryTypeDatatypeProps {
    fn default() -> Self {
        Self::Shallow
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
///     The type of the transition i.e. internal or external.
pub enum TransitionTypeDatatypeProps {
    Internal,
    External,
}
/// Retrieves the Default TransitionTypeDatatypeProps Value
impl Default for TransitionTypeDatatypeProps {
    fn default() -> Self {
        Self::Internal
    }
}


//
// ==== STRUCTS ===
//

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// update a datamodel location with an expression or value.
pub struct AssignProps {
    #[serde(default)]
    pub location: String,
    #[serde(default)]
    pub expr: Option<String>,
    #[serde(default)]
    pub type_value: AssignTypeDatatypeProps,
    #[serde(default)]
    pub attr: Option<String>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
    #[serde(default)]
    /// inline payload used by `<send>` and `<invoke>`.
    pub content: Vec<Map<String, Value>>,
}
/// Instantiates a Default Props Object
impl Default for AssignProps {
    fn default() -> Self {
        Self {
            location: String::default(),
            expr: Option::<String>::default(),
            type_value: AssignTypeDatatypeProps::default(),
            attr: Option::<String>::default(),
            other_attributes: Map::<String, Value>::default(),
            content: Vec::<Map::<String, Value>>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// cancel a pending `<send>` operation.
pub struct CancelProps {
    #[serde(default)]
    pub other_element: Vec<Map<String, Value>>,
    #[serde(default)]
    pub sendid: Option<String>,
    #[serde(default)]
    pub sendidexpr: Option<String>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for CancelProps {
    fn default() -> Self {
        Self {
            other_element: Vec::<Map::<String, Value>>::default(),
            sendid: Option::<String>::default(),
            sendidexpr: Option::<String>::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// inline payload used by `<send>` and `<invoke>`.
pub struct ContentProps {
    #[serde(default)]
    /// inline payload used by `<send>` and `<invoke>`.
    pub content: Option<Vec<ScxmlProps>>,
    #[serde(default)]
    pub expr: Option<String>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for ContentProps {
    fn default() -> Self {
        Self {
            content: Option::<Vec::<ScxmlProps>>::default(),
            expr: Option::<String>::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// represents a single datamodel variable.
pub struct DataProps {
    #[serde(default)]
    pub id: String,
    #[serde(default)]
    pub src: Option<String>,
    #[serde(default)]
    pub expr: Option<String>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
    #[serde(default)]
    /// inline payload used by `<send>` and `<invoke>`.
    pub content: Vec<Map<String, Value>>,
}
/// Instantiates a Default Props Object
impl Default for DataProps {
    fn default() -> Self {
        Self {
            id: String::default(),
            src: Option::<String>::default(),
            expr: Option::<String>::default(),
            other_attributes: Map::<String, Value>::default(),
            content: Vec::<Map::<String, Value>>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// container for one or more `<data>` elements.
pub struct DatamodelProps {
    #[serde(default)]
    /// represents a single datamodel variable.
    pub data: Vec<DataProps>,
    #[serde(default)]
    pub other_element: Vec<Map<String, Value>>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for DatamodelProps {
    fn default() -> Self {
        Self {
            data: Vec::<DataProps>::default(),
            other_element: Vec::<Map::<String, Value>>::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// payload returned when a `<final>` state is reached.
pub struct DonedataProps {
    #[serde(default)]
    /// inline payload used by `<send>` and `<invoke>`.
    pub content: Option<ContentProps>,
    #[serde(default)]
    /// parameter passed to `<invoke>` or `<send>`.
    pub param: Vec<ParamProps>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for DonedataProps {
    fn default() -> Self {
        Self {
            content: Option::<ContentProps>::default(),
            param: Vec::<ParamProps>::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// fallback branch for `<if>` conditions.
pub struct ElseProps {
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for ElseProps {
    fn default() -> Self {
        Self {
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// conditional branch following an `<if>`.
pub struct ElseifProps {
    #[serde(default)]
    pub cond: String,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for ElseifProps {
    fn default() -> Self {
        Self {
            cond: String::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// marks a terminal state in the machine.
pub struct FinalProps {
    #[serde(default)]
    /// actions performed when entering a state.
    pub onentry: Vec<OnentryProps>,
    #[serde(default)]
    /// actions performed when leaving a state.
    pub onexit: Vec<OnexitProps>,
    #[serde(default)]
    /// payload returned when a `<final>` state is reached.
    pub donedata: Vec<DonedataProps>,
    #[serde(default)]
    pub other_element: Vec<Map<String, Value>>,
    #[serde(default)]
    pub id: Option<String>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for FinalProps {
    fn default() -> Self {
        Self {
            onentry: Vec::<OnentryProps>::default(),
            onexit: Vec::<OnexitProps>::default(),
            donedata: Vec::<DonedataProps>::default(),
            other_element: Vec::<Map::<String, Value>>::default(),
            id: Option::<String>::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// executed after an `<invoke>` completes.
pub struct FinalizeProps {
    #[serde(default)]
    pub other_element: Vec<Map<String, Value>>,
    #[serde(default)]
    pub raise_value: Vec<RaiseProps>,
    #[serde(default)]
    pub if_value: Vec<IfProps>,
    #[serde(default)]
    /// iterate over items within executable content.
    pub foreach: Vec<ForeachProps>,
    #[serde(default)]
    /// dispatch an external event.
    pub send: Vec<SendProps>,
    #[serde(default)]
    /// inline executable script.
    pub script: Vec<ScriptProps>,
    #[serde(default)]
    /// update a datamodel location with an expression or value.
    pub assign: Vec<AssignProps>,
    #[serde(default)]
    /// diagnostic output statement.
    pub log: Vec<LogProps>,
    #[serde(default)]
    /// cancel a pending `<send>` operation.
    pub cancel: Vec<CancelProps>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for FinalizeProps {
    fn default() -> Self {
        Self {
            other_element: Vec::<Map::<String, Value>>::default(),
            raise_value: Vec::<RaiseProps>::default(),
            if_value: Vec::<IfProps>::default(),
            foreach: Vec::<ForeachProps>::default(),
            send: Vec::<SendProps>::default(),
            script: Vec::<ScriptProps>::default(),
            assign: Vec::<AssignProps>::default(),
            log: Vec::<LogProps>::default(),
            cancel: Vec::<CancelProps>::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// iterate over items within executable content.
pub struct ForeachProps {
    #[serde(default)]
    pub other_element: Vec<Map<String, Value>>,
    #[serde(default)]
    pub raise_value: Vec<RaiseProps>,
    #[serde(default)]
    pub if_value: Vec<IfProps>,
    #[serde(default)]
    /// iterate over items within executable content.
    pub foreach: Vec<ForeachProps>,
    #[serde(default)]
    /// dispatch an external event.
    pub send: Vec<SendProps>,
    #[serde(default)]
    /// inline executable script.
    pub script: Vec<ScriptProps>,
    #[serde(default)]
    /// update a datamodel location with an expression or value.
    pub assign: Vec<AssignProps>,
    #[serde(default)]
    /// diagnostic output statement.
    pub log: Vec<LogProps>,
    #[serde(default)]
    /// cancel a pending `<send>` operation.
    pub cancel: Vec<CancelProps>,
    #[serde(default)]
    pub array: String,
    #[serde(default)]
    pub item: String,
    #[serde(default)]
    pub index: Option<String>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for ForeachProps {
    fn default() -> Self {
        Self {
            other_element: Vec::<Map::<String, Value>>::default(),
            raise_value: Vec::<RaiseProps>::default(),
            if_value: Vec::<IfProps>::default(),
            foreach: Vec::<ForeachProps>::default(),
            send: Vec::<SendProps>::default(),
            script: Vec::<ScriptProps>::default(),
            assign: Vec::<AssignProps>::default(),
            log: Vec::<LogProps>::default(),
            cancel: Vec::<CancelProps>::default(),
            array: String::default(),
            item: String::default(),
            index: Option::<String>::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// pseudostate remembering previous active children.
pub struct HistoryProps {
    #[serde(default)]
    pub other_element: Vec<Map<String, Value>>,
    #[serde(default)]
    /// edge between states triggered by events.
    pub transition: TransitionProps,
    #[serde(default)]
    pub id: Option<String>,
    #[serde(default)]
    pub type_value: Option<HistoryTypeDatatypeProps>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for HistoryProps {
    fn default() -> Self {
        Self {
            other_element: Vec::<Map::<String, Value>>::default(),
            transition: TransitionProps::default(),
            id: Option::<String>::default(),
            type_value: Option::<HistoryTypeDatatypeProps>::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// conditional execution block.
pub struct IfProps {
    #[serde(default)]
    pub other_element: Vec<Map<String, Value>>,
    #[serde(default)]
    pub raise_value: Vec<RaiseProps>,
    #[serde(default)]
    pub if_value: Vec<IfProps>,
    #[serde(default)]
    /// iterate over items within executable content.
    pub foreach: Vec<ForeachProps>,
    #[serde(default)]
    /// dispatch an external event.
    pub send: Vec<SendProps>,
    #[serde(default)]
    /// inline executable script.
    pub script: Vec<ScriptProps>,
    #[serde(default)]
    /// update a datamodel location with an expression or value.
    pub assign: Vec<AssignProps>,
    #[serde(default)]
    /// diagnostic output statement.
    pub log: Vec<LogProps>,
    #[serde(default)]
    /// cancel a pending `<send>` operation.
    pub cancel: Vec<CancelProps>,
    #[serde(default)]
    /// conditional branch following an `<if>`.
    pub elseif: Option<ElseifProps>,
    #[serde(default)]
    pub else_value: Option<ElseProps>,
    #[serde(default)]
    pub cond: String,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for IfProps {
    fn default() -> Self {
        Self {
            other_element: Vec::<Map::<String, Value>>::default(),
            raise_value: Vec::<RaiseProps>::default(),
            if_value: Vec::<IfProps>::default(),
            foreach: Vec::<ForeachProps>::default(),
            send: Vec::<SendProps>::default(),
            script: Vec::<ScriptProps>::default(),
            assign: Vec::<AssignProps>::default(),
            log: Vec::<LogProps>::default(),
            cancel: Vec::<CancelProps>::default(),
            elseif: Option::<ElseifProps>::default(),
            else_value: Option::<ElseProps>::default(),
            cond: String::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// starting state within a compound state.
pub struct InitialProps {
    #[serde(default)]
    pub other_element: Vec<Map<String, Value>>,
    #[serde(default)]
    /// edge between states triggered by events.
    pub transition: TransitionProps,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for InitialProps {
    fn default() -> Self {
        Self {
            other_element: Vec::<Map::<String, Value>>::default(),
            transition: TransitionProps::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// run an external process or machine.
pub struct InvokeProps {
    #[serde(default)]
    /// inline payload used by `<send>` and `<invoke>`.
    pub content: Vec<ContentProps>,
    #[serde(default)]
    /// parameter passed to `<invoke>` or `<send>`.
    pub param: Vec<ParamProps>,
    #[serde(default)]
    /// executed after an `<invoke>` completes.
    pub finalize: Vec<FinalizeProps>,
    #[serde(default)]
    pub other_element: Vec<Map<String, Value>>,
    #[serde(default)]
    pub type_value: String,
    #[serde(default)]
    pub typeexpr: Option<String>,
    #[serde(default)]
    pub src: Option<String>,
    #[serde(default)]
    pub srcexpr: Option<String>,
    #[serde(default)]
    pub id: Option<String>,
    #[serde(default)]
    pub idlocation: Option<String>,
    #[serde(default)]
    pub namelist: Option<String>,
    #[serde(default)]
    pub autoforward: BooleanDatatypeProps,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for InvokeProps {
    fn default() -> Self {
        Self {
            content: Vec::<ContentProps>::default(),
            param: Vec::<ParamProps>::default(),
            finalize: Vec::<FinalizeProps>::default(),
            other_element: Vec::<Map::<String, Value>>::default(),
            type_value: String::default(),
            typeexpr: Option::<String>::default(),
            src: Option::<String>::default(),
            srcexpr: Option::<String>::default(),
            id: Option::<String>::default(),
            idlocation: Option::<String>::default(),
            namelist: Option::<String>::default(),
            autoforward: BooleanDatatypeProps::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// diagnostic output statement.
pub struct LogProps {
    #[serde(default)]
    pub other_element: Vec<Map<String, Value>>,
    #[serde(default)]
    pub label: Option<String>,
    #[serde(default)]
    pub expr: Option<String>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for LogProps {
    fn default() -> Self {
        Self {
            other_element: Vec::<Map::<String, Value>>::default(),
            label: Option::<String>::default(),
            expr: Option::<String>::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// actions performed when entering a state.
pub struct OnentryProps {
    #[serde(default)]
    pub other_element: Vec<Map<String, Value>>,
    #[serde(default)]
    pub raise_value: Vec<RaiseProps>,
    #[serde(default)]
    pub if_value: Vec<IfProps>,
    #[serde(default)]
    /// iterate over items within executable content.
    pub foreach: Vec<ForeachProps>,
    #[serde(default)]
    /// dispatch an external event.
    pub send: Vec<SendProps>,
    #[serde(default)]
    /// inline executable script.
    pub script: Vec<ScriptProps>,
    #[serde(default)]
    /// update a datamodel location with an expression or value.
    pub assign: Vec<AssignProps>,
    #[serde(default)]
    /// diagnostic output statement.
    pub log: Vec<LogProps>,
    #[serde(default)]
    /// cancel a pending `<send>` operation.
    pub cancel: Vec<CancelProps>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for OnentryProps {
    fn default() -> Self {
        Self {
            other_element: Vec::<Map::<String, Value>>::default(),
            raise_value: Vec::<RaiseProps>::default(),
            if_value: Vec::<IfProps>::default(),
            foreach: Vec::<ForeachProps>::default(),
            send: Vec::<SendProps>::default(),
            script: Vec::<ScriptProps>::default(),
            assign: Vec::<AssignProps>::default(),
            log: Vec::<LogProps>::default(),
            cancel: Vec::<CancelProps>::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// actions performed when leaving a state.
pub struct OnexitProps {
    #[serde(default)]
    pub other_element: Vec<Map<String, Value>>,
    #[serde(default)]
    pub raise_value: Vec<RaiseProps>,
    #[serde(default)]
    pub if_value: Vec<IfProps>,
    #[serde(default)]
    /// iterate over items within executable content.
    pub foreach: Vec<ForeachProps>,
    #[serde(default)]
    /// dispatch an external event.
    pub send: Vec<SendProps>,
    #[serde(default)]
    /// inline executable script.
    pub script: Vec<ScriptProps>,
    #[serde(default)]
    /// update a datamodel location with an expression or value.
    pub assign: Vec<AssignProps>,
    #[serde(default)]
    /// diagnostic output statement.
    pub log: Vec<LogProps>,
    #[serde(default)]
    /// cancel a pending `<send>` operation.
    pub cancel: Vec<CancelProps>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for OnexitProps {
    fn default() -> Self {
        Self {
            other_element: Vec::<Map::<String, Value>>::default(),
            raise_value: Vec::<RaiseProps>::default(),
            if_value: Vec::<IfProps>::default(),
            foreach: Vec::<ForeachProps>::default(),
            send: Vec::<SendProps>::default(),
            script: Vec::<ScriptProps>::default(),
            assign: Vec::<AssignProps>::default(),
            log: Vec::<LogProps>::default(),
            cancel: Vec::<CancelProps>::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// coordinates concurrent regions.
pub struct ParallelProps {
    #[serde(default)]
    /// actions performed when entering a state.
    pub onentry: Vec<OnentryProps>,
    #[serde(default)]
    /// actions performed when leaving a state.
    pub onexit: Vec<OnexitProps>,
    #[serde(default)]
    /// edge between states triggered by events.
    pub transition: Vec<TransitionProps>,
    #[serde(default)]
    /// basic state node.
    pub state: Vec<StateProps>,
    #[serde(default)]
    /// coordinates concurrent regions.
    pub parallel: Vec<ParallelProps>,
    #[serde(default)]
    /// pseudostate remembering previous active children.
    pub history: Vec<HistoryProps>,
    #[serde(default)]
    /// container for one or more `<data>` elements.
    pub datamodel: Vec<DatamodelProps>,
    #[serde(default)]
    /// run an external process or machine.
    pub invoke: Vec<InvokeProps>,
    #[serde(default)]
    pub other_element: Vec<Map<String, Value>>,
    #[serde(default)]
    pub id: Option<String>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for ParallelProps {
    fn default() -> Self {
        Self {
            onentry: Vec::<OnentryProps>::default(),
            onexit: Vec::<OnexitProps>::default(),
            transition: Vec::<TransitionProps>::default(),
            state: Vec::<StateProps>::default(),
            parallel: Vec::<ParallelProps>::default(),
            history: Vec::<HistoryProps>::default(),
            datamodel: Vec::<DatamodelProps>::default(),
            invoke: Vec::<InvokeProps>::default(),
            other_element: Vec::<Map::<String, Value>>::default(),
            id: Option::<String>::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// parameter passed to `<invoke>` or `<send>`.
pub struct ParamProps {
    #[serde(default)]
    pub other_element: Vec<Map<String, Value>>,
    #[serde(default)]
    pub name: String,
    #[serde(default)]
    pub expr: Option<String>,
    #[serde(default)]
    pub location: Option<String>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for ParamProps {
    fn default() -> Self {
        Self {
            other_element: Vec::<Map::<String, Value>>::default(),
            name: String::default(),
            expr: Option::<String>::default(),
            location: Option::<String>::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// raise an internal event.
pub struct RaiseProps {
    #[serde(default)]
    pub event: String,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for RaiseProps {
    fn default() -> Self {
        Self {
            event: String::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// inline executable script.
pub struct ScriptProps {
    #[serde(default)]
    pub src: Option<String>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
    #[serde(default)]
    /// inline payload used by `<send>` and `<invoke>`.
    pub content: Vec<Map<String, Value>>,
}
/// Instantiates a Default Props Object
impl Default for ScriptProps {
    fn default() -> Self {
        Self {
            src: Option::<String>::default(),
            other_attributes: Map::<String, Value>::default(),
            content: Vec::<Map::<String, Value>>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// root element of an SCJSON document.
pub struct ScxmlProps {
    #[serde(default)]
    /// basic state node.
    pub state: Vec<StateProps>,
    #[serde(default)]
    /// coordinates concurrent regions.
    pub parallel: Vec<ParallelProps>,
    #[serde(default)]
    /// marks a terminal state in the machine.
    pub r#final: Vec<FinalProps>,
    #[serde(default)]
    /// container for one or more `<data>` elements.
    pub datamodel: Vec<DatamodelProps>,
    #[serde(default)]
    /// inline executable script.
    pub script: Vec<ScriptProps>,
    #[serde(default)]
    pub other_element: Vec<Map<String, Value>>,
    #[serde(default)]
    /// starting state within a compound state.
    pub initial: Vec<String>,
    #[serde(default)]
    pub name: Option<String>,
    #[serde(default)]
    pub version: Value,
    #[serde(default)]
    pub datamodel_attribute: String,
    #[serde(default)]
    pub binding: Option<BindingDatatypeProps>,
    #[serde(default)]
    pub exmode: Option<ExmodeDatatypeProps>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for ScxmlProps {
    fn default() -> Self {
        Self {
            state: Vec::<StateProps>::default(),
            parallel: Vec::<ParallelProps>::default(),
            r#final: Vec::<FinalProps>::default(),
            datamodel: Vec::<DatamodelProps>::default(),
            script: Vec::<ScriptProps>::default(),
            other_element: Vec::<Map::<String, Value>>::default(),
            initial: Vec::<String>::default(),
            name: Option::<String>::default(),
            version: Value::default(),
            datamodel_attribute: String::default(),
            binding: Option::<BindingDatatypeProps>::default(),
            exmode: Option::<ExmodeDatatypeProps>::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// dispatch an external event.
pub struct SendProps {
    #[serde(default)]
    /// inline payload used by `<send>` and `<invoke>`.
    pub content: Vec<ContentProps>,
    #[serde(default)]
    /// parameter passed to `<invoke>` or `<send>`.
    pub param: Vec<ParamProps>,
    #[serde(default)]
    pub other_element: Vec<Map<String, Value>>,
    #[serde(default)]
    pub event: Option<String>,
    #[serde(default)]
    pub eventexpr: Option<String>,
    #[serde(default)]
    pub target: Option<String>,
    #[serde(default)]
    pub targetexpr: Option<String>,
    #[serde(default)]
    pub type_value: String,
    #[serde(default)]
    pub typeexpr: Option<String>,
    #[serde(default)]
    pub id: Option<String>,
    #[serde(default)]
    pub idlocation: Option<String>,
    #[serde(default)]
    pub delay: String,
    #[serde(default)]
    pub delayexpr: Option<String>,
    #[serde(default)]
    pub namelist: Option<String>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for SendProps {
    fn default() -> Self {
        Self {
            content: Vec::<ContentProps>::default(),
            param: Vec::<ParamProps>::default(),
            other_element: Vec::<Map::<String, Value>>::default(),
            event: Option::<String>::default(),
            eventexpr: Option::<String>::default(),
            target: Option::<String>::default(),
            targetexpr: Option::<String>::default(),
            type_value: String::default(),
            typeexpr: Option::<String>::default(),
            id: Option::<String>::default(),
            idlocation: Option::<String>::default(),
            delay: String::default(),
            delayexpr: Option::<String>::default(),
            namelist: Option::<String>::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// basic state node.
pub struct StateProps {
    #[serde(default)]
    /// actions performed when entering a state.
    pub onentry: Vec<OnentryProps>,
    #[serde(default)]
    /// actions performed when leaving a state.
    pub onexit: Vec<OnexitProps>,
    #[serde(default)]
    /// edge between states triggered by events.
    pub transition: Vec<TransitionProps>,
    #[serde(default)]
    /// starting state within a compound state.
    pub initial: Vec<InitialProps>,
    #[serde(default)]
    /// basic state node.
    pub state: Vec<StateProps>,
    #[serde(default)]
    /// coordinates concurrent regions.
    pub parallel: Vec<ParallelProps>,
    #[serde(default)]
    /// marks a terminal state in the machine.
    pub r#final: Vec<FinalProps>,
    #[serde(default)]
    /// pseudostate remembering previous active children.
    pub history: Vec<HistoryProps>,
    #[serde(default)]
    /// container for one or more `<data>` elements.
    pub datamodel: Vec<DatamodelProps>,
    #[serde(default)]
    /// run an external process or machine.
    pub invoke: Vec<InvokeProps>,
    #[serde(default)]
    pub other_element: Vec<Map<String, Value>>,
    #[serde(default)]
    pub id: Option<String>,
    #[serde(default)]
    pub initial_attribute: Vec<String>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for StateProps {
    fn default() -> Self {
        Self {
            onentry: Vec::<OnentryProps>::default(),
            onexit: Vec::<OnexitProps>::default(),
            transition: Vec::<TransitionProps>::default(),
            initial: Vec::<InitialProps>::default(),
            state: Vec::<StateProps>::default(),
            parallel: Vec::<ParallelProps>::default(),
            r#final: Vec::<FinalProps>::default(),
            history: Vec::<HistoryProps>::default(),
            datamodel: Vec::<DatamodelProps>::default(),
            invoke: Vec::<InvokeProps>::default(),
            other_element: Vec::<Map::<String, Value>>::default(),
            id: Option::<String>::default(),
            initial_attribute: Vec::<String>::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
/// edge between states triggered by events.
pub struct TransitionProps {
    #[serde(default)]
    pub other_element: Vec<Map<String, Value>>,
    #[serde(default)]
    pub raise_value: Vec<RaiseProps>,
    #[serde(default)]
    pub if_value: Vec<IfProps>,
    #[serde(default)]
    /// iterate over items within executable content.
    pub foreach: Vec<ForeachProps>,
    #[serde(default)]
    /// dispatch an external event.
    pub send: Vec<SendProps>,
    #[serde(default)]
    /// inline executable script.
    pub script: Vec<ScriptProps>,
    #[serde(default)]
    /// update a datamodel location with an expression or value.
    pub assign: Vec<AssignProps>,
    #[serde(default)]
    /// diagnostic output statement.
    pub log: Vec<LogProps>,
    #[serde(default)]
    /// cancel a pending `<send>` operation.
    pub cancel: Vec<CancelProps>,
    #[serde(default)]
    pub event: Option<String>,
    #[serde(default)]
    pub cond: Option<String>,
    #[serde(default)]
    pub target: Vec<String>,
    #[serde(default)]
    pub type_value: Option<TransitionTypeDatatypeProps>,
    #[serde(default)]
    pub other_attributes: Map<String, Value>,
}
/// Instantiates a Default Props Object
impl Default for TransitionProps {
    fn default() -> Self {
        Self {
            other_element: Vec::<Map::<String, Value>>::default(),
            raise_value: Vec::<RaiseProps>::default(),
            if_value: Vec::<IfProps>::default(),
            foreach: Vec::<ForeachProps>::default(),
            send: Vec::<SendProps>::default(),
            script: Vec::<ScriptProps>::default(),
            assign: Vec::<AssignProps>::default(),
            log: Vec::<LogProps>::default(),
            cancel: Vec::<CancelProps>::default(),
            event: Option::<String>::default(),
            cond: Option::<String>::default(),
            target: Vec::<String>::default(),
            type_value: Option::<TransitionTypeDatatypeProps>::default(),
            other_attributes: Map::<String, Value>::default(),
        }
    }
}

