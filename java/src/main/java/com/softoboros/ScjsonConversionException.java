/**
 * Agent Name: scjson-conversion-exception
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */
package com.softobros;

/**
 * Exception raised when SCXML and SCJSON conversions fail.
 */
public class ScjsonConversionException extends RuntimeException {
    private static final long serialVersionUID = 1L;

    /**
     * Create an exception with a message.
     *
     * @param message explanation of the failure
     */
    public ScjsonConversionException(String message) {
        super(message);
    }

    /**
     * Create an exception with a message and a cause.
     *
     * @param message explanation of the failure
     * @param cause underlying exception that triggered the failure
     */
    public ScjsonConversionException(String message, Throwable cause) {
        super(message, cause);
    }
}
