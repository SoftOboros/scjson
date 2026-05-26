#!/usr/bin/env bash
#
#  Update pydantic and typescript data models from fresh w3c xsd download
#
#
# remove any old xsd files 
rm ../xsd/*.xsd
# get the fresh set of xsd from w3c
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
# Generate pydantic model
xsdata generate \
        --output pydantic  \
        --package scjson.pydantic.generated \
        --structure-style single-package \
        --unnest-classes \
        --relative-imports \
        ../xsd/scxml.xsd
# generate dataclasses model for conversion
xsdata generate \
        --output dataclasses  \
        --package scjson.dataclasses.generated \
        --structure-style single-package \
        --unnest-classes \
        --relative-imports \
        ../xsd/scxml.xsd 
# Generate strict pydantic models 
xsdata generate \
        --output pydantic  \
        --package scjson.pydantic_strict.generated \
        --structure-style single-package \
        --unnest-classes \
        --relative-imports \
        ../xsd/scxml-strict.xsd
# Generate strict dataclasses models 
xsdata generate \
        --output dataclasses  \
        --package scjson.dataclasses_strict.generated \
        --structure-style single-package \
        --unnest-classes \
        --relative-imports \
        ../xsd/scxml-strict.xsd 
# Patch pydantic models for forward references in schema (see script)
python patch_scxml_forward_ref.py --file ./scjson/pydantic/generated.py
python patch_scxml_forward_ref.py --file ./scjson/pydantic_strict/generated.py
# Loosen other_attributes typing from dict[str, str] to dict[str, Any] for the
# pydantic models only. JSON round-trips integer/object metadata used by
# downstream tools (e.g. Infinity State layout coordinates). The dataclasses
# variants stay dict[str, str] because xsdata's XML serializer requires
# string-typed Attributes for xs:anyAttribute round-trips.
python patch_other_attributes_any.py --file ./scjson/pydantic/generated.py
python patch_other_attributes_any.py --file ./scjson/pydantic_strict/generated.py
# Inject the CONV-E ``help_text: list[str]`` first-class authoring metadata
# field next to every ``other_attributes`` field. The patch is idempotent and
# applies to both pydantic and dataclasses variants. XML serialization of
# ``help_text`` is intentionally suppressed (xsdata ``type: Ignore``) because
# CONV-F owns SCXML comment promotion; CONV-E only commits the JSON-side
# schema surface. See ``docs/concepts/SCJSON-CONV-00-CONCEPTS.md`` CONV-E.
python patch_help_text.py --file ./scjson/pydantic/generated.py
python patch_help_text.py --file ./scjson/pydantic_strict/generated.py
python patch_help_text.py --file ./scjson/dataclasses/generated.py
python patch_help_text.py --file ./scjson/dataclasses_strict/generated.py
# Project the SCXML strict XSD finalize assertion into generated pydantic
# validation. xsdata currently does not emit XSD 1.1 assertions into the
# pydantic or JSON Schema surfaces, so CONV-H keeps this as a post-generation
# patch.
python patch_finalize_restrictions.py \
        --pydantic-file ./scjson/pydantic/generated.py \
        --pydantic-file ./scjson/pydantic_strict/generated.py
