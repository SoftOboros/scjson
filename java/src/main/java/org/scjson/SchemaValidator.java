/**
 * Agent Name: schema-validator
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */
package org.scjson;

import org.everit.json.schema.Schema;
import org.everit.json.schema.loader.SchemaLoader;
import org.json.JSONObject;
import org.json.JSONTokener;

import java.io.InputStream;

/**
 * Utility class for validating JSON documents against the SCJSON schema.
 */
public final class SchemaValidator {
    private SchemaValidator() {
    }

    /**
     * Validate JSON input using the bundled schema.
     *
     * @param jsonStream input JSON stream
     * @throws Exception if validation fails
     */
    public static void validate(InputStream jsonStream) throws Exception {
        try (InputStream schemaStream = SchemaValidator.class.getResourceAsStream("/scjson.schema.json")) {
            Schema schema = SchemaLoader.load(new JSONObject(new JSONTokener(schemaStream)));
            schema.validate(new JSONObject(new JSONTokener(jsonStream)));
        }
    }
}
