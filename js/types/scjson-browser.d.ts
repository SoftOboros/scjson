declare module 'scjson/browser' {
  /**
   * Recursively removes nulls, empty arrays/objects, and empty strings from a value.
   * @param value Any input value (array, object, scalar).
   * @returns Sanitized value or `undefined`.
   */
  export function removeEmpty(value: any): any;

  /**
   * Converts SCXML (as XML string) to SCJSON (as JSON string).
   * @param xmlStr SCXML input as string.
   * @param omitEmpty Optional: if true, removes empty/null fields (default: true).
   * @returns Validated SCJSON as pretty-printed JSON string.
   * @throws Error if validation fails.
   */
  export function xmlToJson(xmlStr: string, omitEmpty?: boolean): {
    result: string;
    valid: boolean;
    errors: object[] | null;
  };

  /**
   * Converts SCJSON (as JSON string) to SCXML (as XML string).
   * @param jsonStr SCJSON input as string.
   * @returns Valid SCXML string.
   * @throws Error if validation fails.
   */
  export function jsonToXml(jsonStr: string): {
    result: string;
    valid: boolean;
    errors: object[] | null;
  };
}
