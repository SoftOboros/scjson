rm ../xsd/*.xsd
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml-attribs.xsd		 
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml-contentmodels.xsd	 
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml-copyright.xsd	 
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml-core-strict.xsd
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml-data-strict.xsd 
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml-datatypes.xsd 
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml-external-strict.xsd
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml-message.xsd
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml-messages.xsd
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml-module-anchor.xsd	 
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml-module-core.xsd 
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml-module-data.xsd	 
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml-module-external.xsd 
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml-module-script.xsd	 
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml-profile-basic.xsd 
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml-profile-ecma.xsd	 
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml-profile-minimum.xsd	 
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml-profile-xpath.xsd	 
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml-strict.xsd	 
wget --directory-prefix=../xsd https://www.w3.org/2011/04/SCXML/scxml.xsd

xsdata generate \
        --output pydantic  \
        --package scjson.pydantic.generated \
        --structure-style single-package \
        --unnest-classes \
        --relative-imports \
        ../xsd/scxml.xsd
        
xsdata generate \
        --output dataclasses  \
        --package scjson.dataclasses.generated \
        --structure-style single-package \
        --unnest-classes \
        --relative-imports \
        ../xsd/scxml.xsd 

xsdata generate \
        --output pydantic  \
        --package scjson.pydantic_strict.generated \
        --structure-style single-package \
        --unnest-classes \
        --relative-imports \
        ../xsd/scxml-strict.xsd
        
xsdata generate \
        --output dataclasses  \
        --package scjson.dataclasses_strict.generated \
        --structure-style single-package \
        --unnest-classes \
        --relative-imports \
        ../xsd/scxml-strict.xsd 

python patch_scxml_forward_ref.py --file ./scjson/pydantic/generated.py
python patch_scxml_forward_ref.py --file ./scjson/pydantic_strict/generated.py
